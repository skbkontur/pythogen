from pythogen import models
from tests.pythogen.model_factories import make_document, make_schema, make_operation_with_response, make_param_obj


def test_nullable_required_object_with_default_value(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
        nullable=True,
        default="default_string_value"
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema},
        required=["prop_schema"],
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop_schema: str | None = Field('default_string_value')""" in rendered_file

def test_not_nullable_required_object_with_default_value(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
        default="default_string_value"
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema},
        required=["prop_schema"],
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop_schema: str = Field('default_string_value')""" in rendered_file

def test_nullable_required_object_without_default_value(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
        nullable=True,
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema},
        required=["prop_schema"],
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop_schema: str | None \n""" in rendered_file

def test_not_nullable_required_object_without_default_value(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string)
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema},
        required=["prop_schema"],
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop_schema: str \n""" in rendered_file

def test_nullable_not_required_object_with_default_value(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
        nullable=True,
        default="default_string_value"
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema}
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop_schema: str | MISSING | None = Field('default_string_value')""" in rendered_file

def test_not_nullable_not_required_object_with_default_value(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
        default="default_string_value"
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema}
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop_schema: str | MISSING = Field('default_string_value')""" in rendered_file

def test_nullable_not_required_object_without_default_value(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
        nullable=True,
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema}
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop_schema: str | MISSING | None = Field(MISSING)""" in rendered_file

def test_not_nullable_not_required_object_without_default_value(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema}
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop_schema: str | MISSING = Field(MISSING)""" in rendered_file

def test_nullable_anyof_required_object_without_default_value(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.object),
    )
    first_prop_schema = make_schema(
        id_="first_prop_schema",
        type_=models.SchemaType(models.Type.string)
    )
    second_prop_schema = make_schema(
        id_="second_prop_schema",
        type_=models.SchemaType(models.Type.null)
    )
    prop_schema.any_of = [first_prop_schema, second_prop_schema]
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema},
        required=["prop_schema"]
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class PropSchema(RootModel):
    root: str | None

class Schema(BaseModel, BaseConfig):
    prop_schema: PropSchema \n""" in rendered_file

def test_nullable_required_object_with_null_default_value(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType([models.Type.string, models.Type.null]),
        default=None,
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema},
        required=["prop_schema"]
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop_schema: str | None = Field(None)""" in rendered_file

def test_all_of_single_schema_parameter_uses_not_inline_schema_model(responses_model_generation_template):
    inner_prop_schema = make_schema(
        id_="inner_prop_schema",
        type_=models.SchemaType(models.Type.string),
    )
    inner_schema = make_schema(
        id_="inner_schema",
        type_=models.SchemaType(models.Type.object),
        props={"name": inner_prop_schema},
    )
    prop_schema = make_schema(
        id_="prop_ref_obj",
        type_=models.SchemaType(models.Type.object),
    )
    prop_schema.all_of = [inner_schema]
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop": prop_schema},
        required=["prop"],
    )
    document = make_document(schema, prop_schema, inner_schema)
    assert "prop_ref_obj" in document.schemas
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop: InnerSchema \n""" in rendered_file
    assert """class InnerSchema(BaseModel, BaseConfig):
    name: str | MISSING = Field(MISSING)\n""" in rendered_file
    assert "class PropRefObj" not in rendered_file

def test_all_of_multiple_schemas_parameter_uses_ref_obj_model(responses_model_generation_template):
    first_prop_schema = make_schema(
        id_="first_prop_schema",
        type_=models.SchemaType(models.Type.string),
    )
    first_schema = make_schema(
        id_="first_schema",
        type_=models.SchemaType(models.Type.object),
        props={"name": first_prop_schema},
    )
    second_prop_schema = make_schema(
        id_="second_prop_schema",
        type_=models.SchemaType(models.Type.string),
    )
    second_schema = make_schema(
        id_="second_schema",
        type_=models.SchemaType(models.Type.object),
        props={"value": second_prop_schema},
    )
    prop_schema = make_schema(
        id_="prop_ref_obj",
        type_=models.SchemaType(models.Type.object),
    )
    prop_schema.all_of = [first_schema, second_schema]
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        props={"prop": prop_schema},
        required=["prop"],
    )
    document = make_document(schema, prop_schema, first_schema, second_schema)
    assert "prop_ref_obj" in document.schemas
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert """class Schema(BaseModel, BaseConfig):
    prop: PropRefObj \n""" in rendered_file

    assert """class PropRefObj(
    FirstSchema, 
    SecondSchema, BaseConfig\n):""" in rendered_file

    assert """class FirstSchema(BaseModel, BaseConfig):
    name: str | MISSING = Field(MISSING)""" in rendered_file

    assert """class SecondSchema(BaseModel, BaseConfig):
    value: str | MISSING = Field(MISSING)""" in rendered_file

def test_required_path_param_generates_without_missing_sentinel(requests_model_generation_template):
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-something",
        response_schema=None,
    )
    path_param_schema = make_schema(
        id_="path_param_schema",
        type_=models.SchemaType(models.Type.string),
    )
    path_parameter = make_param_obj(
        id_="path_parameter",
        orig_key="path_parameter",
        location=models.ParameterLocation.path,
        schema=path_param_schema,
        required=True
    )
    operation.parameters.append(path_parameter)
    document = make_document(path_param_schema)
    rendered_file = requests_model_generation_template.render(
        document=document,
        models=document.sorted_schemas,
        operations=([operation])
    )
    assert """class GetSomethingPathParams(BaseModel, BaseConfig):
    path_parameter: str = Field(alias="path_parameter")""" in rendered_file

def test_not_required_path_param_generates_with_missing_sentinel(requests_model_generation_template):
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-something",
        response_schema=None,
    )
    path_param_schema = make_schema(
        id_="path_param_schema",
        type_=models.SchemaType(models.Type.string),
    )
    path_parameter = make_param_obj(
        id_="path_parameter",
        orig_key="path_parameter",
        location=models.ParameterLocation.path,
        schema=path_param_schema,
    )
    operation.parameters.append(path_parameter)
    document = make_document(path_param_schema)
    rendered_file = requests_model_generation_template.render(
        document=document,
        models=document.sorted_schemas,
        operations=([operation])
    )
    assert """class GetSomethingPathParams(BaseModel, BaseConfig):
    path_parameter: str | MISSING = Field(MISSING, alias="path_parameter")""" in rendered_file

def test_required_query_param_generates_without_missing_sentinel(requests_model_generation_template):
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-something",
        response_schema=None,
    )
    query_param_schema = make_schema(
        id_="query_param_schema",
        type_=models.SchemaType(models.Type.string),
    )
    query_parameter = make_param_obj(
        id_="query_parameter",
        orig_key="query_parameter",
        location=models.ParameterLocation.query,
        schema=query_param_schema,
        required=True
    )
    operation.parameters.append(query_parameter)
    document = make_document(query_param_schema)
    rendered_file = requests_model_generation_template.render(
        document=document,
        models=document.sorted_schemas,
        operations=([operation])
    )
    assert """class GetSomethingQueryParams(BaseModel, BaseConfig):
    query_parameter: str = Field(alias="query_parameter")""" in rendered_file

def test_not_required_query_param_generates_with_missing_sentinel(requests_model_generation_template):
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-something",
        response_schema=None,
    )
    query_param_schema = make_schema(
        id_="query_param_schema",
        type_=models.SchemaType(models.Type.string),
    )
    query_parameter = make_param_obj(
        id_="query_parameter",
        orig_key="query_parameter",
        location=models.ParameterLocation.query,
        schema=query_param_schema,
    )
    operation.parameters.append(query_parameter)
    document = make_document(query_param_schema)
    rendered_file = requests_model_generation_template.render(
        document=document,
        models=document.sorted_schemas,
        operations=([operation])
    )
    assert """class GetSomethingQueryParams(BaseModel, BaseConfig):
    query_parameter: str | MISSING = Field(MISSING, alias="query_parameter")""" in rendered_file

def test_required_headers_generates_without_missing_sentinel(requests_model_generation_template):
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-something",
        response_schema=None,
    )
    header_schema = make_schema(
        id_="header_schema",
        type_=models.SchemaType(models.Type.string),
    )
    header_parameter = make_param_obj(
        id_="header",
        orig_key="header",
        location=models.ParameterLocation.header,
        schema=header_schema,
        required=True
    )
    operation.parameters.append(header_parameter)
    document = make_document(header_schema)
    rendered_file = requests_model_generation_template.render(
        document=document,
        models=document.sorted_schemas,
        operations=([operation])
    )
    assert """class GetSomethingHeaders(BaseModel, BaseConfig):
    header: str = Field(alias="header")""" in rendered_file

def test_not_required_headers_generates_with_missing_sentinel(requests_model_generation_template):
    operation = make_operation_with_response(
        method=models.HttpMethod.get,
        operation_id="get-something",
        response_schema=None,
    )
    header_schema = make_schema(
        id_="header_schema",
        type_=models.SchemaType(models.Type.string),
    )
    header_parameter = make_param_obj(
        id_="header",
        orig_key="header",
        location=models.ParameterLocation.header,
        schema=header_schema,
    )
    operation.parameters.append(header_parameter)
    document = make_document(header_schema)
    rendered_file = requests_model_generation_template.render(
        document=document,
        models=document.sorted_schemas,
        operations=([operation])
    )
    assert """class GetSomethingHeaders(BaseModel, BaseConfig):
    header: str | MISSING = Field(MISSING, alias="header")""" in rendered_file


_LONG_SCHEMA_TITLE = (
    "This is a long schema title, exceeding the 119 character limit, and for this reason it will wrap to prevent the "
    "following error: E501 line too long"
)
_MULTILINE_SCHEMA_DESCRIPTION = (
    """This is a multi-line docstring. The length of some lines may exceed 119 characters. However, it must fit """
    """within 119 characters, including all indentations. In addition to the specified line length limitation, it is """
    """also important to maintain the readability of the text and the author's formatting. The following applies:\n"""
    """- All original line breaks must be preserved to ensure the text remains legible and reflects the author's """
    """original formatting\n"""
    """- Any short line must be unaffected\n"""
    """- Any long line that exceeds the 119 character limit should wrap at the last space instead of a word break """
    """to ensure the text remains legible\n"""
    """- Any long word that do not contain spaces (e.g. hyperlink) will break to fit the line: """
    """https://this-is-a-long-domain-name.example.com/this/is/a/long/url/path/that/obviously/will/not/follow/"""
    """described/length/requirements/with/just/a/119/symbols"""
)
_EXPECTED_MULTILINE_DOCSTRING = """
    This is a long schema title, exceeding the 119 character limit, and for this reason it will wrap to prevent the
    following error: E501 line too long
    This is a multi-line docstring. The length of some lines may exceed 119 characters. However, it must fit within 119
    characters, including all indentations. In addition to the specified line length limitation, it is also important
    to maintain the readability of the text and the author's formatting. The following applies:
    - All original line breaks must be preserved to ensure the text remains legible and reflects the author's original
    formatting
    - Any short line must be unaffected
    - Any long line that exceeds the 119 character limit should wrap at the last space instead of a word break to
    ensure the text remains legible
    - Any long word that do not contain spaces (e.g. hyperlink) will break to fit the line:
    https://this-is-a-long-domain-name.example.com/this/is/a/long/url/path/that/obviously/will/not/follow/described/len
    gth/requirements/with/just/a/119/symbols
"""


def test_multiline_text(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
        description="Multiline text\\r\\nwith\\rall\\ntypes\r\nof\rline\nseparators",
    )
    schema = make_schema(
        id_="schema",
        type_=models.SchemaType(models.Type.object),
        title=_LONG_SCHEMA_TITLE,
        description=_MULTILINE_SCHEMA_DESCRIPTION,
        props={"prop_schema": prop_schema},
        required=["prop_schema"],
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert (
        """class Schema(BaseModel, BaseConfig):\n"""
        f'    """{_EXPECTED_MULTILINE_DOCSTRING}'
        '    """\n'
        """    prop_schema: str = Field(..., description="Multiline text with all types of line separators")\n"""
    ) in rendered_file


def test_model_name_collision(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
    )
    schema = make_schema(
        id_="base_model",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema},
        required=["prop_schema"],
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert (
        """class BaseModelModel(BaseModel, BaseConfig):\n"""
        """    prop_schema: str \n"""
    ) in rendered_file


def test_model_name_underscores(responses_model_generation_template):
    prop_schema = make_schema(
        id_="prop_schema",
        type_=models.SchemaType(models.Type.string),
    )
    schema = make_schema(
        id_="_underscores_schema_",
        type_=models.SchemaType(models.Type.object),
        props={"prop_schema": prop_schema},
        required=["prop_schema"],
    )
    document = make_document(schema, prop_schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert (
        """class UnderscoresSchema(BaseModel, BaseConfig):\n"""
        """    prop_schema: str \n"""
    ) in rendered_file

def test_empty_object(responses_model_generation_template):
    schema = make_schema(
        id_="empty_object",
        type_=models.SchemaType(models.Type.object)
    )
    document = make_document(schema)
    rendered_file = responses_model_generation_template.render(
        document=document,
        models=document.sorted_schemas
    )
    assert (
        """class EmptyObject(BaseModel, BaseConfig):\n"""
        """    ..."""
    ) in rendered_file
