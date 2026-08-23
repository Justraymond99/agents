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
from app.orchestration import DagScheduler, Orchestrator, RevisionPolicy
from app.persistence import SqlTaskStore, TaskStore
from app.providers import OpenAIProvider, RetryingModelClient
from app.services import TaskManager
from app.tools import ToolRegistry, build_builtin_tools


@dataclass
class AtlasRuntime:
    orchestrator: Orchestrator
    task_store: TaskStore
    memory: InMemoryMemoryStore
    tools: ToolRegistry
    manager: TaskManager

    async def initialize(self) -> None:
        if isinstance(self.task_store, SqlTaskStore):
            await self.task_store.init()

    async def shutdown(self) -> None:
        await self.manager.shutdown()
        if isinstance(self.task_store, SqlTaskStore):
            await self.task_store.close()


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
        revision_policy=RevisionPolicy(max_revision_attempts=settings.max_iterations),
        scheduler=DagScheduler(max_parallel_tasks=settings.max_parallel_tasks),
    )
    task_store: TaskStore = SqlTaskStore(settings.database_url)
    manager = TaskManager(orchestrator, task_store)

    return AtlasRuntime(
        orchestrator=orchestrator,
        task_store=task_store,
        memory=InMemoryMemoryStore(),
        tools=tool_registry,
        manager=manager,
    )
