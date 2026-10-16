"""Session memory."""

import unittest

from chatbot.conversation import Conversation
from chatbot.messages import Message
from chatbot.providers.base import ChatProvider
from tests.support import make_settings


class RecordingProvider(ChatProvider):
    def __init__(self) -> None:
        super().__init__(make_settings())
        self.seen: list[tuple[Message, ...]] = []

    def complete(self, messages: tuple[Message, ...] | list[Message]) -> str:
        self.seen.append(tuple(messages))
        return "reply"


class ConversationTests(unittest.TestCase):
    def test_reply_stores_the_assistant_turn(self) -> None:
        conversation = Conversation()
        provider = RecordingProvider()
        conversation.add_user("hello")

        text = conversation.reply(provider)

        self.assertEqual(text, "reply")
        self.assertEqual(
            conversation.messages,
            (
                Message(role="user", content="hello"),
                Message(role="assistant", content="reply"),
            ),
        )
        self.assertEqual(provider.seen, [(Message(role="user", content="hello"),)])

    def test_messages_is_a_snapshot(self) -> None:
        conversation = Conversation()
        conversation.add_user("one")
        snapshot = conversation.messages
        conversation.add_user("two")

        self.assertEqual(snapshot, (Message(role="user", content="one"),))
        self.assertEqual(len(conversation.messages), 2)


if __name__ == "__main__":
    unittest.main()
