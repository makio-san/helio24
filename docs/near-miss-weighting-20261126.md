# Near-miss training weights at the alert tier on the adopted pipeline (2026-11-26)

## Decision

Development basis: the relabelled table `artifacts/relabelled_development_20261111_r1` and the adopted pipeline
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)). The basis changed on 2026-11-12 because the frozen
labels covered under 30% of the mapped 2022 to 2023 M/X flares. Already inspected years: adaptive development evidence,
not an independent test.

Reading `N3_no_gain`, outcome label `result:no-gain`, by the rule frozen in
[`config/near-miss-weighting-v1.json`](../config/near-miss-weighting-v1.json) before any result. The protocol carries an
`acceptance_rule` (`decision.near_miss_w3_goal_met_and_beats_uniform >= 1`); Hale `interpret_result` on
`artifacts/near_miss_weighting_20261126_r1` returns `reject` with observed value 0. That decision is the outcome, and the
frozen reading agrees with it: no candidate meets the goal against the control, so `N2_reweighting_only` does not apply
either. Giving weight 3 to the near-miss negatives of flaring HARPs in training does not raise alert precision by the
frozen rule, and neither does the equal total reweighting of all training negatives.

- `near_miss_w3` meets the per-year primary acceptance in 2015 only (of six years), and so does `uniform_matched`.
  Neither meets `all_year_primary` or `cycle25_primary` (2022 and 2023).
- `near_miss_w3` beats `uniform_matched` in no year. Its alert precision is below `uniform_matched` in 2014, 2015, 2016,
  2017 and 2022; in 2023 it is higher (0.4510 against 0.4433), but it misses more positive runs (74 against 72 of 159)
  and its window recall is 0.0501 lower, above the tolerance of 0.02. The paired HARP-cluster bootstrap interval of the
  precision difference `near_miss_w3` minus `uniform_matched` contains 0 in every year.
- Alert precision against the control: higher in 2014, 2015 and 2023 for both candidates, lower in 2016, 2017 and 2022
  for both. In 2014 both miss more positive runs than the control (68 against 66 of 88) and lose more than 0.02 window
  recall (0.0369 and 0.0213).
- Cycle 25. In the 2022 fallback year alert precision is 0.4542 for `near_miss_w3` and 0.4718 for `uniform_matched`
  against 0.4727 for the control; `near_miss_w3` misses fewer positive runs (26 against 32 of 72) with 115 more
  false-positive windows (1293 against 1178). In 2023 precision is 0.4510 and 0.4433 against 0.4263, and the lower bound
  of the paired bootstrap interval is above 0 for both candidates ([0.0055, 0.0442] and [0.0065, 0.0297]), but both miss
  more positive runs than the control (74 and 72 against 68 of 159); the window recall of `near_miss_w3` falls by 0.0648,
  that of `uniform_matched` by 0.0147.
- Candidate thresholds move with the weighted scores. In 2017 the alert threshold of `near_miss_w3` is itself a fallback
  (prior-year precision 0.50 was not reachable; best prior-year precision 0.4839), and both candidates select much lower
  2017 alert thresholds than the control (0.2637 and 0.2961 against 0.4145): alert precision falls from 0.8676 to 0.6746
  and 0.6969 while one more of the 6 positive runs is alarmed. 2022 is an alert fallback year for the control and for
  both candidates.
- Secondary, reported and not judged: alert precision is at least 0.50 in 2014, 2015 and 2017 for the control and for
  both candidates. 2016, 2022 and 2023 stay below 0.50 for every candidate.
- Descriptive: the within-flaring-HARP AP of `near_miss_w3` is 0.4953 in 2022 and 0.4174 in 2023, against 0.4968 and
  0.4057 for the control and 0.4958 and 0.4108 for `uniform_matched`. The share of alert false-positive windows within
  72 hours of a positive window of the same HARP is 0.6497 in 2022 and 0.7651 in 2023 for `near_miss_w3`, against 0.7139
  and 0.7561 for the control. The ranking of hours inside flaring regions, which motivated the idea, is not visibly
  changed by the weights.

Consequence: on this evidence a training weight of 3 on near-miss negatives within 72 hours is not a route to higher
alert precision. No model is promoted and no alert, threshold, operating point or dashboard setting is changed. The run
used 24 constituent fits, the budget of the protocol, and downloaded nothing. The reserved 2024 to 2025 test was not
accessed.

## Why this was tried

Idea issue #3. The [relabelled cycle-25 diagnostic](cycle25-diagnostic-relabelled-20261112.md) found region AP 0.8315 and
0.8655 against within-flaring-HARP AP 0.4968 and 0.4057 in 2022 and 2023, and that 0.7139 and 0.7561 of the alert
false-positive windows lie within 72 hours of a positive window of the same HARP: the alert tier finds the region and
ranks the hours inside it poorly. Extra flare-history features did not change this
([SGAS flare history](activity-history-relabelled-20261112.md), reading `R3_no_gain`). The earlier weighting experiment
([hard-negative training](hard-negative-years-20261029.md)) used teacher-mined hard negatives on the frozen-label basis
with a recall 0.95 gate, retrained only XGBoost, and neither defined its negatives by near-miss membership nor judged the
alert tier. Weighting the near-miss negatives asks the unchanged recipes to separate the flare day from the
neighbouring days; no feature, model or tier rule changes.

## What was run

One execution of the protocol exactly as merged, from `main` commit `da5fae0`: 2 candidates, 6 years, 2 constituents,
24 constituent fits, no hyperparameter search, 0 downloads. Wall time 237 seconds.

```sh
OMP_NUM_THREADS=3 python -m scripts.audit_near_miss_weighting --config config/near-miss-weighting-v1.json --output artifacts/near_miss_weighting_20261126_r1
```

| item | sha256 |
| --- | --- |
| `config/near-miss-weighting-v1.json` | `7831b49802bb4ff7e9aa99def23582ade1bf25a758eb5fb1caed1450a1dafaed` |
| `artifacts/walk_forward_v2_20261112_r1/report.json` (control) | `c2b326d90253e824e9dd324158933e01c1216788653b1d284bf22850f67f76f1` |
| `artifacts/relabelled_development_20261111_r1/report.json` (labels) | `2847215ce5a5dedb9ebb93d7fa0ba1bcb7b4a7bf9fdcd80bab95e63726b9ac43` |
| `config/walk-forward-v2.json` (pipeline protocol) | `d6e08a575193162afe59e068c568b51dee5e34c3950dcb5b6ed98b817e63d3bb` |
| `config/walk-forward-v1.json` (base recipes) | `7c48fd7381456bee22f928b44da537880f06b4d70fd2b38b822279474c616303` |
| `artifacts/near_miss_weighting_20261126_r1/phase1.json` | `1e89be264456db4d4e3322a0f1ebba91ac208b3555accbc92fdb0009de35489c` |
| `artifacts/near_miss_weighting_20261126_r1/thresholds.json` | `24d0fb16dc6122a477ae36ee9b39e8dd923cd8309618e44f225973c1fa320240` |
| `artifacts/near_miss_weighting_20261126_r1/weights.csv` | `cc6c78fc91ca39ba370912dfb8f73905301c200cb5f11790bf44469a72b1ffa1` |
| `artifacts/near_miss_weighting_20261126_r1/results.csv` | `6867d877aa1879019cab96ace67dccddcfb321bea10eac7f88acffd09a7fcb7c` |
| `artifacts/near_miss_weighting_20261126_r1/intervals.csv` | `5177bfc62075c986ba9167eeee7cc88c2e9882e9eff40ab93a0cb630b4d3bccb` |
| `artifacts/near_miss_weighting_20261126_r1/report.json` | `03ffa9b2bc525fb3cf55855c71b0c9c60f6f41c5a50fd9667a4ea825f52dc5c4` |

Before the run every input named by the protocol was checked against its sha256: the table report, the control report,
both pipeline protocols, and the per-year `predictions.parquet` and `thresholds.json` of the control against
`artifact_hashes` of its report. `models.joblib` was never opened. The runner recomputed the training population and the
near-miss membership of every fold and found them equal to the protocol. Thresholds, weights and candidate probabilities
were written and hashed (`phase1.json`) before any evaluation label was read, and still had the recorded hashes after
the evaluation. The target stored beside the control probabilities equals the table label for every evaluation window.

## Method

Population: the evaluation windows of the adopted pipeline, one per HARP and hour, for 2014, 2015, 2016, 2017, 2022 and
2023. 2018 to 2021 are skipped by the adopted pipeline and stay out. 2022 is an alert fallback year of the control: its
stored alert threshold comes from the fallback rule of `config/walk-forward-v2.json`. The fallback flag of each
candidate's own alert threshold is given in every table.

Candidates. `control`: the stored ensemble probabilities and the stored per-year watch and alert thresholds of
`artifacts/walk_forward_v2_20261112_r1`, not refitted. `near_miss_w3`: a refit of the unchanged `walk-forward-v1` recipes
on the 96 SHARP summaries in which every negative training window that has a positive training window of the same HARP
within 72 hours before or after gets sample weight 3 and every other training row weight 1. `uniform_matched`: the same
refit in which every training negative gets weight `1 + 2 * near_miss_negatives / train_negatives` of its fold and
positives weight 1, so the total negative weight equals that of `near_miss_w3` and only the placement of the extra weight
differs. This is the weight control.

Near-miss membership uses rows and labels of the training role only, after `helio24.walk_forward.annual_fold` purged
boundary windows. The weight is passed to the final estimator of each constituent (logistic regression and XGBoost);
imputer, scaler, sigmoid calibration on the prior year, threshold selection and every measure are unweighted. The
ensemble is 0.45 logistic and 0.55 XGBoost. Per candidate and year the watch threshold (prior-year window recall 0.90)
and the alert threshold (prior-year precision 0.50, recall floor 0.10, fallback flag) are selected on calibration-year
probabilities, so each candidate is judged at its own prior-year thresholds.

Acceptance, identical to [`config/activity-history-v2.json`](../config/activity-history-v2.json): a candidate meets the
per-year primary acceptance when its alert precision is higher than the control, its missed positive runs are not above
the control and its window recall drops by at most 0.02. `all_year_primary`: this holds in all six years.
`cycle25_primary`: it holds in both 2022 and 2023. A candidate meets the goal against the control when
`all_year_primary` holds, or when `cycle25_primary` holds and the lower bound of the paired HARP-cluster bootstrap
interval of the precision difference (1000 draws, seed 24, 2.5 and 97.5 percent quantiles) is above 0 in both 2022 and
2023. In a year `near_miss_w3` beats `uniform_matched` when the per-year primary acceptance holds with `uniform_matched`
in the place of the control.

Reading rule, applied in this order: `N1_near_miss_helps` if `near_miss_w3` meets the goal against the control by a path
and beats `uniform_matched` in every year of that path; otherwise `N2_reweighting_only` if `near_miss_w3` or
`uniform_matched` meets the goal against the control; otherwise `N3_no_gain`.

Counts are overlapping hourly windows. A positive run is a contiguous group of positive windows of one HARP. Neither is
an independent event.

## Training weights

Label counts of the training role only. The near-miss share is `near_miss_negatives / train_negatives`. Calibration and
evaluation rows always have weight 1.0.

| year | training rows | training positives | training negatives | near-miss negatives | near-miss share of negatives | flaring training HARPs | near-miss weight | uniform negative weight | total negative weight `near_miss_w3` | total negative weight `uniform_matched` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 150935 | 3161 | 147774 | 7344 | 0.0497 | 60 | 3.0 | 1.099395 | 162462.0 | 162462.0 |
| 2015 | 228635 | 4616 | 224019 | 11185 | 0.0499 | 93 | 3.0 | 1.099858 | 246389.0 | 246389.0 |
| 2016 | 307980 | 7129 | 300851 | 16421 | 0.0546 | 138 | 3.0 | 1.109164 | 333693.0 | 333693.0 |
| 2017 | 379962 | 8638 | 371324 | 19634 | 0.0529 | 167 | 3.0 | 1.105751 | 410592.0 | 410592.0 |
| 2022 | 466206 | 9141 | 457065 | 20530 | 0.0449 | 174 | 3.0 | 1.089834 | 498125.0 | 498125.0 |
| 2023 | 496391 | 9518 | 486873 | 21974 | 0.0451 | 186 | 3.0 | 1.090266 | 530821.0 | 530821.0 |

## Alert tier

Precision is given with the delivered window recall and the missed positive runs. Intervals are HARP-cluster bootstrap
intervals of each candidate. `fallback` marks an alert threshold selected by the fallback rule.

| year | candidate | fallback | alert threshold | TP | FP | FN | TN | recall | recall 95% interval | precision | precision 95% interval | accuracy | always-negative accuracy | alarm windows | alarmed positive runs | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 0.4627 | 688 | 320 | 1748 | 75595 | 0.2824 | [0.1030, 0.4369] | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 1008 | 22 | 66/88 |
| 2014 | `near_miss_w3` | no | 0.4460 | 598 | 236 | 1838 | 75679 | 0.2455 | [0.0761, 0.3923] | 0.7170 | [0.4360, 0.8674] | 0.9735 | 0.9689 | 834 | 20 | 68/88 |
| 2014 | `uniform_matched` | no | 0.4924 | 636 | 232 | 1800 | 75683 | 0.2611 | [0.0804, 0.4205] | 0.7327 | [0.4716, 0.8709] | 0.9741 | 0.9689 | 868 | 20 | 68/88 |
| 2015 | `control` | no | 0.2631 | 545 | 457 | 916 | 68636 | 0.3730 | [0.1693, 0.5283] | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 1002 | 30 | 27/57 |
| 2015 | `near_miss_w3` | no | 0.2601 | 582 | 455 | 879 | 68638 | 0.3984 | [0.2216, 0.5403] | 0.5612 | [0.3702, 0.7208] | 0.9811 | 0.9793 | 1037 | 30 | 27/57 |
| 2015 | `uniform_matched` | no | 0.2611 | 562 | 435 | 899 | 68658 | 0.3847 | [0.1758, 0.5377] | 0.5637 | [0.3464, 0.7397] | 0.9811 | 0.9793 | 997 | 31 | 26/57 |
| 2016 | `control` | no | 0.2564 | 94 | 109 | 120 | 42819 | 0.4393 | [0.0000, 0.8506] | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 203 | 5 | 3/8 |
| 2016 | `near_miss_w3` | no | 0.2419 | 91 | 142 | 123 | 42786 | 0.4252 | [0.0000, 0.7471] | 0.3906 | [0.0000, 0.5652] | 0.9939 | 0.9950 | 233 | 6 | 2/8 |
| 2016 | `uniform_matched` | no | 0.2574 | 88 | 115 | 126 | 42813 | 0.4112 | [0.0000, 0.8391] | 0.4335 | [0.0000, 0.5691] | 0.9944 | 0.9950 | 203 | 5 | 3/8 |
| 2017 | `control` | no | 0.4145 | 177 | 27 | 88 | 19551 | 0.6679 | [0.0000, 0.8535] | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 204 | 3 | 3/6 |
| 2017 | `near_miss_w3` | yes | 0.2637 | 199 | 96 | 66 | 19482 | 0.7509 | [0.1860, 0.9172] | 0.6746 | [0.0000, 0.9028] | 0.9918 | 0.9866 | 295 | 4 | 2/6 |
| 2017 | `uniform_matched` | no | 0.2961 | 200 | 87 | 65 | 19491 | 0.7547 | [0.1860, 0.9363] | 0.6969 | [0.0000, 0.9143] | 0.9923 | 0.9866 | 287 | 4 | 2/6 |
| 2022 | `control` | yes | 0.1570 | 1056 | 1178 | 1134 | 62225 | 0.4822 | [0.3268, 0.6058] | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 2234 | 40 | 32/72 |
| 2022 | `near_miss_w3` | yes | 0.1401 | 1076 | 1293 | 1114 | 62110 | 0.4913 | [0.3570, 0.6030] | 0.4542 | [0.3329, 0.5854] | 0.9633 | 0.9666 | 2369 | 46 | 26/72 |
| 2022 | `uniform_matched` | yes | 0.1549 | 1056 | 1182 | 1134 | 62221 | 0.4822 | [0.3291, 0.6038] | 0.4718 | [0.3492, 0.6014] | 0.9647 | 0.9666 | 2238 | 40 | 32/72 |
| 2023 | `control` | no | 0.2689 | 1587 | 2136 | 2504 | 90764 | 0.3879 | [0.2918, 0.4663] | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 3723 | 91 | 68/159 |
| 2023 | `near_miss_w3` | no | 0.2935 | 1322 | 1609 | 2769 | 91291 | 0.3231 | [0.2387, 0.3955] | 0.4510 | [0.3708, 0.5383] | 0.9549 | 0.9578 | 2931 | 85 | 74/159 |
| 2023 | `uniform_matched` | no | 0.2777 | 1527 | 1918 | 2564 | 90982 | 0.3733 | [0.2782, 0.4510] | 0.4433 | [0.3656, 0.5280] | 0.9538 | 0.9578 | 3445 | 87 | 72/159 |

## Acceptance

`precision difference` is candidate minus control. `recall drop` is control recall minus candidate recall; a negative
value is a gain. The interval is the paired HARP-cluster bootstrap interval of the precision difference. In 2017 982 of
the 1000 draws could be used against the control (a draw without any alert window of the control or of the candidate is
skipped).

| year | candidate | control fallback | candidate fallback | control precision | candidate precision | precision difference | difference 95% interval | bootstrap draws used | recall drop | missed runs control | missed runs candidate | precision higher | missed runs not above | recall drop at most 0.02 | per-year primary met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `near_miss_w3` | no | no | 0.6825 | 0.7170 | 0.0345 | [-0.0215, 0.0701] | 1000 | 0.0369 | 66 | 68 | yes | no | no | no |
| 2014 | `uniform_matched` | no | no | 0.6825 | 0.7327 | 0.0502 | [0.0134, 0.0813] | 1000 | 0.0213 | 66 | 68 | yes | no | no | no |
| 2015 | `near_miss_w3` | no | no | 0.5439 | 0.5612 | 0.0173 | [-0.0244, 0.0726] | 1000 | -0.0253 | 27 | 27 | yes | yes | yes | yes |
| 2015 | `uniform_matched` | no | no | 0.5439 | 0.5637 | 0.0198 | [0.0022, 0.0413] | 1000 | -0.0116 | 27 | 26 | yes | yes | yes | yes |
| 2016 | `near_miss_w3` | no | no | 0.4631 | 0.3906 | -0.0725 | [-0.1491, 0.0000] | 1000 | 0.0140 | 3 | 2 | no | yes | yes | no |
| 2016 | `uniform_matched` | no | no | 0.4631 | 0.4335 | -0.0296 | [-0.1273, 0.0000] | 1000 | 0.0280 | 3 | 3 | no | yes | no | no |
| 2017 | `near_miss_w3` | no | yes | 0.8676 | 0.6746 | -0.1931 | [-0.3577, 0.1328] | 982 | -0.0830 | 3 | 2 | no | yes | yes | no |
| 2017 | `uniform_matched` | no | no | 0.8676 | 0.6969 | -0.1708 | [-0.3319, 0.1599] | 982 | -0.0868 | 3 | 2 | no | yes | yes | no |
| 2022 | `near_miss_w3` | yes | yes | 0.4727 | 0.4542 | -0.0185 | [-0.0416, 0.0021] | 1000 | -0.0091 | 32 | 26 | no | yes | yes | no |
| 2022 | `uniform_matched` | yes | yes | 0.4727 | 0.4718 | -0.0008 | [-0.0090, 0.0054] | 1000 | 0.0000 | 32 | 32 | no | yes | yes | no |
| 2023 | `near_miss_w3` | no | no | 0.4263 | 0.4510 | 0.0248 | [0.0055, 0.0442] | 1000 | 0.0648 | 68 | 74 | yes | no | no | no |
| 2023 | `uniform_matched` | no | no | 0.4263 | 0.4433 | 0.0170 | [0.0065, 0.0297] | 1000 | 0.0147 | 68 | 72 | yes | no | yes | no |

`near_miss_w3` against `uniform_matched`, the same three conditions with `uniform_matched` in the place of the control.
The interval is descriptive.

| year | `uniform_matched` fallback | `near_miss_w3` fallback | `uniform_matched` precision | `near_miss_w3` precision | precision difference | difference 95% interval | bootstrap draws used | recall drop | missed runs `uniform_matched` | missed runs `near_miss_w3` | precision higher | missed runs not above | recall drop at most 0.02 | beats `uniform_matched` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | no | no | 0.7327 | 0.7170 | -0.0157 | [-0.0624, 0.0201] | 1000 | 0.0156 | 68 | 68 | no | yes | yes | no |
| 2015 | no | no | 0.5637 | 0.5612 | -0.0025 | [-0.0485, 0.0522] | 1000 | -0.0137 | 26 | 27 | no | no | yes | no |
| 2016 | no | no | 0.4335 | 0.3906 | -0.0429 | [-0.0861, 0.0554] | 1000 | -0.0140 | 3 | 2 | no | yes | yes | no |
| 2017 | no | yes | 0.6969 | 0.6746 | -0.0223 | [-0.0642, 0.0189] | 1000 | 0.0038 | 2 | 2 | no | yes | yes | no |
| 2022 | yes | yes | 0.4718 | 0.4542 | -0.0176 | [-0.0394, 0.0022] | 1000 | -0.0091 | 32 | 26 | no | yes | yes | no |
| 2023 | no | no | 0.4433 | 0.4510 | 0.0078 | [-0.0102, 0.0244] | 1000 | 0.0501 | 72 | 74 | yes | no | no | no |

| candidate | years meeting per-year primary | all_year_primary | cycle25_primary | bootstrap lower bound above 0 in 2022 and 2023 | goal met against control | years beating `uniform_matched` | alert fallback years | years with alert precision at least 0.50 (secondary) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `control` |  |  |  |  |  |  | 2022 | 2014, 2015, 2017 |
| `near_miss_w3` | 2015 | no | no | no | no | none | 2017, 2022 | 2014, 2015, 2017 |
| `uniform_matched` | 2015 | no | no | no | no |  | 2022 | 2014, 2015, 2017 |

## Ranking and origin of alert false positives (descriptive)

Reported, not judged. Average precision, region AP and within-flaring-HARP AP do not depend on a threshold. The
false-positive shares are taken at each candidate's own alert threshold. `precision at control recall` is the
candidate's precision at the evaluation-year threshold that delivers the control's alert recall: an oracle-matched
description that uses evaluation labels and is never deployable.

| year | candidate | fallback | average precision | region AP | within-flaring-HARP AP | alert FP windows | alert FP share from never-flaring HARPs | alert FP share within 72 h of a positive window | control alert recall | precision at control recall (oracle) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 0.5015 | 0.7600 | 0.5528 | 320 | 0.1437 | 0.7063 | 0.2824 | 0.6825 |
| 2014 | `near_miss_w3` | no | 0.4857 | 0.7446 | 0.5400 | 236 | 0.1525 | 0.7288 | 0.2824 | 0.6546 |
| 2014 | `uniform_matched` | no | 0.5026 | 0.7625 | 0.5536 | 232 | 0.1336 | 0.7241 | 0.2824 | 0.7006 |
| 2015 | `control` | no | 0.4823 | 0.8264 | 0.5331 | 457 | 0.0853 | 0.8249 | 0.3730 | 0.5439 |
| 2015 | `near_miss_w3` | no | 0.4798 | 0.8173 | 0.5336 | 455 | 0.0813 | 0.8286 | 0.3730 | 0.5761 |
| 2015 | `uniform_matched` | no | 0.4881 | 0.8161 | 0.5381 | 435 | 0.0759 | 0.8138 | 0.3730 | 0.5731 |
| 2016 | `control` | no | 0.4060 | 0.6333 | 0.4853 | 109 | 0.2569 | 0.5688 | 0.4393 | 0.4631 |
| 2016 | `near_miss_w3` | no | 0.3346 | 0.8125 | 0.4330 | 142 | 0.3451 | 0.4859 | 0.4393 | 0.3917 |
| 2016 | `uniform_matched` | no | 0.4114 | 0.8125 | 0.4952 | 115 | 0.2783 | 0.5478 | 0.4393 | 0.4434 |
| 2017 | `control` | no | 0.7975 | 1.0000 | 0.8727 | 27 | 0.1111 | 0.8889 | 0.6679 | 0.8676 |
| 2017 | `near_miss_w3` | yes | 0.7968 | 1.0000 | 0.8784 | 96 | 0.6146 | 0.3750 | 0.6679 | 0.8592 |
| 2017 | `uniform_matched` | no | 0.8031 | 1.0000 | 0.8770 | 87 | 0.5632 | 0.4253 | 0.6679 | 0.8762 |
| 2022 | `control` | yes | 0.4622 | 0.8315 | 0.4968 | 1178 | 0.0823 | 0.7139 | 0.4822 | 0.4727 |
| 2022 | `near_miss_w3` | yes | 0.4554 | 0.8262 | 0.4953 | 1293 | 0.1284 | 0.6497 | 0.4822 | 0.4716 |
| 2022 | `uniform_matched` | yes | 0.4611 | 0.8297 | 0.4958 | 1182 | 0.0854 | 0.7090 | 0.4822 | 0.4718 |
| 2023 | `control` | no | 0.3626 | 0.8655 | 0.4057 | 2136 | 0.1320 | 0.7561 | 0.3879 | 0.4263 |
| 2023 | `near_miss_w3` | no | 0.3694 | 0.8557 | 0.4174 | 1609 | 0.1374 | 0.7651 | 0.3879 | 0.4267 |
| 2023 | `uniform_matched` | no | 0.3670 | 0.8634 | 0.4108 | 1918 | 0.1330 | 0.7633 | 0.3879 | 0.4357 |

## Watch tier

Each candidate at its own prior-year watch threshold (window recall 0.90 on the prior year). No watch threshold is a
fallback.

| year | candidate | fallback | watch threshold | TP | FP | FN | TN | recall | recall 95% interval | precision | precision 95% interval | accuracy | always-negative accuracy | alarm windows | alarmed positive runs | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 0.0311 | 2146 | 9020 | 290 | 66895 | 0.8810 | [0.8065, 0.9357] | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 11166 | 82 | 6/88 |
| 2014 | `near_miss_w3` | no | 0.0306 | 2185 | 9716 | 251 | 66199 | 0.8970 | [0.8286, 0.9452] | 0.1836 | [0.1260, 0.2481] | 0.8728 | 0.9689 | 11901 | 82 | 6/88 |
| 2014 | `uniform_matched` | no | 0.0302 | 2148 | 9198 | 288 | 66717 | 0.8818 | [0.8055, 0.9348] | 0.1893 | [0.1295, 0.2561] | 0.8789 | 0.9689 | 11346 | 82 | 6/88 |
| 2015 | `control` | no | 0.0364 | 1396 | 8079 | 65 | 61014 | 0.9555 | [0.8917, 0.9971] | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 9475 | 56 | 1/57 |
| 2015 | `near_miss_w3` | no | 0.0375 | 1399 | 8441 | 62 | 60652 | 0.9576 | [0.8947, 0.9971] | 0.1422 | [0.0868, 0.1990] | 0.8795 | 0.9793 | 9840 | 56 | 1/57 |
| 2015 | `uniform_matched` | no | 0.0343 | 1399 | 8550 | 62 | 60543 | 0.9576 | [0.8947, 0.9971] | 0.1406 | [0.0859, 0.1973] | 0.8779 | 0.9793 | 9949 | 56 | 1/57 |
| 2016 | `control` | no | 0.0471 | 201 | 1722 | 13 | 41206 | 0.9393 | [0.4545, 1.0000] | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 1923 | 8 | 0/8 |
| 2016 | `near_miss_w3` | no | 0.0507 | 205 | 1814 | 9 | 41114 | 0.9579 | [0.7727, 1.0000] | 0.1015 | [0.0000, 0.1849] | 0.9577 | 0.9950 | 2019 | 8 | 0/8 |
| 2016 | `uniform_matched` | no | 0.0478 | 200 | 1697 | 14 | 41231 | 0.9346 | [0.4545, 1.0000] | 0.1054 | [0.0000, 0.1928] | 0.9603 | 0.9950 | 1897 | 8 | 0/8 |
| 2017 | `control` | no | 0.0270 | 243 | 1058 | 22 | 18520 | 0.9170 | [0.7692, 1.0000] | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1301 | 5 | 1/6 |
| 2017 | `near_miss_w3` | no | 0.0277 | 243 | 1069 | 22 | 18509 | 0.9170 | [0.7692, 1.0000] | 0.1852 | [0.0000, 0.4544] | 0.9450 | 0.9866 | 1312 | 5 | 1/6 |
| 2017 | `uniform_matched` | no | 0.0255 | 242 | 1067 | 23 | 18511 | 0.9132 | [0.7692, 1.0000] | 0.1849 | [0.0000, 0.4533] | 0.9451 | 0.9866 | 1309 | 5 | 1/6 |
| 2022 | `control` | no | 0.0183 | 2024 | 11917 | 166 | 51486 | 0.9242 | [0.8502, 0.9731] | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 13941 | 67 | 5/72 |
| 2022 | `near_miss_w3` | no | 0.0197 | 2016 | 11867 | 174 | 51536 | 0.9205 | [0.8444, 0.9705] | 0.1452 | [0.1006, 0.1967] | 0.8164 | 0.9666 | 13883 | 67 | 5/72 |
| 2022 | `uniform_matched` | no | 0.0189 | 2021 | 11609 | 169 | 51794 | 0.9228 | [0.8475, 0.9727] | 0.1483 | [0.1031, 0.2011] | 0.8204 | 0.9666 | 13630 | 66 | 6/72 |
| 2023 | `control` | no | 0.0405 | 3695 | 16022 | 396 | 76878 | 0.9032 | [0.8486, 0.9425] | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 19717 | 149 | 10/159 |
| 2023 | `near_miss_w3` | no | 0.0447 | 3691 | 15804 | 400 | 77096 | 0.9022 | [0.8479, 0.9412] | 0.1893 | [0.1531, 0.2254] | 0.8329 | 0.9578 | 19495 | 151 | 8/159 |
| 2023 | `uniform_matched` | no | 0.0410 | 3705 | 16111 | 386 | 76789 | 0.9056 | [0.8503, 0.9449] | 0.1870 | [0.1511, 0.2226] | 0.8299 | 0.9578 | 19816 | 149 | 10/159 |

Watch-tier accuracy is below the always-negative accuracy for every candidate in every year.

## Selected thresholds

Selected on calibration-year probabilities before any evaluation label was read. `prior-year recall` and
`prior-year precision` are the calibration-year values at the selected threshold.

| year | candidate | tier | threshold | prior-year recall | prior-year precision | fallback |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | `watch` | 0.0311 |  |  | no |
| 2014 | `control` | `alert` | 0.4627 | 0.1326 | 0.5000 | no |
| 2014 | `near_miss_w3` | `watch` | 0.0306 |  |  | no |
| 2014 | `near_miss_w3` | `alert` | 0.4460 | 0.1230 | 0.5000 | no |
| 2014 | `uniform_matched` | `watch` | 0.0302 |  |  | no |
| 2014 | `uniform_matched` | `alert` | 0.4924 | 0.1038 | 0.5000 | no |
| 2015 | `control` | `watch` | 0.0364 |  |  | no |
| 2015 | `control` | `alert` | 0.2631 | 0.4906 | 0.5000 | no |
| 2015 | `near_miss_w3` | `watch` | 0.0375 |  |  | no |
| 2015 | `near_miss_w3` | `alert` | 0.2601 | 0.4462 | 0.5000 | no |
| 2015 | `uniform_matched` | `watch` | 0.0343 |  |  | no |
| 2015 | `uniform_matched` | `alert` | 0.2611 | 0.4881 | 0.5000 | no |
| 2016 | `control` | `watch` | 0.0471 |  |  | no |
| 2016 | `control` | `alert` | 0.2564 | 0.4969 | 0.5000 | no |
| 2016 | `near_miss_w3` | `watch` | 0.0507 |  |  | no |
| 2016 | `near_miss_w3` | `alert` | 0.2419 | 0.5079 | 0.5000 | no |
| 2016 | `uniform_matched` | `watch` | 0.0478 |  |  | no |
| 2016 | `uniform_matched` | `alert` | 0.2574 | 0.4949 | 0.5000 | no |
| 2017 | `control` | `watch` | 0.0270 |  |  | no |
| 2017 | `control` | `alert` | 0.4145 | 0.2196 | 0.5000 | no |
| 2017 | `near_miss_w3` | `watch` | 0.0277 |  |  | no |
| 2017 | `near_miss_w3` | `alert` | 0.2637 | 0.3505 | 0.4839 | yes |
| 2017 | `uniform_matched` | `watch` | 0.0255 |  |  | no |
| 2017 | `uniform_matched` | `alert` | 0.2961 | 0.3598 | 0.5000 | no |
| 2022 | `control` | `watch` | 0.0183 |  |  | no |
| 2022 | `control` | `alert` | 0.1570 | 0.2361 | 0.1996 | yes |
| 2022 | `near_miss_w3` | `watch` | 0.0197 |  |  | no |
| 2022 | `near_miss_w3` | `alert` | 0.1401 | 0.2812 | 0.2070 | yes |
| 2022 | `uniform_matched` | `watch` | 0.0189 |  |  | no |
| 2022 | `uniform_matched` | `alert` | 0.1549 | 0.2493 | 0.2026 | yes |
| 2023 | `control` | `watch` | 0.0405 |  |  | no |
| 2023 | `control` | `alert` | 0.2689 | 0.4461 | 0.5000 | no |
| 2023 | `near_miss_w3` | `watch` | 0.0447 |  |  | no |
| 2023 | `near_miss_w3` | `alert` | 0.2935 | 0.3753 | 0.5000 | no |
| 2023 | `uniform_matched` | `watch` | 0.0410 |  |  | no |
| 2023 | `uniform_matched` | `alert` | 0.2777 | 0.4183 | 0.5000 | no |

## Frozen-label results

Kept visible for comparison, copied from [hard-negative training](hard-negative-years-20261029.md) and not recomputed:
teacher-mined hard negatives with weight 3 on frozen labels, thresholds at prior-year recall 0.95, XGBoost retrained
only. It is a different basis, a different definition of the weighted negatives and a different tier; the values are
never pooled with the tables above and are not comparable with them. That report found recall at least 0.95 in 3 of 6
comparable positive evaluation years for the weighted arm and an all-year gate result of `False`.

| year | arm | windows | positives | precision | recall | FP | FN | threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `baseline_unweighted` | 75228 | 2310 | 0.135905 | 0.945455 | 13886 | 126 | 0.011475 |
| 2014 | `hard_negative_weighted` | 75228 | 2310 | 0.140464 | 0.940260 | 13291 | 138 | 0.011643 |
| 2014 | `uniform_negative_matched_weight` | 75228 | 2310 | 0.132063 | 0.948052 | 14393 | 120 | 0.010818 |
| 2015 | `baseline_unweighted` | 69138 | 1355 | 0.105164 | 0.993358 | 11453 | 9 | 0.018839 |
| 2015 | `hard_negative_weighted` | 69138 | 1355 | 0.106261 | 0.997048 | 11363 | 4 | 0.019888 |
| 2015 | `uniform_negative_matched_weight` | 69138 | 1355 | 0.104511 | 0.993358 | 11533 | 9 | 0.018748 |
| 2016 | `baseline_unweighted` | 42987 | 181 | 0.071400 | 0.972376 | 2289 | 5 | 0.030831 |
| 2016 | `hard_negative_weighted` | 42987 | 181 | 0.076453 | 0.966851 | 2114 | 6 | 0.035959 |
| 2016 | `uniform_negative_matched_weight` | 42987 | 181 | 0.070683 | 0.972376 | 2314 | 5 | 0.030137 |
| 2017 | `baseline_unweighted` | 19529 | 253 | 0.155512 | 0.936759 | 1287 | 16 | 0.012000 |
| 2017 | `hard_negative_weighted` | 19529 | 253 | 0.149527 | 0.936759 | 1348 | 16 | 0.012829 |
| 2017 | `uniform_negative_matched_weight` | 19529 | 253 | 0.156229 | 0.936759 | 1280 | 16 | 0.012192 |
| 2022 | `baseline_unweighted` | 50756 | 421 | 0.039573 | 0.985748 | 10072 | 6 | 0.008994 |
| 2022 | `hard_negative_weighted` | 50756 | 421 | 0.039281 | 0.985748 | 10150 | 6 | 0.009074 |
| 2022 | `uniform_negative_matched_weight` | 50756 | 421 | 0.038778 | 0.985748 | 10287 | 6 | 0.008743 |
| 2023 | `baseline_unweighted` | 60366 | 781 | 0.103397 | 0.884763 | 5992 | 90 | 0.018203 |
| 2023 | `hard_negative_weighted` | 60366 | 781 | 0.097381 | 0.895006 | 6479 | 82 | 0.016408 |
| 2023 | `uniform_negative_matched_weight` | 60366 | 781 | 0.101536 | 0.888604 | 6141 | 87 | 0.017537 |

## Limits

Already inspected years: adaptive development evidence, not an independent test. The control is the stored pipeline and
is not refitted; `uniform_matched` is the refit and weight control. Near-miss negatives are between 0.0449 and 0.0546
of the training negatives, so the matched uniform weight is between 1.0898 and 1.1092 and `uniform_matched` was expected
to stay close to the control; where it differs from the control (for example the 2017 alert threshold), the difference
is not attributable to near-miss membership. Weighted training changes the raw scores; calibration on the prior year is
unweighted, so the candidates' thresholds move with them and each candidate is judged at its own prior-year thresholds.
One factor (3) and one span (72 hours) were fixed in advance; this result says nothing about other values, and none may
be chosen from these results. Near-miss membership uses window labels, not flare peak times, and is censored at the
edges of the training role. Consecutive hourly windows overlap in 23 of their 24 hours and HARPs repeat, so counts are
windows and positive runs, never independent events, and intervals are HARP-clustered. 2016 and 2017 have few positive
runs (8 and 6) and wide intervals. The bootstrap intervals hold the fitted models and thresholds fixed and omit training
and calibration uncertainty. The relabelled labels are an association by NOAA SGAS and JSOC `NOAA_ARS`, not ground
truth. 2022 is an alert fallback year for all three; 2017 is one for `near_miss_w3`.

## Reproduction

```sh
bash agents/bin/evidence.sh seed
OMP_NUM_THREADS=3 python -m scripts.audit_near_miss_weighting --config config/near-miss-weighting-v1.json --output artifacts/<new directory>
python agents/bin/hale_call.py interpret_result '{"protocol": "config/near-miss-weighting-v1.json", "artifact": "artifacts/<new directory>"}'
```

Config sha256 `7831b49802bb4ff7e9aa99def23582ade1bf25a758eb5fb1caed1450a1dafaed`; `phase1.json` sha256
`1e89be264456db4d4e3322a0f1ebba91ac208b3555accbc92fdb0009de35489c`; `report.json` sha256
`03ffa9b2bc525fb3cf55855c71b0c9c60f6f41c5a50fd9667a4ea825f52dc5c4`. Use a new output directory; the runner refuses to
overwrite an existing one.
