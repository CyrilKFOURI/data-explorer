"""Forecast jobs: models run one after the other in the background, with progress and cancel.

Results are kept by (series, horizon, models) so running the same forecast again is instant.
"""

import threading
import uuid
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal

import numpy as np

from app.domain.timeseries import forecast as fc
from app.domain.timeseries import series as ts
from app.domain.timeseries.seasonality import period_end, starts

Status = Literal["running", "done", "cancelled", "failed"]
KEPT = 16


@dataclass
class SeriesForecast:
    horizon: int
    periods: list[str]  # history (complete periods)
    history: list[float | None]
    future: list[str]  # the forecast periods
    reference: str  # the naive model each model is compared with
    origins: int  # rolling origins used for validation
    results: list[fc.ModelResult]  # sorted by MASE, failures last
    best: str | None


@dataclass
class ForecastJob:
    id: str
    status: Status
    done: int  # models finished
    total: int
    current: str | None = None  # the model being fitted
    result: SeriesForecast | None = None
    error: str | None = None


def future_periods(last: str, period: ts.Period, horizon: int) -> list[str]:
    moment = starts([last], period)[0]
    labels = []
    for _ in range(horizon):
        moment = period_end(moment, period) + timedelta(seconds=1)
        labels.append(moment.strftime(ts.FORMATS[period]))
    return labels


class ForecastJobs:
    def __init__(self, workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="forecast")
        self._jobs: OrderedDict[str, ForecastJob] = OrderedDict()
        self._by_key: dict[tuple[Any, ...], str] = {}
        self._cancels: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._by_key.clear()

    def get(self, job_id: str) -> ForecastJob | None:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> ForecastJob | None:
        job = self._jobs.get(job_id)
        if job and job.status == "running":
            self._cancels[job_id].set()
        return job

    def start(
        self,
        key: tuple[Any, ...],
        values: list[float | None],
        periods: list[str],
        period: ts.Period,
        season: int | None,
        horizon: int,
        models: dict[str, fc.Model],
    ) -> ForecastJob:
        with self._lock:
            known = self._by_key.get(key)
            if known and (job := self._jobs.get(known)) and job.status in ("running", "done"):
                return job
            job = ForecastJob(uuid.uuid4().hex[:12], "running", 0, len(models))
            self._jobs[job.id] = job
            self._cancels[job.id] = threading.Event()
            self._by_key[key] = job.id
            while len(self._jobs) > KEPT:
                old_id, _ = self._jobs.popitem(last=False)
                self._cancels.pop(old_id, None)
                self._by_key = {k: v for k, v in self._by_key.items() if v != old_id}
        self._executor.submit(self._run, job, values, periods, period, season, horizon, models)
        return job

    def _run(
        self,
        job: ForecastJob,
        values: list[float | None],
        periods: list[str],
        period: ts.Period,
        season: int | None,
        horizon: int,
        models: dict[str, fc.Model],
    ) -> None:
        try:
            series, _ = ts.complete(values)
            results: list[fc.ModelResult] = []
            for key, model in models.items():
                if self._cancels[job.id].is_set():
                    job.status = "cancelled"
                    return
                job.current = key
                results.append(fc.run_model(key, model, series, horizon, season))
                job.done += 1
            job.current = None
            reference = self._reference(results, series, horizon, season)
            ranked = sorted(
                results,
                key=lambda r: (
                    r.scores is None,
                    r.scores.mase if r.scores and r.scores.mase is not None else np.inf,
                ),
            )
            best = next((r.key for r in ranked if r.scores), None)
            job.result = SeriesForecast(
                horizon,
                periods,
                [None if v is None else float(v) for v in values],
                future_periods(periods[-1], period, horizon),
                reference,
                len(fc.origins(len(series), horizon, season)),
                ranked,
                best,
            )
            job.status = "done"
        except Exception as error:
            job.status, job.error = "failed", str(error)

    @staticmethod
    def _reference(results: list[fc.ModelResult], series, horizon: int, season: int | None) -> str:
        """The naive reference is always scored, even when it was not among the chosen models."""
        wanted = "seasonal_naive" if season and len(series) > 2 * season + 2 else "naive"
        if not any(r.key == wanted and r.scores for r in results):
            extra = fc.run_model(wanted, fc.MODELS[wanted], series, horizon, season)
            fc.compare_to_reference([*results, extra], season)
            return wanted
        return fc.compare_to_reference(results, season)


ModelFactory = Callable[[str], fc.Model]
