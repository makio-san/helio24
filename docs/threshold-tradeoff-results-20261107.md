# Threshold versus persistence results: persistence adds no value, fixed multipliers are not robust

## Decision and scope

The [frozen protocol](threshold-tradeoff-protocol-20261107.md) was run once on the frozen annual predictions and
thresholds of the completed seven-year comparison (source report SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`; persistence report SHA256
`242b78592fb9c64d1a20809be5179874783bde54a7bc4731fc960fa43841f175`). No model was trained, no label changed
and the reserved 2024–2025 test stayed closed. No fix or change was made during this run. The unchanged control
and both persistence rules reproduce the earlier results exactly in every year and arm.

Decisions:

1. Persistence does not add value over raising the threshold. At the same recall as persistence, an oracle
   threshold has fewer or equal false-alarm windows in all six positive years for both k on the baseline arm.
2. No fixed multiplier of the frozen threshold passes in all six positive years (baseline 2, 3 and 3 years of 6).
   Nothing is adopted.
3. Inside the frozen recall tolerance an oracle threshold would leave large false-alarm headroom, but it uses
   evaluation labels and is not deployable.

## Deployable multipliers

| arm | candidate | years_met | required_years | result |
| --- | --- | --- | --- | --- |
| baseline | mult_1.25 | 2 | 6 | fail |
| baseline | mult_1.5 | 3 | 6 | fail |
| baseline | mult_2.0 | 3 | 6 | fail |
| chronological | mult_1.25 | 4 | 6 | fail |
| chronological | mult_1.5 | 4 | 6 | fail |
| chronological | mult_2.0 | 2 | 6 | fail |

A multiplier passes only if all four per-year conditions hold in all six positive years.

Baseline arm against the unchanged control:

| year | candidate | threshold | recall | recall_drop | fp | episodes | episode_precision | positive_runs_alarmed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 0.011475 | 0.945455 | 0.000000 | 13886 | 686 | 0.097668 | 80 |
| 2014 | mult_1.25 | 0.014344 | 0.938528 | 0.006926 | 12493 | 644 | 0.105590 | 79 |
| 2014 | mult_1.5 | 0.017213 | 0.928139 | 0.017316 | 11307 | 597 | 0.112228 | 79 |
| 2014 | mult_2.0 | 0.022950 | 0.910823 | 0.034632 | 9515 | 570 | 0.121053 | 78 |
| 2015 | control | 0.018839 | 0.993358 | 0.000000 | 11453 | 568 | 0.066901 | 51 |
| 2015 | mult_1.25 | 0.023549 | 0.991144 | 0.002214 | 9926 | 503 | 0.077535 | 51 |
| 2015 | mult_1.5 | 0.028259 | 0.989668 | 0.003690 | 8711 | 464 | 0.084052 | 51 |
| 2015 | mult_2.0 | 0.037678 | 0.977860 | 0.015498 | 6729 | 392 | 0.107143 | 51 |
| 2016 | control | 0.030831 | 0.972376 | 0.000000 | 2289 | 204 | 0.019608 | 7 |
| 2016 | mult_1.25 | 0.038539 | 0.944751 | 0.027624 | 1796 | 180 | 0.027778 | 7 |
| 2016 | mult_1.5 | 0.046246 | 0.928177 | 0.044199 | 1518 | 147 | 0.040816 | 7 |
| 2016 | mult_2.0 | 0.061662 | 0.889503 | 0.082873 | 1122 | 123 | 0.040650 | 7 |
| 2017 | control | 0.012000 | 0.936759 | 0.000000 | 1287 | 85 | 0.058824 | 5 |
| 2017 | mult_1.25 | 0.015000 | 0.932806 | 0.003953 | 1204 | 87 | 0.057471 | 5 |
| 2017 | mult_1.5 | 0.018000 | 0.932806 | 0.003953 | 1118 | 81 | 0.061728 | 5 |
| 2017 | mult_2.0 | 0.024000 | 0.928854 | 0.007905 | 998 | 61 | 0.081967 | 5 |
| 2018 | control | 0.004351 | undefined | 0.000000 | 359 | 30 | 0.000000 | 0 |
| 2018 | mult_1.25 | 0.005439 | undefined | undefined | 305 | 20 | 0.000000 | 0 |
| 2018 | mult_1.5 | 0.006527 | undefined | undefined | 265 | 18 | 0.000000 | 0 |
| 2018 | mult_2.0 | 0.008702 | undefined | undefined | 204 | 23 | 0.000000 | 0 |
| 2022 | control | 0.008994 | 0.985748 | 0.000000 | 10072 | 622 | 0.025723 | 16 |
| 2022 | mult_1.25 | 0.011242 | 0.983373 | 0.002375 | 8819 | 540 | 0.031481 | 16 |
| 2022 | mult_1.5 | 0.013491 | 0.976247 | 0.009501 | 7917 | 477 | 0.035639 | 16 |
| 2022 | mult_2.0 | 0.017988 | 0.966746 | 0.019002 | 6640 | 410 | 0.036585 | 16 |
| 2023 | control | 0.018203 | 0.884763 | 0.000000 | 5992 | 475 | 0.084211 | 36 |
| 2023 | mult_1.25 | 0.022754 | 0.847631 | 0.037132 | 5103 | 441 | 0.092971 | 36 |
| 2023 | mult_1.5 | 0.027305 | 0.820743 | 0.064020 | 4423 | 397 | 0.093199 | 33 |
| 2023 | mult_2.0 | 0.036407 | 0.740077 | 0.144686 | 3443 | 373 | 0.120643 | 33 |

`recall_drop` is the control recall minus the candidate recall.

| year | candidate | episode_precision_higher | fp_lower | positive_runs_alarmed_not_below | recall_drop_ok | primary_met |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | mult_1.25 | yes | yes | no | yes | no |
| 2014 | mult_1.5 | yes | yes | no | yes | no |
| 2014 | mult_2.0 | yes | yes | no | no | no |
| 2015 | mult_1.25 | yes | yes | yes | yes | yes |
| 2015 | mult_1.5 | yes | yes | yes | yes | yes |
| 2015 | mult_2.0 | yes | yes | yes | yes | yes |
| 2016 | mult_1.25 | yes | yes | yes | no | no |
| 2016 | mult_1.5 | yes | yes | yes | no | no |
| 2016 | mult_2.0 | yes | yes | yes | no | no |
| 2017 | mult_1.25 | no | yes | yes | yes | no |
| 2017 | mult_1.5 | yes | yes | yes | yes | yes |
| 2017 | mult_2.0 | yes | yes | yes | yes | yes |
| 2018 | mult_1.25 | no | yes | yes | yes | no |
| 2018 | mult_1.5 | no | yes | yes | yes | no |
| 2018 | mult_2.0 | no | yes | yes | yes | no |
| 2022 | mult_1.25 | yes | yes | yes | yes | yes |
| 2022 | mult_1.5 | yes | yes | yes | yes | yes |
| 2022 | mult_2.0 | yes | yes | yes | yes | yes |
| 2023 | mult_1.25 | yes | yes | yes | no | no |
| 2023 | mult_1.5 | yes | yes | no | no | no |
| 2023 | mult_2.0 | yes | yes | no | no | no |

Multipliers pass in 2015 and 2022 for all three values and in 2017 for 1.5 and 2.0. They fail in 2016 and 2023
on the recall tolerance for every multiplier, in 2014 on alarmed positive runs for 1.25 and 1.5 and on both for
2.0, and in 2023 also on alarmed positive runs for 1.5 and 2.0. 2018 has no positive windows and is not gated;
its recall condition is not applicable. The chronological arm, reported descriptively, passes in 4, 4 and 2 years
of 6 and also fails overall.

Paired full-HARP bootstrap intervals (1000 draws, seed 24), candidate minus control:

| year | candidate | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | mult_1.25 | episode_precision_diff | -0.005884 | 0.019949 | 1000 | 0 |
| 2014 | mult_1.25 | fp_diff | -1732.075000 | -1098.925000 | 1000 | 0 |
| 2014 | mult_1.5 | episode_precision_diff | -0.002708 | 0.029961 | 1000 | 0 |
| 2014 | mult_1.5 | fp_diff | -3141.325000 | -2082.750000 | 1000 | 0 |
| 2014 | mult_2.0 | episode_precision_diff | 0.002763 | 0.044793 | 1000 | 0 |
| 2014 | mult_2.0 | fp_diff | -5313.250000 | -3543.900000 | 1000 | 0 |
| 2015 | mult_1.25 | episode_precision_diff | 0.003133 | 0.021099 | 1000 | 0 |
| 2015 | mult_1.25 | fp_diff | -1926.050000 | -1170.925000 | 1000 | 0 |
| 2015 | mult_1.5 | episode_precision_diff | 0.005397 | 0.034110 | 1000 | 0 |
| 2015 | mult_1.5 | fp_diff | -3451.125000 | -2108.850000 | 1000 | 0 |
| 2015 | mult_2.0 | episode_precision_diff | 0.018605 | 0.068828 | 1000 | 0 |
| 2015 | mult_2.0 | fp_diff | -5944.150000 | -3626.975000 | 1000 | 0 |
| 2016 | mult_1.25 | episode_precision_diff | -0.000208 | 0.025366 | 1000 | 0 |
| 2016 | mult_1.25 | fp_diff | -771.075000 | -296.975000 | 1000 | 0 |
| 2016 | mult_1.5 | episode_precision_diff | 0.001515 | 0.046968 | 1000 | 0 |
| 2016 | mult_1.5 | fp_diff | -1216.175000 | -467.900000 | 1000 | 0 |
| 2016 | mult_2.0 | episode_precision_diff | 0.000807 | 0.055505 | 1000 | 0 |
| 2016 | mult_2.0 | fp_diff | -1782.100000 | -708.900000 | 1000 | 0 |
| 2017 | mult_1.25 | episode_precision_diff | -0.010933 | 0.012740 | 1000 | 0 |
| 2017 | mult_1.25 | fp_diff | -125.000000 | -45.000000 | 1000 | 0 |
| 2017 | mult_1.5 | episode_precision_diff | -0.011578 | 0.045411 | 1000 | 0 |
| 2017 | mult_1.5 | fp_diff | -261.000000 | -84.975000 | 1000 | 0 |
| 2017 | mult_2.0 | episode_precision_diff | 0.000000 | 0.102235 | 1000 | 0 |
| 2017 | mult_2.0 | fp_diff | -459.050000 | -140.950000 | 1000 | 0 |
| 2018 | mult_1.25 | episode_precision_diff | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | mult_1.25 | fp_diff | -119.025000 | -13.000000 | 1000 | 0 |
| 2018 | mult_1.5 | episode_precision_diff | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | mult_1.5 | fp_diff | -198.050000 | -23.000000 | 1000 | 0 |
| 2018 | mult_2.0 | episode_precision_diff | 0.000000 | 0.000000 | 999 | 1 |
| 2018 | mult_2.0 | fp_diff | -325.025000 | -33.000000 | 1000 | 0 |
| 2022 | mult_1.25 | episode_precision_diff | 0.001416 | 0.012726 | 1000 | 0 |
| 2022 | mult_1.25 | fp_diff | -1611.025000 | -947.975000 | 1000 | 0 |
| 2022 | mult_1.5 | episode_precision_diff | 0.003632 | 0.018728 | 1000 | 0 |
| 2022 | mult_1.5 | fp_diff | -2746.075000 | -1617.975000 | 1000 | 0 |
| 2022 | mult_2.0 | episode_precision_diff | 0.003104 | 0.019636 | 1000 | 0 |
| 2022 | mult_2.0 | fp_diff | -4307.275000 | -2615.000000 | 1000 | 0 |
| 2023 | mult_1.25 | episode_precision_diff | -0.002749 | 0.027061 | 1000 | 0 |
| 2023 | mult_1.25 | fp_diff | -1139.000000 | -660.900000 | 1000 | 0 |
| 2023 | mult_1.5 | episode_precision_diff | -0.009724 | 0.026926 | 1000 | 0 |
| 2023 | mult_1.5 | fp_diff | -1994.325000 | -1166.950000 | 1000 | 0 |
| 2023 | mult_2.0 | episode_precision_diff | 0.002983 | 0.071889 | 1000 | 0 |
| 2023 | mult_2.0 | fp_diff | -3199.125000 | -1924.700000 | 1000 | 0 |

The fp_diff intervals are below zero for every multiplier in every year, so the false-alarm reduction is real
for these frozen predictions. The episode precision gain excludes zero in 2015 and 2022 for all multipliers, in
2014 and 2023 only for 2.0, and in 2016 for 1.5 and 2.0; it does not exclude zero in 2017. The intervals are
conditional on frozen predictions and thresholds, ignore retraining uncertainty and have no multiple-comparison
correction. They do not change the pass or fail outcome.

## Oracle comparison at matched recall

Oracle thresholds use the evaluation labels. They are diagnostic references, not deployable rules, and carry no
uncertainty interval. Ties favour the threshold.

| year | candidate | persistence_recall | matched_recall | persistence_fp | matched_fp | persistence_episodes | matched_episodes | persistence_wins | threshold_at_least_as_good |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | persist_3h | 0.913853 | 0.913853 | 12735 | 9676 | 453 | 565 | no | yes |
| 2014 | persist_6h | 0.871429 | 0.871429 | 11604 | 7694 | 355 | 486 | no | yes |
| 2015 | persist_3h | 0.967528 | 0.967528 | 10505 | 6374 | 339 | 378 | no | yes |
| 2015 | persist_6h | 0.927675 | 0.927675 | 9640 | 4517 | 256 | 299 | no | yes |
| 2016 | persist_3h | 0.950276 | 0.950276 | 1943 | 1878 | 118 | 181 | no | yes |
| 2016 | persist_6h | 0.917127 | 0.917127 | 1641 | 1470 | 84 | 139 | no | yes |
| 2017 | persist_3h | 0.905138 | 0.905138 | 1151 | 539 | 50 | 46 | no | yes |
| 2017 | persist_6h | 0.857708 | 0.857708 | 1029 | 436 | 35 | 49 | no | yes |
| 2022 | persist_3h | 0.928741 | 0.928741 | 9003 | 3517 | 391 | 284 | no | yes |
| 2022 | persist_6h | 0.843230 | 0.843230 | 7964 | 2750 | 306 | 268 | no | yes |
| 2023 | persist_3h | 0.788732 | 0.788732 | 5204 | 3951 | 328 | 396 | no | yes |
| 2023 | persist_6h | 0.650448 | 0.650448 | 4432 | 2666 | 243 | 294 | no | yes |

| arm | candidate | years_persistence_wins | years_threshold_at_least_as_good | required_years | result |
| --- | --- | --- | --- | --- | --- |
| baseline | persist_3h | 0 | 6 | 6 | threshold_at_least_as_good |
| baseline | persist_6h | 0 | 6 | 6 | threshold_at_least_as_good |
| chronological | persist_3h | 1 | 5 | 6 | mixed |
| chronological | persist_6h | 0 | 6 | 6 | threshold_at_least_as_good |

For the baseline, persistence has more false-alarm windows than the matched-recall threshold in all six positive
years for both k, so the verdict is that the threshold is at least as good. Persistence has fewer episodes in some
years, for example 453 against 565 in 2014 for 3 hours, but not in 2022 and, in 2017, only for 6 hours, and it never wins on both
measures in the same year. The chronological arm is mixed for 3 hours, with one persistence win in six years, and
threshold at least as good for 6 hours.

## False-alarm headroom inside the recall tolerance

Oracle threshold with window recall at least the control recall minus 0.02, baseline arm:

| year | control_fp | control_episodes | t | recall | precision | fp | episodes | episode_precision | positive_runs_alarmed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 13886 | 686 | 0.018059 | 0.925541 | 0.162759 | 10998 | 588 | 0.113946 | 79 |
| 2015 | 11453 | 568 | 0.038451 | 0.973432 | 0.166121 | 6621 | 377 | 0.114058 | 51 |
| 2016 | 2289 | 204 | 0.036370 | 0.955801 | 0.082263 | 1930 | 188 | 0.026596 | 7 |
| 2017 | 1287 | 85 | 0.068268 | 0.916996 | 0.285363 | 581 | 50 | 0.140000 | 5 |
| 2022 | 10072 | 622 | 0.019121 | 0.966746 | 0.059923 | 6385 | 403 | 0.037221 | 16 |
| 2023 | 5992 | 475 | 0.020741 | 0.865557 | 0.110205 | 5458 | 475 | 0.086316 | 36 |

This oracle would cut false-alarm windows from 13886 to 10998 in 2014, from 11453 to 6621 in 2015, from 2289 to
1930 in 2016, from 1287 to 581 in 2017, from 10072 to 6385 in 2022 and from 5992 to 5458 in 2023. The headroom is
large in 2015, 2017 and 2022 and small in 2023. It is not available to a rule that cannot see the labels.

## Interpretation and limits

- Persistence is dominated by simply raising the threshold on this evidence, so it should not be pursued
  further. No new k value, cooldown or merging rule is added from these results.
- A fixed multiplier works in some years and breaks recall in others, mainly 2016 and 2023, where the control
  recall is already fragile. A single fixed factor is not robust across years.
- The oracle headroom shows that better operating points exist inside the recall tolerance, but choosing them
  without labels is the open problem. This result does not show how to choose a threshold in advance.
- The numbers are adaptive development evidence on already inspected years, not an independent test. Counts are
  overlapping forecast windows and groupings of them, not physical flares or independent events. AP, Brier and log
  loss are unchanged by both families of rules, so ranking quality is not improved here.
- Any new threshold rule would need a new protocol with a rule frozen before results; a deployable pass would
  justify only a separate prospective protocol.

## Reproduction

```sh
export PYTHONPATH=. PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261107
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/audit_threshold_tradeoff.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --episode-audit artifacts/alarm_episodes_20261107_r2 --persistence artifacts/alarm_persistence_20261107_r1 --output artifacts/threshold_tradeoff_20261107_r1
"$PY" -m pytest tests/test_threshold_tradeoff_audit.py tests/test_threshold_tradeoff_protocol.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261107_r8
```

Source hash of the produced `report.json`: `e0cf54967cf89e68865ee13843b24383f5d1fa2106ab33a574ba3cfdd351f14c`. Use new output names for reruns.
Generated artifacts stay outside Git. The paired Turkish edition covers the same findings and limits.
