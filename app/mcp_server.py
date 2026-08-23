from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.memory import MemoryRecord
from app.runtime import build_runtime

mcp = FastMCP("ATLAS")
runtime = build_runtime()
_initialized = False


async def _ensure_runtime() -> None:
    global _initialized
    if not _initialized:
        await runtime.initialize()
        _initialized = True


@mcp.tool()
async def submit_task(goal: str, wait: bool = True) -> dict[str, object]:
    """Submit a natural-language task. Set wait=false for background execution."""
    await _ensure_runtime()
    task = await runtime.manager.submit(goal)
    if not wait:
        return task.model_dump(mode="json")
    await runtime.manager.wait(task.id)
    result = await runtime.task_store.get_result(task.id)
    if result is None:
        return task.model_dump(mode="json")
    return result.model_dump(mode="json")


@mcp.tool()
async def get_task_status(task_id: str) -> dict[str, object]:
    """Return persisted task state."""
    await _ensure_runtime()
    task = await runtime.task_store.get_task(task_id)
    if task is None:
        return {"found": False, "task_id": task_id}
    return {"found": True, **task.model_dump(mode="json")}


@mcp.tool()
async def get_task_result(task_id: str) -> dict[str, object]:
    """Return a completed ATLAS result and trace."""
    await _ensure_runtime()
    result = await runtime.task_store.get_result(task_id)
    if result is None:
        return {"found": False, "task_id": task_id}
    return {"found": True, **result.model_dump(mode="json")}


@mcp.tool()
async def cancel_task(task_id: str) -> dict[str, object]:
    """Cancel a currently running ATLAS task."""
    await _ensure_runtime()
    return {"task_id": task_id, "cancelled": await runtime.manager.cancel(task_id)}


@mcp.tool()
async def query_memory(namespace: str, query: str, limit: int = 10) -> list[dict[str, object]]:
    """Search a namespaced ATLAS memory store."""
    records = await runtime.memory.query(namespace, query, limit)
    return [record.model_dump(mode="json") for record in records]


@mcp.tool()
async def write_memory(namespace: str, key: str, value: str) -> dict[str, object]:
    """Write one namespaced memory record."""
    record = MemoryRecord(namespace=namespace, key=key, value=value)
    await runtime.memory.put(record)
    return record.model_dump(mode="json")


if __name__ == "__main__":
    mcp.run()
