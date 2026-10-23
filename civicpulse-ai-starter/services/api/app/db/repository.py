import json
import sqlite3
from typing import Any

from .connection import get_connection


def _from_row(row: sqlite3.Row) -> dict[str, Any]:
    record = dict(row)
    record["assessment"] = (
        json.loads(record["assessment_json"])
        if record["assessment_json"] is not None
        else None
    )
    del record["assessment_json"]
    return record


def create_report(record: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reports (
                id, created_at, location_text, description, image_path,
                status, ai_status, assessment_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["created_at"],
                record["location_text"],
                record["description"],
                record["image_path"],
                record["status"],
                record["ai_status"],
                json.dumps(record["assessment"])
                if record["assessment"] is not None
                else None,
            ),
        )
        connection.commit()
    return record


def update_report(report_id: str, **changes: Any) -> dict[str, Any] | None:
    allowed = {"status", "ai_status", "assessment"}
    fields = {key: value for key, value in changes.items() if key in allowed}
    if not fields:
        return get_report(report_id)

    assignments = []
    values: list[Any] = []
    for key, value in fields.items():
        column = "assessment_json" if key == "assessment" else key
        assignments.append(f"{column} = ?")
        values.append(json.dumps(value) if key == "assessment" else value)
    values.append(report_id)

    with get_connection() as connection:
        connection.execute(
            f"UPDATE reports SET {', '.join(assignments)} WHERE id = ?",
            values,
        )
        connection.commit()
    return get_report(report_id)


def get_report(report_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
    return _from_row(row) if row else None


def list_reports() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM reports ORDER BY created_at DESC"
        ).fetchall()
    return [_from_row(row) for row in rows]
