"""Evaluate the Python warning rule against the saved audit scenarios."""

import json
from collections import defaultdict
from pathlib import Path

from evidence_rules import customer_count_warning

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "results_v2" / "fairness_audit"


def main():
    with (AUDIT / "scenarios.jsonl").open(encoding="utf-8") as file:
        scenarios = [
            json.loads(line) for line in file if line.strip()
        ]

    if not scenarios:
        raise ValueError("No audit scenarios were found.")

    results = []
    label_scores = defaultdict(lambda: {"correct": 0, "total": 0})

    for scenario in scenarios:
        label = scenario["geographic_label"]
        count = scenario["identified_customers"]
        expected = scenario["expected_warning"]

        if type(expected) is not bool:
            raise TypeError("Expected warning must be True or False.")

        predicted = customer_count_warning(count)
        correct = predicted == expected

        comparison = (
            "fewer than five" if predicted else "at least five"
        )
        decision = "Yes" if predicted else "No"
        explanation = (
            f"{decision}. {label} has {count} identified customers, "
            f"which is {comparison}. This is a descriptive rule, "
            "not a statistical test of representativeness."
        )

        results.append({
            "id": scenario["id"],
            "geographic_label": label,
            "identified_customers": count,
            "expected_warning": expected,
            "predicted_warning": predicted,
            "correct_decision": correct,
            "explanation": explanation,
        })

        label_scores[label]["total"] += 1
        label_scores[label]["correct"] += int(correct)

    correct_count = sum(item["correct_decision"] for item in results)
    accuracy = correct_count / len(results) * 100

    report = {
        "method": "Python rule and fixed explanation template",
        "rule": "identified_customers < 5",
        "cases": len(results),
        "correct_decisions": correct_count,
        "decision_accuracy_percent": accuracy,
        "scores_by_label": dict(label_scores),
        "results": results,
    }

    output = AUDIT / "safeguard_results.json"
    with output.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("Cases checked:", len(results))
    print("Correct rule decisions:", correct_count)
    print(f"Decision accuracy: {accuracy:.2f}%")

    for label, score in sorted(label_scores.items()):
        print(f"{label}: {score['correct']}/{score['total']}")

    print("Saved:", output)


if __name__ == "__main__":
    main()