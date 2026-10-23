from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import logging
import os
import sqlite3

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .auth import (
    authenticate_user,
    create_access_token,
    ensure_bootstrap_admin,
    hash_password,
    require_user,
    require_admin,
)
from .schemas import (
    AdminReportUpdate,
    AuditEvent,
    DemoLoginRequest,
    LoginRequest,
    RegisterRequest,
    ReportCreated,
    HazardAssessment,
    Severity,
    Status,
    TokenResponse,
)
from .severity import apply_severity_policy
from .ai.provider import analyze_image_with_resilience
from .db.connection import initialize_database
from .db.repository import create_report as save_report
from .db.repository import get_report as find_report
from .db.repository import list_reports as find_reports
from .db.repository import update_report, delete_report as remove_report
from .db.repository import create_audit_event, list_audit_events
from .db.repository import list_location_hotspots
from .db.users import create_user, get_user
from .validation import read_valid_image, safe_image_path

APP_NAME = os.getenv("APP_NAME", "CivicPulse AI API")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "8"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
logger = logging.getLogger(__name__)


def _configured_value(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value.strip()
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            key, separator, candidate = line.partition("=")
            if separator and key.strip() == name:
                return candidate.strip().strip('"').strip("'")
    return default


app = FastAPI(title=APP_NAME, version="0.1.0")
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_database()
ensure_bootstrap_admin()

@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME}


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    expires_in = max(5, int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))) * 60
    return TokenResponse(
        access_token=create_access_token(user),
        expires_in=expires_in,
        user={"username": user["username"], "role": user["role"]},
    )


@app.post("/api/auth/demo-login", response_model=TokenResponse)
def demo_login(payload: DemoLoginRequest):
    if _configured_value("DEMO_LOGIN_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Demo login is disabled.")

    username = _configured_value("ADMIN_USERNAME", "demo-admin") if payload.role == "admin" else "demo-user"
    user = get_user(username)
    if not user:
        user = create_user(
            username=username,
            password_hash=hash_password(os.urandom(32).hex()),
            role=payload.role,
            created_at=datetime.now(timezone.utc).isoformat(),
            email=f"{username}@demo.civicpulse.local",
            location="Hackathon demo",
        )
    expires_in = max(5, int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))) * 60
    return TokenResponse(
        access_token=create_access_token(user),
        expires_in=expires_in,
        user={"username": user["username"], "role": user["role"]},
    )


@app.post("/api/auth/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest):
    username = payload.username.strip()
    if get_user(username):
        raise HTTPException(status_code=409, detail="Username is already registered.")
    try:
        user = create_user(
            username=username,
            password_hash=hash_password(payload.password),
            role="user",
            created_at=datetime.now(timezone.utc).isoformat(),
            email=payload.email.strip().lower(),
            location=payload.location.strip(),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username is already registered.")
    expires_in = max(5, int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))) * 60
    return TokenResponse(
        access_token=create_access_token(user),
        expires_in=expires_in,
        user={"username": username, "role": "user"},
    )

@app.post("/api/reports", response_model=ReportCreated, status_code=201)
async def create_report(
    photo: UploadFile = File(...),
    location_text: str = Form(..., min_length=3, max_length=300),
    description: str = Form(default="", max_length=1000),
    user: dict = Depends(require_user),
):
    contents, extension = await read_valid_image(photo, MAX_UPLOAD_MB)

    report_id = str(uuid4())
    image_path = safe_image_path(UPLOAD_DIR, report_id, extension)
    image_path.write_bytes(contents)

    record = {
        "id": report_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "location_text": location_text.strip(),
        "description": description.strip(),
        "image_path": str(image_path),
        "status": "NEW",
        "ai_status": "PENDING",
        "assessment": None,
        "owner_id": user["id"],
    }
    save_report(record)

    try:
        raw_assessment = await analyze_image_with_resilience(
            image_path, location_text, description
        )
        assessment = apply_severity_policy(raw_assessment)
        updated = update_report(
            report_id,
            assessment=assessment.model_dump(),
            ai_status="COMPLETE",
        )
        if updated is not None:
            record = updated
    except Exception:
        logger.exception("AI assessment failed for report %s", report_id)
        fallback = HazardAssessment(
            category="unknown",
            visible_evidence=[],
            suggested_severity="uncertain",
            severity_score=0,
            rationale="Automated analysis was unavailable. Please review the image manually.",
            uncertainty="AI analysis failed or could not be validated.",
            needs_human_review=True,
        ).model_dump()
        updated = update_report(report_id, ai_status="FAILED", assessment=fallback)
        if updated is not None:
            record = updated

    return ReportCreated(**record)

@app.get("/api/reports/{report_id}", response_model=ReportCreated)
def get_report(report_id: str, user: dict = Depends(require_user)):
    record = find_report(report_id, owner_id=user["id"])
    if not record:
        raise HTTPException(status_code=404, detail="Report not found.")
    # Do not return local image path to clients.
    return {k: v for k, v in record.items() if k != "image_path"}

@app.get("/api/admin/reports")
def list_reports(
    response: Response,
    status: Status | None = Query(default=None),
    severity: Severity | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: dict = Depends(require_admin),
):
    records, total = find_reports(
        status=status, severity=severity, page=page, page_size=page_size
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)
    return [
        {k: v for k, v in record.items() if k != "image_path"}
        for record in records
    ]


@app.get("/api/admin/hotspots")
def get_admin_hotspots(
    limit: int = Query(default=10, ge=1, le=50),
    _: dict = Depends(require_admin),
):
    return list_location_hotspots(limit)


@app.get("/api/admin/reports/{report_id}/image")
def get_admin_report_image(report_id: str, _: dict = Depends(require_admin)):
    record = find_report(report_id)
    if not record:
        raise HTTPException(status_code=404, detail="Report not found.")
    image_path = Path(record["image_path"])
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Report image is not available.")
    return FileResponse(image_path)


@app.delete("/api/admin/reports/{report_id}", status_code=204)
def delete_admin_report(report_id: str, _: dict = Depends(require_admin)):
    if remove_report(report_id) is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return Response(status_code=204)


@app.patch("/api/admin/reports/{report_id}", response_model=ReportCreated)
def review_report(
    report_id: str,
    update: AdminReportUpdate,
    actor: dict = Depends(require_admin),
):
    record = find_report(report_id)
    if not record:
        raise HTTPException(status_code=404, detail="Report not found.")
    if not update.model_fields_set:
        raise HTTPException(status_code=400, detail="Provide at least one review field.")
    changes = update.model_dump(exclude_unset=True)
    changes["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    before = {
        key: record.get(key)
        for key in ("status", "verified_category", "verified_severity", "review_note")
    }
    updated = update_report(report_id, **changes)
    create_audit_event(
        report_id,
        actor["username"],
        "report_reviewed",
        {"before": before, "after": changes},
        changes["reviewed_at"],
    )
    return updated


@app.get("/api/admin/reports/{report_id}/audit", response_model=list[AuditEvent])
def get_report_audit(report_id: str, _: dict = Depends(require_admin)):
    if not find_report(report_id):
        raise HTTPException(status_code=404, detail="Report not found.")
    return list_audit_events(report_id)
