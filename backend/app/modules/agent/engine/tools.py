"""The agent's tool registry. The tool contract itself lives in `app.core.tools`, shared with the
modules that offer tools (re-exported here for the engine and the agent's own tools)."""

from collections.abc import Iterator
from typing import Any

from app.core.tools import (
    AppLink,
    Tool,
    ToolContext,
    ToolError,
    ToolKind,
    ToolOutput,
    compact,
    wait_for,
)
from app.modules.agent.engine.provider import ToolSpec

MAX_RESULT_CHARS = 8_000  # ≈ 2,000 tokens (R-AG-T2)

__all__ = [
    "MAX_RESULT_CHARS",
    "AppLink",
    "Tool",
    "ToolContext",
    "ToolError",
    "ToolKind",
    "ToolOutput",
    "ToolRegistry",
    "compact",
    "spec_of",
    "wait_for",
]


def spec_of(tool: Tool[Any]) -> ToolSpec:
    return ToolSpec(tool.name, tool.description, _clean_schema(tool.Input.model_json_schema()))


def _clean_schema(schema: Any) -> Any:
    """Pydantic's JSON schema without the titles (noise for the model)."""
    if isinstance(schema, dict):
        return {k: _clean_schema(v) for k, v in schema.items() if k != "title"}
    if isinstance(schema, list):
        return [_clean_schema(v) for v in schema]
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
        return [spec_of(tool) for tool in self._tools.values()]

    def __len__(self) -> int:
        return len(self._tools)

    def __iter__(self) -> Iterator[Tool[Any]]:
        return iter(self._tools.values())
