import json

import torch
from huggingface_hub import hf_hub_download
from transformers import AutoConfig, AutoModelForSeq2SeqLM, AutoTokenizer

MODEL = "google/flan-t5-small"
REVISION = "0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab"

# Read the setting directly from the pinned source configuration.
config_path = hf_hub_download(
    MODEL, "config.json", revision=REVISION
)
with open(config_path, encoding="utf-8") as file:
    source_config = json.load(file)

config = AutoConfig.from_pretrained(MODEL, revision=REVISION)
config.tie_word_embeddings = source_config["tie_word_embeddings"]

tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL,
    revision=REVISION,
    config=config,
).to("cuda")
model.eval()

print("Loaded setting:", model.config.tie_word_embeddings)
print(
    "Input and output weights share storage:",
    model.get_input_embeddings().weight.data_ptr()
    == model.get_output_embeddings().weight.data_ptr(),
)

prompts = [
    "What is the capital of France?",
    "Translate to German: The house is wonderful.",
    (
        "Answer using only this evidence. "
        "Country: Exampleland. Revenue: GBP 1250.50. "
        "Identified customers: 12. "
        "How many identified customers are recorded?"
    ),
]

with torch.no_grad():
    for prompt in prompts:
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        output = model.generate(
            **inputs,
            max_new_tokens=40,
            do_sample=False,
            num_beams=1,
        )
        print("\nPrompt:", prompt)
        print("Response:", tokenizer.decode(
            output[0], skip_special_tokens=True
        ))

from pathlib import Path

# Use a validation example to investigate the empty-response problem.
root = Path(__file__).resolve().parent
validation_file = (
    root / "submission_v1" / "training_data" / "validation.jsonl"
)

with validation_file.open(encoding="utf-8") as file:
    example = json.loads(next(file))

with torch.no_grad():
    inputs = tokenizer(
        example["prompt"], return_tensors="pt"
    ).to("cuda")

    output = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=False,
        num_beams=1,
    )

print("\nVALIDATION EXAMPLE:", example["id"])
print("Raw output:", tokenizer.decode(
    output[0], skip_special_tokens=False
))
print("Response:", tokenizer.decode(
    output[0], skip_special_tokens=True
))

# Extract the same evidence already supplied in the validation prompt.
evidence = json.loads(example["prompt"].split("Evidence:\n", 1)[1])

simple_prompt = (
    f"Country: {evidence['Country']}\n"
    f"Positive sales revenue: GBP "
    f"{evidence['PositiveSalesRevenueGBP']}\n"
    f"Purchase invoices: {evidence['PurchaseInvoices']}\n"
    f"Identified customers: {evidence['IdentifiedCustomers']}\n\n"
    "What is the positive sales revenue? Copy the amount exactly."
)

with torch.no_grad():
    inputs = tokenizer(
        simple_prompt, return_tensors="pt"
    ).to("cuda")
    output = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=False,
        num_beams=1,
    )

print("\nSIMPLIFIED VALIDATION PROMPT")
print(simple_prompt)
print("Raw output:", tokenizer.decode(
    output[0], skip_special_tokens=False
))
print("Response:", tokenizer.decode(
    output[0], skip_special_tokens=True
))

# Keep exactly the same evidence for all three variations.
context = (
    f"Country: {evidence['Country']}\n"
    f"Positive sales revenue: GBP "
    f"{evidence['PositiveSalesRevenueGBP']}\n"
    f"Purchase invoices: {evidence['PurchaseInvoices']}\n"
    f"Identified customers: {evidence['IdentifiedCustomers']}"
)

variants = {
    "minimal": "What is the positive sales revenue?",
    "format": (
        "What is the positive sales revenue? "
        "Return only GBP followed by the amount."
    ),
    "grounded": (
        "What is the positive sales revenue? "
        "Use only the supplied evidence. Copy the amount exactly. "
        "Return only GBP followed by the amount, with no explanation."
    ),
}

# Evaluate the same three variations on every validation example.
with validation_file.open(encoding="utf-8") as file:
    validation_examples = [
        json.loads(line) for line in file if line.strip()
    ]

records = []

for item in validation_examples:
    facts = json.loads(item["prompt"].split("Evidence:\n", 1)[1])

    context = (
        f"Country: {facts['Country']}\n"
        f"Positive sales revenue: GBP "
        f"{facts['PositiveSalesRevenueGBP']}\n"
        f"Purchase invoices: {facts['PurchaseInvoices']}\n"
        f"Identified customers: {facts['IdentifiedCustomers']}"
    )
    expected = f"GBP {facts['PositiveSalesRevenueGBP']}"

    for name, instruction in variants.items():
        prompt = f"{context}\n\n{instruction}"

        with torch.no_grad():
            inputs = tokenizer(
                prompt, return_tensors="pt"
            ).to("cuda")
            output = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                num_beams=1,
            )

        response = tokenizer.decode(
            output[0], skip_special_tokens=True
        ).strip()

        records.append({
            "record_id": item["id"],
            "variant": name,
            "prompt": prompt,
            "response": response,
            "expected": expected,
            "exact_match": response == expected,
            "model": MODEL,
            "revision": REVISION,
            "max_new_tokens": 256,
            "do_sample": False,
            "num_beams": 1,
        })

output_folder = root / "results_v2"
output_folder.mkdir(exist_ok=True)

with (output_folder / "prompt_validation.json").open(
    "w", encoding="utf-8"
) as file:
    json.dump(records, file, indent=2, ensure_ascii=False)

print("\nVALIDATION PROMPT COMPARISON")
for name in variants:
    selected = [r for r in records if r["variant"] == name]
    correct = sum(r["exact_match"] for r in selected)
    print(f"{name}: {correct}/{len(selected)} exact matches")

print("Saved 18 responses to results_v2/prompt_validation.json")