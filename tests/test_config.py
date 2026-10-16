"""Settings loaded from an environment mapping."""

import os
import unittest
from unittest.mock import patch

from chatbot.config import Provider, Settings, parse_provider
from chatbot.errors import ConfigError


class SettingsTests(unittest.TestCase):
    def test_google_settings_and_fallback_key(self) -> None:
        settings = Settings.from_env(
            Provider.GOOGLE,
            {
                "GEN_AI_MODEL": "gemini-flash-lite-latest",
                "GEN_AI_API_KEY": "fallback-key",
            },
        )

        self.assertEqual(settings.provider, Provider.GOOGLE)
        self.assertEqual(settings.model, "gemini-flash-lite-latest")
        self.assertEqual(settings.api_key, "fallback-key")
        self.assertIsNone(settings.temperature)
        self.assertIsNone(settings.top_p)
        self.assertEqual(settings.max_tokens, 4096)

    def test_provider_specific_key_wins(self) -> None:
        settings = Settings.from_env(
            Provider.OPENAI,
            {
                "GEN_AI_MODEL": "gpt-5.2",
                "OPENAI_API_KEY": "openai-key",
                "GEN_AI_API_KEY": "fallback-key",
                "GEN_AI_TEMPERATURE": "0.2",
                "GEN_AI_TOP_P": "0.9",
                "GEN_AI_MAX_TOKENS": "128",
            },
        )

        self.assertEqual(settings.provider, Provider.OPENAI)
        self.assertEqual(settings.api_key, "openai-key")
        self.assertEqual(settings.temperature, 0.2)
        self.assertEqual(settings.top_p, 0.9)
        self.assertEqual(settings.max_tokens, 128)

    def test_anthropic_key_falls_back(self) -> None:
        settings = Settings.from_env(
            Provider.ANTHROPIC,
            {
                "GEN_AI_PROVIDER": "google",
                "GEN_AI_MODEL": "claude-opus-5-5",
                "GEN_AI_API_KEY": "shared-key",
            },
        )

        self.assertEqual(settings.api_key, "shared-key")
        self.assertEqual(settings.provider, Provider.ANTHROPIC)

    def test_missing_model(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            Settings.from_env(Provider.GOOGLE, {"GEN_AI_API_KEY": "key"})
        self.assertIn("GEN_AI_MODEL", str(caught.exception))

    def test_missing_key_names_the_provider_variable(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            Settings.from_env(Provider.GOOGLE, {"GEN_AI_MODEL": "gemini"})
        self.assertIn("GOOGLE_API_KEY", str(caught.exception))
        self.assertIn("GEN_AI_API_KEY", str(caught.exception))

    def test_unknown_provider_is_rejected(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            parse_provider("groq")
        message = str(caught.exception)
        self.assertIn("groq", message)
        self.assertIn("google", message)
        self.assertIn("openai", message)
        self.assertIn("anthropic", message)

    def test_blank_provider_is_rejected(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            parse_provider("   ")
        self.assertIn("google", str(caught.exception))

    def test_parse_provider_ignores_case_and_space(self) -> None:
        self.assertEqual(parse_provider(" OpenAI "), Provider.OPENAI)

    def test_non_numeric_sampling_values(self) -> None:
        base = {"GEN_AI_MODEL": "gemini", "GEN_AI_API_KEY": "key"}
        with self.assertRaises(ConfigError):
            Settings.from_env(Provider.GOOGLE, {**base, "GEN_AI_TEMPERATURE": "warm"})
        with self.assertRaises(ConfigError):
            Settings.from_env(Provider.GOOGLE, {**base, "GEN_AI_TOP_P": "high"})
        with self.assertRaises(ConfigError):
            Settings.from_env(Provider.GOOGLE, {**base, "GEN_AI_MAX_TOKENS": "1.5"})
        with self.assertRaises(ConfigError):
            Settings.from_env(Provider.GOOGLE, {**base, "GEN_AI_MAX_TOKENS": "0"})

    def test_from_env_reads_the_process_environment(self) -> None:
        with patch.dict(
            os.environ,
            {"GEN_AI_MODEL": "gemini-flash-lite-latest", "GEN_AI_API_KEY": "from-process"},
            clear=True,
        ):
            settings = Settings.from_env(Provider.GOOGLE)
        self.assertEqual(settings.api_key, "from-process")
        self.assertEqual(settings.provider, Provider.GOOGLE)


if __name__ == "__main__":
    unittest.main()
