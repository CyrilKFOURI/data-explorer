"""What the agent needs from an LLM provider: one streamed completion with tools.

Providers live in `modules/agent/providers/`; the loop only knows this interface, so a scripted
provider drives every test and another vendor plugs in without touching the loop."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from app.modules.agent.engine.messages import Message

StopReason = Literal["end_turn", "tool_use", "max_tokens", "refusal", "pause_turn", "other"]
ErrorKind = Literal[
    "not_installed", "no_key", "auth", "rate_limit", "overloaded", "network", "bad_request", "other"
]
Effort = Literal["low", "medium", "high", "xhigh", "max"]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    schema: dict[str, Any]


@dataclass
class Request:
    model: str
    system: str
    messages: list[Message]
    tools: list[ToolSpec] = field(default_factory=list)
    effort: Effort = "high"
    max_tokens: int = 32_000


@dataclass
class Usage:
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
        )


@dataclass
class TextDelta:
    text: str


@dataclass
class ThinkingDelta:
    text: str  # a summary of the model's reasoning (never the raw chain of thought)


@dataclass
class Completed:
    message: Message  # the assistant turn, every block included
    stop: StopReason
    usage: Usage
    detail: str | None = None  # refusal category, etc.


ProviderEvent = TextDelta | ThinkingDelta | Completed


class ProviderError(Exception):
    """A failure the user can act on, with a sentence that says how."""

    def __init__(self, kind: ErrorKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


class Provider(Protocol):
    id: str

    def stream(self, request: Request) -> Iterator[ProviderEvent]:
        """Text and thinking deltas as they come, then exactly one `Completed`.
        Raises `ProviderError`."""
        ...
