"""
Models for parsing OpenApi specifications (https://swagger.io/specification/#oas-document)
"""

from __future__ import annotations

import keyword
import re
import inflection
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from functools import cache, cached_property
from typing import Any


class Undefined:
    ...

UNDEFINED = Undefined()


_PYDANTIC_RESERVED_PROPERTIES = frozenset({
    "schema",
})


_RE_SEPARATOR_CHARACTERS = re.compile("[-.:/\\\\ ]")
_RE_INVALID_CHARACTERS = re.compile("[^0-9a-zA-Z_]")
_RE_INVALID_LEADING_CHARACTERS = re.compile("^[^a-zA-Z_]+")


def _ensure_correct_python_identifier(identifier: str) -> str:
    if identifier.isidentifier():
        return identifier

    identifier = _RE_SEPARATOR_CHARACTERS.sub("_", identifier)
    identifier = _RE_INVALID_CHARACTERS.sub("", identifier)
    identifier = _RE_INVALID_LEADING_CHARACTERS.sub("", identifier)

    return identifier


def _is_reserved_identifier(identifier: str, reserved: frozenset) -> bool:
    return keyword.iskeyword(identifier) or identifier in reserved


def ensure_not_reserved_identifier(identifier: str, reserved: frozenset, suffix: str = "_") -> str:
    if _is_reserved_identifier(identifier, reserved):
        return ensure_not_reserved_identifier(f"{identifier}{suffix}", reserved)

    return identifier


@cache
def _ensure_correct_underscore_identifier(identifier: str, reserved: frozenset = frozenset()) -> str:
    identifier = _ensure_correct_python_identifier(identifier)
    identifier = inflection.underscore(identifier)
    identifier = identifier.strip("_")
    identifier = ensure_not_reserved_identifier(identifier, reserved)

    return identifier


class SafetyKeyMixin:

    @cached_property
    def key(self) -> str:
        identifier = _ensure_correct_underscore_identifier(self.orig_key, _PYDANTIC_RESERVED_PROPERTIES)

        if identifier == self.orig_key:
            return self.orig_key

        self.safety_key = identifier

        return self.safety_key


class HttpMethod(Enum):
    get = "get"
    put = "put"
    post = "post"
    delete = "delete"
    options = "options"
    head = "head"
    patch = "patch"
    trace = "trace"


class ParameterLocation(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


class Format(Enum):
    int32 = "int32"
    int64 = "int64"
    float = "float"
    double = "double"
    date = "date"
    time = "time"
    byte = "byte"
    binary = "binary"
    datetime = "date-time"
    datespan = "date-span"
    duration = "duration"
    password = "password"
    uuid = "uuid"
    guid = "guid"
    uri = "uri"
    hostname = "hostname"
    ipv4 = "ipv4"
    ipv6 = "ipv6"
    ipvanynetwork = "ipvanynetwork"

    @classmethod
    def _missing_(cls, value):
        value = re.sub("[_-]*", "", value)
        for member in cls:
            if member.name.lower() == value:
                return member
        return None


@dataclass
class ContactObject:
    """
    https://swagger.io/specification/#contact-object
    """

    name: str | None
    url: str | None
    email: str | None


@dataclass
class LicenseObject:
    """
    https://swagger.io/specification/#license-object
    """

    name: str
    url: str | None


@dataclass
class InfoObject:
    """
    https://swagger.io/specification/#info-object
    """

    title: str
    version: str
    description: str | None = None
    termsOfService: str | None = None
    contact: ContactObject | None = None
    license: LicenseObject | None = None


class Type(Enum):
    string = "string"
    number = "number"
    integer = "integer"
    boolean = "boolean"
    array = "array"
    object = "object"
    null = "null"
    any = "any"

    @property
    def is_primitive(self) -> bool:
        return self in (
            Type.string,
            Type.number,
            Type.integer,
            Type.boolean,
            Type.null,
        )

    @property
    def is_iterable(self) -> bool:
        return self == Type.array

class SchemaType:
    def __init__(self, types: Type | list[Type] | None = None):
        if types is None:
            self._types = tuple()
        elif isinstance(types, list):
            self._types = tuple(types)
        elif isinstance(types, Type):
            self._types = (types,)
        else:
            raise TypeError(f"Unsupported type for SchemaType: {types!r}")

    def __iter__(self):
        return iter(self._types)

    def __contains__(self, t: Type) -> bool:
        return t in self._types

    def __len__(self):
        return len(self._types)

    def __getitem__(self, i: int) -> Type:
        return self._types[i]

    def __eq__(self, other):
        if isinstance(other, SchemaType):
            return self._types == other._types
        if isinstance(other, Type):
            return len(self._types) == 1 and self._types[0] == other
        return NotImplemented

    def __hash__(self):
        if len(self._types) == 1:
            return hash(self._types[0])
        return hash(self._types)

    def __getattr__(self, name):
        if len(self._types) == 1:
            return getattr(self._types[0], name)
        raise AttributeError(
            f"'SchemaType' has no attribute '{name}' (multiple types present: {[t.value for t in self._types]})"
        )

    def __repr__(self):
        if not self._types:
            return "SchemaType()"

        if len(self._types) == 1:
            return f"SchemaType({self._types[0]!r})"

        types_repr = ", ".join(repr(t) for t in self._types)
        return f"SchemaType([{types_repr}])"

    @property
    def is_primitive(self) -> bool:
        return all(t.is_primitive for t in self._types)

    @property
    def is_iterable(self) -> bool:
        return any(t.is_iterable for t in self._types)

    @property
    def is_multiple(self) -> bool:
        return len(self._types) > 1

@dataclass
class SchemaProperty(SafetyKeyMixin):
    orig_key: str
    safety_key: str | None
    schema: "SchemaObject"


@dataclass
class SchemaObject:
    """
    https://swagger.io/specification/#schema-object
    """

    id: str
    title: str | None
    enum: list[str] | None
    type: SchemaType
    format: Format | None
    items: "SchemaObject" | list["SchemaObject"] | None
    properties: list[SchemaProperty]
    default: Any
    description: str | None = None
    additional_roperties: bool = False
    required: list[str] = field(default_factory=list)
    all_of: list["SchemaObject"] = field(default_factory=list)
    any_of: list["SchemaObject"] = field(default_factory=list)
    one_of: list["SchemaObject"] = field(default_factory=list)
    discriminator: Discriminator | None = None
    nullable: bool = False

    # numbers
    minimum: int | None = None
    maximum: int | None = None
    exclusive_minimum: bool = False
    exclusive_maximum: bool = False

    # Технические поля
    discriminator_base_class_schema: DiscriminatorBaseClassSchema | None = None
    is_fake: bool = False
    is_inline: bool = False

    @property
    def is_nullable(self) -> bool:
        return self.nullable is True or Type.null in self.type

    @property
    def required_properties(self) -> list[SchemaProperty]:
        if not self.required:
            return []

        return [p for p in self.properties if p.orig_key in self.required]

    @property
    def optional_properties(self) -> list[SchemaProperty]:
        if not self.required:
            return self.properties

        return [p for p in self.properties if p.orig_key not in self.required]

    @property
    def inline_allof_models(self) -> list[SchemaObject]:
        return [item for item in self.all_of if item.is_inline]

    @property
    def named_allof_models(self) -> list[SchemaObject]:
        return [item for item in self.all_of if not item.is_inline]

    @property
    def is_single_allof_ref_obj(self) -> bool:
        return self.id.endswith("_ref_obj") and len(self.all_of) == 1

    @property
    def is_single_oneof_obj(self) -> bool:
        return self.id.endswith("_obj") and len(self.one_of) == 1

    @property
    def is_empty_object(self) -> bool:
        return all(
            (
                self.type == Type.object,
                not self.is_fake,
                not self.enum,
                not self.items,
                not self.properties,
                not self.required,
                not self.all_of,
                not self.any_of,
                not self.one_of,
                not self.discriminator,
            )
        )

    @property
    def is_empty_properties(self) -> bool:
        return all(
            (
                not self.properties,
                not self.required,
                not self.all_of,
                not self.any_of,
                not self.one_of,
            )
        )


@dataclass
class ParameterObject(SafetyKeyMixin):
    """
    https://swagger.io/specification/#parameter-object
    """

    id: str
    orig_key: str
    safety_key: str | None
    description: str | None
    location: ParameterLocation
    required: bool
    schema: SchemaObject


@dataclass
class RequestBodyObject:
    """
    https://swagger.io/specification/#request-body-object
    """

    id: str
    description: str | None
    schema: SchemaObject
    required: bool
    is_form_data: bool
    is_multipart_form_data: bool
    are_files_required: bool


@dataclass
class OperationObject:
    """
    https://swagger.io/specification/#operation-object
    """

    method: HttpMethod
    summary: str | None
    description: str | None
    operation_id: str | None
    request_body: RequestBodyObject | None
    responses: ResponsesObject
    parameters: list[ParameterObject]
    path_str: str

    @property
    def path_params(self) -> list[ParameterObject]:
        return [parameter for parameter in self.parameters if parameter.location == ParameterLocation.path]

    @property
    def query_params(self) -> list[ParameterObject]:
        return [parameter for parameter in self.parameters if parameter.location == ParameterLocation.query]

    @property
    def headers(self) -> list[ParameterObject]:
        return [parameter for parameter in self.parameters if parameter.location == ParameterLocation.header]

    @property
    def fn_name(self) -> str | None:
        if self.operation_id is not None:
            return _ensure_correct_underscore_identifier(self.operation_id)

        return f"{self.method.value.lower()}_{_ensure_correct_underscore_identifier(self.path_str)}"


@dataclass
class PathItemObject:
    """
    https://swagger.io/specification/#path-item-object
    """

    summary: str | None
    description: str | None
    operations: dict[HttpMethod, OperationObject]


@dataclass
class ResponseObject:
    id: str
    description: str
    status_code: int
    schema: SchemaObject | None


@dataclass
class ResponsesObject:
    patterned: dict[str, ResponseObject]


@dataclass
class Document:
    info: InfoObject
    paths: dict[str, PathItemObject]
    parameters: dict[str, ParameterObject]
    schemas: dict[str, SchemaObject]

    discriminator_base_class_schemas: list[DiscriminatorBaseClassSchema]

    def _build_sorted_schemas(self, keys: list[str], exclude_enums: bool = False):
        sorted: list[str] = []
        key_for_processing = set(keys)
        while keys:
            key = keys.pop()
            if key in sorted:
                index = sorted.index(key)
            else:
                sorted.append(key)
                index = len(sorted) - 1

            schema = self.schemas[key]

            self._add_one_of_items_in_sorted(schema, key_for_processing, index, sorted)
            self._add_all_of_items_in_sorted(schema, key_for_processing, index, sorted)

            for property in schema.properties:
                if property.schema.id in key_for_processing and property.schema.id not in sorted:
                    sorted.insert(index, property.schema.id)
                    self._add_one_of_items_in_sorted(property.schema, key_for_processing, index, sorted)
                    self._add_all_of_items_in_sorted(property.schema, key_for_processing, index, sorted)
                if property.schema.items:
                    if isinstance(property.schema.items, list):
                        for items in property.schema.items:
                            if items.id in self.schemas:
                                sorted.insert(index, items.id)
                    elif property.schema.items.id in self.schemas:
                        sorted.insert(index, property.schema.items.id)
        sorted_schemas = []
        for key in sorted:
            if self.schemas[key] not in sorted_schemas:
                sorted_schemas.append(self.schemas[key])

        if exclude_enums:
            sorted_schemas = [s for s in sorted_schemas if s.enum is None]
        return sorted_schemas

    def _add_all_of_items_in_sorted(self, schema, key_for_processing, index, sorted):
        for all_of_item in schema.all_of:
            if all_of_item.id in key_for_processing:
                sorted.insert(index, all_of_item.id)


    def _add_one_of_items_in_sorted(self, schema, key_for_processing, index, sorted):
        for one_of_item in schema.one_of:
            if one_of_item.id in key_for_processing:
                sorted.insert(index, one_of_item.id)

    @property
    def sorted_schemas(self) -> list[SchemaObject]:
        keys = [
            key
            for key, schema in self.schemas.items()
            if schema.enum is None and not schema.type.is_primitive and not schema.is_single_allof_ref_obj and not schema.is_single_oneof_obj
        ]
        return self._build_sorted_schemas(keys, exclude_enums=True)

    @property
    def sorted_enums(self) -> list[SchemaObject]:
        keys = [key for key, schema in self.schemas.items() if schema.enum is not None]
        return self._build_sorted_schemas(keys)


@dataclass
class DiscriminatorBaseClassSchema:
    name: str
    attr: str


@dataclass
class Discriminator:
    property_name: str
    mapping: dict[str, SchemaObject]

@dataclass
class HttpMethodObject:
    name: str
    method: HttpMethod
    params: MethodParams

@dataclass
class MethodParams:
    params_name: str | None = None
    query_params: dict[str, Any | None] = dict
    path_params: dict[str, Any | None] = dict
    body: dict[str, Any] = dict
    body_name: str | None = None

class ValueContext(Enum):
    param = "param"
    body = "body"
