from __future__ import annotations

import json
from uuid import uuid4

from app.agents import AgentContext, AgentRegistry, PlannerAgent
from app.models.result import AgentResult, ReviewResult
from app.models.task import Task, TaskStatus
from app.models.trace import RunTrace, TraceEvent, TraceEventType
from app.orchestration.state import ExecutionState, OrchestrationResult


class Orchestrator:
    """Initial sequential ATLAS orchestrator.

    Sprint 4 deliberately favors explicit state transitions and traceability over
    concurrency. DAG-aware parallel execution is added in a later sprint.
    """

    def __init__(
        self,
        *,
        planner: PlannerAgent,
        agents: AgentRegistry,
        reviewer_name: str = "reviewer",
    ) -> None:
        self.planner = planner
        self.agents = agents
        self.reviewer_name = reviewer_name

    async def execute(self, task: Task) -> OrchestrationResult:
        run_id = str(uuid4())
        trace = RunTrace(run_id=run_id, task_id=task.id)
        state = ExecutionState(task_id=task.id, run_id=run_id, trace=trace)

        self._trace(state, TraceEventType.TASK_STARTED, f"Task '{task.id}' started")
        state.status = TaskStatus.RUNNING

        plan = await self.planner.run(
            task.goal,
            AgentContext(task_id=task.id, run_id=run_id),
        )
        state.plan = plan
        task.plan = plan
        task.status = TaskStatus.RUNNING
        self._trace(state, TraceEventType.PLAN_CREATED, "Planner produced a validated task plan")

        pending = {step.id: step for step in plan.steps}
        completed: set[str] = set()

        while pending:
            ready = [
                step
                for step in pending.values()
                if set(step.dependencies).issubset(completed)
            ]

            if not ready:
                state.status = TaskStatus.FAILED
                task.status = TaskStatus.FAILED
                self._trace(
                    state,
                    TraceEventType.TASK_FAILED,
                    "No executable task step remained; dependency state is invalid",
                )
                return self._result(state)

            for step in ready:
                self._trace(
                    state,
                    TraceEventType.AGENT_STARTED,
                    f"Agent '{step.assigned_agent}' started step '{step.id}'",
                    agent=step.assigned_agent,
                )

                agent = self.agents.get(step.assigned_agent)
                context = AgentContext(
                    task_id=task.id,
                    run_id=run_id,
                    values={
                        "goal": task.goal,
                        "step_id": step.id,
                        "dependencies": step.dependencies,
                        "prior_results": {
                            key: value.model_dump(mode="json")
                            for key, value in state.results.items()
                        },
                    },
                )
                output = await agent.run(step.description, context)

                if not isinstance(output, AgentResult):
                    raise TypeError(
                        f"agent '{step.assigned_agent}' returned {type(output).__name__}; "
                        "task steps must return AgentResult"
                    )

                state.results[step.id] = output
                self._trace(
                    state,
                    TraceEventType.AGENT_COMPLETED,
                    f"Agent '{step.assigned_agent}' completed step '{step.id}'",
                    agent=step.assigned_agent,
                )

                if not output.success:
                    state.status = TaskStatus.FAILED
                    task.status = TaskStatus.FAILED
                    self._trace(
                        state,
                        TraceEventType.TASK_FAILED,
                        f"Step '{step.id}' failed",
                        agent=step.assigned_agent,
                    )
                    return self._result(state)

                completed.add(step.id)
                pending.pop(step.id)

        review = await self._review(task, state)
        state.review = review
        self._trace(
            state,
            TraceEventType.REVIEW_COMPLETED,
            "Final review completed",
            agent=self.reviewer_name,
        )

        if review.approved:
            state.status = TaskStatus.PASSED
            task.status = TaskStatus.PASSED
            self._trace(state, TraceEventType.TASK_COMPLETED, f"Task '{task.id}' completed")
        else:
            state.status = TaskStatus.FAILED
            task.status = TaskStatus.FAILED
            self._trace(
                state,
                TraceEventType.TASK_FAILED,
                f"Task '{task.id}' failed final review",
                agent=self.reviewer_name,
            )

        return self._result(state)

    async def _review(self, task: Task, state: ExecutionState) -> ReviewResult:
        reviewer = self.agents.get(self.reviewer_name)
        payload = {
            "goal": task.goal,
            "results": {
                key: value.model_dump(mode="json") for key, value in state.results.items()
            },
        }
        output = await reviewer.run(
            "Review the completed task results:\n" + json.dumps(payload, sort_keys=True),
            AgentContext(task_id=task.id, run_id=state.run_id),
        )
        if not isinstance(output, ReviewResult):
            raise TypeError(
                f"reviewer '{self.reviewer_name}' returned {type(output).__name__}; "
                "expected ReviewResult"
            )
        return output

    @staticmethod
    def _trace(
        state: ExecutionState,
        event_type: TraceEventType,
        message: str,
        *,
        agent: str | None = None,
    ) -> None:
        state.trace.add(TraceEvent(event_type=event_type, message=message, agent=agent))

    @staticmethod
    def _result(state: ExecutionState) -> OrchestrationResult:
        return OrchestrationResult(
            task_id=state.task_id,
            run_id=state.run_id,
            status=state.status,
            results=state.results,
            review=state.review,
            trace=state.trace,
        )
