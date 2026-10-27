# Precision follow-up: comparison, experiments and uncertainty

Date: 2026-10-27. **Precision remains 0.079622 at recall 0.950064.** Six new
models and 24 probability mixtures did not beat the incumbent on calibration.
Neither experiment promoted a new model. The reserved 2024–2025 test stayed closed.

## Why the current number is below the historical number

| population | windows | positives | prevalence | recall | FPR | precision |
| --- | --- | --- | --- | --- | --- | --- |
| V1 historical | 50631 | 1076 | 0.021252 | 0.950743 | 0.104591 | 0.164840 |
| V2 incumbent | 60366 | 781 | 0.012938 | 0.950064 | 0.143946 | 0.079622 |

The previous 0.164840 came from V1 development; the current 0.079622 comes
from V2 validation in 2023. These are different populations, feature calculations,
label coverage and exclusion policies. The previously reported improvement
0.061597 to 0.079622 compared XGBoost with the ensemble on the same V2 rows.
It did not surpass the historical V1 number. Earlier updates did not make this
distinction sufficiently clear.

Precision obeys `recall * prevalence / (recall * prevalence + FPR * (1 - prevalence))`.
The V2 positive-window prevalence is lower, and its measured FPR is higher.
Both terms explain the numerical difference; these observations do not establish
which archive, label or modeling change caused it. As an algebraic illustration,
holding V2 recall and FPR fixed while substituting V1 prevalence gives precision
0.125347. This is a counterfactual calculation, not a measured model result.
Class imbalance alone is not an adequate explanation for the observed gap.

## Error concentration

Of 8577 false-positive windows, 2180 occur in the top 10 HARPs ranked by this
count. Another grouping finds 6815 in HARPs with no positive window in the
retained validation sample. This does not mean those regions never flared:
excluded windows and events outside the sample remain outside the statement.
These are retrospective diagnostics, never inference features or rules for
removing difficult negatives. Counts refer to overlapping forecast windows,
not independent flare events or alarm episodes.

## Bounded experiments

The signed-log experiment fitted median imputation, training-column median
absolute scales, sign-preserving `log1p`, standardization and logistic regression
on training data. The C values were 0.1, 1 and 10. The histogram experiment
fitted HistGradientBoostingClassifier with 15 or 31 leaves, 200 iterations,
learning rate 0.05, minimum leaf size 100 and L2 regularization 10. A third
histogram candidate used 15 leaves and training dates from 2018 onward.
Early stopping was disabled to avoid a random internal validation split.

For each of these six models, sigmoid calibration used 2022 data. The new
model's probability weight was 0.25, 0.5, 0.75 or 1.0; the remaining weight
went to the fixed incumbent. Each bounded search was recorded in its JSON
protocol before execution. Selection used calibration precision at recall
>= 0.95, then AP and candidate ID. Only the selected candidate proceeded to
validation; both searches selected the incumbent. No rejected candidate was
searched on validation. All calibration candidates are retained below.

| experiment | candidate | recall | precision | fp | average_precision | brier | log_loss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| log | incumbent | 0.950119 | 0.090662 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| log | signed_log_C0.1_w0.25 | 0.950119 | 0.088731 | 4108 | 0.299169 | 0.006920 | 0.027359 |
| log | signed_log_C0.1_w0.5 | 0.950119 | 0.089686 | 4060 | 0.309379 | 0.006873 | 0.027081 |
| log | signed_log_C0.1_w0.75 | 0.950119 | 0.087989 | 4146 | 0.314496 | 0.006845 | 0.026924 |
| log | signed_log_C0.1_w1 | 0.950119 | 0.086356 | 4232 | 0.317257 | 0.006835 | 0.026905 |
| log | signed_log_C1_w0.25 | 0.950119 | 0.088613 | 4114 | 0.299178 | 0.006919 | 0.027345 |
| log | signed_log_C1_w0.5 | 0.950119 | 0.089606 | 4064 | 0.309647 | 0.006873 | 0.027066 |
| log | signed_log_C1_w0.75 | 0.950119 | 0.087970 | 4147 | 0.315106 | 0.006844 | 0.026918 |
| log | signed_log_C1_w1 | 0.950119 | 0.086599 | 4219 | 0.317389 | 0.006835 | 0.026919 |
| log | signed_log_C10_w0.25 | 0.950119 | 0.088378 | 4126 | 0.298702 | 0.006919 | 0.027361 |
| log | signed_log_C10_w0.5 | 0.950119 | 0.089226 | 4083 | 0.308675 | 0.006872 | 0.027091 |
| log | signed_log_C10_w0.75 | 0.950119 | 0.087508 | 4171 | 0.314680 | 0.006844 | 0.026950 |
| log | signed_log_C10_w1 | 0.950119 | 0.086263 | 4237 | 0.317655 | 0.006834 | 0.026953 |
| hist | incumbent | 0.950119 | 0.090662 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| hist | hist15_w0.25 | 0.950119 | 0.088633 | 4113 | 0.279769 | 0.007012 | 0.027771 |
| hist | hist15_w0.5 | 0.950119 | 0.088281 | 4131 | 0.261276 | 0.007075 | 0.027923 |
| hist | hist15_w0.75 | 0.950119 | 0.079036 | 4661 | 0.218524 | 0.007174 | 0.028229 |
| hist | hist15_w1 | 0.950119 | 0.072569 | 5112 | 0.185202 | 0.007309 | 0.028734 |
| hist | hist31_w0.25 | 0.950119 | 0.086806 | 4208 | 0.274914 | 0.007030 | 0.027964 |
| hist | hist31_w0.5 | 0.950119 | 0.086337 | 4233 | 0.246827 | 0.007128 | 0.028340 |
| hist | hist31_w0.75 | 0.950119 | 0.079067 | 4659 | 0.198751 | 0.007276 | 0.028919 |
| hist | hist31_w1 | 0.950119 | 0.070572 | 5268 | 0.161461 | 0.007475 | 0.029793 |
| hist | hist15_recent_w0.25 | 0.950119 | 0.079161 | 4653 | 0.285137 | 0.007040 | 0.029004 |
| hist | hist15_recent_w0.5 | 0.950119 | 0.066401 | 5624 | 0.245625 | 0.007275 | 0.030771 |
| hist | hist15_recent_w0.75 | 0.950119 | 0.055264 | 6838 | 0.128351 | 0.007688 | 0.033388 |
| hist | hist15_recent_w1 | 0.950119 | 0.040912 | 9377 | 0.069388 | 0.008281 | 0.038475 |

## Current validation metrics

| metric | value |
| --- | --- |
| precision | 0.079622 |
| recall | 0.950064 |
| fp | 8577.000000 |
| fn | 39.000000 |
| tp | 742.000000 |
| tn | 51008.000000 |
| accuracy | 0.857271 |
| balanced_accuracy | 0.903059 |
| f1 | 0.146931 |
| false_positive_rate | 0.143946 |
| false_alarm_ratio | 0.920378 |
| tss | 0.806118 |
| average_precision | 0.220619 |
| brier | 0.011195 |
| log_loss | 0.043996 |
| threshold | 0.009311 |

The development promotion rule required increased precision at recall >= 0.95,
nondecreasing AP and nonincreasing Brier and log loss. No candidate passed the
first selection step, so the frozen ensemble and threshold remain selected.
The models and prediction artifacts used for the existing dashboard were not
replaced. There was no improvement in this follow-up; failed searches are evidence.

## Conditional uncertainty

| metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- |
| recall | 0.877975 | 0.997118 | 1000 | 0 |
| precision | 0.051430 | 0.111802 | 1000 | 0 |
| false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| brier | 0.007289 | 0.015279 | 1000 | 0 |

Intervals are 95% percentile intervals from 1000 whole-HARP bootstrap draws,
seed 24, with the model and threshold held fixed. They exclude training,
calibration, model-selection and threshold-selection uncertainty and do not
validate future recall. In particular, the recall lower bound is below 0.95.
The same calibration data was used for probability calibration and candidate
selection, so calibration scores are optimistic development scores. Validation
had already informed previous model design; this remains adaptive development.
No independent test result or operational readiness is claimed.

## Next research direction

The bounded model-only searches did not improve precision. The next experiment
should add information known at forecast time, such as verified prior-flare
history and richer magnetic evolution, with availability times and region
associations audited before training. New features may help, but improvement is
not guaranteed. The existing recall constraint remains 0.95; raising the alarm
threshold and silently reducing recall would change the user's objective.

## Reproduction and evidence

```sh
OMP_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \
  --protocol config/precision-log-v1.json --output artifacts/precision_log_20261027_r1
OMP_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \
  --protocol config/precision-hist-v1.json --output artifacts/precision_hist_20261027_r1
.venv/bin/python scripts/report_precision_followup.py --output artifacts/precision_followup_20261027_r1
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_precision_followup_20261027
```

Commands refuse existing artifact directories; use fresh paths for a repeat,
and pass those paths to the reporting script after adapting its input paths.
The reporting script uses the dated input paths shown above. It creates a new
error audit and the paired Markdown documents. Review both editions and refresh
the catalog source hash before publishing if their content changes.

| source | SHA-256 |
| --- | --- |
| artifacts/precision_log_20261027_r1/report.json | 5708ccbb3e6e41735ae41a110ccdc81635e62aac5f6771e7d0cb7697017d6c57 |
| artifacts/precision_hist_20261027_r1/report.json | 56cce200d82344533b630f92b1c81f60c81df711dee9a213c86d47ca2354b69d |
| artifacts/precision_log_20261027_r1/calibration_candidates.csv | 9e5069c5d67a5f21bc1583812633e5295938f0f5d27467926b20727150208805 |
| artifacts/precision_hist_20261027_r1/calibration_candidates.csv | 35b32b13a0c8d8f68acb8470fb539dbdd4f0c47f6a4de8f4a142b5d13dd303e1 |
| artifacts/experiment5_v2_development_20261026_r2/validation_predictions.parquet | 44a2852948b61cd8b42c77497588f16d76e601221ef1b2f8a923ede56b6d8bff |

Source code and protocols are committed; data, models, predictions and generated
HTML remain ignored local artifacts. Previous reports and experiment outputs
are preserved. Historical comparison source: [recall-first results](recall-first-results.en.md).
