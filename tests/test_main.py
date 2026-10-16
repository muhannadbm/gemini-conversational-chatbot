"""Startup provider prompt."""

import unittest
from unittest.mock import patch

from chatbot.config import Provider
from chatbot.errors import ConfigError, ProviderError
from main import main, prompt_for_provider


class ProviderPromptTests(unittest.TestCase):
    def test_retries_until_the_name_is_valid(self) -> None:
        lines = iter(["nope", " OpenAI "])
        outputs: list[str] = []

        chosen = prompt_for_provider(
            input_fn=lambda prompt: next(lines),
            output_fn=outputs.append,
        )

        self.assertEqual(chosen, Provider.OPENAI)
        self.assertEqual(len(outputs), 1)
        self.assertIn("nope", outputs[0])
        self.assertIn("google", outputs[0])
        self.assertIn("openai", outputs[0])
        self.assertIn("anthropic", outputs[0])

    def test_quit_leaves_without_a_provider(self) -> None:
        outputs: list[str] = []
        chosen = prompt_for_provider(
            input_fn=lambda prompt: " quit ",
            output_fn=outputs.append,
        )
        self.assertIsNone(chosen)
        self.assertEqual(outputs, ["Goodbye!"])

    def test_blank_input_is_reported(self) -> None:
        lines = iter([" ", "google"])
        outputs: list[str] = []
        chosen = prompt_for_provider(
            input_fn=lambda prompt: next(lines),
            output_fn=outputs.append,
        )
        self.assertEqual(chosen, Provider.GOOGLE)
        self.assertIn("required", outputs[0].lower())


class MainErrorTests(unittest.TestCase):
    def test_config_error_is_printed(self) -> None:
        outputs: list[str] = []
        with patch("main.Settings.from_env", side_effect=ConfigError("OPENAI_API_KEY is not set.")):
            main(input_fn=lambda prompt: "openai", output_fn=outputs.append)
        self.assertIn("OPENAI_API_KEY is not set.", outputs)

    def test_provider_error_is_printed(self) -> None:
        outputs: list[str] = []
        with (
            patch("main.Settings.from_env"),
            patch("main.ProviderFactory.create"),
            patch("main.run_cli", side_effect=ProviderError("model down")),
        ):
            main(input_fn=lambda prompt: "google", output_fn=outputs.append)
        self.assertIn("model down", outputs)


if __name__ == "__main__":
    unittest.main()
