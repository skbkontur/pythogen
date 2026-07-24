from clients.sync_client import SafetyKeyForTesting
from pythogen import models
from tests.pythogen.model_factories import make_document, make_schema


def test_safety_key():
    item = SafetyKeyForTesting(for_="str value", with_dot_hyphen_back_slash_colon_space=1)

    assert item.model_dump() == {
        'with_dot_hyphen_back_slash_colon_space': 1,
        'old_feature_priority': None,
        'class_': None,
        'for_': 'str value',
        'schema_': None,
    }

    assert item.model_dump(by_alias=True) == {
        '33with.dot-hyphen\\back/slash:colon space&*': 1,
        '34with.dot-and-hyphens&*': None,
        '__Class__': None,
        'for': 'str value',
        'schema': None,
    }

    assert item.model_dump(exclude_none=True) == {
        'with_dot_hyphen_back_slash_colon_space': 1,
        'for_': 'str value',
    }

    assert item.model_dump(exclude_unset=True) == {
        'with_dot_hyphen_back_slash_colon_space': 1,
        'for_': 'str value',
    }

    assert item.model_dump(exclude_unset=True, by_alias=True) == {
        '33with.dot-hyphen\\back/slash:colon space&*': 1,
        'for': 'str value',
    }

    assert item.model_dump(exclude_unset=True, exclude_none=True, by_alias=True) == {
        '33with.dot-hyphen\\back/slash:colon space&*': 1,
        'for': 'str value',
    }


def test_format_missing():
    assert models.Format("date-time") is models.Format.datetime
    assert models.Format("datetime") is models.Format.datetime

def test_sorted_schemas_orders_property_dependencies_with_allof():
    inner_prop_schema = make_schema(
        id_="inner_prop_schema",
        type_=models.SchemaType(models.Type.object),
    )
    inner_schema = make_schema(
        id_="inner_schema",
        type_=models.SchemaType(models.Type.object),
        props={"inner_prop": inner_prop_schema},
    )
    outer_prop_schema = make_schema(
        id_="outer_prop_schema",
        type_=models.SchemaType(models.Type.object),
    )
    outer_schema = make_schema(
        id_="outer_schema",
        type_=models.SchemaType(models.Type.object),
        props={"outer_prop": outer_prop_schema},
    )
    outer_schema.all_of = [inner_schema]
    document = make_document(outer_schema, inner_schema, inner_prop_schema, outer_prop_schema)
    sorted_ids = [schema.id for schema in document.sorted_schemas]
    assert sorted_ids.index("inner_prop_schema") < sorted_ids.index("inner_schema")
    assert sorted_ids.index("outer_prop_schema") < sorted_ids.index("outer_schema")
    assert sorted_ids.index("inner_schema") < sorted_ids.index("outer_schema")

def test_sorted_schemas_orders_property_dependencies_with_oneof():
    inner_prop_schema = make_schema(
        id_="inner_prop_schema",
        type_=models.SchemaType(models.Type.object),
    )
    inner_schema = make_schema(
        id_="inner_schema",
        type_=models.SchemaType(models.Type.object),
        props={"inner_prop": inner_prop_schema},
    )
    outer_prop_schema = make_schema(
        id_="outer_prop_schema",
        type_=models.SchemaType(models.Type.object),
    )
    outer_schema = make_schema(
        id_="outer_schema",
        type_=models.SchemaType(models.Type.object),
        props={"outer_prop": outer_prop_schema},
    )
    outer_schema.one_of = [inner_schema]
    document = make_document(outer_schema, inner_schema, inner_prop_schema, outer_prop_schema)
    sorted_ids = [schema.id for schema in document.sorted_schemas]
    assert sorted_ids.index("inner_prop_schema") < sorted_ids.index("inner_schema")
    assert sorted_ids.index("outer_prop_schema") < sorted_ids.index("outer_schema")
    assert sorted_ids.index("inner_schema") < sorted_ids.index("outer_schema")

def test_sorted_schemas_orders_list_items_with_allof():
    inner_item_schema = make_schema(
        id_="inner_item_schema",
        type_=models.SchemaType(models.Type.object),
    )
    inner_list_schema = make_schema(
        id_="inner_list_schema",
        type_=models.SchemaType(models.Type.array),
        items=inner_item_schema,
    )
    inner_schema = make_schema(
        id_="inner_schema",
        type_=models.SchemaType(models.Type.object),
        props={"inner_list": inner_list_schema},
    )
    outer_item_schema = make_schema(
        id_="outer_item_schema",
        type_=models.SchemaType(models.Type.object),
    )
    outer_list_schema = make_schema(
        id_="outer_list_schema",
        type_=models.SchemaType(models.Type.array),
        items=outer_item_schema,
    )
    outer_schema = make_schema(
        id_="outer_schema",
        type_=models.SchemaType(models.Type.object),
        props={"outer_list": outer_list_schema},
    )
    outer_schema.all_of = [inner_schema]
    document = make_document(
        outer_schema,
        inner_schema,
        inner_list_schema,
        outer_list_schema,
        inner_item_schema,
        outer_item_schema,
    )
    sorted_ids = [schema.id for schema in document.sorted_schemas]
    assert sorted_ids.index("inner_item_schema") < sorted_ids.index("inner_list_schema")
    assert sorted_ids.index("inner_list_schema") < sorted_ids.index("inner_schema")
    assert sorted_ids.index("outer_item_schema") < sorted_ids.index("outer_list_schema")
    assert sorted_ids.index("outer_list_schema") < sorted_ids.index("outer_schema")
    assert sorted_ids.index("inner_schema") < sorted_ids.index("outer_schema")

def test_sorted_schemas_orders_list_items_with_oneof():
    inner_item_schema = make_schema(
        id_="inner_item_schema",
        type_=models.SchemaType(models.Type.object),
    )
    inner_list_schema = make_schema(
        id_="inner_list_schema",
        type_=models.SchemaType(models.Type.array),
        items=inner_item_schema,
    )
    inner_schema = make_schema(
        id_="inner_schema",
        type_=models.SchemaType(models.Type.object),
        props={"inner_list": inner_list_schema},
    )
    outer_item_schema = make_schema(
        id_="outer_item_schema",
        type_=models.SchemaType(models.Type.object),
    )
    outer_list_schema = make_schema(
        id_="outer_list_schema",
        type_=models.SchemaType(models.Type.array),
        items=outer_item_schema,
    )
    outer_schema = make_schema(
        id_="outer_schema",
        type_=models.SchemaType(models.Type.object),
        props={"outer_list": outer_list_schema},
    )
    outer_schema.one_of = [inner_schema]
    document = make_document(
        outer_schema,
        inner_schema,
        inner_list_schema,
        outer_list_schema,
        inner_item_schema,
        outer_item_schema,
    )
    sorted_ids = [schema.id for schema in document.sorted_schemas]
    assert sorted_ids.index("inner_item_schema") < sorted_ids.index("inner_list_schema")
    assert sorted_ids.index("inner_list_schema") < sorted_ids.index("inner_schema")
    assert sorted_ids.index("outer_item_schema") < sorted_ids.index("outer_list_schema")
    assert sorted_ids.index("outer_list_schema") < sorted_ids.index("outer_schema")
    assert sorted_ids.index("inner_schema") < sorted_ids.index("outer_schema")

def test_sorted_schemas_orders_list_items_with_oneof_and_allof():
    inner_schema = make_schema(
        id_="inner_schema",
        type_=models.SchemaType(models.Type.object),
    )
    outer_schema = make_schema(
        id_="outer_schema",
        type_=models.SchemaType(models.Type.object),
    )
    oneof_schema = make_schema(
        id_="oneof_schema",
        type_=models.SchemaType(models.Type.object),
    )
    outer_schema.all_of = [inner_schema]
    oneof_schema.one_of = [inner_schema, outer_schema]
    document = make_document(
        outer_schema,
        inner_schema,
        oneof_schema,
    )
    sorted_ids = [schema.id for schema in document.sorted_schemas]
    assert sorted_ids.index("inner_schema") < sorted_ids.index("outer_schema")
    assert sorted_ids.index("inner_schema") < sorted_ids.index("oneof_schema")
    assert sorted_ids.index("outer_schema") < sorted_ids.index("oneof_schema")
