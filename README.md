# ATLAS

ATLAS is a provider-agnostic multi-agent orchestration harness designed to coordinate specialized AI agents across engineering, research, planning, interview preparation, and personal workflows.

The harness is the source of truth for orchestration, memory, permissions, retries, evaluation, and observability. Codex, Cursor, CLI, web/mobile clients, and eventually Apple Watch connect to the same backend.

## Current status

Sprint 0 — repository bootstrap.

## Initial architecture

```text
Task
  -> Planner
  -> Task Graph
  -> Specialized Agents
  -> Tester
  -> Reviewer
      -> Pass -> Done
      -> Fail -> Revision Loop
```

## Stack

- Python 3.12+
- FastAPI
- Pydantic
- asyncio
- PostgreSQL
- Redis
- pytest
- OpenTelemetry
- Docker

## First milestone

Given a natural-language software task, ATLAS should create a typed plan, dispatch multiple specialized agents, validate the result with an independent tester/reviewer, retry a rejected result once, and return a structured execution trace.

See [`PROJECT_SPEC.md`](./PROJECT_SPEC.md) for the roadmap.
