import pytest

from app.evals import EvalCase, run_eval
from app.evals.runner import Verification
from app.models.result import ReviewResult
from app.models.task import TaskStatus
from app.models.trace import RunTrace
from app.orchestration.state import OrchestrationResult


def outcome(status: TaskStatus = TaskStatus.PASSED) -> OrchestrationResult:
    return OrchestrationResult(
        task_id="task-1",
        run_id="run-1",
        status=status,
        review=ReviewResult(approved=True, summary="agent claims success"),
        trace=RunTrace(run_id="run-1", task_id="task-1"),
    )


@pytest.mark.asyncio
async def test_self_approval_is_not_an_eval_pass() -> None:
    async def executor(goal: str) -> OrchestrationResult:
        return outcome()

    result = await run_eval(EvalCase("self-approved", "fix bug"), executor)
    assert result.status_matched
    assert not result.verified
    assert not result.passed


@pytest.mark.asyncio
async def test_independent_verifier_can_pass() -> None:
    async def executor(goal: str) -> OrchestrationResult:
        return outcome()

    async def verifier(case: EvalCase, result: OrchestrationResult) -> Verification:
        return Verification(passed=True, evidence="Seeded regression test passed")

    result = await run_eval(EvalCase("known-bug", "fix bug"), executor, verifier=verifier)
    assert result.passed
    assert result.verified
    assert result.evidence == "Seeded regression test passed"


@pytest.mark.asyncio
async def test_failed_verification_overrides_agent_approval() -> None:
    async def executor(goal: str) -> OrchestrationResult:
        return outcome()

    async def verifier(case: EvalCase, result: OrchestrationResult) -> Verification:
        return Verification(passed=False, evidence="Known vulnerability still present")

    result = await run_eval(EvalCase("security", "fix bypass"), executor, verifier=verifier)
    assert result.status_matched
    assert not result.passed


@pytest.mark.asyncio
async def test_status_mismatch_fails_even_with_positive_evidence() -> None:
    async def executor(goal: str) -> OrchestrationResult:
        return outcome(TaskStatus.FAILED)

    async def verifier(case: EvalCase, result: OrchestrationResult) -> Verification:
        return Verification(passed=True, evidence="Independent test passed")

    result = await run_eval(EvalCase("bug", "fix bug"), executor, verifier=verifier)
    assert result.verified
    assert not result.status_matched
    assert not result.passed
