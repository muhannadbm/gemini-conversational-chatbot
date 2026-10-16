"""Anthropic Claude adapter. Uses the Messages API."""

from collections.abc import Sequence
from typing import Any

from anthropic import Anthropic

from chatbot.config import Settings
from chatbot.errors import ProviderError
from chatbot.messages import Message
from chatbot.providers.base import (
    ChatProvider,
    require_user_turn,
    validate_sampling,
)


def to_anthropic_messages(messages: Sequence[Message]) -> list[dict[str, str]]:
    """Translate app turns into Messages API turns."""
    return [{"role": message.role, "content": message.content} for message in messages]


def assistant_text(message: Any) -> str:
    """Join the text blocks on a Messages API response."""
    parts: list[str] = []
    for block in message.content:
        if block.type == "text":
            parts.append(block.text)
    return "".join(parts)


class AnthropicChatProvider(ChatProvider):
    """Claude replies through `client.messages.create`."""

    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        super().__init__(settings)
        validate_sampling(
            settings,
            temperature_range=(0.0, 1.0),
            top_p_range=(0.0, 1.0),
        )
        self._client = client if client is not None else Anthropic(api_key=settings.api_key)

    def complete(self, messages: Sequence[Message]) -> str:
        require_user_turn(messages)
        # SDK 1.15 dropped temperature and top_p from the typed method.
        # extra_body still adds them to the JSON the Messages API accepts.
        kwargs: dict[str, Any] = {
            "model": self._settings.model,
            "max_tokens": self._settings.max_tokens,
            "messages": to_anthropic_messages(messages),
        }
        extra_body: dict[str, float] = {}
        if self._settings.temperature is not None:
            extra_body["temperature"] = self._settings.temperature
        if self._settings.top_p is not None:
            extra_body["top_p"] = self._settings.top_p
        if extra_body:
            kwargs["extra_body"] = extra_body
        try:
            message = self._client.messages.create(**kwargs)
        except Exception as exc:
            raise ProviderError(str(exc)) from exc
        return assistant_text(message)
