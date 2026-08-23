from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: MessageRole
    content: str = Field(min_length=1)


class ToolSchema(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: dict[str, object] = Field(default_factory=dict)


class ModelRequest(BaseModel):
    model: str = Field(min_length=1)
    messages: list[Message] = Field(min_length=1)
    tools: list[ToolSchema] = Field(default_factory=list)
    max_output_tokens: int | None = Field(default=None, gt=0)


class ModelUsage(BaseModel):
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class ModelResponse(BaseModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    output_text: str
    response_id: str | None = None
    usage: ModelUsage = Field(default_factory=ModelUsage)
    raw_metadata: dict[str, object] = Field(default_factory=dict)
