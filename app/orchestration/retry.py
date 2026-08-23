from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RevisionPolicy:
    """Controls reviewer-driven revision attempts.

    Revision is intentionally conservative in the first implementation: only
    selected agent roles are rerun, and the number of attempts is capped.
    """

    max_revision_attempts: int = 1
    revisable_agents: tuple[str, ...] = ("builder",)

    def __post_init__(self) -> None:
        if self.max_revision_attempts < 0:
            raise ValueError("max_revision_attempts must be non-negative")

    def can_retry(self, attempts_used: int) -> bool:
        return attempts_used < self.max_revision_attempts

    def is_revisable(self, agent_name: str) -> bool:
        return agent_name.casefold() in {name.casefold() for name in self.revisable_agents}
