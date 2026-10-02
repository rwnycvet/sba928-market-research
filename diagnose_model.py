import json
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

root = Path(__file__).resolve().parent

with (root / "results" / "training_run.json").open(
    encoding="utf-8"
) as file:
    run = json.load(file)

options = {}
if run.get("model_revision"):
    options["revision"] = run["model_revision"]

tokenizer = AutoTokenizer.from_pretrained(run["model"], **options)
model = AutoModelForSeq2SeqLM.from_pretrained(
    run["model"], **options
).to("cuda")
model.eval()

print("Configured tied embeddings:", model.config.tie_word_embeddings)
print("EOS token ID:", tokenizer.eos_token_id)

# Simple diagnostic prompts, separate from the held-out country tests.
prompts = [
    "What is the capital of France?",
    "Translate to German: The house is wonderful.",
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
        print("Token IDs:", output[0].tolist())
        print("Raw output:", tokenizer.decode(
            output[0], skip_special_tokens=False
        ))

        # Compare validation responses without changing either model.
with (root / "training_data" / "validation.jsonl").open(
    encoding="utf-8"
) as file:
    examples = [json.loads(line) for line in file if line.strip()]

comparisons = [
    {"id": item["id"], "reference": item["response"]}
    for item in examples
]

for version in ("original", "fine_tuned"):
    if version == "fine_tuned":
        del model
        torch.cuda.empty_cache()
        model = AutoModelForSeq2SeqLM.from_pretrained(
            root / "models" / "flan-t5-country"
        ).to("cuda")

    model.eval()
    with torch.no_grad():
        for item, result in zip(examples, comparisons):
            inputs = tokenizer(
                item["prompt"], return_tensors="pt"
            ).to("cuda")
            output = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                num_beams=1,
            )
            result[version] = tokenizer.decode(
                output[0], skip_special_tokens=True
            )

destination = root / "results" / "validation_comparison.json"
with destination.open("w", encoding="utf-8") as file:
    json.dump(comparisons, file, indent=2, ensure_ascii=False)

print("\nValidation comparison saved to:", destination)