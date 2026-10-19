-- Synthetic data runs (feature 023): one generation per row. The data, the real rows used for the
-- evaluation and the full report are files in the source dataset's folder
-- (synthetic/<id>/data.parquet, train.parquet, holdout.parquet, report.json), deleted with it.
CREATE TABLE synthetic_runs (
    id                  TEXT PRIMARY KEY,
    dataset_id          TEXT NOT NULL REFERENCES datasets (id) ON DELETE CASCADE,
    method              TEXT NOT NULL,
    settings            TEXT NOT NULL,
    rows                INTEGER NOT NULL,
    scores              TEXT,
    status              TEXT NOT NULL,
    error               TEXT,
    seconds             REAL NOT NULL,
    created_dataset_id  TEXT REFERENCES datasets (id) ON DELETE SET NULL,
    created_at          TEXT NOT NULL
);
CREATE INDEX synthetic_runs_dataset ON synthetic_runs (dataset_id, created_at);
CREATE INDEX synthetic_runs_created ON synthetic_runs (created_dataset_id);
