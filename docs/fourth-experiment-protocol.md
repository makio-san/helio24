# Experiment 4: recall-first model training

User-selected objective (2026-10-19): recall at least 95%, with fewer false
alarms. These are project operating objectives, not universal scientific
acceptability ranges. Accuracy is descriptive, not the optimization target.

Use the verified original SWAN-SF 96-feature tables. V2 is not compatible yet.
Fit on partitions 1–2, calibrate on partition 3, and compare on partition 4.
Do not load partition-5 feature/prediction data or any reserved 2024–2025 data.
Partition 4 has already been studied and is development/selection data, not
an untouched test. Keep all previous model artifacts and dashboard selections.

Apply the experiment-2 temporal boundaries and HARP exclusions, including the
already frozen partition-4 end boundary from its saved purge audit. Verify the
resulting train/calibration/validation row counts against experiment 2. Fit
median imputation on training only. Calibration fits on partition 3 only.

## Fixed training budget

Train eight deterministic XGBoost pipelines (seed 24, histogram tree method,
two threads, learning rate 0.04). All use the same training records and original
features. No early stopping on partition 4 and no adaptively expanded search.

| Candidate | Trees | Depth | Minimum child weight | L2 | Gamma | Positive weight | Region weighting |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| control | 200 | 3 | 5 | 5 | 0 | 1 | No |
| shallow | 600 | 2 | 5 | 5 | 0 | 1 | No |
| depth4 | 600 | 4 | 5 | 5 | 0 | 1 | No |
| depth5 | 600 | 5 | 5 | 5 | 0 | 1 | No |
| depth6 | 800 | 6 | 5 | 5 | 0 | 1 | No |
| regularized | 600 | 4 | 20 | 20 | 0.2 | 1 | No |
| positive_weight | 600 | 4 | 5 | 5 | 0 | 3 | No |
| region_weight | 600 | 4 | 5 | 5 | 0 | 1 | Equal total training weight per HARP |

Subsample and column subsample are 1. Region weights are inverse training-region
window counts, normalized to mean one; no evaluation labels enter those weights.
Fit a strictly monotonic sigmoid calibrator for each model. Save raw and
calibrated probability scores and reliability bins without choosing a calibrator
using later-period outcomes.

## Thresholds, selection and target comparison

For each candidate, select a partition-4 threshold with the fewest false alarms
among thresholds attaining 95% empirical recall; highest threshold breaks ties.
This measures development ranking quality at the requested recall. Attainment
of recall on this same threshold-selection set is not evidence of generalization.
Also report 90% and 99% operating points as sensitivity, not alternative winners.

Separately select the 95% threshold on partition 3 and freeze it before reading
partition-4 scores. Report its transfer to partition 4 without adjustment. These
rows show whether high recall transfers over time, even if the primary
development comparison chooses another operating point. Do not conflate the
two threshold roles.

Rank candidates at 95% development recall by false positives, then descending
AP, then Brier, then candidate name. A promising candidate must improve on the
retrained control's false positives, have AP at least as high, and calibrated
Brier and log loss no worse than the calibrated control. The stretch target is
at least 10% fewer false alarms at recall >=95%, alongside those probability
quality checks. This reduction is a project improvement target, not a universal
metric cutoff. Report each failed check, not only the selected model.

Reproduce the old experiment-2 validation control at its 95% recall operating
point (TP=1023, FP=5183, FN=53, TN=44372); fail closed on disagreement. This
comparison uses identical evaluation records. The old retrospective 91.82%
recall at the 95% validation target remains historical context, not a tuning
signal or a new test in this experiment.

Report accuracy, balanced accuracy, F1, recall, precision, FPR, false-alarm
ratio, TSS, AP, Brier, log loss, thresholds and all confusion counts. Compare
recall to 95%, false positives to the control and the 10% reduction target,
and probability scores to the control. Do not assign arbitrary accuracy/AP
or Brier cutoffs independent of class prevalence and reference performance.

For control and the most promising candidate (or the best-ranked candidate if
none qualifies), report 1,000 HARP-cluster bootstrap intervals at frozen
thresholds. Clearly state these exclude training and selection uncertainty.
Save every fitted candidate, split audit, predictions, decisions, source/code
hashes, metrics and a standalone report under ignored artifacts/experiment4/.

Stop this batch after the eight declared fits and report whether targets were
met. Any follow-up training needs an explicit new protocol and remains
development work; repeatedly evaluating an inspected holdout cannot produce
an independent success claim. No automatic dashboard deployment follows.

Parameter semantics: [official XGBoost documentation](https://xgboost.readthedocs.io/en/stable/parameter.html).
