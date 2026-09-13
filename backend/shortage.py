"""Detect possible medicine shortages for the synthetic prototype data."""

from pathlib import Path

import pandas as pd

from prediction import predict_demand


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INVENTORY_PATH = PROJECT_ROOT / "data" / "hospital_inventory.csv"
DEFAULT_SAFETY_DAYS = 7


def load_inventory():
    """Load hospital inventory and check the columns used by this analysis."""
    inventory = pd.read_csv(INVENTORY_PATH)
    required_columns = {
        "hospital_id",
        "hospital_name",
        "medicine_id",
        "medicine_name",
        "current_stock",
    }
    missing_columns = required_columns.difference(inventory.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    return inventory


def _clean_prediction(hospital_id, medicine_id):
    """Return a usable prediction, treating missing or invalid values as zero."""
    predicted_demand = predict_demand(hospital_id, medicine_id)
    if pd.isna(predicted_demand) or predicted_demand < 0:
        return 0.0
    return float(predicted_demand)


def _status_for_days(days_until_stockout):
    """Translate stockout days into a simple, explainable status."""
    if days_until_stockout < 3:
        return "CRITICAL"
    if days_until_stockout < 7:
        return "WARNING"
    if days_until_stockout < 14:
        return "MONITOR"
    return "SAFE"


def _risk_score_for_days(days_until_stockout):
    """Give zero risk at 14+ days and linearly higher risk near stockout."""
    if days_until_stockout == float("inf"):
        return 0.0
    score = (14 - days_until_stockout) / 14 * 100
    return round(max(0.0, min(100.0, score)), 2)


def analyze_shortage(safety_days=DEFAULT_SAFETY_DAYS):
    """Return shortage calculations for every hospital and medicine row."""
    if safety_days < 0:
        raise ValueError("safety_days must be zero or greater")

    inventory = load_inventory()
    results = []

    for row in inventory.to_dict("records"):
        predicted_daily_demand = _clean_prediction(
            row["hospital_id"], row["medicine_id"]
        )
        current_stock = max(0.0, float(row["current_stock"]))

        # Zero demand means the stock will not run out based on this prediction.
        if predicted_daily_demand == 0:
            days_until_stockout = float("inf")
        else:
            days_until_stockout = current_stock / predicted_daily_demand

        # Safety stock is the predicted demand for the configured buffer period.
        safety_stock = predicted_daily_demand * safety_days
        shortage_quantity = max(0.0, safety_stock - current_stock)
        results.append(
            {
                "hospital_id": row["hospital_id"],
                "hospital_name": row["hospital_name"],
                "medicine_id": row["medicine_id"],
                "medicine_name": row["medicine_name"],
                "current_stock": current_stock,
                "predicted_daily_demand": round(predicted_daily_demand, 2),
                "days_until_stockout": days_until_stockout,
                "safety_stock": round(safety_stock, 2),
                "enough_stock": current_stock >= safety_stock,
                "shortage_quantity": round(shortage_quantity, 2),
                "risk_score": _risk_score_for_days(days_until_stockout),
                "status": _status_for_days(days_until_stockout),
            }
        )

    return pd.DataFrame(results)


def get_critical_shortages(safety_days=DEFAULT_SAFETY_DAYS):
    """Return only rows whose stockout status is CRITICAL."""
    analysis = analyze_shortage(safety_days=safety_days)
    return analysis[analysis["status"] == "CRITICAL"].reset_index(drop=True)


if __name__ == "__main__":
    print(analyze_shortage().head())