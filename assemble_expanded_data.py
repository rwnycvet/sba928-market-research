"""Validate and assemble the five fictional task families."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "training_data_v3"

FILES = {
    "country_cases.jsonl": "country_coverage",
    "consumer_cases.jsonl": "consumer_behavior",
    "trend_cases.jsonl": "market_trends",
    "product_cases.jsonl": "product_demand",
    "competitor_cases.jsonl": "competitor_research",
}

SPLITS = ("train", "validation", "test")
EXPECTED_COUNTS = {
    "train": 640,
    "validation": 160,
    "test": 160,
}


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destinations = [
        DATA / f"{split}.jsonl" for split in SPLITS
    ] + [DATA / "manifest.json"]

    for path in destinations:
        if path.exists():
            raise FileExistsError(
                f"{path.name} already exists. Review before replacing."
            )

    datasets = {split: [] for split in SPLITS}
    seen_ids = set()
    seen_prompts = set()
    group_owners = {}
    group_contexts = {}
    evidence_splits = {}
    source_hashes = {}

    required_fields = (
        "id", "task_family", "source_type", "source_group",
        "split", "instruction", "context", "target",
    )

    for filename, expected_family in FILES.items():
        source = DATA / filename

        with source.open(encoding="utf-8") as file:
            records = [
                json.loads(line) for line in file if line.strip()
            ]

        if not records:
            raise ValueError(f"No examples in {filename}.")

        source_hashes[filename] = file_hash(source)

        for record in records:
            for field in required_fields:
                value = record.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"{filename}: invalid field {field}."
                    )

            example_id = record["id"]
            split = record["split"]
            family = record["task_family"]
            group = record["source_group"]

            if example_id in seen_ids:
                raise ValueError(f"Duplicate ID: {example_id}")
            seen_ids.add(example_id)

            if split not in SPLITS:
                raise ValueError(f"Invalid split: {split}")

            if family != expected_family:
                raise ValueError(
                    f"Wrong task family in {filename}: {family}"
                )

            if record["source_type"] != "synthetic":
                raise ValueError("All v3 examples must be labeled synthetic.")

            owner = (split, family)
            if group in group_owners and group_owners[group] != owner:
                raise ValueError(
                    f"Source group crosses splits or families: {group}"
                )
            group_owners[group] = owner

            context_key = " ".join(record["context"].split())

            if (
                group in group_contexts
                and group_contexts[group] != context_key
            ):
                raise ValueError(
                    f"Source group contains different evidence: {group}"
                )
            group_contexts[group] = context_key

            evidence_key = (family, context_key)
            if (
                evidence_key in evidence_splits
                and evidence_splits[evidence_key] != split
            ):
                raise ValueError(
                    "Identical evidence appears in different splits."
                )
            evidence_splits[evidence_key] = split

            prompt_key = (
                " ".join(record["instruction"].split()),
                context_key,
            )
            if prompt_key in seen_prompts:
                raise ValueError("Duplicate instruction/evidence pair.")
            seen_prompts.add(prompt_key)

            datasets[split].append(record)

    split_details = {}

    for split, records in datasets.items():
        if len(records) != EXPECTED_COUNTS[split]:
            raise ValueError(
                f"{split}: expected {EXPECTED_COUNTS[split]} "
                f"examples, found {len(records)}."
            )

        family_counts = Counter(
            record["task_family"] for record in records
        )
        expected_per_family = EXPECTED_COUNTS[split] // len(FILES)

        if any(
            family_counts[family] != expected_per_family
            for family in FILES.values()
        ):
            raise ValueError(f"Unbalanced task families in {split}.")

        variants_per_group = Counter(
            record["source_group"] for record in records
        )
        if any(count != 2 for count in variants_per_group.values()):
            raise ValueError(
                f"{split}: expected two variations per source group."
            )

        split_details[split] = {
            "examples": len(records),
            "source_groups": len(variants_per_group),
            "examples_by_family": dict(family_counts),
        }

    # Write only after all dataset checks pass.
    for split, records in datasets.items():
        path = DATA / f"{split}.jsonl"
        with path.open("x", encoding="utf-8") as file:
            for record in records:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

    manifest = {
        "dataset_version": "v3_synthetic_computed_evidence",
        "source_type": "synthetic",
        "splits": split_details,
        "source_file_sha256": source_hashes,
        "dataset_sha256": {
            split: file_hash(DATA / f"{split}.jsonl")
            for split in SPLITS
        },
        "limitations": [
            "All examples are fictional, not retailer findings.",
            "Splits share templates and reasoning patterns.",
            "Two prompt variations share each scenario's evidence.",
            "Several tasks supply figures calculated by Python.",
            "Performance does not establish autonomous arithmetic ability.",
            "Previously reviewed v2 tests remain regression checks.",
        ],
    }

    with (DATA / "manifest.json").open("x", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2, ensure_ascii=False)

    print("DATASET CHECKS PASSED")

    for split, details in split_details.items():
        print(
            f"{split}: {details['examples']} examples, "
            f"{details['source_groups']} source groups"
        )

    print("Task families:", len(FILES))
    print("Cross-split source-group overlap: 0")
    print("Cross-split identical-evidence overlap: 0")
    print("Saved datasets and fingerprints to:", DATA)


if __name__ == "__main__":
    main()