# Extra Trees precision experiment

Date: 2026-10-27. Calibration selected `incumbent`. The candidate did not pass all development promotion checks; the incumbent remains selected.

## Scope and frozen search

Three ExtraTreesClassifier models were fitted: raw features without class
weighting, raw features with balanced training class weights, and signed-log
features with balanced weights. Each has 256 trees, maximum depth 20, minimum
leaf size 20, sqrt feature sampling, seed 24 and 2 workers. Median imputation
and any signed-log scales fit on training only. No new external data or
future-derived features were added.

Each model's sigmoid calibration used 2022 data. Four new-model mixture weights
0.25, 0.5, 0.75 and 1.0 yielded 12 candidates plus the incumbent. Candidate
selection maximized calibration precision at recall >=0.95, then AP, then
candidate ID. Only the winner proceeded to 2023 validation. Promotion requires
higher validation precision at recall >=0.95, AP no lower, and Brier/log loss
no higher. The search was fixed in `config/precision-extra-trees-v1.json`
before execution. Training has 484549 windows/8698 positives; calibration has
50756/421; validation has 60366/781. Reserved 2024–2025 data remained unopened.

## All calibration candidates

| candidate | recall | precision | fp | average_precision | brier | log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| incumbent | 0.950119 | 0.090662 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| extra_raw_w0.25 | 0.950119 | 0.084442 | 4337 | 0.288349 | 0.006959 | 0.027548 |
| extra_raw_w0.5 | 0.950119 | 0.072661 | 5105 | 0.282479 | 0.006977 | 0.027652 |
| extra_raw_w0.75 | 0.950119 | 0.068942 | 5402 | 0.250442 | 0.007038 | 0.027993 |
| extra_raw_w1 | 0.950119 | 0.064257 | 5825 | 0.211053 | 0.007141 | 0.028597 |
| extra_balanced_w0.25 | 0.950119 | 0.082902 | 4425 | 0.278416 | 0.007002 | 0.027736 |
| extra_balanced_w0.5 | 0.950119 | 0.078355 | 4705 | 0.260593 | 0.007070 | 0.027935 |
| extra_balanced_w0.75 | 0.950119 | 0.070299 | 5290 | 0.218370 | 0.007188 | 0.028370 |
| extra_balanced_w1 | 0.950119 | 0.064568 | 5795 | 0.177435 | 0.007356 | 0.029120 |
| extra_log_balanced_w0.25 | 0.950119 | 0.087623 | 4165 | 0.278113 | 0.007013 | 0.027768 |
| extra_log_balanced_w0.5 | 0.950119 | 0.079349 | 4641 | 0.261196 | 0.007091 | 0.027995 |
| extra_log_balanced_w0.75 | 0.950119 | 0.069252 | 5376 | 0.211912 | 0.007217 | 0.028449 |
| extra_log_balanced_w1 | 0.950119 | 0.064527 | 5799 | 0.161956 | 0.007392 | 0.029198 |

## Validation comparison

| metric | incumbent | candidate |
| --- | --- | --- |
| precision | 0.079622 | 0.079622 |
| recall | 0.950064 | 0.950064 |
| fp | 8577.000000 | 8577.000000 |
| fn | 39.000000 | 39.000000 |
| tp | 742.000000 | 742.000000 |
| tn | 51008.000000 | 51008.000000 |
| accuracy | 0.857271 | 0.857271 |
| balanced_accuracy | 0.903059 | 0.903059 |
| f1 | 0.146931 | 0.146931 |
| false_positive_rate | 0.143946 | 0.143946 |
| false_alarm_ratio | 0.920378 | 0.920378 |
| tss | 0.806118 | 0.806118 |
| average_precision | 0.220619 | 0.220619 |
| brier | 0.011195 | 0.011195 |
| log_loss | 0.043996 | 0.043996 |
| threshold | 0.009311 | 0.009311 |

## Conditional uncertainty

| model | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- |
| incumbent | recall | 0.877975 | 0.997118 | 1000 | 0 |
| incumbent | precision | 0.051430 | 0.111802 | 1000 | 0 |
| incumbent | false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| incumbent | false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| incumbent | brier | 0.007289 | 0.015279 | 1000 | 0 |
| selected | recall | 0.877975 | 0.997118 | 1000 | 0 |
| selected | precision | 0.051430 | 0.111802 | 1000 | 0 |
| selected | false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| selected | false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| selected | brier | 0.007289 | 0.015279 | 1000 | 0 |

These 95% intervals use 1000 whole-HARP bootstrap draws with seed 24 and fixed
model/threshold. They exclude training, calibration and selection uncertainty.
Calibration is reused for probability fitting and candidate selection; prior
validation results informed development. The result is adaptive development,
not an independent test or a guarantee of future recall. Counts describe
overlapping forecast windows, not independent flares or alerts. The threshold
is selected on validation, not transferred unchanged from calibration.

## What else could improve precision?

The incumbent's missed positive windows are concentrated in these regions:

| harp | positive_windows | missed_windows |
| --- | --- | --- |
| 9152 | 24 | 22 |
| 9584 | 48 | 12 |
| 8990 | 47 | 3 |
| 9091 | 24 | 2 |

HARP 9152 and 9584 account for 34 of the 39 missed windows. Independently audit
their flare associations, original timestamps and measurement quality. This
is a diagnostic priority, not evidence that their labels are wrong. Do not
remove difficult regions or change labels merely to improve metrics.

Next, materialize longer histories from raw, unfiltered observations and test
24/48-hour changes, persistence and flux evolution against the same population.
Earlier retained labeled windows alone are unsuitable history inputs: their
inclusion can depend on future label exclusions. Historical flare features
also require verified report availability and region-association provenance.
Finally, compare candidate families with additional chronological development
folds to reduce dependence on one calibration year. These are hypotheses for
future experiments, not improvements demonstrated by this run.

The following is an unchanged-incumbent threshold diagnostic:

| recall | precision | fp | fn | threshold |
| --- | --- | --- | --- | --- |
| 0.950064 | 0.079622 | 8577 | 39 | 0.009311 |
| 0.900128 | 0.098515 | 6433 | 78 | 0.016103 |
| 0.800256 | 0.132415 | 4095 | 156 | 0.029984 |
| 0.500640 | 0.182115 | 1756 | 390 | 0.070622 |

Higher thresholds can raise precision by sacrificing recall. These rows are
not model improvements; the user objective remains recall >=0.95. They are
shown to distinguish operating-point changes from better ranking. A probability
calibration improvement alone does not guarantee precision at that operating point.

## Reproduction and evidence

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \
  --protocol config/precision-extra-trees-v1.json --output artifacts/precision_extra_trees_20261027_r1
.venv/bin/python scripts/report_extra_trees_precision.py --output artifacts/precision_extra_trees_audit_20261027_r1
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_extra_trees_20261027
```

Existing artifact directories are protected. Repeat using fresh paths and
update the reporting script's dated input paths accordingly. Both document
editions must be reviewed and registered before publication. The existing
dashboard model is not automatically replaced. Models, data, predictions and
HTML are local ignored artifacts; source code and these reports are committed.

| source | SHA-256 |
| --- | --- |
| artifacts/precision_extra_trees_20261027_r1/report.json | 86fe4cbf1c59e451a0f05b09614eb872c2efac217c3babf6ddf17477105b3ab3 |
| artifacts/precision_extra_trees_20261027_r1/calibration_candidates.csv | aa0528ffc5e40f6df4640387204dda174ae03b93b62709575b26b92ee29c7c52 |
| artifacts/precision_extra_trees_20261027_r1/validation_predictions.parquet | 615de72ac7bf51ab9436d7b790755c222635a2b893caa785b9ddd9e60757a445 |
| artifacts/experiment5_v2_development_20261026_r2/validation_predictions.parquet | 44a2852948b61cd8b42c77497588f16d76e601221ef1b2f8a923ede56b6d8bff |

