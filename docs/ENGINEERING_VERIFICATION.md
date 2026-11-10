# ATLAS engineering verification workflow

ATLAS complements Cursor, Codex, Claude, GitHub Actions, CodeRabbit, and Sentry. It does **not** replace any of them.

## Responsibilities

- **GitHub issues/PRs:** canonical scope, owner, acceptance criteria, and human decisions.
- **Cursor / Codex / Claude:** independent implementation environments; use separate worktrees for concurrent edits.
- **GitHub Actions:** authoritative deterministic lint, type checks, and tests.
- **CodeRabbit:** automated review suggestions.
- **ATLAS:** optional, read-only second-level analysis for high-risk changes; report unique findings and evidence.
- **Sentry:** production error signals, not proof of safety.

## Change risk

- **Low:** documentation, copy, styling. CI and ordinary review.
- **Medium:** typical feature/API changes. CI, targeted regression tests, human review.
- **High:** authentication, navigation safety, concurrency, data integrity. CI, targeted safety tests, human review, and optional ATLAS evidence report.

Only a human may approve a high-risk merge. ATLAS must not push, merge, deploy, or modify production as part of verification.

## PR evidence contract

Each PR should link an issue, name an owner, state intended behavior and relevant invariants, list tests actually executed, and disclose residual risks. Keep agent-generated claims distinct from independently executed results. If two people work on one feature, designate an integration owner and isolate concurrent agent changes.

## Measuring incremental value

For each high-risk PR record: ATLAS-only confirmed findings, false positives, extra review minutes, and escaped regressions. Compare with similar PRs using CI and CodeRabbit but without ATLAS. Keep the same test suite and review criteria for both groups.

The evaluation API now distinguishes `status_matched` (the orchestration reported its expected status) from `verified` (an independent verifier ran) and `passed` (both status and evidence passed). Without a verifier, an evaluation **does not pass**.

Example:

```python
from app.evals import EvalCase, run_eval
from app.evals.runner import Verification

async def verifier(case, result):
    # Replace this with independent test execution / seeded-defect checks.
    return Verification(passed=False, evidence="No independent test executed")

report = await run_eval(EvalCase("known-bug", "Fix known regression"), execute, verifier=verifier)
```

The default cases are **scenario descriptions**, not executable ground-truth tests. Do not report benchmark accuracy until verifiers are connected to isolated fixtures and known expected outcomes.

## Operational safety

ATLAS's `run_command` accepts arbitrary executable names; avoiding a shell does not provide isolation. Until a container/VM sandbox, resource limits, and approval boundaries are enforced, keep untrusted tasks read-only and do not grant execution permission against sensitive workspaces.
