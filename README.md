# ATLAS

ATLAS is a provider-agnostic multi-agent orchestration harness designed to coordinate specialized AI agents across engineering, research, planning, interview preparation, and personal workflows.

The harness owns orchestration, tool permissions, execution limits, memory, persistence, review/revision, scheduling, artifacts, approvals, observability, and client interfaces. Codex, Cursor, HTTP clients, and the Apple thin-client scaffold all connect to the same backend.

## v0.1 status

The original implementation roadmap through Sprint 12 is now represented in the repository:

- Sprint 0 — Python/FastAPI bootstrap, Docker, CI, configuration
- Sprint 1 — typed task/result/trace models and DAG validation
- Sprint 2 — provider abstraction, OpenAI Responses adapter, retry/error normalization
- Sprint 3 — Planner, Researcher, Builder, Tester, Reviewer, agent registry
- Sprint 4 — orchestrator and explicit execution state
- Sprint 5 — bounded reviewer-driven revision loop
- Sprint 6 — constrained tools, permissions, timeouts, workspace sandboxing, audit records
- Sprint 7 — bounded concurrent DAG scheduler
- Sprint 8 — async SQL task/result persistence and Redis run-state support
- Sprint 9 — OpenTelemetry tracing plus runtime counters/timings
- Sprint 10 — MCP server for Codex/Cursor-style clients
- Sprint 11 — engineering domain workflows
- Sprint 12 — evaluation harness and benchmark cases

Post-MVP capabilities are also scaffolded: SQL long-term memory, model routing/budget policy, approval gates, artifact storage, background tasks, recurring schedules, dynamic agents, HTTP API security, a lightweight dashboard, and iPhone/watchOS client source.

## Architecture

```text
Client (MCP / HTTP / Apple)
          |
          v
      ATLAS Runtime
          |
          v
       Planner
          |
          v
      Typed DAG
     /    |    \
Research Build  Test
     \    |    /
      Shared State
          |
          v
       Reviewer
       /      \
    PASS      REVISE
                |
                +----> bounded retry
```

## Core stack

- Python 3.12+
- FastAPI + Pydantic
- asyncio
- OpenAI Responses API adapter behind a provider-neutral interface
- SQLAlchemy async persistence (SQLite by default; PostgreSQL supported)
- Redis support for ephemeral run state
- OpenTelemetry
- MCP
- pytest, Ruff, mypy
- Docker / Docker Compose
- SwiftUI/watchOS thin-client source

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
cp .env.example .env
```

Set `ATLAS_OPENAI_API_KEY` in `.env`, then run:

```bash
uvicorn app.main:app --reload
```

Useful endpoints:

```text
GET  /health
POST /tasks
GET  /tasks/{id}
GET  /tasks/{id}/result
GET  /tasks/{id}/trace
POST /tasks/{id}/cancel
GET  /tools
GET  /tools/audit
GET  /metrics
POST /memory/write
POST /memory/query
POST /approvals
POST /artifacts
POST /schedules
GET  /dashboard
```

Task submission is asynchronous over HTTP and returns `202 Accepted`; poll the task/result endpoints for completion.

## Security

Set `ATLAS_API_TOKEN` before exposing ATLAS beyond a trusted local development environment. When configured, every HTTP endpoint except `/health` requires:

```text
Authorization: Bearer <ATLAS_API_TOKEN>
```

Built-in filesystem tools are constrained to `ATLAS_WORKSPACE`, commands are executed without a shell, and agents receive role-specific tool permissions. High-impact external actions should be routed through approval gates before production use.

## MCP

Start the MCP server with:

```bash
python -m app.mcp_server
```

Current MCP surface includes task submission/status/results/cancellation, namespaced memory, artifacts, approval requests, and runtime metrics. See [`docs/MCP_CLIENTS.md`](docs/MCP_CLIENTS.md) for client configuration.

## Persistence

The default local database is SQLite:

```text
ATLAS_DATABASE_URL=sqlite+aiosqlite:///./atlas.db
```

For PostgreSQL, use an async URL such as:

```text
ATLAS_DATABASE_URL=postgresql+asyncpg://atlas:atlas@localhost:5432/atlas
```

`docker compose up -d` starts local PostgreSQL and Redis services.

## Engineering workflow

A typical task can follow:

```text
Planner
  -> Researcher inspects context
  -> Tester reproduces failure
  -> Builder makes the smallest verified change
  -> Tester validates
  -> Reviewer independently approves or rejects
  -> Builder revises when required
```

The model may request constrained tools such as `read_file`, `write_file`, `list_files`, `run_command`, `run_tests`, and `git_diff`. Every executed tool call is recorded in the in-process audit trail.

## Apple Watch / iPhone

`clients/apple/` contains the initial Swift thin-client source. The Watch does not host the agents; it submits tasks to the ATLAS API, checks status/results, and can resolve approvals. A real device build still requires creating the iOS/watchOS targets in Xcode, configuring a reachable HTTPS endpoint, and provisioning/authentication.

## What v0.1 deliberately does not claim

ATLAS is a functional engineering foundation, not a production-hosted autonomous service yet. Deployment, secrets management, durable distributed scheduling, production-grade authentication/authorization, vector retrieval, push notifications, and a signed App Store/watchOS build remain environment/deployment work rather than core harness code.

See [`PROJECT_SPEC.md`](PROJECT_SPEC.md) for the original design and roadmap.
