---
name: review-code
description: Review code or pull requests for correctness, security, regressions and missing verification.
---
# Review Code
1. Establish diff scope, intended behavior, affected consumers and test coverage.
2. Trace changed code in context, including data flow, state transitions and failure paths.
3. Identify actionable correctness, security, data integrity and reliability issues first.
4. Run focused tests if available; otherwise explicitly describe static-review limits.
5. Rank findings with severity, file/location, failure scenario and proposed remediation.
6. Report what was checked, blocking findings, missing tests and remaining uncertainty.
Never invent findings or test outcomes. Reviewing your own work is not independent verification.
