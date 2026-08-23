from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.result import AgentResult, ReviewResult
from app.models.task import TaskPlan, TaskStatus
from app.models.trace import RunTrace


class ExecutionState(BaseModel):
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    status: TaskStatus = TaskStatus.PENDING
    plan: TaskPlan | None = None
    results: dict[str, AgentResult] = Field(default_factory=dict)
    review: ReviewResult | None = None
    trace: RunTrace


class OrchestrationResult(BaseModel):
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    status: TaskStatus
    results: dict[str, AgentResult] = Field(default_factory=dict)
    review: ReviewResult | None = None
    trace: RunTrace
