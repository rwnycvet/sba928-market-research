"""Report competitor-evidence limitations without inventing figures."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results" / "country_revenue.csv"
OUTPUT = ROOT / "results_v3" / "verified_reports"


def main():
    with SOURCE.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fields = reader.fieldnames
        rows = list(reader)

    if set(fields or []) != {"Country", "SalesRevenue"}:
        raise ValueError(
            "The source structure changed. Review its evidence scope."
        )

    if not rows:
        raise ValueError("Country revenue summary is empty.")

    questions = [
        {
            "question": "Does this retailer outsell its competitors?",
            "conclusion": "Cannot be determined from the supplied summary.",
            "additional_data": (
                "Competitor sales for matching dates, product categories "
                "and countries, using consistent currencies and treatment "
                "of returns and cancellations."
            ),
        },
        {
            "question": "What is this retailer's market share?",
            "conclusion": "Cannot be calculated without total-market sales.",
            "additional_data": (
                "Total-market sales covering the same period, categories, "
                "countries, sales channels and revenue definition."
            ),
        },
        {
            "question": "How many retailers operate in each country?",
            "conclusion": (
                "Country sales groups do not measure retailer counts."
            ),
            "additional_data": (
                "Dated business-register or industry data, with a "
                "consistent definition of retailer and a distinction "
                "between companies and store locations."
            ),
        },
        {
            "question": "Can CustomerID counts measure competing retailers?",
            "conclusion": (
                "Customer identifiers do not establish competitor counts."
            ),
            "additional_data": (
                "Verified competitor identities and business classifications."
            ),
        },
    ]

    limitation = (
        "The supplied summary describes the retailer's sales by country. "
        "It contains no competitor revenue, competitor identities or "
        "total-market sales. Missing competitor evidence must not be "
        "treated as zero competitor sales."
    )

    lines = [
        "# Competitor Research Brief",
        "",
        "| Research Question | Evidence-Based Conclusion | "
        "Additional Data Required |",
        "|---|---|---|",
    ]

    for item in questions:
        lines.append(
            f"| {item['question']} | {item['conclusion']} | "
            f"{item['additional_data']} |"
        )

    lines.extend([
        "",
        "**Recommendation:** Obtain comparable competitor evidence "
        "before making competitive-positioning or market-share claims.",
        "",
        f"**Limitation:** {limitation}",
        "",
        "**Evidence:** results/country_revenue.csv",
    ])

    text = "\n".join(lines) + "\n"

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "competitor_brief.md").write_text(text, encoding="utf-8")

    report = {
        "source_file": SOURCE.relative_to(ROOT).as_posix(),
        "method": "Evidence-scope check and fixed report template",
        "questions": questions,
        "limitation": limitation,
    }

    with (OUTPUT / "competitor_brief.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(text)
    print("Saved reports to:", OUTPUT)


if __name__ == "__main__":
    main()