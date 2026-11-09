# Issued SGAS flare-history context: source and results (2026-11-09)

## Decision

Negative result. Adding causal flare history from issued NOAA SGAS products to the 96 magnetic summaries does not
raise precision at the project operating point (prior-year threshold at window recall 0.90). The `history`
candidate meets the primary acceptance in 0 of 6 years and the `flag` candidate in 1 of 6. No model is
promoted and no alert or threshold is changed. The reserved 2024–2025 test was not accessed. The protocol
[`config/activity-history-v1.json`](../config/activity-history-v1.json) was frozen and committed before any
candidate result.

## Why this source

Flare history was blocked because solar event reports carry only an archive `:Created:` time
([probe](history-publication-probe-20261107.md)). The Joint USAF/NOAA Solar and Geophysical Activity Summary
(SGAS) carries an `:Issued:` time in every product and lists the previous UT day's energetic events with NOAA
region number and X-ray class, plus the X-ray background.

| item | value |
| --- | --- |
| archive | `https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_geophysical_activity_summaries/` |
| period | 2010-05-01 to 2023-12-31 |
| files retrieved / expected | 4980 / 4993 |
| bytes | 6020323 |
| reports with a parsed issue time | 4979 |
| event rows parsed | 12286 |
| unparsed event rows | 0 |

Dates without a file: 2015-02-26, 2015-11-07, 2017-07-07, 2019-04-27, 2019-08-02, 2019-08-27, 2021-08-04, 2021-09-28, 2022-01-01, 2022-01-02, 2022-01-03, 2022-04-08, 2022-12-17. One retrieved file has no parseable issue time and is not used. Of the parsed
reports 4937 were issued at 0245 UTC. SGAS lists energetic events, not every C-class flare.

## Method

A window at forecast time t uses only products issued at or before t minus 30 minutes. Regional events are those
whose NOAA number is in the HARP's `NOAA_ARS` on the forecast date. A HARP without a NOAA number, or with no
product in the preceding 75 hours, has `history_available` = 0 and missing regional values. Fifteen features:
`history_available`, `reports_3d`, `hours_since_issue`, `reg_c_1d`, `reg_mx_1d`, `reg_c_3d`, `reg_mx_3d`,
`reg_events_3d`, `reg_max_logflux_3d`, `reg_mx_life`, `reg_max_logflux_life`, `disk_mx_1d`, `disk_mx_3d`,
`disk_max_logflux_1d`, `xray_background_log`. `flag` refits the unchanged recipes with the first three only;
`history` uses all fifteen. No hyperparameter search; 24 constituent fits.

Evaluation-year coverage:

| year | history_available share | reg_mx_3d > 0 share |
| --- | --- | --- |
| 2014 | 0.5203 | 0.0454 |
| 2015 | 0.5482 | 0.0405 |
| 2016 | 0.5499 | 0.0066 |
| 2017 | 0.6040 | 0.0198 |
| 2022 | 0.6178 | 0.0514 |
| 2023 | 0.5388 | 0.0736 |

## Results

| year | candidate | TP | FP | FN | recall | precision | accuracy | always-negative accuracy | episode precision | positive runs alarmed | AP | Brier | log loss | primary met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 2007 | 7634 | 303 | 0.8688 | 0.2082 | 0.8945 | 0.9693 | 0.1636 | 77/83 | 0.5079 | 0.0207 | 0.0765 |  |
| 2014 | flag | 1988 | 7411 | 322 | 0.8606 | 0.2115 | 0.8972 | 0.9693 | 0.1688 | 76/83 | 0.5089 | 0.0207 | 0.0766 | no |
| 2014 | history | 2042 | 8134 | 268 | 0.8840 | 0.2007 | 0.8883 | 0.9693 | 0.1335 | 77/83 | 0.5176 | 0.0206 | 0.0765 | no |
| 2015 | control | 1308 | 6294 | 47 | 0.9653 | 0.1721 | 0.9083 | 0.9804 | 0.1138 | 51/51 | 0.4924 | 0.0136 | 0.0478 |  |
| 2015 | flag | 1319 | 6536 | 36 | 0.9734 | 0.1679 | 0.9049 | 0.9804 | 0.1132 | 51/51 | 0.4937 | 0.0135 | 0.0479 | no |
| 2015 | history | 1296 | 6423 | 59 | 0.9565 | 0.1679 | 0.9062 | 0.9804 | 0.1000 | 50/51 | 0.4725 | 0.0139 | 0.0487 | no |
| 2016 | control | 162 | 1303 | 19 | 0.8950 | 0.1106 | 0.9692 | 0.9958 | 0.0347 | 7/7 | 0.3664 | 0.0033 | 0.0145 |  |
| 2016 | flag | 162 | 1313 | 19 | 0.8950 | 0.1098 | 0.9690 | 0.9958 | 0.0355 | 7/7 | 0.3612 | 0.0033 | 0.0146 | no |
| 2016 | history | 158 | 942 | 23 | 0.8729 | 0.1436 | 0.9776 | 0.9958 | 0.0556 | 7/7 | 0.4356 | 0.0030 | 0.0133 | no |
| 2017 | control | 235 | 1035 | 18 | 0.9289 | 0.1850 | 0.9461 | 0.9870 | 0.0781 | 5/6 | 0.8117 | 0.0049 | 0.0205 |  |
| 2017 | flag | 235 | 1015 | 18 | 0.9289 | 0.1880 | 0.9471 | 0.9870 | 0.0758 | 5/6 | 0.8135 | 0.0049 | 0.0204 | no |
| 2017 | history | 234 | 1123 | 19 | 0.9249 | 0.1724 | 0.9415 | 0.9870 | 0.0556 | 5/6 | 0.7735 | 0.0053 | 0.0227 | no |
| 2022 | control | 414 | 8949 | 7 | 0.9834 | 0.0442 | 0.8235 | 0.9917 | 0.0316 | 16/16 | 0.2800 | 0.0071 | 0.0292 |  |
| 2022 | flag | 414 | 8996 | 7 | 0.9834 | 0.0440 | 0.8226 | 0.9917 | 0.0311 | 16/16 | 0.2808 | 0.0071 | 0.0292 | no |
| 2022 | history | 416 | 12238 | 5 | 0.9881 | 0.0329 | 0.7588 | 0.9917 | 0.0231 | 16/16 | 0.3094 | 0.0071 | 0.0310 | no |
| 2023 | control | 653 | 4852 | 128 | 0.8361 | 0.1186 | 0.9175 | 0.9871 | 0.0905 | 35/38 | 0.2206 | 0.0112 | 0.0440 |  |
| 2023 | flag | 653 | 4818 | 128 | 0.8361 | 0.1194 | 0.9181 | 0.9871 | 0.0928 | 35/38 | 0.2209 | 0.0112 | 0.0440 | yes |
| 2023 | history | 719 | 6343 | 62 | 0.9206 | 0.1018 | 0.8939 | 0.9871 | 0.0745 | 38/38 | 0.2342 | 0.0110 | 0.0422 | no |

Primary acceptance per year: episode precision higher, FP windows lower, alarmed positive runs not below, window
recall drop at most 0.02, all against control.

- Precision: `history` is above control only in 2016 (0.1436 against 0.1106) and below it in the other five years.
- Accuracy stays below the always-negative accuracy for every candidate in every year. Exceeding it requires
  TP greater than FP, that is precision above 0.50.
- AP: `history` is above control in 2014, 2016, 2022 and 2023 and below it in 2015 and 2017. Ranking gains did not
  carry to the prior-year threshold: the `history` threshold is lower than control in every year and admits more
  false alarms in 2014, 2015, 2017, 2022 and 2023.
- `flag` differs from control only by refitting noise; its single pass in 2023 is not attributed to content.

Paired full-HARP bootstrap intervals (1000 draws, seed 24) are in `intervals.csv`.

## Limits

Already inspected years: adaptive development evidence, not an independent test. Counts are overlapping forecast
windows and groupings of them, not physical flares. Archived SGAS text may differ from the bytes first issued.
`NOAA_ARS` is the definitive JSOC association. Regional history is available for only about 52–62% of evaluation
windows.

## Reproduction

```sh
python -m scripts.fetch_activity_summaries --output data/activity_summaries_20261109_r1
python -m scripts.audit_activity_history --output artifacts/activity_history_20261109_r1
```

Config sha256 `f8797376e56bf6be386181fd160f3fde21e8fa9797efe5274316b577cf195d40`; thresholds sha256 `a9bfefa4fe76ed6b4644e2fb2da6277c74bc1b159d8fcf925656b6a29b34f533`. Use new output directories; existing output is not overwritten.
