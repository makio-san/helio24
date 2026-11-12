# SGAS flare history at the alert tier of the adopted pipeline (2026-11-12)

## Decision

Development basis: the relabelled table `artifacts/relabelled_development_20261111_r1` and the adopted pipeline
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)); the basis changed on 2026-11-12 because the
frozen labels covered under 30% of the mapped 2022–2023 M/X flares.

Negative result, reading `R3_no_gain`. Adding the causal SGAS flare-history features to the 96 magnetic summaries
does not raise alert-tier precision on the adopted basis. `history` meets the per-year primary acceptance in
1 of 6 years (2023) and `flag` in 2 of 6 (2015, 2017); neither meets it in both 2022 and 2023.
The number of years with alert precision at least 0.50 stays at 3 for every candidate (2014, 2015, 2017). Alert accuracy
with `history` is below the always-negative accuracy in 2016, 2022, 2023.

- 2022 (alert fallback year for all candidates): `history` lowers precision from 0.4727 to 0.3894 while
  window recall rises from 0.4822 to 0.5836 and missed positive runs fall from 32 to
  22 of 72. The paired interval of the precision difference lies below zero
  (-0.1453 to -0.0331).
- 2023: `history` raises precision from 0.4263 to 0.4352 with recall 0.3879 to 0.4163 and
  missed positive runs 68 to 67 of 159; the paired interval
  includes zero (-0.0210 to 0.0396) and precision stays below 0.50.
- 2017: `history` lowers precision from 0.8676 to 0.6606.

No model is promoted and no alert, threshold or dashboard setting is changed; the reserved 2024–2025 test was not
accessed. The protocol [`config/activity-history-v2.json`](../config/activity-history-v2.json) was frozen, committed and
pushed before any candidate result.

## Why this was repeated

The [relabelled cycle-25 diagnostic](cycle25-diagnostic-relabelled-20261112.md) found that 0.7139 and 0.7561 of the
alert FP windows in 2022 and 2023 lie within 72 hours of a positive window of the same HARP: the alert tier finds the
regions and misses the day. A region's own recent flares are timing information. The
[first test](activity-history-20261109.md) of these features was run on frozen labels and judged at the watch tier
(window recall 0.90). This report repeats it with unchanged features, availability rule and code on the adopted basis and
judges it at the alert tier.

## Method

Candidates: `control` is the stored ensemble and the stored thresholds of the adopted pipeline, without refit. `flag`
refits the unchanged recipes on the 96 summaries plus `history_available`, `reports_3d`, `hours_since_issue`. `history`
uses all fifteen features of [`config/activity-history-v1.json`](../config/activity-history-v1.json). A window at forecast
time t uses only SGAS products issued at or before t minus 30 minutes; regional events are those whose NOAA number is in
the HARP's `NOAA_ARS` on the forecast date. Expanding training, sigmoid calibration on the prior year, ensemble weight
0.45/0.55, no hyperparameter search, 24 constituent fits. Annual populations equal those of the adopted
pipeline. Watch thresholds (prior-year window recall 0.90) and alert thresholds (prior-year precision 0.50, recall floor
0.10, fallback flag) were selected on calibration-year probabilities, written and hashed before evaluation labels were read.

Per-year primary acceptance at the alert tier, against `control`: precision higher, missed positive runs not above,
window recall drop at most 0.02. Counts are overlapping forecast windows; a positive run is a contiguous group of
positive windows of one HARP.

Evaluation-year coverage:

| year | evaluation windows | history_available share | reg_mx_3d > 0 share |
| --- | --- | --- | --- |
| 2014 | 78351 | 0.5226 | 0.0454 |
| 2015 | 70554 | 0.5460 | 0.0399 |
| 2016 | 43142 | 0.5515 | 0.0068 |
| 2017 | 19843 | 0.6073 | 0.0201 |
| 2022 | 65593 | 0.6169 | 0.0590 |
| 2023 | 96991 | 0.5664 | 0.0905 |

## Alert tier

| year | candidate | fallback | TP | FP | FN | recall | precision | precision 95% interval | accuracy | always-negative accuracy | missed positive runs | primary met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | no | 688 | 320 | 1748 | 0.2824 | 0.6825 | 0.4308–0.8477 | 0.9736 | 0.9689 | 66/88 |  |
| 2014 | `flag` | no | 670 | 301 | 1766 | 0.2750 | 0.6900 | 0.4219–0.8502 | 0.9736 | 0.9689 | 68/88 | no |
| 2014 | `history` | no | 708 | 296 | 1728 | 0.2906 | 0.7052 | 0.4628–0.8478 | 0.9742 | 0.9689 | 67/88 | no |
| 2015 | `control` | no | 545 | 457 | 916 | 0.3730 | 0.5439 | 0.3286–0.7166 | 0.9805 | 0.9793 | 27/57 |  |
| 2015 | `flag` | no | 558 | 466 | 903 | 0.3819 | 0.5449 | 0.3340–0.7163 | 0.9806 | 0.9793 | 27/57 | yes |
| 2015 | `history` | no | 485 | 388 | 976 | 0.3320 | 0.5556 | 0.3463–0.7216 | 0.9807 | 0.9793 | 28/57 | no |
| 2016 | `control` | no | 94 | 109 | 120 | 0.4393 | 0.4631 | 0.0000–0.6230 | 0.9947 | 0.9950 | 3/8 |  |
| 2016 | `flag` | no | 94 | 109 | 120 | 0.4393 | 0.4631 | 0.0000–0.6253 | 0.9947 | 0.9950 | 3/8 | no |
| 2016 | `history` | no | 64 | 71 | 150 | 0.2991 | 0.4741 | 0.0000–0.6667 | 0.9949 | 0.9950 | 4/8 | no |
| 2017 | `control` | no | 177 | 27 | 88 | 0.6679 | 0.8676 | 0.0000–1.0000 | 0.9942 | 0.9866 | 3/6 |  |
| 2017 | `flag` | no | 176 | 25 | 89 | 0.6642 | 0.8756 | 0.0000–1.0000 | 0.9943 | 0.9866 | 3/6 | yes |
| 2017 | `history` | no | 181 | 93 | 84 | 0.6830 | 0.6606 | 0.0000–0.9325 | 0.9911 | 0.9866 | 3/6 | no |
| 2022 | `control` | yes | 1056 | 1178 | 1134 | 0.4822 | 0.4727 | 0.3482–0.6021 | 0.9648 | 0.9666 | 32/72 |  |
| 2022 | `flag` | yes | 1064 | 1207 | 1126 | 0.4858 | 0.4685 | 0.3458–0.5997 | 0.9644 | 0.9666 | 31/72 | no |
| 2022 | `history` | yes | 1278 | 2004 | 912 | 0.5836 | 0.3894 | 0.2893–0.4982 | 0.9555 | 0.9666 | 22/72 | no |
| 2023 | `control` | no | 1587 | 2136 | 2504 | 0.3879 | 0.4263 | 0.3483–0.5053 | 0.9522 | 0.9578 | 68/159 |  |
| 2023 | `flag` | no | 1605 | 2188 | 2486 | 0.3923 | 0.4231 | 0.3448–0.5019 | 0.9518 | 0.9578 | 67/159 | no |
| 2023 | `history` | no | 1703 | 2210 | 2388 | 0.4163 | 0.4352 | 0.3583–0.5207 | 0.9526 | 0.9578 | 67/159 | yes |

Fallback years (2022) are years in which no calibration-year threshold reached precision 0.50 with recall at least
0.10; the rule then takes the best available calibration precision. Precision intervals are HARP-cluster bootstrap
intervals of each candidate.

Acceptance criteria:

| year | candidate | precision higher | missed runs not above | recall drop within 0.02 | primary met |
| --- | --- | --- | --- | --- | --- |
| 2014 | `flag` | yes | no | yes | no |
| 2014 | `history` | yes | no | yes | no |
| 2015 | `flag` | yes | yes | yes | yes |
| 2015 | `history` | yes | no | no | no |
| 2016 | `flag` | no | yes | yes | no |
| 2016 | `history` | yes | no | no | no |
| 2017 | `flag` | yes | yes | yes | yes |
| 2017 | `history` | no | yes | yes | no |
| 2022 | `flag` | no | yes | yes | no |
| 2022 | `history` | no | yes | yes | no |
| 2023 | `flag` | no | yes | yes | no |
| 2023 | `history` | yes | yes | yes | yes |

Selected alert thresholds:

| year | candidate | alert threshold | calibration recall | calibration precision | fallback |
| --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 0.4627 | 0.1326 | 0.5000 | no |
| 2014 | `flag` | 0.4640 | 0.1313 | 0.5000 | no |
| 2014 | `history` | 0.4278 | 0.1560 | 0.5000 | no |
| 2015 | `control` | 0.2631 | 0.4906 | 0.5000 | no |
| 2015 | `flag` | 0.2636 | 0.4873 | 0.5000 | no |
| 2015 | `history` | 0.2627 | 0.4819 | 0.5000 | no |
| 2016 | `control` | 0.2564 | 0.4969 | 0.5000 | no |
| 2016 | `flag` | 0.2583 | 0.4887 | 0.5000 | no |
| 2016 | `history` | 0.2918 | 0.4052 | 0.5000 | no |
| 2017 | `control` | 0.4145 | 0.2196 | 0.5000 | no |
| 2017 | `flag` | 0.4292 | 0.1963 | 0.5000 | no |
| 2017 | `history` | 0.3538 | 0.2991 | 0.5000 | no |
| 2022 | `control` | 0.1570 | 0.2361 | 0.1996 | yes |
| 2022 | `flag` | 0.1543 | 0.2414 | 0.1974 | yes |
| 2022 | `history` | 0.1622 | 0.2281 | 0.2155 | yes |
| 2023 | `control` | 0.2689 | 0.4461 | 0.5000 | no |
| 2023 | `flag` | 0.2661 | 0.4511 | 0.5000 | no |
| 2023 | `history` | 0.2999 | 0.3767 | 0.5000 | no |

## Descriptive measures

`precision at control recall` is the candidate's precision at the evaluation-year threshold that delivers the control's
alert recall. It uses evaluation labels, is not deployable and is not part of the acceptance. The precision difference is
candidate minus control, paired HARP-cluster bootstrap, 1000 draws, seed 24. AP and the FP origin shares follow the
cycle-25 diagnostic definitions.

| year | candidate | AP | within-flaring-HARP AP | region AP | precision at control recall | precision difference 95% interval | FP share never-flaring HARPs | FP share within 72 h of positive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 0.5015 | 0.5528 | 0.7600 | 0.6825 |  | 0.1437 | 0.7063 |
| 2014 | `flag` | 0.5029 | 0.5529 | 0.7602 | 0.6805 | -0.0092 / 0.0227 | 0.1229 | 0.7243 |
| 2014 | `history` | 0.5136 | 0.5576 | 0.7959 | 0.7159 | -0.0616 / 0.1081 | 0.1047 | 0.7939 |
| 2015 | `control` | 0.4823 | 0.5331 | 0.8264 | 0.5439 |  | 0.0853 | 0.8249 |
| 2015 | `flag` | 0.4833 | 0.5338 | 0.8330 | 0.5488 | -0.0063 / 0.0108 | 0.0794 | 0.8326 |
| 2015 | `history` | 0.4487 | 0.4945 | 0.8593 | 0.5018 | -0.0306 / 0.0645 | 0.0438 | 0.8660 |
| 2016 | `control` | 0.4060 | 0.4853 | 0.6333 | 0.4631 |  | 0.2569 | 0.5688 |
| 2016 | `flag` | 0.4124 | 0.4901 | 0.7125 | 0.4653 | -0.0115 / 0.0256 | 0.2385 | 0.5688 |
| 2016 | `history` | 0.4430 | 0.4976 | 0.7589 | 0.4541 | -0.3060 / 0.1235 | 0.0423 | 0.7606 |
| 2017 | `control` | 0.7975 | 0.8727 | 1.0000 | 0.8676 |  | 0.1111 | 0.8889 |
| 2017 | `flag` | 0.8005 | 0.8746 | 1.0000 | 0.8762 | -0.0045 / 0.0233 | 0.1200 | 0.8800 |
| 2017 | `history` | 0.7571 | 0.8459 | 0.8333 | 0.8592 | -0.4631 / 0.0000 | 0.6344 | 0.3656 |
| 2022 | `control` | 0.4622 | 0.4968 | 0.8315 | 0.4727 |  | 0.0823 | 0.7139 |
| 2022 | `flag` | 0.4599 | 0.4946 | 0.8319 | 0.4725 | -0.0102 / -0.0003 | 0.0845 | 0.7017 |
| 2022 | `history` | 0.4692 | 0.4975 | 0.8628 | 0.4638 | -0.1453 / -0.0331 | 0.1108 | 0.6607 |
| 2023 | `control` | 0.3626 | 0.4057 | 0.8655 | 0.4263 |  | 0.1320 | 0.7561 |
| 2023 | `flag` | 0.3638 | 0.4069 | 0.8668 | 0.4248 | -0.0068 / 0.0003 | 0.1316 | 0.7550 |
| 2023 | `history` | 0.3737 | 0.4142 | 0.8779 | 0.4486 | -0.0210 / 0.0396 | 0.1285 | 0.7719 |

- `history` alert precision is above control in 2014, 2015, 2016, 2023 and below it in 2017, 2022. No paired interval lies above zero.
- AP with `history` is above control in 2014, 2016, 2022, 2023 and below it in 2015, 2017.
- At the control's delivered recall, `history` precision is above control in 2014, 2023 and below it in
  2015, 2016, 2017, 2022. The 2022 loss is therefore not only a threshold shift: at equal recall precision is
  0.4638 against 0.4727.
- `flag` differs little from control (largest absolute alert precision change
  0.0080); its passes in 2015, 2017 are not attributed to content.
- The 72-hour near-miss share of alert FP windows with `history` is 0.6607 in 2022 and
  0.7719 in 2023 (control 0.7139 and 0.7561): the timing problem is not resolved.

## Watch tier

| year | candidate | TP | FP | FN | recall | precision | accuracy | always-negative accuracy | missed positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 2146 | 9020 | 290 | 0.8810 | 0.1922 | 0.8812 | 0.9689 | 6/88 |
| 2014 | `flag` | 2136 | 8911 | 300 | 0.8768 | 0.1934 | 0.8824 | 0.9689 | 6/88 |
| 2014 | `history` | 2191 | 10033 | 245 | 0.8994 | 0.1792 | 0.8688 | 0.9689 | 5/88 |
| 2015 | `control` | 1396 | 8079 | 65 | 0.9555 | 0.1473 | 0.8846 | 0.9793 | 1/57 |
| 2015 | `flag` | 1396 | 7998 | 65 | 0.9555 | 0.1486 | 0.8857 | 0.9793 | 1/57 |
| 2015 | `history` | 1378 | 7551 | 83 | 0.9432 | 0.1543 | 0.8918 | 0.9793 | 1/57 |
| 2016 | `control` | 201 | 1722 | 13 | 0.9393 | 0.1045 | 0.9598 | 0.9950 | 0/8 |
| 2016 | `flag` | 201 | 1742 | 13 | 0.9393 | 0.1034 | 0.9593 | 0.9950 | 0/8 |
| 2016 | `history` | 195 | 1276 | 19 | 0.9112 | 0.1326 | 0.9700 | 0.9950 | 0/8 |
| 2017 | `control` | 243 | 1058 | 22 | 0.9170 | 0.1868 | 0.9456 | 0.9866 | 1/6 |
| 2017 | `flag` | 243 | 1055 | 22 | 0.9170 | 0.1872 | 0.9457 | 0.9866 | 1/6 |
| 2017 | `history` | 244 | 1059 | 21 | 0.9208 | 0.1873 | 0.9456 | 0.9866 | 1/6 |
| 2022 | `control` | 2024 | 11917 | 166 | 0.9242 | 0.1452 | 0.8158 | 0.9666 | 5/72 |
| 2022 | `flag` | 2025 | 11890 | 165 | 0.9247 | 0.1455 | 0.8162 | 0.9666 | 5/72 |
| 2022 | `history` | 2065 | 14935 | 125 | 0.9429 | 0.1215 | 0.7704 | 0.9666 | 4/72 |
| 2023 | `control` | 3695 | 16022 | 396 | 0.9032 | 0.1874 | 0.8307 | 0.9578 | 10/159 |
| 2023 | `flag` | 3697 | 16118 | 394 | 0.9037 | 0.1866 | 0.8298 | 0.9578 | 10/159 |
| 2023 | `history` | 3770 | 17668 | 321 | 0.9215 | 0.1759 | 0.8145 | 0.9578 | 7/159 |

Watch-tier accuracy is below the always-negative accuracy for every candidate in every year.

## Frozen-label results

Copied from `artifacts/activity_history_20261109_r1`, not recomputed: the first test on frozen labels at the prior-year
window recall 0.90 threshold, under the acceptance of `config/activity-history-v1.json`.

| year | candidate | TP | FP | recall | precision | AP | primary met (v1 rule) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 2007 | 7634 | 0.8688 | 0.2082 | 0.5079 |  |
| 2014 | `flag` | 1988 | 7411 | 0.8606 | 0.2115 | 0.5089 | no |
| 2014 | `history` | 2042 | 8134 | 0.8840 | 0.2007 | 0.5176 | no |
| 2015 | `control` | 1308 | 6294 | 0.9653 | 0.1721 | 0.4924 |  |
| 2015 | `flag` | 1319 | 6536 | 0.9734 | 0.1679 | 0.4937 | no |
| 2015 | `history` | 1296 | 6423 | 0.9565 | 0.1679 | 0.4725 | no |
| 2016 | `control` | 162 | 1303 | 0.8950 | 0.1106 | 0.3664 |  |
| 2016 | `flag` | 162 | 1313 | 0.8950 | 0.1098 | 0.3612 | no |
| 2016 | `history` | 158 | 942 | 0.8729 | 0.1436 | 0.4356 | no |
| 2017 | `control` | 235 | 1035 | 0.9289 | 0.1850 | 0.8117 |  |
| 2017 | `flag` | 235 | 1015 | 0.9289 | 0.1880 | 0.8135 | no |
| 2017 | `history` | 234 | 1123 | 0.9249 | 0.1724 | 0.7735 | no |
| 2022 | `control` | 414 | 8949 | 0.9834 | 0.0442 | 0.2800 |  |
| 2022 | `flag` | 414 | 8996 | 0.9834 | 0.0440 | 0.2808 | no |
| 2022 | `history` | 416 | 12238 | 0.9881 | 0.0329 | 0.3094 | no |
| 2023 | `control` | 653 | 4852 | 0.8361 | 0.1186 | 0.2206 |  |
| 2023 | `flag` | 653 | 4818 | 0.8361 | 0.1194 | 0.2209 | yes |
| 2023 | `history` | 719 | 6343 | 0.9206 | 0.1018 | 0.2342 | no |

The result is negative on both bases.

## Limits

Already inspected years: adaptive development evidence, not an independent test. Counts are overlapping forecast windows
and groupings of them, not physical flares. SGAS lists energetic events, not every C-class flare; archived text may differ
from the bytes first issued. `NOAA_ARS` is the definitive JSOC association and was fixed after the fact. The relabelled
labels were recovered through the same SGAS products and `NOAA_ARS` mapping; features use only events in products issued
before the forecast time while labels use peaks after it, so they do not overlap in time, but they share the source's
region assignment errors. Regional history is available for about 52–62% of evaluation windows. The 2022 alert threshold
is a fallback threshold for every candidate. In 2016 and 2017 a few bootstrap draws had no alarm for one candidate and
were dropped (see `draws_used` in `intervals.csv`).

## Reproduction

```sh
python -m scripts.fetch_activity_summaries --output data/activity_summaries_20261109_r1
python -m scripts.audit_activity_history_relabelled --output artifacts/activity_history_relabelled_20261112_r1
```

Config sha256 `4c3da3f030a6154585c016e03277654e8ca1a86dd8275170deadd0b8d149064a`; thresholds sha256 `7f6171291d4b70d379acff7b3598eca38d45a7a4e1344d97bb4da547f96abdec`. Use new output directories;
existing output is not overwritten.
