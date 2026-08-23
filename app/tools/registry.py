from __future__ import annotations

from app.tools.base import Permission, Tool, ToolCall, ToolResult


class ToolPermissionError(PermissionError):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

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
        return await tool.invoke(call.arguments)
