from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main
from app.db.connection import initialize_database


def image_bytes(format_name: str = "PNG") -> bytes:
    output = BytesIO()
    Image.new("RGB", (2, 2), color="white").save(output, format=format_name)
    return output.getvalue()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "reports.sqlite3"
    upload_path = tmp_path / "uploads"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setattr(main, "UPLOAD_DIR", upload_path)
    initialize_database()
    return TestClient(main.app)


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_read_report(client):
    response = client.post(
        "/api/reports",
        files={"photo": ("hazard.png", image_bytes(), "image/png")},
        data={"location_text": "Main Street near the school", "description": "Road is flooded"},
    )

    assert response.status_code == 201
    report = response.json()
    assert report["ai_status"] == "COMPLETE"
    assert report["assessment"]["category"] == "unknown"
    assert "image_path" not in report

    fetched = client.get(f"/api/reports/{report['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == report["id"]


def test_rejects_fake_image(client):
    response = client.post(
        "/api/reports",
        files={"photo": ("hazard.png", b"not an image", "image/png")},
        data={"location_text": "Main Street"},
    )

    assert response.status_code == 400


def test_rejects_mismatched_image_type(client):
    response = client.post(
        "/api/reports",
        files={"photo": ("hazard.jpg", image_bytes(), "image/jpeg")},
        data={"location_text": "Main Street"},
    )

    assert response.status_code == 415
