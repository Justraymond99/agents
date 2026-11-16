# ATLAS

**Portable AI engineering discipline for the coding assistant you already use.**

ATLAS Core brings structured bug investigation, feature implementation, code review, verification, and optional teaching into existing AI coding environments. **No ATLAS server, MCP setup, or ATLAS API key is required for Core.** Your coding assistant uses its own configured model and tools.

The existing Python **ATLAS Runtime** remains available for advanced multi-agent orchestration, scheduling, persistence, permissions, approvals, and observability. It is optional, not a prerequisite for Core.

## Start here: ATLAS Core (Codex-first)

Prerequisite: Python 3.10+ for the installer; an existing project and compatible coding assistant.

Clone this repository, then run from its root (replace the project path):

```bash
python scripts/atlas_init.py --project /absolute/path/to/your/project --client codex --dry-run
python scripts/atlas_init.py --project /absolute/path/to/your/project --client codex
python scripts/atlas_check.py --project /absolute/path/to/your/project --client codex
```

Open **your project root** in Codex. Try:

> Which ATLAS skills are available? Do not edit anything. Explain the engineering contract and how to enable Teaching Mode.

Then try:

> Use ATLAS Teaching Mode to investigate a bug in this repository. Do not edit files yet. Show your investigation plan and the evidence you need.

The installer copies `AGENTS.md`, canonical skills under `atlas/skills/`, and Codex-compatible skills under `.agents/skills/`. **It never overwrites existing files.** If it reports a skipped file, manually merge the instructions; an existing `AGENTS.md` may otherwise not reference ATLAS. The checker validates file structure, **not** actual Codex discovery or behavior. Confirm skill availability in your client and verify results manually.

For Claude Code use `--client claude` (installs `CLAUDE.md`); for Cursor use `--client cursor` (installs `.cursor/rules/atlas.mdc`). These are instruction-based integrations and may require manual configuration depending on client version.

### Engineering contract

- Understand relevant code and expected behavior before editing.
- Reproduce bugs or gather evidence when feasible; label hypotheses.
- Keep changes minimal and preserve security and safety controls.
- Run relevant checks and report **actual** commands/results.
- Clearly explain remaining risks; never claim self-review is independent.

Core ships three skills: **investigate-bug**, **implement-feature**, and **review-code**. Ask for **ATLAS Teaching Mode** to receive concise explanations of decisions, alternatives, terminology, and verification evidence. Instructions cannot enforce tool permissions or guarantee model compliance.

Run installer tests with `python -m unittest discover -s tests -p 'test_atlas_core.py' -v`.

## Advanced: ATLAS Python Runtime (optional)

ATLAS Runtime is a provider-agnostic multi-agent orchestration harness. It coordinates Planner, Researcher, Builder, Tester and Reviewer agents with typed task DAGs, constrained tools, bounded revisions, persistence, MCP, and evaluations.

### Runtime architecture

```text
MCP / HTTP / Apple client
          |
      ATLAS Runtime
          |
        Planner
          |
       Typed DAG
     /    |    \
Research Build  Test
     \    |    /
      Shared State
          |
        Reviewer
      PASS / REVISE
```

### Runtime stack

Python 3.12+, FastAPI/Pydantic, asyncio, OpenAI Responses adapter behind provider abstraction, SQLAlchemy async SQLite/PostgreSQL, optional Redis, OpenTelemetry, MCP, pytest/Ruff/mypy, Docker, and SwiftUI/watchOS scaffold.

### Runtime quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
cp .env.example .env
```

Set `ATLAS_OPENAI_API_KEY` in `.env`, then start `uvicorn app.main:app --reload`. For MCP run `python -m app.mcp_server`; see [MCP client configuration](docs/MCP_CLIENTS.md).

Runtime HTTP task submission returns `202 Accepted`; poll `GET /tasks/{id}` or `GET /tasks/{id}/result`. Additional endpoints include `/health`, `/dashboard`, `/tools`, `/metrics`, `/memory/write`, `/memory/query`, `/approvals`, `/artifacts`, and `/schedules`.

### Runtime security and limitations

Set `ATLAS_API_TOKEN` before exposing the runtime outside trusted local development. Protected endpoints use `Authorization: Bearer <ATLAS_API_TOKEN>`; `/health` and `/dashboard` remain readable. Built-in filesystem tools are constrained to `ATLAS_WORKSPACE`, commands run without a shell, and roles have tool permissions. High-impact external actions need approval controls before production use.

SQLite is the default (`ATLAS_DATABASE_URL=sqlite+aiosqlite:///./atlas.db`); PostgreSQL and Redis can be started with `docker compose up -d`. See [engineering verification](docs/ENGINEERING_VERIFICATION.md) and [original project specification](PROJECT_SPEC.md).

The runtime is an engineering foundation, **not** a production-hosted autonomous service. Deployment, secrets management, durable distributed scheduling, production-grade authentication/authorization, vector retrieval, push notifications, and signed Apple builds remain future work.

The original Sprint 0–12 roadmap covered API bootstrap, typed DAGs, provider abstraction, agents, orchestration, revision loops, tool safety, scheduling, persistence, telemetry, MCP, engineering workflows, and evaluations. Subsequent scaffolding includes memory, model routing, approval gates, artifacts, recurring schedules, dynamic agents, a dashboard, and Apple thin clients.
