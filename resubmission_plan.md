# SBA 928 Resubmission Plan

## Prompt experiment
On six original validation examples, exact-match results were:
- Minimal: 2/6
- Format: 3/6
- Grounded: 4/6

These are development results, not final test results.

## Revised training task families

1. Consumer behavior
   Interpret purchase frequency from supplied customer summaries.
   Distinguish repeat purchasing from retention.

2. Market trends
   Compare complete monthly periods.
   Flag partial months and avoid unsupported seasonal claims.

3. Product demand and inventory
   Compare positive sales with cancellation-inclusive quantities.
   Avoid exact reorder recommendations without inventory evidence.

4. Country sales and coverage
   Report supplied figures accurately.
   Apply customer-count warnings correctly and preserve geographic labels.

5. Competitor research
   Identify evidence needed for fair competitor comparisons.
   State when competitor performance cannot be determined from the supplied data.

## Evaluation safeguards
Keep variations of the same source example in the same split.
Retain the original test examples as regression checks.
Reserve fresh evaluation cases before training or prompt selection.
Label synthetic examples explicitly and report their results separately.
Measure numerical correctness, unsupported claims, format adherence,
and correct application of evidence limitations.