## Current Progress
Completed retail data inspection, cleaning, country revenue analysis, product rankings, cancellation review, monthly trends, customer purchase-frequency analysis, and country-coverage checks.

Created research prompts and a country-analysis fine-tuning pilot using FLAN-T5 Small. Training used 78 examples from 26 country labels, with six validation labels and six test labels.

Validation loss decreased from 3.1394 to 0.4642, but generated responses contained numerical errors, repeated text, and incorrect limitations. The experiment does not demonstrate reliable business accuracy. See evaluation.md for findings.

## Reproducing the Experiment
The recorded training environment used Windows, Python 3.14, and an NVIDIA RTX 5090. PyTorch is configured for CUDA 13.0.

Run these commands from the project root:

    uv sync
    uv run python analyze_data.py
    uv run python prepare_training_data.py
    uv run python train_model.py

Training downloads the base model and saves local weights under models/, which is excluded from Git. The preparation and training commands regenerate their output files.

Saved experiment evidence includes:
- results/training_run.json
- results/model_comparison.json
- results/validation_comparison.json

The original spreadsheet must be downloaded and placed in data/ as described above.