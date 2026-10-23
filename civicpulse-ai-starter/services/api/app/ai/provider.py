"""
Mock AI adapter to make the starter runnable without API credentials.
Replace this function with Gemini/OpenAI API integration.
Do not use filename or user text alone to infer visual content.
"""
from pathlib import Path
from ..schemas import HazardAssessment

def analyze_image(image_path: Path, location_text: str, description: str) -> HazardAssessment:
    # This is a MOCK result for wiring/UI development, not real image recognition.
    # Make this obvious in your demo until a real vision API is connected.
    return HazardAssessment(
        category="unknown",
        visible_evidence=["Mock provider is active; no image model was called."],
        suggested_severity="uncertain",
        rationale="Demo placeholder only. Connect a vision-capable model to analyze the uploaded photo.",
        uncertainty="This result is not an actual AI prediction.",
        needs_human_review=True,
    )
