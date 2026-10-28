# Annual forecast stability and machine learning methods

The frozen ensemble reached recall >=0.95 in **3 of 6 evaluated years with
positive windows**. There were 7 completed annual folds. This is a retrospective
development audit, not a new independent test or a model improvement claim. No dashboard
model was replaced. The reserved 2024–2025 test remains closed.

## What was evaluated

The protocol plans evaluation years 2014–2023. Each fold trains on all available years
before the preceding calendar year, calibrates on that preceding year, and evaluates
on the next year. Example: a 2023 evaluation trains before 2022 and calibrates in 2022.
Observation and 24-hour prediction intervals must remain inside their role boundaries.
HARPs seen in earlier roles are removed from later roles. The underlying development
population already contains earlier label, quality and region exclusions; these are
retained. Annual populations therefore differ from earlier single-period experiments.

This first annual audit retrains the existing **96-feature** logistic and XGBoost recipes,
their fixed 0.45/0.55 probability blend, and a constant training-prevalence baseline.
It does not rerun the 292-feature long-history candidates. Model settings and ensemble
weights were fixed before this run, but informed by previous development on these years;
the results must not be presented as untouched prospective estimates. There is no
evaluation-based candidate selection. Calibration probabilities and alarm thresholds
are fitted before each year's evaluation, and thresholds are saved before its predictions.

## Fold population and exclusions

| year | status | role | rows | positives | boundary_removed | shared_harp_rows_removed |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | complete | train | 148508 | 2959 | 195 | 0 |
| 2014 | complete | calibration | 74149 | 1287 | 331 | 704 |
| 2014 | complete | evaluation | 75228 | 2310 | 416 | 562 |
| 2015 | complete | train | 223647 | 4246 | 240 | 0 |
| 2015 | complete | calibration | 75228 | 2310 | 416 | 562 |
| 2015 | complete | evaluation | 69138 | 1355 | 224 | 979 |
| 2016 | complete | train | 299785 | 6633 | 308 | 0 |
| 2016 | complete | calibration | 69138 | 1355 | 224 | 979 |
| 2016 | complete | evaluation | 42987 | 181 | 145 | 135 |
| 2017 | complete | train | 370351 | 8036 | 83 | 0 |
| 2017 | complete | calibration | 42987 | 181 | 145 | 135 |
| 2017 | complete | evaluation | 19529 | 253 | 41 | 169 |
| 2018 | complete | train | 413604 | 8241 | 97 | 0 |
| 2018 | complete | calibration | 19529 | 253 | 41 | 169 |
| 2018 | complete | evaluation | 7799 | 0 | 52 | 81 |
| 2019 | skipped | train | 433399 | 8494 | 41 | 0 |
| 2019 | skipped | calibration | 7799 | 0 | 52 | 81 |
| 2019 | skipped | evaluation | 4919 | 0 | 22 | 0 |
| 2020 | skipped | train | 441344 | 8494 | 28 | 0 |
| 2020 | skipped | calibration | 4919 | 0 | 22 | 0 |
| 2020 | skipped | evaluation | 9813 | 0 | 54 | 0 |
| 2021 | skipped | train | 446303 | 8494 | 10 | 0 |
| 2021 | skipped | calibration | 9813 | 0 | 54 | 0 |
| 2021 | skipped | evaluation | 28125 | 204 | 51 | 193 |
| 2022 | complete | train | 456126 | 8494 | 54 | 0 |
| 2022 | complete | calibration | 28125 | 204 | 51 | 193 |
| 2022 | complete | evaluation | 50756 | 421 | 0 | 0 |
| 2023 | complete | train | 484549 | 8698 | 0 | 0 |
| 2023 | complete | calibration | 50756 | 421 | 0 | 0 |
| 2023 | complete | evaluation | 60366 | 781 | 0 | 0 |

| year | reason |
| --- | --- |
| 2014 | completed |
| 2015 | completed |
| 2016 | completed |
| 2017 | completed |
| 2018 | completed |
| 2019 | Training/calibration lacks both classes: ['calibration'] |
| 2020 | Training/calibration lacks both classes: ['calibration'] |
| 2021 | Training/calibration lacks both classes: ['calibration'] |
| 2022 | completed |
| 2023 | completed |

The retained source population has no positive windows in 2018, 2019 or 2020. This is
a statement about retained labels, not proof that no solar flare occurred in those years.
A calibration year missing either class cannot fit sigmoid calibration or a 95% recall
threshold; its fold is explicitly skipped. A zero-positive evaluation year remains in
the report: false positives and accuracy are measurable, recall/AP/TSS are undefined.
`undefined` is not zero. No years are removed for disappointing performance.

## Ensemble results at transferred calibration thresholds

| year | n | positives | threshold | precision | recall | fp | fn | accuracy | average_precision | brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 75228 | 2310 | 0.011475 | 0.135905 | 0.945455 | 13886 | 126 | 0.813740 | 0.507930 | 0.020661 |
| 2015 | 69138 | 1355 | 0.018839 | 0.105164 | 0.993358 | 11453 | 9 | 0.834216 | 0.492441 | 0.013564 |
| 2016 | 42987 | 181 | 0.030831 | 0.071400 | 0.972376 | 2289 | 5 | 0.946635 | 0.366443 | 0.003263 |
| 2017 | 19529 | 253 | 0.012000 | 0.155512 | 0.936759 | 1287 | 16 | 0.933279 | 0.811694 | 0.004907 |
| 2018 | 7799 | 0 | 0.004351 | 0.000000 | undefined | 359 | 0 | 0.953968 | undefined | 0.000012 |
| 2022 | 50756 | 421 | 0.008994 | 0.039573 | 0.985748 | 10072 | 6 | 0.801442 | 0.280023 | 0.007064 |
| 2023 | 60366 | 781 | 0.018203 | 0.103397 | 0.884763 | 5992 | 90 | 0.899248 | 0.220619 | 0.011195 |

Precision is the fraction of alarm windows that are positive; recall is the fraction
of positive windows caught. FP counts negative windows producing alarms, FN counts
missed positive windows. Accuracy measures all correct windows and can be high under
class imbalance. AP summarizes ranking across thresholds; Brier and log loss score
probabilities, with smaller values better. All fractional scores are reported on a
0–1 scale, not as percentages. Counts are overlapping windows, not independent events.

## All model results

| year | model | n | positives | threshold | tp | fp | fn | tn | recall | precision | false_positive_rate | false_alarm_ratio | alarms | tss | average_precision | brier | log_loss | accuracy | balanced_accuracy | f1 | always_quiet_accuracy | precision_defined | recall_defined |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | logistic | 75228 | 2310 | 0.007596 | 2114 | 16884 | 196 | 56034 | 0.915152 | 0.111275 | 0.231548 | 0.888725 | 18998 | 0.683604 | 0.477030 | 0.021418 | 0.087887 | 0.772957 | 0.841802 | 0.198423 | 0.969293 | True | True |
| 2014 | xgboost | 75228 | 2310 | 0.010717 | 2199 | 13985 | 111 | 58933 | 0.951948 | 0.135875 | 0.191791 | 0.864125 | 16184 | 0.760157 | 0.466036 | 0.021391 | 0.078132 | 0.812623 | 0.880079 | 0.237807 | 0.969293 | True | True |
| 2014 | ensemble | 75228 | 2310 | 0.011475 | 2184 | 13886 | 126 | 59032 | 0.945455 | 0.135905 | 0.190433 | 0.864095 | 16070 | 0.755021 | 0.507930 | 0.020661 | 0.076538 | 0.813740 | 0.877511 | 0.237650 | 0.969293 | True | True |
| 2014 | baseline | 75228 | 2310 | 0.019925 | 2310 | 72918 | 0 | 0 | 1.000000 | 0.030707 | 1.000000 | 0.969293 | 75228 | 0.000000 | 0.030707 | 0.029880 | 0.139749 | 0.030707 | 0.500000 | 0.059584 | 0.969293 | True | True |
| 2015 | logistic | 69138 | 1355 | 0.004237 | 1355 | 22849 | 0 | 44934 | 1.000000 | 0.055982 | 0.337090 | 0.944018 | 24204 | 0.662910 | 0.488145 | 0.014151 | 0.051036 | 0.669516 | 0.831455 | 0.106029 | 0.980402 | True | True |
| 2015 | xgboost | 69138 | 1355 | 0.014610 | 1345 | 10004 | 10 | 57779 | 0.992620 | 0.118513 | 0.147589 | 0.881487 | 11349 | 0.845031 | 0.458734 | 0.013538 | 0.046794 | 0.855159 | 0.922516 | 0.211744 | 0.980402 | True | True |
| 2015 | ensemble | 69138 | 1355 | 0.018839 | 1346 | 11453 | 9 | 56330 | 0.993358 | 0.105164 | 0.168966 | 0.894836 | 12799 | 0.824392 | 0.492441 | 0.013564 | 0.047847 | 0.834216 | 0.912196 | 0.190194 | 0.980402 | True | True |
| 2015 | baseline | 69138 | 1355 | 0.018985 | 1355 | 67783 | 0 | 0 | 1.000000 | 0.019598 | 1.000000 | 0.980402 | 69138 | 0.000000 | 0.019598 | 0.019215 | 0.096482 | 0.019598 | 0.500000 | 0.038444 | 0.980402 | True | True |
| 2016 | logistic | 42987 | 181 | 0.027912 | 171 | 2280 | 10 | 40526 | 0.944751 | 0.069767 | 0.053264 | 0.930233 | 2451 | 0.891488 | 0.324128 | 0.003512 | 0.015389 | 0.946728 | 0.945744 | 0.129939 | 0.995789 | True | True |
| 2016 | xgboost | 42987 | 181 | 0.029400 | 168 | 2347 | 13 | 40459 | 0.928177 | 0.066799 | 0.054829 | 0.933201 | 2515 | 0.873348 | 0.285393 | 0.003539 | 0.015098 | 0.945100 | 0.936674 | 0.124629 | 0.995789 | True | True |
| 2016 | ensemble | 42987 | 181 | 0.030831 | 176 | 2289 | 5 | 40517 | 0.972376 | 0.071400 | 0.053474 | 0.928600 | 2465 | 0.918902 | 0.366443 | 0.003263 | 0.014523 | 0.946635 | 0.959451 | 0.133031 | 0.995789 | True | True |
| 2016 | baseline | 42987 | 181 | 0.022126 | 181 | 42806 | 0 | 0 | 1.000000 | 0.004211 | 1.000000 | 0.995789 | 42987 | 0.000000 | 0.004211 | 0.004514 | 0.038327 | 0.004211 | 0.500000 | 0.008386 | 0.995789 | True | True |
| 2017 | logistic | 19529 | 253 | 0.012634 | 241 | 1265 | 12 | 18011 | 0.952569 | 0.160027 | 0.065626 | 0.839973 | 1506 | 0.886944 | 0.798006 | 0.004959 | 0.020210 | 0.934610 | 0.943472 | 0.274019 | 0.987045 | True | True |
| 2017 | xgboost | 19529 | 253 | 0.003571 | 237 | 1663 | 16 | 17613 | 0.936759 | 0.124737 | 0.086273 | 0.875263 | 1900 | 0.850486 | 0.770590 | 0.005529 | 0.023059 | 0.914025 | 0.925243 | 0.220158 | 0.987045 | True | True |
| 2017 | ensemble | 19529 | 253 | 0.012000 | 237 | 1287 | 16 | 17989 | 0.936759 | 0.155512 | 0.066767 | 0.844488 | 1524 | 0.869992 | 0.811694 | 0.004907 | 0.020488 | 0.933279 | 0.934996 | 0.266742 | 0.987045 | True | True |
| 2017 | baseline | 19529 | 253 | 0.021698 | 253 | 19276 | 0 | 0 | 1.000000 | 0.012955 | 1.000000 | 0.987045 | 19529 | 0.000000 | 0.012955 | 0.012864 | 0.071278 | 0.012955 | 0.500000 | 0.025579 | 0.987045 | True | True |
| 2018 | logistic | 7799 | 0 | 0.008619 | 0 | 292 | 0 | 7507 | undefined | 0.000000 | 0.037441 | 1.000000 | 292 | undefined | undefined | 0.000029 | 0.001188 | 0.962559 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | xgboost | 7799 | 0 | 0.001173 | 0 | 558 | 0 | 7241 | undefined | 0.000000 | 0.071548 | 1.000000 | 558 | undefined | undefined | 0.000006 | 0.000470 | 0.928452 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | ensemble | 7799 | 0 | 0.004351 | 0 | 359 | 0 | 7440 | undefined | 0.000000 | 0.046032 | 1.000000 | 359 | undefined | undefined | 0.000012 | 0.000791 | 0.953968 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | baseline | 7799 | 0 | 0.019925 | 0 | 7799 | 0 | 0 | undefined | 0.000000 | 1.000000 | 1.000000 | 7799 | undefined | undefined | 0.000397 | 0.020126 | 0.000000 | undefined | 0.000000 | 1.000000 | True | False |
| 2022 | logistic | 50756 | 421 | 0.011351 | 413 | 9093 | 8 | 41242 | 0.980998 | 0.043446 | 0.180650 | 0.956554 | 9506 | 0.800348 | 0.277638 | 0.007197 | 0.029792 | 0.820691 | 0.900174 | 0.083207 | 0.991705 | True | True |
| 2022 | xgboost | 50756 | 421 | 0.006077 | 413 | 11337 | 8 | 38998 | 0.980998 | 0.035149 | 0.225231 | 0.964851 | 11750 | 0.755767 | 0.227551 | 0.007251 | 0.029865 | 0.776480 | 0.877883 | 0.067866 | 0.991705 | True | True |
| 2022 | ensemble | 50756 | 421 | 0.008994 | 415 | 10072 | 6 | 40263 | 0.985748 | 0.039573 | 0.200099 | 0.960427 | 10487 | 0.785649 | 0.280023 | 0.007064 | 0.029196 | 0.801442 | 0.892824 | 0.076091 | 0.991705 | True | True |
| 2022 | baseline | 50756 | 421 | 0.018622 | 421 | 50335 | 0 | 0 | 1.000000 | 0.008295 | 1.000000 | 0.991705 | 50756 | 0.000000 | 0.008295 | 0.008332 | 0.051682 | 0.008295 | 0.500000 | 0.016453 | 0.991705 | True | True |
| 2023 | logistic | 60366 | 781 | 0.012784 | 697 | 7156 | 84 | 52429 | 0.892446 | 0.088756 | 0.120097 | 0.911244 | 7853 | 0.772348 | 0.216153 | 0.011315 | 0.045501 | 0.880065 | 0.886174 | 0.161455 | 0.987062 | True | True |
| 2023 | xgboost | 60366 | 781 | 0.009432 | 718 | 8146 | 63 | 51439 | 0.919334 | 0.081002 | 0.136712 | 0.918998 | 8864 | 0.782622 | 0.206027 | 0.011386 | 0.045217 | 0.864013 | 0.891311 | 0.148885 | 0.987062 | True | True |
| 2023 | ensemble | 60366 | 781 | 0.018203 | 691 | 5992 | 90 | 53593 | 0.884763 | 0.103397 | 0.100562 | 0.896603 | 6683 | 0.784201 | 0.220619 | 0.011195 | 0.043996 | 0.899248 | 0.892100 | 0.185155 | 0.987062 | True | True |
| 2023 | baseline | 60366 | 781 | 0.017951 | 781 | 59585 | 0 | 0 | 1.000000 | 0.012938 | 1.000000 | 0.987062 | 60366 | 0.000000 | 0.012938 | 0.012795 | 0.069891 | 0.012938 | 0.500000 | 0.025545 | 0.987062 | True | True |

The constant baseline illustrates event prevalence and the high-recall cost of alarming
everywhere. A larger precision accompanied by lower recall is not automatically an
improvement against the user's recall >=0.95 objective. Do not pool these years into a
single success claim: event prevalence and available populations differ across years.

## False-alarm localization

| year | fp | fn | top10_region_fp | zero_positive_region_fp |
| --- | --- | --- | --- | --- |
| 2014 | 13886 | 126 | 2729 | 7646 |
| 2015 | 11453 | 9 | 2696 | 7607 |
| 2016 | 2289 | 5 | 1478 | 1642 |
| 2017 | 1287 | 16 | 1198 | 998 |
| 2018 | 359 | 0 | 358 | 359 |
| 2022 | 10072 | 6 | 2430 | 8510 |
| 2023 | 5992 | 90 | 1836 | 4576 |

`top10_region_fp` counts false-positive windows in the ten HARPs with the most such
windows within that year. `zero_positive_region_fp` counts false positives in HARPs
with no retained positive evaluation window. This does not prove those regions never
flared. Per-region rows, positive counts, false positives, false negatives and mean
missing fraction are in each year's `region_errors.csv`. This localization is descriptive;
it does not establish a causal relationship with quality or permit removing hard regions.

## Findings that guide the next experiment

The ensemble meets the 95% recall objective in 2015, 2016 and 2022, but misses it
in 2014, 2017 and 2023. In 2022 it catches 415 of 421 positive windows while raising
10072 false-positive windows; in 2023 it catches 691 of 781 with 5992 false positives.
Thus a single calibration-selected threshold policy does not reliably preserve the
required trade-off across years. This is measured temporal variation, not proof of
one specific physical cause or proof that more training cannot help.

In 2022, 8510 false positives occur in regions with no retained positive evaluation
window; the corresponding 2023 count is 4576. In 2017 the ten largest contributors
account for 1198 of 1287 false positives. These are priorities for region-level
inspection, not reasons to delete those regions. Different yearly class prevalence,
region populations and label exclusions must be considered before attributing changes
to a model alone. No causal missing-data effect has been established by this audit.

## Conditional uncertainty

| year | model | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | logistic | recall | 0.852587 | 0.957807 | 1000 | 0 |
| 2014 | logistic | precision | 0.071203 | 0.157580 | 1000 | 0 |
| 2014 | logistic | false_positive_rate | 0.198280 | 0.263000 | 1000 | 0 |
| 2014 | logistic | false_alarm_ratio | 0.842420 | 0.928797 | 1000 | 0 |
| 2014 | logistic | brier | 0.015579 | 0.027996 | 1000 | 0 |
| 2014 | xgboost | recall | 0.897797 | 0.981056 | 1000 | 0 |
| 2014 | xgboost | precision | 0.089540 | 0.190895 | 1000 | 0 |
| 2014 | xgboost | false_positive_rate | 0.156668 | 0.224387 | 1000 | 0 |
| 2014 | xgboost | false_alarm_ratio | 0.809105 | 0.910460 | 1000 | 0 |
| 2014 | xgboost | brier | 0.015428 | 0.028196 | 1000 | 0 |
| 2014 | ensemble | recall | 0.888934 | 0.978351 | 1000 | 0 |
| 2014 | ensemble | precision | 0.089500 | 0.191422 | 1000 | 0 |
| 2014 | ensemble | false_positive_rate | 0.156074 | 0.221512 | 1000 | 0 |
| 2014 | ensemble | false_alarm_ratio | 0.808578 | 0.910500 | 1000 | 0 |
| 2014 | ensemble | brier | 0.015018 | 0.026945 | 1000 | 0 |
| 2014 | baseline | recall | 1.000000 | 1.000000 | 1000 | 0 |
| 2014 | baseline | precision | 0.018704 | 0.044908 | 1000 | 0 |
| 2014 | baseline | false_positive_rate | 1.000000 | 1.000000 | 1000 | 0 |
| 2014 | baseline | false_alarm_ratio | 0.955092 | 0.981296 | 1000 | 0 |
| 2014 | baseline | brier | 0.018356 | 0.043516 | 1000 | 0 |
| 2015 | logistic | recall | 1.000000 | 1.000000 | 1000 | 0 |
| 2015 | logistic | precision | 0.031787 | 0.084878 | 1000 | 0 |
| 2015 | logistic | false_positive_rate | 0.293114 | 0.378856 | 1000 | 0 |
| 2015 | logistic | false_alarm_ratio | 0.915122 | 0.968213 | 1000 | 0 |
| 2015 | logistic | brier | 0.008517 | 0.020928 | 1000 | 0 |
| 2015 | xgboost | recall | 0.979385 | 0.999303 | 1000 | 0 |
| 2015 | xgboost | precision | 0.072186 | 0.174073 | 1000 | 0 |
| 2015 | xgboost | false_positive_rate | 0.113725 | 0.182220 | 1000 | 0 |
| 2015 | xgboost | false_alarm_ratio | 0.825927 | 0.927814 | 1000 | 0 |
| 2015 | xgboost | brier | 0.008497 | 0.019141 | 1000 | 0 |
| 2015 | ensemble | recall | 0.977536 | 1.000000 | 1000 | 0 |
| 2015 | ensemble | precision | 0.062672 | 0.155548 | 1000 | 0 |
| 2015 | ensemble | false_positive_rate | 0.133631 | 0.205077 | 1000 | 0 |
| 2015 | ensemble | false_alarm_ratio | 0.844452 | 0.937328 | 1000 | 0 |
| 2015 | ensemble | brier | 0.008322 | 0.019523 | 1000 | 0 |
| 2015 | baseline | recall | 1.000000 | 1.000000 | 1000 | 0 |
| 2015 | baseline | precision | 0.010797 | 0.030434 | 1000 | 0 |
| 2015 | baseline | false_positive_rate | 1.000000 | 1.000000 | 1000 | 0 |
| 2015 | baseline | false_alarm_ratio | 0.969566 | 0.989203 | 1000 | 0 |
| 2015 | baseline | brier | 0.010747 | 0.029638 | 1000 | 0 |
| 2016 | logistic | recall | 0.708333 | 1.000000 | 973 | 27 |
| 2016 | logistic | precision | 0.000000 | 0.130106 | 1000 | 0 |
| 2016 | logistic | false_positive_rate | 0.036613 | 0.071652 | 1000 | 0 |
| 2016 | logistic | false_alarm_ratio | 0.869894 | 1.000000 | 1000 | 0 |
| 2016 | logistic | brier | 0.000525 | 0.007030 | 1000 | 0 |
| 2016 | xgboost | recall | 0.409091 | 1.000000 | 973 | 27 |
| 2016 | xgboost | precision | 0.000000 | 0.127311 | 1000 | 0 |
| 2016 | xgboost | false_positive_rate | 0.032350 | 0.079055 | 1000 | 0 |
| 2016 | xgboost | false_alarm_ratio | 0.872689 | 1.000000 | 1000 | 0 |
| 2016 | xgboost | brier | 0.000725 | 0.006860 | 1000 | 0 |
| 2016 | ensemble | recall | 0.772727 | 1.000000 | 973 | 27 |
| 2016 | ensemble | precision | 0.000000 | 0.132155 | 1000 | 0 |
| 2016 | ensemble | false_positive_rate | 0.031772 | 0.077849 | 1000 | 0 |
| 2016 | ensemble | false_alarm_ratio | 0.867845 | 1.000000 | 1000 | 0 |
| 2016 | ensemble | brier | 0.000507 | 0.006454 | 1000 | 0 |
| 2016 | baseline | recall | 1.000000 | 1.000000 | 973 | 27 |
| 2016 | baseline | precision | 0.000000 | 0.009217 | 1000 | 0 |
| 2016 | baseline | false_positive_rate | 1.000000 | 1.000000 | 1000 | 0 |
| 2016 | baseline | false_alarm_ratio | 0.990783 | 1.000000 | 1000 | 0 |
| 2016 | baseline | brier | 0.000490 | 0.009299 | 1000 | 0 |
| 2017 | logistic | recall | 0.861538 | 1.000000 | 949 | 51 |
| 2017 | logistic | precision | 0.000000 | 0.383697 | 1000 | 0 |
| 2017 | logistic | false_positive_rate | 0.028361 | 0.108912 | 1000 | 0 |
| 2017 | logistic | false_alarm_ratio | 0.616303 | 1.000000 | 1000 | 0 |
| 2017 | logistic | brier | 0.000575 | 0.010397 | 1000 | 0 |
| 2017 | xgboost | recall | 0.800000 | 1.000000 | 949 | 51 |
| 2017 | xgboost | precision | 0.000000 | 0.300939 | 1000 | 0 |
| 2017 | xgboost | false_positive_rate | 0.044046 | 0.136043 | 1000 | 0 |
| 2017 | xgboost | false_alarm_ratio | 0.699061 | 1.000000 | 1000 | 0 |
| 2017 | xgboost | brier | 0.000962 | 0.011223 | 1000 | 0 |
| 2017 | ensemble | recall | 0.800000 | 1.000000 | 949 | 51 |
| 2017 | ensemble | precision | 0.000000 | 0.381721 | 1000 | 0 |
| 2017 | ensemble | false_positive_rate | 0.028381 | 0.113432 | 1000 | 0 |
| 2017 | ensemble | false_alarm_ratio | 0.618279 | 1.000000 | 1000 | 0 |
| 2017 | ensemble | brier | 0.000639 | 0.010144 | 1000 | 0 |
| 2017 | baseline | recall | 1.000000 | 1.000000 | 949 | 51 |
| 2017 | baseline | precision | 0.000000 | 0.031042 | 1000 | 0 |
| 2017 | baseline | false_positive_rate | 1.000000 | 1.000000 | 1000 | 0 |
| 2017 | baseline | false_alarm_ratio | 0.968958 | 1.000000 | 1000 | 0 |
| 2017 | baseline | brier | 0.000471 | 0.030166 | 1000 | 0 |
| 2018 | logistic | recall | undefined | undefined | 0 | 1000 |
| 2018 | logistic | precision | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | logistic | false_positive_rate | 0.003450 | 0.084680 | 1000 | 0 |
| 2018 | logistic | false_alarm_ratio | 1.000000 | 1.000000 | 1000 | 0 |
| 2018 | logistic | brier | 0.000002 | 0.000073 | 1000 | 0 |
| 2018 | xgboost | recall | undefined | undefined | 0 | 1000 |
| 2018 | xgboost | precision | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | xgboost | false_positive_rate | 0.020136 | 0.135446 | 1000 | 0 |
| 2018 | xgboost | false_alarm_ratio | 1.000000 | 1.000000 | 1000 | 0 |
| 2018 | xgboost | brier | 0.000000 | 0.000016 | 1000 | 0 |
| 2018 | ensemble | recall | undefined | undefined | 0 | 1000 |
| 2018 | ensemble | precision | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | ensemble | false_positive_rate | 0.006665 | 0.097282 | 1000 | 0 |
| 2018 | ensemble | false_alarm_ratio | 1.000000 | 1.000000 | 1000 | 0 |
| 2018 | ensemble | brier | 0.000001 | 0.000029 | 1000 | 0 |
| 2018 | baseline | recall | undefined | undefined | 0 | 1000 |
| 2018 | baseline | precision | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | baseline | false_positive_rate | 1.000000 | 1.000000 | 1000 | 0 |
| 2018 | baseline | false_alarm_ratio | 1.000000 | 1.000000 | 1000 | 0 |
| 2018 | baseline | brier | 0.000397 | 0.000397 | 1000 | 0 |
| 2022 | logistic | recall | 0.926562 | 1.000000 | 1000 | 0 |
| 2022 | logistic | precision | 0.021537 | 0.070372 | 1000 | 0 |
| 2022 | logistic | false_positive_rate | 0.145584 | 0.218148 | 1000 | 0 |
| 2022 | logistic | false_alarm_ratio | 0.929628 | 0.978463 | 1000 | 0 |
| 2022 | logistic | brier | 0.003679 | 0.012003 | 1000 | 0 |
| 2022 | xgboost | recall | 0.926562 | 1.000000 | 1000 | 0 |
| 2022 | xgboost | precision | 0.017543 | 0.057538 | 1000 | 0 |
| 2022 | xgboost | false_positive_rate | 0.184199 | 0.267496 | 1000 | 0 |
| 2022 | xgboost | false_alarm_ratio | 0.942462 | 0.982457 | 1000 | 0 |
| 2022 | xgboost | brier | 0.003804 | 0.011657 | 1000 | 0 |
| 2022 | ensemble | recall | 0.944922 | 1.000000 | 1000 | 0 |
| 2022 | ensemble | precision | 0.019666 | 0.064735 | 1000 | 0 |
| 2022 | ensemble | false_positive_rate | 0.161372 | 0.239859 | 1000 | 0 |
| 2022 | ensemble | false_alarm_ratio | 0.935265 | 0.980334 | 1000 | 0 |
| 2022 | ensemble | brier | 0.003654 | 0.011523 | 1000 | 0 |
| 2022 | baseline | recall | 1.000000 | 1.000000 | 1000 | 0 |
| 2022 | baseline | precision | 0.003937 | 0.013912 | 1000 | 0 |
| 2022 | baseline | false_positive_rate | 1.000000 | 1.000000 | 1000 | 0 |
| 2022 | baseline | false_alarm_ratio | 0.986088 | 0.996063 | 1000 | 0 |
| 2022 | baseline | brier | 0.004137 | 0.013741 | 1000 | 0 |
| 2023 | logistic | recall | 0.800265 | 0.965443 | 1000 | 0 |
| 2023 | logistic | precision | 0.057459 | 0.126093 | 1000 | 0 |
| 2023 | logistic | false_positive_rate | 0.093366 | 0.146653 | 1000 | 0 |
| 2023 | logistic | false_alarm_ratio | 0.873907 | 0.942541 | 1000 | 0 |
| 2023 | logistic | brier | 0.007300 | 0.015491 | 1000 | 0 |
| 2023 | xgboost | recall | 0.825963 | 0.989714 | 1000 | 0 |
| 2023 | xgboost | precision | 0.051380 | 0.112699 | 1000 | 0 |
| 2023 | xgboost | false_positive_rate | 0.107924 | 0.165696 | 1000 | 0 |
| 2023 | xgboost | false_alarm_ratio | 0.887301 | 0.948620 | 1000 | 0 |
| 2023 | xgboost | brier | 0.007513 | 0.015465 | 1000 | 0 |
| 2023 | ensemble | recall | 0.792142 | 0.959200 | 1000 | 0 |
| 2023 | ensemble | precision | 0.067199 | 0.143637 | 1000 | 0 |
| 2023 | ensemble | false_positive_rate | 0.076680 | 0.124274 | 1000 | 0 |
| 2023 | ensemble | false_alarm_ratio | 0.856363 | 0.932801 | 1000 | 0 |
| 2023 | ensemble | brier | 0.007289 | 0.015279 | 1000 | 0 |
| 2023 | baseline | recall | 1.000000 | 1.000000 | 1000 | 0 |
| 2023 | baseline | precision | 0.007905 | 0.018382 | 1000 | 0 |
| 2023 | baseline | false_positive_rate | 1.000000 | 1.000000 | 1000 | 0 |
| 2023 | baseline | false_alarm_ratio | 0.981618 | 0.992095 | 1000 | 0 |
| 2023 | baseline | brier | 0.007943 | 0.018045 | 1000 | 0 |

Intervals use 1000 whole-HARP bootstrap draws with seed 24. Models and thresholds remain
fixed; fitting, calibration and historical model-selection uncertainty are excluded.
For a zero-positive year, recall draws are undefined. Adjacent folds share historical
training data, so their results are not independent replications. Calibration is reused
for probability fitting and threshold selection, which may overfit that period.

## Techniques used and why

- Feature engineering: means, variation, latest values and changes from 24 magnetic
  measurements over 12 hours produce 96 baseline features using past observations only.
- Median imputation with missing indicators and standard scaling: transformations learn
  from training only; logistic regression uses scaling, XGBoost does not need it.
- Logistic regression: a regularized probabilistic linear reference model. XGBoost:
  gradient-boosted trees capturing nonlinear feature interactions. This audit uses the
  already frozen parameters, with no new hyperparameter search.
- Ensembling: a fixed weighted average of separately calibrated model probabilities.
- Sigmoid calibration: fits probability adjustment on the later calibration period.
  Threshold selection then targets recall >=0.95 in that period, without promising the
  same recall in a following year.
- Expanding-window evaluation, boundary purging and HARP separation: enforce temporal
  order and reduce similarity leakage between roles. Group bootstrap measures conditional
  uncertainty while retaining within-region dependence.

Earlier separate experiments also tried signed-log transforms, class weighting,
histogram boosting, Extra Trees, interactions, splines and 24/48-hour history summaries.
They are not all rerun here. Deep learning and live-data prediction have not been added
by this audit. Longer training by itself does not guarantee better precision.

## When can the best result be reached, and what follows?

There is no evidence-based date for a perfect model, nor a guarantee that the available
measurements and labels permit perfect separation. Training completion is not proof of
forecasting quality. Progress means reproducible gains at the required recall across
chronological evaluations, with uncertainty and false-alarm burden reported. A practical
precision requirement depends on how many false alerts an application can tolerate;
there is no universal satisfactory precision value.

Next, inspect temporal failures and regional error distributions, then freeze one
targeted candidate comparison using these same annual splits. Consider separating
probability fitting from threshold selection in time and assessing how much calibration
history is needed; do not retune on evaluation-year labels to force the 95% result.
Any revised policy must be measured as a new development experiment. Historical flare
features require verified availability timestamps and region associations. The reserved
test should be used only after the complete selection policy is frozen. These follow-up
experiments are not claimed to have been executed here.

## Reproduction

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_walk_forward.py \
  --protocol config/walk-forward-v1.json --output artifacts/walk_forward_20261028_r1
.venv/bin/python scripts/report_walk_forward.py \
  --source artifacts/walk_forward_20261028_r1 --report-name walk-forward-20261028
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_walk-forward-20261028
```

Use fresh output directories, report names and protocol revisions for reruns; frozen
outputs cannot be overwritten. Review both full editions and register them in
`docs/reports.json` and `docs/reports.md` before publishing. Local model files, predictions,
raw data and generated HTML remain outside Git. Per-fold artifact hashes and code hashes
are recorded in `report.json`.

| source | SHA-256 |
| --- | --- |
| artifacts/walk_forward_20261028_r1/report.json | 6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c |
| artifacts/walk_forward_20261028_r1/metrics.csv | ff928fdd1485d12a323f0b0b49456c18a958ba4176802a34c8aa560f6fb096b0 |

