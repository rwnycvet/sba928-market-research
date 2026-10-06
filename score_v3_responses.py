"""Measure strict reference agreement for the reserved v3 test set."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "training_data_v3" / "test.jsonl"
RESULTS = ROOT / "results_v3" / "expanded_run"

MODEL_FIELDS = {
    "original": "original_response",
    "fine_tuned": "fine_tuned_response",
}


def normalize(text):
    """Ignore whitespace differences only."""
    return " ".join(text.split())


def main():
    with DATA.open(encoding="utf-8") as file:
        examples = [
            json.loads(line) for line in file if line.strip()
        ]

    with (RESULTS / "training_run.json").open(
        encoding="utf-8"
    ) as file:
        run = json.load(file)

    actual_hash = hashlib.sha256(DATA.read_bytes()).hexdigest()

    if actual_hash != run["data_sha256"]["test"]:
        raise ValueError("Test data changed after the recorded run.")

    with (RESULTS / "model_comparison.json").open(
        encoding="utf-8"
    ) as file:
        comparisons = json.load(file)

    expected = {example["id"]: example for example in examples}

    if len(expected) != len(examples):
        raise ValueError("Duplicate IDs in the test dataset.")

    comparison_ids = [item["id"] for item in comparisons]

    if len(set(comparison_ids)) != len(comparison_ids):
        raise ValueError("Duplicate IDs in model comparisons.")

    if set(comparison_ids) != set(expected):
        raise ValueError("Comparison IDs do not match the test dataset.")

    group_sizes = Counter(
        example["source_group"] for example in examples
    )
    if any(size != 2 for size in group_sizes.values()):
        raise ValueError("Expected two prompt variations per scenario.")

    scores = {}
    reviews = []

    for model_name, response_field in MODEL_FIELDS.items():
        family_totals = Counter()
        family_matches = Counter()
        group_matches = defaultdict(list)
        match_count = 0
        empty_count = 0

        for comparison in comparisons:
            example = expected[comparison["id"]]

            if comparison["reference"] != example["target"]:
                raise ValueError("Reference differs from the test target.")

            if (
                comparison["source_group"] != example["source_group"]
                or comparison["task_family"] != example["task_family"]
            ):
                raise ValueError("Comparison metadata does not match.")

            response = comparison[response_field]

            if not isinstance(response, str):
                raise TypeError("Model response must be text.")

            matched = (
                normalize(response) == normalize(example["target"])
            )

            family = example["task_family"]
            group = example["source_group"]

            family_totals[family] += 1
            family_matches[family] += int(matched)
            group_matches[group].append(matched)
            match_count += int(matched)
            empty_count += int(not response.strip())

            reviews.append({
                "model": model_name,
                "id": example["id"],
                "task_family": family,
                "source_group": group,
                "strict_reference_match": matched,
                "reference": example["target"],
                "response": response,
            })

        both_variants_match = sum(
            all(matches) for matches in group_matches.values()
        )

        scores[model_name] = {
            "responses": len(comparisons),
            "strict_reference_matches": match_count,
            "strict_reference_match_percent": round(
                match_count / len(comparisons) * 100, 2
            ),
            "empty_responses": empty_count,
            "source_groups": len(group_matches),
            "groups_with_both_variants_matching": both_variants_match,
            "by_task_family": {
                family: {
                    "matches": family_matches[family],
                    "responses": family_totals[family],
                }
                for family in sorted(family_totals)
            },
        }

        print(f"\nMODEL: {model_name}")
        print(
            f"Strict reference matches: "
            f"{match_count}/{len(comparisons)}"
        )
        print(
            f"Scenarios with both variants matching: "
            f"{both_variants_match}/{len(group_matches)}"
        )
        print("Empty responses:", empty_count)

        for family in sorted(family_totals):
            print(
                f"  {family}: {family_matches[family]}/"
                f"{family_totals[family]}"
            )

    for filename, content in (
        ("strict_reference_scores.json", scores),
        ("strict_reference_review.json", reviews),
    ):
        with (RESULTS / filename).open(
            "w", encoding="utf-8"
        ) as file:
            json.dump(content, file, indent=2, ensure_ascii=False)

    print("\nSaved scoring results to:", RESULTS)


if __name__ == "__main__":
    main()