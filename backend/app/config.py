"""Application settings, read from environment variables and `.env`."""

import os
import sys
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_home() -> Path:
    if sys.platform == "win32" and (local_app_data := os.environ.get("LOCALAPPDATA")):
        return Path(local_app_data) / "DataExplorer"
    return Path.home() / ".local" / "share" / "data-explorer"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DATA_EXPLORER_",
        env_file=("../.env", ".env"),
        extra="ignore",
    )

    home: Path = Field(default_factory=default_home)
    static_dir: Path | None = None
