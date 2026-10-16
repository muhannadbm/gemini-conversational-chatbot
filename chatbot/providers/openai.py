"""OpenAI adapter. Uses the Responses API."""

from collections.abc import Sequence
from typing import Any

from openai import OpenAI

from chatbot.config import Settings
from chatbot.errors import ProviderError
from chatbot.messages import Message
from chatbot.providers.base import (
    ChatProvider,
    generation_kwargs,
    require_user_turn,
    validate_sampling,
)


def to_openai_input(messages: Sequence[Message]) -> list[dict[str, str]]:
    """Translate app turns into Responses API input items."""
    return [{"role": message.role, "content": message.content} for message in messages]


class OpenAIChatProvider(ChatProvider):
    """OpenAI text generation through `client.responses.create`."""

    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        super().__init__(settings)
        validate_sampling(
            settings,
            temperature_range=(0.0, 2.0),
            top_p_range=(0.0, 1.0),
        )
        self._client = client if client is not None else OpenAI(api_key=settings.api_key)

    def complete(self, messages: Sequence[Message]) -> str:
        require_user_turn(messages)
        kwargs: dict[str, Any] = {
            "model": self._settings.model,
            "input": to_openai_input(messages),
            "store": False,
            **generation_kwargs(self._settings, max_tokens_field="max_output_tokens"),
        }
        try:
            response = self._client.responses.create(**kwargs)
        except Exception as exc:
            raise ProviderError(str(exc)) from exc
        return response.output_text or ""
