# Precision context results: causal regional trajectory does not raise precision

## Decision and scope

The [frozen protocol](precision-context-protocol-20261108.md) was run once on the frozen annual predictions
(source report SHA256 `e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`). The thresholds of
all candidates were written to disk and hashed (SHA256 `8bd3b5231402245ddf97dae1c236c9d425412d664d1551b71c3ee33182a541e0`) before any evaluation label was read. Stage
one was inference only with the stored frozen models; stage two was 84 small logistic fits on calibration years.
No label changed and the reserved 2024–2025 test stayed closed.

Decisions:

1. Neither candidate passes in any of the six positive years. The all-year result is negative for `recal`
   (0 of 6) and for `context` (0 of 6).
2. Nothing is adopted. No alert, threshold or model changes.
3. The hypothesis that a region's own probability trajectory and age separate persistently alarmed quiet regions
   from regions approaching a flare is not supported in this record with this second stage. The flare-history
   route stays blocked on provenance and is not revived by this result.

## Baseline gate

The control threshold was reproduced in every year and the recomputed stage-one probabilities equal the frozen
predictions on every row.

| year | calibration positives | calibration HARPs | control threshold reproduced | identity rows matched |
| --- | --- | --- | --- | --- |
| 2014 | 1287 | 588 | yes | 75228 |
| 2015 | 2310 | 629 | yes | 69138 |
| 2016 | 1355 | 599 | yes | 42987 |
| 2017 | 181 | 357 | yes | 19529 |
| 2018 | 253 | 163 | yes | 7799 |
| 2022 | 204 | 255 | yes | 50756 |
| 2023 | 421 | 528 | yes | 60366 |

## Acceptance outcome

| candidate | years_met | required_years | all_year_primary | met_years |
| --- | --- | --- | --- | --- |
| recal | 0 | 6 | no | [] |
| context | 0 | 6 | no | [] |

| year | candidate | episode_precision_higher | fp_lower | positive_runs_alarmed_not_below | recall_drop_ok | primary_met |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | recal | no | no | yes | yes | no |
| 2014 | context | yes | yes | no | yes | no |
| 2015 | recal | no | no | yes | yes | no |
| 2015 | context | yes | no | yes | yes | no |
| 2016 | recal | no | no | yes | yes | no |
| 2016 | context | no | no | yes | yes | no |
| 2017 | recal | yes | yes | yes | no | no |
| 2017 | context | no | no | yes | yes | no |
| 2022 | recal | yes | no | yes | yes | no |
| 2022 | context | no | no | yes | yes | no |
| 2023 | recal | no | no | yes | yes | no |
| 2023 | context | no | no | yes | yes | no |

`context` reduces false-alarm windows only in 2014 (12951 against 13886) and raises episode precision there
(0.1328 against 0.0977), but it alarms 78 of 83 positive runs against 80 for the control, so the year fails.
`recal` reduces false alarms only in 2017, where its recall falls from 0.9368 to 0.8814, beyond the tolerance.
In every other positive year both candidates alarm more windows than the control.

## Metrics by year and candidate

| year | candidate | threshold | TP | FP | recall | precision | episodes | episode precision | alarmed positive runs | AP | Brier | log loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 0.011475 | 2184 | 13886 | 0.9455 | 0.1359 | 686 | 0.0977 | 80 of 83 | 0.5079 | 0.020661 | 0.076538 |
| 2014 | recal | 0.007997 | 2201 | 15161 | 0.9528 | 0.1268 | 725 | 0.0897 | 80 of 83 | 0.5023 | 0.020774 | 0.077533 |
| 2014 | context | 0.009852 | 2163 | 12951 | 0.9364 | 0.1431 | 497 | 0.1328 | 78 of 83 | 0.4918 | 0.021063 | 0.079022 |
| 2015 | control | 0.018839 | 1346 | 11453 | 0.9934 | 0.1052 | 568 | 0.0669 | 51 of 51 | 0.4924 | 0.013564 | 0.047847 |
| 2015 | recal | 0.014615 | 1346 | 11597 | 0.9934 | 0.1040 | 606 | 0.0627 | 51 of 51 | 0.4999 | 0.013269 | 0.046413 |
| 2015 | context | 0.012352 | 1344 | 11553 | 0.9919 | 0.1042 | 509 | 0.0747 | 51 of 51 | 0.4933 | 0.013318 | 0.046577 |
| 2016 | control | 0.030831 | 176 | 2289 | 0.9724 | 0.0714 | 204 | 0.0196 | 7 of 7 | 0.3664 | 0.003263 | 0.014523 |
| 2016 | recal | 0.022311 | 176 | 2740 | 0.9724 | 0.0604 | 253 | 0.0158 | 7 of 7 | 0.3296 | 0.003353 | 0.014374 |
| 2016 | context | 0.013638 | 176 | 3244 | 0.9724 | 0.0515 | 240 | 0.0167 | 7 of 7 | 0.3699 | 0.003237 | 0.013707 |
| 2017 | control | 0.012000 | 237 | 1287 | 0.9368 | 0.1555 | 85 | 0.0588 | 5 of 6 | 0.8117 | 0.004907 | 0.020488 |
| 2017 | recal | 0.006207 | 223 | 1240 | 0.8814 | 0.1524 | 98 | 0.1020 | 5 of 6 | 0.5832 | 0.007895 | 0.034740 |
| 2017 | context | 0.000000 | 253 | 18721 | 1.0000 | 0.0133 | 350 | 0.0171 | 6 of 6 | 0.2836 | 0.011217 | 0.061819 |
| 2022 | control | 0.008994 | 415 | 10072 | 0.9857 | 0.0396 | 622 | 0.0257 | 16 of 16 | 0.2800 | 0.007064 | 0.029196 |
| 2022 | recal | 0.007065 | 416 | 11281 | 0.9881 | 0.0356 | 660 | 0.0258 | 16 of 16 | 0.2797 | 0.007092 | 0.029177 |
| 2022 | context | 0.003310 | 421 | 14303 | 1.0000 | 0.0286 | 639 | 0.0235 | 16 of 16 | 0.2028 | 0.007758 | 0.030726 |
| 2023 | control | 0.018203 | 691 | 5992 | 0.8848 | 0.1034 | 475 | 0.0842 | 36 of 38 | 0.2206 | 0.011195 | 0.043996 |
| 2023 | recal | 0.011625 | 719 | 7178 | 0.9206 | 0.0910 | 489 | 0.0818 | 38 of 38 | 0.2240 | 0.011220 | 0.044252 |
| 2023 | context | 0.005197 | 742 | 9211 | 0.9501 | 0.0746 | 504 | 0.0754 | 38 of 38 | 0.2081 | 0.011621 | 0.043913 |

## Distance to the precision target

The last column is the number of false-alarm windows above the largest count that would give precision 0.30
at the achieved true positives.

| year | candidate | TP | FP | precision | FP allowed for 0.30 | FP excess |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 2184 | 13886 | 0.1359 | 5096 | 8790 |
| 2014 | recal | 2201 | 15161 | 0.1268 | 5135 | 10026 |
| 2014 | context | 2163 | 12951 | 0.1431 | 5047 | 7904 |
| 2015 | control | 1346 | 11453 | 0.1052 | 3140 | 8313 |
| 2015 | recal | 1346 | 11597 | 0.1040 | 3140 | 8457 |
| 2015 | context | 1344 | 11553 | 0.1042 | 3136 | 8417 |
| 2016 | control | 176 | 2289 | 0.0714 | 410 | 1879 |
| 2016 | recal | 176 | 2740 | 0.0604 | 410 | 2330 |
| 2016 | context | 176 | 3244 | 0.0515 | 410 | 2834 |
| 2017 | control | 237 | 1287 | 0.1555 | 553 | 734 |
| 2017 | recal | 223 | 1240 | 0.1524 | 520 | 720 |
| 2017 | context | 253 | 18721 | 0.0133 | 590 | 18131 |
| 2022 | control | 415 | 10072 | 0.0396 | 968 | 9104 |
| 2022 | recal | 416 | 11281 | 0.0356 | 970 | 10311 |
| 2022 | context | 421 | 14303 | 0.0286 | 982 | 13321 |
| 2023 | control | 691 | 5992 | 0.1034 | 1612 | 4380 |
| 2023 | recal | 719 | 7178 | 0.0910 | 1677 | 5501 |
| 2023 | context | 742 | 9211 | 0.0746 | 1731 | 7480 |

The best precision of any cell is 0.1555 (control, 2017). No candidate moves any year closer to 0.30 than the
control, except `context` in 2014 by 886 windows while losing two alarmed positive runs.

## Year without positive windows

2018 has no positive windows and is not gated.

| candidate | threshold | FP windows | episodes |
| --- | --- | --- | --- |
| control | 0.004351 | 359 | 30 |
| recal | 0.000506 | 936 | 66 |
| context | 0.001387 | 502 | 43 |

## Why the second stage fails

The calibration-year threshold of a stage-two model transfers worse than the control threshold. The stage-two
threshold is selected on cross-fitted calibration probabilities, but the evaluation year receives the model
refitted on the whole calibration year, and the evaluation-year distribution of the context features differs
from the calibration year. In 2017 the `context` model fitted on the 2016 calibration year (181 positive windows)
selected a threshold near zero and alarmed every window of 2017: 253 true positives, 18721 false alarms. The
stage-two coefficients also change sign across years for most context features, which shows that the
trajectory relation learned in one year does not hold in the next.

| feature | 2014 | 2015 | 2016 | 2017 | 2022 | 2023 |
| --- | --- | --- | --- | --- | --- | --- |
| logit_p | 2.083 | 1.228 | 2.095 | 2.156 | 1.333 | 1.560 |
| age_log_hours | 0.445 | 0.096 | 0.162 | 0.893 | -0.400 | -0.245 |
| past24_max_logit | -0.029 | 2.362 | 0.786 | 0.911 | 0.920 | 1.576 |
| past24_mean_logit | 0.760 | -0.902 | 0.044 | 0.998 | 1.427 | 0.624 |
| past72_max_logit | -0.258 | -0.131 | -0.084 | -1.694 | -1.962 | 0.266 |
| past72_mean_logit | -0.262 | -0.021 | -0.223 | -0.555 | 0.526 | -1.546 |
| past72_hours_above_control | 0.653 | 0.229 | 0.240 | 1.128 | -0.262 | 0.165 |
| slope6 | 0.007 | 0.168 | 0.040 | 0.231 | -0.363 | -0.024 |
| coverage24 | 0.408 | -0.041 | -0.166 | 0.324 | -0.464 | -0.235 |
| coverage72 | -1.539 | -0.419 | -0.090 | -3.110 | 1.012 | -0.304 |
| missing_fraction | -0.165 | 0.089 | 0.203 | -2.143 | 0.031 | -0.135 |

## Uncertainty

Paired full-HARP bootstrap intervals (1000 draws, seed 24) of the differences against the control for the six
positive years. A negative false-alarm difference means fewer false-alarm windows than the control. The
intervals are conditional on the frozen thresholds and do not include stage-two fitting or threshold selection
uncertainty; they are not corrected for multiple comparisons.

| year | candidate | episode precision diff lower | episode precision diff upper | FP window diff lower | FP window diff upper |
| --- | --- | --- | --- | --- | --- |
| 2014 | recal | -0.0173 | -0.0001 | 975.0 | 1612.0 |
| 2014 | context | 0.0172 | 0.0539 | -1357.3 | -557.8 |
| 2015 | recal | -0.0084 | -0.0015 | 86.0 | 216.0 |
| 2015 | context | -0.0008 | 0.0183 | -181.0 | 358.0 |
| 2016 | recal | -0.0116 | -0.0001 | 311.9 | 617.0 |
| 2016 | context | -0.0128 | 0.0020 | 645.0 | 1365.0 |
| 2017 | recal | -0.0160 | 0.1458 | -296.0 | 151.0 |
| 2017 | context | -0.1144 | 0.0000 | 15384.4 | 19568.2 |
| 2022 | recal | -0.0028 | 0.0036 | 951.0 | 1477.0 |
| 2022 | context | -0.0078 | 0.0014 | 3223.0 | 5404.2 |
| 2023 | recal | -0.0183 | 0.0125 | 885.9 | 1498.0 |
| 2023 | context | -0.0267 | 0.0045 | 2664.8 | 3843.1 |

## Limits

- Adaptive development evidence on already inspected years, not an independent test. Counts are overlapping
  forecast windows and groupings of them, not physical flares.
- The context features were chosen after seeing where false alarms concentrate in these same years; this
  adaptivity would bias the result toward a pass, and the result is still negative.
- Only one second-stage recipe and one lookback set were tested, as frozen. The result rejects this recipe,
  not every use of regional history.
- Calibration years with few positive windows (181 for 2017, 204 for 2022) make stage two unstable; the 2017
  collapse is the clearest case.

## Reproduction

```sh
python scripts/audit_precision_context.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --output artifacts/precision_context_20261109_r1
python -m pytest -q tests/test_precision_context_audit.py tests/test_precision_context_protocol.py
```
