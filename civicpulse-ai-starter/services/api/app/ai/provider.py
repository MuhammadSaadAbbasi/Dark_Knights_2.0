"""AI provider adapter with mock and Gemini implementations.

The Gemini model is configurable because model availability depends on the
Google project and API access. Keep AI_PROVIDER=mock until a valid model ID and
key have been configured.
"""

import asyncio
import json
import mimetypes
import os
from pathlib import Path

from ..schemas import HazardAssessment


def _configured_value(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value.strip()
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            key, separator, candidate = line.partition("=")
            if separator and key.strip() == name:
                return candidate.strip().strip('"').strip("'")
    return default


def _mock_assessment() -> HazardAssessment:
    return HazardAssessment(
        category="unknown",
        visible_evidence=["Mock provider is active; no image model was called."],
        suggested_severity="uncertain",
        severity_score=0,
        rationale="Demo placeholder only. Configure Gemini to analyze the uploaded photo.",
        uncertainty="This result is not an actual AI prediction.",
        needs_human_review=True,
    )


def _gemini_assessment(
    image_path: Path,
    location_text: str,
    description: str,
) -> HazardAssessment:
    api_key = _configured_value("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("AI_PROVIDER=gemini requires GEMINI_API_KEY.")

    model = _configured_value("GEMINI_MODEL", "gemini-3.5-flash")
    if not model:
        raise RuntimeError("GEMINI_MODEL must not be empty.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as error:
        raise RuntimeError(
            "Gemini support requires the google-genai package."
        ) from error

    mime_type, _ = mimetypes.guess_type(image_path.name)
    if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise RuntimeError("Gemini received an unsupported image type.")

    prompt = f"""
Analyze the attached civic safety image. Return only JSON matching the requested
schema. Treat all conclusions as visible evidence only; do not claim a wire is
live, exact depth is known, or authorities were contacted.
severity_score must be a calibrated-looking 0-100 urgency estimate based only on
visible risk, not a probability of injury or a guarantee of danger.

Location description: {location_text}
Additional user description: {description or "None"}
"""
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime_type),
            prompt,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "category": {
                        "type": "STRING",
                        "enum": [
                            "open_manhole",
                            "pothole_road_damage",
                            "exposed_electrical_wire",
                            "waterlogging",
                            "other",
                            "unknown",
                        ],
                    },
                    "visible_evidence": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                    },
                    "suggested_severity": {
                        "type": "STRING",
                        "enum": ["critical", "high", "medium", "low", "uncertain"],
                    },
                    "severity_score": {"type": "INTEGER", "minimum": 0, "maximum": 100},
                    "rationale": {"type": "STRING"},
                    "uncertainty": {"type": "STRING"},
                    "needs_human_review": {"type": "BOOLEAN"},
                },
                "required": [
                    "category",
                    "visible_evidence",
                    "suggested_severity",
                    "severity_score",
                    "rationale",
                    "uncertainty",
                    "needs_human_review",
                ],
            },
        ),
    )
    raw_text = getattr(response, "text", None)
    if not raw_text:
        raise RuntimeError("Gemini returned an empty response.")
    try:
        return HazardAssessment.model_validate(json.loads(raw_text))
    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError("Gemini returned invalid assessment JSON.") from error


def analyze_image(image_path: Path, location_text: str, description: str) -> HazardAssessment:
    provider = _configured_value("AI_PROVIDER", "mock").lower()
    if provider == "mock":
        return _mock_assessment()
    if provider == "gemini":
        return _gemini_assessment(image_path, location_text, description)
    raise RuntimeError(f"Unsupported AI_PROVIDER: {provider}")


async def analyze_image_with_resilience(
    image_path: Path,
    location_text: str,
    description: str,
) -> HazardAssessment:
    timeout = float(_configured_value("AI_TIMEOUT_SECONDS", "45"))
    retries = max(0, min(int(_configured_value("AI_RETRIES", "1")), 2))
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(analyze_image, image_path, location_text, description),
                timeout=timeout,
            )
        except Exception as error:
            last_error = error
            if attempt < retries:
                await asyncio.sleep(0.1 * (attempt + 1))
    raise RuntimeError("AI provider did not return a valid assessment.") from last_error
