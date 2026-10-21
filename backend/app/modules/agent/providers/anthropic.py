"""Claude through the official Anthropic SDK (extra `[agent]`).

- Streamed responses; thinking is adaptive with readable summaries, effort set explicitly.
- Prompt caching: top-level `cache_control` caches the whole stable prefix (tools, system,
  history) from one turn to the next.
- Server-side fallback (`fallbacks: "default"`) on Opus 5.5 and Sonnet 5.5: a request a safety
  classifier declines is re-run on the model Anthropic recommends, inside the same call.
- Assistant blocks are kept as the API returned them and replayed unchanged (thinking blocks are
  only valid in the conversation that produced them, so the history stays append-only).
- Tool inputs stream as generated (`eager_input_streaming`); the loop validates every input
  against the tool's Pydantic model before running it.
- SDK errors become `ProviderError`s with a sentence the user can act on."""

from collections.abc import Callable, Iterator
from typing import Any

from app.modules.agent.engine.messages import Block, Message, Native
from app.modules.agent.engine.provider import (
    Completed,
    ProviderError,
    ProviderEvent,
    Request,
    StopReason,
    TextDelta,
    ThinkingDelta,
    ToolSpec,
    Usage,
)

PROVIDER = "anthropic"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
WITH_FALLBACK = ("claude-opus-5-5", "claude-sonnet-5-5")  # Haiku 5.5 has no server-side fallback
JSON_RETRIES = 2  # an eagerly streamed tool input that can't be parsed: re-issue the request
STOPS: dict[str, StopReason] = {
    "end_turn": "end_turn",
    "tool_use": "tool_use",
    "max_tokens": "max_tokens",
    "refusal": "refusal",
    "pause_turn": "pause_turn",
}


def sdk_installed() -> bool:
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


class AnthropicProvider:
    id = PROVIDER

    def __init__(self, api_key: str, client_factory: Callable[[str], Any] | None = None) -> None:
        self._api_key = api_key
        self._factory = client_factory or _client
        self._client: Any = None

    def stream(self, request: Request) -> Iterator[ProviderEvent]:
        if not self._api_key:
            raise ProviderError(
                "no_key", "No Anthropic API key: add one in the assistant settings."
            )
        if self._client is None:
            self._client = self._factory(self._api_key)
        params = build_params(request)
        for attempt in range(JSON_RETRIES + 1):
            try:
                yield from self._stream_once(params)
                return
            except ValueError:
                if attempt == JSON_RETRIES:
                    raise ProviderError(
                        "other", "The model sent tool arguments that could not be read."
                    ) from None
            except ProviderError:
                raise
            except Exception as error:
                raise translate(error) from error

    def _stream_once(self, params: dict[str, Any]) -> Iterator[ProviderEvent]:
        with self._client.beta.messages.stream(**params) as stream:
            for event in stream:
                if getattr(event, "type", None) != "content_block_delta":
                    continue
                delta = event.delta
                if delta.type == "text_delta" and delta.text:
                    yield TextDelta(delta.text)
                elif delta.type == "thinking_delta" and delta.thinking:
                    yield ThinkingDelta(delta.thinking)
            final = stream.get_final_message()
        yield completed(final)


def _client(api_key: str) -> Any:
    try:
        import anthropic
    except ImportError as error:
        raise ProviderError(
            "not_installed",
            "The assistant needs the Anthropic SDK: run `uv sync --extra agent` in backend/.",
        ) from error
    return anthropic.Anthropic(api_key=api_key, max_retries=3)


# --- request ----------------------------------------------------------------------------------


def build_params(request: Request) -> dict[str, Any]:
    params: dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_tokens,
        "system": request.system,
        "messages": [to_api(m) for m in request.messages if m.blocks],
        "tools": [tool_param(t) for t in request.tools],
        "thinking": {"type": "adaptive", "display": "summarized"},
        "output_config": {"effort": request.effort},
        "cache_control": {"type": "ephemeral"},
    }
    if request.model in WITH_FALLBACK:
        params["fallbacks"] = "default"
        params["betas"] = [FALLBACK_BETA]
    return params


def tool_param(tool: ToolSpec) -> dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.schema,
        "eager_input_streaming": True,
    }


def to_api(message: Message) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    for block in message.blocks:
        native = block.native.block if block.native and block.native.provider == PROVIDER else None
        if block.kind == "tool_result":
            content.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.call_id,
                    "content": block.text,
                    "is_error": block.is_error,
                }
            )
        elif native is not None:
            content.append(native)  # replayed exactly as the API returned it
        elif block.kind == "text" and block.text:
            content.append({"type": "text", "text": block.text})
        elif block.kind == "tool_call":
            content.append(
                {
                    "type": "tool_use",
                    "id": block.call_id,
                    "name": block.name,
                    "input": block.input or {},
                }
            )
        # thinking or native blocks from another provider can't be replayed here: dropped
    return {"role": message.role, "content": content}


# --- response ---------------------------------------------------------------------------------


def completed(message: Any) -> Completed:
    blocks: list[Block] = []
    for raw in message.content:
        native = Native(PROVIDER, raw.model_dump(mode="json", exclude_none=True))
        kind = raw.type
        if kind == "text":
            blocks.append(Block("text", text=raw.text, native=native))
        elif kind in ("thinking", "redacted_thinking"):
            blocks.append(Block("thinking", text=getattr(raw, "thinking", "") or "", native=native))
        elif kind == "tool_use":
            blocks.append(
                Block(
                    "tool_call",
                    call_id=raw.id,
                    name=raw.name,
                    input=raw.input if isinstance(raw.input, dict) else {},
                    native=native,
                )
            )
        else:  # fallback markers and anything newer: kept for the replay
            blocks.append(Block("native", native=native))
    usage = message.usage
    stop = STOPS.get(message.stop_reason or "", "other")
    details = getattr(message, "stop_details", None)
    return Completed(
        Message("assistant", blocks),
        stop,
        Usage(
            model=message.model,
            input_tokens=usage.input_tokens or 0,
            output_tokens=usage.output_tokens or 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        ),
        detail=getattr(details, "category", None) if details else None,
    )


def translate(error: Exception) -> ProviderError:
    """The SDK's typed errors, most specific first (R-AG-B4)."""
    try:
        import anthropic
    except ImportError:
        return ProviderError("other", str(error))
    if isinstance(error, anthropic.AuthenticationError | anthropic.PermissionDeniedError):
        return ProviderError("auth", "The API key was refused: check it in the assistant settings.")
    if isinstance(error, anthropic.RateLimitError):
        return ProviderError("rate_limit", "Rate limit reached: wait a minute and try again.")
    if isinstance(
        error,
        anthropic.OverloadedError
        | anthropic.ServiceUnavailableError
        | anthropic.InternalServerError,
    ):
        return ProviderError("overloaded", "The model is overloaded right now: try again shortly.")
    if isinstance(error, anthropic.NotFoundError):
        return ProviderError("bad_request", "This model is not available for your API key.")
    if isinstance(error, anthropic.BadRequestError):
        return ProviderError("bad_request", f"The request was rejected: {error.message}")
    if isinstance(error, anthropic.APIConnectionError):  # includes timeouts
        return ProviderError(
            "network", "Can't reach the Anthropic API: the assistant needs internet."
        )
    if isinstance(error, anthropic.APIStatusError):
        return ProviderError("other", f"Anthropic API error {error.status_code}: {error.message}")
    return ProviderError("other", str(error) or type(error).__name__)
