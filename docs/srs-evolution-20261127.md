# 24-hour evolution of the issued SRS region description at the alert tier on the adopted pipeline (2026-11-27)

## Decision

Development basis: the relabelled table `artifacts/relabelled_development_20261111_r1` and the adopted pipeline
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)). The basis changed on 2026-11-12 because the frozen
labels covered under 30% of the mapped 2022 to 2023 M/X flares. Already inspected years: adaptive development evidence,
not an independent test.

Reading `S3_no_gain`, outcome label `result:no-gain`, by the rule frozen in
[`config/srs-evolution-v1.json`](../config/srs-evolution-v1.json) before any result. The protocol carries an
`acceptance_rule` (`decision.srs_evolution_goal_met_and_beats_srs_static >= 1`); Hale `interpret_result` on
`artifacts/srs_evolution_20261127_r1` returns `reject` with observed value 0. That decision is the outcome, and the frozen
reading agrees with it: no candidate meets the goal against the control (`candidates_meeting_goal_against_control` is
empty), so `S2_refit_or_static_only` does not apply either. Adding the 24-hour change of the issued NOAA SRS description
to the static SRS context does not raise alert precision by the frozen rule, and the static SRS context alone does not
either.

- `srs_static` meets the per-year primary acceptance in 2015, 2016 and 2017; `srs_evolution` in 2015 and 2016 (of six
  years). Neither meets `all_year_primary` or `cycle25_primary` (2022 and 2023).
- `srs_evolution` beats `srs_static` in 2014, 2015 and 2016, by small precision differences (0.0067, 0.0014, 0.0158)
  whose paired HARP-cluster bootstrap intervals contain 0. It does not beat `srs_static` in 2017, 2022 or 2023.
- Cycle 25. In the 2022 fallback year alert precision is 0.4380 for `srs_static` and 0.4094 for `srs_evolution` against
  0.4727 for the control. Both miss fewer positive runs (26 and 25 against 32 of 72) with more false-positive windows
  (1454 and 1705 against 1178), and the paired bootstrap interval of the precision difference lies entirely below 0 for
  both ([-0.0648, -0.0111] and [-0.1060, -0.0316]), and also for `srs_evolution` minus `srs_static` ([-0.0492, -0.0142]).
  In 2023 alert precision is 0.4207 for `srs_static` and 0.4310 for `srs_evolution` against 0.4263, but both miss more
  positive runs (72 and 79 against 68 of 159) and lose more than 0.02 window recall (0.0379 and 0.0824).
- 2017: `srs_evolution` selects a much lower alert threshold than the control (0.2594 against 0.4145); its alert
  precision falls from 0.8676 to 0.6101 while it alarms the same positive runs (3 of 6 missed). `srs_static` raises 2017
  alert precision to 0.8923.
- 2014: alert precision is 0.6701 (`srs_static`) and 0.6768 (`srs_evolution`) against 0.6825 for the control, with fewer
  missed positive runs (63 against 66 of 88).
- Secondary, reported and not judged: alert precision is at least 0.50 in 2014, 2015 and 2017 for the control and both
  candidates. 2022 is an alert fallback year for all three, and no candidate has another fallback year.
- Descriptive: the evaluation windows with a computable 24-hour change are 0.3275 to 0.3979 of the windows but hold
  0.7853 to 1.0000 of the positive windows. On that subset 2022 alert precision is 0.4212 for `srs_evolution`, 0.4514 for
  `srs_static` and 0.4811 for the control. The within-flaring-HARP AP of `srs_evolution` is 0.4873 in 2022 and 0.3959 in
  2023, against 0.4968 and 0.4057 for the control. The share of alert false-positive windows within 72 hours of a
  positive window of the same HARP is 0.6305 in 2022 and 0.7733 in 2023 for `srs_evolution`, against 0.7139 and 0.7561
  for the control.

Consequence: on this evidence the 24-hour change of the issued SRS description, as frozen here, is not a route to higher
alert precision, and the static SRS description is not either. No model is promoted and no alert, threshold, operating
point or dashboard setting is changed. The run used 24 constituent fits, the budget of the protocol, and downloaded
nothing. The reserved 2024 to 2025 test was not accessed.

## Why this was tried

Idea issue #10. The issued SRS context was tested only as a static snapshot and only on the frozen labels at the recall
0.95 gate ([regional context results](region-context-results-20261109.md)): the 13 static features (`context`) met the
primary rule in 1 of 6 years and the availability-only refit (`flag`) in 4 of 6, so what passed was the refit and the
availability, not the content. The issue cites McCloskey, Gallagher and Bloomfield (2016, 2018), who report that flaring
rates rise when a sunspot group evolves upward in McIntosh class over 24 hours and fall when it evolves downward. The
[relabelled cycle-25 diagnostic](cycle25-diagnostic-relabelled-20261112.md) found that 0.7139 and 0.7561 of the alert
false-positive windows of 2022 and 2023 lie within 72 hours of a positive window of the same HARP: the alert tier finds
the region and misses the day, and growth or decay of the issued region description is a timing signal inside a region.

## What was run

One execution of the protocol exactly as merged, from `main` commit `2083796`: 2 candidates, 6 years, 2 constituents,
24 constituent fits, no hyperparameter search, 0 downloads. Wall time 306 seconds.

```sh
OMP_NUM_THREADS=3 python -m scripts.audit_srs_evolution --config config/srs-evolution-v1.json --output artifacts/srs_evolution_20261127_r1
```

| item | sha256 |
| --- | --- |
| `config/srs-evolution-v1.json` | `be3f3a46478ac1ae0b2a087a07d0d0427f2fa4561fa4e2449e19420f2ebec39f` |
| `artifacts/walk_forward_v2_20261112_r1/report.json` (control) | `c2b326d90253e824e9dd324158933e01c1216788653b1d284bf22850f67f76f1` |
| `artifacts/relabelled_development_20261111_r1/report.json` (labels) | `2847215ce5a5dedb9ebb93d7fa0ba1bcb7b4a7bf9fdcd80bab95e63726b9ac43` |
| `config/walk-forward-v2.json` (pipeline protocol) | `d6e08a575193162afe59e068c568b51dee5e34c3950dcb5b6ed98b817e63d3bb` |
| `config/walk-forward-v1.json` (base recipes) | `7c48fd7381456bee22f928b44da537880f06b4d70fd2b38b822279474c616303` |
| `data/region_summaries_20261109_r1/manifest.json` (SRS) | `36c9ba1c475e32cf171b199a4905225d5525fdda21d9ccbaff25610e1eac3c49` |
| `data/harp_noaa_mapping_20261109_r1/manifest.json` (HARP to NOAA) | `01b8f7cd0489233a49d06af33d5768ee7d256d8ca02dc05618e2b0dd86a27bf8` |
| `artifacts/srs_evolution_20261127_r1/phase1.json` | `b3595807ef556f520fe24a9a8a9619c60aaa4f779e66f63add20521b2b87d98b` |
| `artifacts/srs_evolution_20261127_r1/thresholds.json` | `a51caf355a7ca1ccf92cb94a561f41ff605bb9e04d70b1f65705e80d6f50b011` |
| `artifacts/srs_evolution_20261127_r1/features.json` | `d2f0a739e015d2e3ac4e4a7bc48bc5d227b71160e52c157ade98545b7508bb96` |
| `artifacts/srs_evolution_20261127_r1/srs_coverage.csv` | `af5d88a5d6fe098083774b956b44edce79080f73893e5016b89fcc0204bae6bd` |
| `artifacts/srs_evolution_20261127_r1/results.csv` | `7117f22ecf1755634f6cb130962082916844a3fb92c81ec1ff947123e3befbf2` |
| `artifacts/srs_evolution_20261127_r1/intervals.csv` | `9fbb1427e288fbff70bee5476cd28e54b7496b31ed65bd352c4bb432682d30ef` |
| `artifacts/srs_evolution_20261127_r1/evolution_subset.csv` | `407547daa0ec5b8aa8e64591de78a89d3dd7740417c1c6793b052e79e305d332` |
| `artifacts/srs_evolution_20261127_r1/report.json` | `2dbe1583c607646b7fa31c028d8dca1fce8d277099f5b8588812558bcb98b46d` |

Before the run every input named by the protocol was checked against its sha256: the table report, the control report,
both pipeline protocols, the SRS and mapping manifests, and the per-year `predictions.parquet` and `thresholds.json` of
the control against `artifact_hashes` of its report. Every SRS and mapping file was checked against its manifest. Both
manifests were read for products of the reserved period before any product file was opened, and none was found.
`models.joblib` was never opened. The runner recomputed the nine population and coverage counts of every fold and found
them equal to the protocol, and checked both issue times of every window against the forecast time minus 30 minutes.
Thresholds, feature lists, coverage and candidate probabilities were written and hashed (`phase1.json`) before any
evaluation label was read, and still had the recorded hashes after the evaluation. The target stored beside the control
probabilities equals the table label for every evaluation window.

## Method

Population: the evaluation windows of the adopted pipeline, one per HARP and hour, for 2014, 2015, 2016, 2017, 2022 and
2023. 2018 to 2021 are skipped by the adopted pipeline and stay out. 2022 is an alert fallback year of the control: its
stored alert threshold comes from the fallback rule of `config/walk-forward-v2.json`. The fallback flag of each
candidate's own alert threshold is given in every table.

Candidates. `control`: the stored ensemble probabilities and the stored per-year watch and alert thresholds of
`artifacts/walk_forward_v2_20261112_r1`, not refitted. `srs_static`: a refit of the unchanged `walk-forward-v1` recipes on
the 96 SHARP summaries plus the 13 context features of `config/region-context-v1.json`, unchanged (109 features); it
separates the refit, the availability and the static content from the new content. `srs_evolution`: `srs_static` plus
seven evolution features (116 features): `evo__earlier_listed` and the changes `evo__zurich_rank_change`,
`evo__penumbra_rank_change`, `evo__compact_rank_change`, `evo__mag_rank_change`, `evo__area_log_change` and
`evo__spots_log_change`.

The SRS used by a window at forecast time t is the latest SRS issued at or before t minus 30 minutes, restricted to the
NOAA numbers in the HARP's `NOAA_ARS` on the forecast date. The earlier SRS is the latest SRS issued 12 to 36 hours
before the SRS used; when there is none, nothing older is substituted. A change is taken over the NOAA numbers listed in
both products: the maximum rank in the SRS used minus the maximum in the earlier SRS, and `log(1 + sum)` differences for
the area and the spot count. `evo__earlier_listed` is 1 when a matched number is also listed earlier and 0 when an earlier
SRS exists and lists none of them. Missing values stay missing and pass through the median imputer with missing
indicators of the unchanged recipes; a missing earlier row is never encoded as no change. `evolution_available` is a
reporting flag only, never a model input.

Training: expanding annual walk-forward with `helio24.walk_forward.annual_fold`; models and hyperparameters of
`config/walk-forward-v1.json` unchanged, sigmoid calibration on the prior year, ensemble 0.45 logistic and 0.55 XGBoost.
Per candidate and year the watch threshold (prior-year window recall 0.90) and the alert threshold (prior-year precision
0.50, recall floor 0.10, fallback flag) are selected on calibration-year probabilities, so each candidate is judged at
its own prior-year thresholds.

Acceptance, identical to [`config/activity-history-v2.json`](../config/activity-history-v2.json): a candidate meets the
per-year primary acceptance when its alert precision is higher than the control, its missed positive runs are not above
the control and its window recall drops by at most 0.02. `all_year_primary`: this holds in all six years.
`cycle25_primary`: it holds in both 2022 and 2023. A candidate meets the goal against the control when
`all_year_primary` holds, or when `cycle25_primary` holds and the lower bound of the paired HARP-cluster bootstrap
interval of the precision difference (1000 draws, seed 24, 2.5 and 97.5 percent quantiles) is above 0 in both 2022 and
2023. In a year `srs_evolution` beats `srs_static` when the per-year primary acceptance holds with `srs_static` in the
place of the control.

Reading rule, applied in this order: `S1_evolution_helps` if `srs_evolution` meets the goal against the control by a path
and beats `srs_static` in every year of that path; otherwise `S2_refit_or_static_only` if `srs_evolution` or `srs_static`
meets the goal against the control; otherwise `S3_no_gain`.

Counts are overlapping hourly windows. A positive run is a contiguous group of positive windows of one HARP. Neither is
an independent event.

## SRS coverage

Label-free counts per year and role from `srs_coverage.csv`. `matched SRS row`: windows with at least one matched row in
the SRS used (`srs_available` 1). `change computable`: windows with at least one matched NOAA number also listed in the
earlier SRS, so the six changes are present. `missing each change` is the same for all six change features. The training
and evaluation counts equal the population frozen in the protocol.

| year | role | windows | matched SRS row | share matched | change computable | share computable | `evo__earlier_listed` 1 | `evo__earlier_listed` 0 | missing `evo__earlier_listed` | missing each change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `train` | 150935 | 69264 | 0.4589 | 58302 | 0.3863 | 58302 | 10949 | 81684 | 92633 |
| 2014 | `calibration` | 76710 | 35999 | 0.4693 | 30381 | 0.3961 | 30381 | 5468 | 40861 | 46329 |
| 2014 | `evaluation` | 78351 | 32082 | 0.4095 | 27707 | 0.3536 | 27707 | 4375 | 46269 | 50644 |
| 2015 | `train` | 228635 | 106001 | 0.4636 | 89338 | 0.3907 | 89338 | 16500 | 122797 | 139297 |
| 2015 | `calibration` | 78351 | 32082 | 0.4095 | 27707 | 0.3536 | 27707 | 4375 | 46269 | 50644 |
| 2015 | `evaluation` | 70554 | 27965 | 0.3964 | 23672 | 0.3355 | 23672 | 4293 | 42589 | 46882 |
| 2016 | `train` | 307980 | 138742 | 0.4505 | 117669 | 0.3821 | 117669 | 20910 | 169401 | 190311 |
| 2016 | `calibration` | 70554 | 27965 | 0.3964 | 23672 | 0.3355 | 23672 | 4293 | 42589 | 46882 |
| 2016 | `evaluation` | 43142 | 17181 | 0.3982 | 14130 | 0.3275 | 14130 | 3015 | 25997 | 29012 |
| 2017 | `train` | 379962 | 167677 | 0.4413 | 142252 | 0.3744 | 142252 | 25262 | 212448 | 237710 |
| 2017 | `calibration` | 43142 | 17181 | 0.3982 | 14130 | 0.3275 | 14130 | 3015 | 25997 | 29012 |
| 2017 | `evaluation` | 19843 | 9255 | 0.4664 | 7896 | 0.3979 | 7896 | 1359 | 10588 | 11947 |
| 2022 | `train` | 466206 | 203687 | 0.4369 | 171797 | 0.3685 | 171797 | 31667 | 262742 | 294409 |
| 2022 | `calibration` | 29887 | 13879 | 0.4644 | 11282 | 0.3775 | 11282 | 2597 | 16008 | 18605 |
| 2022 | `evaluation` | 65593 | 29343 | 0.4473 | 24594 | 0.3749 | 24594 | 4575 | 36424 | 40999 |
| 2023 | `train` | 496391 | 217710 | 0.4386 | 183223 | 0.3691 | 183223 | 34264 | 278904 | 313168 |
| 2023 | `calibration` | 65593 | 29343 | 0.4473 | 24594 | 0.3749 | 24594 | 4575 | 36424 | 40999 |
| 2023 | `evaluation` | 96991 | 41627 | 0.4292 | 36235 | 0.3736 | 36235 | 5392 | 55364 | 60756 |

In every year fewer than half of the evaluation windows have a matched SRS row (0.3964 to 0.4664) and fewer still a
computable change (0.3275 to 0.3979).

## Alert tier

Precision is given with the delivered window recall and the missed positive runs. Intervals are HARP-cluster bootstrap
intervals of each candidate. `fallback` marks an alert threshold selected by the fallback rule.

| year | candidate | fallback | alert threshold | TP | FP | FN | TN | recall | recall 95% interval | precision | precision 95% interval | accuracy | always-negative accuracy | alarm windows | alarmed positive runs | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 0.4627 | 688 | 320 | 1748 | 75595 | 0.2824 | [0.1030, 0.4369] | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 1008 | 22 | 66/88 |
| 2014 | `srs_static` | no | 0.4404 | 642 | 316 | 1794 | 75599 | 0.2635 | [0.0996, 0.3988] | 0.6701 | [0.4253, 0.8399] | 0.9731 | 0.9689 | 958 | 25 | 63/88 |
| 2014 | `srs_evolution` | no | 0.4184 | 645 | 308 | 1791 | 75607 | 0.2648 | [0.1127, 0.3902] | 0.6768 | [0.4419, 0.8374] | 0.9732 | 0.9689 | 953 | 25 | 63/88 |
| 2015 | `control` | no | 0.2631 | 545 | 457 | 916 | 68636 | 0.3730 | [0.1693, 0.5283] | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 1002 | 30 | 27/57 |
| 2015 | `srs_static` | no | 0.2639 | 595 | 429 | 866 | 68664 | 0.4073 | [0.1990, 0.5633] | 0.5811 | [0.3710, 0.7500] | 0.9816 | 0.9793 | 1024 | 31 | 26/57 |
| 2015 | `srs_evolution` | no | 0.2664 | 590 | 423 | 871 | 68670 | 0.4038 | [0.1903, 0.5640] | 0.5824 | [0.3606, 0.7463] | 0.9817 | 0.9793 | 1013 | 31 | 26/57 |
| 2016 | `control` | no | 0.2564 | 94 | 109 | 120 | 42819 | 0.4393 | [0.0000, 0.8506] | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 203 | 5 | 3/8 |
| 2016 | `srs_static` | no | 0.2467 | 94 | 108 | 120 | 42820 | 0.4393 | [0.0000, 0.9080] | 0.4653 | [0.0000, 0.5795] | 0.9947 | 0.9950 | 202 | 5 | 3/8 |
| 2016 | `srs_evolution` | no | 0.2384 | 102 | 110 | 112 | 42818 | 0.4766 | [0.0000, 0.9080] | 0.4811 | [0.0000, 0.6174] | 0.9949 | 0.9950 | 212 | 5 | 3/8 |
| 2017 | `control` | no | 0.4145 | 177 | 27 | 88 | 19551 | 0.6679 | [0.0000, 0.8535] | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 204 | 3 | 3/6 |
| 2017 | `srs_static` | no | 0.4308 | 174 | 21 | 91 | 19557 | 0.6566 | [0.0000, 0.8917] | 0.8923 | [0.0000, 0.9929] | 0.9944 | 0.9866 | 195 | 3 | 3/6 |
| 2017 | `srs_evolution` | no | 0.2594 | 194 | 124 | 71 | 19454 | 0.7321 | [0.0000, 0.9490] | 0.6101 | [0.0000, 0.8960] | 0.9902 | 0.9866 | 318 | 3 | 3/6 |
| 2022 | `control` | yes | 0.1570 | 1056 | 1178 | 1134 | 62225 | 0.4822 | [0.3268, 0.6058] | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 2234 | 40 | 32/72 |
| 2022 | `srs_static` | yes | 0.1333 | 1133 | 1454 | 1057 | 61949 | 0.5174 | [0.3689, 0.6364] | 0.4380 | [0.3232, 0.5646] | 0.9617 | 0.9666 | 2587 | 46 | 26/72 |
| 2022 | `srs_evolution` | yes | 0.1216 | 1182 | 1705 | 1008 | 61698 | 0.5397 | [0.3926, 0.6597] | 0.4094 | [0.2965, 0.5309] | 0.9586 | 0.9666 | 2887 | 47 | 25/72 |
| 2023 | `control` | no | 0.2689 | 1587 | 2136 | 2504 | 90764 | 0.3879 | [0.2918, 0.4663] | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 3723 | 91 | 68/159 |
| 2023 | `srs_static` | no | 0.2857 | 1432 | 1972 | 2659 | 90928 | 0.3500 | [0.2501, 0.4327] | 0.4207 | [0.3367, 0.5170] | 0.9523 | 0.9578 | 3404 | 87 | 72/159 |
| 2023 | `srs_evolution` | no | 0.3058 | 1250 | 1650 | 2841 | 91250 | 0.3055 | [0.2091, 0.3862] | 0.4310 | [0.3379, 0.5358] | 0.9537 | 0.9578 | 2900 | 80 | 79/159 |

## Acceptance

`precision difference` is candidate minus control. `recall drop` is control recall minus candidate recall; a negative
value is a gain. The interval is the paired HARP-cluster bootstrap interval of the precision difference. In 2017 982 of
the 1000 draws could be used against the control (a draw without any alert window of the control or of the candidate is
skipped).

| year | candidate | control fallback | candidate fallback | control precision | candidate precision | precision difference | difference 95% interval | bootstrap draws used | recall drop | missed runs control | missed runs candidate | precision higher | missed runs not above | recall drop at most 0.02 | per-year primary met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `srs_static` | no | no | 0.6825 | 0.6701 | -0.0124 | [-0.0369, 0.0246] | 1000 | 0.0189 | 66 | 63 | no | yes | yes | no |
| 2014 | `srs_evolution` | no | no | 0.6825 | 0.6768 | -0.0057 | [-0.0517, 0.0755] | 1000 | 0.0177 | 66 | 63 | no | yes | yes | no |
| 2015 | `srs_static` | no | no | 0.5439 | 0.5811 | 0.0371 | [0.0125, 0.0725] | 1000 | -0.0342 | 27 | 26 | yes | yes | yes | yes |
| 2015 | `srs_evolution` | no | no | 0.5439 | 0.5824 | 0.0385 | [0.0053, 0.0766] | 1000 | -0.0308 | 27 | 26 | yes | yes | yes | yes |
| 2016 | `srs_static` | no | no | 0.4631 | 0.4653 | 0.0023 | [-0.1032, 0.0254] | 1000 | 0.0000 | 3 | 3 | yes | yes | yes | yes |
| 2016 | `srs_evolution` | no | no | 0.4631 | 0.4811 | 0.0181 | [-0.0378, 0.0437] | 1000 | -0.0374 | 3 | 3 | yes | yes | yes | yes |
| 2017 | `srs_static` | no | no | 0.8676 | 0.8923 | 0.0247 | [-0.1084, 0.1336] | 982 | 0.0113 | 3 | 3 | yes | yes | yes | yes |
| 2017 | `srs_evolution` | no | no | 0.8676 | 0.6101 | -0.2576 | [-0.4478, 0.0000] | 982 | -0.0642 | 3 | 3 | no | yes | yes | no |
| 2022 | `srs_static` | yes | yes | 0.4727 | 0.4380 | -0.0347 | [-0.0648, -0.0111] | 1000 | -0.0352 | 32 | 26 | no | yes | yes | no |
| 2022 | `srs_evolution` | yes | yes | 0.4727 | 0.4094 | -0.0633 | [-0.1060, -0.0316] | 1000 | -0.0575 | 32 | 25 | no | yes | yes | no |
| 2023 | `srs_static` | no | no | 0.4263 | 0.4207 | -0.0056 | [-0.0279, 0.0182] | 1000 | 0.0379 | 68 | 72 | no | no | no | no |
| 2023 | `srs_evolution` | no | no | 0.4263 | 0.4310 | 0.0048 | [-0.0281, 0.0381] | 1000 | 0.0824 | 68 | 79 | yes | no | no | no |

`srs_evolution` against `srs_static`, the same three conditions with `srs_static` in the place of the control. The
interval is descriptive; in 2017 994 of the 1000 draws could be used.

| year | `srs_static` fallback | `srs_evolution` fallback | `srs_static` precision | `srs_evolution` precision | precision difference | difference 95% interval | bootstrap draws used | recall drop | missed runs `srs_static` | missed runs `srs_evolution` | precision higher | missed runs not above | recall drop at most 0.02 | beats `srs_static` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | no | no | 0.6701 | 0.6768 | 0.0067 | [-0.0252, 0.0644] | 1000 | -0.0012 | 63 | 63 | yes | yes | yes | yes |
| 2015 | no | no | 0.5811 | 0.5824 | 0.0014 | [-0.0273, 0.0261] | 1000 | 0.0034 | 26 | 26 | yes | yes | yes | yes |
| 2016 | no | no | 0.4653 | 0.4811 | 0.0158 | [-0.0092, 0.1158] | 1000 | -0.0374 | 3 | 3 | yes | yes | yes | yes |
| 2017 | no | no | 0.8923 | 0.6101 | -0.2822 | [-0.4404, 0.0000] | 994 | -0.0755 | 3 | 3 | no | yes | yes | no |
| 2022 | yes | yes | 0.4380 | 0.4094 | -0.0285 | [-0.0492, -0.0142] | 1000 | -0.0224 | 26 | 25 | no | yes | yes | no |
| 2023 | no | no | 0.4207 | 0.4310 | 0.0104 | [-0.0067, 0.0289] | 1000 | 0.0445 | 72 | 79 | yes | no | no | no |

| candidate | years meeting per-year primary | all_year_primary | cycle25_primary | bootstrap lower bound above 0 in 2022 and 2023 | goal met against control | years beating `srs_static` | alert fallback years | years with alert precision at least 0.50 (secondary) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `control` |  |  |  |  |  |  | 2022 | 2014, 2015, 2017 |
| `srs_static` | 2015, 2016, 2017 | no | no | no | no |  | 2022 | 2014, 2015, 2017 |
| `srs_evolution` | 2015, 2016 | no | no | no | no | 2014, 2015, 2016 | 2022 | 2014, 2015, 2017 |

## Where the evolution features exist (descriptive)

Alert counts of each candidate at its own alert threshold on the evaluation windows with (`change_available`) and without
(`change_missing`) a computable 24-hour change, from `evolution_subset.csv`. `positive share` is the share of the year's
positive windows in the subset. In 2017 the `change_missing` subset has no positive window.

| year | candidate | subset | windows | window share | positives | positive share | alert TP | alert FP | alert FN | alert precision | alert recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | `change_available` | 27707 | 0.3536 | 1913 | 0.7853 | 584 | 276 | 1329 | 0.6791 | 0.3053 |
| 2014 | `srs_static` | `change_available` | 27707 | 0.3536 | 1913 | 0.7853 | 556 | 287 | 1357 | 0.6595 | 0.2906 |
| 2014 | `srs_evolution` | `change_available` | 27707 | 0.3536 | 1913 | 0.7853 | 581 | 282 | 1332 | 0.6732 | 0.3037 |
| 2014 | `control` | `change_missing` | 50644 | 0.6464 | 523 | 0.2147 | 104 | 44 | 419 | 0.7027 | 0.1989 |
| 2014 | `srs_static` | `change_missing` | 50644 | 0.6464 | 523 | 0.2147 | 86 | 29 | 437 | 0.7478 | 0.1644 |
| 2014 | `srs_evolution` | `change_missing` | 50644 | 0.6464 | 523 | 0.2147 | 64 | 26 | 459 | 0.7111 | 0.1224 |
| 2015 | `control` | `change_available` | 23672 | 0.3355 | 1229 | 0.8412 | 482 | 369 | 747 | 0.5664 | 0.3922 |
| 2015 | `srs_static` | `change_available` | 23672 | 0.3355 | 1229 | 0.8412 | 530 | 353 | 699 | 0.6002 | 0.4312 |
| 2015 | `srs_evolution` | `change_available` | 23672 | 0.3355 | 1229 | 0.8412 | 524 | 342 | 705 | 0.6051 | 0.4264 |
| 2015 | `control` | `change_missing` | 46882 | 0.6645 | 232 | 0.1588 | 63 | 88 | 169 | 0.4172 | 0.2716 |
| 2015 | `srs_static` | `change_missing` | 46882 | 0.6645 | 232 | 0.1588 | 65 | 76 | 167 | 0.4610 | 0.2802 |
| 2015 | `srs_evolution` | `change_missing` | 46882 | 0.6645 | 232 | 0.1588 | 66 | 81 | 166 | 0.4490 | 0.2845 |
| 2016 | `control` | `change_available` | 14130 | 0.3275 | 174 | 0.8131 | 84 | 95 | 90 | 0.4693 | 0.4828 |
| 2016 | `srs_static` | `change_available` | 14130 | 0.3275 | 174 | 0.8131 | 84 | 96 | 90 | 0.4667 | 0.4828 |
| 2016 | `srs_evolution` | `change_available` | 14130 | 0.3275 | 174 | 0.8131 | 84 | 96 | 90 | 0.4667 | 0.4828 |
| 2016 | `control` | `change_missing` | 29012 | 0.6725 | 40 | 0.1869 | 10 | 14 | 30 | 0.4167 | 0.2500 |
| 2016 | `srs_static` | `change_missing` | 29012 | 0.6725 | 40 | 0.1869 | 10 | 12 | 30 | 0.4545 | 0.2500 |
| 2016 | `srs_evolution` | `change_missing` | 29012 | 0.6725 | 40 | 0.1869 | 18 | 14 | 22 | 0.5625 | 0.4500 |
| 2017 | `control` | `change_available` | 7896 | 0.3979 | 265 | 1.0000 | 177 | 24 | 88 | 0.8806 | 0.6679 |
| 2017 | `srs_static` | `change_available` | 7896 | 0.3979 | 265 | 1.0000 | 174 | 18 | 91 | 0.9062 | 0.6566 |
| 2017 | `srs_evolution` | `change_available` | 7896 | 0.3979 | 265 | 1.0000 | 194 | 105 | 71 | 0.6488 | 0.7321 |
| 2017 | `control` | `change_missing` | 11947 | 0.6021 | 0 | 0.0000 | 0 | 3 | 0 | 0.0000 |  |
| 2017 | `srs_static` | `change_missing` | 11947 | 0.6021 | 0 | 0.0000 | 0 | 3 | 0 | 0.0000 |  |
| 2017 | `srs_evolution` | `change_missing` | 11947 | 0.6021 | 0 | 0.0000 | 0 | 19 | 0 | 0.0000 |  |
| 2022 | `control` | `change_available` | 24594 | 0.3749 | 1773 | 0.8096 | 877 | 946 | 896 | 0.4811 | 0.4946 |
| 2022 | `srs_static` | `change_available` | 24594 | 0.3749 | 1773 | 0.8096 | 943 | 1146 | 830 | 0.4514 | 0.5319 |
| 2022 | `srs_evolution` | `change_available` | 24594 | 0.3749 | 1773 | 0.8096 | 986 | 1355 | 787 | 0.4212 | 0.5561 |
| 2022 | `control` | `change_missing` | 40999 | 0.6251 | 417 | 0.1904 | 179 | 232 | 238 | 0.4355 | 0.4293 |
| 2022 | `srs_static` | `change_missing` | 40999 | 0.6251 | 417 | 0.1904 | 190 | 308 | 227 | 0.3815 | 0.4556 |
| 2022 | `srs_evolution` | `change_missing` | 40999 | 0.6251 | 417 | 0.1904 | 196 | 350 | 221 | 0.3590 | 0.4700 |
| 2023 | `control` | `change_available` | 36235 | 0.3736 | 3231 | 0.7898 | 1306 | 1831 | 1925 | 0.4163 | 0.4042 |
| 2023 | `srs_static` | `change_available` | 36235 | 0.3736 | 3231 | 0.7898 | 1181 | 1699 | 2050 | 0.4101 | 0.3655 |
| 2023 | `srs_evolution` | `change_available` | 36235 | 0.3736 | 3231 | 0.7898 | 1018 | 1413 | 2213 | 0.4188 | 0.3151 |
| 2023 | `control` | `change_missing` | 60756 | 0.6264 | 860 | 0.2102 | 281 | 305 | 579 | 0.4795 | 0.3267 |
| 2023 | `srs_static` | `change_missing` | 60756 | 0.6264 | 860 | 0.2102 | 251 | 273 | 609 | 0.4790 | 0.2919 |
| 2023 | `srs_evolution` | `change_missing` | 60756 | 0.6264 | 860 | 0.2102 | 232 | 237 | 628 | 0.4947 | 0.2698 |

## Ranking and origin of alert false positives (descriptive)

Reported, not judged. Average precision, region AP and within-flaring-HARP AP do not depend on a threshold. The
false-positive shares are taken at each candidate's own alert threshold. `precision at control recall` is the
candidate's precision at the evaluation-year threshold that delivers the control's alert recall: an oracle-matched
description that uses evaluation labels and is never deployable.

| year | candidate | fallback | average precision | region AP | within-flaring-HARP AP | alert FP windows | alert FP share from never-flaring HARPs | alert FP share within 72 h of a positive window | control alert recall | precision at control recall (oracle) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 0.5015 | 0.7600 | 0.5528 | 320 | 0.1437 | 0.7063 | 0.2824 | 0.6825 |
| 2014 | `srs_static` | no | 0.4920 | 0.7731 | 0.5411 | 316 | 0.1203 | 0.6867 | 0.2824 | 0.6577 |
| 2014 | `srs_evolution` | no | 0.4889 | 0.7660 | 0.5395 | 308 | 0.1266 | 0.6721 | 0.2824 | 0.6673 |
| 2015 | `control` | no | 0.4823 | 0.8264 | 0.5331 | 457 | 0.0853 | 0.8249 | 0.3730 | 0.5439 |
| 2015 | `srs_static` | no | 0.4898 | 0.8193 | 0.5413 | 429 | 0.0956 | 0.8345 | 0.3730 | 0.5911 |
| 2015 | `srs_evolution` | no | 0.4918 | 0.8055 | 0.5435 | 423 | 0.0827 | 0.8416 | 0.3730 | 0.6009 |
| 2016 | `control` | no | 0.4060 | 0.6333 | 0.4853 | 109 | 0.2569 | 0.5688 | 0.4393 | 0.4631 |
| 2016 | `srs_static` | no | 0.4210 | 0.5625 | 0.5016 | 108 | 0.2685 | 0.5741 | 0.4393 | 0.4724 |
| 2016 | `srs_evolution` | no | 0.4287 | 0.6841 | 0.5020 | 110 | 0.2364 | 0.5636 | 0.4393 | 0.5281 |
| 2017 | `control` | no | 0.7975 | 1.0000 | 0.8727 | 27 | 0.1111 | 0.8889 | 0.6679 | 0.8676 |
| 2017 | `srs_static` | no | 0.7891 | 0.8667 | 0.8737 | 21 | 0.3810 | 0.6190 | 0.6679 | 0.8939 |
| 2017 | `srs_evolution` | no | 0.7852 | 0.8667 | 0.8718 | 124 | 0.6855 | 0.3145 | 0.6679 | 0.8719 |
| 2022 | `control` | yes | 0.4622 | 0.8315 | 0.4968 | 1178 | 0.0823 | 0.7139 | 0.4822 | 0.4727 |
| 2022 | `srs_static` | yes | 0.4584 | 0.8251 | 0.4931 | 1454 | 0.1114 | 0.6575 | 0.4822 | 0.4615 |
| 2022 | `srs_evolution` | yes | 0.4523 | 0.8247 | 0.4873 | 1705 | 0.1220 | 0.6305 | 0.4822 | 0.4492 |
| 2023 | `control` | no | 0.3626 | 0.8655 | 0.4057 | 2136 | 0.1320 | 0.7561 | 0.3879 | 0.4263 |
| 2023 | `srs_static` | no | 0.3513 | 0.8600 | 0.3976 | 1972 | 0.1476 | 0.7475 | 0.3879 | 0.4140 |
| 2023 | `srs_evolution` | no | 0.3501 | 0.8627 | 0.3959 | 1650 | 0.1339 | 0.7733 | 0.3879 | 0.4071 |

## Watch tier

Each candidate at its own prior-year watch threshold (window recall 0.90 on the prior year). No watch threshold is a
fallback.

| year | candidate | fallback | watch threshold | TP | FP | FN | TN | recall | recall 95% interval | precision | precision 95% interval | accuracy | always-negative accuracy | alarm windows | alarmed positive runs | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 0.0311 | 2146 | 9020 | 290 | 66895 | 0.8810 | [0.8065, 0.9357] | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 11166 | 82 | 6/88 |
| 2014 | `srs_static` | no | 0.0262 | 2191 | 10161 | 245 | 65754 | 0.8994 | [0.8333, 0.9481] | 0.1774 | [0.1222, 0.2402] | 0.8672 | 0.9689 | 12352 | 83 | 5/88 |
| 2014 | `srs_evolution` | no | 0.0251 | 2219 | 10516 | 217 | 65399 | 0.9109 | [0.8503, 0.9548] | 0.1742 | [0.1203, 0.2360] | 0.8630 | 0.9689 | 12735 | 84 | 4/88 |
| 2015 | `control` | no | 0.0364 | 1396 | 8079 | 65 | 61014 | 0.9555 | [0.8917, 0.9971] | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 9475 | 56 | 1/57 |
| 2015 | `srs_static` | no | 0.0350 | 1393 | 8000 | 68 | 61093 | 0.9535 | [0.8876, 0.9934] | 0.1483 | [0.0917, 0.2054] | 0.8856 | 0.9793 | 9393 | 56 | 1/57 |
| 2015 | `srs_evolution` | no | 0.0360 | 1381 | 7770 | 80 | 61323 | 0.9452 | [0.8745, 0.9863] | 0.1509 | [0.0935, 0.2094] | 0.8887 | 0.9793 | 9151 | 56 | 1/57 |
| 2016 | `control` | no | 0.0471 | 201 | 1722 | 13 | 41206 | 0.9393 | [0.4545, 1.0000] | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 1923 | 8 | 0/8 |
| 2016 | `srs_static` | no | 0.0476 | 198 | 1609 | 16 | 41319 | 0.9252 | [0.4091, 1.0000] | 0.1096 | [0.0000, 0.2015] | 0.9623 | 0.9950 | 1807 | 8 | 0/8 |
| 2016 | `srs_evolution` | no | 0.0495 | 198 | 1551 | 16 | 41377 | 0.9252 | [0.4091, 1.0000] | 0.1132 | [0.0000, 0.2061] | 0.9637 | 0.9950 | 1749 | 8 | 0/8 |
| 2017 | `control` | no | 0.0270 | 243 | 1058 | 22 | 18520 | 0.9170 | [0.7692, 1.0000] | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1301 | 5 | 1/6 |
| 2017 | `srs_static` | no | 0.0271 | 246 | 1017 | 19 | 18561 | 0.9283 | [0.7692, 1.0000] | 0.1948 | [0.0000, 0.4787] | 0.9478 | 0.9866 | 1263 | 5 | 1/6 |
| 2017 | `srs_evolution` | no | 0.0216 | 247 | 1100 | 18 | 18478 | 0.9321 | [0.7692, 1.0000] | 0.1834 | [0.0000, 0.4490] | 0.9437 | 0.9866 | 1347 | 5 | 1/6 |
| 2022 | `control` | no | 0.0183 | 2024 | 11917 | 166 | 51486 | 0.9242 | [0.8502, 0.9731] | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 13941 | 67 | 5/72 |
| 2022 | `srs_static` | no | 0.0176 | 2039 | 12169 | 151 | 51234 | 0.9311 | [0.8576, 0.9798] | 0.1435 | [0.0998, 0.1935] | 0.8122 | 0.9666 | 14208 | 67 | 5/72 |
| 2022 | `srs_evolution` | no | 0.0168 | 2044 | 12458 | 146 | 50945 | 0.9333 | [0.8619, 0.9818] | 0.1409 | [0.0983, 0.1901] | 0.8078 | 0.9666 | 14502 | 67 | 5/72 |
| 2023 | `control` | no | 0.0405 | 3695 | 16022 | 396 | 76878 | 0.9032 | [0.8486, 0.9425] | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 19717 | 149 | 10/159 |
| 2023 | `srs_static` | no | 0.0431 | 3679 | 15264 | 412 | 77636 | 0.8993 | [0.8455, 0.9398] | 0.1942 | [0.1579, 0.2306] | 0.8384 | 0.9578 | 18943 | 150 | 9/159 |
| 2023 | `srs_evolution` | no | 0.0427 | 3686 | 15425 | 405 | 77475 | 0.9010 | [0.8470, 0.9409] | 0.1929 | [0.1569, 0.2287] | 0.8368 | 0.9578 | 19111 | 150 | 9/159 |

Watch-tier accuracy is below the always-negative accuracy for every candidate in every year.

## Selected thresholds

Selected on calibration-year probabilities before any evaluation label was read. `prior-year recall` and
`prior-year precision` are the calibration-year values at the selected threshold.

| year | candidate | tier | threshold | prior-year recall | prior-year precision | fallback |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | `watch` | 0.0311 |  |  | no |
| 2014 | `control` | `alert` | 0.4627 | 0.1326 | 0.5000 | no |
| 2014 | `srs_static` | `watch` | 0.0262 |  |  | no |
| 2014 | `srs_static` | `alert` | 0.4404 | 0.1079 | 0.5000 | no |
| 2014 | `srs_evolution` | `watch` | 0.0251 |  |  | no |
| 2014 | `srs_evolution` | `alert` | 0.4184 | 0.1237 | 0.5000 | no |
| 2015 | `control` | `watch` | 0.0364 |  |  | no |
| 2015 | `control` | `alert` | 0.2631 | 0.4906 | 0.5000 | no |
| 2015 | `srs_static` | `watch` | 0.0350 |  |  | no |
| 2015 | `srs_static` | `alert` | 0.2639 | 0.4823 | 0.5000 | no |
| 2015 | `srs_evolution` | `watch` | 0.0360 |  |  | no |
| 2015 | `srs_evolution` | `alert` | 0.2664 | 0.4762 | 0.5000 | no |
| 2016 | `control` | `watch` | 0.0471 |  |  | no |
| 2016 | `control` | `alert` | 0.2564 | 0.4969 | 0.5000 | no |
| 2016 | `srs_static` | `watch` | 0.0476 |  |  | no |
| 2016 | `srs_static` | `alert` | 0.2467 | 0.5311 | 0.5000 | no |
| 2016 | `srs_evolution` | `watch` | 0.0495 |  |  | no |
| 2016 | `srs_evolution` | `alert` | 0.2384 | 0.5366 | 0.5000 | no |
| 2017 | `control` | `watch` | 0.0270 |  |  | no |
| 2017 | `control` | `alert` | 0.4145 | 0.2196 | 0.5000 | no |
| 2017 | `srs_static` | `watch` | 0.0271 |  |  | no |
| 2017 | `srs_static` | `alert` | 0.4308 | 0.2664 | 0.5000 | no |
| 2017 | `srs_evolution` | `watch` | 0.0216 |  |  | no |
| 2017 | `srs_evolution` | `alert` | 0.2594 | 0.4159 | 0.5000 | no |
| 2022 | `control` | `watch` | 0.0183 |  |  | no |
| 2022 | `control` | `alert` | 0.1570 | 0.2361 | 0.1996 | yes |
| 2022 | `srs_static` | `watch` | 0.0176 |  |  | no |
| 2022 | `srs_static` | `alert` | 0.1333 | 0.2653 | 0.1645 | yes |
| 2022 | `srs_evolution` | `watch` | 0.0168 |  |  | no |
| 2022 | `srs_evolution` | `alert` | 0.1216 | 0.2891 | 0.1542 | yes |
| 2023 | `control` | `watch` | 0.0405 |  |  | no |
| 2023 | `control` | `alert` | 0.2689 | 0.4461 | 0.5000 | no |
| 2023 | `srs_static` | `watch` | 0.0431 |  |  | no |
| 2023 | `srs_static` | `alert` | 0.2857 | 0.4068 | 0.5000 | no |
| 2023 | `srs_evolution` | `watch` | 0.0427 |  |  | no |
| 2023 | `srs_evolution` | `alert` | 0.3058 | 0.3676 | 0.5000 | no |

## Frozen-label results

Kept visible for comparison, copied from [regional context results](region-context-results-20261109.md) and not
recomputed: static SRS context on frozen labels, thresholds at prior-year recall 0.95, candidates `flag` (availability
only) and `context` (the 13 static features). It is a different basis, label set and gate; the values are never pooled
with the tables above and are not comparable with them.

| candidate | years_met | required_years | all_year_primary | met_years |
| --- | --- | --- | --- | --- |
| flag | 4 | 6 | no | [2014, 2016, 2022, 2023] |
| context | 1 | 6 | no | [2015] |

| year | candidate | threshold | TP | FP | recall | recall ≥ 0.95 | precision | alarmed positive runs | AP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 0.011475 | 2184 | 13886 | 0.9455 | no | 0.1359 | 80/83 | 0.5079 |
| 2014 | flag | 0.011701 | 2183 | 13761 | 0.9450 | no | 0.1369 | 80/83 | 0.5082 |
| 2014 | context | 0.009703 | 2202 | 14833 | 0.9532 | yes | 0.1293 | 80/83 | 0.4992 |
| 2015 | control | 0.018839 | 1346 | 11453 | 0.9934 | yes | 0.1052 | 51/51 | 0.4924 |
| 2015 | flag | 0.018485 | 1346 | 11551 | 0.9934 | yes | 0.1044 | 51/51 | 0.4930 |
| 2015 | context | 0.018868 | 1347 | 11297 | 0.9941 | yes | 0.1065 | 51/51 | 0.5118 |
| 2016 | control | 0.030831 | 176 | 2289 | 0.9724 | yes | 0.0714 | 7/7 | 0.3664 |
| 2016 | flag | 0.031593 | 173 | 2234 | 0.9558 | yes | 0.0719 | 7/7 | 0.3620 |
| 2016 | context | 0.026925 | 176 | 2380 | 0.9724 | yes | 0.0689 | 7/7 | 0.3645 |
| 2017 | control | 0.012000 | 237 | 1287 | 0.9368 | no | 0.1555 | 5/6 | 0.8117 |
| 2017 | flag | 0.010120 | 238 | 1370 | 0.9407 | no | 0.1480 | 5/6 | 0.8118 |
| 2017 | context | 0.012045 | 237 | 1303 | 0.9368 | no | 0.1539 | 5/6 | 0.7988 |
| 2022 | control | 0.008994 | 415 | 10072 | 0.9857 | yes | 0.0396 | 16/16 | 0.2800 |
| 2022 | flag | 0.009298 | 415 | 9868 | 0.9857 | yes | 0.0404 | 16/16 | 0.2791 |
| 2022 | context | 0.009014 | 415 | 10192 | 0.9857 | yes | 0.0391 | 16/16 | 0.2775 |
| 2023 | control | 0.018203 | 691 | 5992 | 0.8848 | no | 0.1034 | 36/38 | 0.2206 |
| 2023 | flag | 0.018357 | 689 | 5973 | 0.8822 | no | 0.1034 | 36/38 | 0.2205 |
| 2023 | context | 0.017289 | 686 | 6374 | 0.8784 | no | 0.0972 | 36/38 | 0.2258 |

## Limits

Already inspected years: adaptive development evidence, not an independent test. The control is the stored pipeline and
is not refitted; `srs_static` is the refit, availability and static-content control, and it differs from the control
in every year (for example the 2022 alert threshold 0.1333 against 0.1570), so differences between `srs_static` and the
control are not attributable to SRS content alone. The SRS is issued once a day, so at forecast time the change is up to
two days old; that is a limit, not a leak. Coverage is partial: fewer than half of the evaluation windows have a matched
SRS row and fewer still a computable change, so the evolution features can act on a minority of windows, although that
minority holds most positive windows. The SRS lists only regions with sunspots; a region without spots on either day has
no change. NOAA numbers come from `NOAA_ARS`, the definitive JSOC association fixed after the fact: which SRS rows belong
to a HARP is not known to be available at forecast time. Archived SRS text may differ from the bytes first issued. The
relabelled labels were recovered through SGAS products and the same `NOAA_ARS` mapping, so features and labels share the
source's region assignment errors. Seven features, one lag and one rule for the earlier product were fixed in advance; a
null result says nothing about other choices, such as 48 or 72 hour changes or the full McIntosh transition, and none may
be chosen from these results. Consecutive hourly windows overlap in 11 of their 12 observation hours and HARPs repeat,
and every window of a day shares one SRS, so counts are windows and positive runs, never independent events, and
intervals are HARP-clustered. 2016 and 2017 have few positive runs (8 and 6) and wide intervals. The bootstrap intervals
hold the fitted models and thresholds fixed and omit training and calibration uncertainty. 2022 is an alert fallback
year for all three.

## Reproduction

```sh
bash agents/bin/evidence.sh seed
OMP_NUM_THREADS=3 python -m scripts.audit_srs_evolution --config config/srs-evolution-v1.json --output artifacts/<new directory>
python agents/bin/hale_call.py interpret_result '{"protocol": "config/srs-evolution-v1.json", "artifact": "artifacts/<new directory>"}'
```

Config sha256 `be3f3a46478ac1ae0b2a087a07d0d0427f2fa4561fa4e2449e19420f2ebec39f`; `phase1.json` sha256
`b3595807ef556f520fe24a9a8a9619c60aaa4f779e66f63add20521b2b87d98b`; `report.json` sha256
`2dbe1583c607646b7fa31c028d8dca1fce8d277099f5b8588812558bcb98b46d`. Use a new output directory; the runner refuses to
overwrite an existing one.
