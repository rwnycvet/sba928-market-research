# Fine-Tuning Experiment Evaluation

## Method
FLAN-T5 Small was fine-tuned for three epochs using 78 rule-based training examples representing 26 country labels. Six separate country labels were used for validation and six for testing. Training variations shared the same underlying country evidence and were not independent observations.

The experiment used a batch size of four and a learning rate of 0.00005. Epoch 3 was selected using validation loss. Original and fine-tuned responses used identical generation settings.

## Results
Validation loss decreased from 3.1394 to 0.4642. However, manual review showed that improved prediction of reference wording did not establish reliable factual accuracy.

All six original-model test responses were empty. The fine-tuned model generated text for all six, but only three revenue amounts were correct. Four responses incorrectly claimed fewer than five identified customers, and four omitted a recommendation.

Validation responses showed similar problems. The model mislabeled “Unspecified” as Canada, invented figures for Lebanon, and repeatedly applied small-sample warnings to groups above the stated threshold.

## Bias and Fairness
The model did not consistently apply evidence-based coverage warnings. Incorrectly describing countries as having small samples could distort marketing decisions. “Unspecified” represents missing geographic information and must not be reassigned to a country without evidence.

Every test example had a 0% missing-CustomerID rate, limiting evaluation of missing-data handling. The validation example with missing IDs exposed a failure, but one example cannot establish general performance.

## Limitations and Conclusion
This was a small country-brief pilot using templated targets from one retailer. It did not evaluate all market-research tasks. A tied-weights loading warning remained unresolved, limiting confidence in the baseline comparison.

Fine-tuning improved response generation and validation loss but did not demonstrate dependable market-research accuracy or fairness. Generated briefs require verification against calculated evidence.

Future work should investigate loading behavior, improve training-example diversity, and evaluate numerical accuracy and conditional warnings on validation data. Any changes informed by the reviewed test results require a fresh untouched test set before claiming generalization.