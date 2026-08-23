from __future__ import annotations

import json

from openai import APIError, AsyncOpenAI

from app.models.message import (
    MessageRole,
    ModelRequest,
    ModelResponse,
    ModelToolCall,
    ModelUsage,
)
from app.providers.errors import ProviderError, ProviderResponseError


class OpenAIProvider:
    name = "openai"

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self._client = client or AsyncOpenAI()

    async def generate(self, request: ModelRequest) -> ModelResponse:
        instructions: list[str] = []
        input_messages: list[dict[str, str]] = []

        for message in request.messages:
            if message.role in {MessageRole.SYSTEM, MessageRole.DEVELOPER}:
                instructions.append(message.content)
            else:
                input_messages.append(
                    {
                        "role": message.role.value,
                        "content": message.content,
                    }
                )

        kwargs: dict[str, object] = {
            "model": request.model,
            "input": input_messages,
        }
        if instructions:
            kwargs["instructions"] = "\n\n".join(instructions)
        if request.max_output_tokens is not None:
            kwargs["max_output_tokens"] = request.max_output_tokens
        if request.tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "strict": True,
                }
                for tool in request.tools
            ]

        try:
            response = await self._client.responses.create(**kwargs)  # type: ignore[call-overload]
        except APIError as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc

        output_text = response.output_text or ""

        if response.status == "failed":
            error_message = (
                response.error.message if response.error is not None else "unknown provider error"
            )
            raise ProviderResponseError(error_message)

        tool_calls: list[ModelToolCall] = []
        for item in getattr(response, "output", []):
            if getattr(item, "type", None) != "function_call":
                continue
            raw_arguments = getattr(item, "arguments", "{}") or "{}"
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError as exc:
                raise ProviderResponseError("model returned invalid tool-call JSON") from exc
            if not isinstance(arguments, dict):
                raise ProviderResponseError("model tool-call arguments must be an object")
            tool_calls.append(
                ModelToolCall(
                    call_id=str(getattr(item, "call_id", "call")),
                    name=str(getattr(item, "name", "")),
                    arguments=arguments,
                )
            )

        usage = ModelUsage()
        if response.usage is not None:
            usage = ModelUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.total_tokens,
            )

        return ModelResponse(
            provider=self.name,
            model=str(response.model),
            output_text=output_text,
            response_id=response.id,
            usage=usage,
            tool_calls=tool_calls,
            raw_metadata={"status": response.status},
        )
