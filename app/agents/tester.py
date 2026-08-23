from app.agents.base import BaseAgent
from app.models.result import AgentResult
from app.providers.base import ModelClient


TESTER_PROMPT = """You are the ATLAS Tester.
Validate the assigned behavior independently. Reproduce failures when possible, run or reason from tests and evidence, and clearly separate observed results from assumptions.
Return only JSON matching AgentResult.
"""


class TesterAgent(BaseAgent[AgentResult]):
    def __init__(self, client: ModelClient, model: str) -> None:
        super().__init__(
            name="tester",
            role="behavior validation and failure reproduction",
            model=model,
            client=client,
            response_model=AgentResult,
            system_prompt=TESTER_PROMPT,
        )
