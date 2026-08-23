from pathlib import Path

import pytest

from app.tools import Permission, ToolCall, ToolPermissionError, ToolRegistry, build_builtin_tools


@pytest.mark.asyncio
async def test_tool_registry_enforces_permissions(tmp_path: Path) -> None:
    registry = ToolRegistry()
    for tool in build_builtin_tools(tmp_path):
        registry.register(tool)

    with pytest.raises(ToolPermissionError):
        await registry.invoke(
            ToolCall(tool="write_file", arguments={"path": "a.txt", "content": "x"}),
            allowed_permissions={Permission.READ},
        )


@pytest.mark.asyncio
async def test_builtin_read_write_stays_inside_workspace(tmp_path: Path) -> None:
    registry = ToolRegistry()
    for tool in build_builtin_tools(tmp_path):
        registry.register(tool)

    result = await registry.invoke(
        ToolCall(tool="write_file", arguments={"path": "notes/a.txt", "content": "hello"}),
        allowed_permissions={Permission.WRITE},
    )
    assert result.success is True
    assert (tmp_path / "notes" / "a.txt").read_text() == "hello"

    escaped = await registry.invoke(
        ToolCall(tool="read_file", arguments={"path": "../outside.txt"}),
        allowed_permissions={Permission.READ},
    )
    assert escaped.success is False
