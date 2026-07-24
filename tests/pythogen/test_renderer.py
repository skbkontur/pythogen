import pytest
from pythogen import models
from pythogen.renderer import j2_is_optional_response, j2_typerepr, j2_responserepr, iterresponsemap, classname, \
    propertyfield

from tests.pythogen.model_factories import make_document, make_schema, make_responses


@pytest.mark.parametrize(
    "type_, expected",
    [
        (models.Type.string, "str"),
        (models.Type.integer, "int"),
        (models.Type.number, "float"),
        (models.Type.boolean, "bool"),
        (models.Type.null, "None"),
        (models.Type.any, "Any"),
    ]
)
def test_j2_typerepr_single_primitive(type_, expected):
    schema = make_schema("schema", models.SchemaType(type_))
    document = make_document(schema)
    assert j2_typerepr(schema, document) == expected

def test_j2_typerepr_multitype_union():
    multi_type = models.SchemaType([models.Type.string, models.Type.null])
    schema = make_schema("schema", multi_type)
    document = make_document(schema)
    result = j2_typerepr(schema, document)
    assert result in {"str | None", "None | str"}

def test_j2_typerepr_array_single_type():
    item_schema = make_schema("item_schema", models.SchemaType(models.Type.string))
    schema = make_schema("schema", models.SchemaType(models.Type.array), items=item_schema)
    document = make_document(item_schema, schema)
    result = j2_typerepr(schema, document)
    assert result == "list[str]"

def test_j2_typerepr_array_multitype():
    item_schema = make_schema(
        "item_schema",
        models.SchemaType([models.Type.string, models.Type.null])
    )
    schema = make_schema("schema", models.SchemaType(models.Type.array), items=item_schema)
    document = make_document(item_schema, schema)
    result = j2_typerepr(schema, document)
    assert result in {"list[str | None]", "list[None | str]"}

def test_j2_typerepr_array_enum():
    item_schema = make_schema(
        "<inline+SchemaObject>Item",
        models.SchemaType(models.Type.string),
        enum=["FIRST", "SECOND"]
    )
    schema = make_schema("<inline+SchemaObject>", models.SchemaType(models.Type.array), items=item_schema)
    document = make_document(item_schema, schema)
    result = j2_typerepr(schema, document)
    assert result == "list[Literal['FIRST', 'SECOND']]"

def test_responserepr_without_optional():
    prop_schema = make_schema("prop", models.SchemaType(models.Type.string))
    schema = make_schema(
        "resp-schema",
        models.SchemaType(models.Type.object),
        props={"prop": prop_schema},
    )
    document = make_document(schema, prop_schema)
    responses = make_responses(schema=schema)

    assert j2_responserepr(responses, document) == "RespSchema"

def test_responserepr_with_optional():
    prop_schema = make_schema("prop", models.SchemaType(models.Type.string))
    schema = make_schema(
        "resp-schema",
        models.SchemaType(models.Type.object),
        props={"prop": prop_schema},
        nullable=True,
    )
    document = make_document(schema, prop_schema)
    responses = make_responses(schema=schema)

    assert j2_responserepr(responses, document) == "RespSchema | None"

def test_is_optional_response():
    prop_schema = make_schema(
        id_="prop",
        type_=models.SchemaType(models.Type.string))
    schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop": prop_schema},
        nullable=True,
    )
    document = make_document(schema, prop_schema)
    responses = make_responses(schema=schema)

    assert j2_is_optional_response(responses, document) is True

def test_is_optional_response_without_optional():
    prop_schema = make_schema("prop", models.SchemaType(models.Type.string))
    schema = make_schema(
        "resp-schema",
        models.SchemaType(models.Type.object),
        props={"prop": prop_schema},
    )
    document = make_document(schema, prop_schema)
    responses = make_responses(schema=schema)

    assert j2_is_optional_response(responses, document) is False

def test_iterresponsemap_no_schema():
    responses = make_responses(schema=None)
    mapping = iterresponsemap(responses)
    assert mapping == [("200", "None")]

def test_iterresponsemap_empty_schema():
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
    )
    responses = make_responses(schema=schema)
    mapping = iterresponsemap(responses)
    assert mapping == [("200", "response.json()")]

def test_iterresponsemap_schema_with_prop():
    prop_schema = make_schema(
        id_="prop",
        type_=models.SchemaType(models.Type.string),
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop": prop_schema},
    )
    responses = make_responses(schema=schema)
    mapping = iterresponsemap(responses)
    expected = f"{classname(schema.id)}.model_validate(response.json())"
    assert mapping == [("200", expected)]

def test_iterresponsemap_anyof_schema():
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.any),
    )

    first_schema = make_schema(
        id_="first_schema",
        type_=models.SchemaType(models.Type.object),
    )
    second_schema = make_schema(
        id_="second_schema",
        type_=models.SchemaType(models.Type.object),
    )
    schema.any_of = [first_schema, second_schema]
    responses = make_responses(schema=schema)
    mapping = iterresponsemap(responses)
    anyof_classnames = [classname(s.id) for s in schema.any_of]
    anyof_classnames_str = "[" + ", ".join(anyof_classnames) + "]"
    expected = f"self._parse_any_of(response.json(), {anyof_classnames_str})"
    assert mapping == [("200", expected)]

def test_iterresponsemap_array_of_objects_schema():
    item_schema = make_schema(
        id_="item_schema",
        type_=models.SchemaType(models.Type.object),
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.array),
        items=item_schema,
    )
    responses = make_responses(schema=schema)
    mapping = iterresponsemap(responses)
    expected = f"[{classname(item_schema.id)}.model_validate(item) for item in response.json()]"
    assert mapping == [("200", expected)]

def test_iterresponsemap_array_of_primitives_schema():
    item_schema = make_schema(
        id_="item_schema",
        type_=models.SchemaType(models.Type.string),
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.array),
        items=item_schema,
    )
    responses = make_responses(schema=schema)
    mapping = iterresponsemap(responses)
    assert mapping == [("200", "response.json()")]

def test_iterresponsemap_empty_array_schema():
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.array),
    )
    responses = make_responses(schema=schema)
    mapping = iterresponsemap(responses)
    assert mapping == [("200", "response.text")]

def test_iterresponsemap_binary_schema():
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.string),
    )
    schema.format = models.Format.binary
    responses = make_responses(schema)
    mapping = iterresponsemap(responses)
    assert mapping == [("200", "response.content")]

def test_iterresponsemap_string_schema():
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.string),
    )
    responses = make_responses(schema)
    mapping = iterresponsemap(responses)
    assert mapping == [("200", "response.text")]

def test_iterresponsemap_int_schema():
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.integer),
    )
    responses = make_responses(schema)
    mapping = iterresponsemap(responses)
    assert mapping == [("200", "int(response.text)")]

def test_iterresponsemap_any_schema():
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.any),
    )
    responses = make_responses(schema)
    mapping = iterresponsemap(responses)
    assert mapping == [("200", "response.text")]

def test_iterresponsemap_nullable_string_schema():
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType([models.Type.string, models.Type.null]),
    )
    responses = make_responses(schema)
    mapping = iterresponsemap(responses)
    assert mapping == [("200", "response.text")]

def test_iterresponsemap_nullable_array_of_objects_schema():
    item_schema = make_schema(
        id_="item_schema",
        type_=models.SchemaType(models.Type.object),
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType([models.Type.array, models.Type.null]),
        items=item_schema,
    )
    responses = make_responses(schema=schema)
    mapping = iterresponsemap(responses)
    expected = f"[{classname(item_schema.id)}.model_validate(item) for item in response.json()]"
    assert mapping == [("200", expected)]

def test_propertyfield_required_no_default():
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
    )
    prop_schema.default = models.UNDEFINED
    parent_schema = make_schema(
        id_="parent_schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema},
    )
    parent_schema.required.append("prop")
    prop = models.SchemaProperty(orig_key="prop", safety_key=None, schema=prop_schema)
    result = propertyfield(prop, parent_schema)

    assert result == ""
