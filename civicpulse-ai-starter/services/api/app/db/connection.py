import os
import sqlite3
from pathlib import Path
from typing import Iterator


def _database_path() -> Path:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./civicpulse.db")
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise RuntimeError("DATABASE_URL must use the sqlite:/// scheme for the MVP.")
    path = Path(database_url[len(prefix):])
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def get_connection() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                location_text TEXT NOT NULL,
                description TEXT NOT NULL,
                image_path TEXT NOT NULL,
                status TEXT NOT NULL,
                ai_status TEXT NOT NULL,
                assessment_json TEXT
            )
            """
        )
        connection.commit()


def connection_scope() -> Iterator[sqlite3.Connection]:
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()
