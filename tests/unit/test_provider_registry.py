import pytest

from app.models.message import ModelRequest, ModelResponse
from app.providers.errors import ProviderNotFoundError
from app.providers.registry import ProviderRegistry


class FakeProvider:
    name = "fake"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(provider=self.name, model=request.model, output_text="ok")


def test_registry_registers_and_retrieves_provider() -> None:
    registry = ProviderRegistry()
    provider = FakeProvider()

    registry.register(provider)

    assert registry.get("FAKE") is provider
    assert registry.names() == ("fake",)


def test_registry_raises_for_unknown_provider() -> None:
    registry = ProviderRegistry()

    with pytest.raises(ProviderNotFoundError, match="not registered"):
        registry.get("missing")
