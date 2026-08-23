from __future__ import annotations

from dataclasses import dataclass

from app.tools import Permission


@dataclass(frozen=True, slots=True)
class EngineeringPolicy:
    namespace: str = "engineering/personal"
    reviewer_required: bool = True
    tests_required: bool = True
    allowed_permissions: frozenset[Permission] = frozenset(
        {Permission.READ, Permission.WRITE, Permission.EXECUTE}
    )


ENGINEERING_WORKFLOWS: dict[str, str] = {
    "fix_bug": (
        "Inspect the repository, reproduce the defect, identify root cause, implement the smallest "
        "safe fix, run focused and regression tests, then review the diff."
    ),
    "implement_feature": (
        "Inspect existing patterns, plan the smallest compatible change, implement it, add tests, "
        "run validation, and review the diff for correctness and maintainability."
    ),
    "code_review": (
        "Review the supplied code or diff for correctness, security, concurrency, data integrity, "
        "performance, maintainability, observability, and test coverage."
    ),
    "debug": (
        "Reproduce the problem before editing code, collect evidence, form and test hypotheses, "
        "identify root cause, then propose or implement the smallest verified fix."
    ),
}
