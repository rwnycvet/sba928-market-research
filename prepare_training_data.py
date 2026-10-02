"""Prepare evidence-based examples for a country-analysis pilot."""

import csv
import json
import random
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
OUTPUT = ROOT / "training_data"
OUTPUT.mkdir(exist_ok=True)


def read_csv(filename):
    """Read a summary file as a list of dictionaries."""
    with (RESULTS / filename).open(
        encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


def save_jsonl(filename, examples):
    """Write one training example per line."""
    with (OUTPUT / filename).open("w", encoding="utf-8") as file:
        for example in examples:
            file.write(json.dumps(example, ensure_ascii=False) + "\n")


revenue_rows = read_csv("country_revenue.csv")
coverage_rows = read_csv("country_coverage.csv")

revenues = {row["Country"]: row for row in revenue_rows}
coverage = {row["Country"]: row for row in coverage_rows}

if set(revenues) != set(coverage):
    raise ValueError("Revenue and coverage country labels do not match.")

# Shuffle reproducibly, then separate countries before making variations.
countries = sorted(revenues)
if len(countries) < 20:
    raise ValueError("Too few countries for the planned pilot split.")

random.Random(928).shuffle(countries)

partitions = {
    "train": countries[:-12],
    "validation": countries[-12:-6],
    "test": countries[-6:],
}

assert not set(partitions["train"]) & set(partitions["validation"])
assert not set(partitions["train"]) & set(partitions["test"])
assert not set(partitions["validation"]) & set(partitions["test"])

instructions = [
    "Prepare a concise country sales brief from the supplied evidence.",
    "Summarize this country's recorded sales and data coverage for a marketing manager.",
    "Explain this country's sales result, its evidence limitations, and one next action.",
]


def make_example(country, instruction, variant):
    """Build a source-grounded input and a rule-based target response."""
    row = coverage[country]
    revenue = Decimal(revenues[country]["SalesRevenue"]).quantize(
        Decimal("0.01")
    )
    sales_rows = int(row["SalesRows"])
    invoices = int(row["PurchaseInvoices"])
    customers = int(row["IdentifiedCustomers"])
    missing = int(row["MissingCustomerIDRows"])
    missing_percent = missing / sales_rows * 100

    # This threshold is an explicit teaching rule, not a statistical test.
    sparse = customers < 5

    if sparse:
        limitation = (
            "Fewer than five identified customers are represented. "
            "This is a descriptive caution, not a statistical "
            "representativeness test."
        )
        recommendation = (
            "Recommendation: gather more customer evidence before "
            "expanding country-level marketing."
        )
    else:
        limitation = (
            "This retailer's customer records do not establish "
            "national demand or customer motives."
        )
        recommendation = (
            "Recommendation: review customer-level buying patterns "
            "before selecting a marketing campaign."
        )

    if missing:
        limitation += (
            " Missing CustomerIDs limit customer-level conclusions; "
            "the identified-customer count excludes those rows."
        )

    evidence = {
        "Country": country,
        "PositiveSalesRevenueGBP": str(revenue),
        "SalesRows": sales_rows,
        "PurchaseInvoices": invoices,
        "IdentifiedCustomers": customers,
        "MissingCustomerIDRows": missing,
        "MissingCustomerIDPercent": round(missing_percent, 2),
    }

    prompt = (
        instruction
        + "\nReport positive sales revenue, purchase invoices, "
        "identified customers, and the percentage of sales rows "
        "missing CustomerIDs. Include one limitation and one "
        "recommendation. Use only the evidence. Revenue is before "
        "return and cancellation deductions, not net revenue. "
        "Fewer than five identified customers triggers a descriptive "
        "small-sample caution, not a statistical test."
        + "\nEvidence:\n"
        + json.dumps(evidence, ensure_ascii=False)
    )

    response = (
        f"{country}: positive sales revenue was GBP {revenue:,.2f}, "
        f"with {invoices:,} purchase invoices and "
        f"{customers:,} identified customers. "
        f"{missing_percent:.2f}% of sales rows lacked CustomerIDs. "
        "Revenue is before return and cancellation deductions, "
        "not net revenue.\n"
        f"Limitation: {limitation}\n"
        f"{recommendation}"
    )

    return {
        "id": f"{country}_{variant}",
        "topic": "Country sales and coverage",
        "source_group": country,
        "prompt": prompt,
        "response": response,
        "target_origin": "Rule-based draft requiring learner review",
    }


counts = {}

for split, split_countries in partitions.items():
    # Training gets three wordings per country.
    # Validation and test each get one example per held-out country.
    wordings = instructions if split == "train" else instructions[:1]
    examples = [
        make_example(country, instruction, variant)
        for country in split_countries
        for variant, instruction in enumerate(wordings, start=1)
    ]
    save_jsonl(f"{split}.jsonl", examples)
    counts[split] = len(examples)

manifest = {
    "seed": 928,
    "split_unit": "Country",
    "countries_by_split": partitions,
    "example_counts": counts,
    "notes": [
        "Three training variations share each country's evidence.",
        "Variations are not independent observations.",
        "All splits come from the same retailer and historical period.",
        "Targets are rule-based drafts, not independent expert labels.",
        "Test data must not be used to select training settings.",
    ],
}

with (OUTPUT / "manifest.json").open("w", encoding="utf-8") as file:
    json.dump(manifest, file, indent=2, ensure_ascii=False)

print("Country groups:", {k: len(v) for k, v in partitions.items()})
print("Example counts:", counts)
print("Saved files to:", OUTPUT)

preview = make_example(partitions["train"][0], instructions[0], 1)
print("\nTRAINING EXAMPLE TO REVIEW")
print(preview["prompt"])
print("\nTARGET RESPONSE")
print(preview["response"])