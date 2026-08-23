# ATLAS — Multi-Agent Personal Orchestration Harness

ATLAS is a provider-agnostic multi-agent orchestration harness intended to become a reusable personal AI operating layer across software engineering, research, interview preparation, planning, fitness workflows, and eventually iPhone / Apple Watch clients.

## Core principles

- The harness owns orchestration; Codex, Cursor, CLI, web, iPhone, and Watch are clients.
- Agents have constrained responsibilities and tool permissions.
- Model providers are abstracted behind a common interface.
- Every major object uses typed contracts.
- Independent testing and review are part of the workflow.
- Every run has explicit limits, retries, and termination conditions.
- Observability is built in from the start.

## Initial agents

- Planner — decomposes goals into typed steps and dependencies.
- Researcher — gathers context and project knowledge.
- Builder — implements code or approved actions.
- Tester — reproduces failures and validates behavior.
- Reviewer — independently approves or rejects results.

## Core workflow

```text
Task
  -> Planner
  -> Typed Task Graph
  -> Scheduler
  -> Specialized Agents
  -> Shared State
  -> Tester
  -> Reviewer
      -> PASS -> Done
      -> FAIL -> Revision Loop
```

## Phase 1 stack

```text
Python 3.12+
FastAPI
Pydantic
asyncio
PostgreSQL
Redis
pytest
OpenTelemetry
Docker
```

## Repository direction

```text
app/
  api/
  agents/
  orchestration/
  providers/
  tools/
  memory/
  models/
  observability/
  config/
tests/
  unit/
  integration/
  evals/
```

## Initial contracts

```python
from enum import Enum
from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    waiting = "waiting"
    passed = "passed"
    failed = "failed"
    cancelled = "cancelled"

class TaskStep(BaseModel):
    id: str
    description: str
    assigned_agent: str
    dependencies: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.pending

class TaskPlan(BaseModel):
    goal: str
    steps: list[TaskStep]

class AgentResult(BaseModel):
    agent: str
    success: bool
    output: str
    artifacts: list[str] = []
    notes: list[str] = []

class ReviewResult(BaseModel):
    approved: bool
    summary: str
    blocking_issues: list[str] = []
    suggestions: list[str] = []
```

## Tool permissions

Suggested levels:

```text
READ
WRITE
EXECUTE
NETWORK
EXTERNAL_SIDE_EFFECT
ADMIN
```

Example boundaries:

```text
Planner: READ memory only
Researcher: READ + NETWORK
Builder: READ + WRITE + EXECUTE
Tester: READ + EXECUTE
Reviewer: READ
```

High-impact external actions require approval.

## Memory

Short-term memory stores per-run state, intermediate outputs, tool results, tests, and revisions.

Long-term memory stores project architecture, prior decisions, reusable notes, project history, interview weaknesses, and user-defined preferences.

Suggested namespaces:

```text
engineering/aeroarc
engineering/personal
interview/backend
fitness
career
research
personal
```

## Execution limits

Initial defaults:

```text
max_iterations = 3
max_agents_per_task = 8
max_runtime_seconds = 900
max_tool_calls = 50
max_parallel_tasks = 4
max_cost_usd = configurable
```

## Observability

Capture at minimum:

```text
task_id
run_id
agent
model
prompt_tokens
completion_tokens
latency
tool_calls
tool_latency
errors
retries
cost
review_outcome
artifacts
start_time
end_time
```

## MCP surface

Once the local harness is stable, expose tools such as:

```text
submit_task
get_task_status
get_task_result
query_memory
plan_project
run_code_review
run_research
run_tests
```

Codex and Cursor should both connect to the same harness through MCP.

## HTTP API

```text
POST /tasks
GET  /tasks/{task_id}
GET  /tasks/{task_id}/result
GET  /tasks/{task_id}/trace
POST /tasks/{task_id}/cancel
GET  /agents
GET  /tools
POST /memory/query
POST /memory/write
```

## Apple Watch / iPhone direction

The Watch is a thin client, not an agent runtime.

```text
Apple Watch
    -> SwiftUI Watch App
    -> iPhone Companion / HTTPS
    -> ATLAS API
    -> Agents + Tools + Memory
```

Initial Watch capabilities:

```text
ASK
APPROVE
STATUS
NOTIFY
```

Example commands:

```text
What are my top priorities?
Review the AeroArc branch.
Start interview gauntlet.
What workout do I have today?
Save this idea to project memory.
Summarize what changed today.
```

## Milestone 1 — Minimum Viable Harness

Definition of done:

1. Accept a natural-language software task through CLI or API.
2. Generate a typed task plan.
3. Assign at least two specialized agents.
4. Execute the steps.
5. Pass results to an independent tester/reviewer.
6. Reject a deliberately bad result.
7. Retry the failed step once.
8. Return a structured final result.
9. Produce a complete execution trace.
10. Enforce runtime and iteration limits.

## Implementation roadmap

### Sprint 0 — Bootstrap
- Python project
- FastAPI skeleton
- lint / formatting
- pytest
- configuration
- Dockerfile
- CI
- README

### Sprint 1 — Core schemas
- Task
- TaskStep
- TaskPlan
- AgentResult
- ReviewResult
- RunTrace
- enums and validation

### Sprint 2 — Provider layer
- ModelClient protocol
- provider registry
- first OpenAI adapter
- structured outputs
- retries

### Sprint 3 — Base agents
- base Agent
- agent registry
- Planner
- Researcher
- Builder
- Tester
- Reviewer

### Sprint 4 — Orchestrator v0
- sequential execution
- plan validation
- state tracking
- result collection
- failure propagation

### Sprint 5 — Revision loop
- review rejection
- revision request
- retry policy
- max iterations
- terminal failure

### Sprint 6 — Tools
Initial tools:

```text
read_file
write_file
list_files
run_command
run_tests
git_diff
```

### Sprint 7 — DAG + concurrency
- dependency graph
- topological validation
- ready-step queue
- asyncio.gather
- parallel limits

### Sprint 8 — Persistence
PostgreSQL:

```text
tasks
runs
steps
agent_results
tool_calls
reviews
```

Redis:

```text
active run state
locks
ephemeral context
```

### Sprint 9 — Observability
- structured logs
- OpenTelemetry spans
- model usage
- latency
- tool timing
- token/cost accounting

### Sprint 10 — MCP
Expose the first stable tool surface and connect Codex + Cursor.

### Sprint 11 — Engineering domain pack
Use real repositories for repo exploration, feature planning, implementation, testing, debugging, code review, and PR summaries.

### Sprint 12 — Evaluation harness
Benchmark known bugs, insecure PRs, API implementation, failing tests, and concurrency issues.

## First demo

Prompt:

```text
Inspect this Python repository, identify why one unit test is failing,
implement the smallest fix, run the tests, and review the patch.
```

Expected trace:

```text
Planner
  -> Researcher inspects repository
  -> Tester reproduces failure
  -> Builder implements fix
  -> Tester reruns tests
  -> Reviewer reviews diff
  -> Result returned
```

## Non-goals for v0.1

Do not build yet:

- autonomous swarms
- dozens of agents
- complex vector-memory architecture
- native Watch agent execution
- fully autonomous high-impact external side effects
- elaborate frontend
- multi-cloud deployment
- custom model training

## Immediate build order

```text
1. Bootstrap repo
2. Define schemas
3. Build ModelClient
4. Build Planner
5. Build Builder
6. Build Tester
7. Build Reviewer
8. Build sequential Orchestrator
9. Add revision loop
10. Add constrained tools
11. Add traces
12. Build first end-to-end demo
13. DAG execution
14. Persistence
15. MCP
16. Codex
17. Cursor
18. Domain packs
19. iPhone
20. Apple Watch
```

## Success criterion

ATLAS is successful when a user can submit a meaningful task from any supported interface and trust the harness to plan it, select the right agents, use the right tools, execute within explicit limits, independently validate the result, retain useful context, provide a transparent trace, and return a high-quality result without requiring the client itself to manage the workflow.

The end state is not many agents talking.

> **The end state is one dependable system that coordinates intelligent work across the user's entire digital workflow.**
