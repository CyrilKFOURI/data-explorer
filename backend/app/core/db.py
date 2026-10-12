"""SQLite access and migrations.

Migrations are numbered `.sql` files in `core/migrations/`, applied once each, in order.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def apply_migrations(connection: sqlite3.Connection) -> list[str]:
    """Apply pending migrations and return the versions that were applied."""
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " version TEXT PRIMARY KEY,"
        " applied_at TEXT NOT NULL)"
    )
    applied = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
    newly_applied: list[str] = []
    for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if migration.stem in applied:
            continue
        connection.executescript(migration.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (migration.stem, datetime.now(UTC).isoformat()),
        )
        connection.commit()
        newly_applied.append(migration.stem)
    return newly_applied


def is_healthy(db_path: Path) -> bool:
    try:
        connection = connect(db_path)
        try:
            connection.execute("SELECT 1")
        finally:
            connection.close()
        return True
    except sqlite3.Error:
        return False
