"""The chat contract every vendor adapter implements."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from chatbot.config import Settings
from chatbot.errors import ConfigError, ProviderError
from chatbot.messages import Message


class ChatProvider(ABC):
    """A stateless model client. The app owns the conversation history."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @abstractmethod
    def complete(self, messages: Sequence[Message]) -> str:
        """Return the assistant reply for the given conversation."""


def require_user_turn(messages: Sequence[Message]) -> None:
    """Reject a history that cannot be sent as the next user turn."""
    if not messages:
        raise ProviderError("The conversation has no messages.")
    if messages[-1].role != "user":
        raise ProviderError("The latest message must be from the user.")


def generation_kwargs(
    settings: Settings,
    *,
    max_tokens_field: str,
) -> dict[str, float | int]:
    """Sampling fields to send. Unset temperature and top_p are left out."""
    kwargs: dict[str, float | int] = {max_tokens_field: settings.max_tokens}
    if settings.temperature is not None:
        kwargs["temperature"] = settings.temperature
    if settings.top_p is not None:
        kwargs["top_p"] = settings.top_p
    return kwargs


def validate_sampling(
    settings: Settings,
    *,
    temperature_range: tuple[float, float],
    top_p_range: tuple[float, float],
) -> None:
    """Raise ConfigError when a set sampling value is outside the vendor range."""
    _check_range("GEN_AI_TEMPERATURE", settings.temperature, temperature_range)
    _check_range("GEN_AI_TOP_P", settings.top_p, top_p_range)


def _check_range(
    name: str,
    value: float | None,
    bounds: tuple[float, float],
) -> None:
    if value is None:
        return
    low, high = bounds
    if not low <= value <= high:
        raise ConfigError(f"{name} must be between {low} and {high}.")
