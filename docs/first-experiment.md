# First experiment

Run date: 2026-10-12. Real SWAN-SF records; no synthetic training or evaluation data.

## Data

Official archives 1, 3 and 5 were verified with their published MD5 checksums.
The deterministic, class-blind 10% sample contains 19,088 windows. Nineteen
windows were excluded for excessive missing or untrusted measurements.
All retained labeled flare peaks passed the catalog-window check.

| Split | Partition | Windows | M/X windows | HARP regions |
| --- | --- | ---: | ---: | ---: |
| Train | 1 | 7,254 | 129 | 640 |
| Validation | 3 | 4,278 | 131 | 358 |
| Test | 5 | 7,537 | 97 | 669 |

The exact dates and region counts are generated in the notebook and local
`artifacts/report.json`. No cross-split boundary overlap or shared HARP required
removal in this sample. Partitions 2 and 4 were not used.

## Results

Model settings were fixed before testing. XGBoost was selected by validation
average precision (0.4023 versus 0.3778 for logistic regression). Its alarm
threshold, approximately 1.437%, maximizes validation TSS. The selected model
and thresholds were saved before evaluating test predictions.

| Model | Test recall | Test precision | False alarms | Misses | Average precision | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Constant baseline | 0.00% | 0.00% | 0 | 97 | 0.0129 | 0.01273 |
| Logistic regression | 96.91% | 12.11% | 682 | 3 | 0.3588 | 0.01036 |
| XGBoost | 95.88% | 14.98% | 528 | 4 | 0.4520 | 0.00896 |

XGBoost caught 93 of 97 positive windows, issuing 621 alarms. About 85% of its
alarms were false; its false-positive rate among negative windows was 7.10%.
The threshold deliberately favors recall. This is useful as a research starting
point, not evidence of operational readiness.

The baseline always predicts the training prevalence (1.7783%). Its TSS is zero
at every operating point; the tie-break selects no alarms. Precision is recorded
as zero when no alarms are issued and should be read with that convention.

## Interpretation limits

- These are results on a 10% sample, not all SWAN-SF records.
- Counts refer to forecast windows; one flare can label several overlapping windows.
- No independent-event recall or confidence intervals are claimed.
- Calibration bins and Brier scores are measured; no calibration model is fitted.
- The replay uses definitive archive measurements, not a proven historical live feed.
- The held-out test has now been inspected. Further tuning needs a new evaluation design.

The data contract and the notebook contain source links and the exact processing rules.

Environment: Python 3.14.3, pandas 3.0.6, NumPy 2.5.4, scikit-learn 1.9.1,
XGBoost 3.4.1. Model seeds are fixed at 24.
