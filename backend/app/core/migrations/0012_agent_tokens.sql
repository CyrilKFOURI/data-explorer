-- AI agent (026): tokens spent per conversation, the budget of models whose price is unknown.
ALTER TABLE agent_conversations ADD COLUMN tokens INTEGER NOT NULL DEFAULT 0;
