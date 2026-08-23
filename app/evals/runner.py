from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Awaitable, Callable

from app.models.task import TaskStatus
from app.orchestration.state import OrchestrationResult


@dataclass(frozen=True, slots=True)
class EvalCase:
    name: str
    goal: str
    expected_status: TaskStatus = TaskStatus.PASSED


@dataclass(frozen=True, slots=True)
class EvalResult:
    case: str
    passed: bool
    duration_ms: float
    iterations: int


async def run_eval(
    case: EvalCase,
    executor: Callable[[str], Awaitable[OrchestrationResult]],
) -> EvalResult:
    start = perf_counter()
    result = await executor(case.goal)
    return EvalResult(
        case=case.name,
        passed=result.status is case.expected_status,
        duration_ms=(perf_counter() - start) * 1000,
        iterations=result.revision_attempts,
    )


DEFAULT_ENGINEERING_EVALS = (
    EvalCase("known-bug", "Inspect a repository and fix one known failing unit test."),
    EvalCase("race-review", "Review a concurrent update path and identify a race condition."),
    EvalCase("insecure-pr", "Review a patch containing an authorization bypass."),
    EvalCase("small-api", "Implement a small validated API endpoint with tests."),
)
