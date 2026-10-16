"""Load chatbot settings from the process environment."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from chatbot.errors import ConfigError


class Provider(str, Enum):
    """Vendors this app can call. The user types one of these values at startup."""

    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


_API_KEY_ENV = {
    Provider.GOOGLE: "GOOGLE_API_KEY",
    Provider.OPENAI: "OPENAI_API_KEY",
    Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
}
_DEFAULT_MAX_TOKENS = 4096


@dataclass(frozen=True, slots=True)
class Settings:
    """The values a provider needs for one process."""

    provider: Provider
    model: str
    api_key: str
    temperature: float | None
    top_p: float | None
    max_tokens: int

    @classmethod
    def from_env(
        cls,
        provider: Provider,
        environ: Mapping[str, str] | None = None,
    ) -> "Settings":
        """Read settings for `provider` from `environ`, or from `os.environ` when it is omitted."""
        env = os.environ if environ is None else environ
        model = _text(env, "GEN_AI_MODEL")
        if not model:
            raise ConfigError("GEN_AI_MODEL is not set in the environment.")
        return cls(
            provider=provider,
            model=model,
            api_key=_api_key(env, provider),
            temperature=_optional_float(env, "GEN_AI_TEMPERATURE"),
            top_p=_optional_float(env, "GEN_AI_TOP_P"),
            max_tokens=_max_tokens(env),
        )


def _text(env: Mapping[str, str], name: str) -> str:
    raw = env.get(name)
    if raw is None:
        return ""
    return str(raw).strip()


def parse_provider(name: str) -> Provider:
    """Return the provider named by user input.

    Raises ConfigError when the text is empty or not one of the enum values.
    """
    cleaned = name.strip().lower()
    known = ", ".join(member.value for member in Provider)
    if not cleaned:
        raise ConfigError(f"A provider is required. Expected one of: {known}.")
    try:
        return Provider(cleaned)
    except ValueError as exc:
        raise ConfigError(
            f"Unknown provider {cleaned!r}. Expected one of: {known}."
        ) from exc


def _api_key(env: Mapping[str, str], provider: Provider) -> str:
    specific_name = _API_KEY_ENV.get(provider)
    if specific_name:
        specific = _text(env, specific_name)
        if specific:
            return specific
    fallback = _text(env, "GEN_AI_API_KEY")
    if fallback:
        return fallback
    if specific_name:
        raise ConfigError(
            f"{specific_name} is not set in the environment. "
            "GEN_AI_API_KEY is also accepted as a fallback."
        )
    raise ConfigError("GEN_AI_API_KEY is not set in the environment.")


def _optional_float(env: Mapping[str, str], name: str) -> float | None:
    raw = _text(env, name)
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number.") from exc


def _max_tokens(env: Mapping[str, str]) -> int:
    raw = _text(env, "GEN_AI_MAX_TOKENS")
    if not raw:
        return _DEFAULT_MAX_TOKENS
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError("GEN_AI_MAX_TOKENS must be an integer.") from exc
    if value < 1:
        raise ConfigError("GEN_AI_MAX_TOKENS must be at least 1.")
    return value
