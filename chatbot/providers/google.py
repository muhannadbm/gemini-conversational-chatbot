"""Google Gemini adapter."""

from collections.abc import Sequence
from typing import Any

from google import genai
from google.genai import types

from chatbot.config import Settings
from chatbot.errors import ProviderError
from chatbot.messages import Message
from chatbot.providers.base import (
    ChatProvider,
    generation_kwargs,
    require_user_turn,
    validate_sampling,
)


def to_gemini_history(messages: Sequence[Message]) -> list[dict[str, Any]]:
    """Translate app turns into Gemini chat history. Assistant becomes model."""
    history: list[dict[str, Any]] = []
    for turn in messages:
        role = "model" if turn.role == "assistant" else "user"
        history.append({"role": role, "parts": [{"text": turn.content}]})
    return history


class GoogleChatProvider(ChatProvider):
    """Gemini chats through the Google Gen AI SDK."""

    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        super().__init__(settings)
        validate_sampling(
            settings,
            temperature_range=(0.0, 2.0),
            top_p_range=(0.0, 1.0),
        )
        self._client = client if client is not None else genai.Client(api_key=settings.api_key)
        self._config = types.GenerateContentConfig(
            **generation_kwargs(settings, max_tokens_field="max_output_tokens")
        )

    def complete(self, messages: Sequence[Message]) -> str:
        require_user_turn(messages)
        try:
            chat = self._client.chats.create(
                model=self._settings.model,
                history=to_gemini_history(messages[:-1]),
                config=self._config,
            )
            response = chat.send_message(messages[-1].content)
        except Exception as exc:
            raise ProviderError(str(exc)) from exc
        return response.text or ""
