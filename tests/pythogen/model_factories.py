from typing import Any

import pytest
from pythogen import models


def make_document(*schemas: models.SchemaObject) -> models.Document:
    return models.Document(
        info=models.InfoObject(title="test", version="test"),
        paths={},
        parameters={},
        schemas={schema.id: schema for schema in schemas},
        discriminator_base_class_schemas=[],
    )

def make_schema(
        id_: str,
        type_: models.SchemaType,
        title: str | None = None,
        description: str | None = None,
        enum: list[str] | None = None,
        format_: models.Format | None = None,
        items: models.SchemaObject | list[models.SchemaObject] | None = None,
        props: dict[str, models.SchemaObject] | None = None,
        required: list[str] | None = None,
        nullable: bool = False,
        default: Any | None = models.UNDEFINED,
) -> models.SchemaObject:
    return models.SchemaObject(
        id=id_,
        title=title,
        description=description,
        enum=enum,
        type=type_,
        format=format_,
        items=items,
        properties=[
            models.SchemaProperty(orig_key=k, safety_key=None, schema=v)
            for k, v in (props or {}).items()
        ],
        required=[] if required is None else required,
        nullable=nullable,
        default=default,
    )

def make_operation_with_body(
        method: models.HttpMethod,
        operation_id: str,
        body_schema: models.SchemaObject,
) -> models.OperationObject:
    request_body = models.RequestBodyObject(
        id="body",
        description=None,
        schema=body_schema,
        required=False,
        is_form_data=False,
        is_multipart_form_data=False,
        are_files_required=False,
    )
    return models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=operation_id,
        request_body=request_body,
        responses=models.ResponsesObject(
            patterned={}
        ),
        parameters=[],
        path_str="test"
    )

def make_responses(schema: models.SchemaObject | None, code: int = 200) -> models.ResponsesObject:
    return models.ResponsesObject(
        patterned={
            str(code): models.ResponseObject(
                id="resp",
                description="",
                status_code=code,
                schema=schema,
            )
        },
    )

def make_operation_with_response(
        method: models.HttpMethod,
        operation_id: str,
        response_schema: models.SchemaObject | None,
        status_code: int = 200,
        path_str: str = "test",
) -> models.OperationObject:
    response = models.ResponseObject(
        id="response",
        description="",
        status_code=status_code,
        schema=response_schema,
    )
    return models.OperationObject(
        method=method,
        summary=None,
        description=None,
        operation_id=operation_id,
        request_body=None,
        responses=models.ResponsesObject(
            patterned={
                str(status_code): response
            }
        ),
        parameters=[],
        path_str=path_str,
    )

def make_param_obj(
        id_: str,
        orig_key: str,
        location: models.ParameterLocation,
        schema: models.SchemaObject,
        required: bool = False,
) -> models.ParameterObject:
    return models.ParameterObject(
        id=id_,
        orig_key=orig_key,
        safety_key=None,
        description=None,
        location=location,
        required=required,
        schema=schema
    )
