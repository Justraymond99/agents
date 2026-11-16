# ATLAS Core: verify-change

Verification is a repeatable engineering workflow, not a request for an AI assistant to declare its own work correct.

Read `atlas/skills/verify-change/SKILL.md` and ask:

> Use ATLAS verify-change on the current diff. Identify acceptance criteria and risks, run safe relevant checks, and give me a verification report with actual evidence. Do not merge or deploy.

## What a verification report means
- **Verified**: evidence covers the stated claim and material risks; not a guarantee of universal correctness.
- **Partially verified**: some evidence exists but meaningful coverage gaps remain.
- **Blocked**: required verification cannot currently proceed.
- **Failed**: one or more checks failed.

A passing lint or unit-test run is not sufficient proof of an end-to-end feature. Evidence must be matched to each claim. Human approval is still required for consequential actions.

## Fixture checks
From the repository root:

```bash
python -m unittest discover -s tests -p 'test_verification_report.py' -v
```

The fixture checks test report consistency, not model judgment, test quality, or actual app correctness. The skill needs real-world Codex trials and independently assessed evaluations.

**Installer follow-up:** The existing installer/checker enumerates three skills; integrating `verify-change` into Codex installation and smoke tests is a separate issue/PR after the foundational changes are integrated.
