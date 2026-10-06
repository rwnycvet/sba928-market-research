"""Prepare fictional competitor comparisons with verified calculations."""

import json
import random
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "training_data_v3"
OUTPUT.mkdir(exist_ok=True)

INSTRUCTIONS = [
    "Explain whether the evidence supports a fair revenue comparison. "
    "If supported, report the supplied comparison; otherwise state "
    "what additional evidence is needed.",

    "Prepare a concise competitor brief using only this evidence. "
    "Report the verified comparison or explain why a comparison "
    "cannot be made. Avoid claims about overall market leadership.",
]

INVALID_CASES = [
    "different_periods",
    "different_categories",
    "different_countries",
    "different_currencies",
    "missing_competitor_revenue",
]

LIMITATIONS = {
    "different_periods": (
        "The reporting periods differ. Obtain sales for matching dates."
    ),
    "different_categories": (
        "The product categories differ. Obtain sales for matching categories."
    ),
    "different_countries": (
        "The countries differ. Obtain sales for matching countries."
    ),
    "different_currencies": (
        "The currencies differ. Convert both figures to a common currency "
        "using an appropriate documented exchange-rate method."
    ),
    "missing_competitor_revenue": (
        "Retailer B's revenue is unavailable. Obtain comparable "
        "competitor revenue for matching dates, categories and countries."
    ),
}


def main():
    records = []
    seen_evidence = set()

    settings = [
        ("train", 64, 968),
        ("validation", 16, 969),
        ("test", 16, 970),
    ]

    for split, scenario_count, seed in settings:
        rng = random.Random(seed)

        for number in range(scenario_count):
            supported = number % 2 == 0
            case_type = (
                "comparable"
                if supported
                else INVALID_CASES[
                    (number // 2) % len(INVALID_CASES)
                ]
            )

            while True:
                first_pence = rng.randint(100000, 10000000)
                movement = rng.randint(1, first_pence // 2)

                if supported:
                    outcome = (number // 2) % 3
                    second_pence = (
                        first_pence - movement
                        if outcome == 0
                        else first_pence + movement
                        if outcome == 1
                        else first_pence
                    )
                else:
                    second_pence = rng.randint(100000, 10000000)

                evidence_key = (
                    case_type, first_pence, second_pence
                )

                if evidence_key not in seen_evidence:
                    seen_evidence.add(evidence_key)
                    break

            first = Decimal(first_pence) / 100
            second = Decimal(second_pence) / 100
            group = f"competitor_v3_{split}_{number:03d}"

            currency_b = (
                "EUR" if case_type == "different_currencies" else "GBP"
            )

            second_figure = (
                "unavailable"
                if case_type == "missing_competitor_revenue"
                else f"{currency_b} {second:.2f}"
            )

            context = (
                "Fictional teaching scenario, not Online Retail findings. "
                f"Retailer A revenue: GBP {first:.2f}. "
                f"Retailer B revenue: {second_figure}. "
                "Retailer A coverage: complete May 2025, "
                "household storage products, United Kingdom. "
            )

            period_b = (
                "May 1 through May 15, 2025"
                if case_type == "different_periods"
                else "complete May 2025"
            )
            category_b = (
                "toys"
                if case_type == "different_categories"
                else "household storage products"
            )
            country_b = (
                "Germany"
                if case_type == "different_countries"
                else "United Kingdom"
            )

            context += (
                f"Retailer B coverage: {period_b}, "
                f"{category_b}, {country_b}. "
                "Both use revenue before return and cancellation "
                "deductions. Total-market sales are unavailable. "
            )

            difference = None
            higher = None

            if supported:
                difference = abs(first - second)

                if first == second:
                    higher = "tie"
                    comparison = (
                        "Both retailers report equal revenue "
                        "within the matched comparison."
                    )
                else:
                    higher = (
                        "Retailer A" if first > second else "Retailer B"
                    )
                    comparison = (
                        f"{higher} reports GBP {difference:.2f} "
                        "more revenue within the matched comparison."
                    )

                context += f"Python-calculated comparison: {comparison}"

                target = (
                    f"Yes, the figures are comparable; {comparison} "
                    "This does not establish overall market leadership "
                    "or market share."
                )
            else:
                target = (
                    "The evidence does not support a fair revenue "
                    f"comparison. {LIMITATIONS[case_type]}"
                )

            for variant, instruction in enumerate(
                INSTRUCTIONS, start=1
            ):
                records.append({
                    "id": f"{group}_variant_{variant}",
                    "task_family": "competitor_research",
                    "source_type": "synthetic",
                    "source_group": group,
                    "split": split,
                    "instruction": instruction,
                    "context": context,
                    "target": target,
                    "case_type": case_type,
                    "comparison_supported": supported,
                    "computed_higher_retailer": higher,
                    "computed_difference_gbp": (
                        f"{difference:.2f}"
                        if difference is not None
                        else None
                    ),
                })

    output_file = OUTPUT / "competitor_cases.jsonl"

    if output_file.exists():
        raise FileExistsError(
            "competitor_cases.jsonl already exists. "
            "Review before replacing."
        )

    with output_file.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    counts = Counter(record["split"] for record in records)

    for split in ("train", "validation", "test"):
        supported_count = sum(
            record["comparison_supported"]
            for record in records
            if record["split"] == split
        )
        unsupported_count = counts[split] - supported_count

        print(
            f"{split}: {counts[split]} examples "
            f"(Supported: {supported_count}, "
            f"Unsupported: {unsupported_count})"
        )

    print("Total examples:", len(records))
    print("Saved:", output_file)


if __name__ == "__main__":
    main()