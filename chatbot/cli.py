"""Terminal prompt loop."""

from collections.abc import Callable

from chatbot.conversation import Conversation
from chatbot.providers.base import ChatProvider

_PROMPT = "I am your AI Assistant. How can I help you today? (type 'quit' to exit) "


def run_cli(
    conversation: Conversation,
    provider: ChatProvider,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    """Read user lines, print replies, and exit on quit."""
    while True:
        user_input = input_fn(_PROMPT)
        if user_input.strip().lower() == "quit":
            output_fn("Goodbye!")
            break
        conversation.add_user(user_input)
        response = conversation.reply(provider)
        output_fn("--------------------------------")
        output_fn(response)
