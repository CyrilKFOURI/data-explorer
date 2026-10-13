-- Named filter combinations of a dataset, reapplied in one click (JSON list of conditions).
CREATE TABLE saved_filters (
    id          TEXT PRIMARY KEY,
    dataset_id  TEXT NOT NULL REFERENCES datasets (id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    conditions  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    UNIQUE (dataset_id, name)
);
