from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import logging
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ReportCreated, HazardAssessment
from .severity import apply_severity_policy
from .ai.provider import analyze_image
from .db.connection import initialize_database
from .db.repository import create_report as save_report
from .db.repository import get_report as find_report
from .db.repository import list_reports as find_reports
from .db.repository import update_report
from .validation import read_valid_image, safe_image_path

APP_NAME = os.getenv("APP_NAME", "CivicPulse AI API")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "8"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
logger = logging.getLogger(__name__)

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

@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME}

@app.post("/api/reports", response_model=ReportCreated, status_code=201)
async def create_report(
    photo: UploadFile = File(...),
    location_text: str = Form(..., min_length=3, max_length=300),
    description: str = Form(default="", max_length=1000),
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
    }
    save_report(record)

    try:
        raw_assessment = analyze_image(image_path, location_text, description)
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
            rationale="Automated analysis was unavailable. Please review the image manually.",
            uncertainty="AI analysis failed or could not be validated.",
            needs_human_review=True,
        ).model_dump()
        updated = update_report(report_id, ai_status="FAILED", assessment=fallback)
        if updated is not None:
            record = updated

    return ReportCreated(**record)

@app.get("/api/reports/{report_id}")
def get_report(report_id: str):
    record = find_report(report_id)
    if not record:
        raise HTTPException(status_code=404, detail="Report not found.")
    # Do not return local image path to clients.
    return {k: v for k, v in record.items() if k != "image_path"}

@app.get("/api/admin/reports")
def list_reports():
    # DEMO ONLY: protect this endpoint with admin authentication before deployment.
    return [
        {k: v for k, v in record.items() if k != "image_path"}
        for record in find_reports()
    ]
