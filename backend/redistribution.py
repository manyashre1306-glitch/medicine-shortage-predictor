"""Recommend medicine transfers for the synthetic hackathon prototype."""

from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import pandas as pd

from shortage import DEFAULT_SAFETY_DAYS, analyze_shortage


PROJECT_ROOT = Path(__file__).resolve().parent.parent
HOSPITALS_PATH = PROJECT_ROOT / "data" / "hospitals.csv"


def load_hospitals():
    """Load fictional hospital coordinates used for distance estimates."""
    hospitals = pd.read_csv(HOSPITALS_PATH)
    required_columns = {"hospital_id", "latitude", "longitude"}
    missing_columns = required_columns.difference(hospitals.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    # Invalid or missing coordinates remain missing, so they do not break analysis.
    hospitals["latitude"] = pd.to_numeric(hospitals["latitude"], errors="coerce")
    hospitals["longitude"] = pd.to_numeric(hospitals["longitude"], errors="coerce")
    return hospitals[["hospital_id", "latitude", "longitude"]]


def haversine_distance(latitude_one, longitude_one, latitude_two, longitude_two):
    """Return the approximate distance between two points in kilometres."""
    values = [latitude_one, longitude_one, latitude_two, longitude_two]
    if any(pd.isna(value) for value in values):
        return None

    earth_radius_km = 6371.0
    lat_delta = radians(latitude_two - latitude_one)
    longitude_delta = radians(longitude_two - longitude_one)
    latitude_one = radians(latitude_one)
    latitude_two = radians(latitude_two)
    haversine_value = (
        sin(lat_delta / 2) ** 2
        + cos(latitude_one) * cos(latitude_two) * sin(longitude_delta / 2) ** 2
    )
    return 2 * earth_radius_km * asin(sqrt(haversine_value))


def _number(value, default=0.0):
    """Convert a value to a usable non-negative number."""
    if pd.isna(value):
        return default
    return max(default, float(value))


def _format_units(value):
    return f"{value:.0f}"


def _format_days(value):
    if value == float("inf"):
        return "an unknown number of"
    return f"{value:.1f}"


def _recommendation_score(source_surplus, maximum_surplus, distance_km,
                          maximum_distance_km, destination_risk_score):
    """Combine surplus, distance, and urgency into a 0-100 score.

    Surplus contributes 40 points, closeness contributes 30 points, and
    destination urgency contributes 30 points. Missing coordinates receive
    zero distance points but can still be considered when no closer option is
    available.
    """
    surplus_score = 40 * source_surplus / maximum_surplus
    if distance_km is None or maximum_distance_km == 0:
        distance_score = 0.0 if distance_km is None else 30.0
    else:
        distance_score = 30 * (1 - distance_km / maximum_distance_km)
    urgency_score = 30 * destination_risk_score / 100
    return round(max(0.0, min(100.0, surplus_score + distance_score + urgency_score)), 2)


def generate_recommendations(safety_days=DEFAULT_SAFETY_DAYS):
    """Return ranked transfer recommendations for critical and warning rows."""
    shortage_analysis = analyze_shortage(safety_days=safety_days)
    hospitals = load_hospitals().set_index("hospital_id")
    shortage_rows = shortage_analysis[
        shortage_analysis["status"].isin(["CRITICAL", "WARNING"])
        & (shortage_analysis["shortage_quantity"] > 0)
    ]
    source_rows = shortage_analysis[shortage_analysis["safety_stock"] < shortage_analysis["current_stock"]].copy()
    source_rows["source_surplus"] = (
        source_rows["current_stock"] - source_rows["safety_stock"]
    )

    recommendations = []
    for destination in shortage_rows.to_dict("records"):
        candidates = source_rows[
            (source_rows["medicine_id"] == destination["medicine_id"])
            & (source_rows["hospital_id"] != destination["hospital_id"])
            & (source_rows["source_surplus"] > 0)
        ].copy()
        if candidates.empty:
            continue

        destination_coordinates = hospitals.reindex([destination["hospital_id"]]).iloc[0]
        candidate_records = []
        for source in candidates.to_dict("records"):
            source_coordinates = hospitals.reindex([source["hospital_id"]]).iloc[0]
            distance_km = haversine_distance(
                destination_coordinates["latitude"],
                destination_coordinates["longitude"],
                source_coordinates["latitude"],
                source_coordinates["longitude"],
            )
            candidate_records.append({"source": source, "distance_km": distance_km})

        maximum_surplus = max(item["source"]["source_surplus"] for item in candidate_records)
        known_distances = [
            item["distance_km"] for item in candidate_records
            if item["distance_km"] is not None
        ]
        maximum_distance = max(known_distances, default=0.0)

        for item in candidate_records:
            source = item["source"]
            transfer_quantity = min(
                _number(destination["shortage_quantity"]),
                _number(source["source_surplus"]),
            )
            if transfer_quantity <= 0:
                continue

            score = _recommendation_score(
                source["source_surplus"],
                maximum_surplus,
                item["distance_km"],
                maximum_distance,
                _number(destination["risk_score"]),
            )
            if item["distance_km"] is None:
                distance_text = "an unknown distance away"
            else:
                distance_text = f"approximately {item['distance_km']:.1f} km away"
            reason = (
                f"{destination['destination_hospital_name'] if 'destination_hospital_name' in destination else destination['hospital_name']} "
                f"has a {destination['status'].lower()} shortage of "
                f"{destination['medicine_name']} and may run out in "
                f"{_format_days(destination['days_until_stockout'])} days. "
                f"{source['hospital_name']} has {_format_units(source['source_surplus'])} "
                f"units of surplus stock and is {distance_text}. Transfer "
                f"{_format_units(transfer_quantity)} units."
            )
            recommendations.append(
                {
                    "destination_hospital_id": destination["hospital_id"],
                    "destination_hospital_name": destination["hospital_name"],
                    "medicine_id": destination["medicine_id"],
                    "medicine_name": destination["medicine_name"],
                    "destination_status": destination["status"],
                    "destination_risk_score": destination["risk_score"],
                    "shortage_quantity": destination["shortage_quantity"],
                    "source_hospital_id": source["hospital_id"],
                    "source_hospital_name": source["hospital_name"],
                    "source_surplus": round(source["source_surplus"], 2),
                    "distance_km": None if item["distance_km"] is None else round(item["distance_km"], 2),
                    "recommended_transfer": round(transfer_quantity, 2),
                    "recommendation_score": score,
                    "reason": reason,
                }
            )

    columns = [
        "destination_hospital_id",
        "destination_hospital_name",
        "medicine_id",
        "medicine_name",
        "destination_status",
        "destination_risk_score",
        "shortage_quantity",
        "source_hospital_id",
        "source_hospital_name",
        "source_surplus",
        "distance_km",
        "recommended_transfer",
        "recommendation_score",
        "reason",
    ]
    recommendations = pd.DataFrame(recommendations, columns=columns)
    if recommendations.empty:
        return recommendations
    return recommendations.sort_values(
        ["destination_hospital_id", "recommendation_score"],
        ascending=[True, False],
    ).drop_duplicates(
        subset=["destination_hospital_id", "medicine_id", "source_hospital_id"]
    ).reset_index(drop=True)


if __name__ == "__main__":
    print(generate_recommendations().to_string(index=False))