"""Deterministic report checks, not a model-behavior evaluation."""
from dataclasses import dataclass
from typing import Literal

CheckStatus = Literal["passed", "failed", "blocked", "not_run", "not_applicable"]
Verdict = Literal["verified", "partially verified", "blocked", "failed"]


@dataclass(frozen=True)
class Check:
    name: str
    status: CheckStatus
    evidence: str = ""
    reason: str = ""


def validate_report(checks: tuple[Check, ...], verdict: Verdict) -> list[str]:
    """Find contradictions in reported evidence; coverage judgment remains human-led."""
    errors: list[str] = []
    if not checks:
        errors.append("At least one check must be described")
    for check in checks:
        if not check.name.strip():
            errors.append("Each check needs a name")
        if check.status == "passed" and not check.evidence.strip():
            errors.append(f"{check.name}: passing checks require observed evidence")
        if check.status in ("blocked", "not_run", "not_applicable") and not check.reason.strip():
            errors.append(f"{check.name}: status requires a reason")
    if verdict == "verified":
        if not any(c.status == "passed" for c in checks):
            errors.append("Verified requires at least one evidenced passing check")
        if any(c.status in ("failed", "blocked", "not_run") for c in checks):
            errors.append("Verified cannot contain failed, blocked, or unrun required checks")
    if verdict == "failed" and not any(c.status == "failed" for c in checks):
        errors.append("Failed verdict requires a failed check")
    return errors
