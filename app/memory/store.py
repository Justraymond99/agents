from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from pydantic import BaseModel, Field


class MemoryRecord(BaseModel):
    namespace: str = Field(min_length=1)
    key: str = Field(min_length=1)
    value: str
    metadata: dict[str, object] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryStore(Protocol):
    async def put(self, record: MemoryRecord) -> None: ...
    async def get(self, namespace: str, key: str) -> MemoryRecord | None: ...
    async def query(self, namespace: str, text: str, limit: int = 10) -> list[MemoryRecord]: ...


class InMemoryMemoryStore:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], MemoryRecord] = {}

    async def put(self, record: MemoryRecord) -> None:
        self._records[(record.namespace, record.key)] = record.model_copy(deep=True)

    async def get(self, namespace: str, key: str) -> MemoryRecord | None:
        record = self._records.get((namespace, key))
        return record.model_copy(deep=True) if record else None

    async def query(self, namespace: str, text: str, limit: int = 10) -> list[MemoryRecord]:
        needle = text.lower()
        matches = [
            record.model_copy(deep=True)
            for (_, _), record in self._records.items()
            if needle in (record.key + " " + record.value).lower()
        ]
        return matches[:limit]
