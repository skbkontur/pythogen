import datetime

import pytest

from pythogen import models
from pythogen.packager import body_repr
from pythogen.packager import j2_assertions
from pythogen.packager import match_content_repr
from pythogen.packager import match_headers_repr
from pythogen.packager import mock_response_repr
from pythogen.packager import url_repr
from pythogen.packager import path_params_repr
from pythogen.packager import query_params_repr
from pythogen.packager import headers_repr
from tests.pythogen.model_factories import make_document
from tests.pythogen.model_factories import make_operation_with_body
from tests.pythogen.model_factories import make_operation_with_response
from tests.pythogen.model_factories import make_param_obj
from tests.pythogen.model_factories import make_schema


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
    models.Type.boolean,
    models.Type.number,
)
NONPRIMITIVE_FORMATS = (
    models.Format.binary,
    models.Format.date,
    models.Format.datespan,
    models.Format.datetime,
    models.Format.uri
)
PRIMITIVE_BODY_VALUES = {
    models.Type.string: "'string'",
    models.Type.integer: "42",
    models.Type.boolean: True,
    models.Type.number: "42.0",
}
NONPRIMITIVE_RESP_VALUES = {
    models.Format.binary: "b'bytes'",
    models.Format.date: datetime.date(2009, 1, 26).isoformat(),
    models.Format.datespan: str(datetime.timedelta(hours=13, minutes=37)),
    models.Format.datetime: datetime.datetime(2005, 10, 10).isoformat(),
    models.Format.uri: "http://www.example.com/"
}
NONPRIMITIVE_BODY_VALUES = {
    models.Format.binary: "b'bytes'",
    models.Format.date: "datetime.date(2009, 1, 26)",
    models.Format.datespan: "datetime.timedelta(seconds=49020)",
    models.Format.datetime: "datetime.datetime(2005, 10, 10, 0, 0)",
    models.Format.uri: "HttpUrl('http://www.example.com/')"
}

@pytest.mark.parametrize("method", METHODS)
def test_mock_response_repr_binary_successful_method(method: models.HttpMethod):
    resp_schema = make_schema(
        id_="test-resp-schema",
        type_=models.SchemaType(models.Type.string),
        format_=models.Format.binary,
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=method,
        operation_id=f"simple-{method.value}",
        response_schema=resp_schema,
    )
    result = mock_response_repr(operation, document)
    assert result == "content=b'bytes'"

@pytest.mark.parametrize("method", METHODS)
def test_mock_response_repr_string_successful_method(method: models.HttpMethod):
    resp_schema = make_schema(
        id_="test-resp-schema",
        type_=models.SchemaType(models.Type.string),
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=method,
        operation_id=f"simple-{method.value}",
        response_schema=resp_schema,
    )
    result = mock_response_repr(operation, document)
    assert result == "content='string'"

@pytest.mark.parametrize("method", METHODS)
def test_mock_response_repr_dict_successful_method(method: models.HttpMethod):
    resp_schema = make_schema(
        id_="test-resp-schema",
        type_=models.SchemaType(models.Type.object),
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=method,
        operation_id=f"simple-{method.value}",
        response_schema=resp_schema,
    )
    result = mock_response_repr(operation, document)
    assert result == "json={}"

@pytest.mark.parametrize("method", METHODS)
def test_mock_response_repr_list_successful_method(method: models.HttpMethod):
    item_schema = make_schema(
        id_="test-item-schema",
        type_=models.SchemaType(models.Type.string),
    )
    resp_schema = make_schema(
        id_="test-resp-schema",
        type_=models.SchemaType(models.Type.array),
        items=item_schema,
    )
    document = make_document(item_schema, resp_schema)
    operation = make_operation_with_response(
        method=method,
        operation_id=f"simple-{method.value}",
        response_schema=resp_schema,
    )
    result = mock_response_repr(operation, document)
    assert result == "json=['string']"

@pytest.mark.parametrize("method", METHODS)
def test_mock_response_repr_object_successful_method(method: models.HttpMethod):
    prop_schema = make_schema(
        id_="test-prop-schema",
        type_=models.SchemaType(models.Type.string),
    )
    resp_schema = make_schema(
        id_="test-resp-schema",
        type_=models.SchemaType(models.Type.object),
        props={"test-prop": prop_schema},
    )
    document = make_document(prop_schema, resp_schema)
    operation = make_operation_with_response(
        method=method,
        operation_id=f"simple-{method.value}",
        response_schema=resp_schema,
    )
    result = mock_response_repr(operation, document)
    assert result == "json={'test-prop': 'string'}"

@pytest.mark.parametrize("method", METHODS)
def test_mock_response_repr_enum_successful_method(method: models.HttpMethod):
    resp_schema = make_schema(
        id_="test-resp-schema",
        type_=models.SchemaType(models.Type.string),
        enum=["Hello", "World"],
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=method,
        operation_id=f"simple-{method.value}",
        response_schema=resp_schema,
    )
    result = mock_response_repr(operation, document)
    assert result == "content='Hello'"

@pytest.mark.parametrize("method", METHODS)
def test_mock_response_repr_string_succesful_not_200_method(method: models.HttpMethod):
    resp_schema = make_schema(
        id_="test-resp-schema",
        type_=models.SchemaType(models.Type.string),
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=method,
        operation_id=f"simple-{method.value}",
        response_schema=resp_schema,
        status_code=201,
    )
    result = mock_response_repr(operation, document)
    assert result == "content='string'"

@pytest.mark.parametrize("nonprimitive_format", NONPRIMITIVE_FORMATS)
@pytest.mark.parametrize("method", METHODS)
def test_mock_response_repr_nonprimitive_type_succesful_method(method: models.HttpMethod, nonprimitive_format: models.Format):
    resp_schema = make_schema(
        id_="test-resp-schema",
        type_=models.SchemaType(models.Type.string),
        format_=nonprimitive_format
    )
    document = make_document(resp_schema)
    operation = make_operation_with_response(
        method=method,
        operation_id=f"simple-{method.value}",
        response_schema=resp_schema,
    )
    result = mock_response_repr(operation, document)
    if nonprimitive_format == models.Format.binary:
        assert result == "content=b'bytes'"
    else:
        assert result == f"content='{NONPRIMITIVE_RESP_VALUES[nonprimitive_format]}'"

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_primitive_body_repr(primitive_type: models.Type):
    schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(primitive_type),
    )
    document = make_document(schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="test-get",
        body_schema=schema,
    )
    result = body_repr(operation, document)
    assert result == f"body = {PRIMITIVE_BODY_VALUES[primitive_type]}"

def test_object_body_repr():
    schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.object),
    )
    document = make_document(schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="test-get",
        body_schema=schema,
    )
    result = body_repr(operation, document)
    assert result == "body = {}"

@pytest.mark.parametrize("nonprimitive_format", NONPRIMITIVE_FORMATS)
def test_nonprimitive_body_repr(nonprimitive_format: models.Format):
    schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.string),
        format_=nonprimitive_format
    )
    document = make_document(schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="test-get",
        body_schema=schema,
    )
    result = body_repr(operation, document)
    assert result == f"body = {NONPRIMITIVE_BODY_VALUES[nonprimitive_format]}"

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_props_body_repr(primitive_type: models.Type):
    prop_schema = make_schema(
        id_="prop-schema",
        type_=models.SchemaType(primitive_type),
    )
    schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop": prop_schema},
    )
    document = make_document(schema, prop_schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="test-get",
        body_schema=schema,
    )
    result = body_repr(operation, document)
    assert result == f"body = BodySchema(prop={PRIMITIVE_BODY_VALUES[primitive_type]})"

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_prop_array_body_repr(primitive_type: models.Type):
    item_schema = make_schema(id_="item-schema", type_=models.SchemaType(primitive_type))
    arr_schema = make_schema(id_="array-schema", type_=models.SchemaType(models.Type.array), items=item_schema)
    schema = make_schema(id_="body-schema", type_=models.SchemaType(models.Type.object), props={"prop": arr_schema})
    document = make_document(item_schema, arr_schema, schema)
    operation = make_operation_with_body(method=models.HttpMethod.post, operation_id="test-post", body_schema=schema)
    result = body_repr(operation, document)
    assert result == f"body = BodySchema(prop=[{PRIMITIVE_BODY_VALUES[primitive_type]}])"

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_prop_obj_body_repr(primitive_type: models.Type):
    item_schema = make_schema(id_="item-schema", type_=models.SchemaType(primitive_type))
    prop_schema = make_schema(id_="prop-schema", type_=models.SchemaType(models.Type.object), props={"prop": item_schema})
    schema = make_schema(id_="body-schema", type_=models.SchemaType(models.Type.object), props={"prop": prop_schema})
    document = make_document(item_schema, prop_schema, schema)
    operation = make_operation_with_body(method=models.HttpMethod.post, operation_id="test-post", body_schema=schema)
    result = body_repr(operation, document)
    assert result == f"body = BodySchema(prop=PropSchema(prop={PRIMITIVE_BODY_VALUES[primitive_type]}))"

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_list_body_repr(primitive_type: models.Type):
    item_schema = make_schema(
        id_="item-schema",
        type_=models.SchemaType(primitive_type),
    )
    schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.array),
        items=item_schema,
    )
    document = make_document(item_schema, schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="test-get",
        body_schema=schema,
    )
    result = body_repr(operation, document)
    assert result == f"body = [{PRIMITIVE_BODY_VALUES[primitive_type]}]"

def test_enum_body_repr():
    schema = make_schema(
        id_="body-schema",
        type_=models.SchemaType(models.Type.string),
        enum=["FIRST", "SECOND", "THIRD"],
    )
    document = make_document(schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.get,
        operation_id="test-get",
        body_schema=schema,
    )
    result = body_repr(operation, document)
    assert result == "body = 'FIRST'"

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
@pytest.mark.parametrize("method", METHODS)
def test_match_content_repr_primitive_type(method: models.HttpMethod, primitive_type: models.Type):
    expected = {
        models.Type.string: ["b'string'"],
        models.Type.integer: ["b'42'"],
        models.Type.boolean: ["b'true'"],
        models.Type.number: ["b'42.0'"],
    }
    schema = make_schema(id_="schema", type_=models.SchemaType(primitive_type))
    document = make_document(schema)
    operation = make_operation_with_body(method=method, operation_id=f"test-{method.value}", body_schema=schema)
    result = match_content_repr(operation, document)
    assert result == expected[primitive_type]

@pytest.mark.parametrize("format_", NONPRIMITIVE_FORMATS)
@pytest.mark.parametrize("method", METHODS)
def test_match_content_repr_nonprimitive(method: models.HttpMethod, format_: models.Format):
    expected = {
        models.Format.binary: ["b'bytes'"],
        models.Format.datetime: ["b'2005-10-10T00:00:00'"],
        models.Format.date: ["b'2009-01-26'"],
        models.Format.datespan: ["b'13:37:00'"],
        models.Format.uri: ["b'http://www.example.com/'"],
    }
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string), format_=format_)
    document = make_document(schema)
    operation = make_operation_with_body(method=method, operation_id=f"test-{method.value}", body_schema=schema)
    result = match_content_repr(operation, document)
    assert result == expected[format_]

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
@pytest.mark.parametrize("method", METHODS)
def test_match_content_repr_array(method: models.HttpMethod, primitive_type: models.Type):
    expected = {
        models.Type.string: ['b\'["string"]\''],
        models.Type.integer: ["b'[42]'"],
        models.Type.boolean: ["b'[true]'"],
        models.Type.number: ["b'[42.0]'"],
    }
    item_schema = make_schema(id_="item-schema", type_=models.SchemaType(primitive_type))
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.array), items=item_schema)
    document = make_document(schema, item_schema)
    operation = make_operation_with_body(method=method, operation_id=f"test-{method.value}", body_schema=schema)
    result = match_content_repr(operation, document)
    assert result == expected[primitive_type]

@pytest.mark.parametrize("method", METHODS)
def test_match_content_repr_enum(method: models.HttpMethod):
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string), enum=["FIRST", "SECOND", "THIRD"])
    document = make_document(schema)
    operation = make_operation_with_body(method=method, operation_id=f"test-{method.value}", body_schema=schema)
    result = match_content_repr(operation, document)
    assert result == ["b'FIRST'"]

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
@pytest.mark.parametrize("method", METHODS)
def test_match_content_repr_obj_with_props(method: models.HttpMethod, primitive_type: models.Type):
    expected = {
        models.Type.string: ['b\'{"prop": "string"}\''],
        models.Type.integer: ['b\'{"prop": 42}\''],
        models.Type.boolean: ['b\'{"prop": true}\''],
        models.Type.number: ['b\'{"prop": 42.0}\''],
    }
    prop_schema = make_schema(id_="prop-schema", type_=models.SchemaType(primitive_type))
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.object), props={"prop": prop_schema})
    document = make_document(schema, prop_schema)
    operation = make_operation_with_body(method=method, operation_id=f"test-{method.value}", body_schema=schema)
    result = match_content_repr(operation, document)
    assert result == expected[primitive_type]

@pytest.mark.parametrize("method", METHODS)
def test_match_headers(method: models.HttpMethod):
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string))
    document = make_document(schema)
    operation = make_operation_with_body(method=method, operation_id=f"test-{method.value}", body_schema=schema)
    operation.parameters = [make_param_obj(id_="test-header",
                                           orig_key="Test-Header",
                                           location=models.ParameterLocation.header,
                                           schema=schema)]
    result = match_headers_repr(operation, document)
    assert result == "match_headers={'test_header': 'string_param'}"

@pytest.mark.parametrize("method", METHODS)
def test_url_repr_path_param(method: models.HttpMethod):
    base_url = "http://example.com"
    path = "/{test-path-param}"
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string))
    document = make_document(schema)
    operation = make_operation_with_body(method=method, operation_id=f"test-{method.value}", body_schema=schema)
    operation.parameters = [make_param_obj(id_="test-path-param",
                                           orig_key="test-path-param",
                                           location=models.ParameterLocation.path,
                                           schema=schema)]
    result = url_repr(operation=operation, document=document, base_url=base_url, path=path)
    assert result == 'url="http://example.com/string_param"'

@pytest.mark.parametrize("method", METHODS)
def test_url_repr_query_param(method: models.HttpMethod):
    base_url = "http://example.com"
    path = "/"
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string))
    document = make_document(schema)
    operation = make_operation_with_body(method=method, operation_id=f"test-{method.value}", body_schema=schema)
    operation.parameters = [make_param_obj(id_="test-query-param",
                                           orig_key="test-query-param",
                                           location=models.ParameterLocation.query,
                                           schema=schema)]
    result = url_repr(operation=operation, document=document, base_url=base_url, path=path)
    assert result == 'url="http://example.com/?test-query-param=string_param"'

@pytest.mark.parametrize("method", METHODS)
def test_url_repr_combine_params(method: models.HttpMethod):
    base_url = "http://example.com"
    path = "/{test-path-param}"
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string))
    document = make_document(schema)
    operation = make_operation_with_body(method=method, operation_id=f"test-{method.value}", body_schema=schema)
    operation.parameters = [make_param_obj(id_="test-query-param",
                                           orig_key="test-query-param",
                                           location=models.ParameterLocation.query,
                                           schema=schema),
                            make_param_obj(id_="test-path-param",
                                           orig_key="test-path-param",
                                           location=models.ParameterLocation.path,
                                           schema=schema)
                            ]
    result = url_repr(operation=operation, document=document, base_url=base_url, path=path)
    assert result == 'url="http://example.com/string_param?test-query-param=string_param"'

def test_assertions_no_resp():
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string))
    document = make_document(schema)
    operation = make_operation_with_response(method=models.HttpMethod.get, operation_id="test-get", response_schema=None)
    result = j2_assertions(operation=operation, document=document)
    assert result == "assert result is None"

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_assertions_primitive_types(primitive_type: models.Type):
    expected = {
        models.Type.string: "assert result == 'string'",
        models.Type.number: "assert result == 42.0",
        models.Type.boolean: "assert result == True",
        models.Type.integer: "assert result == 42",
    }
    schema = make_schema(id_="schema", type_=models.SchemaType(primitive_type))
    document = make_document(schema)
    operation = make_operation_with_response(method=models.HttpMethod.get, operation_id="test-get", response_schema=schema)
    result = j2_assertions(operation=operation, document=document)
    assert result == expected[primitive_type]

@pytest.mark.parametrize("format_", NONPRIMITIVE_FORMATS)
def test_assertions_nonprimitive(format_: models.Format):
    expected = {
        models.Format.binary: "assert result == b'bytes'",
        models.Format.date: "assert result == '2009-01-26'",
        models.Format.datespan: "assert result == '13:37:00'",
        models.Format.datetime: "assert result == '2005-10-10T00:00:00'",
        models.Format.uri: "assert result == 'http://www.example.com/'",
    }
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string), format_=format_)
    document = make_document(schema)
    operation = make_operation_with_response(method=models.HttpMethod.get, operation_id="test-get", response_schema=schema)
    result = j2_assertions(operation=operation, document=document)
    assert result == expected[format_]

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_assertions_array(primitive_type: models.Type):
    expected = {
        models.Type.string: "assert to_jsonable_python(result) == ['string']",
        models.Type.number: "assert to_jsonable_python(result) == [42.0]",
        models.Type.boolean: "assert to_jsonable_python(result) == [True]",
        models.Type.integer: "assert to_jsonable_python(result) == [42]",
    }
    item_schema = make_schema(id_="item_schema", type_=models.SchemaType(primitive_type))
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.array), items=item_schema)
    document = make_document(schema, item_schema)
    operation = make_operation_with_response(method=models.HttpMethod.get, operation_id="test-get", response_schema=schema)
    result = j2_assertions(operation=operation, document=document)
    assert result == expected[primitive_type]

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_assertions_obj_with_prop(primitive_type: models.Type):
    expected = {
        models.Type.string: "assert to_jsonable_python(result) == {'prop': 'string'}",
        models.Type.number: "assert to_jsonable_python(result) == {'prop': 42.0}",
        models.Type.boolean: "assert to_jsonable_python(result) == {'prop': True}",
        models.Type.integer: "assert to_jsonable_python(result) == {'prop': 42}",
    }
    item_schema = make_schema(id_="item_schema", type_=models.SchemaType(primitive_type))
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.object), props={"prop": item_schema})
    document = make_document(schema, item_schema)
    operation = make_operation_with_response(method=models.HttpMethod.get, operation_id="test-get", response_schema=schema)
    result = j2_assertions(operation=operation, document=document)
    assert result == expected[primitive_type]

def test_assertions_obj():
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.object))
    document = make_document(schema)
    operation = make_operation_with_response(method=models.HttpMethod.get, operation_id="test-get", response_schema=schema)
    result = j2_assertions(operation=operation, document=document)
    assert result == "assert to_jsonable_python(result) == {}"

def test_assertions_enum():
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string), enum=["FIRST", "SECOND", "THIRD"])
    document = make_document(schema)
    operation = make_operation_with_response(method=models.HttpMethod.get, operation_id="test-get", response_schema=schema)
    result = j2_assertions(operation=operation, document=document)
    assert result == "assert result == 'FIRST'"

@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_params_repr(primitive_type: models.Type):
    expected_value = {
        models.Type.string: "'string_param'",
        models.Type.integer: 42,
        models.Type.number: 42.0,
        models.Type.boolean: True,
    }
    schema = make_schema(id_="schema", type_=models.SchemaType(primitive_type))
    document = make_document(schema)
    operation = make_operation_with_body(method=models.HttpMethod.post, operation_id=f"test-post", body_schema=schema)
    operation.parameters = [make_param_obj(id_="test-query-param",
                                           orig_key="test-query-param",
                                           location=models.ParameterLocation.query,
                                           schema=schema),
                            make_param_obj(id_="test-path-param",
                                           orig_key="test-path-param",
                                           location=models.ParameterLocation.path,
                                           schema=schema),
                            make_param_obj(id_="test-header-param",
                                           orig_key="test-header-param",
                                           location=models.ParameterLocation.header,
                                           schema=schema),
                            ]
    path_params_result = path_params_repr(operation=operation, document=document)
    query_params_result = query_params_repr(operation=operation, document=document)
    headers_result = headers_repr(operation=operation, document=document)
    assert path_params_result == f"path_params = TestPostPathParams(test_path_param={expected_value[primitive_type]})"
    assert query_params_result == f"query_params = TestPostQueryParams(test_query_param={expected_value[primitive_type]})"
    assert headers_result == f"headers = TestPostHeaders(test_header_param={expected_value[primitive_type]})"
