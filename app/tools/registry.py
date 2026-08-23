from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.tools.base import Permission, Tool, ToolCall, ToolResult


class ToolPermissionError(PermissionError):
    pass


class ToolAuditRecord(BaseModel):
    tool: str
    permission: Permission
    arguments: dict[str, object] = Field(default_factory=dict)
    success: bool
    error: str | None = None
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._audit: list[ToolAuditRecord] = []

    def register(self, tool: Tool) -> None:
        key = tool.spec.name.lower()
        if key in self._tools:
            raise ValueError(f"tool '{tool.spec.name}' is already registered")
        self._tools[key] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name.lower()]
        except KeyError as exc:
            raise KeyError(f"tool '{name}' is not registered") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def audit_records(self) -> tuple[ToolAuditRecord, ...]:
        return tuple(record.model_copy(deep=True) for record in self._audit)

    async def invoke(
        self,
        call: ToolCall,
        *,
        allowed_permissions: set[Permission],
    ) -> ToolResult:
        tool = self.get(call.tool)
        if tool.spec.permission not in allowed_permissions:
            raise ToolPermissionError(
                f"permission '{tool.spec.permission}' is not allowed for tool '{tool.spec.name}'"
            )
        result = await tool.invoke(call.arguments)
        self._audit.append(
            ToolAuditRecord(
                tool=tool.spec.name,
                permission=tool.spec.permission,
                arguments=dict(call.arguments),
                success=result.success,
                error=result.error,
                duration_ms=result.duration_ms,
            )
        )
        return result
