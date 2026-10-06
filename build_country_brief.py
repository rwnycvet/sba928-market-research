"""Build a country brief using measured revenue and verified warning rules."""

import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from evidence_rules import customer_count_warning

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results"
OUTPUT = ROOT / "results_v3" / "verified_reports"


def read_csv(filename):
    with (SOURCE / filename).open(
        encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


def main():
    revenue_rows = read_csv("country_revenue.csv")
    coverage_rows = read_csv("country_coverage.csv")

    coverage = {row["Country"]: row for row in coverage_rows}

    if len(coverage) != len(coverage_rows):
        raise ValueError("Duplicate countries in the coverage summary.")

    countries = []
    seen_countries = set()

    for row in revenue_rows:
        country = row["Country"]

        if country in seen_countries:
            raise ValueError("Duplicate countries in the revenue summary.")
        seen_countries.add(country)

        revenue = Decimal(row["SalesRevenue"])

        if not revenue.is_finite() or revenue < 0:
            raise ValueError(f"Invalid positive-sales revenue: {country}")

        countries.append({
            "country": country,
            "revenue": revenue,
        })

    countries.sort(
        key=lambda item: (-item["revenue"], item["country"])
    )

    if len(countries) < 3:
        raise ValueError("At least three country summaries are required.")

    products = []

    for rank, item in enumerate(countries[:3], start=1):
        country = item["country"]

        if country not in coverage:
            raise ValueError(f"Missing country coverage: {country}")

        identified = int(coverage[country]["IdentifiedCustomers"])
        warning = customer_count_warning(identified)

        if warning:
            action = (
                "Review revenue concentration and unidentified purchases "
                "before increasing marketing spend."
            )
        elif rank == 1:
            action = (
                "Test a campaign based on recorded product purchases "
                "and measure incremental sales."
            )
        else:
            action = (
                "Review recorded purchase frequency and product mix "
                "to design a small marketing test."
            )

        revenue = item["revenue"].quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        products.append({
            "country": country,
            "positive_sales_revenue_gbp": f"{revenue:.2f}",
            "identified_customers": identified,
            "small_sample_warning": warning,
            "marketing_recommendation": action,
        })

    limitation = (
        "Revenue represents this retailer's positive sales before "
        "return and cancellation deductions, including valid sales "
        "without CustomerIDs. The warning applies only to recorded "
        "identified-customer counts; missing IDs may represent additional "
        "customers. These records do not establish national demand "
        "or explain customer motives."
    )

    lines = [
        "# Country Sales Brief",
        "",
        "Revenue and customer counts are measured findings. "
        "Marketing actions are recommendations.",
        "",
        "| Country | Sales Revenue (GBP) | Identified Customers | "
        "Below-Five Warning | Marketing Recommendation |",
        "|---|---:|---:|---|---|",
    ]

    for item in products:
        warning_text = "Yes" if item["small_sample_warning"] else "No"
        country_text = item["country"].replace("|", "/")
        amount = Decimal(item["positive_sales_revenue_gbp"])

        lines.append(
            f"| {country_text} | {amount:,.2f} | "
            f"{item['identified_customers']:,} | {warning_text} | "
            f"{item['marketing_recommendation']} |"
        )

    lines.extend([
        "",
        f"**Limitation:** {limitation}",
        "",
        "**Evidence:** results/country_revenue.csv and "
        "results/country_coverage.csv",
    ])

    text = "\n".join(lines) + "\n"

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "country_brief.md").write_text(text, encoding="utf-8")

    report = {
        "method": "Prepared sales summaries, Python rule and fixed template",
        "countries": products,
        "limitation": limitation,
    }

    with (OUTPUT / "country_brief.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(text)
    print("Saved reports to:", OUTPUT)


if __name__ == "__main__":
    main()