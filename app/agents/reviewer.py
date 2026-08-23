from app.agents.base import BaseAgent
from app.models.result import ReviewResult
from app.providers.base import ModelClient
from app.tools import Permission, ToolRegistry


REVIEWER_PROMPT = """You are the ATLAS Reviewer.
Review the proposed result independently for correctness, completeness, maintainability, and risk.
Approve only when no blocking issue remains. Return only JSON matching ReviewResult.
"""


class ReviewerAgent(BaseAgent[ReviewResult]):
    def __init__(
        self,
        client: ModelClient,
        model: str,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        super().__init__(
            name="reviewer",
            role="independent quality and risk review",
            model=model,
            client=client,
            response_model=ReviewResult,
            system_prompt=REVIEWER_PROMPT,
            tool_registry=tool_registry,
            allowed_permissions={Permission.READ},
        )
