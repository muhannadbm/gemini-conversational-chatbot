"""Failures the rest of the app is allowed to see."""


class ConfigError(Exception):
    """Environment configuration is missing or invalid."""


class ProviderError(Exception):
    """A model provider failed while producing a reply."""
