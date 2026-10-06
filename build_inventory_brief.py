"""Build an inventory brief from the saved cancellation review."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results" / "top_five_cancellation_review.csv"
OUTPUT = ROOT / "results_v3" / "verified_reports"


def main():
    with SOURCE.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    if len(rows) != 5:
        raise ValueError("Expected five products in the cancellation review.")

    products = []

    for row in rows:
        positive = int(row["UnitsSold"])
        signed = int(row["SignedUnitsIncludingCancellations"])

        if positive <= 0:
            raise ValueError("Positive units sold must exceed zero.")

        if signed <= 0:
            recommendation = (
                "Review transaction reversals before considering "
                "replenishment; the recorded signed balance is "
                "zero or negative."
            )
        else:
            recommendation = (
                "Review the difference between positive and signed units, "
                "current stock and supplier lead times before "
                "setting replenishment."
            )

        products.append({
            "stock_code": row["StockCode"],
            "description": (
                row["Description"].strip() or "Description unavailable"
            ),
            "positive_units": positive,
            "signed_units": signed,
            "recommendation": recommendation,
        })

    limitation = (
        "Positive units measure sales before reversal deductions. "
        "Signed balances include negative quantities in the prepared "
        "priced records; they do not prove that every reversal has been "
        "matched to its original purchase. Stock levels, supplier lead "
        "times and demand lost through stockouts are unavailable, so "
        "exact reorder quantities cannot be determined."
    )

    lines = [
        "# Inventory Brief",
        "",
        "Measured units come from the saved product review. "
        "Inventory actions are recommendations.",
        "",
        "| Product | Positive Units | Signed Units | Recommendation |",
        "|---|---:|---:|---|",
    ]

    for product in products:
        name = (
            f"{product['stock_code']} — {product['description']}"
        ).replace("|", "/")

        lines.append(
            f"| {name} | {product['positive_units']:,} | "
            f"{product['signed_units']:,} | "
            f"{product['recommendation']} |"
        )

    lines.extend([
        "",
        f"**Limitation:** {limitation}",
        "",
        "**Evidence source:** results/top_five_cancellation_review.csv",
    ])

    text = "\n".join(lines) + "\n"

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "inventory_brief.md").write_text(text, encoding="utf-8")

    report = {
        "source_file": SOURCE.relative_to(ROOT).as_posix(),
        "method": "Saved measurements and fixed report template",
        "products": products,
        "limitation": limitation,
    }

    with (OUTPUT / "inventory_brief.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(text)
    print("Saved reports to:", OUTPUT)


if __name__ == "__main__":
    main()