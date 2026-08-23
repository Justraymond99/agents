from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.models.result import AgentResult
from app.providers.base import ModelClient
from app.tools import Permission, ToolRegistry


class DynamicAgentSpec(BaseModel):
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)
    model: str = Field(min_length=1)
    permissions: set[Permission] = Field(default_factory=set)
    max_tool_rounds: int = Field(default=8, ge=0, le=50)


def build_dynamic_agent(
    spec: DynamicAgentSpec,
    client: ModelClient,
    tool_registry: ToolRegistry | None = None,
) -> BaseAgent[AgentResult]:
    """Build a constrained AgentResult-producing agent from a runtime specification."""
    return BaseAgent(
        name=spec.name,
        role=spec.role,
        model=spec.model,
        client=client,
        response_model=AgentResult,
        system_prompt=spec.system_prompt,
        tool_registry=tool_registry,
        allowed_permissions=set(spec.permissions),
        max_tool_rounds=spec.max_tool_rounds,
    )
