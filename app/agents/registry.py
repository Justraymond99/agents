from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.agents.base import BaseAgent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent[Any]] = {}

    def register(self, agent: BaseAgent[BaseModel] | BaseAgent[Any]) -> None:
        key = agent.name.strip().lower()
        if not key:
            raise ValueError("agent name cannot be empty")
        if key in self._agents:
            raise ValueError(f"agent '{key}' is already registered")
        self._agents[key] = agent

    def get(self, name: str) -> BaseAgent[Any]:
        key = name.strip().lower()
        try:
            return self._agents[key]
        except KeyError as exc:
            raise KeyError(f"agent '{key}' is not registered") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._agents))

    def __contains__(self, name: str) -> bool:
        return name.strip().lower() in self._agents
