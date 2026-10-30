# One- and two-year calibration with shared classifier training

The two-year arm reaches recall >=0.95 in 4 of 6 positive evaluation years.
The all-year acceptance gate is `False`. No model or alarm policy was promoted to the
dashboard. The reserved 2024–2025 test stays closed. Year-specific gains must not be
presented as a consistent improvement without the control comparisons below.

## Frozen question and controls

The preceding audit found sparse positive-region support and threshold sensitivity.
This experiment asks whether a fixed two-year calibration window improves temporal
transfer compared with a fixed one-year window when underlying classifier training is
identical. `config/calibration-windows-v1.json` freezes the design; there is no duration
grid or retrospective split-date tuning.

For evaluation year Y, the two new arms share logistic and XGBoost classifiers trained
before January 1 of Y-2. Prediction windows must end by that date. Both retain the same
96 features, original hyperparameters and 0.45/0.55 blend. `shared_train_two_year` calibrates
on Y-2 and Y-1; `shared_train_one_year` uses only the Y-1 subset. Training HARPs are removed
from calibration, and observation/prediction intervals must lie within calendar boundaries.
Each arm fits sigmoid calibration and selects its recall >=0.95 threshold on its own
calibration window, freezes the threshold, then predicts the evaluation year. Probability
fitting and threshold selection still reuse the same calibration rows; this is explicit.

`original_baseline` uses the frozen original annual model with an extra year of classifier
training, where available. Comparing the two new arms isolates calibration duration
under shared training. Comparing either with the original baseline also changes the
classifier training history and is not solely a calibration-duration contrast.

Use the original annual evaluation population, excluding any additional HARP shared
with the new training or two-year pool, and apply the same resulting rows to all arms.
Report any removed rows. Original label/quality exclusions remain. All source models,
predictions and input manifests are hash-verified; baseline keys and labels must align.

## Counts, region diversity and availability

| year | role | rows | positives | regions | positive_regions |
| --- | --- | --- | --- | --- | --- |
| 2014 | train | 82507 | 1633 | 628 | 34 |
| 2014 | one_year | 74853 | 1287 | 593 | 31 |
| 2014 | two_year | 140149 | 2596 | 1128 | 57 |
| 2014 | evaluation | 75228 | 2310 | 629 | 44 |
| 2015 | train | 148508 | 2959 | 1168 | 60 |
| 2015 | one_year | 75790 | 2341 | 636 | 45 |
| 2015 | two_year | 150287 | 3674 | 1217 | 75 |
| 2015 | evaluation | 69138 | 1355 | 599 | 24 |
| 2016 | train | 223647 | 4246 | 1756 | 91 |
| 2016 | one_year | 70117 | 1403 | 608 | 25 |
| 2016 | two_year | 145794 | 3713 | 1228 | 69 |
| 2016 | evaluation | 42987 | 181 | 357 | 4 |
| 2017 | train | 299785 | 6633 | 2385 | 135 |
| 2017 | one_year | 43122 | 193 | 360 | 5 |
| 2017 | two_year | 112391 | 1560 | 956 | 28 |
| 2017 | evaluation | 19529 | 253 | 163 | 3 |
| 2018 | train | 370351 | 8036 | 2984 | 160 |
| 2018 | one_year | 19698 | 253 | 166 | 3 |
| 2018 | two_year | 62782 | 434 | 520 | 7 |
| 2018 | evaluation | 7799 | 0 | 74 | 0 |
| 2019 | train | 413604 | 8241 | 3341 | 164 |
| 2019 | one_year | 7880 | 0 | 75 | 0 |
| 2019 | two_year | 27474 | 253 | 237 | 3 |
| 2019 | evaluation | 4919 | 0 | 44 | 0 |
| 2020 | train | 433399 | 8494 | 3504 | 167 |
| 2020 | one_year | 4919 | 0 | 44 | 0 |
| 2020 | two_year | 12758 | 0 | 118 | 0 |
| 2020 | evaluation | 9813 | 0 | 77 | 0 |
| 2021 | train | 441344 | 8494 | 3578 | 167 |
| 2021 | one_year | 9813 | 0 | 77 | 0 |
| 2021 | two_year | 14742 | 0 | 121 | 0 |
| 2021 | evaluation | 28125 | 204 | 255 | 9 |
| 2022 | train | 446303 | 8494 | 3622 | 167 |
| 2022 | one_year | 28318 | 204 | 258 | 9 |
| 2022 | two_year | 38236 | 204 | 332 | 9 |
| 2022 | evaluation | 50756 | 421 | 528 | 12 |
| 2023 | train | 456126 | 8494 | 3699 | 167 |
| 2023 | one_year | 50756 | 421 | 528 | 12 |
| 2023 | two_year | 78881 | 625 | 783 | 21 |
| 2023 | evaluation | 60366 | 781 | 703 | 27 |

`positive_regions` counts HARPs with retained positive windows, not independent flares.
More windows do not automatically imply more positive-region diversity; inspect the
one-year and two-year counts together. Counts refer to purged populations.

| year | status | additional_evaluation_rows_removed | unavailable | passes_gate |
| --- | --- | --- | --- | --- |
| 2014 | complete | 0 | {} | False |
| 2015 | complete | 0 | {} | False |
| 2016 | complete | 0 | {} | False |
| 2017 | complete | 0 | {} | False |
| 2018 | complete | 0 | {} | undefined |
| 2019 | complete | 0 | {"original_baseline": "Training/calibration lacks both classes: ['calibration']", "shared_train_one_year": "Training or calibration lacks both classes"} | undefined |
| 2020 | skipped | 0 | {"original_baseline": "Training/calibration lacks both classes: ['calibration']", "shared_train_one_year": "Training or calibration lacks both classes", "shared_train_two_year": "Training or calibration lacks both classes"} | undefined |
| 2021 | skipped | 0 | {"original_baseline": "Training/calibration lacks both classes: ['calibration']", "shared_train_one_year": "Training or calibration lacks both classes", "shared_train_two_year": "Training or calibration lacks both classes"} | undefined |
| 2022 | complete | 0 | {} | True |
| 2023 | complete | 0 | {} | False |

Arms independently require both training and calibration classes and nonempty evaluation.
Unavailable arms are never replaced by baseline. The original baseline exists only in
its previously completed folds. A two-year arm may be available in a year without an
original baseline; such results are unpaired evidence, not a measured improvement.
Zero-positive evaluation years retain FP/FPR but have undefined recall/AP. If no alarms
are emitted, precision is undefined too. `undefined` does not mean zero.

## Annual precision, recall and false-positive windows

| year | arm | n | positives | precision | recall | fp | fn | threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | original_baseline | 75228 | 2310 | 0.135905 | 0.945455 | 13886 | 126 | 0.011475 |
| 2014 | shared_train_one_year | 75228 | 2310 | 0.123993 | 0.952381 | 15543 | 110 | 0.010974 |
| 2014 | shared_train_two_year | 75228 | 2310 | 0.130032 | 0.946753 | 14632 | 123 | 0.014190 |
| 2015 | original_baseline | 69138 | 1355 | 0.105164 | 0.993358 | 11453 | 9 | 0.018839 |
| 2015 | shared_train_one_year | 69138 | 1355 | 0.110455 | 0.994096 | 10848 | 8 | 0.020398 |
| 2015 | shared_train_two_year | 69138 | 1355 | 0.114749 | 0.993358 | 10384 | 9 | 0.016427 |
| 2016 | original_baseline | 42987 | 181 | 0.071400 | 0.972376 | 2289 | 5 | 0.030831 |
| 2016 | shared_train_one_year | 42987 | 181 | 0.076092 | 0.972376 | 2137 | 5 | 0.032370 |
| 2016 | shared_train_two_year | 42987 | 181 | 0.044612 | 0.983425 | 3812 | 3 | 0.025267 |
| 2017 | original_baseline | 19529 | 253 | 0.155512 | 0.936759 | 1287 | 16 | 0.012000 |
| 2017 | shared_train_one_year | 19529 | 253 | 0.161814 | 0.944664 | 1238 | 14 | 0.014550 |
| 2017 | shared_train_two_year | 19529 | 253 | 0.149068 | 0.948617 | 1370 | 13 | 0.026176 |
| 2018 | original_baseline | 7799 | 0 | 0.000000 | undefined | 359 | 0 | 0.004351 |
| 2018 | shared_train_one_year | 7799 | 0 | 0.000000 | undefined | 351 | 0 | 0.004511 |
| 2018 | shared_train_two_year | 7799 | 0 | 0.000000 | undefined | 237 | 0 | 0.009588 |
| 2019 | shared_train_two_year | 4919 | 0 | 0.000000 | undefined | 312 | 0 | 0.003541 |
| 2022 | original_baseline | 50756 | 421 | 0.039573 | 0.985748 | 10072 | 6 | 0.008994 |
| 2022 | shared_train_one_year | 50756 | 421 | 0.041375 | 0.983373 | 9592 | 7 | 0.009790 |
| 2022 | shared_train_two_year | 50756 | 421 | 0.041491 | 0.983373 | 9564 | 7 | 0.007402 |
| 2023 | original_baseline | 60366 | 781 | 0.103397 | 0.884763 | 5992 | 90 | 0.018203 |
| 2023 | shared_train_one_year | 60366 | 781 | 0.106350 | 0.889885 | 5840 | 86 | 0.018942 |
| 2023 | shared_train_two_year | 60366 | 781 | 0.060194 | 0.959027 | 11694 | 32 | 0.007094 |

Scores are fractions on a 0–1 scale; counts are overlapping forecast windows, not
independent flares or notifications. Each arm uses its own transferred calibration
threshold. Do not count a higher precision at recall below 0.95 as the requested success.

Two-year arm minus each available control:

| year | control | precision_delta | recall_delta | fp_delta |
| --- | --- | --- | --- | --- |
| 2014 | original_baseline | -0.005874 | 0.001299 | 746 |
| 2014 | shared_train_one_year | 0.006039 | -0.005628 | -911 |
| 2015 | original_baseline | 0.009584 | 0.000000 | -1069 |
| 2015 | shared_train_one_year | 0.004293 | -0.000738 | -464 |
| 2016 | original_baseline | -0.026788 | 0.011050 | 1523 |
| 2016 | shared_train_one_year | -0.031480 | 0.011050 | 1675 |
| 2017 | original_baseline | -0.006443 | 0.011858 | 83 |
| 2017 | shared_train_one_year | -0.012746 | 0.003953 | 132 |
| 2018 | original_baseline | 0.000000 | undefined | -122 |
| 2018 | shared_train_one_year | 0.000000 | undefined | -114 |
| 2022 | original_baseline | 0.001918 | -0.002375 | -508 |
| 2022 | shared_train_one_year | 0.000116 | 0.000000 | -28 |
| 2023 | original_baseline | -0.043202 | 0.074264 | 5702 |
| 2023 | shared_train_one_year | -0.046156 | 0.069142 | 5854 |

Positive precision/recall differences favor the two-year arm; negative FP differences
mean fewer false-positive windows. No pooled multi-year average replaces these contrasts.

## Complete metrics and acceptance

| year | arm | n | positives | threshold | tp | fp | fn | tn | recall | precision | false_positive_rate | false_alarm_ratio | alarms | tss | average_precision | brier | log_loss | accuracy | balanced_accuracy | f1 | always_quiet_accuracy | precision_defined | recall_defined |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | original_baseline | 75228 | 2310 | 0.011475 | 2184 | 13886 | 126 | 59032 | 0.945455 | 0.135905 | 0.190433 | 0.864095 | 16070 | 0.755021 | 0.507930 | 0.020661 | 0.076538 | 0.813740 | 0.877511 | 0.237650 | 0.969293 | True | True |
| 2014 | shared_train_one_year | 75228 | 2310 | 0.010974 | 2200 | 15543 | 110 | 57375 | 0.952381 | 0.123993 | 0.213157 | 0.876007 | 17743 | 0.739224 | 0.483201 | 0.020988 | 0.078063 | 0.791926 | 0.869612 | 0.219419 | 0.969293 | True | True |
| 2014 | shared_train_two_year | 75228 | 2310 | 0.014190 | 2187 | 14632 | 123 | 58286 | 0.946753 | 0.130032 | 0.200664 | 0.869968 | 16819 | 0.746089 | 0.486485 | 0.020934 | 0.077733 | 0.803863 | 0.873045 | 0.228658 | 0.969293 | True | True |
| 2015 | original_baseline | 69138 | 1355 | 0.018839 | 1346 | 11453 | 9 | 56330 | 0.993358 | 0.105164 | 0.168966 | 0.894836 | 12799 | 0.824392 | 0.492441 | 0.013564 | 0.047847 | 0.834216 | 0.912196 | 0.190194 | 0.980402 | True | True |
| 2015 | shared_train_one_year | 69138 | 1355 | 0.020398 | 1347 | 10848 | 8 | 56935 | 0.994096 | 0.110455 | 0.160040 | 0.889545 | 12195 | 0.834056 | 0.488445 | 0.013474 | 0.047741 | 0.842981 | 0.917028 | 0.198819 | 0.980402 | True | True |
| 2015 | shared_train_two_year | 69138 | 1355 | 0.016427 | 1346 | 10384 | 9 | 57399 | 0.993358 | 0.114749 | 0.153195 | 0.885251 | 11730 | 0.840163 | 0.488916 | 0.013481 | 0.046870 | 0.849677 | 0.920082 | 0.205732 | 0.980402 | True | True |
| 2016 | original_baseline | 42987 | 181 | 0.030831 | 176 | 2289 | 5 | 40517 | 0.972376 | 0.071400 | 0.053474 | 0.928600 | 2465 | 0.918902 | 0.366443 | 0.003263 | 0.014523 | 0.946635 | 0.959451 | 0.133031 | 0.995789 | True | True |
| 2016 | shared_train_one_year | 42987 | 181 | 0.032370 | 176 | 2137 | 5 | 40669 | 0.972376 | 0.076092 | 0.049923 | 0.923908 | 2313 | 0.922453 | 0.433388 | 0.003128 | 0.013935 | 0.950171 | 0.961226 | 0.141139 | 0.995789 | True | True |
| 2016 | shared_train_two_year | 42987 | 181 | 0.025267 | 178 | 3812 | 3 | 38994 | 0.983425 | 0.044612 | 0.089053 | 0.955388 | 3990 | 0.894372 | 0.434278 | 0.003199 | 0.015885 | 0.911252 | 0.947186 | 0.085351 | 0.995789 | True | True |
| 2017 | original_baseline | 19529 | 253 | 0.012000 | 237 | 1287 | 16 | 17989 | 0.936759 | 0.155512 | 0.066767 | 0.844488 | 1524 | 0.869992 | 0.811694 | 0.004907 | 0.020488 | 0.933279 | 0.934996 | 0.266742 | 0.987045 | True | True |
| 2017 | shared_train_one_year | 19529 | 253 | 0.014550 | 239 | 1238 | 14 | 18038 | 0.944664 | 0.161814 | 0.064225 | 0.838186 | 1477 | 0.880439 | 0.806978 | 0.004954 | 0.020646 | 0.935890 | 0.940220 | 0.276301 | 0.987045 | True | True |
| 2017 | shared_train_two_year | 19529 | 253 | 0.026176 | 240 | 1370 | 13 | 17906 | 0.948617 | 0.149068 | 0.071073 | 0.850932 | 1610 | 0.877544 | 0.807301 | 0.005278 | 0.022802 | 0.929182 | 0.938772 | 0.257649 | 0.987045 | True | True |
| 2018 | original_baseline | 7799 | 0 | 0.004351 | 0 | 359 | 0 | 7440 | undefined | 0.000000 | 0.046032 | 1.000000 | 359 | undefined | undefined | 0.000012 | 0.000791 | 0.953968 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | shared_train_one_year | 7799 | 0 | 0.004511 | 0 | 351 | 0 | 7448 | undefined | 0.000000 | 0.045006 | 1.000000 | 351 | undefined | undefined | 0.000012 | 0.000796 | 0.954994 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | shared_train_two_year | 7799 | 0 | 0.009588 | 0 | 237 | 0 | 7562 | undefined | 0.000000 | 0.030389 | 1.000000 | 237 | undefined | undefined | 0.000016 | 0.000977 | 0.969611 | undefined | 0.000000 | 1.000000 | True | False |
| 2019 | shared_train_two_year | 4919 | 0 | 0.003541 | 0 | 312 | 0 | 4607 | undefined | 0.000000 | 0.063428 | 1.000000 | 312 | undefined | undefined | 0.000502 | 0.003290 | 0.936572 | undefined | 0.000000 | 1.000000 | True | False |
| 2022 | original_baseline | 50756 | 421 | 0.008994 | 415 | 10072 | 6 | 40263 | 0.985748 | 0.039573 | 0.200099 | 0.960427 | 10487 | 0.785649 | 0.280023 | 0.007064 | 0.029196 | 0.801442 | 0.892824 | 0.076091 | 0.991705 | True | True |
| 2022 | shared_train_one_year | 50756 | 421 | 0.009790 | 414 | 9592 | 7 | 40743 | 0.983373 | 0.041375 | 0.190563 | 0.958625 | 10006 | 0.792810 | 0.284225 | 0.007028 | 0.029089 | 0.810880 | 0.896405 | 0.079409 | 0.991705 | True | True |
| 2022 | shared_train_two_year | 50756 | 421 | 0.007402 | 414 | 9564 | 7 | 40771 | 0.983373 | 0.041491 | 0.190007 | 0.958509 | 9978 | 0.793366 | 0.285019 | 0.006989 | 0.028388 | 0.811431 | 0.896683 | 0.079623 | 0.991705 | True | True |
| 2023 | original_baseline | 60366 | 781 | 0.018203 | 691 | 5992 | 90 | 53593 | 0.884763 | 0.103397 | 0.100562 | 0.896603 | 6683 | 0.784201 | 0.220619 | 0.011195 | 0.043996 | 0.899248 | 0.892100 | 0.185155 | 0.987062 | True | True |
| 2023 | shared_train_one_year | 60366 | 781 | 0.018942 | 695 | 5840 | 86 | 53745 | 0.889885 | 0.106350 | 0.098011 | 0.893650 | 6535 | 0.791874 | 0.229153 | 0.011149 | 0.043730 | 0.901832 | 0.895937 | 0.189995 | 0.987062 | True | True |
| 2023 | shared_train_two_year | 60366 | 781 | 0.007094 | 749 | 11694 | 32 | 47891 | 0.959027 | 0.060194 | 0.196257 | 0.939806 | 12443 | 0.762769 | 0.229548 | 0.011102 | 0.043389 | 0.805752 | 0.881385 | 0.113279 | 0.987062 | True | True |

Precision measures positives among alarms, recall caught positive windows, and accuracy
all correct classifications. AP measures ranking; lower Brier/log loss is better
probabilistic scoring. The frozen gate requires complete candidate coverage of all
originally baseline-comparable positive years, higher precision with recall >=0.95,
AP no lower and Brier/log loss no higher than both controls in every such year. No
automatic deployment follows even a passed gate. Sparse or missing periods stay visible.

## Findings from this run

Only 2022 passes the full per-year gate against both controls. Even there, versus the
shared-training one-year control, precision changes from 0.041375 to 0.041491 and false
positives from 9592 to 9564, with recall unchanged at 0.983373. Both windows contain 9
positive HARPs; extending the window does not add positive-region diversity in that year.

In 2016, positive HARPs increase from 25 to 69, yet false positives rise from 2137 to
3812 and precision falls from 0.076092 to 0.044612 versus the shared-training control.
In 2023, positive HARPs increase from 12 to 21; recall rises from 0.889885 to 0.959027,
but false positives rise from 5840 to 11694 and precision falls from 0.106350 to 0.060194.
More positive-region coverage therefore does not itself establish a better operating
point. No additional evaluation rows were removed in any year.

The 2019 two-year arm has 312 false-positive windows and no positive evaluation windows;
there is no original or one-year control available for that year. In 2020 and 2021 no
arm is available. These periods are not omitted or counted as improvements. The tested
two-year policy is not adopted; another duration search is not justified by this run alone.

## Paired conditional uncertainty

| year | control | metric | lower | upper | valid_draws |
| --- | --- | --- | --- | --- | --- |
| 2014 | original_baseline | precision | -0.009523 | -0.002794 | 1000 |
| 2014 | original_baseline | recall | -0.007179 | 0.014346 | 1000 |
| 2014 | original_baseline | fp | 451.950000 | 1053.000000 | 1000 |
| 2014 | shared_train_one_year | precision | 0.003759 | 0.008677 | 1000 |
| 2014 | shared_train_one_year | recall | -0.011853 | -0.001576 | 1000 |
| 2014 | shared_train_one_year | fp | -1106.050000 | -724.975000 | 1000 |
| 2015 | original_baseline | precision | 0.005274 | 0.015383 | 1000 |
| 2015 | original_baseline | recall | 0.000000 | 0.000000 | 1000 |
| 2015 | original_baseline | fp | -1471.350000 | -740.950000 | 1000 |
| 2015 | shared_train_one_year | precision | 0.002570 | 0.006408 | 1000 |
| 2015 | shared_train_one_year | recall | -0.002999 | 0.000000 | 1000 |
| 2015 | shared_train_one_year | fp | -591.000000 | -341.000000 | 1000 |
| 2016 | original_baseline | precision | -0.048811 | 0.000000 | 1000 |
| 2016 | original_baseline | recall | 0.000000 | 0.090909 | 973 |
| 2016 | original_baseline | fp | 1065.925000 | 2050.150000 | 1000 |
| 2016 | shared_train_one_year | precision | -0.056642 | 0.000000 | 1000 |
| 2016 | shared_train_one_year | recall | 0.000000 | 0.090909 | 973 |
| 2016 | shared_train_one_year | fp | 1186.975000 | 2260.075000 | 1000 |
| 2017 | original_baseline | precision | -0.028886 | 0.000336 | 1000 |
| 2017 | original_baseline | recall | 0.000000 | 0.046154 | 949 |
| 2017 | original_baseline | fp | 25.000000 | 160.000000 | 1000 |
| 2017 | shared_train_one_year | precision | -0.035986 | 0.000000 | 1000 |
| 2017 | shared_train_one_year | recall | 0.000000 | 0.015385 | 949 |
| 2017 | shared_train_one_year | fp | 68.975000 | 208.025000 | 1000 |
| 2018 | original_baseline | precision | 0.000000 | 0.000000 | 1000 |
| 2018 | original_baseline | recall | undefined | undefined | 0 |
| 2018 | original_baseline | fp | -249.000000 | -29.000000 | 1000 |
| 2018 | shared_train_one_year | precision | 0.000000 | 0.000000 | 1000 |
| 2018 | shared_train_one_year | recall | undefined | undefined | 0 |
| 2018 | shared_train_one_year | fp | -222.050000 | -29.000000 | 1000 |
| 2022 | original_baseline | precision | 0.000900 | 0.003161 | 1000 |
| 2022 | original_baseline | recall | -0.009180 | 0.000000 | 1000 |
| 2022 | original_baseline | fp | -653.000000 | -383.950000 | 1000 |
| 2022 | shared_train_one_year | precision | 0.000051 | 0.000206 | 1000 |
| 2022 | shared_train_one_year | recall | 0.000000 | 0.000000 | 1000 |
| 2022 | shared_train_one_year | fp | -41.000000 | -16.000000 | 1000 |
| 2023 | original_baseline | precision | -0.063876 | -0.026031 | 1000 |
| 2023 | original_baseline | recall | 0.022419 | 0.136529 | 1000 |
| 2023 | original_baseline | fp | 4503.850000 | 6915.200000 | 1000 |
| 2023 | shared_train_one_year | precision | -0.067960 | -0.028180 | 1000 |
| 2023 | shared_train_one_year | recall | 0.022985 | 0.128646 | 1000 |
| 2023 | shared_train_one_year | fp | 4635.750000 | 7079.675000 | 1000 |

Intervals are two-year arm minus the named control, from 1000 paired whole-HARP bootstrap
draws per year, seed 24. Both arms use the same sampled regions with classifiers,
calibrators and thresholds fixed. Fitting and historical model-selection uncertainty
are excluded. `valid_draws` identifies undefined precision/recall draws. Adjacent annual
folds share historical training and are not independent replications. Intervals spanning
zero do not establish a directional change at that interval level.

## Interpretation limits

This is adaptive retrospective development motivated by prior diagnostics, not an
untouched test. A longer window trades recency for more data and potentially more positive
regions; neither calibration stability nor precision improvement follows automatically.
The shared-training control is necessary because making room for a longer calibration
period shortens classifier training. Stronger or weaker scores against the original
baseline cannot be attributed solely to duration.

Retain the current model unless the multi-period evidence supports replacing it. Any
next policy must be fixed using earlier inner chronological folds; do not pick a different
duration for each evaluated year using its outcomes. No live forecast, label correction,
additional duration search or release decision is claimed in this report.

## Reproduction

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_calibration_windows.py \
  --protocol config/calibration-windows-v1.json --output artifacts/calibration_windows_20261030_r1
.venv/bin/python scripts/report_calibration_windows.py --source artifacts/calibration_windows_20261030_r1 --report-name calibration-windows-20261030
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_calibration-windows-20261030
```

Choose fresh output directories and report names. Preserve frozen source artifacts
and protocols. Review both full editions, register their source hash and links in
`docs/reports.json` and `docs/reports.md`, and publish into a fresh HTML directory.
Models, calibrators, predictions and generated HTML remain local ignored artifacts.
The experiment records source, protocol, code and output hashes.

| source | SHA-256 |
| --- | --- |
| artifacts/calibration_windows_20261030_r1/report.json | 59290a8f2a74c4f993f45539c2f9f3306cb4e5d97046884560333552d5a247ba |
| artifacts/calibration_windows_20261030_r1/metrics.csv | 73fb4536374c125ee1e611a84ecb8d6207539d70ae6ab744042c7550e2314340 |

