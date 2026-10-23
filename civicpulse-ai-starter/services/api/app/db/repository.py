import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .connection import get_connection


def _from_row(row: sqlite3.Row) -> dict[str, Any]:
    record = dict(row)
    record["assessment"] = (
        json.loads(record["assessment_json"])
        if record["assessment_json"] is not None
        else None
    )
    assessment = record["assessment"]
    if isinstance(assessment, dict) and (
        "severity_score" not in assessment or assessment["severity_score"] == 0
    ):
        fallback_scores = {
            "critical": 90,
            "high": 75,
            "medium": 50,
            "low": 25,
            "uncertain": 0,
        }
        assessment["severity_score"] = fallback_scores.get(
            assessment.get("suggested_severity", "uncertain"), 0
        )
    del record["assessment_json"]
    return record


def create_report(record: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reports (
                id, created_at, location_text, description, image_path,
                status, ai_status, assessment_json, owner_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                record.get("owner_id"),
            ),
        )
        connection.commit()
    return record


def update_report(report_id: str, **changes: Any) -> dict[str, Any] | None:
    allowed = {
        "status",
        "ai_status",
        "assessment",
        "verified_category",
        "verified_severity",
        "review_note",
        "reviewed_at",
    }
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


def get_report(report_id: str, owner_id: int | None = None) -> dict[str, Any] | None:
    owner_clause = ""
    values: list[Any] = [report_id]
    if owner_id is not None:
        owner_clause = " AND owner_id = ?"
        values.append(owner_id)
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT * FROM reports WHERE id = ?{owner_clause}", values
        ).fetchone()
    return _from_row(row) if row else None


def list_reports(
    status: str | None = None,
    severity: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    clauses: list[str] = []
    values: list[str] = []
    if status:
        clauses.append("status = ?")
        values.append(status)
    if severity:
        clauses.append(
            "(verified_severity = ? OR "
            "(verified_severity IS NULL AND json_extract(assessment_json, '$.suggested_severity') = ?))"
        )
        values.extend([severity, severity])
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_connection() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) AS count FROM reports{where}", values
        ).fetchone()["count"]
        rows = connection.execute(
            f"SELECT * FROM reports{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [*values, page_size, (page - 1) * page_size],
        ).fetchall()
    return [_from_row(row) for row in rows], total


def delete_report(report_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT image_path FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
        if not row:
            return None
        connection.execute("DELETE FROM audit_events WHERE report_id = ?", (report_id,))
        connection.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        connection.commit()
    image_path = Path(row["image_path"])
    if image_path.is_file():
        image_path.unlink()
    return {"id": report_id}


def list_location_hotspots(limit: int = 10) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                location_text AS location,
                COUNT(*) AS report_count,
                SUM(
                    CASE WHEN COALESCE(
                        verified_severity,
                        json_extract(assessment_json, '$.suggested_severity')
                    ) IN ('critical', 'high') THEN 1 ELSE 0 END
                ) AS priority_count,
                SUM(
                    CASE WHEN COALESCE(
                        verified_severity,
                        json_extract(assessment_json, '$.suggested_severity')
                    ) = 'critical' THEN 1 ELSE 0 END
                ) AS critical_count
            FROM reports
            GROUP BY location_text
            ORDER BY priority_count DESC, report_count DESC, location_text ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_audit_event(
    report_id: str,
    actor: str,
    action: str,
    changes: dict[str, Any],
    created_at: str,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_events
                (report_id, actor, action, changes_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (report_id, actor, action, json.dumps(changes), created_at),
        )
        connection.commit()


def list_audit_events(report_id: str) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, report_id, actor, action, changes_json, created_at
            FROM audit_events
            WHERE report_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (report_id,),
        ).fetchall()
    return [
        {
            **dict(row),
            "changes": json.loads(row["changes_json"]),
        }
        for row in rows
    ]
