from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_public():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_dashboard_requires_auth_by_default():
    response = client.get("/dashboard")
    assert response.status_code == 401


def test_dashboard_accepts_default_development_credentials():
    response = client.get(
        "/dashboard",
        auth=("goldbot", "change-me"),
    )
    assert response.status_code == 200
    assert "GoldBot AI" in response.text
