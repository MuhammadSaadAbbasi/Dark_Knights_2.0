from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main
from app.auth import ensure_bootstrap_admin
from app.auth import hash_password
from app.db.connection import initialize_database
from app.db.users import create_user


def image_bytes(format_name: str = "PNG") -> bytes:
    output = BytesIO()
    Image.new("RGB", (2, 2), color="white").save(output, format=format_name)
    return output.getvalue()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "reports.sqlite3"
    upload_path = tmp_path / "uploads"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-at-least-32-characters")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "test-password-123")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("DEMO_LOGIN_ENABLED", "true")
    monkeypatch.setattr(main, "UPLOAD_DIR", upload_path)
    initialize_database()
    ensure_bootstrap_admin()
    create_user(
        "citizen",
        hash_password("citizen-password"),
        "user",
        "2026-01-01T00:00:00+00:00",
    )
    return TestClient(main.app)


def admin_headers(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-password-123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def user_headers(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "citizen", "password": "citizen-password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_report(client):
    return client.post(
        "/api/reports",
        headers=user_headers(client),
        files={"photo": ("hazard.png", image_bytes(), "image/png")},
        data={"location_text": "Main Street"},
    ).json()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_read_report(client):
    response = client.post(
        "/api/reports",
        headers=user_headers(client),
        files={"photo": ("hazard.png", image_bytes(), "image/png")},
        data={"location_text": "Main Street near the school", "description": "Road is flooded"},
    )
    assert response.status_code == 201
    report = response.json()
    assert report["ai_status"] == "COMPLETE"
    assert report["assessment"]["category"] == "unknown"
    assert "image_path" not in report
    fetched = client.get(f"/api/reports/{report['id']}", headers=user_headers(client))
    assert fetched.status_code == 200
    assert fetched.json()["id"] == report["id"]


def test_rejects_fake_image(client):
    response = client.post(
        "/api/reports",
        headers=user_headers(client),
        files={"photo": ("hazard.png", b"not an image", "image/png")},
        data={"location_text": "Main Street"},
    )
    assert response.status_code == 400


def test_rejects_mismatched_image_type(client):
    response = client.post(
        "/api/reports",
        headers=user_headers(client),
        files={"photo": ("hazard.jpg", image_bytes(), "image/jpeg")},
        data={"location_text": "Main Street"},
    )
    assert response.status_code == 415


def test_admin_can_review_without_overwriting_ai_assessment(client):
    created = create_report(client)
    response = client.patch(
        f"/api/admin/reports/{created['id']}",
        headers=admin_headers(client),
        json={
            "status": "VERIFIED",
            "verified_category": "pothole_road_damage",
            "verified_severity": "medium",
            "review_note": "Confirmed during review.",
        },
    )
    assert response.status_code == 200
    reviewed = response.json()
    assert reviewed["status"] == "VERIFIED"
    assert reviewed["verified_category"] == "pothole_road_damage"
    assert reviewed["verified_severity"] == "medium"
    assert reviewed["assessment"]["category"] == "unknown"
    assert reviewed["reviewed_at"] is not None


def test_admin_filter_uses_verified_severity_when_available(client):
    created = create_report(client)
    client.patch(
        f"/api/admin/reports/{created['id']}",
        headers=admin_headers(client),
        json={"verified_severity": "critical"},
    )
    response = client.get(
        "/api/admin/reports?severity=critical",
        headers=admin_headers(client),
    )
    assert response.status_code == 200
    assert [report["id"] for report in response.json()] == [created["id"]]


def test_admin_review_creates_audit_event(client):
    created = create_report(client)
    client.patch(
        f"/api/admin/reports/{created['id']}",
        headers=admin_headers(client),
        json={"status": "UNDER_REVIEW", "review_note": "Needs confirmation."},
    )
    audit = client.get(
        f"/api/admin/reports/{created['id']}/audit",
        headers=admin_headers(client),
    )
    assert audit.status_code == 200
    assert audit.json()[0]["action"] == "report_reviewed"
    assert audit.json()[0]["changes"]["after"]["status"] == "UNDER_REVIEW"


def test_admin_login_and_authorization(client):
    invalid_login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    unauthorized = client.get("/api/admin/reports")
    authorized = client.get("/api/admin/reports", headers=admin_headers(client))
    assert invalid_login.status_code == 401
    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_demo_login_returns_role_scoped_sessions(client):
    user = client.post("/api/auth/demo-login", json={"role": "user"})
    admin = client.post("/api/auth/demo-login", json={"role": "admin"})

    assert user.status_code == 200
    assert user.json()["user"]["role"] == "user"
    assert admin.status_code == 200
    assert admin.json()["user"]["role"] == "admin"


def test_user_can_register_and_report_is_owned(client):
    registration = client.post(
        "/api/auth/register",
        json={
            "username": "new-citizen",
            "password": "new-password-123",
            "email": "new@example.com",
            "location": "Central District",
        },
    )
    assert registration.status_code == 201
    token = registration.json()["access_token"]
    created = client.post(
        "/api/reports",
        headers={"Authorization": f"Bearer {token}"},
        files={"photo": ("hazard.png", image_bytes(), "image/png")},
        data={"location_text": "Market Road"},
    ).json()

    own = client.get(
        f"/api/reports/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    other = client.get(f"/api/reports/{created['id']}", headers=user_headers(client))

    assert own.status_code == 200
    assert other.status_code == 404


def test_duplicate_registration_returns_actionable_feedback(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "citizen",
            "password": "another-password",
            "email": "citizen@example.com",
            "location": "Central District",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Username is already registered."


def test_registration_validation_returns_field_feedback(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "bad space", "password": "short"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]
