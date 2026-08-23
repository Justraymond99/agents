from __future__ import annotations

import json
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.models.message import Message, MessageRole, ModelRequest, ToolSchema
from app.providers.base import ModelClient
from app.tools import Permission, ToolCall, ToolRegistry

TOutput = TypeVar("TOutput", bound=BaseModel)


class AgentContext(BaseModel):
    """Structured context supplied to an agent for one execution."""

    task_id: str | None = None
    run_id: str | None = None
    values: dict[str, object] = Field(default_factory=dict)


class BaseAgent(Generic[TOutput]):
    """Provider-agnostic base class for ATLAS agents."""

    def __init__(
        self,
        *,
        name: str,
        role: str,
        model: str,
        client: ModelClient,
        response_model: type[TOutput],
        system_prompt: str,
        tools: list[ToolSchema] | None = None,
        tool_registry: ToolRegistry | None = None,
        allowed_permissions: set[Permission] | None = None,
        max_tool_rounds: int = 8,
        max_output_tokens: int | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self.model = model
        self.client = client
        self.response_model = response_model
        self.system_prompt = system_prompt
        self.tool_registry = tool_registry
        self.allowed_permissions = set(allowed_permissions or set())
        self.max_tool_rounds = max_tool_rounds
        self.max_output_tokens = max_output_tokens

        if tools is not None:
            self.tools = list(tools)
        elif tool_registry is not None:
            self.tools = [
                ToolSchema(
                    name=tool.spec.name,
                    description=tool.spec.description,
                    parameters=tool.spec.parameters,
                )
                for name in tool_registry.names()
                for tool in [tool_registry.get(name)]
                if tool.spec.permission in self.allowed_permissions
            ]
        else:
            self.tools = []

    async def run(self, prompt: str, context: AgentContext | None = None) -> TOutput:
        request = self.build_request(prompt, context)

        for _ in range(self.max_tool_rounds + 1):
            response = await self.client.generate(request)
            if not response.tool_calls:
                return self.parse_response(response.output_text)

            if self.tool_registry is None:
                raise RuntimeError(f"agent '{self.name}' requested tools without a tool registry")

            tool_results: list[dict[str, object]] = []
            for model_call in response.tool_calls:
                result = await self.tool_registry.invoke(
                    ToolCall(tool=model_call.name, arguments=dict(model_call.arguments)),
                    allowed_permissions=self.allowed_permissions,
                )
                tool_results.append(
                    {
                        "call_id": model_call.call_id,
                        "tool": model_call.name,
                        "arguments": model_call.arguments,
                        "result": result.model_dump(mode="json"),
                    }
                )

            messages = list(request.messages)
            messages.append(
                Message(
                    role=MessageRole.DEVELOPER,
                    content=(
                        "Tool calls from the previous model turn were executed. Use these exact "
                        "results as evidence and continue the task. Do not claim any unexecuted action.\n"
                        + json.dumps(tool_results, sort_keys=True)
                    ),
                )
            )
            request = request.model_copy(update={"messages": messages})

        raise RuntimeError(f"agent '{self.name}' exceeded max_tool_rounds={self.max_tool_rounds}")

    def build_request(self, prompt: str, context: AgentContext | None = None) -> ModelRequest:
        if not prompt.strip():
            raise ValueError("agent prompt cannot be empty")

        messages = [Message(role=MessageRole.SYSTEM, content=self.system_prompt)]

        if context is not None and (context.task_id or context.run_id or context.values):
            context_payload = json.dumps(context.model_dump(mode="json"), sort_keys=True)
            messages.append(
                Message(
                    role=MessageRole.DEVELOPER,
                    content=f"Execution context:\n{context_payload}",
                )
            )

        messages.append(Message(role=MessageRole.USER, content=prompt))

        return ModelRequest(
            model=self.model,
            messages=messages,
            tools=self.tools,
            max_output_tokens=self.max_output_tokens,
        )

    def parse_response(self, output_text: str) -> TOutput:
        try:
            return self.response_model.model_validate_json(output_text)
        except ValueError as exc:
            raise ValueError(
                f"agent '{self.name}' returned invalid {self.response_model.__name__} JSON"
            ) from exc
