"""In-memory session history."""

from collections.abc import Sequence

from chatbot.messages import Message
from chatbot.providers.base import ChatProvider


class Conversation:
    """The turns kept for the current process. Nothing is written to disk."""

    def __init__(self) -> None:
        self._messages: list[Message] = []

    @property
    def messages(self) -> Sequence[Message]:
        """A snapshot of the turns stored so far."""
        return tuple(self._messages)

    def add_user(self, content: str) -> None:
        """Append a user turn."""
        self._messages.append(Message(role="user", content=content))

    def add_assistant(self, content: str) -> None:
        """Append an assistant turn."""
        self._messages.append(Message(role="assistant", content=content))

    def reply(self, provider: ChatProvider) -> str:
        """Ask the provider for the next reply and store it."""
        text = provider.complete(self.messages)
        self.add_assistant(text)
        return text
