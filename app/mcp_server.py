from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.memory import MemoryRecord
from app.models.task import Task
from app.runtime import build_runtime

mcp = FastMCP("ATLAS")
runtime = build_runtime()


@mcp.tool()
async def submit_task(goal: str) -> dict[str, object]:
    """Submit a natural-language task to the ATLAS orchestrator."""
    from uuid import uuid4

    task = Task(id=str(uuid4()), goal=goal)
    await runtime.task_store.save_task(task)
    result = await runtime.orchestrator.execute(task)
    await runtime.task_store.save_task(task)
    await runtime.task_store.save_result(result)
    return result.model_dump(mode="json")


@mcp.tool()
async def get_task_status(task_id: str) -> dict[str, object]:
    """Return persisted task state."""
    task = await runtime.task_store.get_task(task_id)
    if task is None:
        return {"found": False, "task_id": task_id}
    return {"found": True, **task.model_dump(mode="json")}


@mcp.tool()
async def get_task_result(task_id: str) -> dict[str, object]:
    """Return a completed ATLAS result and trace."""
    result = await runtime.task_store.get_result(task_id)
    if result is None:
        return {"found": False, "task_id": task_id}
    return {"found": True, **result.model_dump(mode="json")}


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
