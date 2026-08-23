from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from uuid import uuid4

from app.services.task_manager import TaskManager


@dataclass(slots=True)
class ScheduledJob:
    id: str = field(default_factory=lambda: str(uuid4()))
    goal: str = ""
    interval_seconds: float = 3600.0
    enabled: bool = True


class TaskScheduler:
    """Minimal recurring scheduler for periodic ATLAS task submission."""

    def __init__(self, manager: TaskManager) -> None:
        self.manager = manager
        self.jobs: dict[str, ScheduledJob] = {}
        self._workers: dict[str, asyncio.Task[None]] = {}

    def add(self, goal: str, interval_seconds: float) -> ScheduledJob:
        if not goal.strip():
            raise ValueError("scheduled goal cannot be empty")
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        job = ScheduledJob(goal=goal, interval_seconds=interval_seconds)
        self.jobs[job.id] = job
        return job

    def start(self, job_id: str) -> None:
        job = self.jobs[job_id]
        if job_id in self._workers:
            return
        self._workers[job_id] = asyncio.create_task(
            self._run(job),
            name=f"atlas-schedule:{job_id}",
        )

    async def _run(self, job: ScheduledJob) -> None:
        try:
            while job.enabled:
                await self.manager.submit(job.goal)
                await asyncio.sleep(job.interval_seconds)
        finally:
            self._workers.pop(job.id, None)

    async def stop(self, job_id: str) -> bool:
        worker = self._workers.get(job_id)
        if worker is None:
            return False
        self.jobs[job_id].enabled = False
        worker.cancel()
        await asyncio.gather(worker, return_exceptions=True)
        return True

    async def shutdown(self) -> None:
        for job_id in list(self._workers):
            await self.stop(job_id)
