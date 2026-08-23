from __future__ import annotations

from typing import Protocol

from sqlalchemy import JSON, String, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.task import Task
from app.orchestration.state import OrchestrationResult


class TaskStore(Protocol):
    async def save_task(self, task: Task) -> None: ...
    async def get_task(self, task_id: str) -> Task | None: ...
    async def save_result(self, result: OrchestrationResult) -> None: ...
    async def get_result(self, task_id: str) -> OrchestrationResult | None: ...


class InMemoryTaskStore:
    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}
        self.results: dict[str, OrchestrationResult] = {}

    async def save_task(self, task: Task) -> None:
        self.tasks[task.id] = task.model_copy(deep=True)

    async def get_task(self, task_id: str) -> Task | None:
        task = self.tasks.get(task_id)
        return task.model_copy(deep=True) if task else None

    async def save_result(self, result: OrchestrationResult) -> None:
        self.results[result.task_id] = result.model_copy(deep=True)

    async def get_result(self, task_id: str) -> OrchestrationResult | None:
        result = self.results.get(task_id)
        return result.model_copy(deep=True) if result else None


class Base(DeclarativeBase):
    pass


class TaskRow(Base):
    __tablename__ = "atlas_tasks"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    result_payload: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)


class SqlTaskStore:
    def __init__(self, database_url: str) -> None:
        self.engine = create_async_engine(database_url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await self.engine.dispose()

    async def save_task(self, task: Task) -> None:
        async with self.sessions() as session:
            row = await session.get(TaskRow, task.id)
            if row is None:
                row = TaskRow(id=task.id, payload=task.model_dump(mode="json"))
                session.add(row)
            else:
                row.payload = task.model_dump(mode="json")
            await session.commit()

    async def get_task(self, task_id: str) -> Task | None:
        async with self.sessions() as session:
            row = await session.get(TaskRow, task_id)
            return Task.model_validate(row.payload) if row else None

    async def save_result(self, result: OrchestrationResult) -> None:
        async with self.sessions() as session:
            row = await session.get(TaskRow, result.task_id)
            if row is None:
                raise KeyError(f"task '{result.task_id}' is not persisted")
            row.result_payload = result.model_dump(mode="json")
            await session.commit()

    async def get_result(self, task_id: str) -> OrchestrationResult | None:
        async with self.sessions() as session:
            stmt = select(TaskRow).where(TaskRow.id == task_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None or row.result_payload is None:
                return None
            return OrchestrationResult.model_validate(row.result_payload)
