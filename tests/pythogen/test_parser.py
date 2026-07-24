import pytest

from pythogen.models import HttpMethod
from pythogen.parsers.operations import OperationParser
from pythogen.parsers.parameters import ParameterParser
from pythogen.parsers.paths import PathParser
from pythogen.parsers.request_body import RequestBodyParser
from pythogen.parsers.response import ResponseParser
from pythogen.parsers.schemas import SchemaParser
from pythogen.parsers.inline_schemas_aggregator import InlineSchemasAggregator
from pythogen.parsers.references import RefResolver
from pythogen import models


class DummyRefResolver():
    ...

class DummyInlineAggregator():
    ...

@pytest.fixture
def parser():
    return SchemaParser(
        ref_resolver=DummyRefResolver(),
        openapi_data={},
        discriminator_base_class_schemas=[],
        inline_schema_aggregator=DummyInlineAggregator(),
        ignore_unknown_format=False,
    )

def test_parse_type_single(parser):
    data = {"type": "string"}
    schema_type = parser._parse_type(data)
    assert isinstance(schema_type, models.SchemaType)
    assert schema_type == models.Type.string

def test_parse_type_multiple(parser):
    data = {"type": ["string", "null"]}
    schema_type = parser._parse_type(data)
    assert isinstance(schema_type, models.SchemaType)
    assert models.Type.string in schema_type
    assert models.Type.null in schema_type

def test_parse_type_unknown(parser):
    data = {"type": "bruh"}
    with pytest.raises(Exception, match='Unknown type "bruh"'):
        parser._parse_type(data)

def test_parse_default_not_defined(parser):
    data = {"type": "string"}
    schema: models.SchemaObject = parser.parse_item("schema", data)
    assert schema.default is models.UNDEFINED

def test_parse_default_some_value(parser):
    data = {"type": "string", "default": "qwerty"}
    schema: models.SchemaObject = parser.parse_item("schema", data)
    assert schema.default == "qwerty"

def test_parse_default_null(parser):
    data = {"type": ["string", "null"], "default": None}
    schema: models.SchemaObject = parser.parse_item("schema", data)
    assert schema.default is None

def test_parse_allof_property_schema_with_single_item():
    openapi_data = {
        "openapi": "3.0.0",
        "info": {"title": "test", "version": "1.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Inner": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    },
                },
                "Outer": {
                    "type": "object",
                    "properties": {
                        "param": {
                            "allOf": [
                                {"$ref": "#/components/schemas/Inner"},
                            ],
                        },
                    },
                },
            },
        },
    }
    inline_schema_aggregator = InlineSchemasAggregator()
    parser = SchemaParser(
        ref_resolver=RefResolver(openapi_data),
        openapi_data=openapi_data,
        discriminator_base_class_schemas=[],
        inline_schema_aggregator=inline_schema_aggregator,
        ignore_unknown_format=False,
    )
    schemas = parser.parse_collection()
    schema = schemas["Outer"]
    assert schema.properties
    prop_schema = schema.properties[0].schema
    assert prop_schema.id == "param_ref_obj"
    assert len(prop_schema.all_of) == 1
    assert prop_schema.all_of[0].id == "Inner"
    assert "param_ref_obj" in inline_schema_aggregator.get_mapping()

def test_parse_oneof_property_schema_with_single_item():
    openapi_data = {
        "openapi": "3.0.0",
        "info": {"title": "test", "version": "1.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Inner": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    },
                },
                "Outer": {
                    "type": "object",
                    "properties": {
                        "param": {
                            "oneOf": [
                                {"$ref": "#/components/schemas/Inner"},
                            ],
                        },
                    },
                },
            },
        },
    }
    inline_schema_aggregator = InlineSchemasAggregator()
    parser = SchemaParser(
        ref_resolver=RefResolver(openapi_data),
        openapi_data=openapi_data,
        discriminator_base_class_schemas=[],
        inline_schema_aggregator=inline_schema_aggregator,
        ignore_unknown_format=False,
    )
    schemas = parser.parse_collection()
    schema = schemas["Outer"]
    assert schema.properties
    prop_schema = schema.properties[0].schema
    assert prop_schema.id == "param_obj"
    assert len(prop_schema.one_of) == 1
    assert prop_schema.one_of[0].id == "Inner"
    assert "param_obj" in inline_schema_aggregator.get_mapping()

@pytest.mark.parametrize(
    ("combinator_key", "schema_attr"),
    [
        ("allOf", "all_of"),
        ("anyOf", "any_of"),
        ("oneOf", "one_of"),
    ],
)
def test_parse_cyclic_combinator_ref_does_not_recurse(combinator_key, schema_attr):
    openapi_data = {
        "openapi": "3.0.0",
        "info": {"title": "test", "version": "1.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Schema": {
                    combinator_key: [
                        {"$ref": "#/components/schemas/Schema"},
                    ],
                },
            },
        },
    }
    parser = SchemaParser(
        ref_resolver=RefResolver(openapi_data),
        openapi_data=openapi_data,
        discriminator_base_class_schemas=[],
        inline_schema_aggregator=InlineSchemasAggregator(),
        ignore_unknown_format=False,
    )

    schemas = parser.parse_collection()

    schema = schemas["Schema"]
    nested_schema = getattr(schema, schema_attr)[0]
    assert nested_schema.id == "Schema"
    assert nested_schema.is_fake is True
    assert nested_schema.all_of == []
    assert nested_schema.any_of == []
    assert nested_schema.one_of == []

def test_parse_array_items_enum_adds_inline_schema():
    openapi_data = {
        "openapi": "3.0.0",
        "info": {"title": "test", "version": "1.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Schema": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["first", "second"],
                            },
                        },
                    },
                },
            },
        },
    }
    inline_schema_aggregator = InlineSchemasAggregator()
    parser = SchemaParser(
        ref_resolver=RefResolver(openapi_data),
        openapi_data=openapi_data,
        discriminator_base_class_schemas=[],
        inline_schema_aggregator=inline_schema_aggregator,
        ignore_unknown_format=False,
    )
    parser.parse_collection()
    inline_mapping = inline_schema_aggregator.get_mapping()
    assert "tags_listItem" in inline_mapping
    assert inline_mapping["tags_listItem"].enum == ["first", "second"]

def test_parse_format_raise_unknown(parser):
    data = {"type": "string", "format": "unknown_format"}

    with pytest.raises(Exception, match='Unable to parse schema, unknown format "unknown_format"'):
        parser._parse_format(data)

def test_parse_properties_raise_unknown(parser):
    data = {"type": "string", "format": "unknown_format"}

    with pytest.raises(Exception, match='Unable to parse schema, unknown format "unknown_format"'):
        parser._parse_properties(models.SchemaType(models.Type.string), data)


def test_parse_format_ignore_unknown():
    parser = SchemaParser(
        ref_resolver=DummyRefResolver(),
        openapi_data={},
        discriminator_base_class_schemas=[],
        inline_schema_aggregator=DummyInlineAggregator(),
        ignore_unknown_format=True,
    )
    data = {"type": "string", "format": "unknown_format"}

    schema_format = parser._parse_format(data)
    assert schema_format is None

def test_parse_properties_ignore_unknown():
    parser = SchemaParser(
        ref_resolver=DummyRefResolver(),
        openapi_data={},
        discriminator_base_class_schemas=[],
        inline_schema_aggregator=DummyInlineAggregator(),
        ignore_unknown_format=True,
    )
    data = {"type": "string", "format": "unknown_format"}

    properties = parser._parse_properties(models.SchemaType(models.Type.string), data)
    assert properties[0].schema.format is None

def test_parse_operation_with_endpoint_parameters():
    openapi_data = {
        "openapi": "3.0.0",
        "info": {"title": "test", "version": "1.0"},
        "paths": {
            "/test/{id}": {
                "post": {
                    "operationId": "post-id",
                    "parameters": [
                        {
                            "name": "name",
                            "in": "query",
                            "description": "",
                            "required": "true",
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {},
                },
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": "true",
                        "schema": {
                            "type": "string"
                        }
                    }
                ]
            },
        },
        "components": {},
    }
    inline_schema_aggregator = InlineSchemasAggregator()
    ref_resolver = RefResolver(
        openapi_data=openapi_data,
    )
    schema_parser = SchemaParser(
        ref_resolver=ref_resolver,
        openapi_data=openapi_data,
        discriminator_base_class_schemas=[],
        inline_schema_aggregator=inline_schema_aggregator,
        ignore_unknown_format=True,
    )
    response_parser = ResponseParser(
        ref_resolver=ref_resolver,
        schema_parser=schema_parser,
        inline_schema_aggregator=inline_schema_aggregator,
    )
    request_body_parser = RequestBodyParser(
        ref_resolver=ref_resolver,
        schema_parser=schema_parser,
        inline_schema_aggregator=inline_schema_aggregator,
    )
    parameters_parser = ParameterParser(
        ref_resolver=ref_resolver,
        schema_parser=schema_parser,
        openapi_data=openapi_data,
    )
    operation_parser = OperationParser(
        ref_resolver=ref_resolver,
        schema_parser=schema_parser,
        response_parser=response_parser,
        request_body_parser=request_body_parser,
        parameters_parser=parameters_parser,
    )
    path_parser = PathParser(
        ref_resolver=ref_resolver,
        schema_parser=schema_parser,
        operation_parser=operation_parser,
        openapi_data=openapi_data,
    )
    path_items = path_parser.parse_collection()
    parameters = [parameter.orig_key for parameter in path_items["/test/{id}"].operations[HttpMethod.post].parameters]
    assert len(parameters) == 2
    assert "name" in parameters
    assert "id" in parameters
