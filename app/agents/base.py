from __future__ import annotations

import json
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.models.message import Message, MessageRole, ModelRequest, ToolSchema
from app.providers.base import ModelClient

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
        max_output_tokens: int | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self.model = model
        self.client = client
        self.response_model = response_model
        self.system_prompt = system_prompt
        self.tools = list(tools or [])
        self.max_output_tokens = max_output_tokens

    async def run(self, prompt: str, context: AgentContext | None = None) -> TOutput:
        request = self.build_request(prompt, context)
        response = await self.client.generate(request)
        return self.parse_response(response.output_text)

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
