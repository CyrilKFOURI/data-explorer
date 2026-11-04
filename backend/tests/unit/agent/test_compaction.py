from app.modules.agent.engine.compaction import EARLIER, compact
from app.modules.agent.engine.messages import Block, Message, user_text

LONG = '{"rows": 891, "columns": [' + ", ".join(f'"c{i}"' for i in range(200)) + "]}"


def turn(question: str, call_id: str) -> list[Message]:
    return [
        user_text(question),
        Message("assistant", [Block("tool_call", call_id=call_id, name="get_dataset_overview")]),
        Message(
            "user",
            [
                Block(
                    "tool_result",
                    text=LONG,
                    call_id=call_id,
                    name="get_dataset_overview",
                    meta={"summary": "891 rows, 12 columns"},
                )
            ],
        ),
        Message("assistant", [Block("text", text="It has 891 rows.")]),
    ]


def test_results_before_the_last_two_questions_shrink_to_their_summary() -> None:
    history = [*turn("First?", "a"), *turn("Second?", "b"), *turn("Third?", "c")]

    found = compact(history)

    first, second, third = (found[i].blocks[0] for i in (2, 6, 10))
    assert first.text == f"{EARLIER}891 rows, 12 columns" and first.call_id == "a"
    assert second.text == LONG and third.text == LONG
    assert history[2].blocks[0].text == LONG  # the stored history is untouched
    assert [m.role for m in found] == [m.role for m in history]


def test_short_histories_and_short_results_are_kept() -> None:
    history = [*turn("First?", "a"), *turn("Second?", "b")]
    assert compact(history) == history

    small = turn("Zero?", "z")
    small[2].blocks[0].text = '{"rows": 891}'
    assert compact([*small, *history])[2].blocks[0].text == '{"rows": 891}'


def test_the_loop_sends_the_compacted_history() -> None:
    from app.modules.agent.engine.budget import Budget
    from app.modules.agent.engine.loop import Turn
    from app.modules.agent.engine.tools import ToolContext, ToolRegistry
    from tests.unit.agent.fakes import ScriptedProvider, answer

    provider = ScriptedProvider([answer("Fine.")])
    history = [*turn("First?", "a"), *turn("Second?", "b"), user_text("Third?")]
    Turn(
        provider=provider,
        registry=ToolRegistry([]),
        context=ToolContext("d1", [], lambda: False),
        model="claude-opus-5-5",
        system="s",
        history=history,
        budget=Budget(1.0),
    ).run()

    sent = provider.requests[0].messages
    assert sent[2].blocks[0].text.startswith(EARLIER) and sent[6].blocks[0].text == LONG
