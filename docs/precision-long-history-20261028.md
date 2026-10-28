# Long-history precision experiment

Calibration selected `incumbent`. The selected candidate did not pass all development diagnostic promotion checks. Precision changed by 0.000000
percentage points in the matched-recall validation diagnostic. The dashboard model
has not been replaced. See the separate transferred-threshold results before
interpreting these values as operational performance.

## Data and features

The completed materialization verified exactly 595671 original forecast keys.
Training contains 484549 windows/8698 positives; calibration contains 50756/421;
validation contains 60366/781. Training precedes 2022 calibration and 2023 validation.
Reserved 2024–2025 observations and labels were excluded at the logical reader boundary;
archive bytes containing those years were downloaded only for integrity verification.
No labels or retained forecasts were changed. Features use raw observations, independently
of outcome-based row exclusions. The previous disk-space blocker was cleared.

Each 24/48-hour history adds mean, population standard deviation, endpoint change and
normalized change for 24 magnetic measurements, plus coverage/missing indicators:
196 new features, 292 total. Complete cadence requires 120/240 observations strictly
before the forecast. Histories crossing a role boundary, cadence gap or leap-second
transition are unavailable; rows are retained. A measurement needs 80% finite values.
Normalized change divides endpoint change by absolute mean plus standard deviation,
clipped to [-100, 100]; a zero denominator produces a missing value. Availability is
temporal coverage, not an instrument-quality guarantee.

| role | available_24h | available_48h |
| --- | --- | --- |
| train | 446081 | 378074 |
| calibration | 46861 | 39785 |
| validation | 55856 | 47776 |

## Frozen search

Three candidates use signed-log logistic regression (C=1), XGBoost (200 trees, depth 3)
and histogram gradient boosting (200 iterations, 15 leaves). Full parameters and source
hashes are frozen in `config/precision-long-history-v2.json`. Preprocessing fits on training only;
sigmoid calibration fits on calibration. New-model mixture weights 0.25, 0.5, 0.75 and
1.0 produce 12 candidates plus the incumbent. Selection maximizes calibration precision
at recall >=0.95, then AP, then candidate ID. Only the selected candidate is evaluated
on validation. The incumbent remains the 0.45 logistic/0.55 XGBoost ensemble.

| candidate | precision | recall | fp | average_precision | brier | log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| incumbent | 0.090662 | 0.950119 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| history_logistic_w0.25 | 0.087032 | 0.950119 | 4196 | 0.310089 | 0.006871 | 0.027349 |
| history_logistic_w0.5 | 0.087432 | 0.950119 | 4175 | 0.320887 | 0.006799 | 0.027140 |
| history_logistic_w0.75 | 0.085561 | 0.950119 | 4275 | 0.315636 | 0.006768 | 0.027160 |
| history_logistic_w1 | 0.060341 | 0.950119 | 6229 | 0.308453 | 0.006779 | 0.027556 |
| history_xgboost_w0.25 | 0.086040 | 0.950119 | 4249 | 0.296323 | 0.006952 | 0.027592 |
| history_xgboost_w0.5 | 0.082389 | 0.950119 | 4455 | 0.296497 | 0.006940 | 0.027540 |
| history_xgboost_w0.75 | 0.073046 | 0.950119 | 5076 | 0.289074 | 0.006949 | 0.027618 |
| history_xgboost_w1 | 0.064683 | 0.950119 | 5784 | 0.278489 | 0.006978 | 0.027875 |
| history_hist_w0.25 | 0.082372 | 0.950119 | 4456 | 0.291551 | 0.006968 | 0.027668 |
| history_hist_w0.5 | 0.084104 | 0.950119 | 4356 | 0.281037 | 0.006998 | 0.027838 |
| history_hist_w0.75 | 0.080354 | 0.950119 | 4578 | 0.257176 | 0.007072 | 0.028249 |
| history_hist_w1 | 0.065349 | 0.950119 | 5721 | 0.232070 | 0.007192 | 0.028970 |

## Matched-recall development diagnostic

| metric | incumbent | selected |
| --- | --- | --- |
| precision | 0.079622 | 0.079622 |
| recall | 0.950064 | 0.950064 |
| tp | 742.000000 | 742.000000 |
| fp | 8577.000000 | 8577.000000 |
| fn | 39.000000 | 39.000000 |
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

These thresholds are reselected using validation labels to compare precision at
recall >=0.95. They are not thresholds transferred from calibration. Diagnostic promotion
requires higher precision, AP no lower, and Brier/log loss no higher, with recall >=0.95.
Passing this comparison alone does not establish a deployable 95% recall operating point.

## Interpretation and next development step

The strongest new calibration candidate was `history_logistic_w0.5`: precision
0.087432 versus 0.090662 for the incumbent,
with 4175 versus 4012 false-positive windows.
Its AP was 0.320887 versus 0.286706.
Improved overall ranking therefore did not translate into better precision at the
required high-recall operating point in calibration. This does not prove that longer
history is intrinsically unhelpful; it rejects these specific candidates and summaries.

The next research step is additional chronological development folds, with alarm
thresholds fitted on each earlier calibration period and transferred unchanged to the
following period. This should measure the stability of both precision and recall before
another broad parameter search. Any new search needs a frozen budget and must retain
the reserved test. This step has not been executed in this experiment.

## Frozen calibration thresholds on validation

| metric | incumbent | selected |
| --- | --- | --- |
| precision | 0.103397 | 0.103397 |
| recall | 0.884763 | 0.884763 |
| tp | 691.000000 | 691.000000 |
| fp | 5992.000000 | 5992.000000 |
| fn | 90.000000 | 90.000000 |
| tn | 53593.000000 | 53593.000000 |
| accuracy | 0.899248 | 0.899248 |
| balanced_accuracy | 0.892100 | 0.892100 |
| f1 | 0.185155 | 0.185155 |
| false_positive_rate | 0.100562 | 0.100562 |
| false_alarm_ratio | 0.896603 | 0.896603 |
| tss | 0.784201 | 0.784201 |
| average_precision | 0.220619 | 0.220619 |
| brier | 0.011195 | 0.011195 |
| log_loss | 0.043996 | 0.043996 |
| threshold | 0.018203 | 0.018203 |

These thresholds were recorded before validation evaluation and were not adjusted to
validation labels. This table measures temporal transfer of the selected alarm policy;
recall can fall below 0.95. It is distinct from the matched-recall diagnostic above.

## Uncertainty and limitations

| evaluation | model | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- | --- |
| validation_reselected | incumbent | recall | 0.877975 | 0.997118 | 1000 | 0 |
| validation_reselected | incumbent | precision | 0.051430 | 0.111802 | 1000 | 0 |
| validation_reselected | incumbent | false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| validation_reselected | incumbent | false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| validation_reselected | incumbent | brier | 0.007289 | 0.015279 | 1000 | 0 |
| validation_reselected | selected | recall | 0.877975 | 0.997118 | 1000 | 0 |
| validation_reselected | selected | precision | 0.051430 | 0.111802 | 1000 | 0 |
| validation_reselected | selected | false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| validation_reselected | selected | false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| validation_reselected | selected | brier | 0.007289 | 0.015279 | 1000 | 0 |
| calibration_transferred | incumbent | recall | 0.792142 | 0.959200 | 1000 | 0 |
| calibration_transferred | incumbent | precision | 0.067199 | 0.143637 | 1000 | 0 |
| calibration_transferred | incumbent | false_positive_rate | 0.076680 | 0.124274 | 1000 | 0 |
| calibration_transferred | incumbent | false_alarm_ratio | 0.856363 | 0.932801 | 1000 | 0 |
| calibration_transferred | incumbent | brier | 0.007289 | 0.015279 | 1000 | 0 |
| calibration_transferred | selected | recall | 0.792142 | 0.959200 | 1000 | 0 |
| calibration_transferred | selected | precision | 0.067199 | 0.143637 | 1000 | 0 |
| calibration_transferred | selected | false_positive_rate | 0.076680 | 0.124274 | 1000 | 0 |
| calibration_transferred | selected | false_alarm_ratio | 0.856363 | 0.932801 | 1000 | 0 |
| calibration_transferred | selected | brier | 0.007289 | 0.015279 | 1000 | 0 |

Intervals use 1000 whole-HARP bootstrap draws, seed 24, conditional on fitted models
and thresholds. They omit training, calibration and model-selection uncertainty.
Calibration is reused for probability fitting and candidate selection; earlier validation
findings guided this experiment. This is adaptive development, not an independent test.
Counts refer to overlapping forecast windows, not independent flares or alert episodes.
Longer histories do not resolve uncertain event-region associations. No future precision
or recall level is guaranteed. Accuracy is the fraction of all correct predictions;
precision is the positive fraction among alarms; recall is the caught fraction among
positive windows. AP measures ranking across thresholds; lower Brier/log loss indicates
better probabilistic scoring. There is no universal acceptable precision independent
of event prevalence and the cost of false alarms.

## Reproduction and evidence

```sh
.venv/bin/python scripts/materialize_long_history.py --output artifacts/long_history_20261028_r2 --workers 1
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \
  --protocol config/precision-long-history-v2.json --output artifacts/precision_long_history_20261028_r1
.venv/bin/python scripts/report_long_history_precision.py \
  --source artifacts/precision_long_history_20261028_r1 --report-name precision-long-history-20261028
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_precision-long-history-20261028
```

Existing outputs must remain frozen. For another run, choose fresh artifact directories
and document names; freeze the new materialization hash in a new protocol revision before
training. Review both document editions, then register their source hash and links in
`docs/reports.json` and `docs/reports.md` before publishing to a new HTML directory.
Raw data, models, predictions and generated HTML remain outside Git.

| source | SHA-256 |
| --- | --- |
| artifacts/precision_long_history_20261028_r1/report.json | 2fb929cda4dc9e39d198d3b3af5b9457f2f1fe3b8ac3d8d47f8d68f4c2cd77db |
| artifacts/precision_long_history_20261028_r1/calibration_candidates.csv | 8d5e44d793e96b742fbf6cff9cc71fcfd3459f9bc276934e82fb7ced090c6ab2 |
| artifacts/precision_long_history_20261028_r1/operating_thresholds.json | 46a82ab336b9934b63d4e0372fd72a9d1c615b9b38de5bd637ad65419f562ce5 |
| artifacts/precision_long_history_20261028_r1/validation_predictions.parquet | 615de72ac7bf51ab9436d7b790755c222635a2b893caa785b9ddd9e60757a445 |
| artifacts/long_history_20261028_r2/report.json | 5764eabdc9463a507b27759481982622fc406b6cabcadd64baf10d4236e51fee |

