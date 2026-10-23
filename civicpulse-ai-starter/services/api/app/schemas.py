from typing import Literal
from pydantic import BaseModel, Field

Category = Literal[
    "open_manhole", "pothole_road_damage", "exposed_electrical_wire",
    "waterlogging", "other", "unknown"
]
Severity = Literal["critical", "high", "medium", "low", "uncertain"]

class HazardAssessment(BaseModel):
    category: Category = "unknown"
    visible_evidence: list[str] = Field(default_factory=list, max_length=8)
    suggested_severity: Severity = "uncertain"
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
