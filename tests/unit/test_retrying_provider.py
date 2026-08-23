import pytest

from app.models.message import Message, MessageRole, ModelRequest, ModelResponse
from app.providers.errors import ProviderError
from app.providers.retry import RetryPolicy, RetryingModelClient


class FlakyProvider:
    name = "flaky"

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    async def generate(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        if self.calls <= self.failures:
            raise ProviderError("temporary failure")
        return ModelResponse(provider=self.name, model=request.model, output_text="ok")


def request() -> ModelRequest:
    return ModelRequest(
        model="test-model",
        messages=[Message(role=MessageRole.USER, content="hello")],
    )


@pytest.mark.asyncio
async def test_retrying_client_recovers_from_transient_failure() -> None:
    provider = FlakyProvider(failures=2)
    client = RetryingModelClient(
        provider,
        RetryPolicy(max_attempts=3, base_delay_seconds=0, max_delay_seconds=0),
    )

    result = await client.generate(request())

    assert result.output_text == "ok"
    assert provider.calls == 3


@pytest.mark.asyncio
async def test_retrying_client_raises_after_attempt_limit() -> None:
    provider = FlakyProvider(failures=3)
    client = RetryingModelClient(
        provider,
        RetryPolicy(max_attempts=2, base_delay_seconds=0, max_delay_seconds=0),
    )

    with pytest.raises(ProviderError, match="temporary failure"):
        await client.generate(request())

    assert provider.calls == 2
