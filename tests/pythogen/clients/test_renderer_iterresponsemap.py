from pythogen.renderer import iterresponsemap
from pythogen import models
import pytest

def test_iterresponsemap_none() -> None:
    responses = models.ResponsesObject(
        patterned={
            "200": models.ResponseObject(
                id="test-response",
                description="test-response",
                status_code=200,
                schema=None
            )
        }
    )
    code, mapper = iterresponsemap(responses)[0]
    assert code == "200"
    assert mapper == "None"

def test_iterresponsemap_empty_object() -> None:
    responses = models.ResponsesObject(
        patterned={
            "200": models.ResponseObject(
                id="test-response",
                description="test-response",
                status_code=200,
                schema=models.SchemaObject(
                    id="test-response-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.object),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                )
            )
        }
    )
    code, mapper = iterresponsemap(responses)[0]
    assert code == "200"
    assert mapper == "response.json()"

def test_iterresponsemap_not_empty_object() -> None:
    responses = models.ResponsesObject(
        patterned={
            "200": models.ResponseObject(
                id="test-response",
                description="test-response",
                status_code=200,
                schema=models.SchemaObject(
                    id="test-response-schema",
                    title=None,
                    enum=["Test", "Enum"],
                    type=models.SchemaType(models.Type.object),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                )
            )
        }
    )
    code, mapper = iterresponsemap(responses)[0]
    assert code == "200"
    assert mapper == "TestResponseSchema.model_validate(response.json())"

def test_iterresponsemap_any_of() -> None:
    responses = models.ResponsesObject(
        patterned={
            "200": models.ResponseObject(
                id="test-response",
                description="test-response",
                status_code=200,
                schema=models.SchemaObject(
                    id="test-response-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.string),
                    format=None,
                    items=None,
                    properties=[],
                    any_of=[
                        models.SchemaObject(
                            id="first-item",
                            title=None,
                            enum=None,
                            type=models.SchemaType(models.Type.object),
                            format=None,
                            items=None,
                            properties=[],
                            default=models.UNDEFINED
                        ),
                        models.SchemaObject(
                            id="second-item",
                            title=None,
                            enum=None,
                            type=models.SchemaType(models.Type.object),
                            format=None,
                            items=None,
                            properties=[],
                            default=models.UNDEFINED
                        )
                    ],
                    default=models.UNDEFINED
                )
            )
        }
    )
    code, mapper = iterresponsemap(responses)[0]
    assert code == "200"
    assert mapper == "self._parse_any_of(response.json(), [FirstItem, SecondItem])"

def test_iterresponsemap_empty_array() -> None:
    responses = models.ResponsesObject(
        patterned={
            "200": models.ResponseObject(
                id="test-response",
                description="test-response",
                status_code=200,
                schema=models.SchemaObject(
                    id="test-response-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.array),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                )
            )
        }
    )
    code, mapper = iterresponsemap(responses)[0]
    assert code == "200"
    assert mapper == "response.text"

def test_iterresponsemap_array_object() -> None:
    responses = models.ResponsesObject(
        patterned={
            "200": models.ResponseObject(
                id="test-response",
                description="test-response",
                status_code=200,
                schema=models.SchemaObject(
                    id="test-response-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.array),
                    format=None,
                    items=models.SchemaObject(
                        id="item-schema",
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
                )
            )
        }
    )
    code, mapper = iterresponsemap(responses)[0]
    assert code == "200"
    assert mapper == "[ItemSchema.model_validate(item) for item in response.json()]"

def test_iterresponsemap_binary() -> None:
    responses = models.ResponsesObject(
        patterned={
            "200": models.ResponseObject(
                id="test-response",
                description="test-response",
                status_code=200,
                schema=models.SchemaObject(
                    id="test-response-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.string),
                    format=models.Format.binary,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                )
            )
        }
    )
    code, mapper = iterresponsemap(responses)[0]
    assert code == "200"
    assert mapper == "response.content"

def test_iterresponsemap_text() -> None:
    responses = models.ResponsesObject(
        patterned={
            "200": models.ResponseObject(
                id="test-response",
                description="test-response",
                status_code=200,
                schema=models.SchemaObject(
                    id="test-response-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.string),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                )
            )
        }
    )
    code, mapper = iterresponsemap(responses)[0]
    assert code == "200"
    assert mapper == "response.text"

def test_iterresponsemap_int() -> None:
    responses = models.ResponsesObject(
        patterned={
            "200": models.ResponseObject(
                id="test-response",
                description="test-response",
                status_code=200,
                schema=models.SchemaObject(
                    id="test-response-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.integer),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                )
            )
        }
    )
    code, mapper = iterresponsemap(responses)[0]
    assert code == "200"
    assert mapper == "int(response.text)"

def test_iterresponsemap_any() -> None:
    responses = models.ResponsesObject(
        patterned={
            "200": models.ResponseObject(
                id="test-response",
                description="test-response",
                status_code=200,
                schema=models.SchemaObject(
                    id="test-response-schema",
                    title=None,
                    enum=None,
                    type=models.SchemaType(models.Type.any),
                    format=None,
                    items=None,
                    properties=[],
                    default=models.UNDEFINED
                )
            )
        }
    )
    code, mapper = iterresponsemap(responses)[0]
    assert code == "200"
    assert mapper == "response.text"

