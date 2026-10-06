"""Fine-tune FLAN-T5 Small on the five-task market-research pilot."""

import hashlib
import json
import random
from pathlib import Path

import torch
import transformers
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "training_data_v3"
MODEL_DIR = ROOT / "models" / "flan-t5-multitask-v3"
RESULTS = ROOT / "results_v3" / "expanded_run"
RESULTS.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "google/flan-t5-small"
MODEL_REVISION = "0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab"
SEED = 928
EPOCHS = 6
BATCH_SIZE = 4
LEARNING_RATE = 5e-5

random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

if not torch.cuda.is_available():
    raise RuntimeError("CUDA is unavailable. Check the GPU setup.")


def read_examples(split):
    with (DATA / f"{split}.jsonl").open(encoding="utf-8") as file:
        examples = [
            json.loads(line) for line in file if line.strip()
        ]

    for example in examples:
        if example["split"] != split:
            raise ValueError(
                f"Incorrect split for example: {example['id']}"
            )

        example["prompt"] = (
            f"{example['instruction']}\n\n"
            f"Evidence:\n{example['context']}\n\n"
            "Answer:"
        )
        example["response"] = example["target"]

    return examples


train = read_examples("train")
validation = read_examples("validation")
test = read_examples("test")
# Verify that the assembled datasets have not changed.
with (DATA / "manifest.json").open(encoding="utf-8") as file:
    dataset_manifest = json.load(file)

for split in ("train", "validation", "test"):
    actual_hash = hashlib.sha256(
        (DATA / f"{split}.jsonl").read_bytes()
    ).hexdigest()

    expected_hash = dataset_manifest["dataset_sha256"][split]

    if actual_hash != expected_hash:
        raise ValueError(f"Dataset fingerprint changed: {split}")

print(
    f"Dataset sizes: train={len(train)}, "
    f"validation={len(validation)}, test={len(test)}",
    flush=True,
)
print("Dataset fingerprints verified.", flush=True)

groups = [
    {example["source_group"] for example in split}
    for split in (train, validation, test)
]
assert groups[0].isdisjoint(groups[1])
assert groups[0].isdisjoint(groups[2])
assert groups[1].isdisjoint(groups[2])

print("Loading model. The first run downloads its files.", flush=True)
if transformers.__version__ != "4.57.6":
    raise RuntimeError(
        "This experiment expects transformers 4.57.6. "
        f"Found {transformers.__version__}."
    )

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    revision=MODEL_REVISION,
)

model, loading_info = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    revision=MODEL_REVISION,
    output_loading_info=True,
)

for category in (
    "missing_keys",
    "unexpected_keys",
    "mismatched_keys",
    "error_msgs",
):
    if loading_info.get(category):
        raise RuntimeError(
            f"Model loading needs review: "
            f"{category}={loading_info[category]}"
        )

if model.config.tie_word_embeddings is not False:
    raise RuntimeError(
        "The loaded configuration does not match the expected "
        "tie_word_embeddings=False setting."
    )

input_weights = model.get_input_embeddings().weight
output_weights = model.get_output_embeddings().weight

if input_weights.data_ptr() == output_weights.data_ptr():
    raise RuntimeError(
        "Input and output embeddings unexpectedly share storage."
    )

model = model.to("cuda")
model_revision = MODEL_REVISION

print("Model revision:", model_revision, flush=True)
print("Transformers version:", transformers.__version__, flush=True)
print("Model loading checks passed.", flush=True)

# Check lengths rather than silently discarding evidence.
for example in train + validation + test:
    if len(tokenizer(example["prompt"])["input_ids"]) > 512:
        raise ValueError(f"Input too long: {example['id']}")
    if len(tokenizer(example["response"])["input_ids"]) > 256:
        raise ValueError(f"Target too long: {example['id']}")


def make_batch(examples):
    inputs = tokenizer(
        [item["prompt"] for item in examples],
        padding=True,
        return_tensors="pt",
    )
    targets = tokenizer(
        [item["response"] for item in examples],
        padding=True,
        return_tensors="pt",
    )
    labels = targets["input_ids"]
    labels[targets["attention_mask"] == 0] = -100
    inputs["labels"] = labels
    return {key: value.to("cuda") for key, value in inputs.items()}


def validation_loss():
    """Calculate target-token-weighted validation loss."""
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    with torch.no_grad():
        for start in range(0, len(validation), BATCH_SIZE):
            batch = make_batch(validation[start:start + BATCH_SIZE])
            tokens = int((batch["labels"] != -100).sum().item())
            loss = model(**batch).loss
            total_loss += loss.item() * tokens
            total_tokens += tokens
    return total_loss / total_tokens


def generate_responses(examples):
    """Use identical deterministic decoding for both model versions."""
    model.eval()
    responses = []
    with torch.no_grad():
        for example in examples:
            inputs = tokenizer(
                example["prompt"], return_tensors="pt"
            ).to("cuda")
            output = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                num_beams=1,
            )
            responses.append(
                tokenizer.decode(output[0], skip_special_tokens=True)
            )
    return responses


baseline_loss = validation_loss()
history = []
best_loss = float("inf")
best_epoch = None
optimizer = torch.optim.AdamW(
    model.parameters(), lr=LEARNING_RATE
)

print(f"Original validation loss: {baseline_loss:.4f}", flush=True)

for epoch in range(1, EPOCHS + 1):
    model.train()
    shuffled = train.copy()
    random.Random(SEED + epoch).shuffle(shuffled)
    total_loss = 0.0
    total_tokens = 0

    for start in range(0, len(shuffled), BATCH_SIZE):
        batch = make_batch(shuffled[start:start + BATCH_SIZE])
        optimizer.zero_grad(set_to_none=True)
        loss = model(**batch).loss

        if not torch.isfinite(loss):
            raise RuntimeError("Nonfinite training loss detected.")

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        tokens = int((batch["labels"] != -100).sum().item())
        total_loss += loss.item() * tokens
        total_tokens += tokens

    current_loss = validation_loss()
    record = {
        "epoch": epoch,
        "training_loss": total_loss / total_tokens,
        "validation_loss": current_loss,
    }
    history.append(record)
    print(record, flush=True)

    # Select among trained checkpoints using validation only.
    if current_loss < best_loss:
        best_loss = current_loss
        best_epoch = epoch
        model.save_pretrained(MODEL_DIR)
        tokenizer.save_pretrained(MODEL_DIR)

# Evaluate test countries only after training and selection are finished.
del optimizer
del model
torch.cuda.empty_cache()

print("Generating original-model test responses...", flush=True)
load_options = {"revision": model_revision} if model_revision else {}
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME, **load_options
).to("cuda")
original_responses = generate_responses(test)

del model
torch.cuda.empty_cache()

print("Generating fine-tuned test responses...", flush=True)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR).to("cuda")
adapted_responses = generate_responses(test)

comparisons = [
    {
        "id": example["id"],
        "task_family": example["task_family"],
        "source_group": example["source_group"],
        "source_type": example["source_type"],
        "prompt": example["prompt"],
        "reference": example["response"],
        "original_response": original,
        "fine_tuned_response": adapted,
    }
    for example, original, adapted in zip(
        test, original_responses, adapted_responses
    )
]

run_record = {
    "experiment": "Expanded five-task synthetic dataset with computed evidence",
    "evaluation_scope": "Reserved v3 synthetic scenarios; two variants per group",
    "dataset_manifest": dataset_manifest,
    "training_examples": len(train),
    "validation_examples": len(validation),
    "test_examples": len(test),
    "optimizer_steps": EPOCHS * (
        (len(train) + BATCH_SIZE - 1) // BATCH_SIZE
    ),
    "model": MODEL_NAME,
    "model_revision": model_revision,
    "seed": SEED,
    "epochs": EPOCHS,
    "batch_size": BATCH_SIZE,
    "learning_rate": LEARNING_RATE,
    "torch_version": torch.__version__,
    "transformers_version": transformers.__version__,
    "gpu": torch.cuda.get_device_name(0),
    "original_validation_loss": baseline_loss,
    "selected_epoch": best_epoch,
    "selected_validation_loss": best_loss,
    "history": history,
    "data_sha256": {
        split: hashlib.sha256(
            (DATA / f"{split}.jsonl").read_bytes()
        ).hexdigest()
        for split in ("train", "validation", "test")
    },
}

for filename, content in [
    ("training_run.json", run_record),
    ("model_comparison.json", comparisons),
]:
    with (RESULTS / filename).open("w", encoding="utf-8") as file:
        json.dump(content, file, indent=2, ensure_ascii=False)

print("\nTraining and comparison finished.")
print("Selected epoch:", best_epoch)
print("Original validation loss:", baseline_loss)
print("Selected validation loss:", best_loss)
print("Results saved in:", RESULTS / "training_run.json")
print("Test responses saved in:", RESULTS / "model_comparison.json")