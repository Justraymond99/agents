from app.agents.base import BaseAgent
from app.models.result import AgentResult
from app.providers.base import ModelClient
from app.tools import Permission, ToolRegistry


BUILDER_PROMPT = """You are the ATLAS Builder.
Implement the assigned change using the provided context and available tools.
Prefer the smallest correct change, preserve existing conventions, and report exactly what was done.
Return only JSON matching AgentResult.
"""


class BuilderAgent(BaseAgent[AgentResult]):
    def __init__(
        self,
        client: ModelClient,
        model: str,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        super().__init__(
            name="builder",
            role="implementation and artifact creation",
            model=model,
            client=client,
            response_model=AgentResult,
            system_prompt=BUILDER_PROMPT,
            tool_registry=tool_registry,
            allowed_permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
        )
