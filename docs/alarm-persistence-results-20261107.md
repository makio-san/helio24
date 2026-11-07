# Alarm persistence results: fewer false alarms, but recall falls below the frozen limit

## Decision and scope

The [frozen protocol](alarm-persistence-protocol-20261107.md) was run once on the frozen annual
predictions and thresholds of the completed seven-year comparison (source report SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`). Two rules were evaluated:
an alarm only after 3 (`persist_3h`) or 6 (`persist_6h`) consecutive threshold exceedances,
against the unchanged control. No model was trained, no threshold changed, no label changed and the
reserved 2024–2025 test stayed closed.

Decision: neither rule meets the acceptance rules in any year, for either arm. Both reduce false
alarms and episodes and raise episode precision, but both lose more window recall than the frozen
limit of 0.02 in every positive year. Persistence is not adopted, and no further k values, cooldowns
or merging rules are added from these results; that would be a new protocol.

Disclosure: the first execution stopped with an error in 2018 (no positive windows, recall
undefined) before writing output; the recall condition was then made not applicable when the control
recall is undefined, as the protocol states for 2018, and the analysis was run again. No result had
been seen before this fix. The control also reproduces the alarm episode audit exactly in every
year and arm.

## Acceptance outcome

| arm | candidate | k | years_met | required_years | all_year_primary |
| --- | --- | --- | --- | --- | --- |
| baseline | persist_3h | 3 | 0 | 6 | no |
| baseline | persist_6h | 6 | 0 | 6 | no |
| chronological | persist_3h | 3 | 0 | 6 | no |
| chronological | persist_6h | 6 | 0 | 6 | no |

A candidate must satisfy all four per-year conditions in all six positive years for the same k.

| year | candidate | episode_precision_higher | fp_lower | positive_runs_alarmed_not_below | recall_drop_ok | primary_met |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | persist_3h | yes | yes | no | no | no |
| 2014 | persist_6h | yes | yes | no | no | no |
| 2015 | persist_3h | yes | yes | no | no | no |
| 2015 | persist_6h | yes | yes | no | no | no |
| 2016 | persist_3h | yes | yes | yes | no | no |
| 2016 | persist_6h | yes | yes | yes | no | no |
| 2017 | persist_3h | yes | yes | yes | no | no |
| 2017 | persist_6h | yes | yes | yes | no | no |
| 2018 | persist_3h | no | yes | yes | yes | no |
| 2018 | persist_6h | no | yes | yes | yes | no |
| 2022 | persist_3h | yes | yes | yes | no | no |
| 2022 | persist_6h | yes | yes | yes | no | no |
| 2023 | persist_3h | yes | yes | yes | no | no |
| 2023 | persist_6h | yes | yes | no | no | no |

`recall_drop_ok` fails in all six positive years for both k. `positive_runs_alarmed_not_below`
also fails in 2014 and 2015 for both k and in 2023 for 6 hours. 2018 has no positive windows and is
not gated; its flags are shown for completeness. The chronological arm, reported descriptively,
also meets 0 of 6 years.

## Per-year results for the baseline arm

| year | candidate | recall | recall_drop | precision | fp | episodes | hit_episodes | episode_precision | positive_runs | positive_runs_alarmed | median_alarm_delay_hours | max_alarm_delay_hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 0.945455 | 0.000000 | 0.135905 | 13886 | 686 | 67 | 0.097668 | 83 | 80 | 0.0 | 15.0 |
| 2014 | persist_3h | 0.913853 | 0.031602 | 0.142193 | 12735 | 453 | 63 | 0.139073 | 83 | 78 | 0.0 | 17.0 |
| 2014 | persist_6h | 0.871429 | 0.074026 | 0.147830 | 11604 | 355 | 60 | 0.169014 | 83 | 75 | 0.0 | 20.0 |
| 2015 | control | 0.993358 | 0.000000 | 0.105164 | 11453 | 568 | 38 | 0.066901 | 51 | 51 | 0.0 | 7.0 |
| 2015 | persist_3h | 0.967528 | 0.025830 | 0.110951 | 10505 | 339 | 36 | 0.106195 | 51 | 49 | 0.0 | 9.0 |
| 2015 | persist_6h | 0.927675 | 0.065683 | 0.115353 | 9640 | 256 | 35 | 0.136719 | 51 | 48 | 0.0 | 12.0 |
| 2016 | control | 0.972376 | 0.000000 | 0.071400 | 2289 | 204 | 4 | 0.019608 | 7 | 7 | 0.0 | 5.0 |
| 2016 | persist_3h | 0.950276 | 0.022099 | 0.081324 | 1943 | 118 | 4 | 0.033898 | 7 | 7 | 0.0 | 7.0 |
| 2016 | persist_6h | 0.917127 | 0.055249 | 0.091865 | 1641 | 84 | 4 | 0.047619 | 7 | 7 | 0.0 | 10.0 |
| 2017 | control | 0.936759 | 0.000000 | 0.155512 | 1287 | 85 | 5 | 0.058824 | 6 | 5 | 0.0 | 13.0 |
| 2017 | persist_3h | 0.905138 | 0.031621 | 0.165942 | 1151 | 50 | 5 | 0.100000 | 6 | 5 | 2.0 | 15.0 |
| 2017 | persist_6h | 0.857708 | 0.079051 | 0.174157 | 1029 | 35 | 5 | 0.142857 | 6 | 5 | 5.0 | 18.0 |
| 2018 | control | undefined | undefined | 0.000000 | 359 | 30 | 0 | 0.000000 | 0 | 0 | undefined | undefined |
| 2018 | persist_3h | undefined | undefined | 0.000000 | 307 | 14 | 0 | 0.000000 | 0 | 0 | undefined | undefined |
| 2018 | persist_6h | undefined | undefined | 0.000000 | 276 | 6 | 0 | 0.000000 | 0 | 0 | undefined | undefined |
| 2022 | control | 0.985748 | 0.000000 | 0.039573 | 10072 | 622 | 16 | 0.025723 | 16 | 16 | 0.0 | 0.0 |
| 2022 | persist_3h | 0.928741 | 0.057007 | 0.041622 | 9003 | 391 | 16 | 0.040921 | 16 | 16 | 2.0 | 2.0 |
| 2022 | persist_6h | 0.843230 | 0.142518 | 0.042673 | 7964 | 306 | 16 | 0.052288 | 16 | 16 | 5.0 | 5.0 |
| 2023 | control | 0.884763 | 0.000000 | 0.103397 | 5992 | 475 | 40 | 0.084211 | 38 | 36 | 0.0 | 13.0 |
| 2023 | persist_3h | 0.788732 | 0.096031 | 0.105842 | 5204 | 328 | 38 | 0.115854 | 38 | 36 | 2.0 | 15.0 |
| 2023 | persist_6h | 0.650448 | 0.234315 | 0.102834 | 4432 | 243 | 33 | 0.135802 | 38 | 33 | 5.0 | 18.0 |

`recall_drop` is the control recall minus the candidate recall. Alarm delay is measured from the
first positive-labelled window of an alarmed positive run; it is reported, not gated. The recall
losses grow with k and are largest in 2022 and 2023.

## Uncertainty

Paired full-HARP bootstrap intervals (1000 draws, seed 24) for the candidate minus the control:

| year | candidate | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | persist_3h | episode_precision_diff | 0.025754 | 0.056382 | 1000 | 0 |
| 2014 | persist_3h | fp_diff | -1374.025000 | -950.975000 | 1000 | 0 |
| 2014 | persist_6h | episode_precision_diff | 0.049742 | 0.092547 | 1000 | 0 |
| 2014 | persist_6h | fp_diff | -2739.150000 | -1877.975000 | 1000 | 0 |
| 2015 | persist_3h | episode_precision_diff | 0.020060 | 0.063789 | 1000 | 0 |
| 2015 | persist_3h | fp_diff | -1164.050000 | -754.850000 | 1000 | 0 |
| 2015 | persist_6h | episode_precision_diff | 0.039940 | 0.102681 | 1000 | 0 |
| 2015 | persist_6h | fp_diff | -2223.075000 | -1455.850000 | 1000 | 0 |
| 2016 | persist_3h | episode_precision_diff | 0.002824 | 0.031001 | 1000 | 0 |
| 2016 | persist_3h | fp_diff | -484.125000 | -233.000000 | 1000 | 0 |
| 2016 | persist_6h | episode_precision_diff | 0.005690 | 0.060274 | 1000 | 0 |
| 2016 | persist_6h | fp_diff | -907.050000 | -435.975000 | 1000 | 0 |
| 2017 | persist_3h | episode_precision_diff | 0.000000 | 0.108293 | 1000 | 0 |
| 2017 | persist_3h | fp_diff | -216.000000 | -70.000000 | 1000 | 0 |
| 2017 | persist_6h | episode_precision_diff | 0.000000 | 0.218805 | 1000 | 0 |
| 2017 | persist_6h | fp_diff | -423.000000 | -126.925000 | 1000 | 0 |
| 2018 | persist_3h | episode_precision_diff | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | persist_3h | fp_diff | -95.000000 | -19.975000 | 1000 | 0 |
| 2018 | persist_6h | episode_precision_diff | 0.000000 | 0.000000 | 981 | 19 |
| 2018 | persist_6h | fp_diff | -158.025000 | -30.000000 | 1000 | 0 |
| 2022 | persist_3h | episode_precision_diff | 0.006766 | 0.024970 | 1000 | 0 |
| 2022 | persist_3h | fp_diff | -1288.025000 | -870.900000 | 1000 | 0 |
| 2022 | persist_6h | episode_precision_diff | 0.011648 | 0.044252 | 1000 | 0 |
| 2022 | persist_6h | fp_diff | -2558.275000 | -1709.950000 | 1000 | 0 |
| 2023 | persist_3h | episode_precision_diff | 0.016722 | 0.049083 | 1000 | 0 |
| 2023 | persist_3h | fp_diff | -967.000000 | -613.000000 | 1000 | 0 |
| 2023 | persist_6h | episode_precision_diff | 0.026213 | 0.079862 | 1000 | 0 |
| 2023 | persist_6h | fp_diff | -1921.025000 | -1212.925000 | 1000 | 0 |

The fp_diff intervals exclude zero in every year, so the false-alarm reduction is not a sampling
artifact of these frozen predictions. The episode precision gain also excludes zero in 2014, 2015,
2016, 2022 and 2023, while 2017 has a lower bound at zero and 2018 has no positive windows.
The intervals are conditional on frozen predictions and thresholds and do not include retraining
uncertainty or a multiple-comparison correction. They do not change the recall failure.

## Pooled counts

Sums over the seven years, including 2018 episodes and false alarms.

| arm | candidate | k | tp | fp | fn | tn | episodes | hit_episodes | positive_runs | positive_runs_alarmed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | control | 1 | 5049 | 45338 | 252 | 275164 | 2670 | 170 | 201 | 195 |
| baseline | persist_3h | 3 | 4830 | 40848 | 471 | 279654 | 1693 | 162 | 201 | 191 |
| baseline | persist_6h | 6 | 4516 | 36586 | 785 | 283916 | 1285 | 153 | 201 | 184 |
| chronological | control | 1 | 5029 | 64671 | 272 | 255831 | 3558 | 166 | 201 | 194 |
| chronological | persist_3h | 3 | 4824 | 58563 | 477 | 261939 | 2341 | 159 | 201 | 189 |
| chronological | persist_6h | 6 | 4527 | 52470 | 774 | 268032 | 1798 | 153 | 201 | 184 |

For the baseline, 3 hours of persistence cuts episodes from 2670 to 1693 and false-alarm windows
from 45338 to 40848, but true-alarm windows fall from 5049 to 4830. At 6 hours episodes fall to
1285 and false-alarm windows to 36586, with true-alarm windows at 4516 and 184 of 201 positive
runs alarmed instead of 195.

## Interpretation and limits

- Persistence works as intended on the alarm count: short all-negative episodes are removed.
- The cost is missed positive windows near the start of each event and a small number of lost
  positive runs, plus a delay of at least k minus one hours.
- This protocol did not compare persistence with simply raising the alarm threshold, which also
  trades recall for fewer false alarms. The result does not show that persistence is a better
  trade than a higher threshold.
- The numbers are adaptive development evidence on already inspected years, not an independent test.
  Window and episode counts are overlapping forecast windows, not physical flares or independent
  events. AP, Brier and log loss are unchanged by this rule.
- The false-alarm burden stays high: even the best candidate leaves 1132 all-negative episodes
  for 201 positive runs in the pooled baseline.

## Reproduction

```sh
export PYTHONPATH=. PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261107
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/audit_alarm_persistence.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --episode-audit artifacts/alarm_episodes_20261107_r2 --output artifacts/alarm_persistence_20261107_r1
"$PY" -m pytest tests/test_alarm_persistence_audit.py tests/test_alarm_persistence_protocol.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261107_r6
```

Source hash of the produced `report.json`: `242b78592fb9c64d1a20809be5179874783bde54a7bc4731fc960fa43841f175`. Use new output names for reruns.
Generated artifacts stay outside Git. The paired Turkish edition covers the same findings and limits.
