"""Prepare fictional country-coverage examples for an expanded dataset."""

import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "training_data_v3"
OUTPUT.mkdir(exist_ok=True)

LABELS = ["Germany", "Brazil", "Unspecified", "Sampleland"]

INSTRUCTIONS = [
    "Does the fewer-than-five-customer warning apply? "
    "Answer Yes or No, state the customer count and one limitation.",

    "Apply the descriptive customer-count rule to this evidence. "
    "State whether the warning applies, explain why and give one limitation.",
]


def main():
    records = []
    seen_evidence = set()

    # Each scenario receives two instruction variations.
    settings = [
        ("train", 64, 928),
        ("validation", 16, 929),
        ("test", 16, 930),
    ]

    for split, scenario_count, seed in settings:
        rng = random.Random(seed)

        for number in range(scenario_count):
            # Half the scenarios require Yes; half require No.
            expected_warning = number % 2 == 0

            while True:
                count = (
                    rng.randint(0, 4)
                    if expected_warning
                    else rng.randint(5, 100)
                )
                label = rng.choice(LABELS)
                invoices = rng.randint(max(1, count), 500)

                evidence_key = (label, count, invoices)

                if evidence_key not in seen_evidence:
                    seen_evidence.add(evidence_key)
                    break

            group = f"country_v3_{split}_{number:03d}"

            context = (
                "Fictional teaching scenario, not Online Retail findings. "
                f"Geographic label: {label}. "
                f"Identified customers: {count}. "
                f"Purchase invoices: {invoices}. "
                "Apply the warning only when identified customers "
                "are below five, regardless of invoice count. "
                "This is a descriptive rule, not a statistical test. "
                "The records describe one retailer."
            )

            if expected_warning:
                target = (
                    f"Yes, the warning applies because there are "
                    f"{count} identified customers, fewer than five. "
                    "These records do not establish national "
                    "demand or population representativeness."
                )
            else:
                target = (
                    f"No, the warning does not apply because there are "
                    f"{count} identified customers, at least five. "
                    "These records do not establish national "
                    "demand or population representativeness."
                )

            for variant, instruction in enumerate(
                INSTRUCTIONS, start=1
            ):
                records.append({
                    "id": f"{group}_variant_{variant}",
                    "task_family": "country_coverage",
                    "source_type": "synthetic",
                    "source_group": group,
                    "split": split,
                    "instruction": instruction,
                    "context": context,
                    "target": target,
                    "expected_warning": expected_warning,
                })

    output_file = OUTPUT / "country_cases.jsonl"

    if output_file.exists():
        raise FileExistsError(
            "country_cases.jsonl already exists. Review before replacing."
        )

    with output_file.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    counts = Counter(record["split"] for record in records)

    for split in ("train", "validation", "test"):
        yes_count = sum(
            record["expected_warning"]
            for record in records
            if record["split"] == split
        )
        no_count = counts[split] - yes_count

        print(
            f"{split}: {counts[split]} examples "
            f"(Yes: {yes_count}, No: {no_count})"
        )

    print("Total examples:", len(records))
    print("Saved:", output_file)


if __name__ == "__main__":
    main()