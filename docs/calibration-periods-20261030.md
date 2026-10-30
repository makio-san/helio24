# Separate calibration and threshold periods across years

The separated policy reaches recall >=0.95 in 4 of 6 positive evaluation
years. The all-year acceptance gate is `False`. No dashboard model or alarm policy
was replaced, and the reserved 2024–2025 test remains closed. Improvements in one year
are not treated as general model improvement.

## Design and controls

The frozen protocol is `config/calibration-periods-v1.json`. The same yearly logistic
and XGBoost models, 96 features, 0.45/0.55 blend and evaluation populations from
`walk-forward-v1` are retained. This experiment fits new probability calibrators and
thresholds, not new underlying classifiers. Original source hashes, split audits and
evaluation metadata are verified before use.

Three arms are compared. `baseline_full_year` retains the frozen full-year sigmoid
calibrators and threshold. `late_threshold_control` retains those same calibrators and
probabilities but chooses its threshold only on the late half of the preceding year.
This deliberately retains calibration/threshold reuse to control for threshold recency.
`separated_calibration` fits sigmoid calibrators only on the early half and selects its
threshold only on the late half. Each threshold targets recall >=0.95 on its selection
period and is saved before evaluation predictions. Evaluation labels never retune it.

The boundary is July 1 of the year before evaluation. Early prediction windows must
end by the boundary; late observation windows must start on or after it. Late HARPs
also seen in the early half are excluded from both new arms' threshold-selection data.
Outer training and evaluation rows remain unchanged. Splitting changes both sample size
and timing, so this is not a causal isolation of data reuse alone. Source label/quality
exclusions are inherited.

## Fold availability and split audit

| year | status | reason | early_rows | early_positives | late_rows | late_positives | boundary_removed | shared_harp_rows_removed | unavailable | passes_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | complete | undefined | 33718.000000 | 406.000000 | 39614.000000 | 881.000000 | 360.000000 | 457.000000 | {} | False |
| 2015 | complete | undefined | 36445.000000 | 1215.000000 | 37472.000000 | 1054.000000 | 292.000000 | 1019.000000 | {} | False |
| 2016 | complete | undefined | 38615.000000 | 692.000000 | 29912.000000 | 663.000000 | 113.000000 | 498.000000 | {} | False |
| 2017 | complete | undefined | 26232.000000 | 111.000000 | 16505.000000 | 70.000000 | 83.000000 | 167.000000 | {} | False |
| 2018 | complete | undefined | 10352.000000 | 65.000000 | 9078.000000 | 188.000000 | 70.000000 | 29.000000 | {} | undefined |
| 2019 | skipped | Training/calibration lacks both classes: ['calibration'] | undefined | undefined | undefined | undefined | undefined | undefined | undefined | undefined |
| 2020 | skipped | Training/calibration lacks both classes: ['calibration'] | undefined | undefined | undefined | undefined | undefined | undefined | undefined | undefined |
| 2021 | skipped | Training/calibration lacks both classes: ['calibration'] | undefined | undefined | undefined | undefined | undefined | undefined | undefined | undefined |
| 2022 | complete | undefined | 9997.000000 | 75.000000 | 17462.000000 | 129.000000 | 237.000000 | 429.000000 | {} | False |
| 2023 | complete | undefined | 24198.000000 | 192.000000 | 25733.000000 | 229.000000 | 361.000000 | 464.000000 | {} | False |

Original 2019–2021 skips remain because their preceding calibration years lack positive
examples. If a late half lacked both classes, both new policies would be unavailable;
if only the early half lacked both classes, the separated policy would be unavailable.
No silent fallback to baseline is allowed. `undefined` is not a measured zero.

## Precision, recall and false-positive windows

| year | arm | n | positives | precision | recall | fp | fn | threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | baseline_full_year | 75228 | 2310 | 0.135905 | 0.945455 | 13886 | 126 | 0.011475 |
| 2014 | late_threshold_control | 75228 | 2310 | 0.219832 | 0.849351 | 6963 | 348 | 0.037206 |
| 2014 | separated_calibration | 75228 | 2310 | 0.221038 | 0.844156 | 6872 | 360 | 0.032129 |
| 2015 | baseline_full_year | 69138 | 1355 | 0.105164 | 0.993358 | 11453 | 9 | 0.018839 |
| 2015 | late_threshold_control | 69138 | 1355 | 0.196984 | 0.944649 | 5218 | 75 | 0.048456 |
| 2015 | separated_calibration | 69138 | 1355 | 0.191636 | 0.946863 | 5412 | 72 | 0.061086 |
| 2016 | baseline_full_year | 42987 | 181 | 0.071400 | 0.972376 | 2289 | 5 | 0.030831 |
| 2016 | late_threshold_control | 42987 | 181 | 0.069264 | 0.972376 | 2365 | 5 | 0.029657 |
| 2016 | separated_calibration | 42987 | 181 | 0.069620 | 0.972376 | 2352 | 5 | 0.029622 |
| 2017 | baseline_full_year | 19529 | 253 | 0.155512 | 0.936759 | 1287 | 16 | 0.012000 |
| 2017 | late_threshold_control | 19529 | 253 | 0.127043 | 0.952569 | 1656 | 12 | 0.006265 |
| 2017 | separated_calibration | 19529 | 253 | 0.131622 | 0.952569 | 1590 | 12 | 0.005171 |
| 2018 | baseline_full_year | 7799 | 0 | 0.000000 | undefined | 359 | 0 | 0.004351 |
| 2018 | late_threshold_control | 7799 | 0 | 0.000000 | undefined | 1 | 0 | 0.058659 |
| 2018 | separated_calibration | 7799 | 0 | undefined | undefined | 0 | 0 | 0.066088 |
| 2022 | baseline_full_year | 50756 | 421 | 0.039573 | 0.985748 | 10072 | 6 | 0.008994 |
| 2022 | late_threshold_control | 50756 | 421 | 0.070197 | 0.957245 | 5338 | 18 | 0.023981 |
| 2022 | separated_calibration | 50756 | 421 | 0.070566 | 0.957245 | 5308 | 18 | 0.038661 |
| 2023 | baseline_full_year | 60366 | 781 | 0.103397 | 0.884763 | 5992 | 90 | 0.018203 |
| 2023 | late_threshold_control | 60366 | 781 | 0.066412 | 0.956466 | 10501 | 34 | 0.006393 |
| 2023 | separated_calibration | 60366 | 781 | 0.064247 | 0.956466 | 10880 | 34 | 0.005327 |

All scores are fractions on a 0–1 scale. Precision is the positive fraction among alarm
windows; recall is the caught fraction among positive windows. FP/FN are overlapping
forecast windows, not independent flares or notifications. Each arm uses its own frozen
threshold on the same annual evaluation rows. In 2018 there are no retained positive
windows. The separated policy also makes no alarms, so both precision and recall are
undefined; zero FP is not evidence that positive events would be caught.

## Complete metric comparison

| year | arm | n | positives | threshold | tp | fp | fn | tn | recall | precision | false_positive_rate | false_alarm_ratio | alarms | tss | average_precision | brier | log_loss | accuracy | balanced_accuracy | f1 | always_quiet_accuracy | precision_defined | recall_defined |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | baseline_full_year | 75228 | 2310 | 0.011475 | 2184 | 13886 | 126 | 59032 | 0.945455 | 0.135905 | 0.190433 | 0.864095 | 16070 | 0.755021 | 0.507930 | 0.020661 | 0.076538 | 0.813740 | 0.877511 | 0.237650 | 0.969293 | True | True |
| 2014 | late_threshold_control | 75228 | 2310 | 0.037206 | 1962 | 6963 | 348 | 65955 | 0.849351 | 0.219832 | 0.095491 | 0.780168 | 8925 | 0.753860 | 0.507930 | 0.020661 | 0.076538 | 0.902815 | 0.876930 | 0.349266 | 0.969293 | True | True |
| 2014 | separated_calibration | 75228 | 2310 | 0.032129 | 1950 | 6872 | 360 | 66046 | 0.844156 | 0.221038 | 0.094243 | 0.778962 | 8822 | 0.749913 | 0.504801 | 0.022211 | 0.081103 | 0.903866 | 0.874956 | 0.350341 | 0.969293 | True | True |
| 2015 | baseline_full_year | 69138 | 1355 | 0.018839 | 1346 | 11453 | 9 | 56330 | 0.993358 | 0.105164 | 0.168966 | 0.894836 | 12799 | 0.824392 | 0.492441 | 0.013564 | 0.047847 | 0.834216 | 0.912196 | 0.190194 | 0.980402 | True | True |
| 2015 | late_threshold_control | 69138 | 1355 | 0.048456 | 1280 | 5218 | 75 | 62565 | 0.944649 | 0.196984 | 0.076981 | 0.803016 | 6498 | 0.867668 | 0.492441 | 0.013564 | 0.047847 | 0.923443 | 0.933834 | 0.325990 | 0.980402 | True | True |
| 2015 | separated_calibration | 69138 | 1355 | 0.061086 | 1283 | 5412 | 72 | 62371 | 0.946863 | 0.191636 | 0.079843 | 0.808364 | 6695 | 0.867020 | 0.492655 | 0.013746 | 0.050348 | 0.920680 | 0.933510 | 0.318758 | 0.980402 | True | True |
| 2016 | baseline_full_year | 42987 | 181 | 0.030831 | 176 | 2289 | 5 | 40517 | 0.972376 | 0.071400 | 0.053474 | 0.928600 | 2465 | 0.918902 | 0.366443 | 0.003263 | 0.014523 | 0.946635 | 0.959451 | 0.133031 | 0.995789 | True | True |
| 2016 | late_threshold_control | 42987 | 181 | 0.029657 | 176 | 2365 | 5 | 40441 | 0.972376 | 0.069264 | 0.055249 | 0.930736 | 2541 | 0.917126 | 0.366443 | 0.003263 | 0.014523 | 0.944867 | 0.958563 | 0.129317 | 0.995789 | True | True |
| 2016 | separated_calibration | 42987 | 181 | 0.029622 | 176 | 2352 | 5 | 40454 | 0.972376 | 0.069620 | 0.054946 | 0.930380 | 2528 | 0.917430 | 0.367034 | 0.003257 | 0.014633 | 0.945169 | 0.958715 | 0.129937 | 0.995789 | True | True |
| 2017 | baseline_full_year | 19529 | 253 | 0.012000 | 237 | 1287 | 16 | 17989 | 0.936759 | 0.155512 | 0.066767 | 0.844488 | 1524 | 0.869992 | 0.811694 | 0.004907 | 0.020488 | 0.933279 | 0.934996 | 0.266742 | 0.987045 | True | True |
| 2017 | late_threshold_control | 19529 | 253 | 0.006265 | 241 | 1656 | 12 | 17620 | 0.952569 | 0.127043 | 0.085910 | 0.872957 | 1897 | 0.866659 | 0.811694 | 0.004907 | 0.020488 | 0.914589 | 0.933330 | 0.224186 | 0.987045 | True | True |
| 2017 | separated_calibration | 19529 | 253 | 0.005171 | 241 | 1590 | 12 | 17686 | 0.952569 | 0.131622 | 0.082486 | 0.868378 | 1831 | 0.870083 | 0.808219 | 0.004896 | 0.020118 | 0.917968 | 0.935042 | 0.231286 | 0.987045 | True | True |
| 2018 | baseline_full_year | 7799 | 0 | 0.004351 | 0 | 359 | 0 | 7440 | undefined | 0.000000 | 0.046032 | 1.000000 | 359 | undefined | undefined | 0.000012 | 0.000791 | 0.953968 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | late_threshold_control | 7799 | 0 | 0.058659 | 0 | 1 | 0 | 7798 | undefined | 0.000000 | 0.000128 | 1.000000 | 1 | undefined | undefined | 0.000012 | 0.000791 | 0.999872 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | separated_calibration | 7799 | 0 | 0.066088 | 0 | 0 | 0 | 7799 | undefined | undefined | 0.000000 | undefined | 0 | undefined | undefined | 0.000015 | 0.001024 | 1.000000 | undefined | undefined | 1.000000 | False | False |
| 2022 | baseline_full_year | 50756 | 421 | 0.008994 | 415 | 10072 | 6 | 40263 | 0.985748 | 0.039573 | 0.200099 | 0.960427 | 10487 | 0.785649 | 0.280023 | 0.007064 | 0.029196 | 0.801442 | 0.892824 | 0.076091 | 0.991705 | True | True |
| 2022 | late_threshold_control | 50756 | 421 | 0.023981 | 403 | 5338 | 18 | 44997 | 0.957245 | 0.070197 | 0.106049 | 0.929803 | 5741 | 0.851195 | 0.280023 | 0.007064 | 0.029196 | 0.894476 | 0.925598 | 0.130802 | 0.991705 | True | True |
| 2022 | separated_calibration | 50756 | 421 | 0.038661 | 403 | 5308 | 18 | 45027 | 0.957245 | 0.070566 | 0.105453 | 0.929434 | 5711 | 0.851791 | 0.279087 | 0.007239 | 0.032122 | 0.895067 | 0.925896 | 0.131442 | 0.991705 | True | True |
| 2023 | baseline_full_year | 60366 | 781 | 0.018203 | 691 | 5992 | 90 | 53593 | 0.884763 | 0.103397 | 0.100562 | 0.896603 | 6683 | 0.784201 | 0.220619 | 0.011195 | 0.043996 | 0.899248 | 0.892100 | 0.185155 | 0.987062 | True | True |
| 2023 | late_threshold_control | 60366 | 781 | 0.006393 | 747 | 10501 | 34 | 49084 | 0.956466 | 0.066412 | 0.176236 | 0.933588 | 11248 | 0.780230 | 0.220619 | 0.011195 | 0.043996 | 0.825481 | 0.890115 | 0.124200 | 0.987062 | True | True |
| 2023 | separated_calibration | 60366 | 781 | 0.005327 | 747 | 10880 | 34 | 48705 | 0.956466 | 0.064247 | 0.182596 | 0.935753 | 11627 | 0.773870 | 0.218710 | 0.011253 | 0.044239 | 0.819203 | 0.886935 | 0.120406 | 0.987062 | True | True |

Accuracy measures all correctly classified windows and can be misleading under class
imbalance. AP measures ranking; lower Brier/log loss is better probabilistic scoring.
The frozen acceptance gate requires coverage of all comparable positive years, strictly
higher precision at recall >=0.95 in each, no lower AP and no higher Brier/log loss than
baseline. The late-threshold control changes no probabilities, so its AP, Brier and log
loss match baseline exactly. A threshold adjustment is not itself a ranking improvement.

## Interpretation

In 2022 the separated policy raises precision from 0.039573 to 0.070566 and reduces FP
from 10072 to 5308 while retaining recall 0.957245. However, the late-threshold control
already produces precision 0.070197 and 5338 FP at the same recall. Most of the observed
gain that year is reproduced without separating probability fitting from threshold
selection. The separated probabilities have worse Brier/log loss and slightly lower AP
than baseline, so even that year does not pass the full gate.

In 2014 and 2015 precision rises but recall falls to 0.844156 and 0.946863, below the
required target. In 2023 recall rises from 0.884763 to 0.956466, while precision falls
from 0.103397 to 0.064247 and FP rises from 5992 to 10880. The late-threshold control
achieves the same recall with 10501 FP, fewer than the separated policy. The trade-off
therefore changes by year; separating periods is not a consistent precision solution.
No positive evaluation year passes all acceptance checks.

## Paired conditional uncertainty

| year | control | metric | lower | upper | valid_draws |
| --- | --- | --- | --- | --- | --- |
| 2014 | baseline_full_year | precision | 0.053878 | 0.122584 | 1000 |
| 2014 | baseline_full_year | recall | -0.169959 | -0.057813 | 1000 |
| 2014 | baseline_full_year | fp | -8377.075000 | -5600.375000 | 1000 |
| 2014 | late_threshold_control | precision | -0.000056 | 0.002342 | 1000 |
| 2014 | late_threshold_control | recall | -0.011351 | -0.000495 | 1000 |
| 2014 | late_threshold_control | fp | -128.000000 | -56.975000 | 1000 |
| 2015 | baseline_full_year | precision | 0.054081 | 0.122242 | 1000 |
| 2015 | baseline_full_year | recall | -0.110954 | -0.012522 | 1000 |
| 2015 | baseline_full_year | fp | -7524.175000 | -4545.675000 | 1000 |
| 2015 | late_threshold_control | precision | -0.007918 | -0.003062 | 1000 |
| 2015 | late_threshold_control | recall | 0.000000 | 0.005406 | 1000 |
| 2015 | late_threshold_control | fp | 128.000000 | 265.025000 | 1000 |
| 2016 | baseline_full_year | precision | -0.003562 | 0.000000 | 1000 |
| 2016 | baseline_full_year | recall | 0.000000 | 0.000000 | 973 |
| 2016 | baseline_full_year | fp | 33.000000 | 99.000000 | 1000 |
| 2016 | late_threshold_control | precision | 0.000000 | 0.000727 | 1000 |
| 2016 | late_threshold_control | recall | 0.000000 | 0.000000 | 973 |
| 2016 | late_threshold_control | fp | -23.000000 | -5.000000 | 1000 |
| 2017 | baseline_full_year | precision | -0.069991 | 0.000000 | 1000 |
| 2017 | baseline_full_year | recall | 0.000000 | 0.061538 | 949 |
| 2017 | baseline_full_year | fp | 171.000000 | 465.100000 | 1000 |
| 2017 | late_threshold_control | precision | 0.000000 | 0.011735 | 1000 |
| 2017 | late_threshold_control | recall | 0.000000 | 0.000000 | 949 |
| 2017 | late_threshold_control | fp | -103.025000 | -32.000000 | 1000 |
| 2018 | baseline_full_year | precision | undefined | undefined | 0 |
| 2018 | baseline_full_year | recall | undefined | undefined | 0 |
| 2018 | baseline_full_year | fp | -806.050000 | -46.925000 | 1000 |
| 2018 | late_threshold_control | precision | undefined | undefined | 0 |
| 2018 | late_threshold_control | recall | undefined | undefined | 0 |
| 2018 | late_threshold_control | fp | -3.000000 | 0.000000 | 1000 |
| 2022 | baseline_full_year | precision | 0.014695 | 0.050292 | 1000 |
| 2022 | baseline_full_year | recall | -0.093797 | 0.000000 | 1000 |
| 2022 | baseline_full_year | fp | -6038.000000 | -3731.950000 | 1000 |
| 2022 | late_threshold_control | precision | 0.000163 | 0.000662 | 1000 |
| 2022 | late_threshold_control | recall | 0.000000 | 0.000000 | 1000 |
| 2022 | late_threshold_control | fp | -45.000000 | -17.000000 | 1000 |
| 2023 | baseline_full_year | precision | -0.058085 | -0.023437 | 1000 |
| 2023 | baseline_full_year | recall | 0.021894 | 0.133131 | 1000 |
| 2023 | baseline_full_year | fp | 3863.950000 | 5995.200000 | 1000 |
| 2023 | late_threshold_control | precision | -0.003351 | -0.001268 | 1000 |
| 2023 | late_threshold_control | recall | 0.000000 | 0.000000 | 1000 |
| 2023 | late_threshold_control | fp | 273.975000 | 498.000000 | 1000 |

Intervals are separated policy minus the named control, using 1000 paired whole-HARP
bootstrap draws per year with seed 24. The same resampled regions contribute to both
arms. Fitted classifiers, calibrators and thresholds remain fixed; fitting and historical
selection uncertainty are excluded. Undefined precision/recall draws are counted through
`valid_draws`; a zero-positive year has no valid recall draws. An interval spanning zero
does not establish a directional change at that interval level. Years share historical
training and are not independent replications.

## Limitations and next decision

This is adaptive retrospective development informed by earlier errors, not a fresh
independent test. It does not establish a physical cause for temporal changes. Fewer
calibration positives can make the fitted mapping and selected threshold unstable.
The result rejects this fixed half-year recipe as a general replacement, not every
possible chronological calibration policy. Do not tune the split date repeatedly on
these outcomes or lower the recall requirement to declare success.

Before another policy search, inspect the calibration-period score distributions and
positive-region counts across years, then freeze any candidate using earlier inner
chronological folds. A practical policy must demonstrate both recall and false-alarm
burden across periods; calibration alone cannot guarantee better separation of positive
and negative cases. That follow-up analysis and any additional training are not claimed
to have been performed here. The reserved test remains outside development.

## Reproduction

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_calibration_periods.py \
  --protocol config/calibration-periods-v1.json --output artifacts/calibration_periods_20261030_r1
.venv/bin/python scripts/report_calibration_periods.py --source artifacts/calibration_periods_20261030_r1 --report-name calibration-periods-20261030
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_calibration-periods-20261030
```

Use fresh output directories and report names; never overwrite frozen evidence.
Review both full document editions, register their source hash and links in
`docs/reports.json` and `docs/reports.md`, then publish to a fresh HTML directory.
Calibrators, predictions, thresholds and HTML remain local ignored artifacts. Source,
code and output hashes are recorded in the experiment report.

| source | SHA-256 |
| --- | --- |
| artifacts/calibration_periods_20261030_r1/report.json | b6b7a18f4e0eac9a10396eb46451b10eb82beb8cc7140f62e188bc581573e527 |
| artifacts/calibration_periods_20261030_r1/metrics.csv | 92e493f451c49edf8b6761fa1f49198359a84b73321e922c158fbba3d2e526ea |

