"""A conversation in the agent's own terms, independent of any provider.

Blocks a provider needs back unchanged (Anthropic thinking blocks, fallback markers…) keep their
original form in `native`; the history is append-only, so they are replayed byte for byte."""

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

BlockKind = Literal["text", "thinking", "tool_call", "tool_result", "native"]
Role = Literal["user", "assistant"]


@dataclass
class Native:
    """A provider-specific block, replayed as is to the provider that produced it."""

    provider: str
    block: dict[str, Any]


@dataclass
class Block:
    kind: BlockKind
    text: str = ""
    call_id: str | None = None  # tool_call / tool_result
    name: str | None = None  # tool_call: the tool
    input: dict[str, Any] | None = None  # tool_call: its arguments
    is_error: bool = False  # tool_result
    native: Native | None = None
    meta: dict[str, Any] | None = None  # app only (step summary, link, duration): never sent


@dataclass
class Message:
    role: Role
    blocks: list[Block] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "".join(b.text for b in self.blocks if b.kind == "text")

    @property
    def tool_calls(self) -> list[Block]:
        return [b for b in self.blocks if b.kind == "tool_call"]


def user_text(text: str) -> Message:
    return Message("user", [Block("text", text=text)])


def to_dict(message: Message) -> dict[str, Any]:
    return asdict(message)


def from_dict(data: dict[str, Any]) -> Message:
    blocks = []
    for raw in data.get("blocks", []):
        native = raw.get("native")
        blocks.append(
            Block(
                kind=raw["kind"],
                text=raw.get("text", ""),
                call_id=raw.get("call_id"),
                name=raw.get("name"),
                input=raw.get("input"),
                is_error=bool(raw.get("is_error", False)),
                native=Native(native["provider"], native["block"]) if native else None,
                meta=raw.get("meta"),
            )
        )
    return Message(data["role"], blocks)
