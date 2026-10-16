"""Command-line entry point for the conversational chatbot."""

from collections.abc import Callable

from dotenv import load_dotenv

from chatbot.cli import run_cli
from chatbot.config import Provider, Settings, parse_provider
from chatbot.conversation import Conversation
from chatbot.errors import ConfigError, ProviderError
from chatbot.providers import ProviderFactory

_PROVIDER_PROMPT = (
    "Choose a provider (google, openai, anthropic). Type 'quit' to exit: "
)


def prompt_for_provider(
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> Provider | None:
    """Ask until the user enters a Provider value or quits."""
    while True:
        try:
            raw = input_fn(_PROVIDER_PROMPT)
        except EOFError:
            output_fn("Goodbye!")
            return None
        if raw.strip().lower() == "quit":
            output_fn("Goodbye!")
            return None
        try:
            return parse_provider(raw)
        except ConfigError as exc:
            output_fn(str(exc))


def main(
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    load_dotenv()
    chosen = prompt_for_provider(input_fn, output_fn)
    if chosen is None:
        return
    try:
        settings = Settings.from_env(chosen)
        provider = ProviderFactory.create(settings)
    except ConfigError as exc:
        output_fn(str(exc))
        return
    try:
        run_cli(Conversation(), provider, input_fn=input_fn, output_fn=output_fn)
    except ProviderError as exc:
        output_fn(str(exc))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Goodbye!")
