"""
Отвечает за всё, что необходимо сделать (сгенерировать файлы
зависимостей, инициализаций, конфигураций), чтобы сгенерированный
клиент можно было упаковать в пакет.
"""

import dataclasses
import datetime
import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.parse import urlencode
from urllib.parse import urljoin

from jinja2 import Environment
from jinja2 import FileSystemLoader
from pydantic import HttpUrl

from pythogen import models
from pythogen import settings
from pythogen.models import SchemaProperty
from pythogen.renderer import classname, j2_is_optional_response, j2_typerepr, varname, j2_responserepr
from pythogen.renderer import prepare_operations


@dataclasses.dataclass
class InitPackageResponse:
    client_output_path: str


class RawRepr(str):
    """строка, которую вставляем в repr без кавычек"""

    pass


def init_package(
    *, package_name: str, client_name: str, doc_link: str, base_url: str, repo_url: str, author_name: str,
    author_email: str, output_path: Path, document: models.Document, line_length: int,
) -> None:
    env = Environment(
        loader=FileSystemLoader(settings.HTTP_PACKAGE_TEMPLATES_DIR_PATH), extensions=["jinja2.ext.loopcontrols"]
    )
    globals_dict = {
        "classname": classname,
        "varname": varname,
        "mock_response_repr": mock_response_repr,
        "query_params_repr": query_params_repr,
        "path_params_repr": path_params_repr,
        "body_repr": body_repr,
        "headers_repr": headers_repr,
        "assertions": j2_assertions,
        "url_repr": url_repr,
        "match_content_repr": match_content_repr,
        "match_headers_repr": match_headers_repr,
        "typerepr": j2_typerepr,
        "responserepr": j2_responserepr,
        "is_optional_response": j2_is_optional_response,
        "urljoin": urljoin,
    }
    prepared_operations = prepare_operations(document)
    output_path.mkdir(parents=True, exist_ok=True)
    for path, _, files in os.walk(settings.HTTP_PACKAGE_TEMPLATES_DIR_PATH):
        for file in files:
            if not file.endswith(".j2") or file.startswith("!"):
                continue

            filepath = (Path(path) / file).relative_to(settings.HTTP_PACKAGE_TEMPLATES_DIR_PATH)
            output_path_file = output_path / filepath.with_suffix("")

            template = env.get_template(
                filepath.as_posix(),
                globals=globals_dict,
            )

            _render_template(
                document,
                template=template,
                package_name=package_name,
                client_name=client_name,
                doc_link=doc_link,
                base_url=base_url,
                repo_url=repo_url,
                author_name=author_name,
                author_email=author_email,
                line_length=line_length,
                output_path=output_path_file,
                prepared_operations=prepared_operations,
                models=document.sorted_schemas,
                enums=document.sorted_enums,
            )


def _render_template(
    document,
    template,
    package_name,
    client_name,
    doc_link,
    base_url,
    repo_url,
    author_name,
    author_email,
    line_length,
    output_path,
    prepared_operations,
    models,
    enums,
):
    rendered_file = template.render(
        document=document,
        service_name=package_name.split(".")[-1],
        package_name=package_name.replace(".", "_"),
        package_import_path=package_name,
        package_path=package_name.replace(".", "/"),
        client_name=client_name,
        doc_link=doc_link,
        base_url=base_url,
        repo_url=repo_url,
        author_name=author_name,
        author_email=author_email,
        line_length=line_length,
        get=prepared_operations.get,
        post=prepared_operations.post,
        patch=prepared_operations.patch,
        put=prepared_operations.put,
        delete=prepared_operations.delete_no_body,
        head=prepared_operations.head,
        operations=prepared_operations.all(),
        models=models,
        enums=enums,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(rendered_file)

def get_prop_mapping(document: models.Document):
    props = {}
    for schema in document.sorted_schemas:
        props[classname(schema.id)] = schema.required_properties + schema.optional_properties

    return props


def mock_response_repr(operation: models.OperationObject, document: models.Document):
    prop_mapping = get_prop_mapping(document)
    sorted_responses = sorted(operation.responses.patterned.values(), key=lambda response: response.status_code)
    for response in sorted_responses:
        if 200 <= response.status_code < 300:
            response_repr = prefix_mock_resp(response.schema) + handle_response_for_repr(
                response, prop_mapping, mode="json"
            )
            return response_repr
        else:
            print("Unsuccessful response not implemented")
            return "json={}"

    return "json={}"


def handle_response_for_repr(
    response: models.ResponseObject, prop_mapping: dict[str, list[models.SchemaProperty]], mode: str
):
    used = set()
    cache = {}
    response_schema = response.schema

    if response_schema:
        response_type = response_schema.type
    else:
        value = "{}"
        return value

    if response_schema.enum:
        return f"{response_schema.enum[0]!r}"

    if response_type.is_primitive:
        value = handle_primitive_type(response_schema, mode, context=models.ValueContext.body)
        return repr(value)

    if response_type == models.Type.array:
        value = handle_array_json_type(response_schema, prop_mapping, used, cache, mode, context=models.ValueContext.body)
        return str(value)

    if response_type == models.Type.object:
        value = handle_object_json_type(response_schema, prop_mapping, used, cache, mode, context=models.ValueContext.body)
        return str(value)

    raise TypeError("Unknown response type")


def prefix_mock_resp(response_schema: models.SchemaObject):
    if response_schema and response_schema.type.is_primitive:
        return "content="
    else:
        return "json="


def match_content_repr(operation: models.OperationObject, document: models.Document):
    prop_mapping = get_prop_mapping(document)
    used = set()
    cache = {}
    body = operation.request_body
    body_schema = body.schema
    body_type = body_schema.type

    if body_schema.enum:
        value = body_schema.enum[0]
        if isinstance(value, bytes):
            data = value
        else:
            data = (
                value.encode("utf-8") if isinstance(value, str) or isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode("utf-8")
            )
        return _bytes_literal_chunks(data)

    if body_type.is_primitive:
        value = handle_primitive_type(body_schema, mode="json", context=models.ValueContext.body)
        if isinstance(value, bytes):
            data = value
        else:
            data = (
                value.encode("utf-8") if isinstance(value, str) else json.dumps(value, ensure_ascii=False).encode("utf-8")
            )
        return _bytes_literal_chunks(data)

    if body_type == models.Type.array:
        value = handle_array_json_type(body_schema, prop_mapping, used, cache, mode="json", context=models.ValueContext.body)
        return _bytes_literal_chunks(json.dumps(value, ensure_ascii=False).encode("utf-8"))

    if body_type == models.Type.object:
        value = handle_object_json_type(body_schema, prop_mapping, used, cache, mode="json", context=models.ValueContext.body)
        return _bytes_literal_chunks(json.dumps(value, ensure_ascii=False).encode("utf-8"))

    raise ValueError("Unsupported content type")


def match_headers_repr(operation, document):
    prop_mapping = get_prop_mapping(document)
    headers = operation.headers

    sid = classname(operation.fn_name) + "Headers"
    props = []
    for header in headers:
        prop = models.SchemaProperty(orig_key=header.orig_key, safety_key=header.safety_key, schema=header.schema)
        props.append(prop)
    prop_mapping[sid] = props
    stub_schema = models.SchemaObject(
        id=sid,
        title=None,
        enum=None,
        type=models.SchemaType(models.Type.object),
        format=None, items=None,
        properties=props,
        default=models.UNDEFINED
    )
    used = set()
    cache = {}
    value = handle_object_json_type(stub_schema, prop_mapping, used, cache, mode="obj", context=models.ValueContext.param)
    return f"match_headers={value}"


def url_repr(operation, document, base_url, path):
    prop_mapping = get_prop_mapping(document)
    path_params = {}
    for param in operation.path_params:
        value = get_param_value(param.schema, prop_mapping)
        path_params[param.orig_key] = value

    path = path.format(**path_params)

    query_params = {}
    for param in operation.query_params:
        value = get_param_value(param.schema, prop_mapping)
        query_params[param.orig_key] = value

    url = urljoin(base_url, path)
    if query_params:
        url += "?" + urlencode(query_params, quote_via=lambda s, safe, encoding, errors: quote(s, safe="+"))

    return f'url="{url}"'


def get_param_value(schema: models.SchemaObject, prop_mapping: dict[str, list[models.SchemaProperty]]):
    used = set()
    cache = {}
    if schema.enum:
        return schema.enum[0]

    if schema.type == models.Type.any:
        return None

    elif schema.type.is_primitive:
        return handle_primitive_type(schema, mode="obj", context=models.ValueContext.param)

    elif schema.type == models.Type.array:
        return handle_array_type(schema, prop_mapping, used, cache, context=models.ValueContext.param)

    else:
        raise TypeError(f"Unsupported type {schema.type}")

def handle_primitive_type(schema: models.SchemaObject, mode: str, context: models.ValueContext):
    values = {
        models.Type.string: "string",
        models.Type.number: 42.0,
        models.Type.integer: 42,
        models.Type.boolean: True,
    }
    param_type = schema.type
    if len(param_type) > 1:
        param_type = param_type[0]

    if param_type == models.Type.string and schema.format:
        value = handle_string_format_type(schema, mode)
    else:
        value = values[param_type]

    if context == models.ValueContext.param and value == "string":
        value += "_param"
    return value


def handle_string_format_type(schema: models.SchemaObject, mode: str):
    values = {
        models.Format.datetime: datetime.datetime(2005, 10, 10).isoformat()
        if mode == "json"
        else datetime.datetime(2005, 10, 10),
        models.Format.date: datetime.date(2009, 1, 26).isoformat() if mode == "json" else datetime.date(2009, 1, 26),
        models.Format.time: str(datetime.time(hour=13, minute=37)) if mode == "json" else datetime.time(hour=13, minute=37),
        models.Format.datespan: str(datetime.timedelta(hours=13, minutes=37)) if mode == "json" else datetime.timedelta(hours=13, minutes=37),
        models.Format.duration: str(datetime.timedelta(hours=13, minutes=37)) if mode == "json" else datetime.timedelta(hours=13, minutes=37),
        models.Format.binary: b"bytes",
        models.Format.byte: "string",
        models.Format.uri: "http://www.example.com/" if mode == "json" else HttpUrl("http://www.example.com/"),
        models.Format.uuid: "string",
        models.Format.guid: "string",
        models.Format.ipvanynetwork: "192.168.1.0/24",
    }
    param_format = schema.format
    if param_format in values.keys():
        return values[param_format]
    else:
        raise TypeError(f"Unsupported format: {param_format}")


def handle_array_type(
    schema: models.SchemaObject,
    prop_mapping: dict[str, list[models.SchemaProperty]],
    used: set[str],
    cache: dict[str, object],
    context: models.ValueContext
):
    if not schema.items:
        return []

    value = handle_property(schema.items, prop_mapping, used, cache, context)
    if isinstance(value, RawRepr) and value in ("None", "{}", "[]", "") or value in (None, {}, []):
        return "[]"

    return f"[{value if isinstance(value, RawRepr) else repr(value)}]"


def handle_object_type(
    schema: models.SchemaObject,
    prop_mapping: dict[str, list[models.SchemaProperty]],
    used: set[str],
    cache: dict[str, object],
    context: models.ValueContext
):
    if schema.id == "<inline+SchemaObject>":
        return {}

    sid = classname(schema.id)

    if not schema.properties and not prop_mapping[sid]:
        return {}

    if sid in used:
        return None

    if sid in cache:
        return cache[sid]

    used.add(sid)

    if not schema.properties and sid not in prop_mapping.keys():
        result = None

    else:
        properties = prop_mapping.get(sid, schema.required_properties + schema.optional_properties)
        params = {}
        for prop in properties:
            params[prop.key] = handle_property(prop.schema, prop_mapping, used, cache, context)
        result = make_object_repr(sid, params)
    cache[sid] = result
    used.remove(sid)
    return result


def handle_property(
    schema: models.SchemaObject,
    prop_mapping: dict[str, list[models.SchemaProperty]],
    used: set[str],
    cache: dict[str, object],
    context: models.ValueContext
):
    if schema.enum:
        return schema.enum[0]

    if schema.type == models.Type.any:
        return None

    elif schema.type.is_primitive:
        return handle_primitive_type(schema, mode="obj", context=context)

    elif schema.type == models.Type.array:
        return RawRepr(handle_array_type(schema, prop_mapping, used, cache, context))

    elif schema.type == models.Type.object:
        return RawRepr(handle_object_type(schema, prop_mapping, used, cache, context))

    else:
        raise TypeError(f"Unsupported type {schema.type}")


def make_object_repr(class_name: str, params: dict) -> str:
    parts = []
    for key, value in params.items():
        if isinstance(value, RawRepr):
            parts.append(f"{key}={value}")
        else:
            parts.append(f"{key}={value!r}")
    args_str = ", ".join(parts)
    return f"{class_name}({args_str})"


def handle_array_json_type(
    schema: models.SchemaObject,
    prop_mapping: dict[str, list[SchemaProperty]],
    used: set[str],
    cache: dict[str, object],
    mode: str,
    context: models.ValueContext
):
    if not schema.items:
        return []

    value = handle_property_json(schema.items, prop_mapping, used, cache, mode, context)

    if value == {}:
        return []
    return [value]


def handle_object_json_type(
    schema: models.SchemaObject,
    prop_mapping: dict[str, list[models.SchemaProperty]],
    used: set[str],
    cache: dict[str, object],
    mode: str,
    context: models.ValueContext
):
    sid = classname(schema.id)

    if sid in used:
        return {}

    if sid in cache:
        return cache[sid]

    used.add(sid)

    if not schema.properties and sid not in prop_mapping.keys():
        result = {}

    else:
        properties = prop_mapping.get(sid, schema.required_properties + schema.optional_properties)
        result = {}
        for prop in properties:
            if mode == "json":
                key = prop.orig_key
            else:
                key = prop.key
            result[key] = handle_property_json(prop.schema, prop_mapping, used, cache, mode, context=context)

    cache[sid] = result
    used.remove(sid)
    return result


def handle_property_json(
    schema: models.SchemaObject,
    prop_mapping: dict[str, list[models.SchemaProperty]],
    used: set[str],
    cache: dict[str, object],
    mode: str,
    context: models.ValueContext
):
    if schema.enum:
        return schema.enum[0]

    if schema.type == models.Type.any:
        return None

    elif schema.type.is_primitive:
        return handle_primitive_type(schema, mode, context=context)

    elif schema.type == models.Type.array:
        return handle_array_json_type(schema, prop_mapping, used, cache, mode, context)

    elif schema.type == models.Type.object:
        return handle_object_json_type(schema, prop_mapping, used, cache, mode, context)

    else:
        raise TypeError(f"Unsupported type {schema.type}")


def _bytes_literal_chunks(data: bytes, size: int = 80) -> list[str]:
    return [repr(data[i : i + size]) for i in range(0, len(data), size)]


def j2_assertions(operation: models.OperationObject, document: models.Document):
    prop_mapping = get_prop_mapping(document)
    sorted_responses = sorted(operation.responses.patterned.values(), key=lambda response: response.status_code)
    for response in sorted_responses:
        if 200 <= response.status_code < 300:
            expected = handle_response_for_repr(response, prop_mapping, mode="json")
            if not response.schema:
                return "assert result is None"
            if response.schema.type.is_primitive:
                return f"assert result == {expected}"
            return f"assert to_jsonable_python(result) == {expected}"

    return "assert result is None"


def query_params_repr(operation: models.OperationObject, document: models.Document):
    prop_mapping = get_prop_mapping(document)
    query_params = operation.query_params

    sid = classname(operation.fn_name) + "QueryParams"
    props = []
    for param in query_params:
        prop = models.SchemaProperty(orig_key=param.orig_key, safety_key=param.safety_key, schema=param.schema)
        props.append(prop)
    prop_mapping[sid] = props
    stub_schema = models.SchemaObject(
        id=sid,
        title=None,
        enum=None,
        type=models.SchemaType(models.Type.object),
        format=None,
        items=None,
        properties=props,
        default=models.UNDEFINED
    )
    used = set()
    cache = {}
    value = handle_object_type(stub_schema, prop_mapping, used, cache, context=models.ValueContext.param)
    return f"query_params = {value}"


def path_params_repr(operation: models.OperationObject, document: models.Document):
    prop_mapping = get_prop_mapping(document)
    path_params = operation.path_params

    sid = classname(operation.fn_name) + "PathParams"
    props = []
    for param in path_params:
        prop = models.SchemaProperty(orig_key=param.orig_key, safety_key=param.safety_key, schema=param.schema)
        props.append(prop)
    prop_mapping[sid] = props
    stub_schema = models.SchemaObject(
        id=sid,
        title=None,
        enum=None,
        type=models.SchemaType(models.Type.object),
        format=None,
        items=None,
        properties=props,
        default=models.UNDEFINED
    )
    used = set()
    cache = {}
    value = handle_object_type(stub_schema, prop_mapping, used, cache, context=models.ValueContext.param)
    return f"path_params = {value}"


def headers_repr(operation: models.OperationObject, document: models.Document):
    prop_mapping = get_prop_mapping(document)
    headers = operation.headers

    sid = classname(operation.fn_name) + "Headers"
    props = []
    for header in headers:
        prop = models.SchemaProperty(orig_key=header.orig_key, safety_key=header.safety_key, schema=header.schema)
        props.append(prop)
    prop_mapping[sid] = props
    stub_schema = models.SchemaObject(
        id=sid,
        title=None,
        enum=None,
        type=models.SchemaType(models.Type.object),
        format=None,
        items=None,
        properties=props,
        default=models.UNDEFINED
    )
    used = set()
    cache = {}
    value = handle_object_type(stub_schema, prop_mapping, used, cache, models.ValueContext.param)
    return f"headers = {value}"

def body_repr(operation: models.OperationObject, document: models.Document):
    prop_mapping = get_prop_mapping(document)
    body_schema = operation.request_body.schema
    used = set()
    cache = {}
    if body_schema.type.is_primitive:
        if body_schema.enum:
            return f"body = {body_schema.enum[0]!r}"

        value = handle_primitive_type(body_schema, mode="obj", context=models.ValueContext.body)
        return f"body = {value!r}"

    elif body_schema.type == models.Type.array:
        value = handle_array_type(body_schema, prop_mapping, used, cache, context=models.ValueContext.body)
        return f"body = {value}"

    elif body_schema.type == models.Type.object:
        value = handle_object_type(body_schema, prop_mapping, used, cache, context=models.ValueContext.body)
        return f"body = {value}"

    print("Not implemented type")
    return "body = None"

DEFAULT_VALUES_URL = {
    models.Type.string: "string",
    models.Type.integer: 42,
    models.Type.number: 42.0,
    models.Type.boolean: True,
    models.Format.datetime: "2005-10-10+00:00:00",
    models.Format.date: "2009-01-26",
    models.Format.time: "13:37",
    models.Format.datespan: "13:37",
    models.Format.duration: "13:37",
    models.Format.binary: "bytes",
    models.Format.uri: "http://www.example.com/",
    models.Format.uuid: "string",
    models.Format.guid: "string",
    models.Format.ipvanynetwork: "192.168.1.0/24",
}
