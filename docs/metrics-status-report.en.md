# Helio24 — Consolidated metrics report

Report date: 16 October 2026. This document consolidates saved experiment
results; it contains no new model training or test result. Recent source
reviews did not change labels or performance figures.

## Headline results

| Metric | Dashboard model: initial test | Full data: validation | Full data: later-period audit |
| --- | ---: | ---: | ---: |
| Accuracy | %92,94 | %91,37 | %94,80 |
| Recall | %95,88 | %90,06 | %90,61 |
| Precision | %14,98 | %18,52 | %19,00 |
| F1 | 0,2591 | 0,3072 | 0,3141 |
| Balanced accuracy | %94,39 | %90,73 | %92,73 |
| False positive rate | %7,10 | %8,60 | %5,15 |
| False alarm ratio | %85,02 | %81,48 | %81,00 |
| TSS | 0,8878 | 0,8145 | 0,8546 |
| Average precision (AP) | 0,4520 | 0,4720 | 0,4340 |
| Brier score | 0,008956 | 0,014832 | 0,009337 |
| Log loss | 0,030966 | 0,052204 | 0,033344 |
| Alarm threshold | %1,437 | %4,800 | %4,800 |
| Windows | 7.537 | 50.631 | 75.274 |
| Positive windows | 97 | 1.076 | 990 |
| TP: true alarms | 93 | 969 | 897 |
| FP: false alarms | 528 | 4.264 | 3.824 |
| FN: missed positives | 4 | 107 | 93 |
| TN: true negatives | 6.912 | 45.291 | 70.460 |
| Total alarms | 621 | 5.233 | 4.721 |

The dashboard uses experiment 1's XGBoost. The other two columns belong to
experiment 2's full-data XGBoost with sigmoid calibration. Accuracy, F1 and
balanced accuracy were calculated from the saved confusion counts.

The initial test and full-data audit cover different samples. Validation was
used for threshold and model selection. The later period is partition 5,
which has already been inspected; it cannot now be called an untouched final
test. Counts represent potentially overlapping forecast windows, not physical flares.

## Interpretation

The full-data model has 897 true alarms and 3,824 false alarms in the later
period. It catches approximately 91% of positive windows, but about 81% of
alarms are false. False-alarm burden is the main limitation.

Always predicting negative achieves 98.68% accuracy on that period but zero
recall. Accuracy alone is therefore not the objective. AP summarizes
precision–recall performance; it is not trapezoidal PR-AUC. Brier alone is not
a pure calibration measure.

## General meaning of the metrics and criteria

A metric's mathematical range is different from an acceptance criterion. The
ideal endpoint is mathematically defined, but there is no universal rule such
as precision above 50% being “good” for every problem. Acceptance limits must
be set in advance from event prevalence, the cost of misses and false alarms,
forecast horizon, sampling unit and evaluation split. Helio24 criteria therefore
apply only under the same label, window and data split.

| Metric | What does it generally measure? | Mathematical range; ideal | Helio24 acceptance rule |
| --- | --- | --- | --- |
| Accuracy | Fraction of all examples classified correctly: `(TP+TN)/N` | `[0,1]`; `1` | No fixed target; reported with the always-negative baseline |
| Recall / TPR / POD | Fraction of actual positives detected: `TP/(TP+FN)` | `[0,1]`; `1` | Primary target `>=0.95` |
| Precision | Fraction of issued positive alarms that are correct: `TP/(TP+FP)` | `[0,1]`; `1` | No standalone threshold; reduce FP while recall is `>=0.95` |
| F1 | Harmonic mean of precision and recall | `[0,1]`; `1` | Secondary reporting; no frozen threshold |
| Balanced accuracy | Mean of positive recall and negative recall | `[0,1]`; `1`; balanced no-skill reference about `0.5` | Secondary reporting; no frozen threshold |
| FPR | Fraction of actual negatives receiving a false alarm: `FP/(FP+TN)` | `[0,1]`; `0` | Minimize subject to recall `>=0.95` |
| FAR | Fraction of all issued alarms that are false: `FP/(TP+FP)`; `1-precision` | `[0,1]`; `0` | Secondary alarm burden; no separate threshold |
| TSS | Difference between positive detection and false-positive rates: `recall-FPR` | `[-1,1]`; `1`; `0` means no skill | Secondary discrimination measure; no frozen threshold |
| AP | Precision–recall ranking quality across all thresholds | `[0,1]`; `1`; random baseline approximately positive prevalence | A new candidate must not fall below the control's `0.471980` |
| Brier | Mean squared error between forecast probability and binary outcome | `[0,1]`; `0` | A new candidate must not exceed `0.014832` |
| Log loss | Logarithmic loss of probability assigned to the true class; heavily penalizes confident errors | `[0,+∞)`; `0` | A new candidate must not exceed `0.052204` |
| Alarm threshold | Probability cutoff used to turn a probability into an alarm | `[0,1]`; no ideal endpoint | Selected on validation and frozen for later evaluation |

The recall-first experiment additionally requires fewer than 5,183 false
positives; the stronger improvement target is at least a 10% reduction to
4,664 or fewer. These values are not universal scientific standards. They are
Helio24's frozen operational comparison rules. Brier and log loss reflect
calibration, discrimination and data uncertainty together; reliability bins
are inspected separately for calibration.

## Uncertainty and thresholds

Later-period 95% intervals at the full-data model's 90% validation recall
target come from 1,000 whole-HARP bootstrap draws:

| Metric | Point estimate | 95% interval |
| --- | ---: | ---: |
| Recall | %90,61 | %80,09–96,65 |
| Precision | %19,00 | %11,86–27,30 |
| False positive rate | %5,15 | %3,66–6,82 |
| False alarm ratio | %81,00 | %72,70–88,14 |
| Brier | 0,009337 | 0,005959–0,013718 |

These intervals exclude model refitting uncertainty and all solar-cycle
shifts. Calibrated-minus-raw Brier is −0.000113, with a 95% interval
[−0.000628, 0.000332]. Because it includes zero, calibration cannot be
claimed to have delivered a definite improvement.

| Validation recall target | Fixed threshold | Later-period recall | Precision | False alarms |
| --- | ---: | ---: | ---: | ---: |
| %80 | %6,884 | %87,17 | %22,59 | 2.958 |
| %90 | %4,800 | %90,61 | %19,00 | 3.824 |
| %95 | %3,403 | %91,82 | %16,27 | 4.678 |

The target recall is not guaranteed on the later period. No new threshold
was selected by examining the audit results.

## Event-level results and experiment 3

The initial development event mapping detected 86/87 events (98.85%).
Across six mapping rules, 84 of the common 85 events assigned to the same
HARP were detected (98.82%). The initial fully covered 24-hour subset had
47/47 detections. These rates are conditional on mapping and coverage,
not general final-test performance.

Of 333 alarm episodes, 280 consisted entirely of negative-label windows.
False-alarm burden was 4,264 region-hours, 8.42% of monitored region-hours.
The longest entirely negative episode lasted 127 hours. Median warning
before event start was 22.99 hours for detected events. Long episodes may
cover multiple events; this does not guarantee independent, accurate early warnings.

Experiment 3's temporal-feature candidate achieved later-period accuracy
94.24%, recall 91.82%, precision 17.59%, and AP 0.4905. It was not selected
because it failed the development acceptance rules. A favorable later-period
metric was not used to reverse that decision.

## Full report and reproduction

```sh
python scripts/report_metrics.py
```

The command validates 50 saved model/threshold results and writes the original
Turkish `report.html` with embedded figures and CSV tables under
`artifacts/metrics_summary/`. `all_metrics.csv` covers all experiments;
`headline_metrics.csv` holds the three headline results. Other tables hold
thresholds, intervals, reliability bins, event analysis and mapping sensitivity.
`report.json` stores source and output SHA-256 hashes. Existing output is not overwritten.

Raw data and generated reports remain outside Git. This summary, reporting
code and tests are version controlled. Previous experiment files are preserved.

Status at the time of this report: [three-event source review](event-source-review.md).
Next stage: [preparation for a later-period evaluation](next-evaluation-plan.md).

Definitions: [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html),
[scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html),
[solar-flare forecasting evaluation framework](https://academic.oup.com/mnras/article/495/3/3332/5835694).
