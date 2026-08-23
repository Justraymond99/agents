import pytest

from app.memory import InMemoryMemoryStore, MemoryRecord


@pytest.mark.asyncio
async def test_memory_is_namespaced_and_queryable() -> None:
    store = InMemoryMemoryStore()
    await store.put(MemoryRecord(namespace="engineering/aeroarc", key="cache", value="Use Redis"))
    await store.put(MemoryRecord(namespace="fitness", key="cache", value="Not relevant"))

    matches = await store.query("engineering/aeroarc", "redis")

    assert len(matches) == 1
    assert matches[0].key == "cache"
    assert (await store.get("fitness", "cache")) is not None
