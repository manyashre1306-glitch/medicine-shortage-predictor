"""Manual test and small report for the shortage detection component."""

from shortage import analyze_shortage, get_critical_shortages


if __name__ == "__main__":
    analysis = analyze_shortage()
    critical_shortages = get_critical_shortages()

    print("First shortage analysis results:")
    print(analysis.head().to_string(index=False))
    print("\nCritical shortages:")
    if critical_shortages.empty:
        print("No critical shortages found.")
    else:
        print(critical_shortages.to_string(index=False))

    print("\nShortage status counts:")
    print(analysis["status"].value_counts().reindex(
        ["CRITICAL", "WARNING", "MONITOR", "SAFE"], fill_value=0
    ))