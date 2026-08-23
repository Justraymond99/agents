from __future__ import annotations

from app.providers.base import ModelClient
from app.providers.errors import ProviderNotFoundError


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ModelClient] = {}

    def register(self, provider: ModelClient) -> None:
        key = provider.name.strip().lower()
        if not key:
            raise ValueError("provider name cannot be empty")
        self._providers[key] = provider

    def get(self, name: str) -> ModelClient:
        key = name.strip().lower()
        try:
            return self._providers[key]
        except KeyError as exc:
            raise ProviderNotFoundError(f"provider '{name}' is not registered") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
