from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, String, Text, and_, or_, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.memory.store import MemoryRecord


class MemoryBase(DeclarativeBase):
    pass


class MemoryRow(MemoryBase):
    __tablename__ = "atlas_memory"

    namespace: Mapped[str] = mapped_column(String(255), primary_key=True)
    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)


class SqlMemoryStore:
    def __init__(self, database_url: str) -> None:
        self.engine = create_async_engine(database_url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(MemoryBase.metadata.create_all)

    async def close(self) -> None:
        await self.engine.dispose()

    async def put(self, record: MemoryRecord) -> None:
        async with self.sessions() as session:
            row = await session.get(MemoryRow, (record.namespace, record.key))
            now = datetime.now(timezone.utc)
            if row is None:
                session.add(
                    MemoryRow(
                        namespace=record.namespace,
                        key=record.key,
                        value=record.value,
                        metadata_json=record.metadata,
                        updated_at=now,
                    )
                )
            else:
                row.value = record.value
                row.metadata_json = record.metadata
                row.updated_at = now
            await session.commit()

    async def get(self, namespace: str, key: str) -> MemoryRecord | None:
        async with self.sessions() as session:
            row = await session.get(MemoryRow, (namespace, key))
            if row is None:
                return None
            return self._record(row)

    async def query(self, namespace: str, text: str, limit: int = 10) -> list[MemoryRecord]:
        async with self.sessions() as session:
            stmt = select(MemoryRow).where(MemoryRow.namespace == namespace)
            if text:
                pattern = f"%{text}%"
                stmt = stmt.where(or_(MemoryRow.key.ilike(pattern), MemoryRow.value.ilike(pattern)))
            stmt = stmt.order_by(MemoryRow.updated_at.desc()).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()
            return [self._record(row) for row in rows]

    @staticmethod
    def _record(row: MemoryRow) -> MemoryRecord:
        return MemoryRecord(
            namespace=row.namespace,
            key=row.key,
            value=row.value,
            metadata=row.metadata_json,
            updated_at=row.updated_at,
        )
