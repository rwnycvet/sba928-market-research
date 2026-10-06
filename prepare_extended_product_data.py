"""Prepare fictional product examples with calculated unit balances."""

import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "training_data_v3"
OUTPUT.mkdir(exist_ok=True)

INSTRUCTIONS = [
    "Report the calculated signed unit balance and recommend one "
    "inventory action. Do not specify an exact reorder quantity.",

    "Explain the supplied product figures and propose an inventory "
    "planning action. Use the calculated balance and acknowledge "
    "the missing inventory information.",
]

CASE_TYPES = [
    "zero_balance",
    "partial_reversal",
    "no_reversals",
    "negative_balance",
]


def main():
    records = []
    seen_evidence = set()

    settings = [
        ("train", 64, 958),
        ("validation", 16, 959),
        ("test", 16, 960),
    ]

    for split, scenario_count, seed in settings:
        rng = random.Random(seed)

        for number in range(scenario_count):
            case_type = CASE_TYPES[number % len(CASE_TYPES)]

            while True:
                positive = rng.randint(100, 10000)

                if case_type == "zero_balance":
                    reversals = positive
                elif case_type == "partial_reversal":
                    reversals = rng.randint(1, positive - 1)
                elif case_type == "no_reversals":
                    reversals = 0
                else:
                    reversals = positive + rng.randint(1, positive)

                evidence_key = (positive, reversals)

                if evidence_key not in seen_evidence:
                    seen_evidence.add(evidence_key)
                    break

            signed = positive - reversals
            group = f"product_v3_{split}_{number:03d}"

            context = (
                "Fictional teaching scenario, not Online Retail findings. "
                "Product: Demonstration Storage Box. "
                f"Positive units sold: {positive}. "
                f"Recorded reversal units: {reversals}. "
                f"Python-calculated signed unit balance: {signed}. "
                "The balance subtracts reversal units from positive units. "
                "Reversals have not been matched to original purchases "
                "and may relate to purchases outside the recorded period. "
                "Current stock, supplier lead times and demand lost "
                "through stockouts are unavailable."
            )

            if signed == 0:
                target = (
                    "The recorded signed unit balance is zero. "
                    "Recommendation: review transaction reversals before "
                    "considering replenishment; an exact reorder quantity "
                    "requires stock levels and supplier lead times."
                )
            elif signed < 0:
                target = (
                    f"The recorded signed unit balance is {signed}, "
                    "because reversal units exceed positive units "
                    "during the recorded period. "
                    "Recommendation: review transaction timing and "
                    "matching before considering replenishment; "
                    "stock levels and supplier lead times are missing."
                )
            else:
                target = (
                    f"The recorded signed unit balance is {signed} "
                    "after reversal deductions. "
                    "Recommendation: review stock levels, supplier lead "
                    "times and sales timing before deciding replenishment; "
                    "recorded sales do not measure demand lost "
                    "through stockouts."
                )

            for variant, instruction in enumerate(
                INSTRUCTIONS, start=1
            ):
                records.append({
                    "id": f"{group}_variant_{variant}",
                    "task_family": "product_demand",
                    "source_type": "synthetic",
                    "source_group": group,
                    "split": split,
                    "instruction": instruction,
                    "context": context,
                    "target": target,
                    "case_type": case_type,
                    "positive_units": positive,
                    "reversal_units": reversals,
                    "computed_signed_units": signed,
                })

    output_file = OUTPUT / "product_cases.jsonl"

    if output_file.exists():
        raise FileExistsError(
            "product_cases.jsonl already exists. Review before replacing."
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