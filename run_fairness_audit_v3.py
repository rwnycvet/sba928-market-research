"""Run identical audit prompts through the original and revised models."""

import hashlib
import json
from pathlib import Path

import torch
import transformers
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent

# Reuse the frozen scenarios from the earlier controlled audit.
SCENARIOS = (
    ROOT / "results_v2" / "fairness_audit" / "scenarios.jsonl"
)

# Save this model version's responses separately.
AUDIT = ROOT / "results_v3" / "fairness_audit"
AUDIT.mkdir(parents=True, exist_ok=True)

OUTPUT = AUDIT / "responses.json"
ADAPTED = ROOT / "models" / "flan-t5-multitask-v3"

MODEL_NAME = "google/flan-t5-small"
REVISION = "0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab"


def main():
    if OUTPUT.exists():
        raise FileExistsError(
            "Audit responses already exist. Review before replacing."
        )

    if not ADAPTED.exists():
        raise FileNotFoundError(f"Revised model not found: {ADAPTED}")

    if transformers.__version__ != "4.57.6":
        raise RuntimeError("This audit expects Transformers 4.57.6.")

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable.")

    with SCENARIOS.open(encoding="utf-8") as file:
        scenarios = [
            json.loads(line) for line in file if line.strip()
        ]

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME, revision=REVISION
    )

    for scenario in scenarios:
        if len(tokenizer(scenario["prompt"])["input_ids"]) > 512:
            raise ValueError(f"Prompt too long: {scenario['id']}")

    responses = []

    model_sources = [
        ("original", MODEL_NAME, {"revision": REVISION}),
        ("fine_tuned", str(ADAPTED), {}),
    ]

    for model_label, source, options in model_sources:
        print(f"\nLoading {model_label} model...", flush=True)

        model, loading_info = AutoModelForSeq2SeqLM.from_pretrained(
            source,
            output_loading_info=True,
            **options,
        )

        for category in (
            "missing_keys", "unexpected_keys",
            "mismatched_keys", "error_msgs",
        ):
            if loading_info.get(category):
                raise RuntimeError(
                    f"{model_label}: {category}="
                    f"{loading_info[category]}"
                )

        if model.config.tie_word_embeddings is not False:
            raise RuntimeError("Unexpected embedding configuration.")

        model = model.to("cuda")
        model.eval()

        with torch.inference_mode():
            for number, scenario in enumerate(scenarios, start=1):
                inputs = tokenizer(
                    scenario["prompt"],
                    return_tensors="pt",
                ).to("cuda")

                output = model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False,
                    num_beams=1,
                )

                responses.append({
                    **scenario,
                    "model": model_label,
                    "response": tokenizer.decode(
                        output[0], skip_special_tokens=True
                    ),
                    "raw_output": tokenizer.decode(
                        output[0], skip_special_tokens=False
                    ),
                })

                print(
                    f"{model_label}: {number}/{len(scenarios)}",
                    flush=True,
                )

        del model
        torch.cuda.empty_cache()

    report = {
        "base_model": MODEL_NAME,
        "base_revision": REVISION,
        "fine_tuned_model": str(ADAPTED),
        "transformers_version": transformers.__version__,
        "torch_version": torch.__version__,
        "generation": {
            "max_new_tokens": 256,
            "do_sample": False,
            "num_beams": 1,
        },
        "scenario_sha256": hashlib.sha256(
            SCENARIOS.read_bytes()
        ).hexdigest(),
        "responses": responses,
    }

    with OUTPUT.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\nSaved responses:", len(responses))
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()