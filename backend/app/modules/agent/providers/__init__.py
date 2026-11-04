"""LLM providers behind the engine's `Provider` interface, chosen by vendor."""

import importlib.util
from typing import Protocol

from app.modules.agent.engine.provider import Provider
from app.modules.agent.providers.vendors import Vendor


class ModelLister(Protocol):
    def list_models(self) -> list[str]: ...


def sdk_installed(vendor: Vendor) -> bool:
    """Whether the SDK this vendor needs is installed (extra `[agent]`)."""
    return importlib.util.find_spec(vendor.kind) is not None


def make_provider(vendor: Vendor, key: str, base_url: str | None = None) -> Provider:
    """Claude through its dedicated provider; every other vendor through the OpenAI format."""
    if vendor.kind == "anthropic":
        from app.modules.agent.providers.anthropic import AnthropicProvider

        return AnthropicProvider(key)
    from app.modules.agent.providers.openai_compat import OpenAICompatProvider

    return OpenAICompatProvider(
        key,
        base_url if vendor.id == "custom" else vendor.base_url,
        vendor.label,
        needs_key=vendor.needs_key,
        tag=vendor.id,
    )
