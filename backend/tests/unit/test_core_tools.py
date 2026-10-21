from dataclasses import dataclass

import pytest

from app.core.tools import ToolContext, ToolError, compact, wait_for


@dataclass
class Job:
    status: str
    step: int


def test_compact_rounds_cuts_and_summarises() -> None:
    @dataclass
    class Result:
        name: str
        score: float
        series: list[float]
        rows: list[dict]
        empty: list
        missing: None = None

    found = compact(
        Result("x", 0.123456789, [float(i) for i in range(100)], [{"a": i} for i in range(30)], [])
    )

    assert found["score"] == 0.1235
    assert found["series"] == {"values": 100, "first": 0.0, "last": 99.0, "min": 0.0, "max": 99.0}
    assert len(found["rows"]) == 21 and found["rows"][-1] == "… 10 more"
    assert "empty" not in found and "missing" not in found
    assert compact(float("nan")) is None


def test_wait_for_relays_progress_and_returns_the_finished_job() -> None:
    states = iter([Job("running", 1), Job("running", 2), Job("done", 3)])
    seen: list[tuple[str, float | None]] = []
    ctx = ToolContext("d1", progress=lambda message, share: seen.append((message, share)))

    job = wait_for(
        lambda: next(states),
        lambda j: j.status == "done",
        ctx,
        describe=lambda j: (f"step {j.step}", j.step / 3),
        interval=0,
    )

    assert job.step == 3 and [m for m, _ in seen] == ["step 1", "step 2"]


def test_wait_for_cancels_on_stop_and_on_timeout() -> None:
    cancelled: list[str] = []
    running = ToolContext("d1", cancelled=lambda: True)
    with pytest.raises(ToolError, match="Stopped"):
        wait_for(
            lambda: Job("running", 0),
            lambda j: False,
            running,
            cancel=lambda: cancelled.append("stop"),
            interval=0,
        )

    with pytest.raises(ToolError, match="Still running"):
        wait_for(
            lambda: Job("running", 0),
            lambda j: False,
            ToolContext("d1"),
            cancel=lambda: cancelled.append("timeout"),
            timeout=0,
            interval=0,
        )
    assert cancelled == ["stop", "timeout"]
