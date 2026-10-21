"""The LLM vendors the agent can use, and how to tell them apart from an API key alone.

Claude goes through its dedicated provider (prompt cache, thinking, server-side fallback).
Every other vendor speaks the OpenAI chat-completions format, so one generic provider serves
them all, each at its own base URL."""

import re
from dataclasses import dataclass, field
from typing import Literal

Kind = Literal["anthropic", "openai"]


@dataclass(frozen=True)
class Vendor:
    id: str
    label: str
    kind: Kind
    secret: str  # environment variable / secrets-file name of its key
    base_url: str | None = None  # None: the SDK's default (or the user's, for "custom")
    prefixes: tuple[str, ...] = ()  # how its keys start (detection), most specific first
    models: tuple[str, ...] = ()  # known models, best first (others are listed from the API)
    prefer: tuple[str, ...] = ()  # substrings that pick a default among the listed models
    console: str = ""  # where a key is created
    needs_key: bool = True


VENDORS: tuple[Vendor, ...] = (
    Vendor(
        "anthropic",
        "Anthropic (Claude)",
        "anthropic",
        "ANTHROPIC_API_KEY",
        prefixes=("sk-ant-",),
        models=("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"),
        console="console.anthropic.com",
    ),
    Vendor(
        "gemini",
        "Google Gemini",
        "openai",
        "GEMINI_API_KEY",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        prefixes=("AIza",),
        prefer=("pro", "flash"),
        console="aistudio.google.com",
    ),
    Vendor(
        "openrouter",
        "OpenRouter",
        "openai",
        "OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        prefixes=("sk-or-",),
        prefer=("anthropic/claude", "google/gemini", "openai/gpt"),
        console="openrouter.ai",
    ),
    Vendor(
        "groq",
        "Groq",
        "openai",
        "GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        prefixes=("gsk_",),
        prefer=("llama", "qwen"),
        console="console.groq.com",
    ),
    Vendor(
        "openai",
        "OpenAI",
        "openai",
        "OPENAI_API_KEY",
        prefixes=("sk-proj-", "sk-"),
        prefer=("gpt-5", "gpt-4.1", "gpt-4o"),
        console="platform.openai.com",
    ),
    Vendor(
        "mistral",
        "Mistral",
        "openai",
        "MISTRAL_API_KEY",
        base_url="https://api.mistral.ai/v1",
        prefer=("mistral-large", "mistral-medium"),
        console="console.mistral.ai",
    ),
    Vendor(
        "deepseek",
        "DeepSeek",
        "openai",
        "DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1",
        prefer=("deepseek-chat",),
        console="platform.deepseek.com",
    ),
    Vendor(
        "custom",
        "Other OpenAI-compatible API (Ollama, LM Studio…)",
        "openai",
        "CUSTOM_API_KEY",
        needs_key=False,
    ),
)
BY_ID: dict[str, Vendor] = {v.id: v for v in VENDORS}
# When no vendor is chosen, the first one with a key is used.
PREFERENCE = ("anthropic", "gemini", "openai", "openrouter", "groq", "mistral", "deepseek")

# Listed models that are not chat models (embeddings, images, audio…).
NOT_CHAT = re.compile(
    r"embed|image|imagen|tts|audio|whisper|dall-e|moderation|transcri|realtime|veo|aqa|"
    r"learnlm|search|computer-use|robotics",
    re.IGNORECASE,
)


def detect(key: str) -> Vendor | None:
    """The vendor whose keys look like this one, or None when the key doesn't say."""
    key = key.strip()
    for vendor in VENDORS:
        if any(key.startswith(prefix) for prefix in vendor.prefixes):
            return vendor
    return None


@dataclass
class ModelChoice:
    """The models a vendor offers to this key, and the one used by default."""

    models: list[str] = field(default_factory=list)
    default: str | None = None


def chat_models(ids: list[str]) -> list[str]:
    cleaned = [i.removeprefix("models/") for i in ids]
    return sorted({i for i in cleaned if not NOT_CHAT.search(i)})


def _version(model: str) -> tuple[float, ...]:
    return tuple(float(n) for n in re.findall(r"\d+(?:\.\d+)?", model)[:3]) or (0.0,)


def pick_default(vendor: Vendor, models: list[str]) -> str | None:
    """The vendor's best model among those listed: its preferred family, newest version first,
    stable before previews."""
    if vendor.models:
        return next((m for m in vendor.models if not models or m in models), vendor.models[0])
    for wanted in vendor.prefer:
        matching = [m for m in models if wanted in m.lower()]
        if matching:
            stable = [m for m in matching if not re.search(r"preview|exp|beta", m)] or matching
            return max(stable, key=lambda m: (_version(m), -len(m)))
    return models[0] if models else None
