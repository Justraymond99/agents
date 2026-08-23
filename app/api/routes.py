from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.memory import MemoryRecord
from app.models.task import Task
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

    @router.post("/tasks")
    async def submit_task(request: SubmitTaskRequest) -> dict[str, object]:
        task = Task(id=str(uuid4()), goal=request.goal)
        await runtime.task_store.save_task(task)
        result = await runtime.orchestrator.execute(task)
        await runtime.task_store.save_task(task)
        await runtime.task_store.save_result(result)
        return result.model_dump(mode="json")

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
