from app.agents.base import BaseAgent
from app.models.result import ReviewResult
from app.providers.base import ModelClient


REVIEWER_PROMPT = """You are the ATLAS Reviewer.
Review the proposed result independently for correctness, completeness, maintainability, and risk.
Approve only when no blocking issue remains. Return only JSON matching ReviewResult.
"""


class ReviewerAgent(BaseAgent[ReviewResult]):
    def __init__(self, client: ModelClient, model: str) -> None:
        super().__init__(
            name="reviewer",
            role="independent quality and risk review",
            model=model,
            client=client,
            response_model=ReviewResult,
            system_prompt=REVIEWER_PROMPT,
        )
