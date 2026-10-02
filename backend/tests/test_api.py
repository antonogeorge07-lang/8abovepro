from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_portfolio_summary():
    response = client.get("/api/portfolio/summary")

    assert response.status_code == 200

    body = response.json()

    assert body["currency"] == "USD"
    assert body["total_assets"] == 142_850_420
    assert body["custodian_count"] == 3
    assert body["verified_custodian_count"] == 3
    assert len(body["custodians"]) == 3
