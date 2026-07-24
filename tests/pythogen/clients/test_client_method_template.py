from pathlib import Path
import pytest
from pythogen import models
from pythogen.renderer import classname, j2_is_optional_response, j2_typerepr, j2_responserepr, iterresponsemap, \
    PRIMITIVE_TYPE_MAPPING, FORMAT_MAPPING
from jinja2 import Environment
from jinja2 import FileSystemLoader

from tests.pythogen.model_factories import make_schema, make_document

TEMPLATE_DIR_PATH = Path(__file__).parent.parent.parent.parent.absolute() / Path("pythogen/templates/http_toolkit_client/clients")
TEMPLATE_NAME = "!method.j2"
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

@pytest.fixture(scope="module", autouse=True)
def template():
    assert (TEMPLATE_DIR_PATH / TEMPLATE_NAME).exists()
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR_PATH), extensions=["jinja2.ext.loopcontrols"])
    globals_dict = {
        "classname": classname,
        "typerepr": j2_typerepr,
        "responserepr": j2_responserepr,
        "is_optional_response": j2_is_optional_response,
        "iterresponsemap": iterresponsemap,
    }
    template = env.get_template(
        TEMPLATE_NAME,
        globals=globals_dict,
    )
    return template

@pytest.mark.parametrize("method", METHODS)
def test_simple_successful_method(template, method: models.HttpMethod) -> None:
    document = models.Document(
        info=models.InfoObject(
            title="test",
            version="test"
        ),
        paths={},
        parameters={},
        schemas={},
        discriminator_base_class_schemas=[]
    )

    operation = models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=f"simple-{method.value}",
        request_body=None,
        responses=models.ResponsesObject(
            patterned={
                "200": models.ResponseObject(
                    id="test",
                    description="test",
                    status_code=200,
                    schema=None
                )
            }
        ),
        parameters=[],
        path_str="/test"
    )
    items = [("/test", operation)]
    sync = True
    rendered_file = template.render(
        document=document,
        items=items,
        sync=sync,
        method=method.value,
    )
    expected = f"""def simple_{method.value}(
        self,
    ) -> None:
        path = '/test'
        with self._error_handler.handle():
            response = self.{method.value}(
                path)
        return None"""
    assert expected == rendered_file.strip()

@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_primitive_body_successful_method(template, method: models.HttpMethod, primitive_type: models.Type) -> None:
    document = models.Document(
        info=models.InfoObject(
            title="test",
            version="test"
        ),
        paths={},
        parameters={},
        schemas={
            "test-body-schema": models.SchemaObject(
                id="test-body-schema",
                title=None,
                enum=None,
                type=models.SchemaType(primitive_type),
                format=None,
                items=None,
                properties=[],
                default=models.UNDEFINED
            )
        },
        discriminator_base_class_schemas=[]
    )

    operation = models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=f"simple-{method.value}",
        request_body=models.RequestBodyObject(
            id="test-body",
            description=None,
            schema=models.SchemaObject(
                id="test-body-schema",
                title=None,
                enum=None,
                type=models.SchemaType(primitive_type),
                format=None,
                items=None,
                properties=[],
                default=models.UNDEFINED
            ),
            required=False,
            is_form_data=False,
            is_multipart_form_data=False,
            are_files_required=False
        ),
        responses=models.ResponsesObject(
            patterned={
                "200": models.ResponseObject(
                    id="test",
                    description="test",
                    status_code=200,
                    schema=None
                )
            }
        ),
        parameters=[],
        path_str="/test"
    )
    items = [("/test", operation)]
    sync = True
    rendered_file = template.render(
        document=document,
        items=items,
        sync=sync,
        method=method.value,
    )
    expected = f'''def simple_{method.value}(
        self,
        body: {PRIMITIVE_TYPE_MAPPING[primitive_type]},
    ) -> None:
        path = '/test'
        json = body
        with self._error_handler.handle():
            response = self.{method.value}(
                path, body=json)
        return None'''
    assert expected == rendered_file.strip()

@pytest.mark.parametrize("method", METHODS)
def test_dict_any_body_successful_method(template, method: models.HttpMethod) -> None:
    document = models.Document(
        info=models.InfoObject(
            title="test",
            version="test"
        ),
        paths={},
        parameters={},
        schemas={
            "test-body-schema": models.SchemaObject(
                id="test-body-schema",
                title=None,
                enum=None,
                type=models.SchemaType(models.Type.object),
                format=None,
                items=None,
                properties=[],
                default=models.UNDEFINED
            )
        },
        discriminator_base_class_schemas=[]
    )

    operation = models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=f"simple-{method.value}",
        request_body=models.RequestBodyObject(
            id="test-body",
            description=None,
            schema=models.SchemaObject(
                id="test-body-schema",
                title=None,
                enum=None,
                type=models.SchemaType(models.Type.object),
                format=None,
                items=None,
                properties=[],
                default=models.UNDEFINED
            ),
            required=False,
            is_form_data=False,
            is_multipart_form_data=False,
            are_files_required=False
        ),
        responses=models.ResponsesObject(
            patterned={
                "200": models.ResponseObject(
                    id="test",
                    description="test",
                    status_code=200,
                    schema=None
                )
            }
        ),
        parameters=[],
        path_str="/test"
    )
    items = [("/test", operation)]
    sync = True
    rendered_file = template.render(
        document=document,
        items=items,
        sync=sync,
        method=method.value,
    )
    expected = f'''def simple_{method.value}(
        self,
        body: dict[Any, Any],
    ) -> None:
        path = '/test'
        json = body
        with self._error_handler.handle():
            response = self.{method.value}(
                path, json=json)
        return None'''
    assert expected == rendered_file.strip()
    
@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("primitive_type", PRIMITIVE_TYPES)
def test_model_body_successful_method(template, method: models.HttpMethod, primitive_type: models.Type) -> None:
    document = models.Document(
        info=models.InfoObject(
            title="test",
            version="test"
        ),
        paths={},
        parameters={},
        schemas={
            "test-body-schema": models.SchemaObject(
                id="test-body-schema",
                title=None,
                enum=None,
                type=models.SchemaType(models.Type.object),
                format=None,
                items=None,
                properties=[
                    models.SchemaProperty(
                        orig_key="test-prop",
                        safety_key=None,
                        schema=models.SchemaObject(
                            id="test-prop-schema",
                            title=None,
                            enum=None,
                            type=models.SchemaType(primitive_type),
                            format=None,
                            items=None,
                            properties=[],
                            default=models.UNDEFINED
                        )
                    )
                ],
                default=models.UNDEFINED
            ),
            "test-prop": models.SchemaObject(
                id="test-prop-schema",
                title=None,
                enum=None,
                type=models.SchemaType(primitive_type),
                format=None,
                items=None,
                properties=[],
                default=models.UNDEFINED
            )
        },
        discriminator_base_class_schemas=[]
    )

    operation = models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=f"simple-{method.value}",
        request_body=models.RequestBodyObject(
            id="test-body",
            description=None,
            schema=models.SchemaObject(
                id="test-body-schema",
                title=None,
                enum=None,
                type=models.SchemaType(models.Type.object),
                format=None,
                items=None,
                properties=[
                    models.SchemaProperty(
                        orig_key="test-prop",
                        safety_key=None,
                        schema=models.SchemaObject(
                            id="test-prop-schema",
                            title=None,
                            enum=None,
                            type=models.SchemaType(primitive_type),
                            format=None,
                            items=None,
                            properties=[],
                            default=models.UNDEFINED
                        )
                    )
                ],
                default=models.UNDEFINED
            ),
            required=False,
            is_form_data=False,
            is_multipart_form_data=False,
            are_files_required=False
        ),
        responses=models.ResponsesObject(
            patterned={
                "200": models.ResponseObject(
                    id="test",
                    description="test",
                    status_code=200,
                    schema=None
                )
            }
        ),
        parameters=[],
        path_str="/test"
    )
    items = [("/test", operation)]
    sync = True
    rendered_file = template.render(
        document=document,
        items=items,
        sync=sync,
        method=method.value,
    )
    expected = f'''def simple_{method.value}(
        self,
        body: TestBodySchema,
    ) -> None:
        path = '/test'
        json = body.model_dump(by_alias=True, mode="json")
        with self._error_handler.handle():
            response = self.{method.value}(
                path, json=json)
        return None'''
    assert expected == rendered_file.strip()

@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("format", FORMATS)
def test_model_nonprimitive_prop_body_successful_method(template, method: models.HttpMethod, format: models.Format) -> None:
    document = models.Document(
        info=models.InfoObject(
            title="test",
            version="test"
        ),
        paths={},
        parameters={},
        schemas={
            "test-body-schema": models.SchemaObject(
                id="test-body-schema",
                title=None,
                enum=None,
                type=models.SchemaType(models.Type.object),
                format=None,
                items=None,
                properties=[
                    models.SchemaProperty(
                        orig_key="test-prop",
                        safety_key=None,
                        schema=models.SchemaObject(
                            id="test-prop-schema",
                            title=None,
                            enum=None,
                            type=models.SchemaType(models.Type.string),
                            format=format,
                            items=None,
                            properties=[],
                            default=models.UNDEFINED
                        )
                    )
                ],
                default=models.UNDEFINED
            )
        },
        discriminator_base_class_schemas=[]
    )

    operation = models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=f"simple-{method.value}",
        request_body=models.RequestBodyObject(
            id="test-body",
            description=None,
            schema=models.SchemaObject(
                id="test-body-schema",
                title=None,
                enum=None,
                type=models.SchemaType(models.Type.object),
                format=None,
                items=None,
                properties=[
                    models.SchemaProperty(
                        orig_key="test-prop",
                        safety_key=None,
                        schema=models.SchemaObject(
                            id="test-prop-schema",
                            title=None,
                            enum=None,
                            type=models.SchemaType(models.Type.string),
                            format=format,
                            items=None,
                            properties=[],
                            default=models.UNDEFINED
                        )
                    )
                ],
                default=models.UNDEFINED
            ),
            required=False,
            is_form_data=False,
            is_multipart_form_data=False,
            are_files_required=False
        ),
        responses=models.ResponsesObject(
            patterned={
                "200": models.ResponseObject(
                    id="test",
                    description="test",
                    status_code=200,
                    schema=None
                )
            }
        ),
        parameters=[],
        path_str="/test"
    )
    items = [("/test", operation)]
    sync = True
    rendered_file = template.render(
        document=document,
        items=items,
        sync=sync,
        method=method.value,
    )
    expected = f'''def simple_{method.value}(
        self,
        body: TestBodySchema,
    ) -> None:
        path = '/test'
        json = body.model_dump(by_alias=True, mode="json")
        with self._error_handler.handle():
            response = self.{method.value}(
                path, json=json)
        return None'''
    assert expected == rendered_file.strip()

@pytest.mark.parametrize("method", METHODS)
def test_list_body_successful_method(template, method: models.HttpMethod) -> None:
    document = models.Document(
        info=models.InfoObject(
            title="test",
            version="test"
        ),
        paths={},
        parameters={},
        schemas={
            "test-body-schema": models.SchemaObject(
                id="test-body-schema",
                title=None,
                enum=None,
                type=models.SchemaType(models.Type.array),
                format=None,
                items=models.SchemaObject(
                    id="test-list-item-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.object),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                ),
                properties=[],
                default=models.UNDEFINED
            ),
            "test-list-item-schema": models.SchemaObject(
                id="test-list-item-schema",
                title=None,
                enum=None,
                type=models.SchemaType(models.Type.object),
                format=None,
                items=None,
                properties=[],
                default=models.UNDEFINED
            )
        },
        discriminator_base_class_schemas=[]
    )

    operation = models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=f"simple-{method.value}",
        request_body=models.RequestBodyObject(
            id="test-body",
            description=None,
            schema=models.SchemaObject(
                id="test-body-schema",
                title=None,
                enum=None,
                type=models.SchemaType(models.Type.array),
                format=None,
                items=models.SchemaObject(
                    id="test-list-item-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.object),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                ),
                properties=[],
                default=models.UNDEFINED
            ),
            required=False,
            is_form_data=False,
            is_multipart_form_data=False,
            are_files_required=False
        ),
        responses=models.ResponsesObject(
            patterned={
                "200": models.ResponseObject(
                    id="test",
                    description="test",
                    status_code=200,
                    schema=None
                )
            }
        ),
        parameters=[],
        path_str="/test"
    )
    items = [("/test", operation)]
    sync = True
    rendered_file = template.render(
        document=document,
        items=items,
        sync=sync,
        method=method.value,
    )
    expected = f'''def simple_{method.value}(
        self,
        body: list[dict[Any, Any]],
    ) -> None:
        path = '/test'
        json = [item.model_dump(by_alias=True, mode="json") for item in body]
        with self._error_handler.handle():
            response = self.{method.value}(
                path, json=json)
        return None'''
    assert expected == rendered_file.strip()

@pytest.mark.parametrize("method", METHODS)
def test_path_params_successful_method(template, method: models.HttpMethod) -> None:
    document = models.Document(
        info=models.InfoObject(
            title="test",
            version="test"
        ),
        paths={},
        parameters={},
        schemas={},
        discriminator_base_class_schemas=[]
    )

    operation = models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=f"simple-{method.value}",
        request_body=None,
        responses=models.ResponsesObject(
            patterned={
                "200": models.ResponseObject(
                    id="test",
                    description="test",
                    status_code=200,
                    schema=None
                )
            }
        ),
        parameters=[
            models.ParameterObject(
                id="test-param",
                orig_key="test-param",
                safety_key=None,
                description=None,
                location=models.ParameterLocation.path,
                required=False,
                schema=models.SchemaObject(
                    id="test-param-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.string),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                )
            )
        ],
        path_str="/test"
    )
    items = [("/test", operation)]
    sync = True
    rendered_file = template.render(
        document=document,
        items=items,
        sync=sync,
        method=method.value,
    )
    expected = f'''def simple_{method.value}(
        self,
        path_params: Simple{method.value.capitalize()}PathParams,
    ) -> None:
        path = '/test'.format(**path_params.model_dump(by_alias=True, mode="json"))
        with self._error_handler.handle():
            response = self.{method.value}(
                path)
        return None'''
    assert expected == rendered_file.strip()

@pytest.mark.parametrize("method", METHODS)
def test_query_params_successful_method(template, method: models.HttpMethod) -> None:
    document = models.Document(
        info=models.InfoObject(
            title="test",
            version="test"
        ),
        paths={},
        parameters={},
        schemas={},
        discriminator_base_class_schemas=[]
    )

    operation = models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=f"simple-{method.value}",
        request_body=None,
        responses=models.ResponsesObject(
            patterned={
                "200": models.ResponseObject(
                    id="test",
                    description="test",
                    status_code=200,
                    schema=None
                )
            }
        ),
        parameters=[
            models.ParameterObject(
                id="test-param",
                orig_key="test-param",
                safety_key=None,
                description=None,
                location=models.ParameterLocation.query,
                required=False,
                schema=models.SchemaObject(
                    id="test-param-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.string),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                )
            )
        ],
        path_str="/test"
    )
    items = [("/test", operation)]
    sync = True
    rendered_file = template.render(
        document=document,
        items=items,
        sync=sync,
        method=method.value,
    )
    expected = f'''def simple_{method.value}(
        self,
        query_params: Simple{method.value.capitalize()}QueryParams,
    ) -> None:
        path = '/test'
        params = query_params.model_dump(by_alias=True, mode="json", exclude_none=True)
        with self._error_handler.handle():
            response = self.{method.value}(
                path, params=params)
        return None'''
    assert expected == rendered_file.strip()

@pytest.mark.parametrize("method", METHODS)
def test_headers_successful_method(template, method: models.HttpMethod) -> None:
    document = models.Document(
        info=models.InfoObject(
            title="test",
            version="test"
        ),
        paths={},
        parameters={},
        schemas={},
        discriminator_base_class_schemas=[]
    )

    operation = models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=f"simple-{method.value}",
        request_body=None,
        responses=models.ResponsesObject(
            patterned={
                "200": models.ResponseObject(
                    id="test",
                    description="test",
                    status_code=200,
                    schema=None
                )
            }
        ),
        parameters=[
            models.ParameterObject(
                id="test-param",
                orig_key="test-param",
                safety_key=None,
                description=None,
                location=models.ParameterLocation.header,
                required=False,
                schema=models.SchemaObject(
                    id="test-param-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.string),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                )
            )
        ],
        path_str="/test"
    )
    items = [("/test", operation)]
    sync = True
    rendered_file = template.render(
        document=document,
        items=items,
        sync=sync,
        method=method.value,
    )
    expected = f'''def simple_{method.value}(
        self,
        headers: Simple{method.value.capitalize()}Headers | None = None,
    ) -> None:
        path = '/test'
        headers_ = self.convert_headers(headers)
        with self._error_handler.handle():
            response = self.{method.value}(
                path, headers=headers_)
        return None'''
    assert expected == rendered_file.strip()

def test_optional_response(template) -> None:
    schema = make_schema(
        id_="resp-schema",
        type_=models.SchemaType(models.Type.string),
        nullable=True,
    )
    document = make_document(schema)
    operation = models.OperationObject(
        method=models.HttpMethod.get,
        summary=None,
        description=None,
        operation_id="simple-get",
        request_body=None,
        responses=models.ResponsesObject(
            patterned={
                "200": models.ResponseObject(
                    id="test",
                    description="test",
                    status_code=200,
                    schema=schema
                )
            }
        ),
        parameters=[],
        path_str="/test"
    )

    rendered_file = template.render(
        document=document,
        items=[("/test", operation)],
        sync=True,
        method="get",
    )
    assert "    ) -> str | None:" in rendered_file
    assert "if not response.content:\n            return None" in rendered_file
    assert "        return response.text" in rendered_file
