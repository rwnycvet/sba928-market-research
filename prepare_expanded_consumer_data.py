"""Prepare fictional consumer-behavior examples with computed evidence."""

import json
import random
from collections import Counter
from pathlib import Path

from evidence_rules import repeat_customer_percentage

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "training_data_v3"
OUTPUT.mkdir(exist_ok=True)

INSTRUCTIONS = [
    "Report the supplied repeat-purchase percentage and explain "
    "which customers it describes. Answer in two sentences.",

    "Summarize repeat purchasing from the supplied evidence. "
    "Include the percentage, its population and one limitation "
    "in two sentences.",
]


def main():
    records = []
    seen_evidence = set()

    settings = [
        ("train", 64, 938),
        ("validation", 16, 939),
        ("test", 16, 940),
    ]

    for split, scenario_count, seed in settings:
        rng = random.Random(seed)

        for number in range(scenario_count):
            while True:
                identified = rng.randint(20, 2000)
                repeat = rng.randint(0, identified)

                # Half have missing-ID rows; half have none recorded.
                missing_rows = (
                    rng.randint(1, 500)
                    if number % 2 == 0
                    else 0
                )

                evidence_key = (identified, repeat, missing_rows)

                if evidence_key not in seen_evidence:
                    seen_evidence.add(evidence_key)
                    break

            percentage = repeat_customer_percentage(
                identified, repeat
            )

            group = f"consumer_v3_{split}_{number:03d}"

            context = (
                "Fictional teaching scenario, not Online Retail findings. "
                f"Identified customers: {identified}. "
                f"Customers with at least two distinct qualifying "
                f"purchase invoices: {repeat}. "
                f"Repeat-purchase percentage calculated by Python: "
                f"{percentage:.2f}%. "
                f"Qualifying sales rows without CustomerIDs: "
                f"{missing_rows}. "
                "Qualifying purchases are non-cancelled and have "
                "positive quantities and prices. "
                "Customers without recorded IDs are not included "
                "in the customer-level calculation."
            )

            target = (
                f"Among identified customers, {percentage:.2f}% had "
                "at least two distinct qualifying purchase invoices. "
                "This describes repeat purchasing during the recorded "
                "period and is not a retention rate for all customers."
            )

            for variant, instruction in enumerate(
                INSTRUCTIONS, start=1
            ):
                records.append({
                    "id": f"{group}_variant_{variant}",
                    "task_family": "consumer_behavior",
                    "source_type": "synthetic",
                    "source_group": group,
                    "split": split,
                    "instruction": instruction,
                    "context": context,
                    "target": target,
                    "identified_customers": identified,
                    "repeat_customers": repeat,
                    "missing_customer_id_rows": missing_rows,
                    "computed_repeat_percent": percentage,
                })

    output_file = OUTPUT / "consumer_cases.jsonl"

    if output_file.exists():
        raise FileExistsError(
            "consumer_cases.jsonl already exists. "
            "Review before replacing."
        )

    with output_file.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    counts = Counter(record["split"] for record in records)

    for split in ("train", "validation", "test"):
        print(f"{split}: {counts[split]} examples")

    print("Total examples:", len(records))
    print("Saved:", output_file)


if __name__ == "__main__":
    main()