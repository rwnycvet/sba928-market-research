"""Build a monthly brief using Python calculations and coverage checks."""

import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results" / "monthly_revenue.csv"
OUTPUT = ROOT / "results_v3" / "verified_reports"
TWO_PLACES = Decimal("0.01")


def month_index(label):
    year, month = map(int, label.split("-"))

    if year < 1 or not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {label}")

    return year * 12 + month - 1


def rounded(value):
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def main():
    with SOURCE.open(encoding="utf-8-sig", newline="") as file:
        source_rows = list(csv.DictReader(file))

    if not source_rows:
        raise ValueError("Monthly summary is empty.")

    months = []
    seen_months = set()

    for row in source_rows:
        label = row["Month"]

        if label in seen_months:
            raise ValueError(f"Duplicate month: {label}")
        seen_months.add(label)

        revenue = Decimal(row["SalesRevenue"])

        if not revenue.is_finite() or revenue < 0:
            raise ValueError(f"Invalid positive-sales revenue: {label}")

        coverage = row["DataCoverage"].strip()

        months.append({
            "month": label,
            "index": month_index(label),
            "revenue": revenue,
            "coverage": coverage,
            "complete": coverage == "Complete month",
            "change_percent": None,
        })

    months.sort(key=lambda item: item["index"])

    for previous, current in zip(months, months[1:]):
        comparable = (
            previous["complete"]
            and current["complete"]
            and current["index"] == previous["index"] + 1
            and previous["revenue"] > 0
        )

        if comparable:
            current["change_percent"] = (
                (current["revenue"] - previous["revenue"])
                / previous["revenue"] * 100
            )

    complete_months = [item for item in months if item["complete"]]
    increases = [
        item for item in months
        if item["change_percent"] is not None
        and item["change_percent"] > 0
    ]
    decreases = [
        item for item in months
        if item["change_percent"] is not None
        and item["change_percent"] < 0
    ]

    if not complete_months or not increases or not decreases:
        raise ValueError(
            "This brief requires complete months and at least "
            "one qualifying increase and decrease."
        )

    highest = max(complete_months, key=lambda item: item["revenue"])
    largest_increase = max(
        increases, key=lambda item: item["change_percent"]
    )
    largest_decrease = min(
        decreases, key=lambda item: item["change_percent"]
    )

    lines = [
        "# Monthly Sales Brief",
        "",
        "Revenue is positive sales before return and cancellation deductions.",
        "",
        "| Month | Revenue (GBP) | Recorded Coverage | Change (%) |",
        "|---|---:|---|---:|",
    ]

    saved_months = []

    for item in months:
        change_text = (
            f"{rounded(item['change_percent']):+.2f}"
            if item["change_percent"] is not None
            else "N/A"
        )
        revenue_text = f"{rounded(item['revenue']):,.2f}"

        lines.append(
            f"| {item['month']} | {revenue_text} | "
            f"{item['coverage']} | {change_text} |"
        )

        saved_months.append({
            "month": item["month"],
            "positive_sales_revenue_gbp": (
                f"{rounded(item['revenue']):.2f}"
            ),
            "coverage": item["coverage"],
            "change_percent": (
                f"{rounded(item['change_percent']):.2f}"
                if item["change_percent"] is not None
                else None
            ),
        })

    findings = [
        (
            f"Largest qualifying increase: {largest_increase['month']}, "
            f"{rounded(largest_increase['change_percent']):+.2f}%."
        ),
        (
            f"Largest qualifying decrease: {largest_decrease['month']}, "
            f"{rounded(largest_decrease['change_percent']):+.2f}%."
        ),
        (
            f"Highest complete-month revenue: {highest['month']}, "
            f"GBP {rounded(highest['revenue']):,.2f}."
        ),
    ]

    recommendation = (
        "Review inventory timing around the recorded higher-revenue "
        "months using current stock and supplier lead times."
    )

    limitation = (
        "Changes are calculated only between consecutive months "
        "declared complete in the source summary. Partial-month totals "
        "cannot establish a full-month decline. These historical "
        "figures do not prove a recurring seasonal pattern or its cause."
    )

    lines.extend(["", "**Measured findings:**"])
    lines.extend(f"- {finding}" for finding in findings)
    lines.extend([
        "",
        f"**Recommendation:** {recommendation}",
        "",
        f"**Limitation:** {limitation}",
        "",
        "**Evidence:** results/monthly_revenue.csv",
    ])

    text = "\n".join(lines) + "\n"

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "monthly_brief.md").write_text(text, encoding="utf-8")

    report = {
        "method": "Python calculations and fixed report template",
        "months": saved_months,
        "findings": findings,
        "recommendation": recommendation,
        "limitation": limitation,
    }

    with (OUTPUT / "monthly_brief.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(text)
    print("Saved reports to:", OUTPUT)


if __name__ == "__main__":
    main()