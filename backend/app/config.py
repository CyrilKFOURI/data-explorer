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


def default_samples_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "samples"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DATA_EXPLORER_",
        env_file=("../.env", ".env"),
        extra="ignore",
    )

    home: Path = Field(default_factory=default_home)
    static_dir: Path | None = None
    # When set (Docker: /data), browsing and imports are restricted to this folder.
    data_dir: Path | None = None
    samples_dir: Path = Field(default_factory=default_samples_dir)
    max_upload_mb: int = 2048
    # Host names the API answers to (protection against DNS rebinding).
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1", "::1"])
