# ATLAS

ATLAS is a provider-agnostic multi-agent orchestration harness designed to coordinate specialized AI agents across engineering, research, planning, interview preparation, and personal workflows.

The harness is the source of truth for orchestration, memory, permissions, retries, evaluation, and observability. Codex, Cursor, CLI, web/mobile clients, and eventually Apple Watch connect to the same backend.

## Current status

- Sprint 0 — repository bootstrap: complete
- Sprint 1 — typed task/result/trace domain models: complete
- Sprint 2 — provider abstraction, OpenAI adapter, registry, normalized errors, and retries: complete
- Sprint 3 — generic agent runtime, Planner/Researcher/Builder/Tester/Reviewer, agent registry, and tests: complete
- Sprint 4 — sequential orchestrator and execution state: next

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
- OpenAI Responses API adapter
- pytest
- OpenTelemetry
- Docker

## Provider layer

ATLAS agents use a common `ModelClient` interface. Provider-specific SDK details stay behind adapters, while orchestration code works with normalized `ModelRequest` and `ModelResponse` contracts.

The first adapter uses OpenAI's Responses API. The provider registry and retry wrapper are intentionally model-provider independent so additional adapters can be added without changing agent or orchestration code.

## Agent layer

Agents share a generic typed `BaseAgent` runtime. Each specialized agent defines its role, system prompt, model, provider client, and expected Pydantic output contract.

The initial registry contains five roles:

- Planner — produces a validated `TaskPlan`
- Researcher — gathers and synthesizes context
- Builder — implements the assigned change
- Tester — independently validates behavior
- Reviewer — independently approves or rejects the result

Execution context is serialized into a developer message so task/run metadata and prior results can be supplied without mixing them into the user's request.

## First milestone

Given a natural-language software task, ATLAS should create a typed plan, dispatch multiple specialized agents, validate the result with an independent tester/reviewer, retry a rejected result once, and return a structured execution trace.

See [`PROJECT_SPEC.md`](./PROJECT_SPEC.md) for the roadmap.
