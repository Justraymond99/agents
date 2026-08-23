from __future__ import annotations

from openai import AsyncOpenAI

from app.models.message import MessageRole, ModelRequest, ModelResponse, ModelUsage
from app.providers.errors import ProviderResponseError


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

        response = await self._client.responses.create(**kwargs)  # type: ignore[arg-type]
        output_text = response.output_text or ""

        if response.status == "failed":
            message = response.error.message if response.error is not None else "unknown provider error"
            raise ProviderResponseError(message)

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
            raw_metadata={"status": response.status},
        )
