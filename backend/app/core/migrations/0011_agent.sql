-- AI agent conversations (feature 026). One conversation belongs to one dataset and goes with it.
-- Messages are append-only: provider blocks (thinking, fallback markers) are replayed unchanged.
CREATE TABLE agent_conversations (
    id          TEXT PRIMARY KEY,
    dataset_id  TEXT NOT NULL REFERENCES datasets (id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    model       TEXT NOT NULL,
    cost_usd    REAL NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX agent_conversations_dataset ON agent_conversations (dataset_id, updated_at);

CREATE TABLE agent_messages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id  TEXT NOT NULL REFERENCES agent_conversations (id) ON DELETE CASCADE,
    role             TEXT NOT NULL,
    content          TEXT NOT NULL,  -- JSON: the engine's blocks
    created_at       TEXT NOT NULL
);
CREATE INDEX agent_messages_conversation ON agent_messages (conversation_id, id);
