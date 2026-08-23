from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field


class Permission(StrEnum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    EXTERNAL_SIDE_EFFECT = "external_side_effect"
    ADMIN = "admin"


class ToolSpec(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    permission: Permission
    parameters: dict[str, object] = Field(
        default_factory=lambda: {"type": "object", "properties": {}, "additionalProperties": False}
    )
    timeout_seconds: float = Field(default=30.0, gt=0)
    side_effects: bool = False


class ToolCall(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool: str
    success: bool
    output: Any = None
    error: str | None = None
    duration_ms: float = 0.0


ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]


class Tool:
    def __init__(self, spec: ToolSpec, handler: ToolHandler) -> None:
        self.spec = spec
        self.handler = handler

    async def invoke(self, arguments: dict[str, Any]) -> ToolResult:
        start = asyncio.get_running_loop().time()
        try:
            output = await asyncio.wait_for(
                self.handler(arguments), timeout=self.spec.timeout_seconds
            )
            return ToolResult(
                tool=self.spec.name,
                success=True,
                output=output,
                duration_ms=(asyncio.get_running_loop().time() - start) * 1000,
            )
        except Exception as exc:
            return ToolResult(
                tool=self.spec.name,
                success=False,
                error=str(exc),
                duration_ms=(asyncio.get_running_loop().time() - start) * 1000,
            )
