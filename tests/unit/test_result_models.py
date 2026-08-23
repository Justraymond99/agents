from app.models.result import AgentResult, ReviewResult
from app.models.trace import RunTrace, TraceEvent, TraceEventType


def test_agent_result_defaults() -> None:
    result = AgentResult(agent="builder", success=True, output="done")

    assert result.artifacts == []
    assert result.notes == []


def test_review_result_defaults() -> None:
    result = ReviewResult(approved=True, summary="looks good")

    assert result.blocking_issues == []
    assert result.suggestions == []


def test_run_trace_adds_events() -> None:
    trace = RunTrace(run_id="run-1", task_id="task-1")
    trace.add(
        TraceEvent(
            event_type=TraceEventType.TASK_STARTED,
            message="task started",
        )
    )

    assert len(trace.events) == 1
    assert trace.events[0].event_type is TraceEventType.TASK_STARTED
