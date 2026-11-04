"""Plays the assistant's golden tasks against the running app (spec 026, R-AG-E1).

Uses the provider, key and model set in the assistant settings, so every run makes real, possibly
billed, API calls: it is run by hand, never in CI. Changes the assistant asks to make are
dismissed. Each case gets its own conversation, deleted afterwards.

    uv run python evals/agent_eval.py                      # app on http://127.0.0.1:8000
    uv run python evals/agent_eval.py --url http://127.0.0.1:8002 --only titanic-drivers
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RETRIES = 3
RATE_WAIT = 65


@dataclass
class Outcome:
    id: str
    passed: bool = False
    skipped: str | None = None
    tools: list[str] = field(default_factory=list)
    failed_steps: int = 0
    missing: list[str] = field(default_factory=list)  # patterns the answer lacks
    unverified: list[str] = field(default_factory=list)
    end: str = ""
    tokens: int = 0
    usd: float = 0.0
    seconds: float = 0.0
    answer: str = ""
    problems: list[str] = field(default_factory=list)


class App:
    def __init__(self, url: str) -> None:
        self.base = url.rstrip("/") + "/api/v1"

    def call(self, method: str, path: str, body: Any = None, timeout: float = 30) -> Any:
        request = urllib.request.Request(
            self.base + path,
            method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
        return json.loads(raw) if raw else None

    def stream(self, path: str, body: Any, timeout: float = 900) -> Any:
        request = urllib.request.Request(
            self.base + path,
            method="POST",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw in response:
                line = raw.decode("utf-8").strip()
                if line.startswith("data: "):
                    yield json.loads(line[6:])


def play(app: App, case: dict[str, Any], datasets: dict[str, str]) -> Outcome:
    outcome = Outcome(case["id"])
    dataset_id = next((i for name, i in datasets.items() if case["dataset"] in name), None)
    if dataset_id is None:
        outcome.skipped = f"no dataset named like {case['dataset']!r}"
        return outcome
    conversation = app.call("POST", f"/modules/agent/datasets/{dataset_id}/conversations")["id"]
    started = time.perf_counter()
    text = []
    try:
        for event in app.stream(
            f"/modules/agent/conversations/{conversation}/messages",
            {"text": case["question"], "filters": [], "page": None},
        ):
            kind = event["type"]
            if kind == "text":
                text.append(event["text"])
            elif kind == "step_started":
                outcome.tools.append(event["tool"])
            elif kind == "step_done" and not event["ok"]:
                outcome.failed_steps += 1
            elif kind == "confirm":  # the eval never changes the app
                app.call(
                    "POST",
                    f"/modules/agent/conversations/{conversation}/confirm/{event['id']}",
                    {"approved": False},
                )
            elif kind == "done":
                outcome.end = event["end"]
                outcome.tokens = event.get("conversation_tokens", 0)
                outcome.usd = event.get("conversation_usd", 0.0)
                outcome.unverified = event.get("unverified", [])
            elif kind == "error":
                outcome.end = "error"
                outcome.problems.append(f"{event['kind']}: {event['message']}")
    finally:
        outcome.seconds = round(time.perf_counter() - started, 1)
        app.call("DELETE", f"/modules/agent/conversations/{conversation}")
    outcome.answer = "".join(text)
    judge(case, outcome)
    return outcome


def judge(case: dict[str, Any], outcome: Outcome) -> None:
    if outcome.end != "answered":
        outcome.problems.append(f"ended with {outcome.end or 'nothing'}")
    if not set(case["tools"]) & set(outcome.tools):
        outcome.problems.append(f"none of {case['tools']} ran")
    outcome.missing = [p for p in case["mention"] if not re.search(p, outcome.answer, re.I)]
    if outcome.missing:
        outcome.problems.append(f"answer lacks {outcome.missing}")
    allowed = case.get("max_unverified", 1)
    if len(outcome.unverified) > allowed:
        outcome.problems.append(f"{len(outcome.unverified)} unmatched figures (max {allowed})")
    outcome.passed = not outcome.problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Plays the assistant's golden tasks.")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--only", nargs="*", help="case ids to play")
    parser.add_argument(
        "--pause", type=float, default=15, help="seconds between cases (free API tiers)"
    )
    parser.add_argument("--model", help="model to use for this run; the setting is restored")
    args = parser.parse_args()
    app = App(args.url)
    try:
        settings = app.call("GET", "/modules/agent/settings")
    except urllib.error.URLError as error:
        print(f"The app does not answer at {args.url}: {error}")
        return 2
    if not settings["ready"]:
        print("The assistant is not set up: add a key in its settings first.")
        return 2
    cases = json.loads((HERE / "agent_cases.json").read_text(encoding="utf-8"))["cases"]
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]
    datasets = {d["name"].lower(): d["id"] for d in app.call("GET", "/datasets")}
    model = args.model or settings["model"] or "default model"
    print(f"{len(cases)} cases with {settings['active_label']} ({model})\n")
    if args.model:
        app.call("PUT", "/modules/agent/settings", {"model": args.model})
    try:
        outcomes = run(app, cases, datasets, args.pause)
    finally:
        if args.model:
            app.call("PUT", "/modules/agent/settings", {"model": settings["model"]})
    return report(outcomes, settings, model)


def run(
    app: App, cases: list[dict[str, Any]], datasets: dict[str, str], pause: float
) -> list[Outcome]:
    outcomes: list[Outcome] = []
    for case in cases:
        outcome = play(app, case, datasets)
        for _ in range(RETRIES):  # a per-minute quota: wait it out, then play the case again
            limited = [p for p in outcome.problems if p.startswith("rate_limit")]
            if not limited:
                break
            if "today's quota" in limited[0]:  # a daily quota won't come back by waiting
                print(f"  stop  {limited[0]}", flush=True)
                return [*outcomes, outcome]
            print(f"  ...  {case['id']}: rate limit, waiting {RATE_WAIT} s", flush=True)
            time.sleep(RATE_WAIT)
            outcome = play(app, case, datasets)
        outcomes.append(outcome)
        if outcome.skipped:
            print(f"  skip  {outcome.id:<26} {outcome.skipped}", flush=True)
            continue
        mark = "PASS" if outcome.passed else "FAIL"
        detail = "; ".join(outcome.problems)
        print(
            f"  {mark} {outcome.id:<26} {outcome.seconds:>6.1f}s {outcome.tokens:>8,} tok {detail}",
            flush=True,
        )
        time.sleep(pause)
    return outcomes


def report(outcomes: list[Outcome], settings: dict[str, Any], model: str) -> int:
    played = [o for o in outcomes if not o.skipped]
    passed = sum(o.passed for o in played)
    tokens = sum(o.tokens for o in played)
    print(f"\n{passed}/{len(played)} passed · {tokens:,} tokens", end="")
    print(f" · ${sum(o.usd for o in played):.2f}" if settings["effort_supported"] else "")
    results = HERE / "results"
    results.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    found = {
        "provider": settings["active"],
        "model": model,
        "outcomes": [asdict(o) for o in outcomes],
    }
    path = results / f"agent-{stamp}.json"
    path.write_text(json.dumps(found, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Details: {path}")
    return 0 if passed == len(played) else 1


if __name__ == "__main__":
    sys.exit(main())
