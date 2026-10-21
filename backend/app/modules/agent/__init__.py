"""AI agent (docs/features/026-agent-ia): an analyst running the app's analyses through tools.

Self-contained: it uses the app's V1 services through `AppServices` and never imports another
module. Optional: without the Anthropic SDK (extra `[agent]`) or a key, it explains how to enable
itself and the rest of the app is unchanged."""

from fastapi import FastAPI

from app.modules.agent.providers.anthropic import AnthropicProvider, sdk_installed
from app.modules.agent.repository import ConversationRepository
from app.modules.agent.router import router
from app.modules.agent.service import AgentService
from app.modules.agent.settings import SettingsStore
from app.modules.agent.tools import AppServices, default_registry


def setup(app: FastAPI) -> None:
    state = app.state
    services = AppServices(
        columns=state.columns,
        profiling=state.profiling,
        variable=state.variable,
        compare=state.compare,
        correlations=state.correlations,
    )
    state.agent = AgentService(
        repository=ConversationRepository(state.workspace.db_path),
        store=SettingsStore(state.workspace.root / "agent"),
        services=services,
        registry=default_registry(services),
        provider_factory=AnthropicProvider,
        sdk_available=sdk_installed,
    )


__all__ = ["router", "setup"]
