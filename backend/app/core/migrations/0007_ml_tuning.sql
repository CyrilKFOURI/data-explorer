-- 021: the validation of each run (comparable runs share it), and the hyper-parameter searches
-- with every trial.
ALTER TABLE ml_runs ADD COLUMN validation TEXT;

CREATE TABLE ml_tunings (
    id          TEXT PRIMARY KEY,
    dataset_id  TEXT NOT NULL REFERENCES datasets (id) ON DELETE CASCADE,
    target      TEXT NOT NULL,
    model       TEXT NOT NULL,
    metric      TEXT NOT NULL,
    request     TEXT NOT NULL,
    best_value  REAL,
    best_params TEXT NOT NULL,
    default_value REAL,
    importances TEXT NOT NULL,
    status      TEXT NOT NULL,
    seconds     REAL NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE ml_trials (
    tuning_id TEXT NOT NULL REFERENCES ml_tunings (id) ON DELETE CASCADE,
    number    INTEGER NOT NULL,
    value     REAL,
    state     TEXT NOT NULL,
    params    TEXT NOT NULL,
    seconds   REAL NOT NULL,
    PRIMARY KEY (tuning_id, number)
);
