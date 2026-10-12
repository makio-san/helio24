# Experiment 2: full-data probability evaluation

This protocol is fixed before inspecting the new experiment's results.
Experiment 1 remains the reference, including its already inspected partition 5.
No new, untouched final test is claimed.

| Role | Partitions | Use |
| --- | --- | --- |
| Training | 1, 2 | Fit one XGBoost with the original fixed settings |
| Calibration | 3 | Fit a sigmoid mapping on the frozen model's log odds |
| Validation | 4 | Compare raw/calibrated Brier scores and choose alarm thresholds |
| Retrospective audit | 5 | Report frozen operating points; previously inspected period |

Use every available record, retaining the original quality rules and magnetic
features. Purge preceding windows whose prediction interval reaches into the
next role's observations. Remove HARP identities shared with earlier roles.
Report removals, counts, date ranges and class distributions.

Freeze the first experiment's files and hashes under `artifacts/experiment1/`.
Write experiment 2 to `artifacts/experiment2/`; do not replace the dashboard's
model or its original results automatically.

Compare the original frozen sample model, the full-data raw XGBoost, a sigmoid
calibration of that same full-data model, and training prevalence as a reference.
The calibrator fits log loss on partition 3 only, with a strictly positive slope
so it preserves ranking. Its intercept is unconstrained. No hyperparameter search.
Prefer calibrated probabilities only if validation Brier is strictly lower;
report both regardless. Brier is not a pure measure of calibration, so also
report log loss and fixed probability-bin reliability tables with counts.

For each model and recall target 80%, 90%, 95%, select on partition 4 the
threshold with fewest false alarms among candidates meeting the target.
Break ties by the highest threshold. Freeze all thresholds before evaluating
partition 5. A validation recall target is not a guaranteed audit recall.
A strictly monotonic calibrator does not improve ranking; at matched operating
points raw and calibrated models should produce the same alarms.

Report recall, precision, false-positive rate, false-alarm ratio, counts,
average precision, Brier and log loss. Use 1,000 HARP-cluster bootstrap draws,
seed 24, for percentile 95% intervals in the retrospective audit. Resample whole
regions, retaining every window in a sampled region. Use the same resamples
for paired calibrated-minus-raw Brier differences. Report undefined-replicate
counts; do not substitute zero for undefined precision or recall.

These intervals describe region-sampling variability conditional on the fitted
models and frozen thresholds. They exclude training/calibrator uncertainty and
do not account for all dependence between distinct regions or solar-cycle shifts.
Metrics remain window-level, not unique-flare-event detection rates.

Only compressed archives and derived feature tables are needed. Stream the
archives instead of expanding all raw files because local disk space is limited.
Record source MD5, feature-code hash, protocol hash and package versions.

Reference: [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html).
