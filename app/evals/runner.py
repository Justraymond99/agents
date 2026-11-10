from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Awaitable, Callable

from app.models.task import TaskStatus
from app.orchestration.state import OrchestrationResult

# A verifier must inspect independent evidence (e.g. tests, a known diff, or
# seeded defects), rather than trusting the model's own approval.
EvidenceVerifier = Callable[["EvalCase", OrchestrationResult], Awaitable["Verification"]]


@dataclass(frozen=True, slots=True)
class EvalCase:
    name: str
    goal: str
    expected_status: TaskStatus = TaskStatus.PASSED


@dataclass(frozen=True, slots=True)
class Verification:
    passed: bool
    evidence: str


@dataclass(frozen=True, slots=True)
class EvalResult:
    case: str
    passed: bool
    duration_ms: float
    iterations: int
    status_matched: bool = False
    verified: bool = False
    evidence: str = ""


async def run_eval(
    case: EvalCase,
    executor: Callable[[str], Awaitable[OrchestrationResult]],
    *,
    verifier: EvidenceVerifier | None = None,
) -> EvalResult:
    start = perf_counter()
    result = await executor(case.goal)
    status_matched = result.status is case.expected_status
    verification = await verifier(case, result) if verifier is not None else None
    # An agent approving its own output is never sufficient to pass an eval.
    passed = status_matched and verification is not None and verification.passed
    return EvalResult(
        case=case.name,
        passed=passed,
        duration_ms=(perf_counter() - start) * 1000,
        iterations=result.revision_attempts,
        status_matched=status_matched,
        verified=verification is not None,
        evidence=verification.evidence if verification is not None else "No independent verifier supplied",
    )


DEFAULT_ENGINEERING_EVALS = (
    EvalCase("known-bug", "Inspect a repository and fix one known failing unit test."),
    EvalCase("race-review", "Review a concurrent update path and identify a race condition."),
    EvalCase("insecure-pr", "Review a patch containing an authorization bypass."),
    EvalCase("small-api", "Implement a small validated API endpoint with tests."),
)
