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


class CreateApprovalRequest(BaseModel):
    action: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)


class ResolveApprovalRequest(BaseModel):
    approved: bool


class CreateArtifactRequest(BaseModel):
    name: str = Field(min_length=1)
    content: str
    media_type: str = "text/plain"


class CreateScheduleRequest(BaseModel):
    goal: str = Field(min_length=1)
    interval_seconds: float = Field(gt=0)
    start: bool = True


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

    @router.get("/tools/audit")
    async def tool_audit() -> list[dict[str, object]]:
        return [record.model_dump(mode="json") for record in runtime.tools.audit_records()]

    @router.get("/metrics")
    async def metrics() -> dict[str, object]:
        return runtime.metrics.snapshot()

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

    @router.post("/approvals")
    async def create_approval(request: CreateApprovalRequest) -> dict[str, object]:
        approval = runtime.approvals.create(request.action, request.reason, request.payload)
        return approval.model_dump(mode="json")

    @router.get("/approvals/{approval_id}")
    async def get_approval(approval_id: str) -> dict[str, object]:
        approval = runtime.approvals.get(approval_id)
        if approval is None:
            raise HTTPException(status_code=404, detail="approval not found")
        return approval.model_dump(mode="json")

    @router.post("/approvals/{approval_id}/resolve")
    async def resolve_approval(
        approval_id: str,
        request: ResolveApprovalRequest,
    ) -> dict[str, object]:
        try:
            approval = runtime.approvals.resolve(approval_id, request.approved)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="approval not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return approval.model_dump(mode="json")

    @router.post("/artifacts")
    async def create_artifact(request: CreateArtifactRequest) -> dict[str, object]:
        artifact = runtime.artifacts.put_bytes(
            request.name,
            request.content.encode("utf-8"),
            media_type=request.media_type,
        )
        return artifact.model_dump(mode="json")

    @router.get("/artifacts/{artifact_id}")
    async def get_artifact(artifact_id: str) -> dict[str, object]:
        artifact = runtime.artifacts.get(artifact_id)
        if artifact is None:
            raise HTTPException(status_code=404, detail="artifact not found")
        return artifact.model_dump(mode="json")

    @router.post("/schedules")
    async def create_schedule(request: CreateScheduleRequest) -> dict[str, object]:
        job = runtime.scheduler.add(request.goal, request.interval_seconds)
        if request.start:
            runtime.scheduler.start(job.id)
        return {
            "id": job.id,
            "goal": job.goal,
            "interval_seconds": job.interval_seconds,
            "enabled": job.enabled,
        }

    @router.get("/schedules")
    async def list_schedules() -> list[dict[str, object]]:
        return [
            {
                "id": job.id,
                "goal": job.goal,
                "interval_seconds": job.interval_seconds,
                "enabled": job.enabled,
            }
            for job in runtime.scheduler.jobs.values()
        ]

    @router.post("/schedules/{job_id}/stop")
    async def stop_schedule(job_id: str) -> dict[str, object]:
        if job_id not in runtime.scheduler.jobs:
            raise HTTPException(status_code=404, detail="schedule not found")
        stopped = await runtime.scheduler.stop(job_id)
        return {"id": job_id, "stopped": stopped}

    return router
