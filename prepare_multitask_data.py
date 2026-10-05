"""Prepare multiple market-research task families for SBA 928."""

from pathlib import Path
import csv
import json

# Resolve paths relative to this script.
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results"
DESTINATION = ROOT / "training_data_v2"

# Each task family needs its own evidence and evaluation criteria.
TASK_FAMILIES = {
    "consumer_behavior": ["customer_purchase_summary.csv"],
    "market_trends": ["monthly_revenue.csv"],
    "product_demand": [
        "product_summary.csv",
        "top_five_cancellation_review.csv",
    ],
    "country_coverage": [
        "country_revenue.csv",
        "country_coverage.csv",
    ],
    "competitor_research": [],
}


def main():
    """Check that the required evidence files exist."""
    missing = []

    for family, filenames in TASK_FAMILIES.items():
        print(f"\nTask family: {family}")

        if not filenames:
            print("Scope: identify missing competitor evidence.")
            continue

        for filename in filenames:
            path = SOURCE / filename
            if path.is_file():
                print(f"  Found: {filename}")
            else:
                missing.append(filename)
                print(f"  MISSING: {filename}")

    if missing:
        raise FileNotFoundError(
            "Required evidence is missing: " + ", ".join(missing)
        )

    DESTINATION.mkdir(exist_ok=True)
    print("\nEvidence checks passed.")
    print("New dataset folder:", DESTINATION)
        # Read the actual customer summary rather than hardcode its figures.
    source_file = SOURCE / "customer_purchase_summary.csv"
    with source_file.open(encoding="utf-8-sig", newline="") as file:
        summary = next(csv.DictReader(file))

    customers = int(summary["IdentifiedCustomers"])
    repeat_customers = int(summary["RepeatCustomers"])
    repeat_percent = float(summary["RepeatCustomerPercent"])

    record = {
        "id": "consumer_behavior_real_001",
        "task_family": "consumer_behavior",
        "source_type": "real_data_summary",
        "source_group": "uci_online_retail_customer_summary",
        "source_files": ["results/customer_purchase_summary.csv"],
        "instruction": (
            "Report the repeat-customer percentage and explain "
            "which customers it describes. Answer in two sentences."
        ),
        "context": (
            f"Identified customers: {customers}. "
            f"Customers with at least two qualifying purchase invoices: "
            f"{repeat_customers}. "
            f"Repeat-customer percentage: {repeat_percent:.2f}%. "
            "Only positive, non-cancelled purchase rows are included. "
            "Rows without CustomerIDs are excluded from this calculation."
        ),
        "target": (
            f"{repeat_percent:.2f}% of identified customers had at least "
            "two qualifying purchase invoices during the recorded period. "
            "This describes customers with recorded IDs and is not "
            "a retention rate for all customers."
        ),
        "split": "train",
    }

    output_file = DESTINATION / "example_preview.json"
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(record, file, indent=2, ensure_ascii=False)

    print("\nFIRST TRAINING RECORD")
    print(json.dumps(record, indent=2, ensure_ascii=False))
        # Read the monthly summary and select the incomplete month.
    monthly_file = SOURCE / "monthly_revenue.csv"
    with monthly_file.open(encoding="utf-8-sig", newline="") as file:
        monthly_rows = list(csv.DictReader(file))

    december = next(
        row for row in monthly_rows
        if row["Month"] == "2011-12"
    )

    trend_record = {
        "id": "market_trends_real_001",
        "task_family": "market_trends",
        "source_type": "real_data_summary",
        "source_group": "uci_online_retail_monthly_summary",
        "source_files": ["results/monthly_revenue.csv"],
        "instruction": (
            "Can this month's total establish a decline from "
            "the previous complete month? Explain in two sentences."
        ),
        "context": (
            f"Month: {december['Month']}. "
            f"Positive sales revenue: GBP "
            f"{float(december['SalesRevenue']):.2f}. "
            f"Coverage: {december['DataCoverage']}. "
            "The preceding month covers a full calendar month."
        ),
        "target": (
            "No, December 2011 contains data only through December 9, "
            "so its total is not directly comparable with a full month. "
            "Compare equivalent periods before concluding that sales declined."
        ),
        "split": "train",
    }

    # Save both examples as JSONL: one complete record per line.
        # Read the cancellation review for the highest positive-sales product.
    review_file = SOURCE / "top_five_cancellation_review.csv"
    with review_file.open(encoding="utf-8-sig", newline="") as file:
        product_rows = list(csv.DictReader(file))

    product = next(
        row for row in product_rows
        if row["StockCode"] == "23843"
    )

    product_record = {
        "id": "product_demand_real_001",
        "task_family": "product_demand",
        "source_type": "real_data_summary",
        "source_group": "uci_online_retail_product_23843",
        "source_files": [
            "results/top_five_cancellation_review.csv"
        ],
        "instruction": (
            "Does this evidence justify increasing inventory? "
            "Explain in two sentences."
        ),
        "context": (
            f"Product code: {product['StockCode']}. "
            f"Description: {product['Description']}. "
            f"Positive units sold: {product['UnitsSold']}. "
            "Signed units including cancellations: "
            f"{product['SignedUnitsIncludingCancellations']}. "
            "Current stock and supplier lead times are unavailable."
        ),
        "target": (
            "The 80,995 positive units are offset by cancellations, "
            "leaving a recorded balance of zero units. "
            "This evidence alone does not justify increasing inventory; "
            "review transaction history, current stock and supplier lead times."
        ),
        "split": "train",
    }

    print("\nPRODUCT DEMAND RECORD")
    print(json.dumps(product_record, indent=2, ensure_ascii=False))

        # Use Germany to teach correct application of the coverage rule.
    coverage_file = SOURCE / "country_coverage.csv"
    with coverage_file.open(encoding="utf-8-sig", newline="") as file:
        coverage_rows = list(csv.DictReader(file))

    germany = next(
        row for row in coverage_rows
        if row["Country"] == "Germany"
    )
    identified_count = int(germany["IdentifiedCustomers"])

    if identified_count < 5:
        raise ValueError("This example expects at least five customers.")

    country_record = {
        "id": "country_coverage_real_001",
        "task_family": "country_coverage",
        "source_type": "real_data_summary",
        "source_group": "uci_online_retail_country_Germany",
        "source_files": ["results/country_coverage.csv"],
        "instruction": (
            "Does the fewer-than-five-identified-customers warning apply? "
            "Answer in two sentences and state one remaining limitation."
        ),
        "context": (
            f"Country: Germany. "
            f"Identified customers: {identified_count}. "
            f"Purchase invoices: {germany['PurchaseInvoices']}. "
            "Apply the warning only when identified customers are below five. "
            "This is a descriptive teaching rule, not a statistical test. "
            "The records come from one retailer."
        ),
        "target": (
            f"No, Germany has {identified_count} identified customers, "
            "so the fewer-than-five warning does not apply. "
            "These records describe one retailer and do not establish "
            "national demand or population representativeness."
        ),
        "split": "train",
    }

    print("\nCOUNTRY COVERAGE RECORD")
    print(json.dumps(country_record, indent=2, ensure_ascii=False))

    competitor_record = {
        "id": "competitor_research_real_001",
        "task_family": "competitor_research",
        "source_type": "real_data_scope",
        "source_group": "uci_online_retail_competitor_scope",
        "source_files": ["results/country_revenue.csv"],
        "instruction": (
            "Can this evidence establish whether the retailer outsells "
            "its competitors? Answer in two sentences and identify "
            "the additional evidence needed."
        ),
        "context": (
            "The supplied country revenue summary describes one retailer. "
            "It contains no competitor sales figures or total-market sales. "
            "Revenue represents positive sales before deductions "
            "for returns and cancellations."
        ),
        "target": (
            "No, one retailer's country sales cannot establish whether "
            "it outsells competitors or determine its market share. "
            "Obtain comparable competitor sales for matching time periods, "
            "product categories and countries, using consistent currencies "
            "and treatment of returns and cancellations."
        ),
        "split": "train",
    }

    print("\nCOMPETITOR RESEARCH RECORD")
    print(json.dumps(competitor_record, indent=2, ensure_ascii=False))

    records = [
        record,
        trend_record,
        product_record,
        country_record,
        competitor_record,
    ]
        # Validate the reviewed examples before saving them.
    required_strings = [
        "id",
        "task_family",
        "source_type",
        "source_group",
        "instruction",
        "context",
        "target",
        "split",
    ]

    seen_ids = set()
    family_counts = {}

    for example in records:
        for field in required_strings:
            value = example.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Missing or empty field: {field}")

        if example["id"] in seen_ids:
            raise ValueError(f"Duplicate example ID: {example['id']}")
        seen_ids.add(example["id"])

        family = example["task_family"]
        if family not in TASK_FAMILIES:
            raise ValueError(f"Unknown task family: {family}")

        # These examples have already been reviewed, so keep them in training.
        if example["split"] != "train":
            raise ValueError("Reviewed examples must remain in training.")

        sources = example.get("source_files")
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"Missing sources for {example['id']}")

        for source in sources:
            if not (ROOT / source).is_file():
                raise FileNotFoundError(source)

        family_counts[family] = family_counts.get(family, 0) + 1

    if set(family_counts) != set(TASK_FAMILIES):
        raise ValueError("At least one task family is missing.")

    print("\nDATASET CHECKS PASSED")
    print("Unique example IDs:", len(seen_ids))
    for family, count in family_counts.items():
        print(f"{family}: {count}")
    output_file = DESTINATION / "real_examples.jsonl"

    with output_file.open("w", encoding="utf-8") as file:
        for example in records:
            file.write(json.dumps(example, ensure_ascii=False) + "\n")

    print("\nMARKET TREND RECORD")
    print(json.dumps(trend_record, indent=2, ensure_ascii=False))
    print("\nSaved training examples:", len(records))

if __name__ == "__main__":
    main()