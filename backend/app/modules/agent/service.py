"""The agent behind the API: settings, conversations, and turns played in a background thread whose
events stream to the browser (spec 026, § 4)."""

import queue
import re
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from app.core.errors import AppError
from app.domain.filters.model import Condition
from app.domain.report.build import describe_condition
from app.modules.agent.engine.budget import Budget
from app.modules.agent.engine.loop import (
    Notice,
    Spent,
    StepDone,
    StepStarted,
    Turn,
    TurnEvent,
    TurnResult,
)
from app.modules.agent.engine.messages import Message, user_text
from app.modules.agent.engine.prompt import ColumnBrief, system_prompt, turn_context
from app.modules.agent.engine.provider import (
    Completed,
    Provider,
    ProviderError,
    Request,
    TextDelta,
    ThinkingDelta,
)
from app.modules.agent.engine.tools import ToolContext, ToolRegistry
from app.modules.agent.repository import Conversation, ConversationRepository
from app.modules.agent.settings import EFFORTS, MODELS, AgentSettings, KeyStatus, SettingsStore
from app.modules.agent.tools import AppServices

CONTEXT = re.compile(r"^<app_context>.*?</app_context>\s*", re.DOTALL)
NEW_TITLE = "New conversation"
TITLE_CHARS = 60
END = object()  # closes an event stream
BUDGET_REACHED = (
    "This conversation reached its budget: raise it in the assistant settings or start a new one."
)
NOT_INSTALLED = "The assistant needs the Anthropic SDK: run `uv sync --extra agent` in backend/."


class AgentError(AppError):
    def __init__(self, message: str, code: str = "agent_error", status: int = 400) -> None:
        super().__init__(message, code=code, status_code=status)


@dataclass
class Run:
    """A turn being played: its events, and the flag Stop raises."""

    conversation_id: str
    events: "queue.Queue[Any]" = field(default_factory=queue.Queue)
    stop: threading.Event = field(default_factory=threading.Event)


class AgentService:
    def __init__(
        self,
        repository: ConversationRepository,
        store: SettingsStore,
        services: AppServices,
        registry: ToolRegistry,
        provider_factory: Callable[[str], Provider],
        sdk_available: Callable[[], bool] = lambda: True,
    ) -> None:
        self.repository = repository
        self.store = store
        self.services = services
        self.registry = registry
        self.provider_factory = provider_factory
        self.sdk_available = sdk_available
        self._runs: dict[str, Run] = {}
        self._lock = threading.Lock()

    # --- settings -------------------------------------------------------------------------------

    def settings(self) -> tuple[AgentSettings, KeyStatus]:
        return self.store.load(), self.store.key_status()

    def update_settings(
        self,
        model: str | None = None,
        effort: str | None = None,
        budget_usd: float | None = None,
        api_key: str | None = None,
    ) -> tuple[AgentSettings, KeyStatus]:
        current = self.store.load()
        if model is not None:
            if model not in MODELS:
                raise AgentError(f"Unknown model {model!r}.", "unknown_model")
            current.model = model
        if effort is not None:
            if effort not in EFFORTS:
                raise AgentError(f"Unknown effort {effort!r}.", "unknown_effort")
            current.effort = effort  # type: ignore[assignment]
        if budget_usd is not None:
            if not 0 < budget_usd <= 100:
                raise AgentError("The budget must be between $0.01 and $100.", "bad_budget")
            current.budget_usd = budget_usd
        self.store.save(current)
        if api_key is not None:
            try:
                self.store.save_key(api_key)
            except ValueError as error:
                raise AgentError(str(error), "bad_key") from error
        return self.settings()

    def test_key(self) -> str:
        """A tiny request with the saved key and model: the model's answer, or a clear error."""
        settings = self.store.load()
        key, _ = self.store.key()
        request = Request(
            model=settings.model,
            system="Reply with the single word OK.",
            messages=[user_text("Test")],
            effort="low",
            max_tokens=2_000,
        )
        try:
            for event in self.provider_factory(key).stream(request):
                if isinstance(event, Completed):
                    return settings.model
        except ProviderError as error:
            raise AgentError(error.message, f"key_{error.kind}") from error
        raise AgentError("The model gave no answer.", "key_other")

    # --- conversations --------------------------------------------------------------------------

    def conversations(self, dataset_id: str) -> list[Conversation]:
        self.services.columns.ready(dataset_id)
        return self.repository.for_dataset(dataset_id)

    def create(self, dataset_id: str) -> Conversation:
        self.services.columns.ready(dataset_id)
        return self.repository.create(dataset_id, NEW_TITLE, self.store.load().model)

    def conversation(self, conversation_id: str) -> tuple[Conversation, list[Message]]:
        found = self.repository.get(conversation_id)
        if found is None:
            raise AgentError("This conversation no longer exists.", "unknown_conversation", 404)
        return found, self.repository.messages(conversation_id)

    def delete(self, conversation_id: str) -> None:
        if not self.repository.delete(conversation_id):
            raise AgentError("This conversation no longer exists.", "unknown_conversation", 404)

    def running(self, conversation_id: str) -> bool:
        return conversation_id in self._runs

    # --- turns ----------------------------------------------------------------------------------

    def send(
        self,
        conversation_id: str,
        text: str,
        conditions: list[Condition],
        page: str | None = None,
    ) -> Run:
        """Starts a turn in the background and returns it; `events(run)` streams it."""
        conversation, history = self.conversation(conversation_id)
        text = text.strip()
        if not text:
            raise AgentError("Write a message first.", "empty_message")
        with self._lock:
            if conversation_id in self._runs:
                raise AgentError("The assistant is still answering.", "busy", 409)
            run = Run(conversation_id)
            self._runs[conversation_id] = run
        threading.Thread(
            target=self._play,
            args=(run, conversation, history, text, conditions, page),
            name=f"agent-{conversation_id}",
            daemon=True,
        ).start()
        return run

    def stop(self, conversation_id: str) -> bool:
        run = self._runs.get(conversation_id)
        if run is not None:
            run.stop.set()
        return run is not None

    def events(self, run: Run, heartbeat: float = 15.0) -> Iterator[dict[str, Any] | None]:
        """The turn's events, then the end; None is a keep-alive while nothing happens."""
        while True:
            try:
                event = run.events.get(timeout=heartbeat)
            except queue.Empty:
                yield None
                continue
            if event is END:
                return
            yield event

    def _play(
        self,
        run: Run,
        conversation: Conversation,
        history: list[Message],
        text: str,
        conditions: list[Condition],
        page: str | None,
    ) -> None:
        emit = run.events.put
        try:
            settings = self.store.load()
            budget = Budget(settings.budget_usd, conversation.cost_usd)
            if budget.exceeded:
                emit(
                    _error(
                        "budget",
                        BUDGET_REACHED,
                    )
                )
                return
            if not self.sdk_available():
                emit(
                    _error(
                        "not_installed",
                        NOT_INSTALLED,
                    )
                )
                return
            key, _ = self.store.key()
            question = user_text(
                turn_context([describe_condition(c) for c in conditions], page) + text
            )
            turn = Turn(
                provider=self.provider_factory(key),
                registry=self.registry,
                context=ToolContext(conversation.dataset_id, conditions, run.stop.is_set),
                model=settings.model,
                system=self._system(conversation.dataset_id),
                history=[*history, question],
                budget=budget,
                emit=lambda event: emit(_event(event)),
                should_stop=run.stop.is_set,
                effort=settings.effort,
            )
            result = turn.run()
            if result.messages:
                self.repository.append(
                    conversation.id, [question, *result.messages], result.cost_usd, settings.model
                )
                if conversation.title == NEW_TITLE:
                    self.repository.rename(conversation.id, _title(text))
            emit(_finish(result, budget))
        except Exception as error:  # the stream must always end with a message
            emit(_error("other", f"The assistant failed: {error}"))
        finally:
            with self._lock:
                self._runs.pop(run.conversation_id, None)
            emit(END)

    def _system(self, dataset_id: str) -> str:
        dataset = self.services.columns.ready(dataset_id)
        views = [v for v in self.services.columns.columns(dataset_id) if not v.excluded]
        stats = self.services.profiling.overview(dataset_id).column_stats
        columns = [
            ColumnBrief(
                v.name,
                v.type,
                v.role,
                stats[v.name].missing_pct if v.name in stats else None,
            )
            for v in views
            if v.type != "ignored"
        ]
        return system_prompt(dataset.name, dataset.row_count or 0, columns)


def strip_context(text: str) -> str:
    """The user's own words, without the app context sent along."""
    return CONTEXT.sub("", text, count=1)


def _title(text: str) -> str:
    line = " ".join(text.split())
    return line if len(line) <= TITLE_CHARS else line[: TITLE_CHARS - 1] + "…"


def _event(event: TurnEvent) -> dict[str, Any]:
    if isinstance(event, TextDelta):
        return {"type": "text", "text": event.text}
    if isinstance(event, ThinkingDelta):
        return {"type": "thinking", "text": event.text}
    if isinstance(event, StepStarted):
        return {
            "type": "step_started",
            "id": event.call_id,
            "tool": event.tool,
            "label": event.label,
            "input": event.input,
        }
    if isinstance(event, StepDone):
        return {
            "type": "step_done",
            "id": event.call_id,
            "ok": event.ok,
            "summary": event.summary,
            "link": event.link,
            "ms": event.ms,
        }
    if isinstance(event, Spent):
        return {
            "type": "spent",
            "turn_usd": event.turn_usd,
            "conversation_usd": event.conversation_usd,
            "tokens": event.tokens,
        }
    if isinstance(event, Notice):
        return {"type": "notice", "message": event.message}
    return {"type": "notice", "message": str(event)}


def _error(kind: str, message: str) -> dict[str, Any]:
    return {"type": "error", "kind": kind, "message": message}


ENDINGS = {
    "max_steps": "Step limit reached: the answer uses what was found so far.",
    "budget": "The conversation reached its budget: raise it in the assistant settings to go on.",
    "stopped": "Stopped.",
    "refused": "The model declined this request.",
    "truncated": "The answer was cut off.",
    "tool_failures": "A tool kept failing, so the assistant stopped.",
}


def _finish(result: TurnResult, budget: Budget) -> dict[str, Any]:
    if result.end == "error" and result.error is not None:
        return _error(result.error.kind, result.error.message)
    return {
        "type": "done",
        "end": result.end,
        "message": ENDINGS.get(result.end),
        "turn_usd": result.cost_usd,
        "conversation_usd": budget.spent_usd,
    }
