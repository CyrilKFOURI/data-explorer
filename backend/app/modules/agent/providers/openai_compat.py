"""Any OpenAI-compatible chat API through the official OpenAI SDK (extra `[agent]`): OpenAI
itself, Google Gemini, Mistral, Groq, DeepSeek, OpenRouter, and local servers (Ollama, LM Studio).

The engine's messages are translated to chat-completions messages: assistant tool calls become
`tool_calls`, each tool result a `tool` message. Blocks only Claude understands (thinking) are not
sent. Responses stream; tool-call arguments arrive in pieces and are assembled, then parsed and
validated by the loop like any other tool input.

Some vendors attach data to a tool call that must come back with it (Gemini's thought
signatures, in `extra_content`). It is kept as the block's `native` part, tagged with the vendor,
and only ever replayed to that vendor."""

import json
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
    ToolSpec,
    Usage,
)

PROVIDER = "openai"
STOPS: dict[str, StopReason] = {
    "stop": "end_turn",
    "tool_calls": "tool_use",
    "function_call": "tool_use",
    "length": "max_tokens",
    "content_filter": "refusal",
}


class OpenAICompatProvider:
    id = PROVIDER

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        label: str = "the provider",
        client_factory: Callable[[str, str | None], Any] | None = None,
        needs_key: bool = True,
        tag: str = PROVIDER,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._label = label
        self._needs_key = needs_key
        self._tag = tag  # the vendor, for the data only it understands
        self._factory = client_factory or _client
        self._client: Any = None

    def _ready(self) -> Any:
        if self._needs_key and not self._api_key:
            raise ProviderError("no_key", f"No API key for {self._label}: add one in the settings.")
        if self._client is None:
            self._client = self._factory(self._api_key or "none", self._base_url)
        return self._client

    def stream(self, request: Request) -> Iterator[ProviderEvent]:
        client = self._ready()
        try:
            yield from self._stream(client, request)
        except ProviderError:
            raise
        except Exception as error:
            raise translate(error, self._label) from error

    def list_models(self) -> list[str]:
        client = self._ready()
        try:
            return [m.id for m in client.models.list()]
        except Exception as error:
            raise translate(error, self._label) from error

    def _stream(self, client: Any, request: Request) -> Iterator[ProviderEvent]:
        params: dict[str, Any] = {
            "model": request.model,
            "messages": to_api(request.system, request.messages, self._tag),
            "stream": True,
            "stream_options": {"include_usage": True},
            "max_tokens": min(request.max_tokens, 16_000),
        }
        if request.tools:
            params["tools"] = [tool_param(t) for t in request.tools]
        text: list[str] = []
        calls: dict[int, dict[str, Any]] = {}
        finish: str | None = None
        usage = Usage(request.model)
        for chunk in client.chat.completions.create(**params):
            if getattr(chunk, "usage", None):
                usage = _usage(chunk.usage, chunk.model or request.model)
            for choice in chunk.choices or []:
                delta = choice.delta
                if delta is not None and delta.content:
                    text.append(delta.content)
                    yield TextDelta(delta.content)
                for call in (delta.tool_calls or []) if delta is not None else []:
                    found = calls.setdefault(
                        _slot(calls, call), {"id": "", "name": "", "arguments": "", "extra": None}
                    )
                    if call.id:
                        found["id"] = call.id
                    if call.function is not None:
                        found["name"] += call.function.name or ""
                        found["arguments"] += call.function.arguments or ""
                    extra = (call.model_extra or {}).get("extra_content")
                    if extra:
                        found["extra"] = extra
                if choice.finish_reason:
                    finish = choice.finish_reason
        blocks: list[Block] = []
        if text:
            blocks.append(Block("text", text="".join(text)))
        for index in sorted(calls):
            call = calls[index]
            blocks.append(
                Block(
                    "tool_call",
                    call_id=call["id"] or f"call_{index}",
                    name=call["name"],
                    input=_arguments(call["arguments"]),
                    native=Native(self._tag, {"extra_content": call["extra"]})
                    if call["extra"]
                    else None,
                )
            )
        stop = STOPS.get(finish or "", "other")
        if calls and stop in ("end_turn", "other"):  # some APIs say "stop" after tool calls
            stop = "tool_use"
        yield Completed(Message("assistant", blocks), stop, usage)


def _slot(calls: dict[int, dict[str, Any]], call: Any) -> int:
    """Where a tool-call piece belongs. Most APIs number the calls; Gemini sends each one whole,
    without a number: a new id is then a new call, and a piece without id continues the last."""
    if call.index is not None:
        return call.index
    if call.id and not any(found["id"] == call.id for found in calls.values()):
        return len(calls)
    return next((i for i, found in calls.items() if found["id"] == call.id), max(calls, default=0))


def _client(api_key: str, base_url: str | None) -> Any:
    try:
        import openai
    except ImportError as error:
        raise ProviderError(
            "not_installed",
            "The assistant needs the OpenAI SDK: run `uv sync --extra agent` in backend/.",
        ) from error
    return openai.OpenAI(api_key=api_key, base_url=base_url, max_retries=3)


def tool_param(tool: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description, "parameters": tool.schema},
    }


def to_api(system: str, messages: list[Message], tag: str = PROVIDER) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for message in messages:
        if message.role == "assistant":
            text = "".join(b.text for b in message.blocks if b.kind == "text")
            calls = [_call(b, tag) for b in message.blocks if b.kind == "tool_call"]
            if not text and not calls:
                continue  # e.g. a Claude turn with only thinking blocks
            entry: dict[str, Any] = {"role": "assistant", "content": text or None}
            if calls:
                entry["tool_calls"] = calls
            found.append(entry)
            continue
        text = "".join(b.text for b in message.blocks if b.kind == "text")
        if text:
            found.append({"role": "user", "content": text})
        for block in message.blocks:
            if block.kind == "tool_result":
                content = ("Error: " if block.is_error else "") + block.text
                found.append({"role": "tool", "tool_call_id": block.call_id, "content": content})
    return found


def _call(block: Block, tag: str) -> dict[str, Any]:
    call: dict[str, Any] = {
        "id": block.call_id,
        "type": "function",
        "function": {"name": block.name, "arguments": json.dumps(block.input or {})},
    }
    if block.native is not None and block.native.provider == tag:
        call.update(block.native.block)  # e.g. Gemini's thought signature, sent back unchanged
    return call


def _arguments(raw: str) -> dict[str, Any]:
    """Tool arguments as a dict; anything unreadable is left for the loop to report."""
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except ValueError:
        return {"_unreadable_arguments": raw[:500]}
    return value if isinstance(value, dict) else {"_unreadable_arguments": raw[:500]}


def _usage(usage: Any, model: str) -> Usage:
    details = getattr(usage, "prompt_tokens_details", None)
    cached = (getattr(details, "cached_tokens", 0) or 0) if details else 0
    prompt = getattr(usage, "prompt_tokens", 0) or 0
    return Usage(
        model=model,
        input_tokens=max(prompt - cached, 0),
        output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        cache_read_tokens=cached,
    )


def translate(error: Exception, label: str) -> ProviderError:
    try:
        import openai
    except ImportError:
        return ProviderError("other", str(error))
    if isinstance(error, openai.AuthenticationError | openai.PermissionDeniedError):
        return ProviderError("auth", f"{label} refused the API key: check it in the settings.")
    if isinstance(error, openai.RateLimitError):
        return ProviderError(
            "rate_limit",
            f"{label}: rate limit or quota reached for this model; try again later or choose "
            "another model in the settings (free keys often have no quota for the largest ones).",
        )
    if isinstance(error, openai.NotFoundError):
        return ProviderError("bad_request", f"{label} does not offer this model to your key.")
    if isinstance(error, openai.BadRequestError | openai.UnprocessableEntityError):
        return ProviderError("bad_request", f"{label} rejected the request: {error.message}")
    if isinstance(error, openai.InternalServerError):
        return ProviderError(
            "overloaded", f"{label} is having trouble right now: try again shortly."
        )
    if isinstance(error, openai.APIConnectionError):  # includes timeouts
        return ProviderError("network", f"Can't reach {label}: check the internet connection.")
    if isinstance(error, openai.APIStatusError):
        return ProviderError("other", f"{label} error {error.status_code}: {error.message}")
    return ProviderError("other", str(error) or type(error).__name__)
