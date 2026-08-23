import pytest
from pydantic import ValidationError

from app.models.message import Message, MessageRole, ModelRequest, ModelResponse, ToolSchema


def test_model_request_accepts_messages_and_tools() -> None:
    request = ModelRequest(
        model="test-model",
        messages=[Message(role=MessageRole.USER, content="hello")],
        tools=[
            ToolSchema(
                name="search",
                description="Search for context",
                parameters={"type": "object", "properties": {}},
            )
        ],
        max_output_tokens=256,
    )

    assert request.model == "test-model"
    assert request.messages[0].role is MessageRole.USER
    assert request.tools[0].name == "search"


def test_model_request_requires_at_least_one_message() -> None:
    with pytest.raises(ValidationError):
        ModelRequest(model="test-model", messages=[])


def test_model_response_usage_defaults_to_zero() -> None:
    response = ModelResponse(provider="fake", model="fake-model", output_text="done")

    assert response.usage.input_tokens == 0
    assert response.usage.output_tokens == 0
    assert response.usage.total_tokens == 0
