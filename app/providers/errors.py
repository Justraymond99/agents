class ProviderError(RuntimeError):
    """Base exception for model provider failures."""


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider is not registered."""


class ProviderResponseError(ProviderError):
    """Raised when a provider returns an unusable response."""
