import asyncio

import pytest

from app.models.task import TaskPlan, TaskStep
from app.orchestration.scheduler import DagScheduler


@pytest.mark.asyncio
async def test_dependent_step_waits_for_dependency_to_finish() -> None:
    dependency_finished = asyncio.Event()
    dependent_started_too_early = False

    plan = TaskPlan(
        goal="preserve dependency ordering",
        steps=[
            TaskStep(id="prepare", description="prepare", assigned_agent="builder"),
            TaskStep(
                id="consume",
                description="consume prepared result",
                assigned_agent="tester",
                dependencies=["prepare"],
            ),
        ],
    )

    async def runner(step: TaskStep) -> None:
        nonlocal dependent_started_too_early
        if step.id == "prepare":
            await asyncio.sleep(0.05)
            dependency_finished.set()
            return

        if not dependency_finished.is_set():
            dependent_started_too_early = True

    await DagScheduler(max_parallel_tasks=2).run(plan, runner)

    assert not dependent_started_too_early
