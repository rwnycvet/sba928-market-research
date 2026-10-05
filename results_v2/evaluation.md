# Multitask Pilot Evaluation

## Experiment

The pilot used 15 training examples, five validation examples,
and five test examples across five market-research task families.
The training set contained five real-data examples and ten synthetic
examples. Validation and test examples were synthetic.

FLAN-T5 Small was trained for three epochs using Transformers 4.57.6
and model revision 0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab.
The initial model-loading checks passed.

Validation loss decreased from 3.5434564468 to 3.2699645373.
Epoch 3 was selected using validation loss.

## Manual Test Review

A complete answer must correctly address every requested element,
include the required scope or limitation, and avoid unsupported claims.
This is a manual content assessment, not an exact-wording comparison.

| Task | Original model | Fine-tuned model |
|---|---|---|
| Consumer behavior | Reports 5% instead of 35%; omits population scope. | Omits the percentage and population scope. |
| Country coverage | Does not explicitly apply the warning or explain its limits. | Does not explicitly apply the warning or explain its limits. |
| Monthly trends | Correct “No,” but no explanation or recommended comparison. | Ambiguous conclusion; no coverage explanation or recommended comparison. |
| Product demand | Says negative units instead of zero. | Omits zero balance and gives an unsupported explanation. |
| Competitor research | Correctly names Retailer F; omits GBP 2700 difference and scope. | Incorrectly names Retailer E; omits the difference and scope. |

Complete-answer score:
- Original model: 0/5.
- Fine-tuned model: 0/5.

Competitor identification was correct before fine-tuning and incorrect
after fine-tuning. This is an observed regression on one example.

## Interpretation and Limitations

Lower validation loss did not establish improved factual reliability.
The original model produced nonempty answers on all five revised test
prompts, but this does not resolve its earlier failures on different prompts.

The dataset is a small pilot. One test example per task cannot establish
reliable task-level performance or support a quantitative fairness claim.
Synthetic scenarios share reasoning patterns with training examples, so
separate IDs and group labels do not establish broad generalization.

The model should not be relied on for unsupervised business decisions.

These test results have now been reviewed. If they guide further changes,
this set must be described as a development or regression set, and a new
reserved test set is needed for a fresh final evaluation.