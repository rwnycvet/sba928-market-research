"""Create a small fictional test set for the final model comparison."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "training_data_v2"


def make_record(family, instruction, context, target):
    return {
        "id": f"{family}_test_001",
        "task_family": family,
        "source_type": "synthetic",
        "source_group": f"synthetic_test_{family}_001",
        "split": "test",
        "instruction": instruction,
        "context": (
            "Fictional test scenario, not Online Retail findings. "
            + context
        ),
        "target": target,
    }


def main():
    records = [
        make_record(
            "consumer_behavior",
            "Calculate the repeat-customer percentage and explain which "
            "customers it describes.",
            "There are 80 identified customers. Of these, 28 have at least "
            "two distinct qualifying purchase invoices. Qualifying purchases "
            "are non-cancelled and have positive quantities and prices. "
            "Another 120 qualifying sales rows lack CustomerIDs; the number "
            "of customers represented by those rows is unknown.",
            "35% of identified customers have at least two qualifying "
            "purchase invoices. This percentage excludes unidentified "
            "customers and is not a retention rate for all customers.",
        ),
        make_record(
            "country_coverage",
            "State whether the fewer-than-five-customers warning applies "
            "and explain its limits.",
            "Geographic label: Sampleland. Identified customers: 3. "
            "Purchase invoices: 18. Apply the warning when identified "
            "customers are below five, regardless of invoice count. "
            "The warning is descriptive, not a statistical test.",
            "The warning applies because Sampleland has 3 identified "
            "customers, despite having 18 purchase invoices. This descriptive "
            "rule does not establish statistical significance or national "
            "representativeness.",
        ),
        make_record(
            "market_trends",
            "Can these totals establish a decline in full-month revenue? "
            "Recommend an appropriate comparison.",
            "Complete August 2025 positive sales revenue: GBP 24000.00. "
            "September 1 through September 10, 2025 positive sales revenue: "
            "GBP 11000.00. Remaining September revenue is unavailable. "
            "Other sales definitions and coverage are consistent.",
            "No, ten days of September cannot establish a decline in "
            "full-month revenue compared with all of August. Obtain complete "
            "September revenue or compare equivalent date ranges.",
        ),
        make_record(
            "product_demand",
            "Report the signed unit balance and assess whether these sales "
            "alone justify increasing inventory.",
            "Product: Display Stand C. Positive units: 2750. Cancelled "
            "units: 2750. Cancellations fully offset the positive purchases. "
            "Current stock and supplier lead times are unavailable.",
            "The signed balance is zero units because all 2750 positive "
            "units are offset by cancellations. These sales alone do not "
            "justify increasing inventory; review the transactions and "
            "inventory information before deciding replenishment.",
        ),
        make_record(
            "competitor_research",
            "Identify which retailer reports higher revenue and by how much. "
            "Limit the conclusion to the supplied evidence.",
            "Retailer E reports GBP 14500.00 and Retailer F reports GBP "
            "17200.00. Both figures cover the complete first quarter of "
            "2025, the same product category and country, and use the same "
            "revenue definition before returns and cancellations. "
            "Total-market sales are unavailable.",
            "Retailer F reports GBP 2700.00 more revenue than Retailer E "
            "within the matched comparison. This does not establish overall "
            "market leadership or market share.",
        ),
    ]

    existing = []
    for filename in ("train.jsonl", "validation.jsonl"):
        with (DATA / filename).open(encoding="utf-8") as file:
            existing.extend(
                json.loads(line) for line in file if line.strip()
            )

    existing_ids = {record["id"] for record in existing}
    existing_groups = {record["source_group"] for record in existing}

    test_ids = [record["id"] for record in records]
    test_groups = [record["source_group"] for record in records]

    if len(set(test_ids)) != len(test_ids):
        raise ValueError("Duplicate test IDs.")

    if existing_ids.intersection(test_ids):
        raise ValueError("Test IDs overlap with training or validation.")

    if existing_groups.intersection(test_groups):
        raise ValueError("Test groups overlap with training or validation.")

    output = DATA / "test.jsonl"
    if output.exists():
        raise FileExistsError(
            "test.jsonl already exists. Review it before replacing "
            "the reserved test set."
        )

    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("Test examples:", len(records))
    print("Test ID overlap with training/validation: 0")
    print("Test group overlap with training/validation: 0")
    print("Saved:", output)


if __name__ == "__main__":
    main()