"""Prepare fictional monthly-trend examples with computed evidence."""

import json
import random
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "training_data_v3"
OUTPUT.mkdir(exist_ok=True)

INSTRUCTIONS = [
    "Summarize the monthly revenue comparison in two sentences. "
    "Use the supplied calculated change when months are complete "
    "and include one planning recommendation.",

    "Explain whether these figures support a full-month revenue "
    "comparison. Report any supplied calculated change and "
    "recommend an appropriate planning action.",
]

CASE_TYPES = ["increase", "decrease", "unchanged", "partial"]
PENNY = Decimal("0.01")


def main():
    records = []
    seen_evidence = set()

    settings = [
        ("train", 64, 948),
        ("validation", 16, 949),
        ("test", 16, 950),
    ]

    for split, scenario_count, seed in settings:
        rng = random.Random(seed)

        for number in range(scenario_count):
            case_type = CASE_TYPES[number % len(CASE_TYPES)]

            while True:
                previous_pence = rng.randint(10000, 5000000)
                movement = rng.randint(1, previous_pence // 2)

                if case_type == "increase":
                    current_pence = previous_pence + movement
                elif case_type == "unchanged":
                    current_pence = previous_pence
                else:
                    current_pence = previous_pence - movement

                evidence_key = (
                    case_type, previous_pence, current_pence
                )

                if evidence_key not in seen_evidence:
                    seen_evidence.add(evidence_key)
                    break

            previous = Decimal(previous_pence) / 100
            current = Decimal(current_pence) / 100
            group = f"trends_v3_{split}_{number:03d}"

            context = (
                "Fictional teaching scenario, not Online Retail findings. "
                f"Previous month's positive sales revenue: "
                f"GBP {previous:.2f}; complete month. "
                f"Current month's positive sales revenue: "
                f"GBP {current:.2f}. "
                "Both totals describe the same retailer, product "
                "categories and countries. Revenue is before "
                "deductions for returns and cancellations. "
            )

            change = None
            percent = None

            if case_type == "partial":
                context += (
                    "Current-month coverage: first ten days only. "
                    "Remaining current-month sales are unavailable. "
                    "A full-month change has not been calculated "
                    "because coverage differs."
                )

                target = (
                    "The partial current month does not establish "
                    "a decline in full-month revenue. "
                    "Recommendation: obtain complete-month figures "
                    "or compare equivalent date ranges."
                )
            else:
                change = current - previous
                percent = (
                    change / previous * 100
                ).quantize(PENNY, rounding=ROUND_HALF_UP)

                context += (
                    "Current-month coverage: complete month. "
                    f"Python-calculated revenue change: "
                    f"GBP {change:.2f}. "
                    f"Python-calculated percentage change: "
                    f"{percent:.2f}%."
                )

                if case_type == "unchanged":
                    finding = (
                        "Recorded positive sales revenue was unchanged "
                        "between the two complete months."
                    )
                else:
                    direction = (
                        "increased"
                        if case_type == "increase"
                        else "decreased"
                    )
                    finding = (
                        f"Recorded positive sales revenue {direction} "
                        f"by GBP {abs(change):.2f} "
                        f"({abs(percent):.2f}%) between complete months."
                    )

                target = (
                    f"{finding} "
                    "Recommendation: review inventory timing using "
                    "this comparison without assuming a recurring "
                    "seasonal pattern."
                )

            for variant, instruction in enumerate(
                INSTRUCTIONS, start=1
            ):
                records.append({
                    "id": f"{group}_variant_{variant}",
                    "task_family": "market_trends",
                    "source_type": "synthetic",
                    "source_group": group,
                    "split": split,
                    "instruction": instruction,
                    "context": context,
                    "target": target,
                    "case_type": case_type,
                    "previous_revenue_gbp": f"{previous:.2f}",
                    "current_revenue_gbp": f"{current:.2f}",
                    "computed_change_gbp": (
                        f"{change:.2f}" if change is not None else None
                    ),
                    "computed_change_percent": (
                        f"{percent:.2f}" if percent is not None else None
                    ),
                })

    output_file = OUTPUT / "trend_cases.jsonl"

    if output_file.exists():
        raise FileExistsError(
            "trend_cases.jsonl already exists. Review before replacing."
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