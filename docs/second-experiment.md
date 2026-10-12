# Experiment 2: full-data calibration audit

The full-data experiment is complete. Calibration slightly improved probability
scores, but the paired uncertainty interval does not establish a clear improvement.
False alarms remain a major limitation. No dashboard model was replaced.

## Protocol and coverage

The [protocol](second-experiment-protocol.md) was committed before these results
were inspected. All five official archives were checked against their published
MD5 values. Of 331,185 windows, 2,284 failed the existing measurement-quality rule.
Another 2,279 windows were removed at chronological boundaries. No shared-HARP
or duplicate removals were needed after boundary purging.

| Role | Partitions | Retained windows | M/X windows | HARPs |
| --- | --- | ---: | ---: | ---: |
| Training | 1, 2 | 159,247 | 2,522 | 1,569 |
| Calibration | 3 | 41,470 | 1,322 | 384 |
| Threshold validation | 4 | 50,631 | 1,076 | 470 |
| Retrospective audit | 5 | 75,274 | 990 | 753 |

Partition 5 was inspected during experiment 1. These results are a retrospective
audit, **not a new untouched final test**. Fixed XGBoost settings were reused.
Calibration fits a positive-slope sigmoid on log odds using partition 3 only.
Partition 4 selects probability preference and operating thresholds. All decisions
were saved before generating partition 5 predictions.

## Probability calibration

| Model | Validation Brier | Audit Brier | Audit log loss |
| --- | ---: | ---: | ---: |
| Frozen sample model | 0.015489 | 0.009569 | 0.034322 |
| Full-data raw model | 0.014855 | 0.009450 | 0.033363 |
| Full-data calibrated model | 0.014832 | 0.009337 | 0.033344 |

Validation Brier selected calibrated probabilities. The paired audit Brier
difference, calibrated minus raw, was **−0.000113**. The 95% HARP-cluster bootstrap
interval was **[−0.000628, +0.000332]**. Because it crosses zero, the small point
improvement should not be presented as a reliable gain.

Brier combines calibration, discrimination and outcome uncertainty; it is not a
pure calibration measure. The local report includes reliability plots and bin
counts. Higher-probability bins have fewer observations and need caution.

## Recall and false alarms

The following targets were selected on validation data; their audit recall is
not guaranteed to equal the target. Thresholds refer to calibrated probabilities.

| Validation recall target | Threshold | Audit recall | Audit precision | False alarms | Misses |
| --- | ---: | ---: | ---: | ---: | ---: |
| 80% | 6.8845% | 87.17% | 22.59% | 2,958 | 127 |
| 90% | 4.7999% | 90.61% | 19.00% | 3,824 | 93 |
| 95% | 3.4028% | 91.82% | 16.27% | 4,678 | 81 |

At the 90% validation target, the original frozen model reached 89.60% audit
recall with 3,933 false alarms; the full-data model reached 90.61% with 3,824.
This is a descriptive comparison, not proof of general improvement. At the 95%
validation target, the original model's audit recall was higher (93.84%), with
more false alarms (5,738). There is no uniformly superior operating point.

Raw and calibrated full-data models produced identical alarms at corresponding
recall targets, as expected from a monotonic probability transformation.
Calibration changes probability interpretation, not the ranking of windows.

For the 90% target, whole-HARP 95% intervals were:

- Recall: **80.09%–96.65%**.
- Precision: **11.86%–27.30%**.
- False-positive rate: **3.66%–6.82%**.

About 81% of alarms at that operating point were false. It remains a research
prototype; the audit does not justify switching on live alerts.

## Reproduction and limitations

Commands are in the [README](../README.md#experiment-2-full-data-calibration).
The ignored `artifacts/experiment2/report.html` is a standalone report with
figures, complete metrics, bin counts and bootstrap intervals. CSV/JSON outputs
include input hashes, source archive checksums, calibrator parameters, thresholds,
package versions and source-code hashes. Original artifacts remain byte-identical
to the frozen experiment 1 snapshot.

Bootstrap draws resample whole HARP regions 1,000 times, using seed 24. Intervals
are conditional on the fitted models and thresholds; they exclude fitting
uncertainty, cross-region dependence and future solar-cycle shifts. Counts are
forecast windows, not unique flare events. Full-data training also extends the
training period; this experiment does not isolate the effect of sample size.

The next modeling experiment should target better discrimination, with its
evaluation plan fixed before fitting. Repeatedly tuning against this audit period
would invalidate any claim that it is a fresh final evaluation. Additional
untouched later-period data is needed for that claim.
