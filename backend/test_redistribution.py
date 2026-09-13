"""Manual report for the synthetic redistribution recommendation component."""

from redistribution import generate_recommendations
from shortage import analyze_shortage


if __name__ == "__main__":
    recommendations = generate_recommendations()
    shortages = analyze_shortage()
    shortage_cases = shortages[
        shortages["status"].isin(["CRITICAL", "WARNING"])
        & (shortages["shortage_quantity"] > 0)
    ]
    matched_cases = recommendations[
        ["destination_hospital_id", "medicine_id"]
    ].drop_duplicates()
    unmatched_cases = shortage_cases.merge(
        matched_cases,
        left_on=["hospital_id", "medicine_id"],
        right_on=["destination_hospital_id", "medicine_id"],
        how="left",
        indicator=True,
    )
    unmatched_cases = unmatched_cases[unmatched_cases["_merge"] == "left_only"]

    print("Redistribution recommendations:")
    if recommendations.empty:
        print("No recommendations found.")
    else:
        print(recommendations.to_string(index=False))

    print("\nHighest priority recommendations:")
    print(recommendations.head(3).to_string(index=False))
    print(
        f"\nShortage cases with a recommendation: "
        f"{len(matched_cases)} of {len(shortage_cases)}"
    )
    print("\nShortage cases without a suitable surplus source:")
    if unmatched_cases.empty:
        print("None")
    else:
        print(unmatched_cases[["hospital_id", "medicine_id", "medicine_name", "status"]].to_string(index=False))