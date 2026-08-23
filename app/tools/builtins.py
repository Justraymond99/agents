from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.tools.base import Permission, Tool, ToolSpec


def _resolve(root: Path, raw: str) -> Path:
    target = (root / raw).resolve()
    if root.resolve() not in target.parents and target != root.resolve():
        raise ValueError("path escapes configured workspace")
    return target


def build_builtin_tools(workspace: Path) -> list[Tool]:
    root = workspace.resolve()

    async def read_file(args: dict[str, Any]) -> str:
        path = _resolve(root, str(args["path"]))
        return path.read_text(encoding="utf-8")

    async def write_file(args: dict[str, Any]) -> str:
        path = _resolve(root, str(args["path"]))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(args.get("content", "")), encoding="utf-8")
        return str(path.relative_to(root))

    async def list_files(args: dict[str, Any]) -> list[str]:
        path = _resolve(root, str(args.get("path", ".")))
        return sorted(str(p.relative_to(root)) for p in path.iterdir())

    async def run_command(args: dict[str, Any]) -> dict[str, Any]:
        command = args.get("command")
        if not isinstance(command, list) or not command or not all(
            isinstance(part, str) for part in command
        ):
            raise ValueError("command must be a non-empty list of strings")
        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def run_tests(args: dict[str, Any]) -> dict[str, Any]:
        test_args = args.get("args", ["-q"])
        if not isinstance(test_args, list) or not all(isinstance(x, str) for x in test_args):
            raise ValueError("args must be a list of strings")
        return await run_command({"command": ["pytest", *test_args]})

    async def git_diff(args: dict[str, Any]) -> dict[str, Any]:
        return await run_command({"command": ["git", "diff", "--", "."]})

    path_schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
        "additionalProperties": False,
    }
    write_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
        "additionalProperties": False,
    }
    command_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "array", "items": {"type": "string"}, "minItems": 1}
        },
        "required": ["command"],
        "additionalProperties": False,
    }
    test_schema = {
        "type": "object",
        "properties": {"args": {"type": "array", "items": {"type": "string"}}},
        "additionalProperties": False,
    }

    return [
        Tool(
            ToolSpec(
                name="read_file",
                description="Read a UTF-8 workspace file",
                permission=Permission.READ,
                parameters=path_schema,
            ),
            read_file,
        ),
        Tool(
            ToolSpec(
                name="write_file",
                description="Write a UTF-8 workspace file",
                permission=Permission.WRITE,
                parameters=write_schema,
                side_effects=True,
            ),
            write_file,
        ),
        Tool(
            ToolSpec(
                name="list_files",
                description="List a workspace directory",
                permission=Permission.READ,
                parameters={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "additionalProperties": False,
                },
            ),
            list_files,
        ),
        Tool(
            ToolSpec(
                name="run_command",
                description="Run a command without a shell",
                permission=Permission.EXECUTE,
                parameters=command_schema,
                timeout_seconds=120,
            ),
            run_command,
        ),
        Tool(
            ToolSpec(
                name="run_tests",
                description="Run pytest",
                permission=Permission.EXECUTE,
                parameters=test_schema,
                timeout_seconds=180,
            ),
            run_tests,
        ),
        Tool(
            ToolSpec(
                name="git_diff",
                description="Return the current git diff",
                permission=Permission.READ,
            ),
            git_diff,
        ),
    ]
