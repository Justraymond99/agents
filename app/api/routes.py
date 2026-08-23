from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.memory import MemoryRecord
from app.runtime import AtlasRuntime


class SubmitTaskRequest(BaseModel):
    goal: str = Field(min_length=1)


class MemoryWriteRequest(BaseModel):
    namespace: str = Field(min_length=1)
    key: str = Field(min_length=1)
    value: str


class MemoryQueryRequest(BaseModel):
    namespace: str = Field(min_length=1)
    text: str = ""
    limit: int = Field(default=10, ge=1, le=100)


def build_router(runtime: AtlasRuntime) -> APIRouter:
    router = APIRouter()

    @router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
    async def submit_task(request: SubmitTaskRequest) -> dict[str, object]:
        task = await runtime.manager.submit(request.goal)
        return task.model_dump(mode="json")

    @router.get("/tasks/{task_id}")
    async def get_task(task_id: str) -> dict[str, object]:
        task = await runtime.task_store.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="task not found")
        return task.model_dump(mode="json")

    @router.get("/tasks/{task_id}/result")
    async def get_result(task_id: str) -> dict[str, object]:
        result = await runtime.task_store.get_result(task_id)
        if result is None:
            raise HTTPException(status_code=404, detail="result not found")
        return result.model_dump(mode="json")

    @router.get("/tasks/{task_id}/trace")
    async def get_trace(task_id: str) -> dict[str, object]:
        result = await runtime.task_store.get_result(task_id)
        if result is None:
            raise HTTPException(status_code=404, detail="result not found")
        return result.trace.model_dump(mode="json")

    @router.post("/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str) -> dict[str, object]:
        task = await runtime.task_store.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="task not found")
        cancelled = await runtime.manager.cancel(task_id)
        return {"task_id": task_id, "cancelled": cancelled}

    @router.get("/tools")
    async def list_tools() -> dict[str, object]:
        return {"tools": list(runtime.tools.names())}

    @router.post("/memory/write")
    async def write_memory(request: MemoryWriteRequest) -> dict[str, object]:
        record = MemoryRecord(
            namespace=request.namespace,
            key=request.key,
            value=request.value,
        )
        await runtime.memory.put(record)
        return record.model_dump(mode="json")

    @router.post("/memory/query")
    async def query_memory(request: MemoryQueryRequest) -> list[dict[str, object]]:
        records = await runtime.memory.query(request.namespace, request.text, request.limit)
        return [record.model_dump(mode="json") for record in records]

    return router
