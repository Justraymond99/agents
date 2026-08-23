from __future__ import annotations

import asyncio
from time import perf_counter
from uuid import uuid4

from app.models.task import Task, TaskStatus
from app.observability import MetricsRecorder, span
from app.orchestration import Orchestrator
from app.persistence import TaskStore


class TaskManager:
    """Owns background ATLAS executions for HTTP/Watch clients."""

    def __init__(
        self,
        orchestrator: Orchestrator,
        store: TaskStore,
        metrics: MetricsRecorder | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.store = store
        self.metrics = metrics or MetricsRecorder()
        self._running: dict[str, asyncio.Task[None]] = {}

    async def submit(self, goal: str) -> Task:
        task = Task(id=str(uuid4()), goal=goal)
        await self.store.save_task(task)
        self.metrics.increment("tasks.submitted")
        background = asyncio.create_task(self._execute(task), name=f"atlas:{task.id}")
        self._running[task.id] = background
        background.add_done_callback(lambda _: self._running.pop(task.id, None))
        return task

    async def _execute(self, task: Task) -> None:
        started = perf_counter()
        try:
            with span("atlas.task", task_id=task.id):
                result = await self.orchestrator.execute(task)
            await self.store.save_task(task)
            await self.store.save_result(result)
            if result.status is TaskStatus.PASSED:
                self.metrics.increment("tasks.passed")
            else:
                self.metrics.increment("tasks.failed")
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            self.metrics.increment("tasks.cancelled")
            await self.store.save_task(task)
            raise
        except Exception:
            task.status = TaskStatus.FAILED
            self.metrics.increment("tasks.errored")
            await self.store.save_task(task)
            raise
        finally:
            self.metrics.observe("tasks.duration_ms", (perf_counter() - started) * 1000)

    async def wait(self, task_id: str) -> None:
        background = self._running.get(task_id)
        if background is not None:
            await background

    async def cancel(self, task_id: str) -> bool:
        background = self._running.get(task_id)
        if background is None:
            return False
        background.cancel()
        try:
            await background
        except asyncio.CancelledError:
            pass
        return True

    async def shutdown(self) -> None:
        tasks = list(self._running.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
