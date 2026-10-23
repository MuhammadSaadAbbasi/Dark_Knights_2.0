from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import os
import shutil

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ReportCreated, HazardAssessment
from .severity import apply_severity_policy
from .ai.provider import analyze_image

APP_NAME = os.getenv("APP_NAME", "CivicPulse AI API")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "8"))
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title=APP_NAME, version="0.1.0")
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage is only for this starter/demo. Replace with SQLite/PostgreSQL.
REPORTS: dict[str, dict] = {}

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME}

@app.post("/api/reports", response_model=ReportCreated, status_code=201)
async def create_report(
    photo: UploadFile = File(...),
    location_text: str = Form(..., min_length=3, max_length=300),
    description: str = Form(default="", max_length=1000),
):
    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG, or WebP image.")
    contents = await photo.read()
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Image must be smaller than {MAX_UPLOAD_MB} MB.")

    report_id = str(uuid4())
    # Demo only: private storage is not configured here. Do not serve this folder publicly.
    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[photo.content_type]
    image_path = UPLOAD_DIR / f"{report_id}{extension}"
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
    REPORTS[report_id] = record

    try:
        raw_assessment = analyze_image(image_path, location_text, description)
        assessment = apply_severity_policy(raw_assessment)
        record["assessment"] = assessment.model_dump()
        record["ai_status"] = "COMPLETE"
    except Exception:
        # Keep report saved if provider fails; production should log a redacted error and offer retry.
        record["ai_status"] = "FAILED"
        record["assessment"] = HazardAssessment(
            category="unknown",
            visible_evidence=[],
            suggested_severity="uncertain",
            rationale="Automated analysis was unavailable. Please review the image manually.",
            uncertainty="AI analysis failed or could not be validated.",
            needs_human_review=True,
        ).model_dump()

    return ReportCreated(**record)

@app.get("/api/reports/{report_id}")
def get_report(report_id: str):
    record = REPORTS.get(report_id)
    if not record:
        raise HTTPException(status_code=404, detail="Report not found.")
    # Do not return local image path to clients.
    return {k: v for k, v in record.items() if k != "image_path"}

@app.get("/api/admin/reports")
def list_reports():
    # DEMO ONLY: protect this endpoint with admin authentication before deployment.
    return [
        {k: v for k, v in record.items() if k != "image_path"}
        for record in sorted(REPORTS.values(), key=lambda x: x["created_at"], reverse=True)
    ]
