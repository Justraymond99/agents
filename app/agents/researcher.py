from app.agents.base import BaseAgent
from app.models.result import AgentResult
from app.providers.base import ModelClient
from app.tools import Permission, ToolRegistry


RESEARCHER_PROMPT = """You are the ATLAS Researcher.
Gather and synthesize the context needed for the assigned task.
Do not claim actions you did not perform. Return only JSON matching AgentResult.
"""


class ResearcherAgent(BaseAgent[AgentResult]):
    def __init__(
        self,
        client: ModelClient,
        model: str,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        super().__init__(
            name="researcher",
            role="context gathering and synthesis",
            model=model,
            client=client,
            response_model=AgentResult,
            system_prompt=RESEARCHER_PROMPT,
            tool_registry=tool_registry,
            allowed_permissions={Permission.READ},
        )
