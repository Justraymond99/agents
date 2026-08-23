from __future__ import annotations

from dataclasses import dataclass

from openai import AsyncOpenAI

from app.agents import (
    AgentRegistry,
    BuilderAgent,
    PlannerAgent,
    ResearcherAgent,
    ReviewerAgent,
    TesterAgent,
)
from app.config.settings import Settings, get_settings
from app.memory import InMemoryMemoryStore
from app.orchestration import Orchestrator, RevisionPolicy
from app.persistence import InMemoryTaskStore
from app.providers import OpenAIProvider, RetryingProvider


@dataclass
class AtlasRuntime:
    orchestrator: Orchestrator
    task_store: InMemoryTaskStore
    memory: InMemoryMemoryStore


def build_runtime(settings: Settings | None = None) -> AtlasRuntime:
    settings = settings or get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else AsyncOpenAI()
    provider = RetryingProvider(OpenAIProvider(client))

    planner = PlannerAgent(provider, settings.default_model)
    registry = AgentRegistry()
    registry.register(ResearcherAgent(provider, settings.default_model))
    registry.register(BuilderAgent(provider, settings.default_model))
    registry.register(TesterAgent(provider, settings.default_model))
    registry.register(ReviewerAgent(provider, settings.default_model))

    orchestrator = Orchestrator(
        planner=planner,
        agents=registry,
        revision_policy=RevisionPolicy(max_attempts=settings.max_iterations),
    )
    return AtlasRuntime(
        orchestrator=orchestrator,
        task_store=InMemoryTaskStore(),
        memory=InMemoryMemoryStore(),
    )
