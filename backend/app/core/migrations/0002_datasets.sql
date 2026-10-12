-- An imported dataset: a source (file or folder) copied as normalized Parquet in the workspace.
CREATE TABLE datasets (
    id             TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    source_path    TEXT NOT NULL,
    source_kind    TEXT NOT NULL CHECK (source_kind IN ('file', 'folder')),
    format         TEXT NOT NULL,
    options        TEXT NOT NULL,            -- JSON ImportOptions
    fingerprint    TEXT NOT NULL,            -- source state + options
    storage_path   TEXT NOT NULL,
    row_count      INTEGER,
    col_count      INTEGER,
    size_bytes     INTEGER,
    sample_pct     REAL NOT NULL DEFAULT 100,
    status         TEXT NOT NULL CHECK (status IN ('importing', 'ready', 'error')),
    error          TEXT,
    created_at     TEXT NOT NULL,
    imported_at    TEXT,
    last_opened_at TEXT,
    types_version  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX datasets_fingerprint ON datasets (fingerprint);

-- Source files as they were when imported, to detect later changes.
CREATE TABLE dataset_files (
    dataset_id TEXT NOT NULL REFERENCES datasets (id) ON DELETE CASCADE,
    path       TEXT NOT NULL,
    size       INTEGER NOT NULL,
    mtime      REAL NOT NULL,
    PRIMARY KEY (dataset_id, path)
);

-- Long-running background work (imports now; training, generation later).
CREATE TABLE jobs (
    id          TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    dataset_id  TEXT REFERENCES datasets (id) ON DELETE CASCADE,
    status      TEXT NOT NULL CHECK (status IN ('pending', 'running', 'done', 'failed')),
    progress    REAL NOT NULL DEFAULT 0,
    message     TEXT,
    created_at  TEXT NOT NULL,
    finished_at TEXT
);
