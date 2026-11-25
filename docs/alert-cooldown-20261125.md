# Alert cooldown and direction of alert false positives on the adopted pipeline (2026-11-25)

## Decision

Development basis: the relabelled table `artifacts/relabelled_development_20261111_r1` and the adopted pipeline
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)). The basis changed on 2026-11-12 because the frozen
labels covered under 30% of the mapped 2022 to 2023 M/X flares. Already inspected years: adaptive development evidence,
not an independent test.

Reading `C3_no_gain`, outcome label `result:no-gain`, by the rule frozen in
[`config/alert-cooldown-v1.json`](../config/alert-cooldown-v1.json) before any result. The protocol carries an
`acceptance_rule` (`decision.candidates_meeting_goal >= 1`); Hale `interpret_result` on `artifacts/alert_cooldown_20261125_r1` returns
`reject` with observed value 0. That decision is the outcome. A fixed causal cooldown of 24 or 48 hours does
not raise alert precision by the frozen rule.

- Years in which `cooldown_24h` meets the per-year primary acceptance: none (of six); `cooldown_48h` meets it in
  2016 only. Neither meets `cycle25_primary` (2022 and 2023), so `C2_partial` does not apply either.
- Alert precision is above the control in 2015, 2016 for `cooldown_24h` and in 2016, 2022, 2023 for
  `cooldown_48h`; it is below the control in 2014, 2017, 2022, 2023 and in 2014, 2015, 2017. The lower bound of the paired
  HARP-cluster bootstrap interval of the precision difference is above 0 in no year for either candidate
  (`cooldown_48h` in 2016 has a lower bound of exactly 0.0000).
- In cycle 25 `cooldown_48h` has higher precision than the control (0.4934 against 0.4727 in the 2022
  fallback year, 0.4396 against 0.4263 in 2023), but it misses more positive runs
  (33 against 32 of 72, and 73 against 68 of 159) and its window recall falls by 0.1068 and 0.0545,
  above the tolerance of 0.02.
- The cooldown removes true-positive windows along with false-positive windows. Over the six years `cooldown_24h` removes
  3040 alert windows, 1613 of them TP and 1427 FP; `cooldown_48h` removes 1685, 792 of them TP and
  893 FP. The window recall drop is between 0.1164 and 0.3774 for `cooldown_24h` and between
  0.0140 and 0.2189 for `cooldown_48h`; it stays within 0.02 only for `cooldown_48h` in 2016.
- Secondary, reported and not judged: alert precision is at least 0.50 in 2014, 2015, 2017 for the control and in
  2014, 2015, 2016, 2017 for both cooldowns. 2022 and 2023 stay below 0.50 for every candidate.
- Descriptive direction split of the control alert false positives (4227 windows over six years): the share of
  `lingering` windows is 0.1875 (2014), 0.3873 (2015), 0.4862 (2016), 0.8889 (2017), 0.3132 (2022), 0.3305 (2023); of `early` windows
  0.1969 (2014), 0.1860 (2015), 0.0000 (2016), 0.0000 (2017), 0.1528 (2022), 0.2289 (2023); of `between` windows
  0.3219 (2014), 0.2516 (2015), 0.0826 (2016), 0.0000 (2017), 0.2479 (2022), 0.1966 (2023). The three together reproduce the within-72-hours share of the
  relabelled cycle-25 diagnostic (0.7063 (2014), 0.8249 (2015), 0.5688 (2016), 0.8889 (2017), 0.7139 (2022), 0.7561 (2023)). The largest class is
  `between` in 2014, `lingering` in 2015, `lingering` in 2016, `lingering` in 2017, `lingering` in 2022, `lingering` in 2023. This part has no reading rule and decides nothing.

Consequence: on this evidence a fixed causal cooldown is not a route to higher alert precision. No model is promoted
and no alert, threshold, operating point or dashboard setting is changed. Nothing was fitted (0 model fits) and nothing
was downloaded. The reserved 2024 to 2025 test was not accessed.

## Why this was tried

Idea issue #2. The [relabelled cycle-25 diagnostic](cycle25-diagnostic-relabelled-20261112.md) (D5) found that 0.7139 and
0.7561 of the alert false-positive windows of 2022 and 2023 lie within 72 hours of a positive window of the same HARP,
but its 72-hour span is symmetric: it does not say whether those alarms come before the flaring or stay on after it.
Extra information ([SGAS flare history](activity-history-relabelled-20261112.md),
[zero-latency ceiling](history-latency-ceiling-20261112.md)) and a [wider horizon](horizon-72h-20261116.md) did not raise
alert precision. A cooldown needs no new information: it uses only the model's own past outputs. Earlier persistence
rules ([alarm persistence](alarm-persistence-results-20261107.md),
[threshold versus persistence](threshold-tradeoff-results-20261107.md)) were tested on the frozen-label basis and not at
the alert tier, and no cooldown was tested.

## What was run

One execution of the protocol exactly as merged, from `main` commit `746de33`, with 0 model fits, 2 cooldown candidates
and the descriptive direction split. Wall time 22 seconds.

```sh
OMP_NUM_THREADS=3 python -m scripts.audit_alert_cooldown --config config/alert-cooldown-v1.json --output artifacts/alert_cooldown_20261125_r1
```

| item | sha256 |
| --- | --- |
| `config/alert-cooldown-v1.json` | `ebae981393830c7b53ed1ff4cce68f8e9a4ebfcdb4b25c8e701fe76224053690` |
| `artifacts/walk_forward_v2_20261112_r1/report.json` (control) | `c2b326d90253e824e9dd324158933e01c1216788653b1d284bf22850f67f76f1` |
| `artifacts/relabelled_development_20261111_r1/report.json` (labels) | `2847215ce5a5dedb9ebb93d7fa0ba1bcb7b4a7bf9fdcd80bab95e63726b9ac43` |
| `artifacts/alert_cooldown_20261125_r1/selections.json` | `72baf0591439bf2a648d6fec4f8c9f0e843c838595a5c03ad209094f5ea17e87` |
| `artifacts/alert_cooldown_20261125_r1/report.json` | `f3e45dde103a13d21885e5469f2148db84947be5d36b7ab34812b0334fff6a6f` |
| `artifacts/alert_cooldown_20261125_r1/results.csv` | `f1d7a46ddb5c3bbb3301334c0d9b08340653618a9c5459e7e5024143bc66bb9e` |
| `artifacts/alert_cooldown_20261125_r1/intervals.csv` | `ba697747492632faefb613ff41a3ba20c9ec0cefc2cb50117002d40dcf5bbdb4` |
| `artifacts/alert_cooldown_20261125_r1/directions.csv` | `37e1a312fe8f6c6072cecd99cda9dbbc0272412635a8269e0a9415aa57c9ef7c` |
| `artifacts/alert_cooldown_20261125_r1/offset_quantiles.csv` | `03f4e5409ca8475c41e7d1ac24841e44e24cae1c7a3eab0a1eba909637e49d4e` |
| `artifacts/alert_cooldown_20261125_r1/offset_bins.csv` | `68119525a63277c2c06643071441d9aa4ddbdec9ec1e53d4b443a9a37b435674` |

The runner checked the control report, the per-year `predictions.parquet` and `thresholds.json` and every shard of the
relabelled table against their stored sha256 before use. `models.joblib` was never opened. The alert states of the control
and of both candidates and the stored thresholds were written to disk and hashed (`selections.json`) before any evaluation
label was read. The control reproduces the stored `alert_alarm` column exactly in every year.

## Method

Population: the evaluation windows of the control artifact, one per HARP and hour, for 2014, 2015, 2016, 2017, 2022 and
2023. 2022 is an alert fallback year: its stored alert threshold comes from the fallback rule of
`config/walk-forward-v2.json` and is marked in every table.

Candidates. `control`: alert when the stored ensemble probability is at or above the stored alert threshold of the year.
`cooldown_24h`: the alert is on when the probability is at or above the threshold and the run of consecutive hourly
windows of the HARP at or above the threshold is at most 24 long; from the 25th consecutive hour on the alert is
suppressed until one window falls below the threshold. `cooldown_48h`: the same rule with 48 hours. A gap in the hourly
windows of a HARP ends the run. The rule is causal: it uses only stored probabilities of the current and earlier windows
of the same HARP and the stored threshold, never a label, a later window or another HARP. No threshold is selected and
only the alert tier changes; the watch tier is the stored watch tier of the control.

Acceptance, identical to [`config/activity-history-v2.json`](../config/activity-history-v2.json): a candidate meets the
per-year primary acceptance when its alert precision is higher than the control, its missed positive runs are not above
the control and its window recall drops by at most 0.02. `all_year_primary`: this holds in all six years.
`cycle25_primary`: it holds in both 2022 and 2023. A candidate meets the goal when `all_year_primary` holds, or when
`cycle25_primary` holds and the lower bound of the paired HARP-cluster bootstrap interval of the precision difference
(1000 draws, seed 24, 2.5 and 97.5 percent quantiles) is above 0 in both 2022 and 2023.

Reading rule, applied in this order: `C1_goal_met` if at least one cooldown meets the goal; otherwise `C2_partial` if at
least one meets `cycle25_primary`; otherwise `C3_no_gain`.

Counts are overlapping hourly windows. A positive run is a contiguous group of positive windows of one HARP; an alert
episode is a contiguous group of alert windows of one HARP. Neither is an independent event.

## Alert tier

Precision is given with the delivered window recall and the missed positive runs. Intervals are HARP-cluster bootstrap
intervals of each candidate.

| year | candidate | fallback | alert threshold | TP | FP | FN | TN | recall | recall 95% interval | precision | precision 95% interval | accuracy | always-negative accuracy | alarm windows | alarmed positive runs | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 0.4627 | 688 | 320 | 1748 | 75595 | 0.2824 | [0.1030, 0.4369] | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 1008 | 22 | 66/88 |
| 2014 | `cooldown_24h` | no | 0.4627 | 398 | 240 | 2038 | 75675 | 0.1634 | [0.0698, 0.2416] | 0.6238 | [0.3550, 0.8386] | 0.9709 | 0.9689 | 638 | 20 | 68/88 |
| 2014 | `cooldown_48h` | no | 0.4627 | 516 | 298 | 1920 | 75617 | 0.2118 | [0.0878, 0.3180] | 0.6339 | [0.3897, 0.8268] | 0.9717 | 0.9689 | 814 | 21 | 67/88 |
| 2015 | `control` | no | 0.2631 | 545 | 457 | 916 | 68636 | 0.3730 | [0.1693, 0.5283] | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 1002 | 30 | 27/57 |
| 2015 | `cooldown_24h` | no | 0.2631 | 375 | 298 | 1086 | 68795 | 0.2567 | [0.1224, 0.3989] | 0.5572 | [0.3463, 0.7259] | 0.9804 | 0.9793 | 673 | 29 | 28/57 |
| 2015 | `cooldown_48h` | no | 0.2631 | 443 | 376 | 1018 | 68717 | 0.3032 | [0.1466, 0.4553] | 0.5409 | [0.3305, 0.7013] | 0.9802 | 0.9793 | 819 | 30 | 27/57 |
| 2016 | `control` | no | 0.2564 | 94 | 109 | 120 | 42819 | 0.4393 | [0.0000, 0.8506] | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 203 | 5 | 3/8 |
| 2016 | `cooldown_24h` | no | 0.2564 | 61 | 56 | 153 | 42872 | 0.2850 | [0.0000, 0.4713] | 0.5214 | [0.0000, 0.7731] | 0.9952 | 0.9950 | 117 | 5 | 3/8 |
| 2016 | `cooldown_48h` | no | 0.2564 | 91 | 56 | 123 | 42872 | 0.4252 | [0.0000, 0.8161] | 0.6190 | [0.0000, 0.8354] | 0.9959 | 0.9950 | 147 | 5 | 3/8 |
| 2017 | `control` | no | 0.4145 | 177 | 27 | 88 | 19551 | 0.6679 | [0.0000, 0.8535] | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 204 | 3 | 3/6 |
| 2017 | `cooldown_24h` | no | 0.4145 | 77 | 15 | 188 | 19563 | 0.2906 | [0.0000, 0.3846] | 0.8370 | [0.0000, 1.0000] | 0.9898 | 0.9866 | 92 | 3 | 3/6 |
| 2017 | `cooldown_48h` | no | 0.4145 | 119 | 21 | 146 | 19557 | 0.4491 | [0.0000, 0.6615] | 0.8500 | [0.0000, 1.0000] | 0.9916 | 0.9866 | 140 | 3 | 3/6 |
| 2022 | `control` | yes | 0.1570 | 1056 | 1178 | 1134 | 62225 | 0.4822 | [0.3268, 0.6058] | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 2234 | 40 | 32/72 |
| 2022 | `cooldown_24h` | yes | 0.1570 | 543 | 690 | 1647 | 62713 | 0.2479 | [0.1642, 0.3258] | 0.4404 | [0.3110, 0.5438] | 0.9644 | 0.9666 | 1233 | 34 | 38/72 |
| 2022 | `cooldown_48h` | yes | 0.1570 | 822 | 844 | 1368 | 62559 | 0.3753 | [0.2523, 0.4857] | 0.4934 | [0.3703, 0.5956] | 0.9663 | 0.9666 | 1666 | 39 | 33/72 |
| 2023 | `control` | no | 0.2689 | 1587 | 2136 | 2504 | 90764 | 0.3879 | [0.2918, 0.4663] | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 3723 | 91 | 68/159 |
| 2023 | `cooldown_24h` | no | 0.2689 | 1080 | 1501 | 3011 | 91399 | 0.2640 | [0.2080, 0.3180] | 0.4184 | [0.3420, 0.5027] | 0.9535 | 0.9578 | 2581 | 83 | 76/159 |
| 2023 | `cooldown_48h` | no | 0.2689 | 1364 | 1739 | 2727 | 91161 | 0.3334 | [0.2634, 0.3965] | 0.4396 | [0.3643, 0.5203] | 0.9540 | 0.9578 | 3103 | 86 | 73/159 |

## Acceptance

`precision difference` is candidate minus control. `recall drop` is control recall minus candidate recall. The interval
is the paired HARP-cluster bootstrap interval of the precision difference. In 2017 982 of the 1000 draws could be
used (a draw without any alert window of the control or of the candidate is skipped).

| year | candidate | fallback | control precision | candidate precision | precision difference | difference 95% interval | bootstrap draws used | recall drop | missed runs control | missed runs candidate | precision higher | missed runs not above | recall drop at most 0.02 | per-year primary met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `cooldown_24h` | no | 0.6825 | 0.6238 | -0.0587 | [-0.1312, 0.0360] | 1000 | 0.1190 | 66 | 68 | no | no | no | no |
| 2014 | `cooldown_48h` | no | 0.6825 | 0.6339 | -0.0486 | [-0.0802, -0.0041] | 1000 | 0.0706 | 66 | 67 | no | no | no | no |
| 2015 | `cooldown_24h` | no | 0.5439 | 0.5572 | 0.0133 | [-0.1480, 0.1566] | 1000 | 0.1164 | 27 | 28 | yes | no | no | no |
| 2015 | `cooldown_48h` | no | 0.5439 | 0.5409 | -0.0030 | [-0.1020, 0.0846] | 1000 | 0.0698 | 27 | 27 | no | yes | no | no |
| 2016 | `cooldown_24h` | no | 0.4631 | 0.5214 | 0.0583 | [-0.0134, 0.2090] | 1000 | 0.1542 | 3 | 3 | yes | yes | no | no |
| 2016 | `cooldown_48h` | no | 0.4631 | 0.6190 | 0.1560 | [0.0000, 0.2896] | 1000 | 0.0140 | 3 | 3 | yes | yes | yes | yes |
| 2017 | `cooldown_24h` | no | 0.8676 | 0.8370 | -0.0307 | [-0.1741, 0.2182] | 982 | 0.3774 | 3 | 3 | no | yes | no | no |
| 2017 | `cooldown_48h` | no | 0.8676 | 0.8500 | -0.0176 | [-0.0944, 0.0957] | 982 | 0.2189 | 3 | 3 | no | yes | no | no |
| 2022 | `cooldown_24h` | yes | 0.4727 | 0.4404 | -0.0323 | [-0.1195, 0.0360] | 1000 | 0.2342 | 32 | 38 | no | no | no | no |
| 2022 | `cooldown_48h` | yes | 0.4727 | 0.4934 | 0.0207 | [-0.0426, 0.0718] | 1000 | 0.1068 | 32 | 33 | yes | no | no | no |
| 2023 | `cooldown_24h` | no | 0.4263 | 0.4184 | -0.0078 | [-0.0553, 0.0349] | 1000 | 0.1239 | 68 | 76 | no | no | no | no |
| 2023 | `cooldown_48h` | no | 0.4263 | 0.4396 | 0.0133 | [-0.0191, 0.0414] | 1000 | 0.0545 | 68 | 73 | yes | no | no | no |

| candidate | years meeting per-year primary | all_year_primary | cycle25_primary | bootstrap lower bound above 0 in 2022 and 2023 | goal met | years with alert precision at least 0.50 (secondary) |
| --- | --- | --- | --- | --- | --- | --- |
| `control` |  |  |  |  |  | 2014, 2015, 2017 |
| `cooldown_24h` | none | no | no | no | no | 2014, 2015, 2016, 2017 |
| `cooldown_48h` | 2016 | no | no | no | no | 2014, 2015, 2016, 2017 |

Windows removed by each cooldown against the control:

| year | candidate | fallback | control alert windows | alert windows removed | TP windows removed | FP windows removed | FP share of removed windows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `cooldown_24h` | no | 1008 | 370 | 290 | 80 | 0.2162 |
| 2014 | `cooldown_48h` | no | 1008 | 194 | 172 | 22 | 0.1134 |
| 2015 | `cooldown_24h` | no | 1002 | 329 | 170 | 159 | 0.4833 |
| 2015 | `cooldown_48h` | no | 1002 | 183 | 102 | 81 | 0.4426 |
| 2016 | `cooldown_24h` | no | 203 | 86 | 33 | 53 | 0.6163 |
| 2016 | `cooldown_48h` | no | 203 | 56 | 3 | 53 | 0.9464 |
| 2017 | `cooldown_24h` | no | 204 | 112 | 100 | 12 | 0.1071 |
| 2017 | `cooldown_48h` | no | 204 | 64 | 58 | 6 | 0.0938 |
| 2022 | `cooldown_24h` | yes | 2234 | 1001 | 513 | 488 | 0.4875 |
| 2022 | `cooldown_48h` | yes | 2234 | 568 | 234 | 334 | 0.5880 |
| 2023 | `cooldown_24h` | no | 3723 | 1142 | 507 | 635 | 0.5560 |
| 2023 | `cooldown_48h` | no | 3723 | 620 | 223 | 397 | 0.6403 |

## Alert episodes and delay

A cooldown shortens episodes and never splits or adds one, so the number of alert episodes equals the control in every
year; the number of hit episodes cannot rise. Delay is in hours from the start of a positive run to its first alert
window, over the alarmed positive runs. The median delay is above the control in 2014, 2015, 2022, 2023 for `cooldown_24h`
and in 2014, 2023 for `cooldown_48h`.

| year | candidate | fallback | alert episodes | hit episodes | episode precision | median alert delay (h) | maximum alert delay (h) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 90 | 51 | 0.5667 | 1.5 | 28.0 |
| 2014 | `cooldown_24h` | no | 90 | 51 | 0.5667 | 6.5 | 32.0 |
| 2014 | `cooldown_48h` | no | 90 | 51 | 0.5667 | 2.0 | 28.0 |
| 2015 | `control` | no | 99 | 47 | 0.4747 | 0.0 | 30.0 |
| 2015 | `cooldown_24h` | no | 99 | 47 | 0.4747 | 3.0 | 30.0 |
| 2015 | `cooldown_48h` | no | 99 | 47 | 0.4747 | 0.0 | 30.0 |
| 2016 | `control` | no | 21 | 6 | 0.2857 | 1.0 | 14.0 |
| 2016 | `cooldown_24h` | no | 21 | 6 | 0.2857 | 1.0 | 14.0 |
| 2016 | `cooldown_48h` | no | 21 | 6 | 0.2857 | 1.0 | 14.0 |
| 2017 | `control` | no | 11 | 7 | 0.6364 | 2.0 | 21.0 |
| 2017 | `cooldown_24h` | no | 11 | 7 | 0.6364 | 2.0 | 21.0 |
| 2017 | `cooldown_48h` | no | 11 | 7 | 0.6364 | 2.0 | 21.0 |
| 2022 | `control` | yes | 139 | 51 | 0.3669 | 0.0 | 35.0 |
| 2022 | `cooldown_24h` | yes | 139 | 48 | 0.3453 | 0.5 | 69.0 |
| 2022 | `cooldown_48h` | yes | 139 | 50 | 0.3597 | 0.0 | 35.0 |
| 2023 | `control` | no | 358 | 137 | 0.3827 | 0.0 | 44.0 |
| 2023 | `cooldown_24h` | no | 358 | 134 | 0.3743 | 1.0 | 44.0 |
| 2023 | `cooldown_48h` | no | 358 | 137 | 0.3827 | 1.0 | 44.0 |

## Watch tier

The stored watch tier of the control, unchanged by any candidate and reported once.

| year | watch threshold | TP | FP | FN | TN | recall | recall 95% interval | precision | precision 95% interval | accuracy | always-negative accuracy | alarm windows | episodes | hit episodes | episode precision | median delay (h) | maximum delay (h) | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.0311 | 2146 | 9020 | 290 | 66895 | 0.8810 | [0.8065, 0.9357] | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 11166 | 561 | 87 | 0.1551 | 0.0 | 17.0 | 6/88 |
| 2015 | 0.0364 | 1396 | 8079 | 65 | 61014 | 0.9555 | [0.8917, 0.9971] | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 9475 | 460 | 44 | 0.0957 | 0.0 | 19.0 | 1/57 |
| 2016 | 0.0471 | 201 | 1722 | 13 | 41206 | 0.9393 | [0.4545, 1.0000] | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 1923 | 150 | 6 | 0.0400 | 0.0 | 9.0 | 0/8 |
| 2017 | 0.0270 | 243 | 1058 | 22 | 18520 | 0.9170 | [0.7692, 1.0000] | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1301 | 81 | 6 | 0.0741 | 0.0 | 15.0 | 1/6 |
| 2022 | 0.0183 | 2024 | 11917 | 166 | 51486 | 0.9242 | [0.8502, 0.9731] | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 13941 | 587 | 53 | 0.0903 | 0.0 | 8.0 | 5/72 |
| 2023 | 0.0405 | 3695 | 16022 | 396 | 76878 | 0.9032 | [0.8486, 0.9425] | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 19717 | 753 | 122 | 0.1620 | 0.0 | 22.0 | 10/159 |

Watch-tier accuracy is below the always-negative accuracy in every year.

## Direction of alert false positives (descriptive)

Frozen with the protocol; it has no reading rule, decides nothing and never feeds a candidate rule. It uses evaluation
labels. Every alert false-positive window falls in exactly one class, relative to the positive windows of the same HARP
in the evaluation population of the year: `never_flaring_harp` (the HARP has no positive window in the year), `early` (a
positive window more than 0 and at most 72 hours after it and none within 72 hours before), `lingering` (a positive
window more than 0 and at most 72 hours before it and none within 72 hours after), `between` (positive windows within
72 hours on both sides), `flaring_harp_other` (the HARP has a positive window in the year but none within 72 hours).
`control FP windows removed` counts the control false-positive windows of the class that the cooldown no longer alerts.

Over the six years the cooldowns remove these control false-positive windows per class (removed / control):
`cooldown_24h` `early` 115/817, `lingering` 736/1389, `between` 372/939, `flaring_harp_other` 128/587, `never_flaring_harp` 76/495; `cooldown_48h` `early` 59/817, `lingering` 525/1389, `between` 187/939, `flaring_harp_other` 102/587, `never_flaring_harp` 20/495.
The per-year values are in the table.

| year | candidate | fallback | class | FP windows | share of alert FP windows | HARPs | control FP windows removed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | `early` | 63 | 0.1969 | 4 |  |
| 2014 | `control` | no | `lingering` | 60 | 0.1875 | 8 |  |
| 2014 | `control` | no | `between` | 103 | 0.3219 | 8 |  |
| 2014 | `control` | no | `flaring_harp_other` | 48 | 0.1500 | 2 |  |
| 2014 | `control` | no | `never_flaring_harp` | 46 | 0.1437 | 3 |  |
| 2014 | `cooldown_24h` | no | `early` | 63 | 0.2625 | 4 | 0 |
| 2014 | `cooldown_24h` | no | `lingering` | 26 | 0.1083 | 8 | 34 |
| 2014 | `cooldown_24h` | no | `between` | 76 | 0.3167 | 6 | 27 |
| 2014 | `cooldown_24h` | no | `flaring_harp_other` | 48 | 0.2000 | 2 | 0 |
| 2014 | `cooldown_24h` | no | `never_flaring_harp` | 27 | 0.1125 | 3 | 19 |
| 2014 | `cooldown_48h` | no | `early` | 63 | 0.2114 | 4 | 0 |
| 2014 | `cooldown_48h` | no | `lingering` | 50 | 0.1678 | 8 | 10 |
| 2014 | `cooldown_48h` | no | `between` | 91 | 0.3054 | 8 | 12 |
| 2014 | `cooldown_48h` | no | `flaring_harp_other` | 48 | 0.1611 | 2 | 0 |
| 2014 | `cooldown_48h` | no | `never_flaring_harp` | 46 | 0.1544 | 3 | 0 |
| 2015 | `control` | no | `early` | 85 | 0.1860 | 8 |  |
| 2015 | `control` | no | `lingering` | 177 | 0.3873 | 8 |  |
| 2015 | `control` | no | `between` | 115 | 0.2516 | 6 |  |
| 2015 | `control` | no | `flaring_harp_other` | 41 | 0.0897 | 3 |  |
| 2015 | `control` | no | `never_flaring_harp` | 39 | 0.0853 | 6 |  |
| 2015 | `cooldown_24h` | no | `early` | 85 | 0.2852 | 8 | 0 |
| 2015 | `cooldown_24h` | no | `lingering` | 77 | 0.2584 | 7 | 100 |
| 2015 | `cooldown_24h` | no | `between` | 62 | 0.2081 | 6 | 53 |
| 2015 | `cooldown_24h` | no | `flaring_harp_other` | 35 | 0.1174 | 3 | 6 |
| 2015 | `cooldown_24h` | no | `never_flaring_harp` | 39 | 0.1309 | 6 | 0 |
| 2015 | `cooldown_48h` | no | `early` | 85 | 0.2261 | 8 | 0 |
| 2015 | `cooldown_48h` | no | `lingering` | 124 | 0.3298 | 8 | 53 |
| 2015 | `cooldown_48h` | no | `between` | 93 | 0.2473 | 6 | 22 |
| 2015 | `cooldown_48h` | no | `flaring_harp_other` | 35 | 0.0931 | 3 | 6 |
| 2015 | `cooldown_48h` | no | `never_flaring_harp` | 39 | 0.1037 | 6 | 0 |
| 2016 | `control` | no | `early` | 0 | 0.0000 | 0 |  |
| 2016 | `control` | no | `lingering` | 53 | 0.4862 | 1 |  |
| 2016 | `control` | no | `between` | 9 | 0.0826 | 1 |  |
| 2016 | `control` | no | `flaring_harp_other` | 19 | 0.1743 | 1 |  |
| 2016 | `control` | no | `never_flaring_harp` | 28 | 0.2569 | 7 |  |
| 2016 | `cooldown_24h` | no | `early` | 0 | 0.0000 | 0 | 0 |
| 2016 | `cooldown_24h` | no | `lingering` | 0 | 0.0000 | 0 | 53 |
| 2016 | `cooldown_24h` | no | `between` | 9 | 0.1607 | 1 | 0 |
| 2016 | `cooldown_24h` | no | `flaring_harp_other` | 19 | 0.3393 | 1 | 0 |
| 2016 | `cooldown_24h` | no | `never_flaring_harp` | 28 | 0.5000 | 7 | 0 |
| 2016 | `cooldown_48h` | no | `early` | 0 | 0.0000 | 0 | 0 |
| 2016 | `cooldown_48h` | no | `lingering` | 0 | 0.0000 | 0 | 53 |
| 2016 | `cooldown_48h` | no | `between` | 9 | 0.1607 | 1 | 0 |
| 2016 | `cooldown_48h` | no | `flaring_harp_other` | 19 | 0.3393 | 1 | 0 |
| 2016 | `cooldown_48h` | no | `never_flaring_harp` | 28 | 0.5000 | 7 | 0 |
| 2017 | `control` | no | `early` | 0 | 0.0000 | 0 |  |
| 2017 | `control` | no | `lingering` | 24 | 0.8889 | 2 |  |
| 2017 | `control` | no | `between` | 0 | 0.0000 | 0 |  |
| 2017 | `control` | no | `flaring_harp_other` | 0 | 0.0000 | 0 |  |
| 2017 | `control` | no | `never_flaring_harp` | 3 | 0.1111 | 1 |  |
| 2017 | `cooldown_24h` | no | `early` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_24h` | no | `lingering` | 12 | 0.8000 | 1 | 12 |
| 2017 | `cooldown_24h` | no | `between` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_24h` | no | `flaring_harp_other` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_24h` | no | `never_flaring_harp` | 3 | 0.2000 | 1 | 0 |
| 2017 | `cooldown_48h` | no | `early` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_48h` | no | `lingering` | 18 | 0.8571 | 2 | 6 |
| 2017 | `cooldown_48h` | no | `between` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_48h` | no | `flaring_harp_other` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_48h` | no | `never_flaring_harp` | 3 | 0.1429 | 1 | 0 |
| 2022 | `control` | yes | `early` | 180 | 0.1528 | 11 |  |
| 2022 | `control` | yes | `lingering` | 369 | 0.3132 | 15 |  |
| 2022 | `control` | yes | `between` | 292 | 0.2479 | 12 |  |
| 2022 | `control` | yes | `flaring_harp_other` | 240 | 0.2037 | 9 |  |
| 2022 | `control` | yes | `never_flaring_harp` | 97 | 0.0823 | 11 |  |
| 2022 | `cooldown_24h` | yes | `early` | 124 | 0.1797 | 11 | 56 |
| 2022 | `cooldown_24h` | yes | `lingering` | 109 | 0.1580 | 10 | 260 |
| 2022 | `cooldown_24h` | yes | `between` | 207 | 0.3000 | 10 | 85 |
| 2022 | `cooldown_24h` | yes | `flaring_harp_other` | 153 | 0.2217 | 8 | 87 |
| 2022 | `cooldown_24h` | yes | `never_flaring_harp` | 97 | 0.1406 | 11 | 0 |
| 2022 | `cooldown_48h` | yes | `early` | 153 | 0.1813 | 11 | 27 |
| 2022 | `cooldown_48h` | yes | `lingering` | 155 | 0.1836 | 13 | 214 |
| 2022 | `cooldown_48h` | yes | `between` | 284 | 0.3365 | 12 | 8 |
| 2022 | `cooldown_48h` | yes | `flaring_harp_other` | 155 | 0.1836 | 8 | 85 |
| 2022 | `cooldown_48h` | yes | `never_flaring_harp` | 97 | 0.1149 | 11 | 0 |
| 2023 | `control` | no | `early` | 489 | 0.2289 | 24 |  |
| 2023 | `control` | no | `lingering` | 706 | 0.3305 | 31 |  |
| 2023 | `control` | no | `between` | 420 | 0.1966 | 25 |  |
| 2023 | `control` | no | `flaring_harp_other` | 239 | 0.1119 | 17 |  |
| 2023 | `control` | no | `never_flaring_harp` | 282 | 0.1320 | 11 |  |
| 2023 | `cooldown_24h` | no | `early` | 430 | 0.2865 | 24 | 59 |
| 2023 | `cooldown_24h` | no | `lingering` | 429 | 0.2858 | 31 | 277 |
| 2023 | `cooldown_24h` | no | `between` | 213 | 0.1419 | 22 | 207 |
| 2023 | `cooldown_24h` | no | `flaring_harp_other` | 204 | 0.1359 | 17 | 35 |
| 2023 | `cooldown_24h` | no | `never_flaring_harp` | 225 | 0.1499 | 11 | 57 |
| 2023 | `cooldown_48h` | no | `early` | 457 | 0.2628 | 24 | 32 |
| 2023 | `cooldown_48h` | no | `lingering` | 517 | 0.2973 | 31 | 189 |
| 2023 | `cooldown_48h` | no | `between` | 275 | 0.1581 | 22 | 145 |
| 2023 | `cooldown_48h` | no | `flaring_harp_other` | 228 | 0.1311 | 17 | 11 |
| 2023 | `cooldown_48h` | no | `never_flaring_harp` | 262 | 0.1507 | 11 | 20 |

Hour offsets of the false-positive windows of flaring HARPs. `hours_since_last_positive` and `hours_to_next_positive`
exist only where the HARP has an earlier or a later positive window in the year; `hours_to_nearest_positive` is the
smaller of the two.

| year | candidate | measure | windows | minimum | q10 | q25 | median | q75 | q90 | maximum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | `hours_since_last_positive` | 251 | 1.0 | 3.0 | 8.00 | 24.0 | 126.00 | 149.0 | 174.0 |
| 2014 | `control` | `hours_to_next_positive` | 168 | 1.0 | 3.0 | 6.00 | 18.5 | 30.25 | 46.3 | 73.0 |
| 2014 | `control` | `hours_to_nearest_positive` | 274 | 1.0 | 2.0 | 5.25 | 15.0 | 36.00 | 127.7 | 174.0 |
| 2014 | `cooldown_24h` | `hours_since_last_positive` | 190 | 1.0 | 3.0 | 10.00 | 49.0 | 134.75 | 153.1 | 174.0 |
| 2014 | `cooldown_24h` | `hours_to_next_positive` | 141 | 1.0 | 4.0 | 11.00 | 19.0 | 34.00 | 49.0 | 73.0 |
| 2014 | `cooldown_24h` | `hours_to_nearest_positive` | 213 | 1.0 | 2.0 | 6.00 | 16.0 | 54.00 | 133.8 | 174.0 |
| 2014 | `cooldown_48h` | `hours_since_last_positive` | 229 | 1.0 | 3.0 | 9.00 | 24.0 | 130.00 | 150.2 | 174.0 |
| 2014 | `cooldown_48h` | `hours_to_next_positive` | 156 | 1.0 | 3.0 | 10.00 | 19.5 | 32.00 | 47.5 | 73.0 |
| 2014 | `cooldown_48h` | `hours_to_nearest_positive` | 252 | 1.0 | 2.0 | 6.00 | 15.0 | 42.25 | 129.9 | 174.0 |
| 2015 | `control` | `hours_since_last_positive` | 334 | 1.0 | 3.0 | 7.00 | 20.0 | 49.75 | 93.7 | 224.0 |
| 2015 | `control` | `hours_to_next_positive` | 200 | 1.0 | 2.9 | 6.75 | 13.0 | 26.00 | 34.0 | 67.0 |
| 2015 | `control` | `hours_to_nearest_positive` | 418 | 1.0 | 2.0 | 6.00 | 16.0 | 39.00 | 71.3 | 224.0 |
| 2015 | `cooldown_24h` | `hours_since_last_positive` | 175 | 1.0 | 2.0 | 5.00 | 12.0 | 32.50 | 200.6 | 224.0 |
| 2015 | `cooldown_24h` | `hours_to_next_positive` | 147 | 1.0 | 3.0 | 7.00 | 14.0 | 26.50 | 35.4 | 67.0 |
| 2015 | `cooldown_24h` | `hours_to_nearest_positive` | 259 | 1.0 | 2.0 | 5.00 | 13.0 | 28.00 | 108.2 | 224.0 |
| 2015 | `cooldown_48h` | `hours_since_last_positive` | 253 | 1.0 | 3.0 | 6.00 | 12.0 | 37.00 | 109.8 | 224.0 |
| 2015 | `cooldown_48h` | `hours_to_next_positive` | 178 | 1.0 | 2.7 | 7.00 | 14.5 | 27.00 | 35.0 | 67.0 |
| 2015 | `cooldown_48h` | `hours_to_nearest_positive` | 337 | 1.0 | 2.0 | 5.00 | 13.0 | 29.00 | 92.4 | 224.0 |
| 2016 | `control` | `hours_since_last_positive` | 62 | 1.0 | 3.0 | 7.25 | 22.5 | 37.75 | 46.9 | 53.0 |
| 2016 | `control` | `hours_to_next_positive` | 28 | 1.0 | 2.0 | 4.00 | 164.5 | 171.25 | 184.9 | 217.0 |
| 2016 | `control` | `hours_to_nearest_positive` | 81 | 1.0 | 2.0 | 12.00 | 32.0 | 52.00 | 170.0 | 217.0 |
| 2016 | `cooldown_24h` | `hours_since_last_positive` | 9 | 1.0 | 1.0 | 2.00 | 3.0 | 4.00 | 4.2 | 5.0 |
| 2016 | `cooldown_24h` | `hours_to_next_positive` | 28 | 1.0 | 2.0 | 4.00 | 164.5 | 171.25 | 184.9 | 217.0 |
| 2016 | `cooldown_24h` | `hours_to_nearest_positive` | 28 | 1.0 | 1.0 | 2.00 | 164.5 | 171.25 | 184.9 | 217.0 |
| 2016 | `cooldown_48h` | `hours_since_last_positive` | 9 | 1.0 | 1.0 | 2.00 | 3.0 | 4.00 | 4.2 | 5.0 |
| 2016 | `cooldown_48h` | `hours_to_next_positive` | 28 | 1.0 | 2.0 | 4.00 | 164.5 | 171.25 | 184.9 | 217.0 |
| 2016 | `cooldown_48h` | `hours_to_nearest_positive` | 28 | 1.0 | 1.0 | 2.00 | 164.5 | 171.25 | 184.9 | 217.0 |
| 2017 | `control` | `hours_since_last_positive` | 24 | 1.0 | 2.0 | 3.75 | 6.5 | 10.00 | 14.8 | 18.0 |
| 2017 | `control` | `hours_to_next_positive` | 12 | 83.0 | 84.1 | 89.50 | 94.5 | 97.25 | 98.9 | 100.0 |
| 2017 | `control` | `hours_to_nearest_positive` | 24 | 1.0 | 2.0 | 3.75 | 6.5 | 10.00 | 14.8 | 18.0 |
| 2017 | `cooldown_24h` | `hours_since_last_positive` | 12 | 1.0 | 2.1 | 3.75 | 6.5 | 11.50 | 16.9 | 18.0 |
| 2017 | `cooldown_24h` | `hours_to_next_positive` | 12 | 83.0 | 84.1 | 89.50 | 94.5 | 97.25 | 98.9 | 100.0 |
| 2017 | `cooldown_24h` | `hours_to_nearest_positive` | 12 | 1.0 | 2.1 | 3.75 | 6.5 | 11.50 | 16.9 | 18.0 |
| 2017 | `cooldown_48h` | `hours_since_last_positive` | 18 | 1.0 | 1.7 | 3.00 | 5.0 | 7.75 | 16.3 | 18.0 |
| 2017 | `cooldown_48h` | `hours_to_next_positive` | 12 | 83.0 | 84.1 | 89.50 | 94.5 | 97.25 | 98.9 | 100.0 |
| 2017 | `cooldown_48h` | `hours_to_nearest_positive` | 18 | 1.0 | 1.7 | 3.00 | 5.0 | 7.75 | 16.3 | 18.0 |
| 2022 | `control` | `hours_since_last_positive` | 909 | 1.0 | 5.0 | 12.00 | 33.0 | 79.00 | 157.2 | 221.0 |
| 2022 | `control` | `hours_to_next_positive` | 595 | 1.0 | 4.0 | 10.00 | 31.0 | 63.00 | 117.0 | 286.0 |
| 2022 | `control` | `hours_to_nearest_positive` | 1081 | 1.0 | 3.0 | 9.00 | 26.0 | 64.00 | 112.0 | 286.0 |
| 2022 | `cooldown_24h` | `hours_since_last_positive` | 428 | 1.0 | 5.0 | 11.75 | 27.5 | 75.00 | 156.0 | 193.0 |
| 2022 | `cooldown_24h` | `hours_to_next_positive` | 449 | 1.0 | 4.0 | 13.00 | 41.0 | 75.00 | 127.2 | 286.0 |
| 2022 | `cooldown_24h` | `hours_to_nearest_positive` | 593 | 1.0 | 3.0 | 9.00 | 25.0 | 74.00 | 114.8 | 286.0 |
| 2022 | `cooldown_48h` | `hours_since_last_positive` | 575 | 1.0 | 4.0 | 9.00 | 27.0 | 64.50 | 160.6 | 194.0 |
| 2022 | `cooldown_48h` | `hours_to_next_positive` | 560 | 1.0 | 4.0 | 10.00 | 34.0 | 66.00 | 119.1 | 286.0 |
| 2022 | `cooldown_48h` | `hours_to_nearest_positive` | 747 | 1.0 | 3.0 | 7.00 | 20.0 | 55.00 | 101.0 | 286.0 |
| 2023 | `control` | `hours_since_last_positive` | 1341 | 1.0 | 4.0 | 11.00 | 28.0 | 58.00 | 91.0 | 193.0 |
| 2023 | `control` | `hours_to_next_positive` | 1409 | 1.0 | 6.8 | 17.00 | 49.0 | 95.00 | 174.2 | 248.0 |
| 2023 | `control` | `hours_to_nearest_positive` | 1854 | 1.0 | 4.0 | 9.00 | 22.5 | 50.00 | 83.0 | 213.0 |
| 2023 | `cooldown_24h` | `hours_since_last_positive` | 835 | 1.0 | 4.0 | 10.50 | 30.0 | 70.00 | 115.0 | 193.0 |
| 2023 | `cooldown_24h` | `hours_to_next_positive` | 945 | 1.0 | 6.0 | 15.00 | 38.0 | 89.00 | 152.0 | 248.0 |
| 2023 | `cooldown_24h` | `hours_to_nearest_positive` | 1276 | 1.0 | 4.0 | 9.00 | 22.0 | 57.00 | 99.5 | 213.0 |
| 2023 | `cooldown_48h` | `hours_since_last_positive` | 985 | 1.0 | 4.0 | 11.00 | 27.0 | 63.00 | 111.0 | 193.0 |
| 2023 | `cooldown_48h` | `hours_to_next_positive` | 1120 | 1.0 | 6.9 | 16.75 | 46.0 | 93.00 | 158.0 | 248.0 |
| 2023 | `cooldown_48h` | `hours_to_nearest_positive` | 1477 | 1.0 | 4.0 | 9.00 | 22.0 | 54.00 | 94.0 | 213.0 |

Counts of the same offsets in fixed bins of hours:

| year | candidate | measure | (0,6] | (6,12] | (12,24] | (24,48] | (48,72] | (72,120] | above 120 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | `hours_since_last_positive` | 53 | 35 | 40 | 28 | 7 | 15 | 73 |
| 2014 | `control` | `hours_to_next_positive` | 43 | 16 | 53 | 41 | 13 | 2 | 0 |
| 2014 | `control` | `hours_to_nearest_positive` | 77 | 47 | 58 | 35 | 9 | 14 | 34 |
| 2014 | `cooldown_24h` | `hours_since_last_positive` | 32 | 27 | 20 | 16 | 7 | 15 | 73 |
| 2014 | `cooldown_24h` | `hours_to_next_positive` | 27 | 15 | 47 | 37 | 13 | 2 | 0 |
| 2014 | `cooldown_24h` | `hours_to_nearest_positive` | 56 | 39 | 38 | 23 | 9 | 14 | 34 |
| 2014 | `cooldown_48h` | `hours_since_last_positive` | 41 | 35 | 40 | 18 | 7 | 15 | 73 |
| 2014 | `cooldown_48h` | `hours_to_next_positive` | 32 | 15 | 53 | 41 | 13 | 2 | 0 |
| 2014 | `cooldown_48h` | `hours_to_nearest_positive` | 65 | 47 | 58 | 25 | 9 | 14 | 34 |
| 2015 | `control` | `hours_since_last_positive` | 77 | 55 | 49 | 67 | 44 | 21 | 21 |
| 2015 | `control` | `hours_to_next_positive` | 50 | 42 | 55 | 45 | 8 | 0 | 0 |
| 2015 | `control` | `hours_to_nearest_positive` | 118 | 62 | 77 | 75 | 45 | 21 | 20 |
| 2015 | `cooldown_24h` | `hours_since_last_positive` | 56 | 36 | 24 | 17 | 6 | 15 | 21 |
| 2015 | `cooldown_24h` | `hours_to_next_positive` | 34 | 32 | 40 | 33 | 8 | 0 | 0 |
| 2015 | `cooldown_24h` | `hours_to_nearest_positive` | 84 | 43 | 53 | 37 | 7 | 15 | 20 |
| 2015 | `cooldown_48h` | `hours_since_last_positive` | 72 | 55 | 43 | 31 | 16 | 15 | 21 |
| 2015 | `cooldown_48h` | `hours_to_next_positive` | 44 | 34 | 47 | 45 | 8 | 0 | 0 |
| 2015 | `cooldown_48h` | `hours_to_nearest_positive` | 107 | 56 | 71 | 51 | 17 | 15 | 20 |
| 2016 | `control` | `hours_since_last_positive` | 15 | 6 | 12 | 24 | 5 | 0 | 0 |
| 2016 | `control` | `hours_to_next_positive` | 9 | 0 | 0 | 0 | 0 | 2 | 17 |
| 2016 | `control` | `hours_to_nearest_positive` | 15 | 6 | 12 | 24 | 5 | 2 | 17 |
| 2016 | `cooldown_24h` | `hours_since_last_positive` | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2016 | `cooldown_24h` | `hours_to_next_positive` | 9 | 0 | 0 | 0 | 0 | 2 | 17 |
| 2016 | `cooldown_24h` | `hours_to_nearest_positive` | 9 | 0 | 0 | 0 | 0 | 2 | 17 |
| 2016 | `cooldown_48h` | `hours_since_last_positive` | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2016 | `cooldown_48h` | `hours_to_next_positive` | 9 | 0 | 0 | 0 | 0 | 2 | 17 |
| 2016 | `cooldown_48h` | `hours_to_nearest_positive` | 9 | 0 | 0 | 0 | 0 | 2 | 17 |
| 2017 | `control` | `hours_since_last_positive` | 12 | 9 | 3 | 0 | 0 | 0 | 0 |
| 2017 | `control` | `hours_to_next_positive` | 0 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2017 | `control` | `hours_to_nearest_positive` | 12 | 9 | 3 | 0 | 0 | 0 | 0 |
| 2017 | `cooldown_24h` | `hours_since_last_positive` | 6 | 3 | 3 | 0 | 0 | 0 | 0 |
| 2017 | `cooldown_24h` | `hours_to_next_positive` | 0 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2017 | `cooldown_24h` | `hours_to_nearest_positive` | 6 | 3 | 3 | 0 | 0 | 0 | 0 |
| 2017 | `cooldown_48h` | `hours_since_last_positive` | 12 | 3 | 3 | 0 | 0 | 0 | 0 |
| 2017 | `cooldown_48h` | `hours_to_next_positive` | 0 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2017 | `cooldown_48h` | `hours_to_nearest_positive` | 12 | 3 | 3 | 0 | 0 | 0 | 0 |
| 2022 | `control` | `hours_since_last_positive` | 127 | 102 | 125 | 219 | 88 | 92 | 156 |
| 2022 | `control` | `hours_to_next_positive` | 103 | 64 | 89 | 138 | 78 | 68 | 55 |
| 2022 | `control` | `hours_to_nearest_positive` | 214 | 140 | 162 | 219 | 106 | 149 | 91 |
| 2022 | `cooldown_24h` | `hours_since_last_positive` | 57 | 58 | 75 | 99 | 27 | 44 | 68 |
| 2022 | `cooldown_24h` | `hours_to_next_positive` | 68 | 40 | 60 | 90 | 73 | 66 | 52 |
| 2022 | `cooldown_24h` | `hours_to_nearest_positive` | 115 | 84 | 93 | 106 | 42 | 99 | 54 |
| 2022 | `cooldown_48h` | `hours_since_last_positive` | 103 | 79 | 83 | 147 | 27 | 44 | 92 |
| 2022 | `cooldown_48h` | `hours_to_next_positive` | 97 | 58 | 69 | 135 | 78 | 68 | 55 |
| 2022 | `cooldown_48h` | `hours_to_nearest_positive` | 184 | 111 | 108 | 144 | 45 | 101 | 54 |
| 2023 | `control` | `hours_since_last_positive` | 196 | 183 | 240 | 300 | 207 | 145 | 70 |
| 2023 | `control` | `hours_to_next_positive` | 141 | 126 | 199 | 236 | 207 | 235 | 265 |
| 2023 | `control` | `hours_to_nearest_positive` | 322 | 281 | 370 | 400 | 242 | 152 | 87 |
| 2023 | `cooldown_24h` | `hours_since_last_positive` | 131 | 119 | 129 | 153 | 110 | 123 | 70 |
| 2023 | `cooldown_24h` | `hours_to_next_positive` | 101 | 103 | 151 | 169 | 119 | 156 | 146 |
| 2023 | `cooldown_24h` | `hours_to_nearest_positive` | 224 | 202 | 246 | 238 | 162 | 117 | 87 |
| 2023 | `cooldown_48h` | `hours_since_last_positive` | 151 | 143 | 175 | 189 | 134 | 123 | 70 |
| 2023 | `cooldown_48h` | `hours_to_next_positive` | 112 | 104 | 163 | 196 | 157 | 202 | 186 |
| 2023 | `cooldown_48h` | `hours_to_nearest_positive` | 255 | 227 | 300 | 283 | 184 | 141 | 87 |

One row per control alert false-positive window, with its class, both offsets and whether each candidate keeps the
alert, is stored in `artifacts/alert_cooldown_20261125_r1/control_fp_windows_<year>.parquet`.

## Frozen-label results

Kept visible for comparison, copied from the `alert_0.5` rows of the [frozen-label two-tier report](two-tier-20261110.md)
and not recomputed: the alert tier on frozen labels, before the basis changed. No cooldown was run on frozen labels, and
the values are not comparable with the tables above because the labels differ.

| year | fallback | threshold | TP | FP | FN | recall | precision | precision 95% interval | accuracy | always-negative accuracy | alarm windows | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | no | 0.4743 | 644 | 248 | 1666 | 0.2788 | 0.7220 | [0.4414, 0.8625] | 0.9746 | 0.9693 | 892 | 63/83 |
| 2015 | no | 0.2578 | 551 | 476 | 804 | 0.4066 | 0.5365 | [0.3109, 0.7080] | 0.9815 | 0.9804 | 1027 | 24/51 |
| 2016 | no | 0.2515 | 76 | 112 | 105 | 0.4199 | 0.4043 | [0.0000, 0.5249] | 0.9950 | 0.9958 | 188 | 2/7 |
| 2017 | no | 0.3397 | 182 | 43 | 71 | 0.7194 | 0.8089 | [0.0000, 0.9691] | 0.9942 | 0.9870 | 225 | 2/6 |
| 2022 | yes | 0.0931 | 221 | 1111 | 200 | 0.5249 | 0.1659 | [0.0725, 0.2543] | 0.9742 | 0.9917 | 1332 | 2/16 |
| 2023 | no | 0.3538 | 79 | 106 | 702 | 0.1012 | 0.4270 | [0.0968, 0.7441] | 0.9866 | 0.9871 | 185 | 30/38 |

## Limits

Already inspected years: adaptive development evidence, not an independent test. A cooldown only removes alert windows:
window recall cannot rise, missed positive runs cannot fall and the alert delay cannot shorten, so the only possible
gain was precision. Consecutive hourly windows overlap in 23 of their 24 hours and HARPs repeat, so counts are windows
and positive runs, never independent events, and intervals are HARP-clustered. 2016 and 2017 have few positive runs
(8 and 6), and their intervals are wide; the single per-year acceptance of `cooldown_48h` in 2016 rests on
147 alert windows. The direction classes use evaluation labels and are censored at the edges of the evaluation
population (the start and end of a HARP's stored windows and of the year), so a flare just outside can make a window
look unrelated. Classes are relative to positive windows, not to flare peak times. The relabelled labels are an
association by NOAA SGAS and JSOC `NOAA_ARS`, not ground truth. Two cooldown lengths were fixed in advance; no other
length was tried, and none may be chosen from these results. 2022 is an alert fallback year.

## Reproduction

```sh
bash agents/bin/evidence.sh seed
OMP_NUM_THREADS=3 python -m scripts.audit_alert_cooldown --config config/alert-cooldown-v1.json --output artifacts/<new directory>
python agents/bin/hale_call.py interpret_result '{"protocol": "config/alert-cooldown-v1.json", "artifact": "artifacts/<new directory>"}'
```

Config sha256 `ebae981393830c7b53ed1ff4cce68f8e9a4ebfcdb4b25c8e701fe76224053690`; selections sha256
`72baf0591439bf2a648d6fec4f8c9f0e843c838595a5c03ad209094f5ea17e87`; `report.json` sha256
`f3e45dde103a13d21885e5469f2148db84947be5d36b7ab34812b0334fff6a6f`. Use a new output directory; the runner refuses to
overwrite an existing one.
