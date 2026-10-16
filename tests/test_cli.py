"""Terminal loop, with input and output injected."""

import unittest

from chatbot.cli import run_cli
from chatbot.conversation import Conversation
from chatbot.errors import ProviderError
from chatbot.messages import Message
from chatbot.providers.base import ChatProvider
from tests.support import make_settings


class StubProvider(ChatProvider):
    def __init__(self, reply: str = "Attention is a weighted mix.") -> None:
        super().__init__(make_settings())
        self.reply = reply

    def complete(self, messages: object) -> str:
        return self.reply


class ExplodingProvider(ChatProvider):
    def __init__(self) -> None:
        super().__init__(make_settings())

    def complete(self, messages: object) -> str:
        raise ProviderError("model down")


class CliTests(unittest.TestCase):
    def test_quit_ignores_case_and_space(self) -> None:
        outputs: list[str] = []

        run_cli(
            Conversation(),
            StubProvider(),
            input_fn=lambda prompt: " Quit ",
            output_fn=outputs.append,
        )

        self.assertEqual(outputs, ["Goodbye!"])

    def test_one_reply_then_quit(self) -> None:
        conversation = Conversation()
        outputs: list[str] = []
        lines = iter(["Explain attention.", "quit"])

        run_cli(
            conversation,
            StubProvider(),
            input_fn=lambda prompt: next(lines),
            output_fn=outputs.append,
        )

        self.assertEqual(
            outputs,
            ["--------------------------------", "Attention is a weighted mix.", "Goodbye!"],
        )
        self.assertEqual(
            conversation.messages,
            (
                Message(role="user", content="Explain attention."),
                Message(role="assistant", content="Attention is a weighted mix."),
            ),
        )

    def test_provider_errors_stop_the_loop(self) -> None:
        conversation = Conversation()
        with self.assertRaises(ProviderError):
            run_cli(
                conversation,
                ExplodingProvider(),
                input_fn=lambda prompt: "hello",
                output_fn=lambda line: None,
            )
        self.assertEqual(conversation.messages, (Message(role="user", content="hello"),))


if __name__ == "__main__":
    unittest.main()
