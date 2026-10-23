from pathlib import Path

import pytest

from app.ai.provider import analyze_image


def test_mock_provider_is_safe_default(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_PROVIDER", "mock")

    result = analyze_image(Path(tmp_path / "image.png"), "Main Street", "")

    assert result.category == "unknown"
    assert result.needs_human_review is True


def test_gemini_requires_key(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        analyze_image(Path(tmp_path / "image.png"), "Main Street", "")
