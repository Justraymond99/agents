from app.agents.base import BaseAgent
from app.models.task import TaskPlan
from app.providers.base import ModelClient


PLANNER_PROMPT = """You are the ATLAS Planner.
Decompose the requested goal into the smallest useful executable task graph.
Assign each step to one of: researcher, builder, tester, reviewer.
Return only JSON matching the TaskPlan schema. Keep dependencies explicit and acyclic.
"""


class PlannerAgent(BaseAgent[TaskPlan]):
    def __init__(self, client: ModelClient, model: str) -> None:
        super().__init__(
            name="planner",
            role="task planning and decomposition",
            model=model,
            client=client,
            response_model=TaskPlan,
            system_prompt=PLANNER_PROMPT,
        )
