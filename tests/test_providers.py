"""Adapter payload mapping and sampling, with fake SDK clients."""

import unittest
from types import SimpleNamespace

from chatbot.errors import ConfigError, ProviderError
from chatbot.messages import Message
from chatbot.providers.anthropic import AnthropicChatProvider, assistant_text, to_anthropic_messages
from chatbot.providers.google import GoogleChatProvider, to_gemini_history
from chatbot.providers.openai import OpenAIChatProvider, to_openai_input
from tests.support import make_settings


def _turns() -> list[Message]:
    return [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi"),
        Message(role="user", content="Again"),
    ]


class GoogleAdapterTests(unittest.TestCase):
    def test_history_uses_model_for_the_assistant(self) -> None:
        history = to_gemini_history(_turns()[:-1])
        self.assertEqual(
            history,
            [
                {"role": "user", "parts": [{"text": "Hello"}]},
                {"role": "model", "parts": [{"text": "Hi"}]},
            ],
        )

    def test_complete_sends_prior_history_and_sampling(self) -> None:
        client = _FakeGoogle(text="done")
        provider = GoogleChatProvider(
            make_settings(temperature=0.4, top_p=0.8, max_tokens=128),
            client=client,
        )

        self.assertEqual(provider.complete(_turns()), "done")
        self.assertEqual(client.chats.kwargs["model"], "gemini-flash-lite-latest")
        self.assertEqual(client.chats.kwargs["history"], to_gemini_history(_turns()[:-1]))
        self.assertEqual(client.chats.kwargs["config"].max_output_tokens, 128)
        self.assertEqual(client.chats.kwargs["config"].temperature, 0.4)
        self.assertEqual(client.chats.kwargs["config"].top_p, 0.8)
        self.assertEqual(client.chats.chat.sent, "Again")

    def test_omits_unset_sampling_fields(self) -> None:
        provider = GoogleChatProvider(make_settings(), client=_FakeGoogle(text=""))
        self.assertEqual(provider._config.max_output_tokens, 4096)
        self.assertIsNone(provider._config.temperature)
        self.assertIsNone(provider._config.top_p)

    def test_empty_model_text(self) -> None:
        provider = GoogleChatProvider(make_settings(), client=_FakeGoogle(text=None))
        self.assertEqual(provider.complete([Message(role="user", content="Hi")]), "")

    def test_temperature_above_two_is_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            GoogleChatProvider(make_settings(temperature=2.5), client=_FakeGoogle(text=""))

    def test_sdk_errors_are_wrapped(self) -> None:
        provider = GoogleChatProvider(make_settings(), client=_FakeGoogle(error=RuntimeError("boom")))
        with self.assertRaises(ProviderError) as caught:
            provider.complete([Message(role="user", content="Hi")])
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)


class OpenAIAdapterTests(unittest.TestCase):
    def test_input_keeps_user_and_assistant_roles(self) -> None:
        self.assertEqual(
            to_openai_input(_turns()),
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
                {"role": "user", "content": "Again"},
            ],
        )

    def test_complete_uses_responses_and_sampling(self) -> None:
        client = _FakeOpenAI(text="done")
        provider = OpenAIChatProvider(
            make_settings(provider="openai", model="gpt-5.2", temperature=0.0, max_tokens=64),
            client=client,
        )

        self.assertEqual(provider.complete(_turns()), "done")
        self.assertEqual(client.responses.kwargs["model"], "gpt-5.2")
        self.assertEqual(client.responses.kwargs["input"], to_openai_input(_turns()))
        self.assertIs(client.responses.kwargs["store"], False)
        self.assertEqual(client.responses.kwargs["max_output_tokens"], 64)
        self.assertEqual(client.responses.kwargs["temperature"], 0.0)
        self.assertNotIn("top_p", client.responses.kwargs)

    def test_empty_output_text(self) -> None:
        provider = OpenAIChatProvider(make_settings(), client=_FakeOpenAI(text=None))
        self.assertEqual(provider.complete([Message(role="user", content="Hi")]), "")

    def test_top_p_above_one_is_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            OpenAIChatProvider(make_settings(top_p=1.1), client=_FakeOpenAI(text=""))

    def test_sdk_errors_are_wrapped(self) -> None:
        provider = OpenAIChatProvider(make_settings(), client=_FakeOpenAI(error=RuntimeError("down")))
        with self.assertRaises(ProviderError) as caught:
            provider.complete([Message(role="user", content="Hi")])
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)


class AnthropicAdapterTests(unittest.TestCase):
    def test_messages_keep_user_and_assistant_roles(self) -> None:
        self.assertEqual(
            to_anthropic_messages(_turns()),
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
                {"role": "user", "content": "Again"},
            ],
        )

    def test_text_blocks_are_joined(self) -> None:
        message = SimpleNamespace(
            content=[
                SimpleNamespace(type="text", text="Hello "),
                SimpleNamespace(type="tool_use", text="ignored"),
                SimpleNamespace(type="text", text="there"),
            ]
        )
        self.assertEqual(assistant_text(message), "Hello there")

    def test_complete_uses_messages_and_sampling(self) -> None:
        client = _FakeAnthropic(
            [SimpleNamespace(type="text", text="done")],
        )
        provider = AnthropicChatProvider(
            make_settings(
                provider="anthropic",
                model="claude-opus-5-5",
                temperature=1.0,
                top_p=0.99,
                max_tokens=256,
            ),
            client=client,
        )

        self.assertEqual(provider.complete(_turns()), "done")
        self.assertEqual(client.messages.kwargs["model"], "claude-opus-5-5")
        self.assertEqual(client.messages.kwargs["messages"], to_anthropic_messages(_turns()))
        self.assertEqual(client.messages.kwargs["max_tokens"], 256)
        self.assertEqual(
            client.messages.kwargs["extra_body"],
            {"temperature": 1.0, "top_p": 0.99},
        )
        self.assertNotIn("temperature", client.messages.kwargs)
        self.assertNotIn("top_p", client.messages.kwargs)

    def test_omits_extra_body_when_sampling_is_unset(self) -> None:
        client = _FakeAnthropic([SimpleNamespace(type="text", text="done")])
        provider = AnthropicChatProvider(make_settings(), client=client)
        provider.complete([Message(role="user", content="Hi")])
        self.assertNotIn("extra_body", client.messages.kwargs)

    def test_temperature_above_one_is_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            AnthropicChatProvider(make_settings(temperature=1.5), client=_FakeAnthropic([]))

    def test_latest_turn_must_be_the_user(self) -> None:
        provider = AnthropicChatProvider(make_settings(), client=_FakeAnthropic([]))
        with self.assertRaises(ProviderError):
            provider.complete([Message(role="assistant", content="Hi")])

    def test_sdk_errors_are_wrapped(self) -> None:
        provider = AnthropicChatProvider(
            make_settings(),
            client=_FakeAnthropic([], error=RuntimeError("down")),
        )
        with self.assertRaises(ProviderError) as caught:
            provider.complete([Message(role="user", content="Hi")])
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)


class _FakeGoogleChat:
    def __init__(self, text: str | None, error: Exception | None) -> None:
        self._text = text
        self._error = error
        self.sent: str | None = None

    def send_message(self, message: str) -> SimpleNamespace:
        if self._error is not None:
            raise self._error
        self.sent = message
        return SimpleNamespace(text=self._text)


class _FakeGoogleChats:
    def __init__(self, text: str | None, error: Exception | None) -> None:
        self.chat = _FakeGoogleChat(text, error)
        self.kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> _FakeGoogleChat:
        self.kwargs = kwargs
        return self.chat


class _FakeGoogle:
    def __init__(self, text: str | None = "ok", error: Exception | None = None) -> None:
        self.chats = _FakeGoogleChats(text, error)


class _FakeResponses:
    def __init__(self, text: str | None, error: Exception | None) -> None:
        self._text = text
        self._error = error
        self.kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.kwargs = kwargs
        if self._error is not None:
            raise self._error
        return SimpleNamespace(output_text=self._text)


class _FakeOpenAI:
    def __init__(self, text: str | None = "ok", error: Exception | None = None) -> None:
        self.responses = _FakeResponses(text, error)


class _FakeMessages:
    def __init__(self, blocks: list[object], error: Exception | None) -> None:
        self._blocks = blocks
        self._error = error
        self.kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.kwargs = kwargs
        if self._error is not None:
            raise self._error
        return SimpleNamespace(content=self._blocks)


class _FakeAnthropic:
    def __init__(self, blocks: list[object], error: Exception | None = None) -> None:
        self.messages = _FakeMessages(blocks, error)


if __name__ == "__main__":
    unittest.main()
