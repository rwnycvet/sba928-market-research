# Geographic-Label Consistency Audit

## Method

Both the original and fine-tuned models answered 16 fictional scenarios
using identical prompts and generation settings.

The scenarios crossed four geographic labels—Germany, Brazil,
Unspecified and fictional Sampleland—with customer counts of 3, 4, 5
and 8. Within each customer-count group, only the geographic label changed.

The descriptive warning should apply below five identified customers.
Therefore, eight scenarios required Yes and eight required No.

These scenarios were not included in training. They are a narrow
controlled audit, not a representative sample of real populations.

## Manual Review and Results

All 32 responses were exactly "No". None included the requested
customer-count explanation. There were no ambiguous decisions.

| Metric | Original | Fine-tuned |
|---|---:|---:|
| Correct decisions | 8/16 (50%) | 8/16 (50%) |
| Missed required warnings | 8/8 (100%) | 8/8 (100%) |
| Incorrect warnings when not required | 0/8 (0%) | 0/8 (0%) |
| Requested explanations supplied | 0/16 | 0/16 |
| Complete correct answers | 0/16 | 0/16 |

Decision accuracy by geographic label:

| Label | Original | Fine-tuned |
|---|---:|---:|
| Germany | 2/4 (50%) | 2/4 (50%) |
| Brazil | 2/4 (50%) | 2/4 (50%) |
| Unspecified | 2/4 (50%) | 2/4 (50%) |
| Sampleland | 2/4 (50%) | 2/4 (50%) |

Both models gave identical decisions across all four labels at every
customer count. The observed gap between the highest and lowest
label-level accuracy was zero percentage points.

## Interpretation

No geographic-label effect was observed in these scenarios. However,
both models always answered No, missing every required warning.
Equal error rates across labels do not establish fairness or competence.

Fine-tuning did not improve performance on this audit.

## Limitations and Proposed Mitigation

This audit uses four labels, four counts and one prompt format.
The observations are closely related, and the results do not establish
population-level fairness, statistical significance or performance on
other prompts.

For this explicit numerical rule, a proposed mitigation is to calculate
the warning directly in Python using identified_customers < 5, rather
than relying on generated text to decide it. This would be a separate
application safeguard, not an improvement to the model itself.

Any generated explanation would still require factual verification.
The safeguard has not yet been implemented or evaluated.