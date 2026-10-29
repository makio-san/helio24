# Multi-period hard-negative training comparison

The hard-negative candidate reaches recall >=0.95 in 3 of 6 comparable positive
evaluation years. Precision exceeds baseline in 3 evaluated years. The all-year
gate result is `False`. No dashboard model was promoted; the reserved 2024–2025 test
remains closed. A gain in one year is not presented as general improvement.

## Frozen design and data separation

`config/hard-negative-v2.json` makes the previously selected design executable without
changing its candidate budget. The annual populations, 96 magnetic features and baseline
hyperparameters match `walk-forward-v1`. All prior model and prediction hashes are verified;
new annual split audits and evaluation metadata must exactly match the frozen baseline.
All original outer-training rows are retained. Historical label/quality exclusions remain.

For evaluation year Y, calibration is Y-1 and outer training precedes that year. A teacher
XGBoost fits before January 1 of Y-3; mining uses known negatives from the last two outer-
training years. Observation/prediction boundaries are purged; mining HARPs also seen by
the teacher are excluded from mining, not from final student training. The highest-scored
ceil(0.10 * eligible_count) negatives are selected, using forecast time and HARP to break
ties. The teacher never sees the mining windows during fitting. Evaluation-year errors
are not used as training examples, features or mining labels.

Three fixed arms are evaluated:

- `baseline_unweighted`: the frozen 0.45 logistic/0.55 XGBoost ensemble.
- `hard_negative_weighted`: selected negatives receive weight 3, every other training
  row weight 1. Only the XGBoost component is retrained; logistic stays unchanged.
- `uniform_negative_matched_weight`: all training negatives receive weight
  `1 + 2 * hard_negative_count / outer_training_negative_count`, positives weight 1.
  Its total training negative weight matches the targeted arm exactly up to rounding.

Each new XGBoost is sigmoid-calibrated on the same outer calibration year. Its 0.45/0.55
ensemble threshold is selected there at recall >=0.95 and written before evaluation
predictions. It is never retuned on evaluation labels. Neither the blend nor the weight
factor is selected from evaluation results. Separating probability calibration and
threshold selection into different periods was not part of this experiment.

## Coverage, mining counts and gates

| year | status | reason | teacher_rows | eligible_negatives | hard_negatives | targeted_weight_sum | uniform_weight_sum | passes_gate | beats_uniform_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | complete | undefined | 21050.000000 | 123934.000000 | 12394.000000 | 173296.000000 | 173296.000000 | False | True |
| 2015 | complete | undefined | 82507.000000 | 137553.000000 | 13756.000000 | 251159.000000 | 251159.000000 | True | True |
| 2016 | complete | undefined | 148508.000000 | 146613.000000 | 14662.000000 | 329109.000000 | 329109.000000 | False | True |
| 2017 | complete | undefined | 223647.000000 | 142081.000000 | 14209.000000 | 398769.000000 | 398769.000000 | False | False |
| 2018 | complete | undefined | 299785.000000 | 110831.000000 | 11084.000000 | 435772.000000 | 435772.000000 | undefined | False |
| 2019 | skipped | Training/calibration lacks both classes: ['calibration'] | undefined | undefined | undefined | undefined | undefined | undefined | undefined |
| 2020 | skipped | Training/calibration lacks both classes: ['calibration'] | undefined | undefined | undefined | undefined | undefined | undefined | undefined |
| 2021 | skipped | Training/calibration lacks both classes: ['calibration'] | undefined | undefined | undefined | undefined | undefined | undefined | undefined |
| 2022 | complete | undefined | 441344.000000 | 14742.000000 | 1475.000000 | 459076.000000 | 459076.000000 | False | True |
| 2023 | complete | undefined | 446303.000000 | 38032.000000 | 3804.000000 | 492157.000000 | 492157.000000 | False | False |

The existing 2019–2021 fold skips are preserved because their preceding calibration
years lack positive examples. In the retained 2018 evaluation data there are no positives;
recall is undefined, while false alarms remain measurable. Missing class diversity in
teacher fitting or no mining negatives would make new arms unavailable, not silently
replace them with baseline. `undefined` never means a measured zero.

## Precision, recall and false alarms by period

| year | arm | n | positives | precision | recall | fp | fn | threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | baseline_unweighted | 75228 | 2310 | 0.135905 | 0.945455 | 13886 | 126 | 0.011475 |
| 2014 | hard_negative_weighted | 75228 | 2310 | 0.140464 | 0.940260 | 13291 | 138 | 0.011643 |
| 2014 | uniform_negative_matched_weight | 75228 | 2310 | 0.132063 | 0.948052 | 14393 | 120 | 0.010818 |
| 2015 | baseline_unweighted | 69138 | 1355 | 0.105164 | 0.993358 | 11453 | 9 | 0.018839 |
| 2015 | hard_negative_weighted | 69138 | 1355 | 0.106261 | 0.997048 | 11363 | 4 | 0.019888 |
| 2015 | uniform_negative_matched_weight | 69138 | 1355 | 0.104511 | 0.993358 | 11533 | 9 | 0.018748 |
| 2016 | baseline_unweighted | 42987 | 181 | 0.071400 | 0.972376 | 2289 | 5 | 0.030831 |
| 2016 | hard_negative_weighted | 42987 | 181 | 0.076453 | 0.966851 | 2114 | 6 | 0.035959 |
| 2016 | uniform_negative_matched_weight | 42987 | 181 | 0.070683 | 0.972376 | 2314 | 5 | 0.030137 |
| 2017 | baseline_unweighted | 19529 | 253 | 0.155512 | 0.936759 | 1287 | 16 | 0.012000 |
| 2017 | hard_negative_weighted | 19529 | 253 | 0.149527 | 0.936759 | 1348 | 16 | 0.012829 |
| 2017 | uniform_negative_matched_weight | 19529 | 253 | 0.156229 | 0.936759 | 1280 | 16 | 0.012192 |
| 2018 | baseline_unweighted | 7799 | 0 | 0.000000 | undefined | 359 | 0 | 0.004351 |
| 2018 | hard_negative_weighted | 7799 | 0 | 0.000000 | undefined | 342 | 0 | 0.004922 |
| 2018 | uniform_negative_matched_weight | 7799 | 0 | 0.000000 | undefined | 352 | 0 | 0.004456 |
| 2022 | baseline_unweighted | 50756 | 421 | 0.039573 | 0.985748 | 10072 | 6 | 0.008994 |
| 2022 | hard_negative_weighted | 50756 | 421 | 0.039281 | 0.985748 | 10150 | 6 | 0.009074 |
| 2022 | uniform_negative_matched_weight | 50756 | 421 | 0.038778 | 0.985748 | 10287 | 6 | 0.008743 |
| 2023 | baseline_unweighted | 60366 | 781 | 0.103397 | 0.884763 | 5992 | 90 | 0.018203 |
| 2023 | hard_negative_weighted | 60366 | 781 | 0.097381 | 0.895006 | 6479 | 82 | 0.016408 |
| 2023 | uniform_negative_matched_weight | 60366 | 781 | 0.101536 | 0.888604 | 6141 | 87 | 0.017537 |

Scores are fractions on a 0–1 scale. FP and FN count overlapping forecast windows, not
independent flares or alert episodes. Each annual comparison uses the same population
and transferred thresholds for all arms, but populations and event prevalence differ
between years. More precision at the cost of missing the recall objective is not accepted
as the requested improvement.

Candidate minus baseline differences, and precision difference versus the uniform control:

| year | precision_delta | recall_delta | fp_delta | precision_delta_vs_uniform |
| --- | --- | --- | --- | --- |
| 2014 | 0.004559 | -0.005195 | -595 | 0.008401 |
| 2015 | 0.001096 | 0.003690 | -90 | 0.001750 |
| 2016 | 0.005053 | -0.005525 | -175 | 0.005770 |
| 2017 | -0.005985 | 0.000000 | 61 | -0.006703 |
| 2018 | 0.000000 | undefined | -17 | 0.000000 |
| 2022 | -0.000292 | 0.000000 | 78 | 0.000503 |
| 2023 | -0.006016 | 0.010243 | 487 | -0.004155 |

Positive precision/recall differences favor the candidate; negative FP differences mean
fewer false-positive windows. No pooled multi-year score substitutes for this table.

## Complete metric results

| year | arm | n | positives | threshold | tp | fp | fn | tn | recall | precision | false_positive_rate | false_alarm_ratio | alarms | tss | average_precision | brier | log_loss | accuracy | balanced_accuracy | f1 | always_quiet_accuracy | precision_defined | recall_defined |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | baseline_unweighted | 75228 | 2310 | 0.011475 | 2184 | 13886 | 126 | 59032 | 0.945455 | 0.135905 | 0.190433 | 0.864095 | 16070 | 0.755021 | 0.507930 | 0.020661 | 0.076538 | 0.813740 | 0.877511 | 0.237650 | 0.969293 | True | True |
| 2014 | hard_negative_weighted | 75228 | 2310 | 0.011643 | 2172 | 13291 | 138 | 59627 | 0.940260 | 0.140464 | 0.182273 | 0.859536 | 15463 | 0.757987 | 0.510933 | 0.020603 | 0.076915 | 0.821489 | 0.878993 | 0.244416 | 0.969293 | True | True |
| 2014 | uniform_negative_matched_weight | 75228 | 2310 | 0.010818 | 2190 | 14393 | 120 | 58525 | 0.948052 | 0.132063 | 0.197386 | 0.867937 | 16583 | 0.750666 | 0.507635 | 0.020720 | 0.076842 | 0.807080 | 0.875333 | 0.231832 | 0.969293 | True | True |
| 2015 | baseline_unweighted | 69138 | 1355 | 0.018839 | 1346 | 11453 | 9 | 56330 | 0.993358 | 0.105164 | 0.168966 | 0.894836 | 12799 | 0.824392 | 0.492441 | 0.013564 | 0.047847 | 0.834216 | 0.912196 | 0.190194 | 0.980402 | True | True |
| 2015 | hard_negative_weighted | 69138 | 1355 | 0.019888 | 1351 | 11363 | 4 | 56420 | 0.997048 | 0.106261 | 0.167638 | 0.893739 | 12714 | 0.829410 | 0.507691 | 0.013446 | 0.047811 | 0.835590 | 0.914705 | 0.192053 | 0.980402 | True | True |
| 2015 | uniform_negative_matched_weight | 69138 | 1355 | 0.018748 | 1346 | 11533 | 9 | 56250 | 0.993358 | 0.104511 | 0.170146 | 0.895489 | 12879 | 0.823212 | 0.496547 | 0.013538 | 0.047829 | 0.833059 | 0.911606 | 0.189125 | 0.980402 | True | True |
| 2016 | baseline_unweighted | 42987 | 181 | 0.030831 | 176 | 2289 | 5 | 40517 | 0.972376 | 0.071400 | 0.053474 | 0.928600 | 2465 | 0.918902 | 0.366443 | 0.003263 | 0.014523 | 0.946635 | 0.959451 | 0.133031 | 0.995789 | True | True |
| 2016 | hard_negative_weighted | 42987 | 181 | 0.035959 | 175 | 2114 | 6 | 40692 | 0.966851 | 0.076453 | 0.049386 | 0.923547 | 2289 | 0.917465 | 0.359998 | 0.003342 | 0.015167 | 0.950683 | 0.958733 | 0.141700 | 0.995789 | True | True |
| 2016 | uniform_negative_matched_weight | 42987 | 181 | 0.030137 | 176 | 2314 | 5 | 40492 | 0.972376 | 0.070683 | 0.054058 | 0.929317 | 2490 | 0.918318 | 0.346950 | 0.003294 | 0.014598 | 0.946053 | 0.959159 | 0.131786 | 0.995789 | True | True |
| 2017 | baseline_unweighted | 19529 | 253 | 0.012000 | 237 | 1287 | 16 | 17989 | 0.936759 | 0.155512 | 0.066767 | 0.844488 | 1524 | 0.869992 | 0.811694 | 0.004907 | 0.020488 | 0.933279 | 0.934996 | 0.266742 | 0.987045 | True | True |
| 2017 | hard_negative_weighted | 19529 | 253 | 0.012829 | 237 | 1348 | 16 | 17928 | 0.936759 | 0.149527 | 0.069932 | 0.850473 | 1585 | 0.866827 | 0.807564 | 0.004807 | 0.020118 | 0.930155 | 0.933414 | 0.257889 | 0.987045 | True | True |
| 2017 | uniform_negative_matched_weight | 19529 | 253 | 0.012192 | 237 | 1280 | 16 | 17996 | 0.936759 | 0.156229 | 0.066404 | 0.843771 | 1517 | 0.870355 | 0.814773 | 0.004883 | 0.020454 | 0.933637 | 0.935178 | 0.267797 | 0.987045 | True | True |
| 2018 | baseline_unweighted | 7799 | 0 | 0.004351 | 0 | 359 | 0 | 7440 | undefined | 0.000000 | 0.046032 | 1.000000 | 359 | undefined | undefined | 0.000012 | 0.000791 | 0.953968 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | hard_negative_weighted | 7799 | 0 | 0.004922 | 0 | 342 | 0 | 7457 | undefined | 0.000000 | 0.043852 | 1.000000 | 342 | undefined | undefined | 0.000013 | 0.000833 | 0.956148 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | uniform_negative_matched_weight | 7799 | 0 | 0.004456 | 0 | 352 | 0 | 7447 | undefined | 0.000000 | 0.045134 | 1.000000 | 352 | undefined | undefined | 0.000012 | 0.000798 | 0.954866 | undefined | 0.000000 | 1.000000 | True | False |
| 2022 | baseline_unweighted | 50756 | 421 | 0.008994 | 415 | 10072 | 6 | 40263 | 0.985748 | 0.039573 | 0.200099 | 0.960427 | 10487 | 0.785649 | 0.280023 | 0.007064 | 0.029196 | 0.801442 | 0.892824 | 0.076091 | 0.991705 | True | True |
| 2022 | hard_negative_weighted | 50756 | 421 | 0.009074 | 415 | 10150 | 6 | 40185 | 0.985748 | 0.039281 | 0.201649 | 0.960719 | 10565 | 0.784099 | 0.295986 | 0.006976 | 0.028844 | 0.799905 | 0.892050 | 0.075551 | 0.991705 | True | True |
| 2022 | uniform_negative_matched_weight | 50756 | 421 | 0.008743 | 415 | 10287 | 6 | 40048 | 0.985748 | 0.038778 | 0.204371 | 0.961222 | 10702 | 0.781378 | 0.281821 | 0.007059 | 0.029185 | 0.797206 | 0.890689 | 0.074620 | 0.991705 | True | True |
| 2023 | baseline_unweighted | 60366 | 781 | 0.018203 | 691 | 5992 | 90 | 53593 | 0.884763 | 0.103397 | 0.100562 | 0.896603 | 6683 | 0.784201 | 0.220619 | 0.011195 | 0.043996 | 0.899248 | 0.892100 | 0.185155 | 0.987062 | True | True |
| 2023 | hard_negative_weighted | 60366 | 781 | 0.016408 | 699 | 6479 | 82 | 53106 | 0.895006 | 0.097381 | 0.108735 | 0.902619 | 7178 | 0.786271 | 0.222139 | 0.011198 | 0.044134 | 0.891313 | 0.893135 | 0.175650 | 0.987062 | True | True |
| 2023 | uniform_negative_matched_weight | 60366 | 781 | 0.017537 | 694 | 6141 | 87 | 53444 | 0.888604 | 0.101536 | 0.103063 | 0.898464 | 6835 | 0.785542 | 0.220415 | 0.011195 | 0.043977 | 0.896829 | 0.892771 | 0.182248 | 0.987062 | True | True |

Precision measures true positive windows among alarms, recall the positive windows caught,
and accuracy all correct classifications. AP measures ranking; lower Brier/log loss is
better probabilistic scoring. The frozen gate requires higher precision and recall >=0.95
in every comparable positive evaluation year, AP no lower and Brier/log loss no higher
than baseline in each year. To attribute benefit to targeted mining, precision must also
beat the matched uniform control in those years. Gate success alone would not trigger
automatic deployment; failure retains the existing model.

## Paired conditional uncertainty

| year | control | metric | lower | upper | valid_draws |
| --- | --- | --- | --- | --- | --- |
| 2014 | baseline_unweighted | precision | 0.002408 | 0.007154 | 1000 |
| 2014 | baseline_unweighted | recall | -0.013678 | -0.000691 | 1000 |
| 2014 | baseline_unweighted | fp | -764.000000 | -434.975000 | 1000 |
| 2014 | uniform_negative_matched_weight | precision | 0.005029 | 0.012299 | 1000 |
| 2014 | uniform_negative_matched_weight | recall | -0.019066 | -0.001842 | 1000 |
| 2014 | uniform_negative_matched_weight | fp | -1345.025000 | -852.950000 | 1000 |
| 2015 | baseline_unweighted | precision | 0.000179 | 0.002295 | 1000 |
| 2015 | baseline_unweighted | recall | 0.000000 | 0.014995 | 1000 |
| 2015 | baseline_unweighted | fp | -178.000000 | -5.000000 | 1000 |
| 2015 | uniform_negative_matched_weight | precision | 0.000783 | 0.002977 | 1000 |
| 2015 | uniform_negative_matched_weight | recall | 0.000000 | 0.014995 | 1000 |
| 2015 | uniform_negative_matched_weight | fp | -253.025000 | -92.975000 | 1000 |
| 2016 | baseline_unweighted | precision | -0.000052 | 0.010993 | 1000 |
| 2016 | baseline_unweighted | recall | -0.045455 | 0.000000 | 973 |
| 2016 | baseline_unweighted | fp | -397.075000 | -10.000000 | 1000 |
| 2016 | uniform_negative_matched_weight | precision | 0.000000 | 0.011565 | 1000 |
| 2016 | uniform_negative_matched_weight | recall | -0.045455 | 0.000000 | 973 |
| 2016 | uniform_negative_matched_weight | fp | -420.050000 | -41.000000 | 1000 |
| 2017 | baseline_unweighted | precision | -0.021850 | 0.000000 | 1000 |
| 2017 | baseline_unweighted | recall | 0.000000 | 0.000000 | 949 |
| 2017 | baseline_unweighted | fp | 19.000000 | 110.025000 | 1000 |
| 2017 | uniform_negative_matched_weight | precision | -0.023925 | 0.000000 | 1000 |
| 2017 | uniform_negative_matched_weight | recall | 0.000000 | 0.000000 | 949 |
| 2017 | uniform_negative_matched_weight | fp | 22.975000 | 123.000000 | 1000 |
| 2018 | baseline_unweighted | precision | 0.000000 | 0.000000 | 1000 |
| 2018 | baseline_unweighted | recall | undefined | undefined | 0 |
| 2018 | baseline_unweighted | fp | -35.000000 | -3.000000 | 1000 |
| 2018 | uniform_negative_matched_weight | precision | 0.000000 | 0.000000 | 1000 |
| 2018 | uniform_negative_matched_weight | recall | undefined | undefined | 0 |
| 2018 | uniform_negative_matched_weight | fp | -20.000000 | -2.000000 | 1000 |
| 2022 | baseline_unweighted | precision | -0.000591 | -0.000078 | 1000 |
| 2022 | baseline_unweighted | recall | 0.000000 | 0.000000 | 1000 |
| 2022 | baseline_unweighted | fp | 26.975000 | 135.000000 | 1000 |
| 2022 | uniform_negative_matched_weight | precision | 0.000232 | 0.000916 | 1000 |
| 2022 | uniform_negative_matched_weight | recall | 0.000000 | 0.000000 | 1000 |
| 2022 | uniform_negative_matched_weight | fp | -197.000000 | -88.975000 | 1000 |
| 2023 | baseline_unweighted | precision | -0.008899 | -0.003330 | 1000 |
| 2023 | baseline_unweighted | recall | 0.002820 | 0.020027 | 1000 |
| 2023 | baseline_unweighted | fp | 334.000000 | 658.050000 | 1000 |
| 2023 | uniform_negative_matched_weight | precision | -0.006306 | -0.002403 | 1000 |
| 2023 | uniform_negative_matched_weight | recall | 0.001700 | 0.012065 | 1000 |
| 2023 | uniform_negative_matched_weight | fp | 220.000000 | 475.025000 | 1000 |

Each interval is candidate minus the named control, using 1000 paired whole-HARP bootstrap
draws with seed 24 within a year. Both arms use the same sampled regions and fixed models
and thresholds. Training, calibration and model-selection uncertainty are omitted. FP
intervals concern resampled window counts; recall draws are undefined in a zero-positive
year. Intervals spanning zero do not establish a directional difference at that interval
level. Adjacent years share historical training data and are not independent replications.

## Interpretation limits and next decision

This is an adaptive development experiment: prior annual errors motivated the design.
The test years were not fresh, even though no evaluation rows were used for fitting.
Hard-negative weighting can suppress true positives or distort calibration as well as
reduce false alarms. A negative result rejects this particular weighting recipe, not
every possible method of learning from difficult negatives. Inspect the year-by-year
and uniform-control comparisons before choosing another hypothesis. Any next experiment
needs a new frozen protocol; do not change thresholds on these years to manufacture a
95% recall claim. No further candidate search or live deployment is claimed here.

## Reproduction and evidence

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_hard_negative_years.py \
  --protocol config/hard-negative-v2.json --output artifacts/hard_negative_years_20261029_r1
.venv/bin/python scripts/report_hard_negative_years.py --source artifacts/hard_negative_years_20261029_r1 --report-name hard-negative-years-20261029
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_hard-negative-years-20261029
```

Choose fresh output directories and report names for reruns. Preserve frozen models,
protocols and predictions. Review both editions and register their source hash and links
in `docs/reports.json` and `docs/reports.md` before publishing. Generated models, mined
training windows, predictions and HTML remain local ignored artifacts. Model, threshold,
prediction and code hashes are recorded in the experiment report.

| source | SHA-256 |
| --- | --- |
| artifacts/hard_negative_years_20261029_r1/report.json | 6356159d08b2c406bc76bc7fdce81680664ec8c4d41683ca8422ea7291439f8f |
| artifacts/hard_negative_years_20261029_r1/metrics.csv | a952c8d5854c923e74192200db539e5cb379e0db96167918a8ecc2c29f7441ca |

