# HARP life-phase features on the adopted pipeline (2026-11-26)

## Decision

Development basis: the relabelled table `artifacts/relabelled_development_20261111_r1` and the adopted pipeline
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)). The basis changed on 2026-11-12 because the frozen
labels covered under 30% of the mapped 2022 to 2023 M/X flares. Already inspected years: adaptive development evidence,
not an independent test.

Reading `L3_no_gain`, outcome label `result:no-gain`, by the rule frozen in
[`config/life-phase-v1.json`](../config/life-phase-v1.json) before any result. The protocol carries an `acceptance_rule`
(`decision.life_phase_goal_met_and_beats_age_only >= 1`); Hale `interpret_result` on `artifacts/life_phase_20261126_r1` returns `reject`
with observed value 0. That decision is the outcome. Placing each window in the stored life of its HARP does not raise
alert precision by the frozen rule, and neither does the age-only refit.

- Years in which `life_phase` meets the per-year primary acceptance against the control: none (of six).
  `age_only` meets it in 2015, 2017. Neither candidate meets `all_year_primary` or `cycle25_primary`
  (2022 and 2023), so neither meets the goal against the control and `L2_refit_or_age_only` does not apply either.
- `life_phase` beats `age_only` in none of the six years. Its alert precision is above `age_only` in
  2022, 2023, but in each of those years it misses more positive runs or loses more than 0.02 of window recall.
- `life_phase` alert precision is above the control in 2023 and below it in 2014, 2015, 2016, 2017, 2022.
  In 2023 it is 0.4386 against 0.4263, but it misses 71 against
  68 of 159 positive runs and its window recall falls by 0.0318.
  In the 2022 alert fallback year it is 0.4706 against 0.4727, with 34
  against 32 of 72 positive runs missed and a recall drop of 0.0589.
- The lower bound of the paired HARP-cluster bootstrap interval of the alert precision difference against the control
  is above 0 in no year for either candidate (the `age_only` lower bound in 2017 is exactly 0.0000). The interval lies wholly below 0 in 2015 for `life_phase` and in
  2022 for `age_only`; the interval of `life_phase` minus `age_only` lies wholly below 0 in 2015.
- `age_only` alert precision is above the control in 2015, 2017 and below it in 2014, 2016, 2022, 2023; its
  differences are small (largest 0.0127).
- Secondary, reported and not judged: alert precision is at least 0.50 in 2014, 2015, 2017 for each of the control,
  `age_only` and `life_phase`. 2022 and 2023 stay below 0.50 for every candidate.
- Descriptive: `life_phase` has fewer watch-tier false-positive windows than the control in 2015, 2022, 2023 and a higher
  within-flaring-HARP AP in 2014, 2016, 2023. On the evaluation windows without a stored-window gap in the last 72 hours,
  `life_phase` alert precision is above the control in 2023. None of this is judged by the reading.

Consequence: on this evidence the six-measurement life-phase features are not a route to higher alert precision. No
model is promoted and no alert, threshold, operating point or dashboard setting is changed. The run made 24 constituent
fits (the budget), downloaded nothing and did not access the reserved 2024 to 2025 test.

## Why this was tried

Idea issue #11. Every feature of the adopted pipeline describes the last 12 hours, so the model cannot tell a region
that is still growing from one past its peak. The [relabelled cycle-25 diagnostic](cycle25-diagnostic-relabelled-20261112.md)
found within-flaring-HARP AP 0.4968 and 0.4057 in 2022 and 2023, and that 0.7139 and 0.7561 of the alert false-positive
windows lie within 72 hours of a positive window of the same HARP: the alert tier finds the region and ranks the hours
inside it poorly. The [frozen-label long-history experiment](precision-long-history-20261028.md) used 24 and 48 hour
summaries without a lifetime reference, on one split and a recall 0.95 gate.

## What was run

One execution of the protocol exactly as merged, from `main` commit `da5fae0` (which contains the protocol merge
`bb8826f`), with 24 constituent fits (2 candidates, 6 years, 2 constituents), no hyperparameter search and no download.
Wall time 299 seconds.

```sh
OMP_NUM_THREADS=3 python -m scripts.audit_life_phase --config config/life-phase-v1.json --output artifacts/life_phase_20261126_r1
```

| item | sha256 |
| --- | --- |
| `config/life-phase-v1.json` | `7339ad5fbd85fdcfc579e599c9c0b0635603fbd330119f1948c2fc6e451a74f2` |
| `artifacts/relabelled_development_20261111_r1/report.json` (table) | `2847215ce5a5dedb9ebb93d7fa0ba1bcb7b4a7bf9fdcd80bab95e63726b9ac43` |
| `artifacts/walk_forward_v2_20261112_r1/report.json` (control) | `c2b326d90253e824e9dd324158933e01c1216788653b1d284bf22850f67f76f1` |
| `config/walk-forward-v2.json` | `d6e08a575193162afe59e068c568b51dee5e34c3950dcb5b6ed98b817e63d3bb` |
| `config/walk-forward-v1.json` | `7c48fd7381456bee22f928b44da537880f06b4d70fd2b38b822279474c616303` |
| `artifacts/life_phase_20261126_r1/phase1.json` | `62489c3dfb77a14a44219bd509233be914534ea1bc4b7d80b263b61e9dd42feb` |
| `artifacts/life_phase_20261126_r1/thresholds.json` | `4d2901e3f055a5f2703ab4a5ccb9b694894c3017f0e88d20864ba21304271189` |
| `artifacts/life_phase_20261126_r1/features.json` | `4d1697ebfbbbdda8b49fd29266ff00f73cfde12ede52118c12bf1e707902fdeb` |
| `artifacts/life_phase_20261126_r1/life_coverage.csv` | `adac7b44bf70c499313a186a5ae7eec5ae49f7ed8d989406ad2607b81cfc43fc` |
| `artifacts/life_phase_20261126_r1/results.csv` | `6e775deeac2971ff2bfe5fed2d8fcfae918e6d4cb61b214ab502ca72ddea556f` |
| `artifacts/life_phase_20261126_r1/intervals.csv` | `bfc803050abfa78771904222f0917d1ca9da9e487e67d072a2a7a661fb81849f` |
| `artifacts/life_phase_20261126_r1/complete_history.csv` | `d13d56adab69f84bbf36616ec6879f6b52e2428321ecaf4044dedfcbc145a41a` |
| `artifacts/life_phase_20261126_r1/report.json` | `c305b5aa3f77024ef54b5e62518ec0d7fc96fbc80b7b6bcdead53fb167d4d129` |

The runner checked the table report, the control report, both pipeline protocols and the per-year control
`predictions.parquet` and `thresholds.json` against their stored sha256 before use; `models.joblib` was never opened.
It recomputed the eight population counts of every year and found them equal to the protocol. The stored alert fallback
flags (2022) equal the protocol. Thresholds, feature lists, coverage and candidate probabilities were written to disk and
hashed (`phase1.json`) before any evaluation label was read, and still had the recorded hashes after evaluation. The
stored control labels equal the relabelled table label for every evaluation window.

## Method

Population: the evaluation windows of the adopted pipeline, one per HARP and hour, for 2014, 2015, 2016, 2017, 2022 and
2023, with an expanding annual walk-forward (training before the calibration year, calibration on the prior year). 2022
is an alert fallback year: its stored alert threshold comes from the fallback rule of `config/walk-forward-v2.json`
because prior-year precision 0.50 was unreachable. The candidates' own alert thresholds are also fallback thresholds in
2022 and in no other year. Fallback years are marked in every table.

Candidates. `control`: the stored ensemble probabilities and stored watch and alert thresholds, not refitted.
`age_only`: refit of the unchanged walk-forward-v1 recipes (0.45 logistic and 0.55 XGBoost, sigmoid calibration on the prior
year) on the 96 SHARP summaries plus `life__log1p_hours_since_first_window` (97 features). `life_phase`: `age_only` plus 36
life-phase features (133 features): for each of `USFLUX`, `TOTUSJH`, `TOTPOT`, `SAVNCPP`, `R_VALUE` and `MEANSHR` the ratio of
the current `__mean` to the running maximum of earlier stored windows of the HARP (clipped at 100), the running z-score
against their mean and standard deviation (clipped to -100 to 100), the hours since the running maximum, and the change
against the latest stored earlier window at or before 24, 48 and 72 hours. The features use only forecast keys and the
six `__mean` summaries of earlier windows of the same HARP, never a label, label status, role, later window or other
HARP. No window count and no gap flag is a model input. Each candidate selects its own watch threshold (prior-year
window recall 0.90) and alert threshold (prior-year precision 0.50, recall floor 0.10, fallback flag) on calibration-year
probabilities.

Acceptance, identical to [`config/activity-history-v2.json`](../config/activity-history-v2.json): a candidate meets the
per-year primary acceptance when its alert precision is higher than the control, its missed positive runs are not above
the control and its window recall drops by at most 0.02. `all_year_primary`: this holds in all six years.
`cycle25_primary`: it holds in both 2022 and 2023. A candidate meets the goal against the control by the all-year path, or
by the cycle-25 path with the lower bound of the paired HARP-cluster bootstrap interval of the precision difference (1000
draws, seed 24, 2.5 and 97.5 percent quantiles) above 0 in both 2022 and 2023. `life_phase` beats `age_only` in a year when
the same per-year rule holds with `age_only` in the place of the control. `specific_goal`: `life_phase` meets the goal by a
path and beats `age_only` in every year of that path.

Reading rule, applied in this order: `L1_life_phase_helps` if `life_phase` meets `specific_goal`; otherwise
`L2_refit_or_age_only` if either candidate meets the goal against the control; otherwise `L3_no_gain`.

Counts are overlapping hourly windows. A positive run is a contiguous group of positive windows of one HARP. Neither is
an independent event.

## Population and feature coverage

Counted before any fit, identical to the protocol and recomputed by the runner. A recent gap is a spacing above 1.5
hours between consecutive stored windows of the HARP in the last 72 hours; it is computed for reporting only.

| year | train rows | train positives | calibration rows | calibration positives | evaluation rows | train windows with recent gap | evaluation windows with recent gap | evaluation windows younger than 72 h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 150935 | 3161 | 76710 | 1455 | 78351 | 27432 | 18877 | 31437 |
| 2015 | 228635 | 4616 | 78351 | 2436 | 70554 | 41882 | 14648 | 29127 |
| 2016 | 307980 | 7129 | 70554 | 1461 | 43142 | 60765 | 8294 | 18972 |
| 2017 | 379962 | 8638 | 43142 | 214 | 19843 | 75419 | 3299 | 8263 |
| 2022 | 466206 | 9141 | 29887 | 377 | 65593 | 90404 | 16677 | 26771 |
| 2023 | 496391 | 9518 | 65593 | 2190 | 96991 | 95330 | 21883 | 37863 |

Missing values of selected life features on the evaluation windows (`life_coverage.csv` holds all 37 for every role).
`life__log1p_hours_since_first_window` is never missing.

| year | evaluation rows | windows with recent gap | missing `life__USFLUX__ratio_to_running_max` | missing `life__USFLUX__running_z` | missing `life__USFLUX__change_24h` | missing `life__USFLUX__change_48h` | missing `life__USFLUX__change_72h` | missing `life__R_VALUE__ratio_to_running_max` | missing `life__R_VALUE__running_z` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 78351 | 18877 | 635 | 1261 | 12134 | 22351 | 31437 | 17574 | 17837 |
| 2015 | 70554 | 14648 | 598 | 1187 | 11296 | 20622 | 29127 | 14287 | 14691 |
| 2016 | 43142 | 8294 | 356 | 709 | 7260 | 13486 | 18972 | 7774 | 8007 |
| 2017 | 19843 | 3299 | 162 | 323 | 3232 | 5846 | 8263 | 3312 | 3428 |
| 2022 | 65593 | 16677 | 544 | 1085 | 10472 | 19053 | 26771 | 8873 | 9256 |
| 2023 | 96991 | 21883 | 751 | 1492 | 14684 | 26714 | 37863 | 15167 | 15684 |

## Alert tier

Precision is given with the delivered window recall and the missed positive runs. Intervals are HARP-cluster bootstrap
intervals of each candidate.

| year | candidate | fallback | alert threshold | TP | FP | FN | TN | recall | recall 95% interval | precision | precision 95% interval | accuracy | always-negative accuracy | alarm windows | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 0.4627 | 688 | 320 | 1748 | 75595 | 0.2824 | [0.1030, 0.4369] | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 1008 | 66/88 |
| 2014 | `age_only` | no | 0.4538 | 704 | 335 | 1732 | 75580 | 0.2890 | [0.1084, 0.4438] | 0.6776 | [0.4284, 0.8425] | 0.9736 | 0.9689 | 1039 | 65/88 |
| 2014 | `life_phase` | no | 0.4318 | 773 | 381 | 1663 | 75534 | 0.3173 | [0.1181, 0.4897] | 0.6698 | [0.4190, 0.8322] | 0.9739 | 0.9689 | 1154 | 66/88 |
| 2015 | `control` | no | 0.2631 | 545 | 457 | 916 | 68636 | 0.3730 | [0.1693, 0.5283] | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 1002 | 27/57 |
| 2015 | `age_only` | no | 0.2633 | 546 | 435 | 915 | 68658 | 0.3737 | [0.1711, 0.5244] | 0.5566 | [0.3369, 0.7317] | 0.9809 | 0.9793 | 981 | 27/57 |
| 2015 | `life_phase` | no | 0.2492 | 572 | 555 | 889 | 68538 | 0.3915 | [0.1775, 0.5518] | 0.5075 | [0.2947, 0.6697] | 0.9795 | 0.9793 | 1127 | 27/57 |
| 2016 | `control` | no | 0.2564 | 94 | 109 | 120 | 42819 | 0.4393 | [0.0000, 0.8506] | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 203 | 3/8 |
| 2016 | `age_only` | no | 0.2525 | 95 | 111 | 119 | 42817 | 0.4439 | [0.0000, 0.8736] | 0.4612 | [0.0000, 0.6196] | 0.9947 | 0.9950 | 206 | 3/8 |
| 2016 | `life_phase` | no | 0.2505 | 103 | 154 | 111 | 42774 | 0.4813 | [0.0000, 0.8621] | 0.4008 | [0.0000, 0.5357] | 0.9939 | 0.9950 | 257 | 2/8 |
| 2017 | `control` | no | 0.4145 | 177 | 27 | 88 | 19551 | 0.6679 | [0.0000, 0.8535] | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 204 | 3/6 |
| 2017 | `age_only` | no | 0.4356 | 177 | 25 | 88 | 19553 | 0.6679 | [0.0000, 0.8535] | 0.8762 | [0.0000, 1.0000] | 0.9943 | 0.9866 | 202 | 3/6 |
| 2017 | `life_phase` | no | 0.3661 | 187 | 58 | 78 | 19520 | 0.7057 | [0.0233, 0.9108] | 0.7633 | [0.0000, 0.9481] | 0.9931 | 0.9866 | 245 | 2/6 |
| 2022 | `control` | yes | 0.1570 | 1056 | 1178 | 1134 | 62225 | 0.4822 | [0.3268, 0.6058] | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 2234 | 32/72 |
| 2022 | `age_only` | yes | 0.1515 | 1100 | 1273 | 1090 | 62130 | 0.5023 | [0.3491, 0.6270] | 0.4635 | [0.3432, 0.5899] | 0.9640 | 0.9666 | 2373 | 29/72 |
| 2022 | `life_phase` | yes | 0.1641 | 927 | 1043 | 1263 | 62360 | 0.4233 | [0.2913, 0.5378] | 0.4706 | [0.3388, 0.6204] | 0.9648 | 0.9666 | 1970 | 34/72 |
| 2023 | `control` | no | 0.2689 | 1587 | 2136 | 2504 | 90764 | 0.3879 | [0.2918, 0.4663] | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 3723 | 68/159 |
| 2023 | `age_only` | no | 0.2648 | 1618 | 2211 | 2473 | 90689 | 0.3955 | [0.2997, 0.4710] | 0.4226 | [0.3481, 0.5033] | 0.9517 | 0.9578 | 3829 | 69/159 |
| 2023 | `life_phase` | no | 0.2749 | 1457 | 1865 | 2634 | 91035 | 0.3561 | [0.2673, 0.4279] | 0.4386 | [0.3580, 0.5248] | 0.9536 | 0.9578 | 3322 | 71/159 |

## Acceptance

`precision difference` is candidate minus control. `recall drop` is control recall minus candidate recall. The interval is
the paired HARP-cluster bootstrap interval of the precision difference. In 2017 982 of the 1000 draws could be used (a draw without any alert window of one side is skipped).

| year | candidate | fallback | control precision | candidate precision | precision difference | difference 95% interval | bootstrap draws used | recall drop | missed runs control | missed runs candidate | precision higher | missed runs not above | recall drop at most 0.02 | per-year primary met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `age_only` | no | 0.6825 | 0.6776 | -0.0050 | [-0.0148, 0.0072] | 1000 | -0.0066 | 66 | 65 | no | yes | yes | no |
| 2014 | `life_phase` | no | 0.6825 | 0.6698 | -0.0127 | [-0.0590, 0.0199] | 1000 | -0.0349 | 66 | 66 | no | yes | yes | no |
| 2015 | `age_only` | no | 0.5439 | 0.5566 | 0.0127 | [-0.0017, 0.0322] | 1000 | -0.0007 | 27 | 27 | yes | yes | yes | yes |
| 2015 | `life_phase` | no | 0.5439 | 0.5075 | -0.0364 | [-0.0943, -0.0078] | 1000 | -0.0185 | 27 | 27 | no | yes | yes | no |
| 2016 | `age_only` | no | 0.4631 | 0.4612 | -0.0019 | [-0.0294, 0.0092] | 1000 | -0.0047 | 3 | 3 | no | yes | yes | no |
| 2016 | `life_phase` | no | 0.4631 | 0.4008 | -0.0623 | [-0.2215, 0.0067] | 1000 | -0.0421 | 3 | 2 | no | yes | yes | no |
| 2017 | `age_only` | no | 0.8676 | 0.8762 | 0.0086 | [0.0000, 0.0288] | 982 | 0.0000 | 3 | 3 | yes | yes | yes | yes |
| 2017 | `life_phase` | no | 0.8676 | 0.7633 | -0.1044 | [-0.2202, 0.0294] | 982 | -0.0377 | 3 | 2 | no | yes | yes | no |
| 2022 | `age_only` | yes | 0.4727 | 0.4635 | -0.0091 | [-0.0209, -0.0003] | 1000 | -0.0201 | 32 | 29 | no | yes | yes | no |
| 2022 | `life_phase` | yes | 0.4727 | 0.4706 | -0.0021 | [-0.0390, 0.0304] | 1000 | 0.0589 | 32 | 34 | no | no | no | no |
| 2023 | `age_only` | no | 0.4263 | 0.4226 | -0.0037 | [-0.0105, 0.0033] | 1000 | -0.0076 | 68 | 69 | no | no | yes | no |
| 2023 | `life_phase` | no | 0.4263 | 0.4386 | 0.0123 | [-0.0101, 0.0366] | 1000 | 0.0318 | 68 | 71 | yes | no | no | no |

| candidate | years meeting per-year primary | all_year_primary | cycle25_primary | bootstrap lower bound above 0 in 2022 and 2023 | goal against control met | years with alert precision at least 0.50 (secondary) |
| --- | --- | --- | --- | --- | --- | --- |
| `control` |  |  |  |  |  | 2014, 2015, 2017 |
| `age_only` | 2015, 2017 | no | no | no | no | 2014, 2015, 2017 |
| `life_phase` | none | no | no | no | no | 2014, 2015, 2017 |

`life_phase` against `age_only`, each with its own prior-year thresholds:

| year | fallback | age_only precision | life_phase precision | precision difference | difference 95% interval | bootstrap draws used | recall drop | missed runs age_only | missed runs life_phase | beats age_only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | no | 0.6776 | 0.6698 | -0.0077 | [-0.0487, 0.0208] | 1000 | -0.0283 | 65 | 66 | no |
| 2015 | no | 0.5566 | 0.5075 | -0.0490 | [-0.1126, -0.0158] | 1000 | -0.0178 | 27 | 27 | no |
| 2016 | no | 0.4612 | 0.4008 | -0.0604 | [-0.2200, 0.0028] | 1000 | -0.0374 | 3 | 2 | no |
| 2017 | no | 0.8762 | 0.7633 | -0.1130 | [-0.2310, 0.0294] | 982 | -0.0377 | 3 | 2 | no |
| 2022 | yes | 0.4635 | 0.4706 | 0.0070 | [-0.0307, 0.0412] | 1000 | 0.0790 | 29 | 34 | no |
| 2023 | no | 0.4226 | 0.4386 | 0.0160 | [-0.0084, 0.0425] | 1000 | 0.0394 | 69 | 71 | no |

## Watch tier

Each candidate with its own prior-year watch threshold. Not part of the reading.

| year | candidate | fallback | watch threshold | TP | FP | FN | TN | recall | recall 95% interval | precision | precision 95% interval | accuracy | always-negative accuracy | alarm windows | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 0.0311 | 2146 | 9020 | 290 | 66895 | 0.8810 | [0.8065, 0.9357] | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 11166 | 6/88 |
| 2014 | `age_only` | no | 0.0309 | 2154 | 9030 | 282 | 66885 | 0.8842 | [0.8106, 0.9382] | 0.1926 | [0.1320, 0.2598] | 0.8812 | 0.9689 | 11184 | 6/88 |
| 2014 | `life_phase` | no | 0.0269 | 2199 | 10204 | 237 | 65711 | 0.9027 | [0.8403, 0.9470] | 0.1773 | [0.1223, 0.2394] | 0.8667 | 0.9689 | 12403 | 5/88 |
| 2015 | `control` | no | 0.0364 | 1396 | 8079 | 65 | 61014 | 0.9555 | [0.8917, 0.9971] | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 9475 | 1/57 |
| 2015 | `age_only` | no | 0.0365 | 1396 | 8032 | 65 | 61061 | 0.9555 | [0.8908, 0.9964] | 0.1481 | [0.0910, 0.2053] | 0.8852 | 0.9793 | 9428 | 1/57 |
| 2015 | `life_phase` | no | 0.0405 | 1374 | 7227 | 87 | 61866 | 0.9405 | [0.8627, 0.9865] | 0.1597 | [0.0998, 0.2202] | 0.8963 | 0.9793 | 8601 | 2/57 |
| 2016 | `control` | no | 0.0471 | 201 | 1722 | 13 | 41206 | 0.9393 | [0.4545, 1.0000] | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 1923 | 0/8 |
| 2016 | `age_only` | no | 0.0488 | 200 | 1650 | 14 | 41278 | 0.9346 | [0.4545, 1.0000] | 0.1081 | [0.0000, 0.1974] | 0.9614 | 0.9950 | 1850 | 0/8 |
| 2016 | `life_phase` | no | 0.0407 | 203 | 2323 | 11 | 40605 | 0.9486 | [0.5000, 1.0000] | 0.0804 | [0.0000, 0.1522] | 0.9459 | 0.9950 | 2526 | 0/8 |
| 2017 | `control` | no | 0.0270 | 243 | 1058 | 22 | 18520 | 0.9170 | [0.7692, 1.0000] | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1301 | 1/6 |
| 2017 | `age_only` | no | 0.0241 | 243 | 1110 | 22 | 18468 | 0.9170 | [0.7692, 1.0000] | 0.1796 | [0.0000, 0.4515] | 0.9430 | 0.9866 | 1353 | 1/6 |
| 2017 | `life_phase` | no | 0.0235 | 243 | 1082 | 22 | 18496 | 0.9170 | [0.7538, 1.0000] | 0.1834 | [0.0000, 0.4496] | 0.9444 | 0.9866 | 1325 | 1/6 |
| 2022 | `control` | no | 0.0183 | 2024 | 11917 | 166 | 51486 | 0.9242 | [0.8502, 0.9731] | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 13941 | 5/72 |
| 2022 | `age_only` | no | 0.0193 | 2023 | 11565 | 167 | 51838 | 0.9237 | [0.8493, 0.9728] | 0.1489 | [0.1034, 0.2015] | 0.8211 | 0.9666 | 13588 | 6/72 |
| 2022 | `life_phase` | no | 0.0218 | 2010 | 10494 | 180 | 52909 | 0.9178 | [0.8386, 0.9699] | 0.1607 | [0.1125, 0.2165] | 0.8373 | 0.9666 | 12504 | 7/72 |
| 2023 | `control` | no | 0.0405 | 3695 | 16022 | 396 | 76878 | 0.9032 | [0.8486, 0.9425] | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 19717 | 10/159 |
| 2023 | `age_only` | no | 0.0407 | 3696 | 16101 | 395 | 76799 | 0.9034 | [0.8496, 0.9424] | 0.1867 | [0.1512, 0.2221] | 0.8299 | 0.9578 | 19797 | 8/159 |
| 2023 | `life_phase` | no | 0.0410 | 3698 | 15883 | 393 | 77017 | 0.9039 | [0.8500, 0.9432] | 0.1889 | [0.1530, 0.2248] | 0.8322 | 0.9578 | 19581 | 8/159 |

Watch-tier accuracy is below the always-negative accuracy in every year for every candidate.

## Ranking and origin of alert false positives (descriptive)

AP, region AP and within-flaring-HARP AP use the full evaluation-year ranking. The false-positive shares refer to the
alert windows of each candidate. `precision_at_control_recall` is the candidate's precision at the evaluation-year
threshold that delivers the control's alert recall: an oracle-matched description that uses evaluation labels and is
never deployable (for the control it is its own alert precision). `life_phase` is above the control on it in
2014, `age_only` in 2014, 2015, 2017, 2022.

| year | candidate | fallback | average precision | region AP | within-flaring-HARP AP | alert FP share from never-flaring HARPs | alert FP share within 72 h of a positive window | precision_at_control_recall (oracle) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 0.5015 | 0.7600 | 0.5528 | 0.1437 | 0.7063 | 0.6825 |
| 2014 | `age_only` | no | 0.5041 | 0.7615 | 0.5552 | 0.1373 | 0.7194 | 0.6894 |
| 2014 | `life_phase` | no | 0.5027 | 0.7724 | 0.5599 | 0.1286 | 0.7428 | 0.7311 |
| 2015 | `control` | no | 0.4823 | 0.8264 | 0.5331 | 0.0853 | 0.8249 | 0.5439 |
| 2015 | `age_only` | no | 0.4752 | 0.8237 | 0.5259 | 0.0782 | 0.8322 | 0.5561 |
| 2015 | `life_phase` | no | 0.4601 | 0.7890 | 0.5143 | 0.1441 | 0.7387 | 0.5113 |
| 2016 | `control` | no | 0.4060 | 0.6333 | 0.4853 | 0.2569 | 0.5688 | 0.4631 |
| 2016 | `age_only` | no | 0.4121 | 0.6005 | 0.4909 | 0.2523 | 0.5586 | 0.4585 |
| 2016 | `life_phase` | no | 0.4385 | 0.7375 | 0.5117 | 0.2792 | 0.3831 | 0.4455 |
| 2017 | `control` | no | 0.7975 | 1.0000 | 0.8727 | 0.1111 | 0.8889 | 0.8676 |
| 2017 | `age_only` | no | 0.8015 | 1.0000 | 0.8755 | 0.1200 | 0.8800 | 0.8850 |
| 2017 | `life_phase` | no | 0.7932 | 1.0000 | 0.8657 | 0.4310 | 0.5690 | 0.8592 |
| 2022 | `control` | yes | 0.4622 | 0.8315 | 0.4968 | 0.0823 | 0.7139 | 0.4727 |
| 2022 | `age_only` | yes | 0.4633 | 0.8356 | 0.4975 | 0.0943 | 0.6952 | 0.4813 |
| 2022 | `life_phase` | yes | 0.4482 | 0.8183 | 0.4866 | 0.0911 | 0.6855 | 0.4131 |
| 2023 | `control` | no | 0.3626 | 0.8655 | 0.4057 | 0.1320 | 0.7561 | 0.4263 |
| 2023 | `age_only` | no | 0.3636 | 0.8612 | 0.4066 | 0.1316 | 0.7553 | 0.4263 |
| 2023 | `life_phase` | no | 0.3654 | 0.8610 | 0.4118 | 0.1421 | 0.7662 | 0.4252 |

## Windows without a recent gap (descriptive)

Alert counts on the evaluation windows without a stored-window gap in the last 72 hours, with each candidate's own
alert threshold. The positive rate of windows with a gap is above that of windows without one in 2014, 2016, 2017, 2022, 2023
(slightly below in 2015, equal at four decimals): gaps carry label information, as the protocol's leak question expected. On this subset
`life_phase` precision is above the control in 2023 and `age_only` in 2015, 2016, 2017. This table has
no reading rule.

| year | candidate | fallback | windows without recent gap | window share | positives | positive share | positive rate with gap | positive rate without gap | TP | FP | FN | precision | recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 59474 | 0.7591 | 1750 | 0.7184 | 0.0363 | 0.0294 | 526 | 293 | 1224 | 0.6422 | 0.3006 |
| 2014 | `age_only` | no | 59474 | 0.7591 | 1750 | 0.7184 | 0.0363 | 0.0294 | 541 | 308 | 1209 | 0.6372 | 0.3091 |
| 2014 | `life_phase` | no | 59474 | 0.7591 | 1750 | 0.7184 | 0.0363 | 0.0294 | 586 | 333 | 1164 | 0.6376 | 0.3349 |
| 2015 | `control` | no | 55906 | 0.7924 | 1158 | 0.7926 | 0.0207 | 0.0207 | 420 | 384 | 738 | 0.5224 | 0.3627 |
| 2015 | `age_only` | no | 55906 | 0.7924 | 1158 | 0.7926 | 0.0207 | 0.0207 | 420 | 365 | 738 | 0.5350 | 0.3627 |
| 2015 | `life_phase` | no | 55906 | 0.7924 | 1158 | 0.7926 | 0.0207 | 0.0207 | 444 | 450 | 714 | 0.4966 | 0.3834 |
| 2016 | `control` | no | 34848 | 0.8078 | 156 | 0.7290 | 0.0070 | 0.0045 | 84 | 100 | 72 | 0.4565 | 0.5385 |
| 2016 | `age_only` | no | 34848 | 0.8078 | 156 | 0.7290 | 0.0070 | 0.0045 | 86 | 102 | 70 | 0.4574 | 0.5513 |
| 2016 | `life_phase` | no | 34848 | 0.8078 | 156 | 0.7290 | 0.0070 | 0.0045 | 88 | 141 | 68 | 0.3843 | 0.5641 |
| 2017 | `control` | no | 16544 | 0.8337 | 157 | 0.5925 | 0.0327 | 0.0095 | 93 | 27 | 64 | 0.7750 | 0.5924 |
| 2017 | `age_only` | no | 16544 | 0.8337 | 157 | 0.5925 | 0.0327 | 0.0095 | 93 | 25 | 64 | 0.7881 | 0.5924 |
| 2017 | `life_phase` | no | 16544 | 0.8337 | 157 | 0.5925 | 0.0327 | 0.0095 | 101 | 53 | 56 | 0.6558 | 0.6433 |
| 2022 | `control` | yes | 48916 | 0.7458 | 1567 | 0.7155 | 0.0374 | 0.0320 | 693 | 916 | 874 | 0.4307 | 0.4422 |
| 2022 | `age_only` | yes | 48916 | 0.7458 | 1567 | 0.7155 | 0.0374 | 0.0320 | 725 | 982 | 842 | 0.4247 | 0.4627 |
| 2022 | `life_phase` | yes | 48916 | 0.7458 | 1567 | 0.7155 | 0.0374 | 0.0320 | 599 | 824 | 968 | 0.4209 | 0.3823 |
| 2023 | `control` | no | 75108 | 0.7744 | 2785 | 0.6808 | 0.0597 | 0.0371 | 1091 | 1763 | 1694 | 0.3823 | 0.3917 |
| 2023 | `age_only` | no | 75108 | 0.7744 | 2785 | 0.6808 | 0.0597 | 0.0371 | 1107 | 1808 | 1678 | 0.3798 | 0.3975 |
| 2023 | `life_phase` | no | 75108 | 0.7744 | 2785 | 0.6808 | 0.0597 | 0.0371 | 968 | 1482 | 1817 | 0.3951 | 0.3476 |

## Frozen-label results

Kept visible for comparison, copied from the [frozen-label long-history experiment](precision-long-history-20261028.md)
and not recomputed: 24 and 48 hour history summaries on frozen labels, one split (calibration 2022, validation 2023) and a
recall 0.95 gate. Calibration selected the `incumbent`; the strongest history candidate had a higher AP but lower
precision at the gate. A different basis, split and gate: never pooled with the tables above.

| split | candidate | precision | recall | FP | average precision |
| --- | --- | --- | --- | --- | --- |
| calibration 2022, recall 0.95 gate | `incumbent` | 0.090662 | 0.950119 | 4012 | 0.286706 |
| calibration 2022, recall 0.95 gate | `history_logistic_w0.5` | 0.087432 | 0.950119 | 4175 | 0.320887 |
| validation 2023, transferred calibration threshold | `incumbent` (selected) | 0.103397 | 0.884763 | 5992 | 0.220619 |

## Limits

Already inspected years: adaptive development evidence, not an independent test. The control is the stored pipeline
and is not refitted; `age_only` is the refit and record-length control. The stored record of a HARP starts at its first
stored window, not at the emergence of the region, so the running maximum is a maximum of what was observed. Many
windows are young: in every year a large part of the evaluation windows has no stored window 72 hours earlier, where the
72-hour change is missing and the running statistics rest on few windows. Stored windows are label-status filtered: the
count feature was dropped and no feature states whether a particular earlier window exists, but the values of the life
features still rest on the stored earlier windows only; the complete-history table describes this and the reading does
not judge it. Gaps also come from quality and cadence rejections. Six measurements, three lags and two clips were fixed in
advance; a null result says nothing about other choices, and none may be chosen from these results. Consecutive hourly
windows overlap in 11 of their 12 observation hours and HARPs repeat, so counts are windows and positive runs, never
independent events, and intervals are HARP-clustered. 2016 and 2017 have few positive runs (8 and 6) and wide intervals.
The relabelled labels are an association by NOAA SGAS and JSOC `NOAA_ARS`, not ground truth. 2022 is an alert fallback year.

## Reproduction

```sh
bash agents/bin/evidence.sh seed
OMP_NUM_THREADS=3 python -m scripts.audit_life_phase --config config/life-phase-v1.json --output artifacts/<new directory>
python agents/bin/hale_call.py interpret_result '{"protocol": "config/life-phase-v1.json", "artifact": "artifacts/<new directory>"}'
```

Config sha256 `7339ad5fbd85fdcfc579e599c9c0b0635603fbd330119f1948c2fc6e451a74f2`; `phase1.json` sha256 `62489c3dfb77a14a44219bd509233be914534ea1bc4b7d80b263b61e9dd42feb`; `report.json` sha256 `c305b5aa3f77024ef54b5e62518ec0d7fc96fbc80b7b6bcdead53fb167d4d129`. Use a new
output directory; the runner refuses to overwrite an existing one. Fits are deterministic up to floating-point threading
differences.
