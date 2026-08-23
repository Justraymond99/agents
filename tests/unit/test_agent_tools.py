import json

import pytest

from app.agents.base import BaseAgent
from app.models.message import ModelRequest, ModelResponse, ModelToolCall
from app.models.result import AgentResult
from app.providers.base import ModelClient
from app.tools import Permission, Tool, ToolRegistry, ToolSpec


class QueueClient(ModelClient):
    name = "fake"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        if self.calls == 1:
            return ModelResponse(
                provider="fake",
                model=request.model,
                output_text="",
                tool_calls=[ModelToolCall(call_id="1", name="lookup", arguments={"key": "x"})],
            )
        return ModelResponse(
            provider="fake",
            model=request.model,
            output_text=json.dumps({"agent": "demo", "success": True, "output": "used tool"}),
        )


@pytest.mark.asyncio
async def test_base_agent_executes_tool_then_continues() -> None:
    async def lookup(args: dict[str, object]) -> str:
        return f"value:{args['key']}"

    registry = ToolRegistry()
    registry.register(
        Tool(
            ToolSpec(
                name="lookup",
                description="lookup a value",
                permission=Permission.READ,
                parameters={
                    "type": "object",
                    "properties": {"key": {"type": "string"}},
                    "required": ["key"],
                    "additionalProperties": False,
                },
            ),
            lookup,
        )
    )
    client = QueueClient()
    agent = BaseAgent(
        name="demo",
        role="demo",
        model="test",
        client=client,
        response_model=AgentResult,
        system_prompt="demo",
        tool_registry=registry,
        allowed_permissions={Permission.READ},
    )

    result = await agent.run("go")

    assert result.success is True
    assert client.calls == 2
