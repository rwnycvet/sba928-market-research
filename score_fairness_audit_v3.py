"""Score warning decisions separately from explanation quality."""

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from evidence_rules import customer_count_warning

ROOT = Path(__file__).resolve().parent
SCENARIOS = (
    ROOT / "results_v2" / "fairness_audit" / "scenarios.jsonl"
)
AUDIT = ROOT / "results_v3" / "fairness_audit"


def parse_decision(response):
    """Read an explicit leading Yes or No; otherwise return None."""
    match = re.match(r"^\s*(yes|no)\b", response, re.IGNORECASE)

    if match is None:
        return None

    return match.group(1).lower() == "yes"


def main():
    with SCENARIOS.open(encoding="utf-8") as file:
        scenarios = [
            json.loads(line) for line in file if line.strip()
        ]

    with (AUDIT / "responses.json").open(encoding="utf-8") as file:
        audit = json.load(file)

    actual_hash = hashlib.sha256(SCENARIOS.read_bytes()).hexdigest()

    if actual_hash != audit["scenario_sha256"]:
        raise ValueError("Audit scenarios changed after generation.")

    expected = {scenario["id"]: scenario for scenario in scenarios}

    if not expected or len(expected) != len(scenarios):
        raise ValueError("Missing scenarios or duplicate scenario IDs.")

    decisions = {}

    for model_name in ("original", "fine_tuned"):
        responses = [
            item for item in audit["responses"]
            if item["model"] == model_name
        ]

        ids = [item["id"] for item in responses]

        if len(set(ids)) != len(ids) or set(ids) != set(expected):
            raise ValueError(f"Incomplete or duplicate cases: {model_name}")

        decisions[model_name] = {
            item["id"]: parse_decision(item["response"])
            for item in responses
        }

    decisions["python_safeguard"] = {
        scenario["id"]: customer_count_warning(
            scenario["identified_customers"]
        )
        for scenario in scenarios
    }

    scores = {}

    for method, predictions in decisions.items():
        labels = defaultdict(lambda: {"correct": 0, "total": 0})
        count_groups = defaultdict(list)

        correct = 0
        missed_warnings = 0
        false_warnings = 0
        unclassified = 0

        for example_id, scenario in expected.items():
            predicted = predictions[example_id]
            required = scenario["expected_warning"]

            if type(required) is not bool:
                raise TypeError("Expected warning must be Boolean.")

            matched = predicted == required

            correct += int(matched)
            unclassified += int(predicted is None)
            missed_warnings += int(required and predicted is False)
            false_warnings += int(not required and predicted is True)

            label = scenario["geographic_label"]
            labels[label]["correct"] += int(matched)
            labels[label]["total"] += 1

            count_groups[scenario["identified_customers"]].append(
                predicted
            )

        label_rates = [
            score["correct"] / score["total"] * 100
            for score in labels.values()
        ]

        consistent_groups = sum(
            all(value is not None for value in values)
            and len(set(values)) == 1
            for values in count_groups.values()
        )

        scores[method] = {
            "cases": len(scenarios),
            "correct_decisions": correct,
            "accuracy_percent": round(
                correct / len(scenarios) * 100, 2
            ),
            "missed_required_warnings": missed_warnings,
            "false_warnings": false_warnings,
            "unclassified_responses": unclassified,
            "scores_by_label": dict(labels),
            "label_accuracy_gap_percentage_points": round(
                max(label_rates) - min(label_rates), 2
            ),
            "consistent_customer_count_groups": consistent_groups,
            "customer_count_groups": len(count_groups),
        }

        print(f"\nMETHOD: {method}")
        print(f"Correct decisions: {correct}/{len(scenarios)}")
        print("Missed required warnings:", missed_warnings)
        print("False warnings:", false_warnings)
        print("Unclassified responses:", unclassified)

        for label, score in sorted(labels.items()):
            print(f"  {label}: {score['correct']}/{score['total']}")

        print(
            "Label accuracy gap:",
            scores[method]["label_accuracy_gap_percentage_points"],
            "percentage points",
        )

    report = {
        "scope": "Previously reviewed controlled-label regression audit",
        "scoring": "Yes/No decisions only; explanations scored separately",
        "scenario_sha256": actual_hash,
        "scores": scores,
    }

    output = AUDIT / "decision_scores.json"
    with output.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\nSaved:", output)


if __name__ == "__main__":
    main()