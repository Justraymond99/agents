from __future__ import annotations

import json

from redis.asyncio import Redis


class RedisRunStateStore:
    def __init__(self, redis_url: str, ttl_seconds: int = 3600) -> None:
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds

    def _key(self, run_id: str) -> str:
        return f"atlas:run:{run_id}"

    async def put(self, run_id: str, state: dict[str, object]) -> None:
        await self.redis.set(
            self._key(run_id),
            json.dumps(state, sort_keys=True),
            ex=self.ttl_seconds,
        )

    async def get(self, run_id: str) -> dict[str, object] | None:
        raw = await self.redis.get(self._key(run_id))
        if raw is None:
            return None
        value = json.loads(raw)
        if not isinstance(value, dict):
            return None
        return value

    async def delete(self, run_id: str) -> None:
        await self.redis.delete(self._key(run_id))

    async def close(self) -> None:
        await self.redis.aclose()
