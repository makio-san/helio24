# Threshold selection v2 results: the baseline arm passes the gate, and no prior-year rule passes

## Decision and scope

The [frozen v2 protocol](threshold-selection-v2-protocol-20261108.md) was run once on the frozen annual
predictions of the completed seven-year comparison (source report SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`). The thresholds were chosen from the
calibration windows of the year before each evaluation year only, were written to disk and hashed (SHA256
`0cd0c51e523f9ded6e7f20bfc059b1e4855cf3f7e57ee5a27ed0a50e29c5a0f2`) before any evaluation label was read, and the control rule reproduced the stored baseline
threshold in every year. No model was trained or recalibrated, no label changed and the reserved 2024–2025 test
stayed closed.

Decisions:

1. The feasibility gate passed for the baseline arm in all seven years, so the arm is evaluable. Recomputed
   probabilities equal the frozen ones exactly.
2. No rule passes in all six positive years. `w93` passes in 3 of 6 years and `w90`, `run95` and `run90` each
   pass in 2 of 6.
3. Nothing is adopted. No alert, threshold or model changes. A prior-year recall target is an unreliable guide
   for the threshold in this record, for the baseline arm as it was for both TCN arms.

## Feasibility gate

| check | result |
| --- | --- |
| G1 | 20 of 20 |
| G2 | 7 of 7 |
| G3 | 7 of 7 |
| G4 | 7 of 7 |

The identity check recomputes the calibrated ensemble probability of the stored frozen models with inference only
and compares it with the `baseline` column of the frozen predictions. It uses no label.

| year | stored threshold | recomputed threshold | rows matched | max abs difference |
| --- | --- | --- | --- | --- |
| 2014 | 0.011475 | 0.011475 | 75228 | 0.0 |
| 2015 | 0.018839 | 0.018839 | 69138 | 0.0 |
| 2016 | 0.030831 | 0.030831 | 42987 | 0.0 |
| 2017 | 0.012000 | 0.012000 | 19529 | 0.0 |
| 2018 | 0.004351 | 0.004351 | 7799 | 0.0 |
| 2022 | 0.008994 | 0.008994 | 50756 | 0.0 |
| 2023 | 0.018203 | 0.018203 | 60366 | 0.0 |

All seven stored model files matched their frozen SHA256 values. The recomputed control threshold also equals the
threshold stored in the walk-forward artifact for `ensemble` in every year.

## Acceptance outcome

| arm | rule | years_met | required_years | all_year_primary |
| --- | --- | --- | --- | --- |
| baseline | w93 | 3 | 6 | no |
| baseline | w90 | 2 | 6 | no |
| baseline | run95 | 2 | 6 | no |
| baseline | run90 | 2 | 6 | no |

A rule must satisfy all four per-year conditions in all six positive years.

| year | rule | episode_precision_higher | fp_lower | positive_runs_alarmed_not_below | recall_drop_ok | primary_met |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | w93 | yes | yes | no | yes | no |
| 2014 | w90 | yes | yes | no | no | no |
| 2014 | run95 | yes | yes | no | yes | no |
| 2014 | run90 | yes | yes | no | no | no |
| 2015 | w93 | yes | yes | yes | yes | yes |
| 2015 | w90 | yes | yes | yes | no | no |
| 2015 | run95 | yes | yes | yes | no | no |
| 2015 | run90 | yes | yes | no | no | no |
| 2016 | w93 | yes | yes | yes | no | no |
| 2016 | w90 | yes | yes | yes | no | no |
| 2016 | run95 | yes | yes | yes | no | no |
| 2016 | run90 | yes | yes | no | no | no |
| 2017 | w93 | yes | yes | yes | yes | yes |
| 2017 | w90 | yes | yes | yes | yes | yes |
| 2017 | run95 | yes | yes | yes | yes | yes |
| 2017 | run90 | yes | yes | yes | yes | yes |
| 2022 | w93 | yes | yes | yes | yes | yes |
| 2022 | w90 | yes | yes | yes | yes | yes |
| 2022 | run95 | yes | yes | yes | yes | yes |
| 2022 | run90 | yes | yes | yes | yes | yes |
| 2023 | w93 | no | yes | yes | no | no |
| 2023 | w90 | yes | yes | no | no | no |
| 2023 | run95 | yes | yes | no | no | no |
| 2023 | run90 | yes | yes | no | no | no |

The two years in which all four rules pass are 2017 and 2022. In 2016 and 2023 no rule keeps the window recall
drop within 0.02. In 2014, `w93` and `run95` fail on alarmed positive runs (79 against 80 for the control), and
`w90` and `run90` fail on the recall drop. In 2015 only `w93` passes.

## Metrics by year and rule

The control is `control_w95`. Recall and counts are for the evaluation year. Calibration recall is measured on
the calibration windows used to select the threshold.

| year | rule | threshold | ratio to control | calibration recall | evaluation recall | FP windows | episodes | episode precision | alarmed positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control_w95 | 0.0115 | 1.0000 | 0.9503 | 0.9455 | 13886 | 686 | 0.0977 | 80 of 83 |
| 2014 | w93 | 0.0135 | 1.1754 | 0.9301 | 0.9407 | 12895 | 634 | 0.1057 | 79 of 83 |
| 2014 | w90 | 0.0324 | 2.8212 | 0.9005 | 0.8688 | 7634 | 483 | 0.1636 | 77 of 83 |
| 2014 | run95 | 0.0164 | 1.4335 | 0.9192 | 0.9290 | 11607 | 613 | 0.1126 | 79 of 83 |
| 2014 | run90 | 0.0561 | 4.8866 | 0.8159 | 0.7684 | 5158 | 411 | 0.1971 | 72 of 83 |
| 2015 | control_w95 | 0.0188 | 1.0000 | 0.9502 | 0.9934 | 11453 | 568 | 0.0669 | 51 of 51 |
| 2015 | w93 | 0.0269 | 1.4257 | 0.9303 | 0.9897 | 9048 | 480 | 0.0813 | 51 of 51 |
| 2015 | w90 | 0.0407 | 2.1597 | 0.9000 | 0.9653 | 6294 | 378 | 0.1138 | 51 of 51 |
| 2015 | run95 | 0.0407 | 2.1597 | 0.9000 | 0.9653 | 6294 | 378 | 0.1138 | 51 of 51 |
| 2015 | run90 | 0.0576 | 3.0587 | 0.8398 | 0.9240 | 4410 | 298 | 0.1477 | 49 of 51 |
| 2016 | control_w95 | 0.0308 | 1.0000 | 0.9506 | 0.9724 | 2289 | 204 | 0.0196 | 7 of 7 |
| 2016 | w93 | 0.0380 | 1.2311 | 0.9306 | 0.9448 | 1825 | 183 | 0.0273 | 7 of 7 |
| 2016 | w90 | 0.0539 | 1.7473 | 0.9004 | 0.8950 | 1303 | 144 | 0.0347 | 7 of 7 |
| 2016 | run95 | 0.0687 | 2.2274 | 0.8620 | 0.8729 | 1013 | 116 | 0.0517 | 7 of 7 |
| 2016 | run90 | 0.1025 | 3.3238 | 0.7616 | 0.8343 | 602 | 88 | 0.0455 | 6 of 7 |
| 2017 | control_w95 | 0.0120 | 1.0000 | 0.9503 | 0.9368 | 1287 | 85 | 0.0588 | 5 of 6 |
| 2017 | w93 | 0.0143 | 1.1935 | 0.9337 | 0.9328 | 1223 | 83 | 0.0602 | 5 of 6 |
| 2017 | w90 | 0.0219 | 1.8211 | 0.9006 | 0.9289 | 1035 | 64 | 0.0781 | 5 of 6 |
| 2017 | run95 | 0.0578 | 4.8197 | 0.7901 | 0.9249 | 645 | 56 | 0.0893 | 5 of 6 |
| 2017 | run90 | 0.0578 | 4.8197 | 0.7901 | 0.9249 | 645 | 56 | 0.0893 | 5 of 6 |
| 2022 | control_w95 | 0.0090 | 1.0000 | 0.9510 | 0.9857 | 10072 | 622 | 0.0257 | 16 of 16 |
| 2022 | w93 | 0.0094 | 1.0464 | 0.9314 | 0.9857 | 9803 | 605 | 0.0264 | 16 of 16 |
| 2022 | w90 | 0.0110 | 1.2186 | 0.9020 | 0.9834 | 8949 | 538 | 0.0316 | 16 of 16 |
| 2022 | run95 | 0.0115 | 1.2804 | 0.8824 | 0.9834 | 8700 | 540 | 0.0315 | 16 of 16 |
| 2022 | run90 | 0.0115 | 1.2804 | 0.8824 | 0.9834 | 8700 | 540 | 0.0315 | 16 of 16 |
| 2023 | control_w95 | 0.0182 | 1.0000 | 0.9501 | 0.8848 | 5992 | 475 | 0.0842 | 36 of 38 |
| 2023 | w93 | 0.0209 | 1.1481 | 0.9311 | 0.8630 | 5433 | 470 | 0.0830 | 36 of 38 |
| 2023 | w90 | 0.0242 | 1.3301 | 0.9002 | 0.8361 | 4852 | 442 | 0.0905 | 35 of 38 |
| 2023 | run95 | 0.0329 | 1.8075 | 0.7910 | 0.7721 | 3782 | 388 | 0.1108 | 33 of 38 |
| 2023 | run90 | 0.0366 | 2.0091 | 0.7767 | 0.7401 | 3421 | 370 | 0.1216 | 33 of 38 |

Where a rule passes, the gain is small. In 2022, `w90` lowers false-alarm windows from 10072 to 8949 and raises
episode precision from 0.0257 to 0.0316. The highest episode precision among passing cells is 0.0893, for `run95`
and `run90` in 2017, against 0.0588 for the control. Evaluation recall can fall well below calibration recall: for the control
in 2023 it is 0.8848 against 0.9501.

## Year without positive windows

2018 has no positive windows, so recall-based conditions are not applicable and it is not gated. The table shows
false alarms only.

| rule | threshold | FP windows | episodes |
| --- | --- | --- | --- |
| control_w95 | 0.0044 | 359 | 30 |
| w93 | 0.0140 | 104 | 15 |
| w90 | 0.0529 | 1 | 1 |
| run95 | 0.0031 | 442 | 40 |
| run90 | 0.0031 | 442 | 40 |

## Uncertainty

Paired full-HARP bootstrap intervals (1000 draws, seed 24) of the differences against the control, for the six
positive years. A negative false-alarm difference means fewer false-alarm windows than the control. The
intervals are conditional on the frozen selected thresholds. They do not include the uncertainty of the
threshold selection itself, nor retraining uncertainty, and are not corrected for multiple comparisons.

| year | rule | episode precision diff lower | episode precision diff upper | FP window diff lower | FP window diff upper |
| --- | --- | --- | --- | --- | --- |
| 2014 | w93 | -0.0046 | 0.0208 | -1234.1 | -780.0 |
| 2014 | w90 | 0.0340 | 0.1015 | -7582.2 | -5007.9 |
| 2014 | run95 | -0.0025 | 0.0317 | -2774.1 | -1825.0 |
| 2014 | run90 | 0.0597 | 0.1466 | -10535.5 | -6973.9 |
| 2015 | w93 | 0.0035 | 0.0284 | -3015.2 | -1846.8 |
| 2015 | w90 | 0.0215 | 0.0808 | -6490.0 | -3996.9 |
| 2015 | run95 | 0.0215 | 0.0808 | -6490.0 | -3996.9 |
| 2015 | run90 | 0.0403 | 0.1338 | -8742.1 | -5428.7 |
| 2016 | w93 | -0.0002 | 0.0244 | -724.0 | -279.0 |
| 2016 | w90 | 0.0000 | 0.0418 | -1506.2 | -600.0 |
| 2016 | run95 | 0.0026 | 0.0913 | -1946.0 | -767.9 |
| 2016 | run90 | -0.0060 | 0.0531 | -2541.4 | -1068.8 |
| 2017 | w93 | -0.0056 | 0.0122 | -95.0 | -33.0 |
| 2017 | w90 | 0.0000 | 0.0704 | -401.0 | -124.0 |
| 2017 | run95 | -0.0031 | 0.1307 | -1019.0 | -293.9 |
| 2017 | run90 | -0.0031 | 0.1307 | -1019.0 | -293.9 |
| 2022 | w93 | -0.0002 | 0.0020 | -342.0 | -203.0 |
| 2022 | w90 | 0.0015 | 0.0129 | -1438.2 | -854.0 |
| 2022 | run95 | 0.0015 | 0.0125 | -1775.0 | -1044.8 |
| 2022 | run90 | 0.0015 | 0.0125 | -1775.0 | -1044.8 |
| 2023 | w93 | -0.0086 | 0.0066 | -724.0 | -408.0 |
| 2023 | w90 | -0.0087 | 0.0241 | -1463.0 | -845.0 |
| 2023 | run95 | 0.0008 | 0.0552 | -2778.2 | -1656.9 |
| 2023 | run90 | 0.0036 | 0.0725 | -3227.2 | -1936.8 |

## Limits

- The result is adaptive development evidence on already inspected years, not an independent test. Counts are
  overlapping forecast windows and groupings of them, not physical flares.
- Calibration years contain few positive runs in some cases (7 in the calibration year for 2017), so selected
  thresholds can be noisy. A failure shows that a prior-year recall target is an unreliable guide in this record,
  not that no better threshold exists.
- The rules, targets and acceptance conditions are identical to version 1 and were not tuned on this arm. The
  negative result for both TCN arms was known before this protocol was frozen.
- The shards were regenerated rather than the original files. All 20 matched their frozen hashes, and see the
  [evidence recovery report](evidence-recovery-20261108.md) for the code-hash difference and the unknown size of
  two earlier download attempts.
- The model files and inputs used in this run were copied into a fresh clone. Two partial copies of model files
  were detected by hash and replaced before the single run. The G2 check also verified every model file.

## Reproduction

The run is a single pass into a new output directory. It needs the frozen inputs in `artifacts/`: the annual
predictions, the walk-forward artifact and the verified shards.

```sh
python scripts/audit_threshold_selection_baseline.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --output artifacts/threshold_selection_baseline_20261108_r1
python -m pytest -q tests/test_threshold_selection_baseline_audit.py
```
