from pathlib import Path
from urllib.parse import urljoin

import pytest
from pythogen import models
from pythogen.renderer import classname, j2_is_optional_response, j2_typerepr, j2_responserepr, iterresponsemap, \
    prepare_operations, varname
from pythogen.packager import (mock_response_repr, query_params_repr, path_params_repr, headers_repr, body_repr,
                               j2_assertions, url_repr, match_headers_repr, match_content_repr)
from jinja2 import Environment
from jinja2 import FileSystemLoader

from tests.pythogen.model_factories import make_document, make_schema, make_operation_with_body, \
    make_operation_with_response, make_param_obj, make_responses

TEMPLATE_DIR_PATH = Path(__file__).parent.parent.parent.absolute() / Path(
    "pythogen/templates/http_client_package/tests/client_tests")
METHOD_TEMPLATE_NAME = "!test_method.j2"
ERROR_METHOD_TEMPLATE_NAME = "!test_error_method.j2"
TEST_TEMPLATE_NAME = "!test.j2"
METHODS = (
    models.HttpMethod.get,
    models.HttpMethod.post,
    models.HttpMethod.put,
    models.HttpMethod.patch,
    models.HttpMethod.delete,
    models.HttpMethod.head
)
PRIMITIVE_TYPES = (
    models.Type.string,
    models.Type.integer,
    models.Type.number,
    models.Type.boolean,
    models.Type.null,
)
FORMATS = (
    models.Format.date,
    models.Format.datetime,
    models.Format.datespan,
    models.Format.binary,
    models.Format.uri
)

GLOBALS_DICT = {
        "varname": varname,
        "classname": classname,
        "typerepr": j2_typerepr,
        "responserepr": j2_responserepr,
        "is_optional_response": j2_is_optional_response,
        "iterresponsemap": iterresponsemap,
        "mock_response_repr": mock_response_repr,
        "query_params_repr": query_params_repr,
        "path_params_repr": path_params_repr,
        "headers_repr": headers_repr,
        "body_repr": body_repr,
        "assertions": j2_assertions,
        "url_repr": url_repr,
        "match_headers_repr": match_headers_repr,
        "match_content_repr": match_content_repr,
        "urljoin": urljoin,
    }

@pytest.fixture(scope="module", autouse=True)
def method_template():
    assert (TEMPLATE_DIR_PATH / METHOD_TEMPLATE_NAME).exists
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR_PATH), extensions=["jinja2.ext.loopcontrols"])
    template = env.get_template(
        METHOD_TEMPLATE_NAME,
        globals=GLOBALS_DICT,
    )
    return template

@pytest.fixture(scope="module", autouse=True)
def error_method_template():
    assert (TEMPLATE_DIR_PATH / ERROR_METHOD_TEMPLATE_NAME).exists
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR_PATH), extensions=["jinja2.ext.loopcontrols"])
    template = env.get_template(
        ERROR_METHOD_TEMPLATE_NAME,
        globals=GLOBALS_DICT,
    )
    return template

@pytest.fixture(scope="module", autouse=True)
def test_template():
    assert (TEMPLATE_DIR_PATH / TEST_TEMPLATE_NAME).exists
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR_PATH), extensions=["jinja2.ext.loopcontrols"])
    template = env.get_template(
        TEST_TEMPLATE_NAME,
        globals=GLOBALS_DICT,
    )
    return template

def test_simple_pydantic_model_response(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"]
    )
    document = make_document(resp_schema, prop_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    response_model = RespSchema
    resp_schema_factory = ModelFactory.create_factory(
        model=response_model, __use_defaults__=True
    )
    result_obj = resp_schema_factory.build()
    result_json = to_jsonable_python(result_obj)
    httpx_mock.add_response(
        method="get",
        json=result_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_nullable_pydantic_model_response(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"],
        nullable=True,
    )
    document = make_document(resp_schema, prop_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    class RespGetSchemaNullable(RootModel[RespSchema | None]): ...
    resp_get_schema_nullable_factory = ModelFactory.create_factory(
        model=RespGetSchemaNullable, __use_defaults__=True
    )
    result_obj = resp_get_schema_nullable_factory.build().root
    result_json = to_jsonable_python(result_obj)
    httpx_mock.add_response(
        method="get",
        json=result_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_pydantic_model_with_missing_response(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
    )
    document = make_document(resp_schema, prop_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    response_model = RespSchema
    resp_schema_factory = ModelFactory.create_factory(
        model=response_model, __use_defaults__=True
    )
    result_obj = resp_schema_factory.build()
    result_json = to_jsonable_python(result_obj)
    httpx_mock.add_response(
        method="get",
        json=result_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_pydantic_model_array_response(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    item_schema = make_schema(
        id_="item-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"]
    )
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.array),
        items=item_schema,
    )
    document = make_document(resp_schema, item_schema, prop_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    response_model = ItemSchema
    item_schema_list_factory = ModelFactory.create_factory(
        model=response_model, __use_defaults__=True
    )
    result_obj = item_schema_list_factory.batch(size=3)
    result_json = to_jsonable_python(result_obj)
    httpx_mock.add_response(
        method="get",
        json=result_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_string_response(method_template) -> None:
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.string),
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    class RespStr(RootModel[str]): ...
    resp_str_factory = ModelFactory.create_factory(
        model=RespStr, __use_defaults__=True
    )
    result_obj = resp_str_factory.build().root
    httpx_mock.add_response(
        method="get",
        text=str(result_obj),
        url="{base_url}/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_nullable_string_response(method_template) -> None:
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.string),
        nullable=True,
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    class RespStr(RootModel[str | None]): ...
    resp_str_factory = ModelFactory.create_factory(
        model=RespStr, __use_defaults__=True
    )
    result_obj = resp_str_factory.build().root
    httpx_mock.add_response(
        method="get",
        text=str(result_obj),
        url="{base_url}/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_integer_response(method_template) -> None:
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.integer),
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    class RespInt(RootModel[int]): ...
    resp_int_factory = ModelFactory.create_factory(
        model=RespInt, __use_defaults__=True
    )
    result_obj = resp_int_factory.build().root
    httpx_mock.add_response(
        method="get",
        text=str(result_obj),
        url="{base_url}/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_bytes_response(method_template) -> None:
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.string),
        format_=models.Format.binary
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    class RespBytes(RootModel[bytes]): ...
    resp_bytes_factory = ModelFactory.create_factory(
        model=RespBytes, __use_defaults__=True
    )
    result_obj = resp_bytes_factory.build().root
    httpx_mock.add_response(
        method="get",
        content=result_obj,
        url="{base_url}/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_none_response(method_template) -> None:
    document = make_document()
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=None
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    result_obj = None
    httpx_mock.add_response(
        method="get",
        content=b"",
        url="{base_url}/test"
    )
    result = client.get_schema(
    )  # type: ignore[func-returns-value]
    assert result == result_obj"""
    assert rendered_file == expected

def test_list_of_primitives_response(method_template) -> None:
    item_schema = make_schema(
        id_="item-schema",
        type_=models.SchemaType(models.Type.string),
    )
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.array),
        items=item_schema,
    )
    document = make_document(resp_schema, item_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    class RespStrList(RootModel[list[str]]): ...
    resp_str_list_factory = ModelFactory.create_factory(
        model=RespStrList, __use_defaults__=True
    )
    result_obj = resp_str_list_factory.build().root
    result_json = to_jsonable_python(result_obj)
    httpx_mock.add_response(
        method="get",
        json=result_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_empty_schema_response(method_template) -> None:
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.object),
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    result_obj: dict[Any, Any] = {{}}
    result_json = to_jsonable_python(result_obj)
    httpx_mock.add_response(
        method="get",
        json=result_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_match_headers(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"]
    )
    header_schema = make_schema(
        id_="header-schema",
        type_=models.SchemaType(models.Type.string),
    )
    headers = make_param_obj(
        id_="headers",
        orig_key="headers",
        location=models.ParameterLocation.header,
        schema=header_schema
    )
    document = make_document(resp_schema, prop_schema, header_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    operation.parameters.append(headers)
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    headers_model = GetSchemaHeaders
    get_schema_headers_factory = ModelFactory.create_factory(
        model=headers_model, __use_defaults__=True
    )
    headers_obj = get_schema_headers_factory.build()
    headers_json = to_jsonable_python(headers_obj, by_alias=False)
    response_model = RespSchema
    resp_schema_factory = ModelFactory.create_factory(
        model=response_model, __use_defaults__=True
    )
    result_obj = resp_schema_factory.build()
    result_json = to_jsonable_python(result_obj)
    httpx_mock.add_response(
        method="get",
        json=result_json,
        match_headers=headers_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
        headers=headers_obj,
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_match_body_json(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    body_schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"]
    )
    document = make_document(prop_schema, body_schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        body_schema=body_schema,
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    body_model = BodySchema
    body_schema_factory = ModelFactory.create_factory(
        model=body_model, __use_defaults__=True
    )
    body_obj = body_schema_factory.build()
    body_json = to_jsonable_python(body_obj)
    result_obj = None
    httpx_mock.add_response(
        method="get",
        content=b"",
        match_json=body_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
        body = body_obj,
    )  # type: ignore[func-returns-value]
    assert result == result_obj"""
    assert rendered_file == expected

def test_match_files_multipart(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    body_schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"]
    )
    document = make_document(prop_schema, body_schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        body_schema=body_schema,
    )
    operation.request_body.is_multipart_form_data = True
    operation.request_body.are_files_required = True
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    files_obj: dict[str, BinaryIO | tuple[str, BinaryIO, str]] = {{
        "file": ("test.txt", io.BytesIO(b"test"), "text/plain"),
    }}
    result_obj = None
    httpx_mock.add_response(
        method="get",
        content=b"",
        url="{base_url}/test"
    )
    result = client.get_schema(
        files=files_obj,
    )  # type: ignore[func-returns-value]
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    request_content = requests[0].read()
    assert b'filename="test.txt"' in request_content
    assert b"\\r\\n\\r\\ntest\\r\\n" in request_content
    assert result == result_obj"""
    assert rendered_file == expected

def test_match_files_multipart_and_binary_response(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    body_schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"]
    )
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.string),
        format_=models.Format.binary
    )
    document = make_document(prop_schema, body_schema, resp_schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        body_schema=body_schema,
    )
    operation.request_body.is_multipart_form_data = True
    operation.request_body.are_files_required = True
    operation.responses = make_responses(resp_schema)
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    files_obj: dict[str, BinaryIO | tuple[str, BinaryIO, str]] = {{
        "file": ("test.txt", io.BytesIO(b"test"), "text/plain"),
    }}
    class RespBytes(RootModel[bytes]): ...
    resp_bytes_factory = ModelFactory.create_factory(
        model=RespBytes, __use_defaults__=True
    )
    result_obj = resp_bytes_factory.build().root
    httpx_mock.add_response(
        method="get",
        content=result_obj,
        url="{base_url}/test"
    )
    result = client.get_schema(
        files=files_obj,
    )
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    request_content = requests[0].read()
    assert b'filename="test.txt"' in request_content
    assert b"\\r\\n\\r\\ntest\\r\\n" in request_content
    assert result == result_obj"""
    assert rendered_file == expected

def test_match_body_primitive(method_template) -> None:
    body_schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.string),
    )
    document = make_document(body_schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        body_schema=body_schema,
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    class BodyStr(RootModel[str]): ...
    body_str_factory = ModelFactory.create_factory(
        model=BodyStr, __use_defaults__=True
    )
    body_obj = body_str_factory.build().root
    body_content = str(body_obj).encode()
    result_obj = None
    httpx_mock.add_response(
        method="get",
        content=b"",
        match_content=body_content,
        url="{base_url}/test"
    )
    result = client.get_schema(
        body = body_obj,
    )  # type: ignore[func-returns-value]
    assert result == result_obj"""
    assert rendered_file == expected

def test_match_body_list_of_primitives(method_template) -> None:
    item_schema = make_schema(
        id_="item-schema",
        type_=models.SchemaType(models.Type.string),
    )
    body_schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.array),
        items=item_schema,
    )
    document = make_document(body_schema, item_schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        body_schema=body_schema,
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    class BodyStrList(RootModel[list[str]]): ...
    body_str_list_factory = ModelFactory.create_factory(
        model=BodyStrList, __use_defaults__=True
    )
    body_obj = body_str_list_factory.build().root
    body_json = to_jsonable_python(body_obj)
    result_obj = None
    httpx_mock.add_response(
        method="get",
        content=b"",
        match_json=body_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
        body = body_obj,
    )  # type: ignore[func-returns-value]
    assert result == result_obj"""
    assert rendered_file == expected

def test_match_body_empty_schema(method_template) -> None:
    body_schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.object),
    )
    document = make_document(body_schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        body_schema=body_schema,
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    body_obj: dict[Any, Any] = {{}}
    body_json = to_jsonable_python(body_obj)
    result_obj = None
    httpx_mock.add_response(
        method="get",
        content=b"",
        match_json=body_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
        body = body_obj,
    )  # type: ignore[func-returns-value]
    assert result == result_obj"""
    assert rendered_file == expected

def test_match_body_list(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    item_schema = make_schema(
        id_="item-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"]
    )
    body_schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.array),
        items=item_schema,
    )
    document = make_document(prop_schema, item_schema, body_schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        body_schema=body_schema,
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    body_model = ItemSchema
    item_schema_list_factory = ModelFactory.create_factory(
        model=body_model, __use_defaults__=True
    )
    body_obj = item_schema_list_factory.batch(size=3)
    body_json = to_jsonable_python(body_obj)
    result_obj = None
    httpx_mock.add_response(
        method="get",
        content=b"",
        match_json=body_json,
        url="{base_url}/test"
    )
    result = client.get_schema(
        body = body_obj,
    )  # type: ignore[func-returns-value]
    assert result == result_obj"""
    assert rendered_file == expected

def test_path_params(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"]
    )
    path_param_schema = make_schema(
        id_="path-param-schema",
        type_=models.SchemaType(models.Type.string),
    )
    path_parameter = make_param_obj(
        id_="path_parameter",
        orig_key="path_parameter",
        location=models.ParameterLocation.path,
        schema=path_param_schema
    )
    document = make_document(resp_schema, prop_schema, path_param_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema,
        path_str="test/{path_parameter}",
    )
    operation.parameters.append(path_parameter)
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    path_params_model = GetSchemaPathParams
    get_schema_path_params_factory = ModelFactory.create_factory(
        model=path_params_model, __use_defaults__=True
    )
    path_params_obj = get_schema_path_params_factory.build()
    path_params_json = to_jsonable_python(path_params_obj)
    response_model = RespSchema
    resp_schema_factory = ModelFactory.create_factory(
        model=response_model, __use_defaults__=True
    )
    result_obj = resp_schema_factory.build()
    result_json = to_jsonable_python(result_obj)
    httpx_mock.add_response(
        method="get",
        json=result_json,
        url="{base_url}/test/{{path_parameter}}".format(**path_params_json),
    )
    result = client.get_schema(
        path_params=path_params_obj,
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_query_params(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"]
    )
    query_param_schema = make_schema(
        id_="query-param-schema",
        type_=models.SchemaType(models.Type.string),
    )
    query_parameter = make_param_obj(
        id_="query_parameter",
        orig_key="query_parameter",
        location=models.ParameterLocation.query,
        schema=query_param_schema
    )
    document = make_document(resp_schema, prop_schema, query_param_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema,
        path_str="test",
    )
    operation.parameters.append(query_parameter)
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    query_params_model = GetSchemaQueryParams
    get_schema_query_params_factory = ModelFactory.create_factory(
        model=query_params_model, __use_defaults__=True
    )
    query_params_obj = get_schema_query_params_factory.build()
    query_params_json = to_jsonable_python(query_params_obj)
    response_model = RespSchema
    resp_schema_factory = ModelFactory.create_factory(
        model=response_model, __use_defaults__=True
    )
    result_obj = resp_schema_factory.build()
    result_json = to_jsonable_python(result_obj)
    httpx_mock.add_response(
        method="get",
        json=result_json,
        url="{base_url}/test?{{query_params}}".format(query_params=urlencode(query_params_json, doseq=False)),
    )
    result = client.get_schema(
        query_params=query_params_obj,
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_path_and_query_params(method_template) -> None:
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop-schema": prop_schema},
        required=["prop-schema"]
    )
    path_param_schema = make_schema(
        id_="path-param-schema",
        type_=models.SchemaType(models.Type.string),
    )
    path_parameter = make_param_obj(
        id_="path_parameter",
        orig_key="path_parameter",
        location=models.ParameterLocation.path,
        schema=path_param_schema
    )
    query_param_schema = make_schema(
        id_="query-param-schema",
        type_=models.SchemaType(models.Type.string),
    )
    query_parameter = make_param_obj(
        id_="query_parameter",
        orig_key="query_parameter",
        location=models.ParameterLocation.query,
        schema=query_param_schema
    )
    document = make_document(resp_schema, prop_schema, path_param_schema, query_param_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema,
        path_str="test/{path_parameter}",
    )
    operation.parameters.append(path_parameter)
    operation.parameters.append(query_parameter)
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    path_params_model = GetSchemaPathParams
    get_schema_path_params_factory = ModelFactory.create_factory(
        model=path_params_model, __use_defaults__=True
    )
    path_params_obj = get_schema_path_params_factory.build()
    path_params_json = to_jsonable_python(path_params_obj)
    query_params_model = GetSchemaQueryParams
    get_schema_query_params_factory = ModelFactory.create_factory(
        model=query_params_model, __use_defaults__=True
    )
    query_params_obj = get_schema_query_params_factory.build()
    query_params_json = to_jsonable_python(query_params_obj)
    response_model = RespSchema
    resp_schema_factory = ModelFactory.create_factory(
        model=response_model, __use_defaults__=True
    )
    result_obj = resp_schema_factory.build()
    result_json = to_jsonable_python(result_obj)
    httpx_mock.add_response(
        method="get",
        json=result_json,
        url="{base_url}/test/{{path_parameter}}?{{query_params}}".format(**path_params_json, query_params=urlencode(query_params_json, doseq=False)),
    )
    result = client.get_schema(
        path_params=path_params_obj,
        query_params=query_params_obj,
    )
    assert result == result_obj"""
    assert rendered_file == expected

def test_custom_error_test(error_method_template) -> None:
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string))
    document = make_document(schema)
    operation = make_operation_with_body(method=models.HttpMethod.post, operation_id=f"post", body_schema=schema)
    path = "/" + operation.path_str
    sync = True
    base_url = "http://test"
    rendered_file = error_method_template.render(
        document=document,
        path=path,
        operation=operation,
        sync=sync,
        method="post",
        base_url=base_url,
    )
    expected = f"""def test_post_custom_error(client_with_custom_error: Client,httpx_mock: HTTPXMock) -> None:
    class BodyStr(RootModel[str]): ...
    body_str_factory = ModelFactory.create_factory(
        model=BodyStr, __use_defaults__=True
    )
    body_obj = body_str_factory.build().root
    body_content = str(body_obj).encode()
    result_obj = None
    httpx_mock.add_response(
        method="post",
        content=b"",
        status_code=404,
        match_content=body_content,
        url="http://test/test"
    )
    with pytest.raises(CustomError) as error:
        result = client_with_custom_error.post(
            body = body_obj,
        )  # type: ignore[func-returns-value]
    assert "My own error" in str(error.value)"""
    assert expected == rendered_file.strip()

def test_custom_error_before_tests(test_template) -> None:
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string))
    document = make_document(schema)
    operation = make_operation_with_body(method=models.HttpMethod.post, operation_id=f"post", body_schema=schema)
    path = operation.path_str
    document.paths = {
        path: models.PathItemObject(
            summary=None,
            description=None,
            operations={
            models.HttpMethod.post: operation
        })
    }
    sync = True
    prepared_operations = prepare_operations(document)
    rendered_file = test_template.render(
        sync=sync,
        operations=prepared_operations.all(),
    )
    assert """class CustomError(ApiError):
    def __init__(self, response: Response):
        reason = response.reason + " My own error"
        super(ApiError, self).__init__(reason)"""
    assert """@pytest.fixture\ndef client_with_custom_error() -> Client:
    return Client(base_url="", error_class=CustomError)""" in rendered_file

def test_extra_slash_in_base_url(method_template) -> None:
    resp_schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.integer),
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-schema",
        response_schema=resp_schema
    )
    path = "/" + operation.path_str
    items = [(path, operation)]
    sync = True
    base_url = "http://test/"
    rendered_file = method_template.render(
        document=document,
        items=items,
        sync=sync,
        method="get",
        base_url=base_url,
    )
    expected = f"""\ndef test_get_schema(client: Client,httpx_mock: HTTPXMock) -> None:
    class RespInt(RootModel[int]): ...
    resp_int_factory = ModelFactory.create_factory(
        model=RespInt, __use_defaults__=True
    )
    result_obj = resp_int_factory.build().root
    httpx_mock.add_response(
        method="get",
        text=str(result_obj),
        url="http://test/test"
    )
    result = client.get_schema(
    )
    assert result == result_obj"""
    assert rendered_file == expected