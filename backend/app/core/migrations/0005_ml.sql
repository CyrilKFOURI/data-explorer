-- Machine learning runs: one trained model per row; the full result and the fitted pipeline
-- are files in the dataset's folder (ml/<id>.json, ml/<id>.joblib), deleted with it.
CREATE TABLE ml_runs (
    id          TEXT PRIMARY KEY,
    dataset_id  TEXT NOT NULL REFERENCES datasets (id) ON DELETE CASCADE,
    target      TEXT NOT NULL,
    task        TEXT NOT NULL,
    model       TEXT NOT NULL,
    settings    TEXT NOT NULL,
    conditions  TEXT NOT NULL,
    metric      TEXT NOT NULL,
    score       REAL,
    seconds     REAL NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE INDEX ml_runs_dataset_target ON ml_runs (dataset_id, target, created_at);
