import sqlite3
from typing import Any

from .connection import get_connection


def get_user(username: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, username, password_hash, email, location, role, is_active, created_at
            FROM users WHERE username = ?
            """,
            (username,),
        ).fetchone()
    return dict(row) if row else None


def create_user(
    username: str,
    password_hash: str,
    role: str,
    created_at: str,
    email: str | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (username, password_hash, email, location, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, password_hash, email, location, role, created_at),
        )
        connection.commit()
        return {
            "id": cursor.lastrowid,
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "location": location,
            "role": role,
            "is_active": 1,
            "created_at": created_at,
        }


def username_exists(username: str) -> bool:
    return get_user(username) is not None
