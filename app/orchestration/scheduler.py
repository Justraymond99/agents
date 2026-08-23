from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.models.task import TaskPlan, TaskStep

StepRunner = Callable[[TaskStep], Awaitable[None]]


class DagScheduler:
    """Execute dependency-ready task steps with bounded concurrency."""

    def __init__(self, max_parallel_tasks: int = 4) -> None:
        if max_parallel_tasks < 1:
            raise ValueError("max_parallel_tasks must be >= 1")
        self.max_parallel_tasks = max_parallel_tasks

    async def run(self, plan: TaskPlan, runner: StepRunner) -> None:
        pending = {step.id: step for step in plan.steps}
        completed: set[str] = set()

        while pending:
            ready = [
                step
                for step in pending.values()
                if set(step.dependencies).issubset(completed)
            ]
            if not ready:
                raise RuntimeError("no dependency-ready steps remain")

            batch = ready[: self.max_parallel_tasks]
            await asyncio.gather(*(runner(step) for step in batch))
            for step in batch:
                completed.add(step.id)
                pending.pop(step.id)
