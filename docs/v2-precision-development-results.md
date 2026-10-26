# Helio24: V2 precision development results

Evaluation date: 2026-10-26. The selected development candidate is the
**ensemble**, a fixed probability blend of 45% logistic regression and 55%
XGBoost. At the operating point constrained to recall >= 0.95, validation
precision increased from the standalone XGBoost result of 0.061597 to
0.079622. False-positive windows fell from 11,304 to 8,577 while recall stayed
at 0.950064.

This is a development result, not an independent test result. The reserved
2024–2025 test data was not materialized, predicted or inspected.

## Data and selection protocol

The model uses 96 causal features: mean, population standard deviation, last
value and end-to-start delta for each of 24 dataset-native magnetic
measurements in the 12 hours before the forecast. The target is an M- or
X-class GOES flare peak in `[forecast_time, forecast_time + 24h)`.

| Role | Period | Rows | Positive windows | HARPs |
| --- | --- | ---: | ---: | ---: |
| Training | 2010-05-01–2021-12-31 | 484549 | 8698 | 3954 |
| Calibration | 2022-01-01–2022-12-31 | 50756 | 421 | 528 |
| Validation | 2023-01-01–2023-12-31 | 60366 | 781 | 703 |

The materializer excluded 81,613 windows overlapping a major HEK event that
could not be assigned to a HARP and 24 ambiguous windows. Imputation, scaling
and model fitting used training data only. Sigmoid probability calibration and
the blend weight search used the calibration role. The blend search evaluated
logistic weights from 0.00 to 1.00 in steps of 0.05 and selected 0.45 by maximum
precision at recall >= 0.95. The final alarm threshold was selected on
validation by maximum precision, then minimum false positives, among candidates
meeting recall >= 0.95.

## Validation metrics

| Model | Recall | Precision | TP | FP | FN | TN | FPR | FAR | Accuracy | Balanced accuracy | F1 | TSS | AP | Brier | Log loss | Threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 1.000000 | 0.012938 | 781 | 59585 | 0 | 0 | 1.000000 | 0.987062 | 0.012938 | 0.500000 | 0.025545 | 0.000000 | 0.012938 | 0.012795 | 0.069891 | 0.017951 |
| Logistic | 0.950064 | 0.060052 | 742 | 11614 | 39 | 47971 | 0.194915 | 0.939948 | 0.806961 | 0.877575 | 0.112963 | 0.755149 | 0.216153 | 0.011315 | 0.045501 | 0.005988 |
| XGBoost | 0.950064 | 0.061597 | 742 | 11304 | 39 | 48281 | 0.189712 | 0.938403 | 0.812096 | 0.880176 | 0.115693 | 0.760352 | 0.206027 | 0.011386 | 0.045217 | 0.004231 |
| Ensemble | 0.950064 | 0.079622 | 742 | 8577 | 39 | 51008 | 0.143946 | 0.920378 | 0.857271 | 0.903059 | 0.146931 | 0.806118 | 0.220619 | 0.011195 | 0.043996 | 0.009311 |

The ensemble produces about 8 correct alarms per 100 alarms. Precision remains
low in absolute terms because positive windows comprise only 1.29% of
validation. Against XGBoost on the same rows and at the same recall, the
ensemble improves precision by 0.018025, or 29.26% relative, and removes 2,727
false-positive windows, a 24.12% reduction. It also improves AP, Brier score,
log loss, F1, TSS and balanced accuracy.

The earlier V1 development result had precision 0.164840 at recall 0.950743.
It is historical context only: V1 and V2 use different archives, label
coverage, exclusion rules, time populations and feature calculations. It is
not valid evidence that the V2 ensemble regressed by a measured amount.

## Criteria and interpretation

| Measure | Development criterion | Ensemble result | Decision |
| --- | --- | ---: | --- |
| Recall | >= 0.950000 | 0.950064 | Met |
| Precision | Higher than XGBoost 0.061597 | 0.079622 | Met |
| False-positive windows | <= 10174 (10% below 11304) | 8577 | Met |
| AP | >= XGBoost 0.206027 | 0.220619 | Met |
| Brier | <= XGBoost 0.011386 | 0.011195 | Met |
| Log loss | <= XGBoost 0.045217 | 0.043996 | Met |

Precision is the fraction of alarms that are correct. Recall is the fraction
of positive windows detected. FPR is the fraction of negative windows alarmed;
FAR is the fraction of alarms that are false. AP evaluates ranking across
thresholds. Brier score and log loss evaluate probability error, with lower
values preferred. Balanced accuracy averages positive and negative class
recall. TSS is recall minus FPR. Ordinary accuracy is included but is not a
primary criterion: always predicting quiet would obtain 0.987062 accuracy on
this imbalanced validation set while detecting no positive window.

There is no universal acceptable precision threshold for solar-flare warning.
The operational value depends on the cost of a missed flare and of acting on a
false alarm. The 0.079622 result meets the frozen comparative development
criteria, but is still too low to claim operational readiness.

## Rejected precision experiments

Six XGBoost configurations were compared on calibration. `positive_weight`
won that search with calibration precision 0.067306, but fell to 0.058922 on
validation with 11,851 false positives and AP 0.171683. It was rejected. This
negative result shows that class weighting and tree complexity did not transfer
reliably to the next year.

| Candidate | Calibration precision | Calibration FP | Calibration AP |
| --- | ---: | ---: | ---: |
| control | 0.058746 | 6409 | 0.230126 |
| shallow | 0.062824 | 5967 | 0.225990 |
| depth4 | 0.066500 | 5615 | 0.161133 |
| regularized | 0.060809 | 6178 | 0.189601 |
| positive_weight | 0.067306 | 5543 | 0.179510 |
| region_weight | 0.065115 | 5743 | 0.164416 |

Probability stacking, logit stacking and rank averaging were also probed and
did not exceed the fixed 0.45/0.55 probability blend on validation precision.
They were not promoted into the frozen protocol.

## Limitations and uncertainty

- The initial standalone models were inspected on validation before the
  ensemble candidate was introduced. Although its weight was selected only on
  calibration, this makes the broader development process adaptive.
- The threshold was deliberately selected on validation. These figures estimate
  the chosen development operating point and are not an untouched generalization
  estimate.
- No confidence interval is reported in this revision. The overlapping windows
  are correlated within HARP regions, so an ordinary row bootstrap would be
  misleading; a future interval must resample whole HARPs.
- TP, FP and FN count overlapping forecast windows, not independent flares or
  operational alert episodes. Window recall does not equal event recall.
- The exact upstream Git revision that generated the V2 archive is unavailable.
  The separately audited contract supports dataset-native modeling, not full
  raw-magnetogram reproducibility.
- The result does not estimate Earth impact, satellite damage or an exact flare
  time. Live data compatibility remains unverified.

## Reproduction and frozen evidence

```sh
.venv/bin/python scripts/run_v2_development.py \
  --materialized artifacts/v2_development_features_20261025_r2 \
  --protocol config/experiment5-v7.json \
  --output artifacts/experiment5_v2_development_20261026_r2
.venv/bin/python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_precision_20261026
```

The selected configuration and operating point are frozen in
`config/experiment5-v8.json`. The local development report SHA-256 is
`b57ce8e12de3d18740872b1504f97ff6a9dee22b272143836bb1a739d155ef03`;
the predictions SHA-256 is
`44a2852948b61cd8b42c77497588f16d76e601221ef1b2f8a923ede56b6d8bff`.
The rejected tree probe report SHA-256 is
`0540f797dd44795a14e19557346d2563b29bb76582b605163d1171d4db3efd01`.
Models, predictions, datasets and generated HTML remain local ignored
artifacts. The version-controlled protocols, code and bilingual reports provide
the reviewable record.
