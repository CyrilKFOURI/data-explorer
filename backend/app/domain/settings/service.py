"""Global settings (detection thresholds) in SQLite, and the workspace's disk usage."""

import json
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from app.core import db
from app.core.storage import Workspace
from app.domain.datasets.service import DatasetService
from app.domain.settings import gpu
from app.domain.settings.gpu import GpuStatus
from app.domain.typing.engine import DEFAULT_THRESHOLDS, Thresholds

DETECTION_KEY = "detection"
COMPUTE_KEY = "compute"


class DetectionSettings(BaseModel):
    """Bounds keep detection sensible: below half, "mostly numbers" would mean nothing."""

    parse_rate: float = Field(default=DEFAULT_THRESHOLDS.parse_rate, ge=0.5, le=1)
    empty_rate: float = Field(default=DEFAULT_THRESHOLDS.empty_rate, ge=0.5, le=1)
    discrete_max: int = Field(default=DEFAULT_THRESHOLDS.discrete_max, ge=2, le=1000)
    identifier_unique: float = Field(default=DEFAULT_THRESHOLDS.identifier_unique, ge=0.5, le=1)


class ComputeSettings(BaseModel):
    """None = automatic: on when a ready GPU is found. Used by the deep models (023b)."""

    use_gpu: bool | None = None


class AppSettings(BaseModel):
    detection: DetectionSettings = Field(default_factory=DetectionSettings)
    compute: ComputeSettings = Field(default_factory=ComputeSettings)


@dataclass
class DatasetUsage:
    id: str
    name: str
    bytes: int


@dataclass
class StorageInfo:
    workspace: str
    total_bytes: int
    datasets: list[DatasetUsage]


def folder_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


class SettingsService:
    def __init__(self, workspace: Workspace, datasets: DatasetService) -> None:
        self.workspace = workspace
        self.datasets = datasets
        self.cache_clearers: list[Callable[[], None]] = []
        self._gpu: GpuStatus | None = None

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        connection = db.connect(self.workspace.db_path)
        try:
            yield connection
        finally:
            connection.close()

    def get(self) -> AppSettings:
        with self._db() as connection:
            rows = connection.execute(
                "SELECT key, value FROM settings WHERE key IN (?, ?)", (DETECTION_KEY, COMPUTE_KEY)
            ).fetchall()
        stored = {row["key"]: json.loads(row["value"]) for row in rows}
        return AppSettings(
            detection=DetectionSettings.model_validate(stored.get(DETECTION_KEY, {})),
            compute=ComputeSettings.model_validate(stored.get(COMPUTE_KEY, {})),
        )

    def update(self, settings: AppSettings) -> AppSettings:
        with self._db() as connection:
            for key, value in (
                (DETECTION_KEY, settings.detection.model_dump_json()),
                (COMPUTE_KEY, settings.compute.model_dump_json()),
            ):
                connection.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
                    (key, value),
                )
            connection.commit()
        return settings

    def gpu(self, refresh: bool = False) -> GpuStatus:
        """The card found at start-up (or again on demand: "Check again")."""
        if refresh or self._gpu is None:
            self._gpu = gpu.detect()
        return self._gpu

    def thresholds(self) -> Thresholds:
        return Thresholds(**self.get().detection.model_dump())

    def storage(self) -> StorageInfo:
        usage = [
            DatasetUsage(d.id, d.name, folder_size(self.workspace.dataset_dir(d.id)))
            for d in self.datasets.list_all()
        ]
        usage.sort(key=lambda item: -item.bytes)
        return StorageInfo(str(self.workspace.root), folder_size(self.workspace.root), usage)

    def clear_caches(self) -> None:
        for clear in self.cache_clearers:
            clear()
