"""Small endpoint test for the FastAPI backend."""

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_api_endpoints():
    root_response = client.get("/")
    assert root_response.status_code == 200
    assert root_response.json() == {
        "message": "Medicine Shortage Prediction API",
        "status": "running",
    }

    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "healthy"

    shortages_response = client.get("/shortages")
    assert shortages_response.status_code == 200
    assert isinstance(shortages_response.json(), list)
    assert "hospital_id" in shortages_response.json()[0]

    critical_response = client.get("/shortages/critical")
    assert critical_response.status_code == 200
    assert all(row["status"] == "CRITICAL" for row in critical_response.json())

    redistribution_response = client.get("/redistribution")
    assert redistribution_response.status_code == 200
    assert isinstance(redistribution_response.json(), list)
    assert "recommended_transfer" in redistribution_response.json()[0]

    summary_response = client.get("/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_hospitals"] > 0
    assert summary["total_medicines"] > 0
    assert summary["total_redistribution_recommendations"] >= 0

    cors_response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert cors_response.headers["access-control-allow-origin"] == "http://localhost:3000"


if __name__ == "__main__":
    test_api_endpoints()
    print("All API endpoint tests passed.")