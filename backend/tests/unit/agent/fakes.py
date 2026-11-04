"""A scripted provider and toy tools: the loop is tested without network or SDK."""

import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, ClassVar

from pydantic import BaseModel

from app.modules.agent.engine.messages import Block, Message
from app.modules.agent.engine.provider import (
    Completed,
    ProviderError,
    ProviderEvent,
    Request,
    StopReason,
    TextDelta,
    Usage,
)
from app.modules.agent.engine.tools import AppLink, Tool, ToolContext, ToolError, ToolOutput


def answer(text: str, stop: StopReason = "end_turn", tokens: int = 100) -> Completed:
    return Completed(
        Message("assistant", [Block("text", text=text)]), stop, Usage("claude-opus-5-5", tokens, 10)
    )


def calls(*items: tuple[str, dict[str, Any]], stop: StopReason = "tool_use") -> Completed:
    blocks = [
        Block("tool_call", call_id=f"c{i}", name=name, input=args)
        for i, (name, args) in enumerate(items)
    ]
    return Completed(Message("assistant", blocks), stop, Usage("claude-opus-5-5", 100, 10))


@dataclass
class ScriptedProvider:
    """Plays one scripted response per call; records the requests it received."""

    script: list[Completed | ProviderError]
    id: str = "scripted"
    requests: list[Request] = field(default_factory=list)

    def stream(self, request: Request) -> Iterator[ProviderEvent]:
        self.requests.append(request)
        if not self.script:
            raise AssertionError("The provider was called more times than scripted")
        step = self.script.pop(0)
        if isinstance(step, ProviderError):
            raise step
        if step.message.text:
            yield TextDelta(step.message.text)
        yield step


class ColumnInput(BaseModel):
    column: str


class Echo(Tool[ColumnInput]):
    name: ClassVar[str] = "echo_column"
    description: ClassVar[str] = "Echo a column name."
    Input: ClassVar[type[BaseModel]] = ColumnInput

    def __init__(self) -> None:
        self.threads: set[int] = set()
        self.barrier: threading.Barrier | None = None

    def run(self, ctx: ToolContext, args: ColumnInput) -> ToolOutput:
        self.threads.add(threading.get_ident())
        if self.barrier is not None:
            self.barrier.wait(timeout=5)  # proves two calls run at the same time
        if args.column == "missing":
            raise ToolError("Column 'missing' not found. Columns: a, b.")
        if args.column == "big":
            return ToolOutput("big", "x" * 20_000)
        return ToolOutput(
            f"Echoed {args.column}",
            {"column": args.column, "dataset": ctx.dataset_id},
            AppLink("variable", {"column": args.column}, f"Open {args.column}"),
        )


class Empty(BaseModel):
    pass


class Delete(Tool[Empty]):
    name: ClassVar[str] = "delete_dataset"
    description: ClassVar[str] = "Delete the dataset."
    kind = "write"
    Input: ClassVar[type[BaseModel]] = Empty

    def __init__(self) -> None:
        self.ran = False

    def run(self, ctx: ToolContext, args: Empty) -> ToolOutput:
        self.ran = True
        return ToolOutput("Deleted", "deleted")
