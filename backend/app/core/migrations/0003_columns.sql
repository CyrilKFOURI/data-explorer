-- One row per column of a dataset: what was detected, what the user corrected, a summary.
-- Effective value = user_* when set, else detected_*. Parsers and lists are JSON.
CREATE TABLE columns (
    dataset_id      TEXT NOT NULL REFERENCES datasets (id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    position        INTEGER NOT NULL,
    storage_dtype   TEXT NOT NULL,
    detected_type   TEXT NOT NULL,
    detected_role   TEXT,
    detected_parser TEXT NOT NULL,
    detected_order  TEXT,
    candidates      TEXT NOT NULL,          -- best parser per kind, to switch type cheaply
    confidence      TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
    reasons         TEXT NOT NULL,
    user_type       TEXT,
    user_role       TEXT,                   -- '' = explicitly no role
    user_parser     TEXT,
    user_order      TEXT,
    excluded        INTEGER NOT NULL DEFAULT 0,
    summary         TEXT,
    PRIMARY KEY (dataset_id, name)
);

ALTER TABLE datasets ADD COLUMN types_reviewed_at TEXT;
