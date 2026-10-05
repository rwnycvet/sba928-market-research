"""Create fictional validation examples without adding them to training."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "training_data_v2"


def make_record(family, instruction, context, target):
    return {
        "id": f"{family}_validation_001",
        "task_family": family,
        "source_type": "synthetic",
        "source_group": f"synthetic_validation_{family}_001",
        "split": "validation",
        "instruction": instruction,
        "context": (
            "Fictional validation scenario, not Online Retail findings. "
            + context
        ),
        "target": target,
    }


def main():
    records = [
        make_record(
            "consumer_behavior",
            "Report this customer's distinct purchase-invoice count and "
            "whether they qualify as a repeat customer.",
            "CustomerID: DEMO072. Four qualifying product rows have invoice "
            "numbers P701, P702, P702 and P703. All are positive, non-cancelled "
            "purchases. A repeat customer has at least two distinct qualifying "
            "purchase invoices during the recorded period.",
            "Customer DEMO072 has three distinct qualifying purchase invoices "
            "and meets the repeat-customer definition during the recorded "
            "period. This does not establish purchasing motives or loyalty.",
        ),
        make_record(
            "country_coverage",
            "Apply the fewer-than-five-customers warning and state one "
            "limitation without changing the geographic label.",
            "Geographic label: Unspecified. Identified customers: 8. Apply "
            "the descriptive warning only when identified customers are "
            "below five. These records describe one retailer; Unspecified "
            "does not identify a known country.",
            "The warning does not apply because Unspecified has 8 identified "
            "customers. The geographic label is unknown, so these records "
            "cannot support a conclusion about a particular country's demand.",
        ),
        make_record(
            "market_trends",
            "Calculate the change in recorded positive sales revenue and "
            "state one limitation.",
            "Complete June 2025 revenue: GBP 15000.00. Complete July 2025 "
            "revenue: GBP 18000.00. Both totals use matching retailer, category, "
            "country and revenue definitions, before returns and cancellations.",
            "Positive sales revenue increased by GBP 3000.00, or 20%, from "
            "June to July 2025. Two monthly totals do not establish the cause "
            "or prove a recurring seasonal pattern.",
        ),
        make_record(
            "product_demand",
            "Report the signed unit balance and recommend one inventory "
            "planning action without an exact reorder quantity.",
            "Product: Desk Tray B. Positive units: 640. Cancelled units: 160. "
            "Signed units including cancellations: 480. Stock levels, supplier "
            "lead times and demand lost through stockouts are unknown.",
            "The signed balance is 480 units after accounting for 160 "
            "cancelled units. Review stock levels and supplier lead times "
            "against the timing of sales before deciding replenishment; "
            "the evidence does not establish an exact reorder quantity.",
        ),
        make_record(
            "competitor_research",
            "Can these figures establish which retailer has higher comparable "
            "sales revenue? Identify any additional evidence needed.",
            "Retailer C reports GBP 9000.00 and Retailer D reports EUR "
            "11000.00 for the same complete month, product category and "
            "country, using the same treatment of returns and cancellations. "
            "No exchange rate or currency-conversion method is supplied.",
            "The figures do not establish a comparable revenue ranking "
            "because they use different currencies. Convert them to a common "
            "currency using an appropriate documented exchange-rate method "
            "before comparing.",
        ),
    ]

    with (DATA / "train.jsonl").open(encoding="utf-8") as file:
        training = [json.loads(line) for line in file if line.strip()]

    training_ids = {record["id"] for record in training}
    training_groups = {record["source_group"] for record in training}

    for record in records:
        if record["id"] in training_ids:
            raise ValueError("A validation ID also appears in training.")
        if record["source_group"] in training_groups:
            raise ValueError("A validation source group also appears in training.")

    output = DATA / "validation.jsonl"
    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("Validation examples:", len(records))
    print("Training/validation ID overlap: 0")
    print("Training/validation source-group overlap: 0")
    print("Saved:", output)


if __name__ == "__main__":
    main()