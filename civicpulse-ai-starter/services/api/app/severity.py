from .schemas import HazardAssessment

def apply_severity_policy(result: HazardAssessment) -> HazardAssessment:
    """
    Transparent MVP policy, not a validated safety classifier.
    Human review is required for all high-risk categories.
    """
    if result.category == "unknown" or result.category == "other":
        result.suggested_severity = "uncertain"
        result.severity_score = min(result.severity_score, 35)
        result.needs_human_review = True
    elif result.category in {"open_manhole", "exposed_electrical_wire"}:
        if result.suggested_severity in {"low", "medium", "uncertain"}:
            result.suggested_severity = "high"
        result.severity_score = max(result.severity_score, 70)
        result.needs_human_review = True
        result.uncertainty = (
            result.uncertainty
            + " A photo cannot confirm exact danger or whether a wire is live."
        ).strip()
    else:
        result.needs_human_review = True
    if result.suggested_severity == "critical":
        result.severity_score = max(result.severity_score, 85)
    elif result.suggested_severity == "high":
        result.severity_score = max(result.severity_score, 70)
    return result
