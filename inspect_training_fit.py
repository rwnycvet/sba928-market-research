"""Inspect model responses to examples used during training."""

import json
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "models" / "flan-t5-multitask-v2"
DATA = ROOT / "training_data_v2" / "train.jsonl"
OUTPUT = ROOT / "results_v2" / "multitask_run"


def main():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable.")

    with DATA.open(encoding="utf-8") as file:
        examples = [
            json.loads(line) for line in file if line.strip()
        ]

    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL).to("cuda")
    model.eval()

    reviews = []

    with torch.inference_mode():
        for example in examples:
            prompt = (
                f"{example['instruction']}\n\n"
                f"Evidence:\n{example['context']}\n\n"
                "Answer:"
            )

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
            )

            reviews.append({
                "id": example["id"],
                "task_family": example["task_family"],
                "reference": example["target"],
                "model_response": response,
            })

            print("\nID:", example["id"])
            print("REFERENCE:", example["target"])
            print("MODEL:", response, flush=True)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT / "training_fit_review.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(reviews, file, indent=2, ensure_ascii=False)

    print("\nTraining examples reviewed:", len(reviews))
    print("Saved:", output_file)


if __name__ == "__main__":
    main()