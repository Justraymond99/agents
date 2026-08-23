from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
from app.providers import OpenAIProvider, RetryingModelClient
from app.tools import ToolRegistry, build_builtin_tools


@dataclass
class AtlasRuntime:
    orchestrator: Orchestrator
    task_store: InMemoryTaskStore
    memory: InMemoryMemoryStore
    tools: ToolRegistry


def build_runtime(settings: Settings | None = None) -> AtlasRuntime:
    settings = settings or get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key or "not-configured")
    provider = RetryingModelClient(OpenAIProvider(client))

    tool_registry = ToolRegistry()
    for tool in build_builtin_tools(Path(settings.workspace)):
        tool_registry.register(tool)

    planner = PlannerAgent(provider, settings.default_model)
    registry = AgentRegistry()
    registry.register(ResearcherAgent(provider, settings.default_model, tool_registry))
    registry.register(BuilderAgent(provider, settings.default_model, tool_registry))
    registry.register(TesterAgent(provider, settings.default_model, tool_registry))
    registry.register(ReviewerAgent(provider, settings.default_model, tool_registry))

    orchestrator = Orchestrator(
        planner=planner,
        agents=registry,
        revision_policy=RevisionPolicy(max_attempts=settings.max_iterations),
    )
    return AtlasRuntime(
        orchestrator=orchestrator,
        task_store=InMemoryTaskStore(),
        memory=InMemoryMemoryStore(),
        tools=tool_registry,
    )
