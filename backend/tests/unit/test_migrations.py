from pathlib import Path

from app.core import db


def test_migrations_create_tables(tmp_path: Path) -> None:
    connection = db.connect(tmp_path / "app.db")
    applied = db.apply_migrations(connection)
    tables = {
        row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    connection.close()

    assert applied == ["0001_init"]
    assert {"schema_migrations", "settings"} <= tables


def test_migrations_are_idempotent(tmp_path: Path) -> None:
    connection = db.connect(tmp_path / "app.db")
    db.apply_migrations(connection)
    second_run = db.apply_migrations(connection)
    connection.close()

    assert second_run == []
