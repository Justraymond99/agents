import pytest

from app.memory.store import InMemoryMemoryStore, MemoryRecord


@pytest.mark.asyncio
async def test_query_is_scoped_to_requested_namespace() -> None:
    store = InMemoryMemoryStore()
    await store.put(
        MemoryRecord(
            namespace="engineering/aeroarc",
            key="deployment",
            value="shared-keyword production rollout notes",
        )
    )
    await store.put(
        MemoryRecord(
            namespace="personal",
            key="private-note",
            value="shared-keyword personal note",
        )
    )

    results = await store.query("engineering/aeroarc", "shared-keyword")

    assert [record.namespace for record in results] == ["engineering/aeroarc"]
    assert [record.key for record in results] == ["deployment"]
