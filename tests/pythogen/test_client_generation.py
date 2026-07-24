from pathlib import Path

import pytest

from jinja2 import Environment
from jinja2 import FileSystemLoader

from pythogen import models
from pythogen.renderer import varname, classname, j2_is_optional_response, j2_typerepr, j2_responserepr, \
    iterresponsemap, parameterfield, propertyfield, j2_repr_any_of, docstring_lines, wrap_lines, prepare_operations
from tests.pythogen.model_factories import make_document, make_schema, make_operation_with_body

TEMPLATE_DIR_PATH = Path(__file__).parent.parent.parent.absolute() / Path(
    "pythogen/templates/http_toolkit_client")
TEMPLATE_NAME = "/clients/!client.j2"

GLOBALS_DICT = {
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
        "line_length": 119,
    }

@pytest.fixture(scope="module", autouse=True)
def template():
    assert (TEMPLATE_DIR_PATH / TEMPLATE_NAME).exists
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR_PATH), extensions=["jinja2.ext.loopcontrols"])
    template = env.get_template(
        TEMPLATE_NAME,
        globals=GLOBALS_DICT,
    )
    return template

def render_for_schema(template, schema: models.SchemaObject) -> str:
    document = make_document(schema)
    operation = make_operation_with_body(
        method=models.HttpMethod.post,
        operation_id="post",
        body_schema=schema,
    )
    path = operation.path_str
    document.paths = {
        path: models.PathItemObject(
            summary=None,
            description=None,
            operations={models.HttpMethod.post: operation},
        )
    }

    prepared_operations = prepare_operations(document)

    rendered_file = template.render(
        sync=True,
        document=document,
        name="",
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
        import_path=None,
    )
    return rendered_file

def test_custom_error_before_tests(template) -> None:
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string))
    rendered_file = render_for_schema(template, schema)
    assert """class Client(Service):

    def __init__(
        self,
        headers: tuple[Header, ...] = (),
        error_class: Type[ApiError] = ApiError,
        transport: BaseTransport = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            transport=transport or HttpxTransport(*args, **kwargs),
            headers=headers
        )
        self._error_handler = ErrorHandler(error_class)""" in rendered_file.strip()
    assert """
        with self._error_handler.handle():
            response = self.post(
                path, body=json)""" in rendered_file.strip()

def test_primitive_body(template):
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.string))
    rendered_file = render_for_schema(template, schema)
    assert "json = body\n" in rendered_file
    assert "path, body=json" in rendered_file
    assert "path, json=json" not in rendered_file
    assert "model_dump(by_alias=True" not in rendered_file

def test_array_of_primitives_body(template):
    item_schema = make_schema(id_="item", type_=models.SchemaType(models.Type.string))
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.array))
    schema.items = item_schema
    rendered_file = render_for_schema(template, schema)
    assert "json = body" in rendered_file
    assert "path, json=json" in rendered_file
    assert "path, body=json" not in rendered_file
    assert "model_dump(by_alias=True" not in rendered_file

def test_array_of_objects_body(template):
    item_schema = make_schema(id_="item", type_=models.SchemaType(models.Type.object))
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.array))
    schema.items = item_schema
    rendered_file = render_for_schema(template, schema)
    assert "[item.model_dump(by_alias=True, mode=\"json\") for item in body]" in rendered_file
    assert "path, json=json" in rendered_file
    assert "path, body=json" not in rendered_file

def test_empty_object_body(template):
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.object))
    rendered_file = render_for_schema(template, schema)
    assert "json = body" in rendered_file
    assert "path, json=json" in rendered_file
    assert "path, body=json" not in rendered_file

def test_object_with_prop_body(template):
    prop_schema = make_schema(id_="prop", type_=models.SchemaType(models.Type.string))
    schema = make_schema(id_="schema", type_=models.SchemaType(models.Type.object), props={"prop": prop_schema})
    rendered_file = render_for_schema(template, schema)
    assert "json = body.model_dump(by_alias=True, mode=\"json\")" in rendered_file
    assert "path, json=json" in rendered_file
    assert "path, body=json" not in rendered_file
