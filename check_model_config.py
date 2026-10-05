import json
from pathlib import Path

import transformers
from huggingface_hub import hf_hub_download
from transformers import AutoConfig

root = Path(__file__).resolve().parent

# Use the model revision recorded in the original experiment.
run_file = root / "submission_v1" / "results" / "training_run.json"
run = json.loads(run_file.read_text(encoding="utf-8"))

model_name = run["model"]
revision = run.get("model_revision")

if not revision:
    revision = "0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab"
    print("Using the locally cached revision for diagnosis.")
    print("The original training revision was not recorded.")
    
config_path = hf_hub_download(
    repo_id=model_name,
    filename="config.json",
    revision=revision,
)

raw_config = json.loads(
    Path(config_path).read_text(encoding="utf-8")
)
loaded_config = AutoConfig.from_pretrained(
    model_name,
    revision=revision,
)

print("Transformers version:", transformers.__version__)
print("Model:", model_name)
print("Revision:", revision)
print("Raw file setting:", raw_config.get("tie_word_embeddings"))
print("Loaded config setting:", loaded_config.tie_word_embeddings)