import json

import pytest

from app.agents import AgentContext, BuilderAgent, PlannerAgent, ReviewerAgent
from app.models.message import ModelRequest, ModelResponse


class FakeProvider:
    name = "fake"

    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.requests: list[ModelRequest] = []

    async def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return ModelResponse(provider=self.name, model=request.model, output_text=self.output_text)


@pytest.mark.asyncio
async def test_planner_returns_typed_plan() -> None:
    provider = FakeProvider(
        json.dumps(
            {
                "goal": "fix failing test",
                "steps": [
                    {
                        "id": "inspect",
                        "description": "inspect the failure",
                        "assigned_agent": "researcher",
                        "dependencies": [],
                        "status": "pending",
                    },
                    {
                        "id": "fix",
                        "description": "implement the fix",
                        "assigned_agent": "builder",
                        "dependencies": ["inspect"],
                        "status": "pending",
                    },
                ],
            }
        )
    )
    agent = PlannerAgent(provider, "test-model")

    result = await agent.run("Fix the failing unit test")

    assert result.goal == "fix failing test"
    assert [step.id for step in result.steps] == ["inspect", "fix"]
    assert provider.requests[0].model == "test-model"


@pytest.mark.asyncio
async def test_builder_includes_execution_context() -> None:
    provider = FakeProvider(
        json.dumps(
            {
                "agent": "builder",
                "success": True,
                "output": "implemented",
                "artifacts": ["app/example.py"],
                "notes": [],
            }
        )
    )
    agent = BuilderAgent(provider, "test-model")
    context = AgentContext(task_id="task-1", values={"failure": "expected 2, got 1"})

    result = await agent.run("Implement the smallest fix", context)

    assert result.success is True
    developer_messages = [
        message for message in provider.requests[0].messages if message.role.value == "developer"
    ]
    assert len(developer_messages) == 1
    assert "task-1" in developer_messages[0].content
    assert "expected 2, got 1" in developer_messages[0].content


@pytest.mark.asyncio
async def test_reviewer_returns_review_result() -> None:
    provider = FakeProvider(
        json.dumps(
            {
                "approved": False,
                "summary": "missing regression test",
                "blocking_issues": ["no regression coverage"],
                "suggestions": [],
            }
        )
    )
    agent = ReviewerAgent(provider, "test-model")

    result = await agent.run("Review this patch")

    assert result.approved is False
    assert result.blocking_issues == ["no regression coverage"]


@pytest.mark.asyncio
async def test_agent_rejects_invalid_json() -> None:
    provider = FakeProvider("not-json")
    agent = BuilderAgent(provider, "test-model")

    with pytest.raises(ValueError, match="invalid AgentResult JSON"):
        await agent.run("Build it")


def test_agent_rejects_empty_prompt() -> None:
    provider = FakeProvider("{}")
    agent = BuilderAgent(provider, "test-model")

    with pytest.raises(ValueError, match="cannot be empty"):
        agent.build_request("   ")
