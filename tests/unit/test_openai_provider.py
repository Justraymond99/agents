from types import SimpleNamespace
from typing import cast

import pytest
from openai import AsyncOpenAI

from app.models.message import Message, MessageRole, ModelRequest, ToolSchema
from app.providers.openai import OpenAIProvider


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}

    async def create(self, **kwargs: object) -> SimpleNamespace:
        self.kwargs = kwargs
        return SimpleNamespace(
            output_text="done",
            status="completed",
            error=None,
            usage=SimpleNamespace(input_tokens=10, output_tokens=4, total_tokens=14),
            model="test-model",
            id="resp_test",
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


@pytest.mark.asyncio
async def test_openai_provider_normalizes_messages_tools_and_usage() -> None:
    fake = FakeOpenAIClient()
    provider = OpenAIProvider(client=cast(AsyncOpenAI, fake))
    request = ModelRequest(
        model="test-model",
        messages=[
            Message(role=MessageRole.SYSTEM, content="system rules"),
            Message(role=MessageRole.USER, content="hello"),
        ],
        tools=[
            ToolSchema(
                name="lookup",
                description="Look something up",
                parameters={"type": "object", "properties": {}},
            )
        ],
        max_output_tokens=128,
    )

    result = await provider.generate(request)

    assert fake.responses.kwargs["instructions"] == "system rules"
    assert fake.responses.kwargs["model"] == "test-model"
    assert fake.responses.kwargs["max_output_tokens"] == 128
    assert result.output_text == "done"
    assert result.response_id == "resp_test"
    assert result.usage.total_tokens == 14
