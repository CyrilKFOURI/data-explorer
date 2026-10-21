"""Conversations and their messages in SQLite (migration 0011_agent.sql)."""

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.core import db
from app.modules.agent.engine.messages import Message, from_dict, to_dict


@dataclass
class Conversation:
    id: str
    dataset_id: str
    title: str
    model: str
    cost_usd: float
    created_at: str
    updated_at: str
    tokens: int = 0


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _conversation(row: sqlite3.Row) -> Conversation:
    return Conversation(
        row["id"],
        row["dataset_id"],
        row["title"],
        row["model"],
        row["cost_usd"],
        row["created_at"],
        row["updated_at"],
        row["tokens"],
    )


class ConversationRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        connection = db.connect(self.db_path)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def create(self, dataset_id: str, title: str, model: str) -> Conversation:
        now = _now()
        found = Conversation(uuid.uuid4().hex[:12], dataset_id, title, model, 0.0, now, now)
        with self._db() as connection:
            connection.execute(
                "INSERT INTO agent_conversations "
                "(id, dataset_id, title, model, cost_usd, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (found.id, dataset_id, title, model, 0.0, now, now),
            )
        return found

    def get(self, conversation_id: str) -> Conversation | None:
        with self._db() as connection:
            row = connection.execute(
                "SELECT * FROM agent_conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
        return _conversation(row) if row else None

    def for_dataset(self, dataset_id: str) -> list[Conversation]:
        with self._db() as connection:
            rows = connection.execute(
                "SELECT * FROM agent_conversations WHERE dataset_id = ? ORDER BY updated_at DESC",
                (dataset_id,),
            ).fetchall()
        return [_conversation(r) for r in rows]

    def delete(self, conversation_id: str) -> bool:
        with self._db() as connection:
            cursor = connection.execute(
                "DELETE FROM agent_conversations WHERE id = ?", (conversation_id,)
            )
        return cursor.rowcount > 0

    def rename(self, conversation_id: str, title: str) -> None:
        with self._db() as connection:
            connection.execute(
                "UPDATE agent_conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, _now(), conversation_id),
            )

    def messages(self, conversation_id: str) -> list[Message]:
        with self._db() as connection:
            rows = connection.execute(
                "SELECT role, content FROM agent_messages WHERE conversation_id = ? ORDER BY id",
                (conversation_id,),
            ).fetchall()
        return [from_dict({"role": r["role"], **json.loads(r["content"])}) for r in rows]

    def append(
        self,
        conversation_id: str,
        messages: list[Message],
        cost_usd: float,
        model: str,
        tokens: int = 0,
    ) -> None:
        """Adds a turn's messages and its cost, in one transaction (append-only history)."""
        now = _now()
        with self._db() as connection:
            for message in messages:
                payload = to_dict(message)
                payload.pop("role")
                connection.execute(
                    "INSERT INTO agent_messages (conversation_id, role, content, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (conversation_id, message.role, json.dumps(payload, ensure_ascii=False), now),
                )
            connection.execute(
                "UPDATE agent_conversations SET cost_usd = cost_usd + ?, tokens = tokens + ?, "
                "model = ?, updated_at = ? WHERE id = ?",
                (cost_usd, tokens, model, now, conversation_id),
            )
