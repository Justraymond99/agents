from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStep(BaseModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    assigned_agent: str = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING

    @model_validator(mode="after")
    def validate_dependencies(self) -> "TaskStep":
        if self.id in self.dependencies:
            raise ValueError("a task step cannot depend on itself")
        if len(self.dependencies) != len(set(self.dependencies)):
            raise ValueError("task step dependencies must be unique")
        return self


class TaskPlan(BaseModel):
    goal: str = Field(min_length=1)
    steps: list[TaskStep] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_plan(self) -> "TaskPlan":
        step_ids = [step.id for step in self.steps]

        if len(step_ids) != len(set(step_ids)):
            raise ValueError("task step ids must be unique")

        known_ids = set(step_ids)
        for step in self.steps:
            unknown = set(step.dependencies) - known_ids
            if unknown:
                raise ValueError(
                    f"task step '{step.id}' has unknown dependencies: {sorted(unknown)}"
                )

        self._validate_acyclic()
        return self

    def _validate_acyclic(self) -> None:
        dependencies = {step.id: set(step.dependencies) for step in self.steps}
        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(step_id: str) -> None:
            if step_id in permanent:
                return
            if step_id in temporary:
                raise ValueError("task plan dependencies must be acyclic")

            temporary.add(step_id)
            for dependency in dependencies[step_id]:
                visit(dependency)
            temporary.remove(step_id)
            permanent.add(step_id)

        for step_id in dependencies:
            visit(step_id)


class Task(BaseModel):
    id: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    status: TaskStatus = TaskStatus.PENDING
    plan: TaskPlan | None = None
