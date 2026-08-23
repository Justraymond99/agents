from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.models.message import ModelRequest, ModelResponse


@runtime_checkable
class ModelClient(Protocol):
    name: str

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a model response for a normalized ATLAS request."""
        ...
