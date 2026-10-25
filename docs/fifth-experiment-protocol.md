# Experiment 5: later-period evaluation protocol

Design date: 2026-10-23. Status: **design frozen; execution blocked by the
unfinished data contract**. This protocol contains no new performance result.
Its machine-readable counterpart is `config/experiment5.json`. Changes require
a new version and explanation before fitting, never a silent post-test revision.

## Prediction question and scope

Using the preceding 12 hours of measurements, estimate the probability of at
least one M/X flare peak in `[forecast_time, forecast_time + 24h)` for a HARP.
This is the existing peak-based benchmark target, not a claim to predict flare
onset, Earth impact or satellite damage. A HARP may contain multiple NOAA regions.
Report the proportion of alarms preceding flare start separately when reliable
event identity and coverage permit it. Do not call window recall event recall.

## Frozen chronological design

All boundaries below are UTC; starts are inclusive and ends exclusive.

| Role | Start | End | Purpose |
| --- | --- | --- | --- |
| train | 2010-05-01 00:00 | 2022-01-01 00:00 | Fit preprocessing and models |
| calibration | 2022-01-01 00:00 | 2023-01-01 00:00 | Fit probability calibration |
| validation | 2023-01-01 00:00 | 2024-01-01 00:00 | Choose model and thresholds |
| test | 2024-01-01 00:00 | 2026-01-01 00:00 | One final evaluation after freezing |

Assign by forecast time, then retain only windows whose entire observation
and target interval fits inside that role. A target interval ending exactly
at the role boundary is allowed because its endpoint is exclusive. Drop
later-role rows whose HARP was retained in an earlier role. Reject duplicate
HARP/forecast keys. Record exclusions, retained regions, class counts and date
coverage. Do not relax rules or move dates because performance is disappointing.
Empty roles, absent classes or insufficient coverage block execution and require
a documented design revision before any model scores.

`development_split` accepts only HARP and explicit-time interval metadata;
it rejects labels/features and forecast times in the reserved test period.
It does not load files. Callers must filter at the storage-reader boundary,
not read test data first and drop it afterwards. A separate final-test runner
still needs implementation and review. These checks are workflow controls,
not a security barrier against arbitrary direct file access.

## Seven prerequisites before fitting

| Gate | Current status |
| --- | --- |
| measurement_semantics | pending |
| quality_policy | pending |
| utc_conversion | pending |
| label_inclusion_policy | pending |
| versioned_dataset_manifest | pending |
| development_coverage_audit | pending |
| training_runner_review | pending |

Measurement evidence must identify the production version and units/formulas,
including EPS. Quality policy must reproduce original flags or define and audit
a versioned alternative on old development data. UTC conversion and interval
conventions must be explicit. Unresolved event identities must not silently
become negative examples: freeze confidence, ambiguity and exclusion rules
before constructing targets. The exact V2 label contract is still pending.

The dataset manifest must pin files, hashes, schema, feature/label/quality
versions, extraction code and environment, and document that the final period
has not influenced selection. Development coverage must be audited before fitting.
Gate strings are review declarations, not automatic proof of scientific validity.
Keep them pending until evidence is recorded and reviewed; also freeze the
execution contract before `require_training_ready` can succeed. No training
runner for this protocol is delivered in this preparation step.

## Fixed candidate budget and preprocessing

Fit only three methods, without a hyperparameter search:

| ID | Fixed design |
| --- | --- |
| baseline | Constant training positive-window prevalence |
| logistic | C=1.0, lbfgs, max_iter=2000, no class weighting, seed=24 |
| xgboost | 200 trees, depth=3, learning_rate=0.04, min_child_weight=5, L2=5, gamma=0, positive weight=1, subsample=1, column subsample=1, hist, threads=2, seed=24 |

Use the existing 24 unweighted magnetic quantities and their mean, standard
deviation, last value and delta: 96 features, subject to the compatibility gate.
Keep the historical extraction definition; do not substitute weighted columns
or fit an empirical EPS conversion. Only pre-issue measurements may contribute;
no interpolation from later observations. Apply the frozen quality policy first.
Median imputation with missing indicators fits on training only. Standard scaling
for logistic regression also fits on training only. XGBoost is unscaled.
Convergence failure is a reported failure, not permission for an adaptive search.

Fit a positive-slope sigmoid on calibration data for each learned model;
save raw and calibrated probabilities, but use calibrated scores for selection.
The constant baseline is not calibrated. No early stopping on validation or
test. Do not pool calibration/validation into a refit after threshold selection.
Existing V1 models remain historical references unless the bridge is validated;
do not compare counts across different sample populations as improvement evidence.

## Selection, success criteria and final evaluation

On validation, choose the threshold minimizing false positives subject to
recall >=0.95, breaking ties with the highest threshold. Save 0.90 and 0.99
operating points as sensitivity results, not alternative winner criteria.
Rank learned candidates by FP ascending, AP descending, Brier ascending, ID.
Logistic replaces the XGBoost control only if it has fewer FP, AP no lower,
and Brier/log loss no higher. Otherwise retain control. A 10% FP reduction
relative to control is an improvement target, not a universal scientific cutoff.
If neither learned model beats the training-prevalence baseline in validation
AP, Brier and log loss, report failure and do not open the final test.

Before final access, freeze the selected model, control, baseline, preprocessing,
calibrators, thresholds, dataset/protocol hashes and package versions in an
immutable decision manifest. The final runner must reserve a one-time evaluation
record before reading outcomes; a failed attempt must be recorded rather than
silently rerun to select a better result. No test-based changes to features,
labels, model or threshold are allowed. After inspection, further iterations
need another holdout or must be called retrospective.

On the same eligible test rows, report the selected model, control and baseline
at their frozen thresholds. Recall >=0.95 is the primary requested target;
it is not guaranteed by achieving it on validation. Report FP counts, FPR,
precision, FAR, accuracy, balanced accuracy, F1, TSS, AP, Brier, log loss,
confusion counts and reliability bins. Show the missed target explicitly.
Compare FP reductions only alongside achieved recall; a loss of recall is not
an alarm-quality improvement. A candidate improvement claim requires at least
95% test recall, at least 10% fewer FP than control, AP no lower and Brier/log
loss no higher. Control retained as winner cannot claim improvement over itself.
These are point-estimate project criteria, not statistical significance claims.

Use 1,000 whole-HARP bootstrap draws with seed 24 for 95% intervals at frozen
thresholds; paired differences use the same resampled regions. These intervals
exclude training/selection uncertainty and do not prove solar-cycle robustness.
Report window-level and eligible event-level analyses separately. No automatic
dashboard replacement or live deployment follows from the test.

## Preparation outputs and reproduction

```sh
python scripts/check_evaluation_protocol.py
python scripts/publish_reports.py --output artifacts/bilingual_reports_protocol5
```

The preflight reads configuration only, records code/document hashes under
`artifacts/experiment5_preflight/`, and exits with code 2 while prerequisites
are unresolved. Existing output directories are preserved; use `--output` for
a new revision. It never reads observations, labels or model predictions.
Current real-data row counts and final-test performance are intentionally
unreported because the executable data contract has not passed its gates.
