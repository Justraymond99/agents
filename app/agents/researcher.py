from app.agents.base import BaseAgent
from app.models.result import AgentResult
from app.providers.base import ModelClient


RESEARCHER_PROMPT = """You are the ATLAS Researcher.
Gather and synthesize the context needed for the assigned task.
Do not claim actions you did not perform. Return only JSON matching AgentResult.
"""


class ResearcherAgent(BaseAgent[AgentResult]):
    def __init__(self, client: ModelClient, model: str) -> None:
        super().__init__(
            name="researcher",
            role="context gathering and synthesis",
            model=model,
            client=client,
            response_model=AgentResult,
            system_prompt=RESEARCHER_PROMPT,
        )
