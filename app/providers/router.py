from __future__ import annotations

from dataclasses import dataclass

from app.models.message import ModelRequest, ModelResponse
from app.providers.base import ModelClient


@dataclass(frozen=True, slots=True)
class BudgetPolicy:
    max_output_tokens: int | None = None
    max_total_tokens_per_call: int | None = None


class BudgetExceededError(RuntimeError):
    pass


class RoutingModelClient:
    """Routes model requests to provider adapters without changing agents."""

    name = "router"

    def __init__(
        self,
        default: ModelClient,
        routes: dict[str, ModelClient] | None = None,
        budget: BudgetPolicy | None = None,
    ) -> None:
        self.default = default
        self.routes = dict(routes or {})
        self.budget = budget or BudgetPolicy()

    def _client_for(self, model: str) -> ModelClient:
        for prefix, client in self.routes.items():
            if model.startswith(prefix):
                return client
        return self.default

    async def generate(self, request: ModelRequest) -> ModelResponse:
        effective = request
        if self.budget.max_output_tokens is not None:
            requested = request.max_output_tokens or self.budget.max_output_tokens
            effective = request.model_copy(
                update={"max_output_tokens": min(requested, self.budget.max_output_tokens)}
            )

        response = await self._client_for(request.model).generate(effective)
        if (
            self.budget.max_total_tokens_per_call is not None
            and response.usage.total_tokens > self.budget.max_total_tokens_per_call
        ):
            raise BudgetExceededError(
                f"model call used {response.usage.total_tokens} tokens; "
                f"limit is {self.budget.max_total_tokens_per_call}"
            )
        return response
