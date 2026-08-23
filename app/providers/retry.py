from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.models.message import ModelRequest, ModelResponse
from app.providers.base import ModelClient
from app.providers.errors import ProviderError


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay_seconds < 0:
            raise ValueError("base_delay_seconds cannot be negative")
        if self.max_delay_seconds < self.base_delay_seconds:
            raise ValueError("max_delay_seconds must be >= base_delay_seconds")


class RetryingModelClient:
    def __init__(self, client: ModelClient, policy: RetryPolicy | None = None) -> None:
        self._client = client
        self._policy = policy or RetryPolicy()
        self.name = client.name

    async def generate(self, request: ModelRequest) -> ModelResponse:
        last_error: ProviderError | None = None

        for attempt in range(1, self._policy.max_attempts + 1):
            try:
                return await self._client.generate(request)
            except ProviderError as exc:
                last_error = exc
                if attempt == self._policy.max_attempts:
                    break

                delay = min(
                    self._policy.base_delay_seconds * (2 ** (attempt - 1)),
                    self._policy.max_delay_seconds,
                )
                if delay > 0:
                    await asyncio.sleep(delay)

        assert last_error is not None
        raise last_error
