"""
Responsible for rendering/generating client code from data
that was parsed from an OpenAPI file.
"""
import copy
import logging
import re
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Iterator, Iterable
from typing import TypeVar

import inflection
from jinja2 import Environment
from jinja2 import FileSystemLoader

from pythogen import models
from pythogen import settings
from pythogen.models import SchemaObject

PathStr = TypeVar("PathStr", bound=str)


logger = logging.getLogger(__name__)


def render_client(
    *,
    document: models.Document,
    name: str,
    package_name: str,
    output_path: Path,
    line_length: int,
) -> None:
    """Отрисовывает сгенерированный клиент на основе j2-шаблонов

    Arguments
    ---------
    document
        Спаршенный в python-объекты OpenApi-файл
    """
    env = Environment(
        loader=FileSystemLoader(settings.HTTP_CLIENT_TEMPLATES_DIR_PATH), extensions=["jinja2.ext.loopcontrols"]
    )

    prepared_operations = prepare_operations(document)
    globals_dict = {
        "varname": varname,
        "classname": classname,
        "typerepr": j2_typerepr,
        "responserepr": j2_responserepr,
        "is_optional_response": j2_is_optional_response,
        "iterresponsemap": iterresponsemap,
        "parameterfield": parameterfield,
        "propertyfield": propertyfield,
        "repranyof": j2_repr_any_of,
        "docstring_lines": docstring_lines,
        "wrap_lines": wrap_lines,
        "line_length": line_length,
        "Type": models.Type,
    }

    output_path.mkdir(parents=True, exist_ok=True)

    for path, _, files in os.walk(settings.HTTP_CLIENT_TEMPLATES_DIR_PATH):
        for file in files:
            if not file.endswith(".j2") or file.startswith("!"):
                continue

            filepath = (Path(path) / file).relative_to(settings.HTTP_CLIENT_TEMPLATES_DIR_PATH)
            output_path_file = output_path / "src" / Path(package_name.replace(".", "/")) / filepath.with_suffix("")

            template = env.get_template(
                filepath.as_posix(),
                globals=globals_dict,
            )

            _render_template(
                template=template,
                document=document,
                prepared_operations=prepared_operations,
                name=name,
                import_path=package_name,
                output_path=output_path_file,
            )


_RE_LINE_BREAKS = re.compile(r"\\r\\n|\\r|\\n|\r\n|\r|\n")


def _replace_line_breaks(text: str, replacement: str) -> str:
    return _RE_LINE_BREAKS.sub(replacement, text).strip(replacement)


def _render_template(template, document, prepared_operations, name, import_path, output_path):
    rendered_client = template.render(
        document=document,
        name=name,
        version=document.info.version,
        enums=document.sorted_enums,
        models=document.sorted_schemas,
        get=prepared_operations.get,
        post=prepared_operations.post,
        patch=prepared_operations.patch,
        post_no_body=prepared_operations.post_no_body,
        put=prepared_operations.put,
        delete_no_body=prepared_operations.delete_no_body,
        head=prepared_operations.head,
        discriminator_base_class_schemas=document.discriminator_base_class_schemas,
        operations=prepared_operations.all(),
        import_path=import_path,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(rendered_client)


@dataclass
class PreparedOperations(Generic[PathStr]):
    get: dict[PathStr, models.OperationObject]
    post: dict[PathStr, models.OperationObject]
    post_no_body: dict[PathStr, models.OperationObject]
    put: dict[PathStr, models.OperationObject]
    patch: dict[PathStr, models.OperationObject]
    delete_no_body: dict[PathStr, models.OperationObject]
    head: dict[PathStr, models.OperationObject]


    def all(self) -> tuple[models.OperationObject, ...]:
        return (
            *self.get.values(),
            *self.post.values(),
            *self.post_no_body.values(),
            *self.put.values(),
            *self.patch.values(),
            *self.delete_no_body.values(),
            *self.head.values(),
        )


def prepare_operations(document: models.Document) -> PreparedOperations:
    prepared_operations: PreparedOperations = PreparedOperations(
        get={},
        post={},
        post_no_body={},
        put={},
        patch={},
        delete_no_body={},
        head={}
    )

    for path, path_item in document.paths.items():
        for method, operation in path_item.operations.items():
            if method is models.HttpMethod.get:
                prepared_operations.get[path] = operation
            elif method is models.HttpMethod.post:
                prepared_operations.post[path] = operation
            elif method is models.HttpMethod.patch:
                prepared_operations.patch[path] = operation
            elif method is models.HttpMethod.put:
                prepared_operations.put[path] = operation
            elif method is models.HttpMethod.delete:
                prepared_operations.delete_no_body[path] = operation
            elif method is models.HttpMethod.head:
                prepared_operations.head[path] = operation
            else:
                logger.error(f'Unable to parse document, "{method}" operations support not implemented yet')

    return prepared_operations


def iterresponsemap(responses: models.ResponsesObject) -> list[tuple[str, str]]:
    mapping = []

    for code, response in responses.patterned.items():
        if response.schema is None:
            mapper = "None"
            mapping.append((code, mapper))
            continue

        schema_type = response.schema.type

        if models.Type.object in schema_type and response.schema.is_empty_object:
            mapper = "response.json()"
            mapping.append((code, mapper))
            continue

        if models.Type.object in schema_type and not response.schema.any_of:
            mapper = f"{classname(response.schema.id)}.model_validate(response.json())"
            mapping.append((code, mapper))
            continue

        if response.schema.any_of:
            items_class_names = [classname(items.id) for items in response.schema.any_of]
            items_class_names_str: str = "[" + ", ".join(items_class_names) + "]"
            mapper = f"self._parse_any_of(response.json(), {items_class_names_str})"
            mapping.append((code, mapper))
            continue

        if schema_type.is_iterable:
            if isinstance(response.schema.items, list):
                items_collection = response.schema.items
            else:
                items_collection = [response.schema.items]  # type: ignore

            for items in items_collection:
                if items is None:
                    mapper = "response.text"
                    mapping.append((code, mapper))
                    continue

                if models.Type.object in items.type:
                    items_class_name = classname(items.id)
                    mapper = f"[{items_class_name}.model_validate(item) for item in response.json()]"
                    mapping.append((code, mapper))
                    continue

                mapper = "response.json()"
                mapping.append((code, mapper))
                continue
            continue

        if models.Type.string in schema_type and response.schema.format is models.Format.binary:
            mapping.append((code, "response.content"))
            continue

        if models.Type.string in schema_type:
            mapping.append((code, "response.text"))
            continue

        if models.Type.integer in schema_type:
            mapping.append((code, "int(response.text)"))
            continue

        if models.Type.any in schema_type:
            mapping.append((code, "response.text"))
            continue

        raise NotImplementedError(
            f"Unable to create response mapping of {response.id} <response.schema.type={response.schema.type}>"
        )

    return mapping


def _collect_success_response_types(
    responses: models.ResponsesObject, document: models.Document
) -> tuple[list[str], list[models.SchemaObject]]:
    types = []
    schemas: list[models.SchemaObject] = []

    for response in responses.patterned.values():
        if 300 > response.status_code >= 200 and response.schema:
            types.append(j2_typerepr(response.schema, document))
            schemas.append(response.schema)

    return sorted(set(types)), schemas


def j2_is_optional_response(responses: models.ResponsesObject, document: models.Document) -> bool:
    types, schemas = _collect_success_response_types(responses, document)
    return len(schemas) > 0 and len(types) == 1 and schemas[0].nullable


def j2_responserepr(responses: models.ResponsesObject, document: models.Document) -> str:
    """Represent method response on j2 template"""
    types, _ = _collect_success_response_types(responses, document)

    if not types:
        return "None"

    elif len(types) == 1:
        if j2_is_optional_response(responses, document):
            return f"{types[0]} | None"
        else:
            return f"{types[0]}"
    else:
        return _generate_type_with_union(types)


def j2_typerepr(schema: models.SchemaObject, document: models.Document, filter_null: bool = False) -> str:
    """Represent data type on j2 template"""
    if schema.type.is_multiple:
        if filter_null and schema.is_nullable:
            types = [type_ for type_ in schema.type if type_ != models.Type.null]
        else:
            types = schema.type
        if not types:
            types = schema.type
        repr_types = _generate_type_with_union(
            [j2_typerepr(_schema_with_type(schema, models.SchemaType(type_)), document) for type_ in types]
        )
        return repr_types

    representation = "dict"

    if schema.type.is_primitive:
        if schema.enum:
            if schema.id == "<inline+SchemaObject>" or schema.id == "<inline+SchemaObject>Item":
                representation = f"Literal{schema.enum}"
            else:
                representation = classname(schema.id)
        elif schema.format in FORMAT_MAPPING:
            representation = FORMAT_MAPPING[schema.format]  # type: ignore
        else:
            representation = PRIMITIVE_TYPE_MAPPING[schema.type]

    elif schema.type == models.Type.object and schema.id != "<inline+SchemaObject>":
        if schema.is_empty_object:
            representation = "dict[Any, Any]"
        else:
            representation = classname(schema.id)

    elif schema.type == models.Type.any:
        representation = "Any"

    elif schema.any_of or schema.one_of:
        representation = classname(schema.id)

    elif (
        schema.type == models.Type.array
        and schema.items
        and isinstance(schema.items, models.SchemaObject)
        and (schema.items.any_of or schema.items.one_of)
    ):
        represented_items = _generate_type_with_union(j2_typerepr(anyof_item, document, False) for anyof_item in (schema.items.any_of or schema.items.one_of))
        representation = f"list[{represented_items}]"

    elif schema.type == models.Type.array and schema.items:
        represented_item = j2_typerepr(schema.items, document)  # type: ignore
        representation = f"list[{represented_item}]"

    elif schema.discriminator:
        representation = _generate_type_with_union(j2_typerepr(item, document) for item in schema.discriminator.mapping.values())

    if schema.all_of and len(schema.all_of) == 1:
        representation = j2_typerepr(schema.all_of[0], document)

    return representation


def j2_repr_any_of(any_of_items: list[models.SchemaObject], document: models.Document) -> str:
    items = []
    for item in any_of_items:
        if item.additional_roperties:
            items.append("dict[Any, Any]")
        elif item.type is models.Type.array and item.items:
            representation = j2_typerepr(item, document)
            items.append(representation)
        elif item.type.is_primitive:
            items.append(PRIMITIVE_TYPE_MAPPING[item.type])
        elif item.is_empty_object:
            items.append("dict[Any, Any]")
        elif item.id:
            items.append(classname(item.id))
        else:
            logger.error(f"j2_repr_any_of unsupported SchemaObject {item}")
    return _generate_type_with_union(items)


def varname(value: str) -> str:
    clean_value = re.sub(r"\W|^(?=\d)", "_", value)  # remove special characters
    clean_value = re.sub("_{2,}", "_", clean_value)  # __ -> _
    clean_value = clean_value.replace(" ", "_")
    return inflection.underscore(clean_value)


_RESERVED_CLASS_NAMES = frozenset({
    "Any",
    "AsyncHttpxTransport",
    "AsyncService",
    "BaseAsyncTransport",
    "BaseConfig",
    "BaseModel",
    "BaseTransport",
    "BinaryIO",
    "Callable",
    "ConfigDict",
    "Enum",
    "ErrorHandler",
    "Field",
    "Header",
    "HttpUrl",
    "HttpxTransport",
    "IO",
    "IPvAnyNetwork",
    "Iterable",
    "Iterator",
    "Literal",
    "Mapping",
    "Protocol",
    "Response",
    "RootModel",
    "Sequence",
    "Service",
    "Type",
    "ValidationInfo",
})


_RE_SPECIAL_CHARACTERS = re.compile(r"\W|^(?=\d)")
_RE_REPEATING_UNDERSCORES = re.compile(r"_{2,}")


def classname(value: str) -> str:
    clean_value = _RE_SPECIAL_CHARACTERS.sub("_", value)
    clean_value = _RE_REPEATING_UNDERSCORES.sub("_", clean_value)
    clean_value = clean_value.strip("_")
    clean_value = inflection.camelize(clean_value)
    clean_value = models.ensure_not_reserved_identifier(clean_value, reserved=_RESERVED_CLASS_NAMES, suffix="Model")
    return clean_value


def parameterfield(parameter: models.ParameterObject) -> str:
    args: list[str] = []

    if not parameter.required:
        args.append("MISSING")

    if parameter.safety_key != parameter.orig_key:
        args.append(f'alias="{parameter.orig_key}"')

    if parameter.description:
        args.append(f'description="{_replace_line_breaks(parameter.description, replacement=" ")}"')

    if parameter.schema.discriminator:
        args.append(f'discriminator="{parameter.schema.discriminator.property_name}"')

    return "Field(" + ", ".join(args) + ")"


def propertyfield(schema_property: models.SchemaProperty, parent_schema: models.SchemaObject) -> str:
    args: list[str] = []

    if schema_property.schema.default is not models.UNDEFINED:
        args.append(repr(schema_property.schema.default))
    elif schema_property.orig_key not in parent_schema.required:
        args.append("MISSING")
    else:
        args.append("...")

    if schema_property.schema.minimum is not None:
        if schema_property.schema.exclusive_minimum:
            args.append(f"gt={schema_property.schema.minimum}")
        else:
            args.append(f"ge={schema_property.schema.minimum}")

    if schema_property.schema.maximum is not None:
        if schema_property.schema.exclusive_maximum:
            args.append(f"lt={schema_property.schema.maximum}")
        else:
            args.append(f"le={schema_property.schema.maximum}")

    if schema_property.safety_key and schema_property.safety_key != schema_property.orig_key:
        args.append(f'alias="{schema_property.orig_key}"')

    if not schema_property.safety_key and varname(schema_property.orig_key) != schema_property.orig_key:
        args.append(f'alias="{schema_property.orig_key}"')

    if schema_property.schema.description:
        args.append(f'description="{_replace_line_breaks(schema_property.schema.description, replacement=" ")}"')

    if schema_property.schema.discriminator:
        args.append(f'discriminator="{schema_property.schema.discriminator.property_name}"')

    if args == ["MISSING"]:
        return "= Field(MISSING)"

    if args == ["..."]:
        return ""

    return "= Field(" + ", ".join(args) + ")"


def wrap_lines(lines: Iterable[str], maxlength: int) -> Iterator[str]:
    for line in lines:
        while len(line) > maxlength:
            space = line.rfind(" ", 0, maxlength + 1)

            if space == -1:
                yield line[:maxlength]
                line = line[maxlength:]
                continue

            yield line[:space].rstrip()
            line = line[space:].lstrip()

        yield line


def docstring_lines(model: SchemaObject) -> Iterator[str]:
    if model.title or model.description:
        yield '"""'

        if model.title:
            yield model.title

        if model.description:
            for line in _replace_line_breaks(model.description, replacement=os.linesep).splitlines():
                yield line

        yield '"""'


PRIMITIVE_TYPE_MAPPING = {
    models.Type.integer: "int",
    models.Type.number: "float",
    models.Type.boolean: "bool",
    models.Type.string: "str",
    models.Type.null: "None",
}

FORMAT_MAPPING = {
    models.Format.binary: "bytes",
    models.Format.uri: "HttpUrl",
    models.Format.date: "datetime.date",
    models.Format.time: "datetime.time",
    models.Format.datetime: "datetime.datetime",
    models.Format.datespan: "datetime.timedelta",
    models.Format.duration: "datetime.timedelta",
    models.Format.ipvanynetwork: "IPvAnyNetwork"
}


def _generate_type_with_union(types: Iterable[str]) -> str:
    types_list = list(types)
    if len(types_list) == 1:
        return types_list[0]
    return f"{' | '.join(types_list)}"

def _schema_with_type(schema: models.SchemaObject, type_: models.SchemaType) -> models.SchemaObject:
    schema_copy = copy.copy(schema)
    schema_copy.type = type_
    return schema_copy
