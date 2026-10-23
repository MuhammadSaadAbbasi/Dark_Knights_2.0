from typing import Literal
from pydantic import BaseModel, Field

Category = Literal[
    "open_manhole", "pothole_road_damage", "exposed_electrical_wire",
    "waterlogging", "other", "unknown"
]
Severity = Literal["critical", "high", "medium", "low", "uncertain"]
Status = Literal["NEW", "UNDER_REVIEW", "VERIFIED", "ASSIGNED", "RESOLVED", "REJECTED"]

class HazardAssessment(BaseModel):
    category: Category = "unknown"
    visible_evidence: list[str] = Field(default_factory=list, max_length=8)
    suggested_severity: Severity = "uncertain"
    severity_score: int = Field(default=0, ge=0, le=100)
    rationale: str = Field(max_length=500)
    uncertainty: str = Field(max_length=500)
    needs_human_review: bool = True

class ReportCreated(BaseModel):
    id: str
    created_at: str
    location_text: str
    description: str
    status: str
    ai_status: str
    assessment: HazardAssessment | None
    verified_category: Category | None = None
    verified_severity: Severity | None = None
    review_note: str | None = None
    reviewed_at: str | None = None
    image_url: str | None = None


class AdminReportUpdate(BaseModel):
    status: Status | None = None
    verified_category: Category | None = None
    verified_severity: Severity | None = None
    review_note: str | None = Field(default=None, max_length=1000)


class AuditEvent(BaseModel):
    id: int
    report_id: str
    actor: str
    action: str
    changes: dict[str, object]
    created_at: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=256)


class RegisterRequest(LoginRequest):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str = Field(
        min_length=5,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    location: str = Field(min_length=3, max_length=300)


class DemoLoginRequest(BaseModel):
    role: Literal["user", "admin"]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict[str, str]
