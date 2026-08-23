from __future__ import annotations

import json
from uuid import uuid4

from app.agents import AgentContext, AgentRegistry, PlannerAgent
from app.models.result import AgentResult, ReviewResult
from app.models.task import Task, TaskStatus, TaskStep
from app.models.trace import RunTrace, TraceEvent, TraceEventType
from app.orchestration.retry import RevisionPolicy
from app.orchestration.scheduler import DagScheduler
from app.orchestration.state import ExecutionState, OrchestrationResult


class StepExecutionError(RuntimeError):
    def __init__(self, step: TaskStep) -> None:
        super().__init__(f"step '{step.id}' failed")
        self.step = step


class Orchestrator:
    """ATLAS orchestrator with DAG execution and bounded reviewer-driven revision."""

    def __init__(
        self,
        *,
        planner: PlannerAgent,
        agents: AgentRegistry,
        reviewer_name: str = "reviewer",
        revision_policy: RevisionPolicy | None = None,
        scheduler: DagScheduler | None = None,
    ) -> None:
        self.planner = planner
        self.agents = agents
        self.reviewer_name = reviewer_name
        self.revision_policy = revision_policy or RevisionPolicy()
        self.scheduler = scheduler or DagScheduler()

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

        if not await self._execute_plan(task, state):
            return self._result(state)

        while True:
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
                return self._result(state)

            if not self.revision_policy.can_retry(state.revision_attempts):
                state.status = TaskStatus.FAILED
                task.status = TaskStatus.FAILED
                self._trace(
                    state,
                    TraceEventType.TASK_FAILED,
                    f"Task '{task.id}' failed final review after revision limit",
                    agent=self.reviewer_name,
                )
                return self._result(state)

            revision_steps = self._revision_steps(state)
            if not revision_steps:
                state.status = TaskStatus.FAILED
                task.status = TaskStatus.FAILED
                self._trace(
                    state,
                    TraceEventType.TASK_FAILED,
                    "Review rejected the task but no configured revisable step exists",
                    agent=self.reviewer_name,
                )
                return self._result(state)

            state.revision_attempts += 1
            self._trace(
                state,
                TraceEventType.REVISION_REQUESTED,
                f"Revision attempt {state.revision_attempts} requested",
                agent=self.reviewer_name,
            )

            if not await self._execute_revisions(task, state, review, revision_steps):
                return self._result(state)

    async def _execute_plan(self, task: Task, state: ExecutionState) -> bool:
        assert state.plan is not None

        async def runner(step: TaskStep) -> None:
            output = await self._run_step(task, state, step)
            if not output.success:
                raise StepExecutionError(step)

        try:
            await self.scheduler.run(state.plan, runner)
        except StepExecutionError as exc:
            return self._fail(
                task,
                state,
                f"Step '{exc.step.id}' failed",
                agent=exc.step.assigned_agent,
            )
        except RuntimeError as exc:
            return self._fail(task, state, str(exc))
        return True

    async def _run_step(
        self,
        task: Task,
        state: ExecutionState,
        step: TaskStep,
        *,
        extra_context: dict[str, object] | None = None,
        instruction: str | None = None,
    ) -> AgentResult:
        self._trace(
            state,
            TraceEventType.AGENT_STARTED,
            f"Agent '{step.assigned_agent}' started step '{step.id}'",
            agent=step.assigned_agent,
        )

        agent = self.agents.get(step.assigned_agent)
        values: dict[str, object] = {
            "goal": task.goal,
            "step_id": step.id,
            "dependencies": step.dependencies,
            "prior_results": {
                key: value.model_dump(mode="json") for key, value in state.results.items()
            },
        }
        if extra_context:
            values.update(extra_context)

        output = await agent.run(
            instruction or step.description,
            AgentContext(task_id=task.id, run_id=state.run_id, values=values),
        )

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
        return output

    def _revision_steps(self, state: ExecutionState) -> list[TaskStep]:
        assert state.plan is not None
        return [
            step
            for step in state.plan.steps
            if self.revision_policy.is_revisable(step.assigned_agent)
        ]

    async def _execute_revisions(
        self,
        task: Task,
        state: ExecutionState,
        review: ReviewResult,
        steps: list[TaskStep],
    ) -> bool:
        feedback = review.model_dump(mode="json")

        for step in steps:
            previous_result = state.results.get(step.id)
            instruction = (
                "Revise the prior work for this step in response to reviewer feedback.\n\n"
                f"Original step: {step.description}\n\n"
                f"Reviewer feedback: {json.dumps(feedback, sort_keys=True)}"
            )
            output = await self._run_step(
                task,
                state,
                step,
                instruction=instruction,
                extra_context={
                    "revision_attempt": state.revision_attempts,
                    "review_feedback": feedback,
                    "previous_result": (
                        previous_result.model_dump(mode="json")
                        if previous_result is not None
                        else None
                    ),
                },
            )
            if not output.success:
                return self._fail(
                    task,
                    state,
                    f"Revision of step '{step.id}' failed",
                    agent=step.assigned_agent,
                )

        return True

    async def _review(self, task: Task, state: ExecutionState) -> ReviewResult:
        reviewer = self.agents.get(self.reviewer_name)
        payload = {
            "goal": task.goal,
            "revision_attempts": state.revision_attempts,
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

    def _fail(
        self,
        task: Task,
        state: ExecutionState,
        message: str,
        *,
        agent: str | None = None,
    ) -> bool:
        state.status = TaskStatus.FAILED
        task.status = TaskStatus.FAILED
        self._trace(state, TraceEventType.TASK_FAILED, message, agent=agent)
        return False

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
            revision_attempts=state.revision_attempts,
            trace=state.trace,
        )
