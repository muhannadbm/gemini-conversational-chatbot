"""Select a registered chat provider from settings."""

from typing import ClassVar

from chatbot.config import Provider, Settings
from chatbot.errors import ConfigError
from chatbot.providers.base import ChatProvider


class ProviderFactory:
    """Build the adapter named by settings. The class itself has no vendor branches."""

    _registry: ClassVar[dict[str, type[ChatProvider]]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: type[ChatProvider]) -> None:
        """Make `name` resolve to `provider_cls`."""
        cls._registry[name] = provider_cls

    @classmethod
    def create(cls, settings: Settings) -> ChatProvider:
        """Return a new adapter for `settings.provider`."""
        try:
            provider_cls = cls._registry[settings.provider]
        except KeyError as exc:
            name = _provider_name(settings.provider)
            known = ", ".join(sorted(_provider_name(key) for key in cls._registry))
            raise ConfigError(
                f"Unknown provider {name!r}. Expected one of: {known}."
            ) from exc
        return provider_cls(settings)


def _provider_name(name: str) -> str:
    return name.value if isinstance(name, Provider) else name
