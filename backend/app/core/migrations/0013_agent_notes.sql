-- AI agent (026c): short facts about a dataset that every conversation on it starts with.
-- Written by the user, or by the assistant once the user confirms. They go with the dataset.
CREATE TABLE agent_notes (
    id          TEXT PRIMARY KEY,
    dataset_id  TEXT NOT NULL REFERENCES datasets (id) ON DELETE CASCADE,
    text        TEXT NOT NULL,
    source      TEXT NOT NULL,  -- user | agent
    created_at  TEXT NOT NULL
);
CREATE INDEX agent_notes_dataset ON agent_notes (dataset_id, created_at);
