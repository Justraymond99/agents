import json

import pytest

from app.agents import AgentRegistry, BuilderAgent, PlannerAgent, ResearcherAgent, ReviewerAgent
from app.models.message import ModelRequest, ModelResponse
from app.models.task import Task, TaskStatus
from app.models.trace import TraceEventType
from app.orchestration import Orchestrator, RevisionPolicy


class QueueProvider:
    name = "fake"

    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)
        self.requests: list[ModelRequest] = []

    async def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        if not self.outputs:
            raise AssertionError("fake provider has no queued output")
        return ModelResponse(
            provider=self.name,
            model=request.model,
            output_text=self.outputs.pop(0),
        )


@pytest.mark.asyncio
async def test_orchestrator_executes_dependencies_then_reviews() -> None:
    planner_provider = QueueProvider(
        [
            json.dumps(
                {
                    "goal": "fix bug",
                    "steps": [
                        {
                            "id": "build",
                            "description": "implement fix",
                            "assigned_agent": "builder",
                            "dependencies": ["inspect"],
                        },
                        {
                            "id": "inspect",
                            "description": "inspect bug",
                            "assigned_agent": "researcher",
                            "dependencies": [],
                        },
                    ],
                }
            )
        ]
    )
    researcher_provider = QueueProvider(
        [json.dumps({"agent": "researcher", "success": True, "output": "root cause"})]
    )
    builder_provider = QueueProvider(
        [json.dumps({"agent": "builder", "success": True, "output": "fixed"})]
    )
    reviewer_provider = QueueProvider(
        [json.dumps({"approved": True, "summary": "looks good"})]
    )

    registry = AgentRegistry()
    registry.register(ResearcherAgent(researcher_provider, "test-model"))
    registry.register(BuilderAgent(builder_provider, "test-model"))
    registry.register(ReviewerAgent(reviewer_provider, "test-model"))

    task = Task(id="task-1", goal="Fix the bug")
    orchestrator = Orchestrator(
        planner=PlannerAgent(planner_provider, "test-model"),
        agents=registry,
    )

    result = await orchestrator.execute(task)

    assert result.status is TaskStatus.PASSED
    assert task.status is TaskStatus.PASSED
    assert list(result.results) == ["inspect", "build"]
    assert result.review is not None and result.review.approved is True
    assert result.revision_attempts == 0
    assert result.trace.events[0].event_type is TraceEventType.TASK_STARTED
    assert result.trace.events[-1].event_type is TraceEventType.TASK_COMPLETED


@pytest.mark.asyncio
async def test_orchestrator_stops_when_step_fails() -> None:
    planner_provider = QueueProvider(
        [
            json.dumps(
                {
                    "goal": "investigate",
                    "steps": [
                        {
                            "id": "inspect",
                            "description": "inspect failure",
                            "assigned_agent": "researcher",
                            "dependencies": [],
                        },
                        {
                            "id": "build",
                            "description": "implement fix",
                            "assigned_agent": "builder",
                            "dependencies": ["inspect"],
                        },
                    ],
                }
            )
        ]
    )
    researcher_provider = QueueProvider(
        [
            json.dumps(
                {
                    "agent": "researcher",
                    "success": False,
                    "output": "could not reproduce",
                }
            )
        ]
    )
    builder_provider = QueueProvider(
        [json.dumps({"agent": "builder", "success": True, "output": "unused"})]
    )
    reviewer_provider = QueueProvider(
        [json.dumps({"approved": True, "summary": "unused"})]
    )

    registry = AgentRegistry()
    registry.register(ResearcherAgent(researcher_provider, "test-model"))
    registry.register(BuilderAgent(builder_provider, "test-model"))
    registry.register(ReviewerAgent(reviewer_provider, "test-model"))

    task = Task(id="task-2", goal="Investigate failure")
    result = await Orchestrator(
        planner=PlannerAgent(planner_provider, "test-model"),
        agents=registry,
    ).execute(task)

    assert result.status is TaskStatus.FAILED
    assert list(result.results) == ["inspect"]
    assert len(builder_provider.requests) == 0
    assert len(reviewer_provider.requests) == 0
    assert result.trace.events[-1].event_type is TraceEventType.TASK_FAILED


@pytest.mark.asyncio
async def test_orchestrator_can_disable_revisions() -> None:
    planner_provider = QueueProvider(
        [
            json.dumps(
                {
                    "goal": "change",
                    "steps": [
                        {
                            "id": "build",
                            "description": "make change",
                            "assigned_agent": "builder",
                            "dependencies": [],
                        }
                    ],
                }
            )
        ]
    )
    builder_provider = QueueProvider(
        [json.dumps({"agent": "builder", "success": True, "output": "done"})]
    )
    reviewer_provider = QueueProvider(
        [
            json.dumps(
                {
                    "approved": False,
                    "summary": "needs tests",
                    "blocking_issues": ["missing tests"],
                }
            )
        ]
    )

    registry = AgentRegistry()
    registry.register(BuilderAgent(builder_provider, "test-model"))
    registry.register(ReviewerAgent(reviewer_provider, "test-model"))

    task = Task(id="task-3", goal="Make change")
    result = await Orchestrator(
        planner=PlannerAgent(planner_provider, "test-model"),
        agents=registry,
        revision_policy=RevisionPolicy(max_revision_attempts=0),
    ).execute(task)

    assert result.status is TaskStatus.FAILED
    assert result.review is not None
    assert result.review.blocking_issues == ["missing tests"]
    assert result.revision_attempts == 0
    assert len(builder_provider.requests) == 1
    assert result.trace.events[-1].event_type is TraceEventType.TASK_FAILED


@pytest.mark.asyncio
async def test_orchestrator_revises_builder_after_rejected_review() -> None:
    planner_provider = QueueProvider(
        [
            json.dumps(
                {
                    "goal": "change",
                    "steps": [
                        {
                            "id": "build",
                            "description": "make change",
                            "assigned_agent": "builder",
                            "dependencies": [],
                        }
                    ],
                }
            )
        ]
    )
    builder_provider = QueueProvider(
        [
            json.dumps({"agent": "builder", "success": True, "output": "first draft"}),
            json.dumps({"agent": "builder", "success": True, "output": "revised with tests"}),
        ]
    )
    reviewer_provider = QueueProvider(
        [
            json.dumps(
                {
                    "approved": False,
                    "summary": "needs tests",
                    "blocking_issues": ["missing tests"],
                }
            ),
            json.dumps({"approved": True, "summary": "tests added; approved"}),
        ]
    )

    registry = AgentRegistry()
    registry.register(BuilderAgent(builder_provider, "test-model"))
    registry.register(ReviewerAgent(reviewer_provider, "test-model"))

    task = Task(id="task-4", goal="Make change")
    result = await Orchestrator(
        planner=PlannerAgent(planner_provider, "test-model"),
        agents=registry,
    ).execute(task)

    assert result.status is TaskStatus.PASSED
    assert result.revision_attempts == 1
    assert result.results["build"].output == "revised with tests"
    assert len(builder_provider.requests) == 2
    assert len(reviewer_provider.requests) == 2
    assert any(
        event.event_type is TraceEventType.REVISION_REQUESTED
        for event in result.trace.events
    )
    revision_request = builder_provider.requests[1]
    joined = "\n".join(message.content for message in revision_request.messages)
    assert "missing tests" in joined
    assert "first draft" in joined
    assert result.trace.events[-1].event_type is TraceEventType.TASK_COMPLETED


@pytest.mark.asyncio
async def test_orchestrator_fails_after_revision_limit() -> None:
    planner_provider = QueueProvider(
        [
            json.dumps(
                {
                    "goal": "change",
                    "steps": [
                        {
                            "id": "build",
                            "description": "make change",
                            "assigned_agent": "builder",
                            "dependencies": [],
                        }
                    ],
                }
            )
        ]
    )
    builder_provider = QueueProvider(
        [
            json.dumps({"agent": "builder", "success": True, "output": "first draft"}),
            json.dumps({"agent": "builder", "success": True, "output": "revision"}),
        ]
    )
    reviewer_provider = QueueProvider(
        [
            json.dumps({"approved": False, "summary": "still wrong"}),
            json.dumps({"approved": False, "summary": "still wrong"}),
        ]
    )

    registry = AgentRegistry()
    registry.register(BuilderAgent(builder_provider, "test-model"))
    registry.register(ReviewerAgent(reviewer_provider, "test-model"))

    result = await Orchestrator(
        planner=PlannerAgent(planner_provider, "test-model"),
        agents=registry,
        revision_policy=RevisionPolicy(max_revision_attempts=1),
    ).execute(Task(id="task-5", goal="Make change"))

    assert result.status is TaskStatus.FAILED
    assert result.revision_attempts == 1
    assert len(builder_provider.requests) == 2
    assert len(reviewer_provider.requests) == 2
    assert result.trace.events[-1].event_type is TraceEventType.TASK_FAILED


def test_revision_policy_rejects_negative_attempt_limit() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        RevisionPolicy(max_revision_attempts=-1)
