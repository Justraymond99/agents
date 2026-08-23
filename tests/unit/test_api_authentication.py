from fastapi.testclient import TestClient

from app.main import app, settings


def test_protected_post_requires_api_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "api_token", "secret-token")

    with TestClient(app) as client:
        response = client.post("/memory/query", json={"namespace": "engineering", "text": "atlas"})

    assert response.status_code == 401
    assert response.json() == {"detail": "unauthorized"}
