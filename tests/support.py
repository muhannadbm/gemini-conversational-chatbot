"""Shared fixtures for the stdlib test suite."""

from chatbot.config import Provider, Settings


def make_settings(
    *,
    provider: Provider | str = Provider.GOOGLE,
    model: str = "gemini-flash-lite-latest",
    api_key: str = "test-key",
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int = 4096,
) -> Settings:
    """A valid Settings object."""
    return Settings(
        provider=provider if isinstance(provider, Provider) else Provider(provider),
        model=model,
        api_key=api_key,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )
