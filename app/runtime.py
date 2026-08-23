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
from app.approvals import ApprovalManager
from app.config.settings import Settings, get_settings
from app.memory import MemoryStore, SqlMemoryStore
from app.observability import MetricsRecorder, configure_tracing
from app.orchestration import DagScheduler, Orchestrator, RevisionPolicy
from app.persistence import SqlTaskStore, TaskStore
from app.providers import OpenAIProvider, RetryingModelClient
from app.services import TaskManager
from app.tools import ToolRegistry, build_builtin_tools


@dataclass
class AtlasRuntime:
    orchestrator: Orchestrator
    task_store: TaskStore
    memory: MemoryStore
    tools: ToolRegistry
    metrics: MetricsRecorder
    approvals: ApprovalManager
    manager: TaskManager

    async def initialize(self) -> None:
        configure_tracing("atlas")
        if isinstance(self.task_store, SqlTaskStore):
            await self.task_store.init()
        if isinstance(self.memory, SqlMemoryStore):
            await self.memory.init()

    async def shutdown(self) -> None:
        await self.manager.shutdown()
        if isinstance(self.task_store, SqlTaskStore):
            await self.task_store.close()
        if isinstance(self.memory, SqlMemoryStore):
            await self.memory.close()


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
    memory: MemoryStore = SqlMemoryStore(settings.database_url)
    metrics = MetricsRecorder()
    approvals = ApprovalManager()
    manager = TaskManager(orchestrator, task_store, metrics)

    return AtlasRuntime(
        orchestrator=orchestrator,
        task_store=task_store,
        memory=memory,
        tools=tool_registry,
        metrics=metrics,
        approvals=approvals,
        manager=manager,
    )
