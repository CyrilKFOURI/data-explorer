-- Saved KPIs of a dataset (feature 022): the definition as JSON, "auto" choices kept as such.
CREATE TABLE kpi_definitions (
    id          TEXT PRIMARY KEY,
    dataset_id  TEXT NOT NULL REFERENCES datasets (id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    definition  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE INDEX kpi_definitions_dataset ON kpi_definitions (dataset_id);
