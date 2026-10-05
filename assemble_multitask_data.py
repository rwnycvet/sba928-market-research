"""Combine reviewed real and synthetic examples into a training file."""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "training_data_v2"


def main():
    # Read the five real-data examples, one JSON record per line.
    with (DATA / "real_examples.jsonl").open(
        encoding="utf-8"
    ) as file:
        real_records = [
            json.loads(line)
            for line in file
            if line.strip()
        ]

        # Combine the explicitly listed fictional scenario files.
    synthetic_records = []

    for filename in (
        "synthetic_competitor_scenarios.json",
        "synthetic_country_scenarios.json",
        "synthetic_trend_scenarios.json",
        "synthetic_product_scenarios.json",
        "synthetic_consumer_scenarios.json",
    ):
        with (DATA / filename).open(encoding="utf-8") as file:
            scenarios = json.load(file)

        if not isinstance(scenarios, list):
            raise ValueError(f"{filename} must contain a JSON list.")

        synthetic_records.extend(scenarios)

    records = real_records + synthetic_records
    seen_ids = set()

    for record in records:
        for field in (
            "id", "task_family", "source_type", "source_group",
            "split", "instruction", "context", "target"
        ):
            value = record.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Missing or invalid field: {field}")

        if record["id"] in seen_ids:
            raise ValueError(f"Duplicate ID: {record['id']}")
        seen_ids.add(record["id"])

        if record["split"] != "train":
            raise ValueError("This file accepts training examples only.")

    for record in synthetic_records:
        if record["source_type"] != "synthetic":
            raise ValueError("Fictional examples must be labeled synthetic.")

    output = DATA / "train.jsonl"
    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("Real-data examples:", len(real_records))
    print("Synthetic examples:", len(synthetic_records))
    print("Total training examples:", len(records))

    print("\nExamples by task family:")
    for family, count in sorted(
        Counter(record["task_family"] for record in records).items()
    ):
        print(f"  {family}: {count}")

    print("\nSaved:", output)


if __name__ == "__main__":
    main()