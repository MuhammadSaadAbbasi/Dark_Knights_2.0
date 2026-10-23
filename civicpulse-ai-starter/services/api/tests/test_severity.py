from app.schemas import HazardAssessment
from app.severity import apply_severity_policy


def test_electrical_wire_is_high_risk():
    assessment = HazardAssessment(
        category="exposed_electrical_wire",
        visible_evidence=["A cable is visible"],
        suggested_severity="medium",
        rationale="The image shows a cable.",
        uncertainty="The image cannot confirm whether it is live.",
    )

    result = apply_severity_policy(assessment)

    assert result.suggested_severity == "high"
    assert result.needs_human_review is True
