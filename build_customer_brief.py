"""Build a customer brief from measured evidence and Python calculations."""

import csv
import json
from pathlib import Path

from evidence_rules import repeat_customer_percentage

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results" / "customer_purchase_summary.csv"
OUTPUT = ROOT / "results_v3" / "verified_reports"


def main():
    with SOURCE.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    if len(rows) != 1:
        raise ValueError("Expected exactly one customer-summary row.")

    row = rows[0]
    identified = int(row["IdentifiedCustomers"])
    repeat = int(row["RepeatCustomers"])
    single = int(row["SingleInvoiceCustomers"])

    if single + repeat != identified:
        raise ValueError("Customer counts do not reconcile.")

    percentage = repeat_customer_percentage(identified, repeat)

    if percentage is None:
        finding = (
            "No identified customers are available, so a "
            "repeat-customer percentage cannot be calculated."
        )
    else:
        finding = (
            f"{repeat:,} of {identified:,} identified customers "
            f"({percentage:.2f}%) had at least two distinct "
            "qualifying purchase invoices during the recorded period."
        )

    limitation = (
        "This calculation excludes purchases without CustomerIDs. "
        "It describes repeat purchasing among identified customers "
        "and is not a retention rate for all customers."
    )

    recommendation = (
        "Review purchase intervals and product choices among "
        "identified repeat customers before designing a marketing test."
        if identified > 0
        else "Improve customer identification before analyzing repeat purchasing."
    )

    report = {
        "source_file": SOURCE.relative_to(ROOT).as_posix(),
        "method": "Python calculation and fixed report template",
        "identified_customers": identified,
        "repeat_customers": repeat,
        "single_invoice_customers": single,
        "repeat_customer_percent": percentage,
        "finding": finding,
        "limitation": limitation,
        "recommendation": recommendation,
    }

    text = (
        "# Customer Purchasing Brief\n\n"
        f"**Measured finding:** {finding}\n\n"
        f"**Limitation:** {limitation}\n\n"
        f"**Recommendation:** {recommendation}\n\n"
        f"**Evidence source:** {report['source_file']}\n"
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)

    with (OUTPUT / "customer_brief.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    (OUTPUT / "customer_brief.md").write_text(text, encoding="utf-8")

    print(text)
    print("Saved reports to:", OUTPUT)


if __name__ == "__main__":
    main()