import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import default_samples_dir
from app.modules.agent.engine.provider import ProviderError
from app.modules.agent.engine.tools import ToolContext, ToolError
from tests.api.test_profiling import import_path
from tests.unit.agent.fakes import ScriptedProvider, answer, calls

BASE = "/api/v1/modules/agent"


@pytest.fixture(autouse=True)
def no_key_in_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATA_EXPLORER_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.fixture
def traps(client: TestClient) -> str:
    return import_path(client, default_samples_dir() / "typing_traps.csv")


def script(client: TestClient, *steps: Any) -> ScriptedProvider:
    provider = ScriptedProvider(list(steps))
    client.app.state.agent.provider_factory = lambda key: provider  # type: ignore[attr-defined]
    return provider


def events(response: Any) -> list[dict[str, Any]]:
    return [
        json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")
    ]


def conversation(client: TestClient, dataset_id: str) -> str:
    created = client.post(f"{BASE}/datasets/{dataset_id}/conversations")
    assert created.status_code == 201
    return created.json()["id"]


def test_settings_and_key_never_leave_the_backend(client: TestClient) -> None:
    settings = client.get(f"{BASE}/settings").json()
    assert settings["model"] == "claude-opus-5-5" and settings["key"]["configured"] is False

    saved = client.put(
        f"{BASE}/settings", json={"api_key": "sk-ant-test-1234abcd", "budget_usd": 2}
    ).json()

    assert saved["key"] == {"configured": True, "source": "file", "hint": "…abcd"}
    assert saved["budget_usd"] == 2
    assert "sk-ant-test-1234abcd" not in json.dumps(client.get(f"{BASE}/settings").json())
    removed = client.put(f"{BASE}/settings", json={"api_key": ""}).json()
    assert removed["key"]["configured"] is False
    assert client.put(f"{BASE}/settings", json={"model": "gpt-5"}).status_code == 400


def test_a_turn_runs_tools_streams_and_is_saved(client: TestClient, traps: str) -> None:
    provider = script(
        client,
        calls(("profile_column", {"column": "age"})),
        answer("Age is right-skewed."),
    )
    cid = conversation(client, traps)
    filters = [{"column": "country", "op": "in", "values": ["FR"]}]

    response = client.post(
        f"{BASE}/conversations/{cid}/messages",
        json={"text": "Describe age", "filters": filters, "page": "Overview"},
    )

    seen = events(response)
    kinds = [e["type"] for e in seen]
    assert kinds[0] == "spent" and "step_started" in kinds and "text" in kinds
    assert seen[-1]["type"] == "done" and seen[-1]["end"] == "answered"
    done = next(e for e in seen if e["type"] == "step_done")
    assert done["ok"] and done["link"]["page"] == "variable" and "age" in done["summary"]
    # the model saw the filters and the page, and the system prompt lists the columns
    first = provider.requests[0]
    assert "country is FR" in first.messages[-1].text and "Overview" in first.messages[-1].text
    assert "- age:" in first.system
    # saved: title, cost, transcript without the app context
    detail = client.get(f"{BASE}/conversations/{cid}").json()
    assert detail["conversation"]["title"] == "Describe age"
    assert detail["conversation"]["cost_usd"] > 0
    user, assistant = detail["messages"]
    assert user == {"role": "user", "text": "Describe age", "thinking": "", "steps": []}
    assert assistant["text"] == "Age is right-skewed."
    step = assistant["steps"][0]
    assert step["tool"] == "profile_column" and step["ok"] and step["label"] == "Profiling age"
    # the next turn replays the whole history
    script(client, answer("Sure."))
    client.post(f"{BASE}/conversations/{cid}/messages", json={"text": "And income?"})
    assert len(client.get(f"{BASE}/conversations/{cid}").json()["messages"]) == 4


def test_errors_end_the_stream_with_a_message(client: TestClient, traps: str) -> None:
    cid = conversation(client, traps)
    script(
        client,
        ProviderError("auth", "The API key was refused: check it in the assistant settings."),
    )

    seen = events(client.post(f"{BASE}/conversations/{cid}/messages", json={"text": "Hi"}))

    assert seen[-1] == {
        "type": "error",
        "kind": "auth",
        "message": "The API key was refused: check it in the assistant settings.",
    }
    # nothing was saved: the question can be asked again cleanly
    assert client.get(f"{BASE}/conversations/{cid}").json()["messages"] == []


def test_the_budget_is_enforced(client: TestClient, traps: str) -> None:
    client.put(f"{BASE}/settings", json={"budget_usd": 0.0001})
    script(client, calls(("list_columns", {})), answer("never reached"))
    cid = conversation(client, traps)

    first = events(client.post(f"{BASE}/conversations/{cid}/messages", json={"text": "Go"}))
    assert first[-1]["end"] == "budget"

    second = events(client.post(f"{BASE}/conversations/{cid}/messages", json={"text": "Again"}))
    assert second[-1]["type"] == "error" and second[-1]["kind"] == "budget"


def test_without_a_key_the_assistant_says_how_to_add_one(client: TestClient, traps: str) -> None:
    cid = conversation(client, traps)

    seen = events(client.post(f"{BASE}/conversations/{cid}/messages", json={"text": "Hi"}))

    assert seen[-1]["kind"] == "no_key" and "settings" in seen[-1]["message"]


def test_conversations_are_listed_and_deleted(client: TestClient, traps: str) -> None:
    cid = conversation(client, traps)
    listed = client.get(f"{BASE}/datasets/{traps}/conversations").json()
    assert [c["id"] for c in listed] == [cid]
    assert client.delete(f"{BASE}/conversations/{cid}").status_code == 204
    assert client.get(f"{BASE}/conversations/{cid}").status_code == 404


# --- tools against the real services --------------------------------------------------------


def run_tool(client: TestClient, dataset_id: str, name: str, args: dict[str, Any]):
    tool = client.app.state.agent.registry.get(name)  # type: ignore[attr-defined]
    return tool.run(ToolContext(dataset_id), tool.parse(args))


def test_tools_return_the_apps_own_figures(client: TestClient, traps: str) -> None:
    profile = run_tool(client, traps, "profile_column", {"column": "age"})
    reference = client.get(f"/api/v1/datasets/{traps}/variable", params={"column": "age"}).json()
    assert profile.content["mean"] == pytest.approx(
        reference["numeric"]["describe"]["mean"], rel=1e-3
    )
    assert profile.content["normality"]["tests"] and "outliers_iqr" in profile.content

    country = run_tool(client, traps, "profile_column", {"column": "country"})
    assert country.content["most_frequent"] and country.link.page == "variable"

    compared = run_tool(client, traps, "compare_columns", {"x": "country", "y": "income"})
    assert compared.content["kind"] == "groups" and compared.content["tests"]
    assert compared.link.params == {"x": "country", "y": "income"}

    ranked = run_tool(client, traps, "rank_associations_with", {"target": "income"})
    values = [abs(r["value"]) for r in ranked.content["ranked"]]
    assert values == sorted(values, reverse=True)

    counted = run_tool(
        client,
        traps,
        "count_rows",
        {"conditions": [{"column": "country", "op": "in", "values": ["FR"]}]},
    )
    assert 0 < counted.content["rows"] < counted.content["of_rows"] == 600

    overview = run_tool(client, traps, "get_dataset_overview", {})
    assert overview.content["rows"] == 600 and overview.content["alerts"]


def test_tool_errors_point_to_the_right_column(client: TestClient, traps: str) -> None:
    with pytest.raises(ToolError, match="did you mean 'age'"):
        run_tool(client, traps, "profile_column", {"column": "AGE"})
    with pytest.raises(ToolError, match="not found"):
        run_tool(client, traps, "compare_columns", {"x": "nope", "y": "age"})


def test_stop_ends_the_turn_after_the_current_step(client: TestClient, traps: str) -> None:
    import threading

    called, release = threading.Event(), threading.Event()

    class Waiting(ScriptedProvider):
        def stream(self, request):  # type: ignore[override]
            called.set()
            release.wait(timeout=5)  # the user presses Stop while the model "thinks"
            yield from super().stream(request)

    agent = client.app.state.agent  # type: ignore[attr-defined]
    provider = Waiting([calls(("list_columns", {})), answer("never reached")])
    agent.provider_factory = lambda key: provider
    agent.store.save_key("sk-ant-test-1234abcd")
    cid = conversation(client, traps)

    run = agent.send(cid, "List the columns", [])
    assert called.wait(timeout=5)
    assert agent.stop(cid) is True
    release.set()
    seen = [e for e in agent.events(run, heartbeat=0.5) if e is not None]

    assert seen[-1]["type"] == "done" and seen[-1]["end"] == "stopped"
    assert len(provider.requests) == 1  # no second model call after Stop
    assert not agent.running(cid)
