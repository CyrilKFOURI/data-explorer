from types import SimpleNamespace
from typing import Any

import httpx2
import openai
import pytest
from openai.types.chat import ChatCompletionChunk

from app.modules.agent.engine.messages import Block, Message, user_text
from app.modules.agent.engine.provider import (
    Completed,
    ProviderError,
    Request,
    TextDelta,
    ToolSpec,
)
from app.modules.agent.providers.openai_compat import OpenAICompatProvider, to_api, translate
from app.modules.agent.providers.vendors import BY_ID, chat_models, detect, pick_default
from app.modules.agent.settings import SettingsStore


def chunk(**delta: Any) -> ChatCompletionChunk:
    finish = delta.pop("finish", None)
    usage = delta.pop("usage", None)
    return ChatCompletionChunk.model_validate(
        {
            "id": "c1",
            "object": "chat.completion.chunk",
            "created": 0,
            "model": "gemini-x-pro",
            "choices": [] if usage else [{"index": 0, "delta": delta, "finish_reason": finish}],
            **({"usage": usage} if usage else {}),
        }
    )


class FakeClient:
    def __init__(self, chunks: list[Any] | Exception) -> None:
        self.chunks, self.calls = chunks, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self.models = SimpleNamespace(
            list=lambda: [
                SimpleNamespace(id=i) for i in ("models/gemini-x-pro", "text-embedding-1")
            ]
        )

    def _create(self, **params: Any):
        self.calls.append(params)
        if isinstance(self.chunks, Exception):
            raise self.chunks
        return iter(self.chunks)


def provider(client: FakeClient) -> OpenAICompatProvider:
    return OpenAICompatProvider(
        "AIza-key", "https://x/v1", "Google Gemini", client_factory=lambda k, u: client
    )


def request() -> Request:
    return Request(
        model="gemini-x-pro",
        system="system",
        messages=[user_text("Why?")],
        tools=[ToolSpec("profile_column", "Profile.", {"type": "object"})],
    )


def test_streams_text_and_assembles_tool_calls() -> None:
    client = FakeClient(
        [
            chunk(role="assistant", content="Let me "),
            chunk(content="look."),
            chunk(
                tool_calls=[
                    {
                        "index": 0,
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "profile_column", "arguments": '{"col'},
                    }
                ]
            ),
            chunk(
                tool_calls=[{"index": 0, "function": {"arguments": 'umn": "Age"}'}}],
                finish="tool_calls",
            ),
            chunk(
                usage={
                    "prompt_tokens": 120,
                    "completion_tokens": 30,
                    "total_tokens": 150,
                    "prompt_tokens_details": {"cached_tokens": 100},
                }
            ),
        ]
    )

    events = list(provider(client).stream(request()))

    assert [e.text for e in events if isinstance(e, TextDelta)] == ["Let me ", "look."]
    done = events[-1]
    assert isinstance(done, Completed) and done.stop == "tool_use"
    call = done.message.blocks[1]
    assert (call.call_id, call.name, call.input) == ("call_1", "profile_column", {"column": "Age"})
    assert (done.usage.input_tokens, done.usage.cache_read_tokens, done.usage.output_tokens) == (
        20,
        100,
        30,
    )
    params = client.calls[0]
    assert params["messages"][0] == {"role": "system", "content": "system"}
    assert params["tools"][0]["function"]["name"] == "profile_column"
    assert params["stream_options"] == {"include_usage": True}


def test_history_is_translated_to_chat_messages() -> None:
    history = [
        user_text("Why?"),
        Message(
            "assistant",
            [
                Block("thinking", text="hidden"),  # Claude-only: not sent
                Block(
                    "tool_call", call_id="call_1", name="profile_column", input={"column": "Age"}
                ),
            ],
        ),
        Message("user", [Block("tool_result", text='{"mean": 29.7}', call_id="call_1")]),
    ]

    found = to_api("system", history)

    assert found[1] == {"role": "user", "content": "Why?"}
    assert found[2]["role"] == "assistant" and found[2]["content"] is None
    assert found[2]["tool_calls"][0]["function"] == {
        "name": "profile_column",
        "arguments": '{"column": "Age"}',
    }
    assert found[3] == {"role": "tool", "tool_call_id": "call_1", "content": '{"mean": 29.7}'}


def test_errors_and_missing_key() -> None:
    response = httpx2.Response(401, request=httpx2.Request("POST", "https://x"))
    error = openai.AuthenticationError("bad", response=response, body=None)
    assert translate(error, "Google Gemini").kind == "auth"
    with pytest.raises(ProviderError) as raised:
        list(provider(FakeClient(error)).stream(request()))
    assert "Google Gemini refused the API key" in raised.value.message
    with pytest.raises(ProviderError) as raised:
        list(OpenAICompatProvider("", None, "OpenAI").stream(request()))
    assert raised.value.kind == "no_key"


def test_models_are_listed_without_non_chat_ones() -> None:
    assert chat_models([m for m in provider(FakeClient([])).list_models()]) == ["gemini-x-pro"]


def test_keys_tell_their_vendor() -> None:
    assert detect("sk-ant-api03-xyz").id == "anthropic"  # type: ignore[union-attr]
    assert detect("AIzaSyABC").id == "gemini"  # type: ignore[union-attr]
    assert detect("sk-or-v1-abc").id == "openrouter"  # type: ignore[union-attr]
    assert detect("gsk_abc").id == "groq"  # type: ignore[union-attr]
    assert detect("sk-proj-abc").id == "openai"  # type: ignore[union-attr]
    assert detect("abc123") is None


def test_the_default_model_is_the_newest_of_the_preferred_family() -> None:
    gemini = BY_ID["gemini"]
    listed = ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-3.0-pro-preview", "gemini-2.5-flash"]
    assert pick_default(gemini, listed) == "gemini-2.5-pro"  # stable before previews
    assert pick_default(BY_ID["anthropic"], []) == "claude-opus-5-5"


def test_a_key_saved_under_the_wrong_vendor_is_moved(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("DATA_EXPLORER_GEMINI_API_KEY", raising=False)
    (tmp_path / "secrets.env").write_text(
        "ANTHROPIC_API_KEY=AIzaSyMisfiled1234\n", encoding="utf-8"
    )

    store = SettingsStore(tmp_path)

    assert store.key(BY_ID["gemini"]) == ("AIzaSyMisfiled1234", "file")
    assert store.key(BY_ID["anthropic"])[0] == ""
    assert store.vendor().id == "gemini"
