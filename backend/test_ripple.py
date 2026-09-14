"""Tests for the non-mutating ripple simulation endpoint."""

from pandas.testing import assert_frame_equal
from fastapi.testclient import TestClient

from main import app
from shortage import load_inventory


client = TestClient(app)


def test_ripple_simulation_uses_a_source_without_mutating_inventory():
    recommendations = client.get("/redistribution")
    assert recommendations.status_code == 200
    recommendation = recommendations.json()[0]
    original_inventory = load_inventory()

    response = client.post(
        "/ripple/simulate",
        json={
            "hospital_id": recommendation["destination_hospital_id"],
            "medicine_id": recommendation["medicine_id"],
        },
    )

    assert response.status_code == 200
    simulation = response.json()
    assert simulation["affected_hospital"] == recommendation["destination_hospital_id"]
    assert simulation["medicine"] == recommendation["medicine_id"]
    assert simulation["source_hospital"] == recommendation["source_hospital_id"]
    assert simulation["recommended_transfer_quantity"] > 0
    assert simulation["recommended_transfer_quantity"] <= simulation["available_surplus"]
    assert simulation["final_ripple_status"] in {"RIPPLE CONTAINED", "POTENTIAL RIPPLE"}

    assert_frame_equal(original_inventory, load_inventory())


if __name__ == "__main__":
    test_ripple_simulation_uses_a_source_without_mutating_inventory()
    print("Ripple simulation test passed.")
