# SBA 928 Resubmission Evaluation

## Changes Made

The resubmission expands training from country-only briefs to five task families:

- Consumer behavior
- Country sales and coverage
- Monthly market trends
- Product demand and inventory
- Competitor research

The revised experiment uses explicitly labeled fictional scenarios. Several tasks supply figures calculated by Python, so the model is evaluated on reporting and interpreting supplied evidence rather than independently performing arithmetic.

The original experiments remain preserved.

## Model Loading

The revised run uses:

- Model: `google/flan-t5-small`
- Revision: `0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab`
- Transformers: `4.57.6`

The initial loading checks found no reported missing, unexpected or mismatched weights. The loaded configuration retained `tie_word_embeddings=False`, and input/output embeddings did not share storage.

These checks address the previously observed configuration problem. They do not establish reliable reasoning or prove which revision the original submission used.

## Dataset and Training

| Split | Prompt Examples | Underlying Scenarios |
|---|---:|---:|
| Training | 640 | 320 |
| Validation | 160 | 80 |
| Test | 160 | 80 |

Each scenario has two instruction variations kept in the same split. Task-family counts are balanced within each split.

Checks found no shared source groups or identical evidence across splits. Dataset fingerprints were recorded and verified before training.

Training used six epochs, batch size four, learning rate 0.00005 and seed 928, giving 960 optimizer updates.

Epoch 6 was selected using the lowest validation loss. Validation loss decreased from 3.468904 to 0.020701.

## Test Results

Both models used identical test prompts and greedy generation settings.

Strict reference agreement ignores whitespace differences only.

| Measure | Original Model | Fine-Tuned Model |
|---|---:|---:|
| Strict reference matches | 0/160 | 132/160 |
| Strict reference agreement | 0% | 82.5% |
| Scenarios with both variations matching | 0/80 | 64/80 |
| Empty responses | 12 | 0 |

| Task Family | Fine-Tuned Strict Matches |
|---|---:|
| Competitor research | 32/32 |
| Consumer behavior | 32/32 |
| Country coverage | 15/32 |
| Monthly trends | 21/32 |
| Product demand | 32/32 |

The original model's zero strict matches must not be interpreted as zero factual accuracy. Correct alternative wording or incomplete answers can fail this metric.

Manual review of the 28 fine-tuned mismatches identified:

- 17 incorrect customer-warning decisions.
- Nine monthly-trend answers with incorrect percentages, directions or both.
- Two ambiguous answers describing a decrease using a negative decrease amount.

The review did not justify increasing the conservative complete-answer count above 132/160.

Lower validation loss did not eliminate important business errors.

## Geographic-Label Consistency Audit

The controlled audit used Germany, Brazil, Unspecified and fictional Sampleland at customer counts of 3, 4, 5 and 8. Within each count group, only the geographic label changed.

The warning applies below five identified customers. This is a descriptive teaching rule, not a statistical test.

These previously reviewed scenarios were used as a regression audit.

| Measure | Original Model | Fine-Tuned v3 | Python Safeguard |
|---|---:|---:|---:|
| Correct warning decisions | 8/16 | 8/16 | 16/16 |
| Missed required warnings | 8 | 8 | 0 |
| False warnings | 0 | 0 | 0 |
| Unclassified decisions | 0 | 0 | 0 |
| Highest-to-lowest label accuracy gap | 0 percentage points | 0 percentage points | 0 percentage points |

Both models answered No to every case. The fine-tuned model sometimes also described three or four customers as “at least five.”

Equal performance across labels reflected consistent failure on required warnings. It does not establish population fairness or absence of bias.

## Implemented Application Safeguards

The reporting application uses Python calculations and fixed templates for protected findings:

- Customer-count warnings use `identified_customers < 5`.
- Repeat purchasing uses identified customer counts and distinct qualifying invoices.
- Country briefs retain otherwise valid sales without CustomerIDs.
- Inventory briefs preserve positive units and signed balances separately.
- Monthly changes require consecutive complete months.
- Competitor briefs identify missing comparison evidence without inventing figures.

Recommendations are labeled separately from measured findings.

The application generates five briefs and a combined document with:

```powershell
uv run python build_verified_briefs.py
```

Outputs are saved under `results_v3/verified_reports`.

Correct application outputs do not change the raw model's measured scores. The warning safeguard scored 16/16 on the defined audit rule; this does not establish broad fairness.

## Limitations and Conclusion

The expanded evaluation is entirely synthetic and shares templates and reasoning patterns with training. Two prompt variations per scenario are related observations, not independent cases.

Several tasks include Python-computed figures. Their results do not establish independent arithmetic ability, reliability on new wording or generalization to real retailer briefs.

The model learned the reference patterns substantially better, but still makes consequential rule and numerical errors. Generated answers require verification before business use.

The verified reporting application provides a controlled way to present the supplied retailer findings while preserving the model's failures transparently.