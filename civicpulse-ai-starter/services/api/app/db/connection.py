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
                assessment_json TEXT,
                verified_category TEXT,
                verified_severity TEXT,
                review_note TEXT,
                reviewed_at TEXT,
                owner_id INTEGER
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                changes_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                location TEXT,
                role TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(reports)").fetchall()
        }
        for name, definition in {
            "verified_category": "TEXT",
            "verified_severity": "TEXT",
            "review_note": "TEXT",
            "reviewed_at": "TEXT",
            "owner_id": "INTEGER",
        }.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE reports ADD COLUMN {name} {definition}")
        user_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        for name, definition in {"email": "TEXT", "location": "TEXT"}.items():
            if name not in user_columns:
                connection.execute(f"ALTER TABLE users ADD COLUMN {name} {definition}")
        connection.commit()


def connection_scope() -> Iterator[sqlite3.Connection]:
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()
