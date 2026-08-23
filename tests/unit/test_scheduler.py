import asyncio

import pytest

from app.models.task import TaskPlan, TaskStep
from app.orchestration.scheduler import DagScheduler


@pytest.mark.asyncio
async def test_scheduler_respects_dependencies() -> None:
    plan = TaskPlan(
        goal="demo",
        steps=[
            TaskStep(id="a", description="a", assigned_agent="researcher"),
            TaskStep(id="b", description="b", assigned_agent="builder"),
            TaskStep(id="c", description="c", assigned_agent="tester", dependencies=["a", "b"]),
        ],
    )
    seen: list[str] = []

    async def runner(step: TaskStep) -> None:
        await asyncio.sleep(0)
        if step.id == "c":
            assert set(seen) == {"a", "b"}
        seen.append(step.id)

    await DagScheduler(max_parallel_tasks=2).run(plan, runner)

    assert seen[-1] == "c"
