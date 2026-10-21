"""The contract every agent tool follows (spec 026, § 5.1).

A tool wraps one capability of the app: typed input (a Pydantic model, so the model's arguments are
validated before anything runs), a compact result for the model, a one-line summary and a link
that reopens the same analysis in the app. Its `kind` decides what the loop may do on its own."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ValidationError

from app.domain.filters.model import Condition
from app.modules.agent.engine.provider import ToolSpec

ToolKind = Literal["read", "compute", "write", "rows"]
# read: no effect · compute: may take long, no lasting effect · write: changes the app's state
# (always confirmed) · rows: reads raw rows (data sharing level applies)

MAX_RESULT_CHARS = 8_000  # ≈ 2,000 tokens (R-AG-T2)


@dataclass
class ToolContext:
    dataset_id: str
    conditions: list[Condition] = field(default_factory=list)  # the user's active filters
    cancelled: Callable[[], bool] = lambda: False


@dataclass(frozen=True)
class AppLink:
    """A page of the app in a given state (R-AG-T5), e.g. compare?x=Sex&y=Survived."""

    page: str
    params: dict[str, str] = field(default_factory=dict)
    label: str = ""


@dataclass
class ToolOutput:
    summary: str  # one line for the conversation: "Sex × Survived: χ², V = 0.54 (strong)"
    content: dict[str, Any] | str  # what the model reads
    link: AppLink | None = None


class ToolError(Exception):
    """A failure the model can fix on its next step: say what was wrong and what to do."""


class Tool[I: BaseModel](ABC):
    name: ClassVar[str]
    description: ClassVar[str]  # when to use it, and when not to
    kind: ClassVar[ToolKind] = "read"
    Input: ClassVar[type[BaseModel]]

    def label(self, args: I) -> str:
        """What the step shows while it runs: "Comparing Sex × Survived"."""
        return self.name.replace("_", " ").capitalize()

    @abstractmethod
    def run(self, ctx: ToolContext, args: I) -> ToolOutput: ...

    def parse(self, raw: dict[str, Any] | None) -> I:
        try:
            return self.Input.model_validate(raw or {})  # type: ignore[return-value]
        except ValidationError as error:
            problems = "; ".join(
                f"{'.'.join(str(p) for p in e['loc']) or 'input'}: {e['msg']}"
                for e in error.errors()
            )
            raise ToolError(f"Invalid arguments for {self.name}: {problems}.") from error

    def spec(self) -> ToolSpec:
        return ToolSpec(self.name, self.description, _clean_schema(self.Input.model_json_schema()))


def _clean_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Pydantic's JSON schema without the titles (noise for the model)."""
    if isinstance(schema, dict):
        return {k: _clean_schema(v) for k, v in schema.items() if k != "title"}
    if isinstance(schema, list):
        return [_clean_schema(v) for v in schema]  # type: ignore[return-value]
    return schema


class ToolRegistry:
    """The tools of one agent, in a fixed order (a stable tool list keeps the prompt cache)."""

    def __init__(self, tools: list[Tool[Any]] | None = None) -> None:
        self._tools: dict[str, Tool[Any]] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: Tool[Any]) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name!r} registered twice")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool[Any] | None:
        return self._tools.get(name)

    def specs(self) -> list[ToolSpec]:
        return [tool.spec() for tool in self._tools.values()]

    def __len__(self) -> int:
        return len(self._tools)

    def __iter__(self):
        return iter(self._tools.values())
