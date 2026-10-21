"""The agent's settings and API key (spec 026, R-AG-P3).

Settings live in `<workspace>/agent/settings.json`. The key is read from the environment
(`DATA_EXPLORER_ANTHROPIC_API_KEY`, then the SDK's own `ANTHROPIC_API_KEY`), otherwise from
`<workspace>/agent/secrets.env`, written when the user pastes a key in the app. The key never
leaves the backend: the API only says whether one is set and shows its last four characters."""

import contextlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, get_args

from app.modules.agent.engine.provider import Effort

ENV_KEYS = ("DATA_EXPLORER_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY")
SECRET_NAME = "ANTHROPIC_API_KEY"
MODELS = ("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5")
DEFAULT_MODEL = "claude-opus-5-5"
EFFORTS: tuple[Effort, ...] = get_args(Effort)
KeySource = Literal["env", "file", "none"]


@dataclass
class AgentSettings:
    model: str = DEFAULT_MODEL
    effort: Effort = "high"
    budget_usd: float = 1.0  # per conversation (R-AG-B2)


@dataclass(frozen=True)
class KeyStatus:
    configured: bool
    source: KeySource
    hint: str | None  # "…a1b2"


class SettingsStore:
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    @property
    def _settings_path(self) -> Path:
        return self.folder / "settings.json"

    @property
    def _secrets_path(self) -> Path:
        return self.folder / "secrets.env"

    # --- settings ---------------------------------------------------------------------------

    def load(self) -> AgentSettings:
        try:
            raw = json.loads(self._settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return AgentSettings()
        found = AgentSettings()
        if raw.get("model") in MODELS:
            found.model = raw["model"]
        if raw.get("effort") in EFFORTS:
            found.effort = raw["effort"]
        budget = raw.get("budget_usd")
        if isinstance(budget, int | float) and 0 < budget <= 100:
            found.budget_usd = float(budget)
        return found

    def save(self, settings: AgentSettings) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        self._settings_path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")

    # --- key ----------------------------------------------------------------------------------

    def key(self) -> tuple[str, KeySource]:
        for name in ENV_KEYS:
            value = os.environ.get(name, "").strip()
            if value:
                return value, "env"
        try:
            for line in self._secrets_path.read_text(encoding="utf-8").splitlines():
                name, _, value = line.partition("=")
                if name.strip() == SECRET_NAME and value.strip():
                    return value.strip(), "file"
        except OSError:
            pass
        return "", "none"

    def key_status(self) -> KeyStatus:
        value, source = self.key()
        return KeyStatus(bool(value), source, f"…{value[-4:]}" if len(value) >= 8 else None)

    def save_key(self, value: str) -> None:
        """Writes the key to the workspace secrets file; an empty value removes it."""
        value = value.strip()
        if not value:
            self._secrets_path.unlink(missing_ok=True)
            return
        if any(ch.isspace() for ch in value) or "=" in value:
            raise ValueError("This does not look like an API key.")
        self.folder.mkdir(parents=True, exist_ok=True)
        self._secrets_path.write_text(f"{SECRET_NAME}={value}\n", encoding="utf-8")
        with contextlib.suppress(OSError):  # owner-only where the system allows it
            os.chmod(self._secrets_path, 0o600)
