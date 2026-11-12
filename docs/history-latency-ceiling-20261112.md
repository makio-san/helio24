# Timing-source scan and zero-latency flare-history ceiling (2026-11-12)

## Decision

Development basis: the relabelled table `artifacts/relabelled_development_20261111_r1` and the adopted pipeline
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)); the basis changed on 2026-11-12 because the
frozen labels covered under 30% of the mapped 2022–2023 M/X flares.

Reading `L2_no_gain_at_zero_latency`, by the rule frozen in
[`config/history-latency-ceiling-v1.json`](../config/history-latency-ceiling-v1.json) before any candidate result.
`event_time` gives the model regional flare history at zero publication latency, which no archived product proves was
available; it is an optimistic ceiling and not achievable performance. Even so it meets the per-year primary acceptance
at the alert tier in 2 of 6 years (2016, 2023) and not in both 2022 and 2023.

The result is mixed, not uniformly negative:

- Cycle 25 moves in the wanted direction. 2022 (alert fallback year for all candidates): precision 0.4727 to
  0.5357, paired interval above zero (0.0129 to 0.1382), but window recall falls from
  0.4822 to 0.3735 and missed positive runs rise from 32 to 37 of 72, so the
  criterion fails; at the control's recall 2022 precision is 0.4526, below control. 2023: precision 0.4263 to 0.4409, recall 0.3879 to 0.4610, missed
  positive runs 68 to 60 of 159; the criterion is met but the paired interval includes zero
  (-0.0189 to 0.0473) and precision stays below 0.50. AP rises from 0.4622 to
  0.4937 in 2022 and from 0.3626 to 0.4130 in 2023.
- Cycle 24 loses. 2015: precision 0.5439 to 0.4655, paired interval below zero (-0.1388 to
  -0.0209). 2017: 0.8676 to 0.4812. 2014: 0.6825 to 0.6224. In these years the selected
  alert threshold delivers more recall and fewer missed positive runs at lower precision.
- Years with alert precision at least 0.50: `control` 2014, 2015, 2017; `event_time` 2014, 2016, 2022. The count stays at 3.
- Alert accuracy is below the always-negative accuracy in 2016, 2022, 2023 for `control` and in 2015, 2017, 2023 for `event_time`.

Consequence: the evidence does not justify downloading GOES XRS flux (about 153 MB) or auditing a real-time event
source in order to raise alert precision, and the flare-history route is closed for the alert tier under the frozen
rule. No model is promoted and no alert, threshold or dashboard setting is changed. Nothing was downloaded. The reserved
2024–2025 test was not accessed.

## Source scan

Directory listings only; no file was downloaded.

| source | file / location | size | period | content | status |
| --- | --- | --- | --- | --- | --- |
| GOES-15 XRS 1-minute science flux | `sci_xrsf-l2-avg1m_g15_s20100407_e20200304_v2-2-1.nc`, NCEI `goes15/xrsf-l2-avg1m_science/` | 31 MB | 2010-04-07 to 2020-03-04 | full disk, no region | not downloaded |
| GOES-16 XRS 1-minute science flux | annual files y2020–y2023, NGDC `goes16/l2/data/xrsf-l2-avg1m_science/` | 28, 30, 32, 32 MB | 2020–2023 (the 241 MB mission file also holds reserved 2024–2025 and must not be used) | full disk, no region | not downloaded |
| GOES-16 XRS flare location | `xrsf-l2-flloc_science` mission file | 595 KB | 2017-02-09 onwards; holds 2024–2025 | location; no training years in cycle 24 | not downloaded |
| SWPC daily event reports | archived event lists | small | 2010–2023 | region and minute times; only an archive `:Created:` time 39–76 h after the report day | probed earlier, availability unverified |
| AIA / SUVI EUV region imagery | JSOC / NGDC | tens of GB | 2010– / 2017– | region-resolved, measurement-time causal | not downloaded; over the free disk space (about 18 GiB) |
| SGAS event times (this report) | `data/activity_summaries_20261109_r1` | local, 22 MB | 2010–2023 | region and minute times; issued once a day | used as a zero-latency ceiling |

| already tested, negative | report |
| --- | --- |
| 96 SHARP summaries, variants and extra features | [precision-features](precision-features-20261027.md) |
| 24/48-hour summary histories | [precision-long-history](precision-long-history-20261028.md) |
| TCN on 12-minute sequences | [temporal-evaluation-final](temporal-evaluation-final-20261106.md) |
| Issued SRS region context | [region-context-results](region-context-results-20261109.md) |
| Issued SGAS flare history, frozen and relabelled labels | [activity-history](activity-history-20261109.md), [activity-history-relabelled](activity-history-relabelled-20261112.md) |
| Daily Br-map CNN score | [image-features](image-features-20261110.md) |
| Own probability trajectory and region age | [precision-context-results](precision-context-results-20261109.md) |

GOES XRS 1-minute flux has not been used in the project. It is causal by measurement time but disk-integrated: it cannot
say which region flared. The [causal SGAS history](activity-history-relabelled-20261112.md) is region-resolved but issued
once a day at about 0245 UTC for the previous UT day, so the newest usable event is about 3 to 51 hours old. Before
paying for a faster source, this report measures what the same information would give with no delay.

## Method

Each SGAS section A row gives Begin, Max and End as HHMM on the UT day before the issue date. The event time is End
(Max, then Begin, when End is blank); a time earlier than Begin is moved to the next day. 12286 event rows were
parsed. A window at forecast time t uses every event whose event time is at or before t minus 30 minutes, whatever the
issue time of the product that lists it. This is not the deployable rule. Labels use GOES peaks at or after t, so no
feature event lies inside the label window. Regional events are those whose NOAA number is in the HARP's `NOAA_ARS` on
the forecast date; a HARP without a NOAA number has `event_available` = 0 and missing regional values.

Sixteen features: `event_available`, `reg_mx_6h`, `reg_mx_12h`, `reg_mx_24h`, `reg_mx_72h`, `reg_c_24h`, `reg_c_72h`,
`reg_events_24h`, `reg_max_logflux_24h`, `reg_max_logflux_72h`, `reg_hours_since_mx`, `reg_hours_since_event`,
`reg_mx_life`, `reg_max_logflux_life`, `disk_mx_24h`, `disk_max_logflux_24h`.

Candidates: `control` is the stored ensemble and thresholds of the adopted pipeline; `history` is the stored causal SGAS
history candidate of `artifacts/activity_history_relabelled_20261112_r1`; neither is refit. `event_time` refits the
unchanged recipes on the 96 summaries plus the sixteen features: expanding training, sigmoid calibration on the prior
year, ensemble weight 0.45/0.55, no hyperparameter search, 12 constituent fits, one feature set. Annual populations
equal those of the adopted pipeline. Watch thresholds (prior-year window recall 0.90) and alert thresholds (prior-year
precision 0.50, recall floor 0.10, fallback flag) were selected on calibration-year probabilities, written and hashed
before evaluation labels were read.

Per-year primary acceptance at the alert tier, against `control`: precision higher, missed positive runs not above,
window recall drop at most 0.02. `L1_latency_binding` required this in all six years, or in both 2022 and 2023 with a
paired bootstrap lower bound above 0 in both. Counts are overlapping forecast windows; a positive run is a contiguous
group of positive windows of one HARP.

Evaluation-year coverage of the zero-latency features:

| year | evaluation windows | event_available share | reg_mx_24h > 0 share | reg_mx_72h > 0 share |
| --- | --- | --- | --- | --- |
| 2014 | 78351 | 0.5226 | 0.0263 | 0.0475 |
| 2015 | 70554 | 0.5460 | 0.0197 | 0.0409 |
| 2016 | 43142 | 0.5515 | 0.0047 | 0.0083 |
| 2017 | 19843 | 0.6073 | 0.0133 | 0.0209 |
| 2022 | 65593 | 0.6172 | 0.0305 | 0.0605 |
| 2023 | 96991 | 0.5664 | 0.0467 | 0.0934 |

## Alert tier

| year | candidate | fallback | TP | FP | FN | recall | precision | precision 95% interval | accuracy | always-negative accuracy | missed positive runs | primary met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 688 | 320 | 1748 | 0.2824 | 0.6825 | 0.4308–0.8477 | 0.9736 | 0.9689 | 66/88 |  |
| 2014 | `history` | no | 708 | 296 | 1728 | 0.2906 | 0.7052 | 0.4628–0.8478 | 0.9742 | 0.9689 | 67/88 | no |
| 2014 | `event_time` | no | 801 | 486 | 1635 | 0.3288 | 0.6224 | 0.3865–0.7877 | 0.9729 | 0.9689 | 61/88 | no |
| 2015 | `control` | no | 545 | 457 | 916 | 0.3730 | 0.5439 | 0.3286–0.7166 | 0.9805 | 0.9793 | 27/57 |  |
| 2015 | `history` | no | 485 | 388 | 976 | 0.3320 | 0.5556 | 0.3463–0.7216 | 0.9807 | 0.9793 | 28/57 | no |
| 2015 | `event_time` | no | 648 | 744 | 813 | 0.4435 | 0.4655 | 0.2792–0.6266 | 0.9779 | 0.9793 | 22/57 | no |
| 2016 | `control` | no | 94 | 109 | 120 | 0.4393 | 0.4631 | 0.0000–0.6230 | 0.9947 | 0.9950 | 3/8 |  |
| 2016 | `history` | no | 64 | 71 | 150 | 0.2991 | 0.4741 | 0.0000–0.6667 | 0.9949 | 0.9950 | 4/8 | no |
| 2016 | `event_time` | no | 99 | 74 | 115 | 0.4626 | 0.5723 | 0.0000–0.7091 | 0.9956 | 0.9950 | 2/8 | yes |
| 2017 | `control` | no | 177 | 27 | 88 | 0.6679 | 0.8676 | 0.0000–1.0000 | 0.9942 | 0.9866 | 3/6 |  |
| 2017 | `history` | no | 181 | 93 | 84 | 0.6830 | 0.6606 | 0.0000–0.9325 | 0.9911 | 0.9866 | 3/6 | no |
| 2017 | `event_time` | no | 205 | 221 | 60 | 0.7736 | 0.4812 | 0.0000–0.8440 | 0.9858 | 0.9866 | 1/6 | no |
| 2022 | `control` | yes | 1056 | 1178 | 1134 | 0.4822 | 0.4727 | 0.3482–0.6021 | 0.9648 | 0.9666 | 32/72 |  |
| 2022 | `history` | yes | 1278 | 2004 | 912 | 0.5836 | 0.3894 | 0.2893–0.4982 | 0.9555 | 0.9666 | 22/72 | no |
| 2022 | `event_time` | yes | 818 | 709 | 1372 | 0.3735 | 0.5357 | 0.4051–0.6836 | 0.9683 | 0.9666 | 37/72 | no |
| 2023 | `control` | no | 1587 | 2136 | 2504 | 0.3879 | 0.4263 | 0.3483–0.5053 | 0.9522 | 0.9578 | 68/159 |  |
| 2023 | `history` | no | 1703 | 2210 | 2388 | 0.4163 | 0.4352 | 0.3583–0.5207 | 0.9526 | 0.9578 | 67/159 | yes |
| 2023 | `event_time` | no | 1886 | 2392 | 2205 | 0.4610 | 0.4409 | 0.3674–0.5199 | 0.9526 | 0.9578 | 60/159 | yes |

Fallback years (2022) are years in which no calibration-year threshold reached precision 0.50 with recall at least
0.10; the rule then takes the best available calibration precision. Precision intervals are HARP-cluster bootstrap
intervals of each candidate.

Acceptance criteria:

| year | candidate | precision higher | missed runs not above | recall drop within 0.02 | primary met |
| --- | --- | --- | --- | --- | --- |
| 2014 | `history` | yes | no | yes | no |
| 2014 | `event_time` | no | yes | yes | no |
| 2015 | `history` | yes | no | no | no |
| 2015 | `event_time` | no | yes | yes | no |
| 2016 | `history` | yes | no | no | no |
| 2016 | `event_time` | yes | yes | yes | yes |
| 2017 | `history` | no | yes | yes | no |
| 2017 | `event_time` | no | yes | yes | no |
| 2022 | `history` | no | yes | yes | no |
| 2022 | `event_time` | yes | no | no | no |
| 2023 | `history` | yes | yes | yes | yes |
| 2023 | `event_time` | yes | yes | yes | yes |

Selected alert thresholds:

| year | candidate | alert threshold | calibration recall | calibration precision | fallback |
| --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 0.4627 | 0.1326 | 0.5000 | no |
| 2014 | `history` | 0.4278 | 0.1560 | 0.5000 | no |
| 2014 | `event_time` | 0.3534 | 0.2502 | 0.5000 | no |
| 2015 | `control` | 0.2631 | 0.4906 | 0.5000 | no |
| 2015 | `history` | 0.2627 | 0.4819 | 0.5000 | no |
| 2015 | `event_time` | 0.2519 | 0.5115 | 0.5000 | no |
| 2016 | `control` | 0.2564 | 0.4969 | 0.5000 | no |
| 2016 | `history` | 0.2918 | 0.4052 | 0.5000 | no |
| 2016 | `event_time` | 0.3132 | 0.4073 | 0.5000 | no |
| 2017 | `control` | 0.4145 | 0.2196 | 0.5000 | no |
| 2017 | `history` | 0.3538 | 0.2991 | 0.5000 | no |
| 2017 | `event_time` | 0.2307 | 0.5187 | 0.5000 | no |
| 2022 | `control` | 0.1570 | 0.2361 | 0.1996 | yes |
| 2022 | `history` | 0.1622 | 0.2281 | 0.2155 | yes |
| 2022 | `event_time` | 0.2466 | 0.1326 | 0.2463 | yes |
| 2023 | `control` | 0.2689 | 0.4461 | 0.5000 | no |
| 2023 | `history` | 0.2999 | 0.3767 | 0.5000 | no |
| 2023 | `event_time` | 0.2855 | 0.4292 | 0.5000 | no |

Paired HARP-cluster bootstrap intervals of the alert precision difference (candidate minus the compared candidate, 1000
draws, seed 24):

| year | candidate | against | lower | upper | draws used |
| --- | --- | --- | --- | --- | --- |
| 2014 | `history` | `control` | -0.0616 | 0.1081 | 1000 |
| 2014 | `event_time` | `control` | -0.1184 | 0.0144 | 1000 |
| 2014 | `event_time` | `history` | -0.1366 | -0.0148 | 1000 |
| 2015 | `history` | `control` | -0.0306 | 0.0645 | 1000 |
| 2015 | `event_time` | `control` | -0.1388 | -0.0209 | 1000 |
| 2015 | `event_time` | `history` | -0.1497 | -0.0306 | 1000 |
| 2016 | `history` | `control` | -0.3060 | 0.1235 | 994 |
| 2016 | `event_time` | `control` | 0.0000 | 0.3070 | 999 |
| 2016 | `event_time` | `history` | 0.0000 | 0.4745 | 994 |
| 2017 | `history` | `control` | -0.4631 | 0.0000 | 982 |
| 2017 | `event_time` | `control` | -0.5652 | 0.0990 | 982 |
| 2017 | `event_time` | `history` | -0.3277 | 0.1000 | 1000 |
| 2022 | `history` | `control` | -0.1453 | -0.0331 | 1000 |
| 2022 | `event_time` | `control` | 0.0129 | 0.1382 | 1000 |
| 2022 | `event_time` | `history` | 0.0645 | 0.2507 | 1000 |
| 2023 | `history` | `control` | -0.0210 | 0.0396 | 1000 |
| 2023 | `event_time` | `control` | -0.0189 | 0.0473 | 1000 |
| 2023 | `event_time` | `history` | -0.0214 | 0.0307 | 1000 |

## Descriptive measures

`precision at control recall` is the candidate's precision at the evaluation-year threshold that delivers the control's
alert recall. It uses evaluation labels, is not deployable and is not part of the acceptance. AP and the FP origin
shares follow the cycle-25 diagnostic definitions.

| year | candidate | AP | within-flaring-HARP AP | region AP | precision at control recall | FP share never-flaring HARPs | FP share within 72 h of positive |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 0.5015 | 0.5528 | 0.7600 | 0.6846 | 0.1437 | 0.7063 |
| 2014 | `history` | 0.5136 | 0.5576 | 0.7959 | 0.7159 | 0.1047 | 0.7939 |
| 2014 | `event_time` | 0.5072 | 0.5506 | 0.8042 | 0.6647 | 0.1111 | 0.7325 |
| 2015 | `control` | 0.4823 | 0.5331 | 0.8264 | 0.5439 | 0.0853 | 0.8249 |
| 2015 | `history` | 0.4487 | 0.4945 | 0.8593 | 0.5018 | 0.0438 | 0.8660 |
| 2015 | `event_time` | 0.4344 | 0.4783 | 0.8613 | 0.4802 | 0.0954 | 0.7540 |
| 2016 | `control` | 0.4060 | 0.4853 | 0.6333 | 0.4631 | 0.2569 | 0.5688 |
| 2016 | `history` | 0.4430 | 0.4976 | 0.7589 | 0.4541 | 0.0423 | 0.7606 |
| 2016 | `event_time` | 0.4804 | 0.5191 | 0.9167 | 0.5839 | 0.0405 | 0.8243 |
| 2017 | `control` | 0.7975 | 0.8727 | 1.0000 | 0.8762 | 0.1111 | 0.8889 |
| 2017 | `history` | 0.7571 | 0.8459 | 0.8333 | 0.8592 | 0.6344 | 0.3656 |
| 2017 | `event_time` | 0.7763 | 0.8607 | 1.0000 | 0.7902 | 0.6154 | 0.3801 |
| 2022 | `control` | 0.4622 | 0.4968 | 0.8315 | 0.4752 | 0.0823 | 0.7139 |
| 2022 | `history` | 0.4692 | 0.4975 | 0.8628 | 0.4638 | 0.1108 | 0.6607 |
| 2022 | `event_time` | 0.4937 | 0.5195 | 0.8801 | 0.4526 | 0.0028 | 0.8702 |
| 2023 | `control` | 0.3626 | 0.4057 | 0.8655 | 0.4263 | 0.1320 | 0.7561 |
| 2023 | `history` | 0.3737 | 0.4142 | 0.8779 | 0.4486 | 0.1285 | 0.7719 |
| 2023 | `event_time` | 0.4130 | 0.4464 | 0.9026 | 0.4740 | 0.0911 | 0.8399 |

- `event_time` alert precision is above control in 2016, 2022, 2023 and below it in 2014, 2015, 2017. The paired interval lies above
  zero in 2022 and below zero in 2015.
- AP with `event_time` is above control in 2014, 2016, 2022, 2023 and below it in 2015, 2017.
- At the control's delivered recall, `event_time` precision is above control in 2016, 2023 and below it in 2014, 2015, 2017, 2022.
  The losses are therefore not only threshold shifts, and the 2022 gain at the selected threshold comes from operating
  at lower recall: at the control's recall, 2022 precision is 0.4526 against 0.4727.
- The 72-hour near-miss share of alert FP windows with `event_time` is 0.8702 in 2022 and
  0.8399 in 2023 (control 0.7139 and 0.7561).

## Watch tier

| year | candidate | TP | FP | FN | recall | precision | accuracy | always-negative accuracy | missed positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 2146 | 9020 | 290 | 0.8810 | 0.1922 | 0.8812 | 0.9689 | 6/88 |
| 2014 | `history` | 2191 | 10033 | 245 | 0.8994 | 0.1792 | 0.8688 | 0.9689 | 5/88 |
| 2014 | `event_time` | 2208 | 10256 | 228 | 0.9064 | 0.1772 | 0.8662 | 0.9689 | 6/88 |
| 2015 | `control` | 1396 | 8079 | 65 | 0.9555 | 0.1473 | 0.8846 | 0.9793 | 1/57 |
| 2015 | `history` | 1378 | 7551 | 83 | 0.9432 | 0.1543 | 0.8918 | 0.9793 | 1/57 |
| 2015 | `event_time` | 1371 | 7173 | 90 | 0.9384 | 0.1605 | 0.8971 | 0.9793 | 1/57 |
| 2016 | `control` | 201 | 1722 | 13 | 0.9393 | 0.1045 | 0.9598 | 0.9950 | 0/8 |
| 2016 | `history` | 195 | 1276 | 19 | 0.9112 | 0.1326 | 0.9700 | 0.9950 | 0/8 |
| 2016 | `event_time` | 198 | 1626 | 16 | 0.9252 | 0.1086 | 0.9619 | 0.9950 | 0/8 |
| 2017 | `control` | 243 | 1058 | 22 | 0.9170 | 0.1868 | 0.9456 | 0.9866 | 1/6 |
| 2017 | `history` | 244 | 1059 | 21 | 0.9208 | 0.1873 | 0.9456 | 0.9866 | 1/6 |
| 2017 | `event_time` | 245 | 1038 | 20 | 0.9245 | 0.1910 | 0.9467 | 0.9866 | 1/6 |
| 2022 | `control` | 2024 | 11917 | 166 | 0.9242 | 0.1452 | 0.8158 | 0.9666 | 5/72 |
| 2022 | `history` | 2065 | 14935 | 125 | 0.9429 | 0.1215 | 0.7704 | 0.9666 | 4/72 |
| 2022 | `event_time` | 2016 | 10280 | 174 | 0.9205 | 0.1640 | 0.8406 | 0.9666 | 6/72 |
| 2023 | `control` | 3695 | 16022 | 396 | 0.9032 | 0.1874 | 0.8307 | 0.9578 | 10/159 |
| 2023 | `history` | 3770 | 17668 | 321 | 0.9215 | 0.1759 | 0.8145 | 0.9578 | 7/159 |
| 2023 | `event_time` | 3747 | 15561 | 344 | 0.9159 | 0.1941 | 0.8360 | 0.9578 | 7/159 |

Watch-tier accuracy is below the always-negative accuracy for every candidate in every year.

## Frozen-label results

This ceiling was not run on the frozen labels. The frozen-label results of the causal SGAS history remain in
[activity-history-20261109](activity-history-20261109.md) and are repeated in
[activity-history-relabelled-20261112](activity-history-relabelled-20261112.md); they are negative.

## Limits

Optimistic and not deployable: real-time knowledge of the event, its class and its NOAA number 30 minutes after the
event ended is assumed and no archived product proves it. Already inspected years: adaptive development evidence, not an
independent test. Counts are overlapping forecast windows and groupings of them, not physical flares. SGAS lists
energetic events, not every C-class flare. Thirteen days have no SGAS file and one has no issue time; their events are
absent and are not encoded. `NOAA_ARS` is the definitive JSOC association and was fixed after the fact. The relabelled
M/X labels were recovered from the same SGAS rows, so past regional M/X features are past labels of the same region seen
without delay; an operational source would be noisier. The 2022 alert threshold is a fallback threshold for every
candidate. In 2016 and 2017 a few bootstrap draws had no alarm for one candidate and were dropped (`draws used`). The
scan lists sizes from directory listings; file contents were not inspected. The reading concerns flare history as an
added feature of the unchanged recipes; it does not test GOES XRS flux itself.

## Reproduction

```sh
python -m scripts.fetch_activity_summaries --output data/activity_summaries_20261109_r1
python -m scripts.audit_activity_history_relabelled --output artifacts/activity_history_relabelled_20261112_r1
python -m scripts.audit_history_latency_ceiling --output artifacts/history_latency_ceiling_20261112_r1
```

Config sha256 `986cf5894c78ece27306cebf5e85baad58cb4bcc45d608d489a26ebad5ba3628`; thresholds sha256 `1cd295c8245de4767e2618e1c12ee3b661bde921fe624030151b2be95023a6da`. Use new output directories;
existing output is not overwritten.
