"""Provider-neutral conversation turns."""

from dataclasses import dataclass
from typing import Literal

Role = Literal["user", "assistant"]


@dataclass(frozen=True, slots=True)
class Message:
    """One turn in the session history."""

    role: Role
    content: str
