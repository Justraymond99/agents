from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class TraceEventType(StrEnum):
    TASK_STARTED = "task_started"
    PLAN_CREATED = "plan_created"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    TOOL_CALLED = "tool_called"
    TEST_COMPLETED = "test_completed"
    REVIEW_COMPLETED = "review_completed"
    REVISION_REQUESTED = "revision_requested"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"


class TraceEvent(BaseModel):
    event_type: TraceEventType
    message: str = Field(min_length=1)
    agent: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RunTrace(BaseModel):
    run_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    events: list[TraceEvent] = Field(default_factory=list)

    def add(self, event: TraceEvent) -> None:
        self.events.append(event)
