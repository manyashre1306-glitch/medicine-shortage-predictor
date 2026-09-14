"""Non-mutating medicine shortage ripple simulations."""

from redistribution import generate_recommendations
from shortage import analyze_shortage, _risk_score_for_days, _status_for_days


def _simulation_metrics(current_stock, predicted_daily_demand):
    """Calculate the same stockout metrics used by shortage detection."""
    current_stock = max(0.0, float(current_stock))
    predicted_daily_demand = max(0.0, float(predicted_daily_demand))
    days_until_stockout = (
        float("inf")
        if predicted_daily_demand == 0
        else current_stock / predicted_daily_demand
    )
    return {
        "days_until_stockout": days_until_stockout,
        "risk_score": _risk_score_for_days(days_until_stockout),
        "status": _status_for_days(days_until_stockout),
    }


def simulate_ripple(hospital_id, medicine_id):
    """Simulate the top existing transfer without changing source data."""
    shortage_analysis = analyze_shortage()
    affected_rows = shortage_analysis[
        (shortage_analysis["hospital_id"] == hospital_id)
        & (shortage_analysis["medicine_id"] == medicine_id)
    ]
    if affected_rows.empty:
        raise ValueError("The selected hospital and medicine combination was not found.")

    affected = affected_rows.iloc[0].to_dict()
    recommendation_rows = generate_recommendations()
    matching_recommendations = recommendation_rows[
        (recommendation_rows["destination_hospital_id"] == hospital_id)
        & (recommendation_rows["medicine_id"] == medicine_id)
    ]
    if matching_recommendations.empty:
        raise ValueError("No redistribution source is available for this shortage.")

    recommendation = matching_recommendations.sort_values(
        "recommendation_score", ascending=False
    ).iloc[0].to_dict()
    source_rows = shortage_analysis[
        (shortage_analysis["hospital_id"] == recommendation["source_hospital_id"])
        & (shortage_analysis["medicine_id"] == medicine_id)
    ]
    if source_rows.empty:
        raise ValueError("The recommended source inventory could not be found.")

    source = source_rows.iloc[0].to_dict()
    transfer_quantity = float(recommendation["recommended_transfer"])
    source_stock_after_transfer = max(0.0, float(source["current_stock"]) - transfer_quantity)
    source_after = _simulation_metrics(
        source_stock_after_transfer,
        source["predicted_daily_demand"],
    )

    return {
        "affected_hospital": affected["hospital_id"],
        "affected_hospital_name": affected["hospital_name"],
        "medicine": affected["medicine_id"],
        "medicine_name": affected["medicine_name"],
        "current_stock": affected["current_stock"],
        "predicted_daily_demand": affected["predicted_daily_demand"],
        "days_until_stockout": affected["days_until_stockout"],
        "initial_shortage_status": affected["status"],
        "initial_risk_score": affected["risk_score"],
        "source_hospital": source["hospital_id"],
        "source_hospital_name": source["hospital_name"],
        "source_hospital_current_stock": source["current_stock"],
        "available_surplus": recommendation["source_surplus"],
        "recommended_transfer_quantity": transfer_quantity,
        "source_hospital_stock_after_simulated_transfer": source_stock_after_transfer,
        "source_hospital_risk_after_transfer": source_after["risk_score"],
        "source_hospital_status_after_transfer": source_after["status"],
        "reason": recommendation["reason"],
        "final_ripple_status": (
            "RIPPLE CONTAINED"
            if source_after["status"] == "SAFE"
            else "POTENTIAL RIPPLE"
        ),
    }
