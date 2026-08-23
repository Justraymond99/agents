import pytest
from pydantic import ValidationError

from app.models.task import TaskPlan, TaskStep


def test_valid_task_plan() -> None:
    plan = TaskPlan(
        goal="Fix failing unit test",
        steps=[
            TaskStep(
                id="inspect",
                description="Inspect the failing test",
                assigned_agent="researcher",
            ),
            TaskStep(
                id="fix",
                description="Implement the smallest fix",
                assigned_agent="builder",
                dependencies=["inspect"],
            ),
        ],
    )

    assert plan.goal == "Fix failing unit test"
    assert plan.steps[1].dependencies == ["inspect"]


def test_rejects_duplicate_step_ids() -> None:
    with pytest.raises(ValidationError):
        TaskPlan(
            goal="Duplicate ids",
            steps=[
                TaskStep(id="same", description="First", assigned_agent="planner"),
                TaskStep(id="same", description="Second", assigned_agent="builder"),
            ],
        )


def test_rejects_unknown_dependency() -> None:
    with pytest.raises(ValidationError):
        TaskPlan(
            goal="Unknown dependency",
            steps=[
                TaskStep(
                    id="build",
                    description="Build feature",
                    assigned_agent="builder",
                    dependencies=["missing"],
                )
            ],
        )


def test_rejects_self_dependency() -> None:
    with pytest.raises(ValidationError):
        TaskStep(
            id="loop",
            description="Invalid step",
            assigned_agent="builder",
            dependencies=["loop"],
        )


def test_rejects_cycle() -> None:
    with pytest.raises(ValidationError):
        TaskPlan(
            goal="Cyclic plan",
            steps=[
                TaskStep(
                    id="a",
                    description="A",
                    assigned_agent="planner",
                    dependencies=["b"],
                ),
                TaskStep(
                    id="b",
                    description="B",
                    assigned_agent="builder",
                    dependencies=["a"],
                ),
            ],
        )
