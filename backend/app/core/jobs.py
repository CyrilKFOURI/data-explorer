"""Run long tasks in the background. Status and progress live in the `jobs` table."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Protocol


class JobRunner(Protocol):
    def submit(self, task: Callable[[], None]) -> None: ...

    def shutdown(self) -> None: ...


class ThreadJobRunner:
    def __init__(self, max_workers: int = 2) -> None:
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="job")

    def submit(self, task: Callable[[], None]) -> None:
        self._pool.submit(task)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)


class InlineJobRunner:
    """Runs tasks immediately; used by tests for deterministic behavior."""

    def submit(self, task: Callable[[], None]) -> None:
        task()

    def shutdown(self) -> None:
        pass
