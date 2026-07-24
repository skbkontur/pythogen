from pathlib import Path

import pytest

from jinja2 import Environment
from jinja2 import FileSystemLoader

from pythogen import models
from pythogen.renderer import varname, classname, j2_typerepr, j2_responserepr, iterresponsemap, parameterfield, \
    propertyfield, j2_repr_any_of, docstring_lines, wrap_lines, prepare_operations
from tests.pythogen.model_factories import make_document, make_schema, make_operation_with_body

TEMPLATE_DIR_PATH = Path(__file__).parent.parent.parent.absolute() / Path(
    "pythogen/templates/http_toolkit_client")
TEMPLATE_NAME = "_error_handler.py.j2"

GLOBALS_DICT = {
        "varname": varname,
        "classname": classname,
        "typerepr": j2_typerepr,
        "responserepr": j2_responserepr,
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

def test_custom_error_before_tests(template) -> None:
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
    name = ""
    prepared_operations = prepare_operations(document)
    import_path = None
    rendered_file = template.render(
        sync=True,
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
    assert """class ErrorHandler:
    def __init__(self, error_class: Type[ApiError]):
        self._error_class = error_class

    @contextmanager
    def handle(self):
        try:
            yield
        except HttpError as error:
            response = error.response
            if 400 <= response.status_code < 500:
                raise self._error_class(response=response) from error
            raise ServerError(response.reason) from error""" in rendered_file.strip()
