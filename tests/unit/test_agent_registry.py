import json

import pytest

from app.agents import AgentRegistry, BuilderAgent, PlannerAgent
from app.models.message import ModelRequest, ModelResponse


class FakeProvider:
    name = "fake"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(provider=self.name, model=request.model, output_text=json.dumps({}))


def test_registry_registers_and_retrieves_agents() -> None:
    provider = FakeProvider()
    planner = PlannerAgent(provider, "test-model")
    builder = BuilderAgent(provider, "test-model")
    registry = AgentRegistry()

    registry.register(planner)
    registry.register(builder)

    assert registry.get("PLANNER") is planner
    assert registry.get("builder") is builder
    assert registry.names() == ("builder", "planner")
    assert "planner" in registry


def test_registry_rejects_duplicate_agent_names() -> None:
    provider = FakeProvider()
    registry = AgentRegistry()
    registry.register(PlannerAgent(provider, "test-model"))

    with pytest.raises(ValueError, match="already registered"):
        registry.register(PlannerAgent(provider, "test-model"))


def test_registry_raises_for_unknown_agent() -> None:
    registry = AgentRegistry()

    with pytest.raises(KeyError, match="not registered"):
        registry.get("missing")
