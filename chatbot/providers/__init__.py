"""Composition root. Importing this package registers the built-in providers."""

from chatbot.config import Provider
from chatbot.providers.anthropic import AnthropicChatProvider
from chatbot.providers.factory import ProviderFactory
from chatbot.providers.google import GoogleChatProvider
from chatbot.providers.openai import OpenAIChatProvider

ProviderFactory.register(Provider.GOOGLE, GoogleChatProvider)
ProviderFactory.register(Provider.OPENAI, OpenAIChatProvider)
ProviderFactory.register(Provider.ANTHROPIC, AnthropicChatProvider)

__all__ = [
    "AnthropicChatProvider",
    "GoogleChatProvider",
    "OpenAIChatProvider",
    "ProviderFactory",
]
