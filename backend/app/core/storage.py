"""Workspace layout: where the app keeps its database, datasets and cache."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Workspace:
    root: Path

    @property
    def db_path(self) -> Path:
        return self.root / "app.db"

    @property
    def datasets_dir(self) -> Path:
        return self.root / "datasets"

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    def ensure(self) -> None:
        for directory in (self.root, self.datasets_dir, self.cache_dir):
            directory.mkdir(parents=True, exist_ok=True)
