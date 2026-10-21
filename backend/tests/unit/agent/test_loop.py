import threading
from typing import Any

from app.modules.agent.engine.budget import Budget, cost
from app.modules.agent.engine.loop import MAX_FAILURES, Spent, StepDone, StepStarted, Turn
from app.modules.agent.engine.messages import Message, from_dict, to_dict, user_text
from app.modules.agent.engine.provider import ProviderError, TextDelta, Usage
from app.modules.agent.engine.tools import MAX_RESULT_CHARS, ToolContext, ToolRegistry
from tests.unit.agent.fakes import Delete, Echo, ScriptedProvider, answer, calls


def turn(script: list, *tools: Any, budget: float = 10.0, **options: Any) -> tuple[Turn, list]:
    events: list = []
    registry = ToolRegistry(list(tools) or [Echo()])
    played = Turn(
        provider=ScriptedProvider(script),
        registry=registry,
        context=ToolContext("d1"),
        model="claude-opus-5-5",
        system="You are a test.",
        history=[user_text("What drives survival?")],
        budget=Budget(budget),
        emit=events.append,
        **options,
    )
    return played, events


def test_an_answer_without_tools_ends_the_turn() -> None:
    played, events = turn([answer("Sex and class.")])

    result = played.run()

    assert result.end == "answered"
    assert [m.role for m in result.messages] == ["assistant"]
    assert result.messages[0].text == "Sex and class."
    assert any(isinstance(e, TextDelta) for e in events)
    spent = [e for e in events if isinstance(e, Spent)]
    assert spent and spent[-1].turn_usd == result.cost_usd > 0


def test_a_tool_runs_and_its_result_goes_back_to_the_model() -> None:
    played, events = turn([calls(("echo_column", {"column": "Age"})), answer("Done.")])

    result = played.run()

    assert result.end == "answered"
    assert [m.role for m in result.messages] == ["assistant", "user", "assistant"]
    tool_result = result.messages[1].blocks[0]
    assert tool_result.kind == "tool_result" and tool_result.call_id == "c0"
    assert '"column": "Age"' in tool_result.text and '"dataset": "d1"' in tool_result.text
    assert tool_result.meta and tool_result.meta["link"]["page"] == "variable"
    started = next(e for e in events if isinstance(e, StepStarted))
    done = next(e for e in events if isinstance(e, StepDone))
    assert (started.tool, done.ok, done.summary) == ("echo_column", True, "Echoed Age")
    # the second request carries the first answer and the tool result
    second = played.provider.requests[1]  # type: ignore[attr-defined]
    assert [m.role for m in second.messages] == ["user", "assistant", "user"]


def test_independent_read_tools_run_in_parallel() -> None:
    echo = Echo()
    echo.barrier = threading.Barrier(2)
    script = [
        calls(("echo_column", {"column": "a"}), ("echo_column", {"column": "b"})),
        answer("ok"),
    ]
    played, _ = turn(script, echo)

    result = played.run()

    assert result.end == "answered" and len(echo.threads) == 2
    assert len(result.messages[1].blocks) == 2  # both results in one message


def test_bad_arguments_and_unknown_tools_come_back_as_errors() -> None:
    script = [calls(("echo_column", {"col": "Age"}), ("nope", {})), answer("Sorry.")]
    played, _ = turn(script)

    result = played.run()

    first, second = result.messages[1].blocks
    assert first.is_error and "column" in first.text and "Field required" in first.text
    assert second.is_error and "Unknown tool 'nope'" in second.text and "echo_column" in second.text
    assert result.end == "answered"


def test_a_tool_error_teaches_the_model() -> None:
    played, _ = turn([calls(("echo_column", {"column": "missing"})), answer("Fixed.")])

    result = played.run()

    block = result.messages[1].blocks[0]
    assert block.is_error and "Columns: a, b" in block.text


def test_side_effects_are_denied_unless_the_gate_allows_them() -> None:
    delete = Delete()
    played, _ = turn([calls(("delete_dataset", {})), answer("Not allowed.")], delete)
    result = played.run()
    assert not delete.ran and result.messages[1].blocks[0].is_error

    delete = Delete()
    played, _ = turn(
        [calls(("delete_dataset", {})), answer("Done.")], delete, gate=lambda tool, call: "allow"
    )
    played.run()
    assert delete.ran


def test_the_step_limit_answers_every_pending_call() -> None:
    script = [calls(("echo_column", {"column": "a"})), calls(("echo_column", {"column": "b"}))]
    played, _ = turn(script, max_steps=1)

    result = played.run()

    assert result.end == "max_steps"
    last = result.messages[-1]
    assert last.role == "user" and last.blocks[0].is_error and "Step limit" in last.blocks[0].text


def test_the_budget_stops_the_turn() -> None:
    script = [calls(("echo_column", {"column": "a"}), stop="tool_use")]
    played, _ = turn(script, budget=0.000001)

    result = played.run()

    assert result.end == "budget"


def test_stop_refusal_truncation_and_provider_errors() -> None:
    played, _ = turn([answer("x")], should_stop=lambda: True)
    assert played.run().end == "stopped"

    played, _ = turn([answer("", stop="refusal")])
    assert played.run().end == "refused"

    played, _ = turn([calls(("echo_column", {"column": "a"}), stop="max_tokens")])
    result = played.run()
    assert result.end == "truncated" and result.messages[-1].blocks[0].is_error

    played, _ = turn([ProviderError("auth", "Invalid key: check the assistant settings.")])
    result = played.run()
    assert result.end == "error" and result.error and result.error.kind == "auth"


def test_repeated_failures_of_one_tool_end_the_turn() -> None:
    script = [calls(("echo_column", {"column": "missing"})) for _ in range(MAX_FAILURES)]
    played, _ = turn(script)

    assert played.run().end == "tool_failures"


def test_large_results_are_capped() -> None:
    played, _ = turn([calls(("echo_column", {"column": "big"})), answer("ok")])

    result = played.run()

    text = result.messages[1].blocks[0].text
    assert len(text) < MAX_RESULT_CHARS + 100 and text.endswith("narrower result]")


def test_messages_round_trip_and_costs() -> None:
    message = calls(("echo_column", {"column": "a"})).message
    assert from_dict(to_dict(message)) == message
    assert isinstance(from_dict(to_dict(user_text("hi"))), Message)

    usage = Usage("claude-opus-5-5", 1_000_000, 100_000, 1_000_000, 0)
    assert round(cost(usage), 4) == round(4.0 + 2.0 + 0.2, 4)
    assert cost(Usage("claude-haiku-5-5", 1_000_000)) == 0.10


def test_a_long_tool_reports_its_progress() -> None:
    from typing import ClassVar

    from pydantic import BaseModel

    from app.modules.agent.engine.loop import StepProgress
    from app.modules.agent.engine.tools import Tool, ToolOutput

    class Empty(BaseModel):
        pass

    class Slow(Tool[Empty]):
        name: ClassVar[str] = "slow"
        description: ClassVar[str] = "Slow."
        kind = "compute"
        Input: ClassVar[type[BaseModel]] = Empty

        def run(self, ctx, args):  # type: ignore[override]
            ctx.progress("Half way", 0.5)
            return ToolOutput("done", "done")

    played, events = turn([calls(("slow", {})), answer("ok")], Slow())

    played.run()

    progress = [e for e in events if isinstance(e, StepProgress)]
    assert [(p.call_id, p.message, p.share) for p in progress] == [("c0", "Half way", 0.5)]
