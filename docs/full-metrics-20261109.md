# Full metrics at the project operating point (2026-11-09)

## Purpose and scope

This report lists every project metric for the frozen annual V2 baseline at the operating point defined in
[operating-point-decision-20261109.md](operating-point-decision-20261109.md): the threshold chosen on the prior
calibration year at window recall 0.90, applied unchanged to the next year. It is descriptive. No model, threshold,
label or feature was changed, and the reserved 2024–2025 test was not accessed. The frozen definition is
[`config/full-metrics-v1.json`](../config/full-metrics-v1.json).

The baseline is the original 96-feature ensemble (0.45 logistic + 0.55 XGBoost, sigmoid-calibrated), evaluated
on the development years 2014, 2015, 2016, 2017, 2022 and 2023. 2018 has zero positives and is not reported.

## Counts

| year | windows | positive windows | TP | FP | FN | TN |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 75228 | 2310 | 2007 | 7634 | 303 | 65284 |
| 2015 | 69138 | 1355 | 1308 | 6294 | 47 | 61489 |
| 2016 | 42987 | 181 | 162 | 1303 | 19 | 41503 |
| 2017 | 19529 | 253 | 235 | 1035 | 18 | 18241 |
| 2022 | 50756 | 421 | 414 | 8949 | 7 | 41386 |
| 2023 | 60366 | 781 | 653 | 4852 | 128 | 54733 |

## Threshold metrics

| year | threshold | accuracy | always-negative accuracy | recall | precision | F1 | balanced accuracy | FPR | FAR | TSS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.0324 | 0.8945 | 0.9693 | 0.8688 | 0.2082 | 0.3359 | 0.8821 | 0.1047 | 0.7918 | 0.7641 |
| 2015 | 0.0407 | 0.9083 | 0.9804 | 0.9653 | 0.1721 | 0.2921 | 0.9362 | 0.0929 | 0.8279 | 0.8725 |
| 2016 | 0.0539 | 0.9692 | 0.9958 | 0.8950 | 0.1106 | 0.1968 | 0.9323 | 0.0304 | 0.8894 | 0.8646 |
| 2017 | 0.0219 | 0.9461 | 0.9870 | 0.9289 | 0.1850 | 0.3086 | 0.9376 | 0.0537 | 0.8150 | 0.8752 |
| 2022 | 0.0110 | 0.8235 | 0.9917 | 0.9834 | 0.0442 | 0.0846 | 0.9028 | 0.1778 | 0.9558 | 0.8056 |
| 2023 | 0.0242 | 0.9175 | 0.9871 | 0.8361 | 0.1186 | 0.2078 | 0.8773 | 0.0814 | 0.8814 | 0.7547 |

## Probability and ranking metrics

| year | prevalence | AP | ROC AUC | Brier | log loss |
| --- | --- | --- | --- | --- | --- |
| 2014 | 0.0307 | 0.5079 | 0.9498 | 0.0207 | 0.0765 |
| 2015 | 0.0196 | 0.4924 | 0.9781 | 0.0136 | 0.0478 |
| 2016 | 0.0042 | 0.3664 | 0.9899 | 0.0033 | 0.0145 |
| 2017 | 0.0130 | 0.8117 | 0.9891 | 0.0049 | 0.0205 |
| 2022 | 0.0083 | 0.2800 | 0.9698 | 0.0071 | 0.0292 |
| 2023 | 0.0129 | 0.2206 | 0.9509 | 0.0112 | 0.0440 |

## 95% intervals

Whole-HARP bootstrap, 1000 draws, seed 24, threshold fixed. Intervals exclude model refitting uncertainty and all
solar-cycle shifts.

| year | recall | precision | F1 | balanced accuracy | FPR | FAR | TSS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.7722–0.9283 | 0.1327–0.2868 | 0.2278–0.4372 | 0.8352–0.9154 | 0.0803–0.1303 | 0.7132–0.8673 | 0.6705–0.8308 |
| 2015 | 0.9107–0.9930 | 0.1069–0.2401 | 0.1917–0.3856 | 0.9085–0.9552 | 0.0676–0.1201 | 0.7599–0.8931 | 0.8170–0.9103 |
| 2016 | 0.3182–1.0000 | 0.0122–0.2039 | 0.0235–0.3357 | 0.6497–0.9886 | 0.0163–0.0493 | 0.7961–0.9878 | 0.2995–0.9771 |
| 2017 | 0.7692–1.0000 | 0.0397–0.4693 | 0.0763–0.6227 | 0.8601–0.9800 | 0.0204–0.0946 | 0.5307–0.9603 | 0.7201–0.9601 |
| 2022 | 0.9357–1.0000 | 0.0222–0.0724 | 0.0434–0.1350 | 0.8764–0.9243 | 0.1420–0.2158 | 0.9276–0.9778 | 0.7528–0.8486 |
| 2023 | 0.7245–0.9257 | 0.0765–0.1630 | 0.1367–0.2735 | 0.8209–0.9227 | 0.0605–0.1030 | 0.8370–0.9235 | 0.6418–0.8454 |

## Unweighted mean over the six years

| metric | mean |
| --- | --- |
| accuracy | 0.9099 |
| recall | 0.9129 |
| precision | 0.1398 |
| f1 | 0.2376 |
| balanced_accuracy | 0.9114 |
| fpr | 0.0902 |
| far | 0.8602 |
| tss | 0.8228 |
| ap | 0.4465 |
| roc_auc | 0.9713 |
| brier | 0.0101 |
| log_loss | 0.0388 |

The mean is a summary of six adaptive development years with different prevalence, not a pooled estimate.

## Status against targets

- Recall: delivered 0.8361–0.9834 against the 0.90 target; 2014, 2016 and 2023 fall below it.
- Precision: 0.0442–0.2082; the earlier 0.30 target is not reached in any year.
- FAR is 1 − precision (0.7918–0.9558).
- Accuracy is below the always-negative accuracy in every year, so it is not a useful objective.
- TSS 0.7547–0.8752, balanced accuracy 0.8773–0.9376 and ROC AUC 0.9498–0.9899 are high; these are not limited by prevalence the way precision is.
- AP is 0.2206–0.8117, strongly year dependent (2017 highest, 2023 lowest).
- No frozen acceptance threshold exists for F1, balanced accuracy, TSS, AP, Brier or log loss; they are reported only.

## Limits

These are adaptive development years that were already inspected, not an independent test. Counts are overlapping
forecast windows, not physical flares. Brier and log loss reflect calibration, discrimination and data uncertainty
together.

## Reproduction

```sh
python -m scripts.audit_full_metrics --output artifacts/full_metrics_20261109_r1
```

Inputs: `artifacts/temporal_years_20261101_r1` (baseline column of `predictions.parquet`) and
`artifacts/operating_point_review_20261109_r1/deployable_thresholds.json` (recall target 0.9). Output hashes are in
`artifacts/full_metrics_20261109_r1/report.json` (config sha256 `82366e0b8630a83709be6e9e67317e30a4824f704dcfeb3139244548a82e5f76`, thresholds sha256
`bd4594e2ab0e5ebcdc58cc438b59f7a213828fa3dfdd5b5dfb9c7fcb0df3d6c0`). Existing output is not overwritten.
