"""Provider selection."""

import unittest

from chatbot.config import Provider
from chatbot.errors import ConfigError
from chatbot.providers.base import ChatProvider
from chatbot.providers.factory import ProviderFactory
from tests.support import make_settings


class DummyProvider(ChatProvider):
    def complete(self, messages: object) -> str:
        return "dummy"


class FactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        import chatbot.providers as providers

        self.assertIs(providers.ProviderFactory, ProviderFactory)
        self._original = dict(ProviderFactory._registry)

    def tearDown(self) -> None:
        ProviderFactory._registry.clear()
        ProviderFactory._registry.update(self._original)

    def test_builtin_providers_are_registered(self) -> None:
        self.assertEqual(
            set(ProviderFactory._registry),
            {"google", "openai", "anthropic"},
        )

    def test_create_returns_the_registered_class(self) -> None:
        ProviderFactory.register(Provider.GOOGLE, DummyProvider)
        provider = ProviderFactory.create(make_settings())
        self.assertIsInstance(provider, DummyProvider)

    def test_missing_registration_lists_registered_names(self) -> None:
        del ProviderFactory._registry[Provider.GOOGLE]
        with self.assertRaises(ConfigError) as caught:
            ProviderFactory.create(make_settings())
        message = str(caught.exception)
        self.assertIn("google", message)
        self.assertIn("anthropic", message)
        self.assertIn("openai", message)


if __name__ == "__main__":
    unittest.main()
