# Regional context results: issued SRS features do not raise precision

## Decision and scope

The [frozen protocol](region-context-protocol-20261109.md) was run once. The 96 magnetic summaries plus
causal SRS context were refitted with the unchanged walk-forward recipes in the annual folds of the frozen
baseline (28 constituent fits); every fold audit equalled the frozen baseline audit. Thresholds of all candidates
were written to disk and hashed (SHA256 `dc2a7d1606234d72c400b07c4b45de5dec267b9d34460330d38a6082566b0f84`) before any evaluation label was read. No label changed and
the reserved 2024–2025 test stayed closed.

Decisions:

1. `context` passes the four per-year conditions in 1 of 6 positive years (2015). `flag`, the refit with only
   the availability flag and the hours since issue, passes in 4 of 6 (2014, 2016, 2022, 2023). Neither passes
   all six years, so the all-year result is negative for both.
2. The SRS content is not credited with any gain. Where `flag` passes, `context` does not; where `context`
   passes (2015), the gain is 156 false-alarm windows out of 11453 and an episode-precision rise from 0.0669
   to 0.0690. In 2014, 2016, 2022 and 2023 `context` has more false alarms than the control.
3. Nothing is adopted. No alert, threshold or model changes. Magnetic class, McIntosh class, area, spot count
   and region age from the issued SRS do not add separating power on top of the SHARP summaries in this record
   with this recipe.

## Context availability in the folds

Share of windows with `srs_available` 1 by fold role. Where it is 0 every context value is missing and passes
through the imputer with a missing indicator.

| year | train | calibration | evaluation |
| --- | --- | --- | --- |
| 2014 | 45.9% | 46.7% | 40.8% |
| 2015 | 46.3% | 40.8% | 39.8% |
| 2016 | 45.0% | 39.8% | 39.8% |
| 2017 | 44.1% | 39.8% | 46.2% |
| 2018 | 43.6% | 46.2% | 40.7% |
| 2022 | 43.6% | 45.9% | 44.8% |
| 2023 | 43.8% | 44.8% | 40.5% |

## Acceptance outcome

| candidate | years_met | required_years | all_year_primary | met_years |
| --- | --- | --- | --- | --- |
| flag | 4 | 6 | no | [2014, 2016, 2022, 2023] |
| context | 1 | 6 | no | [2015] |

| year | candidate | episode_precision_higher | fp_lower | positive_runs_alarmed_not_below | recall_drop_ok | primary_met |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | flag | yes | yes | yes | yes | yes |
| 2014 | context | no | no | yes | yes | no |
| 2015 | flag | yes | no | yes | yes | no |
| 2015 | context | yes | yes | yes | yes | yes |
| 2016 | flag | yes | yes | yes | yes | yes |
| 2016 | context | no | no | yes | yes | no |
| 2017 | flag | no | no | yes | yes | no |
| 2017 | context | no | no | yes | yes | no |
| 2022 | flag | yes | yes | yes | yes | yes |
| 2022 | context | yes | no | yes | yes | no |
| 2023 | flag | yes | yes | yes | yes | yes |
| 2023 | context | no | no | yes | yes | no |

The `flag` passes are small refitting effects: the false-alarm reduction is 125 windows in 2014, 55 in 2016,
204 in 2022 and 19 in 2023, each under 2.1% of the control's false alarms, and 2016 loses three true
positives. They cannot be attributed to SRS content because `flag` carries none.

## Metrics by year and candidate

| year | candidate | threshold | TP | FP | recall | recall ≥ 0.95 | precision | episodes | episode precision | alarmed positive runs | AP | Brier | log loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 0.011475 | 2184 | 13886 | 0.9455 | no | 0.1359 | 686 | 0.0977 | 80 of 83 | 0.5079 | 0.020661 | 0.076538 |
| 2014 | flag | 0.011701 | 2183 | 13761 | 0.9450 | no | 0.1369 | 669 | 0.1001 | 80 of 83 | 0.5082 | 0.020658 | 0.076536 |
| 2014 | context | 0.009703 | 2202 | 14833 | 0.9532 | yes | 0.1293 | 734 | 0.0913 | 80 of 83 | 0.4992 | 0.020852 | 0.076997 |
| 2015 | control | 0.018839 | 1346 | 11453 | 0.9934 | yes | 0.1052 | 568 | 0.0669 | 51 of 51 | 0.4924 | 0.013564 | 0.047847 |
| 2015 | flag | 0.018485 | 1346 | 11551 | 0.9934 | yes | 0.1044 | 561 | 0.0677 | 51 of 51 | 0.4930 | 0.013557 | 0.047811 |
| 2015 | context | 0.018868 | 1347 | 11297 | 0.9941 | yes | 0.1065 | 551 | 0.0690 | 51 of 51 | 0.5118 | 0.013329 | 0.047211 |
| 2016 | control | 0.030831 | 176 | 2289 | 0.9724 | yes | 0.0714 | 204 | 0.0196 | 7 of 7 | 0.3664 | 0.003263 | 0.014523 |
| 2016 | flag | 0.031593 | 173 | 2234 | 0.9558 | yes | 0.0719 | 198 | 0.0253 | 7 of 7 | 0.3620 | 0.003273 | 0.014583 |
| 2016 | context | 0.026925 | 176 | 2380 | 0.9724 | yes | 0.0689 | 208 | 0.0192 | 7 of 7 | 0.3645 | 0.003224 | 0.014176 |
| 2017 | control | 0.012000 | 237 | 1287 | 0.9368 | no | 0.1555 | 85 | 0.0588 | 5 of 6 | 0.8117 | 0.004907 | 0.020488 |
| 2017 | flag | 0.010120 | 238 | 1370 | 0.9407 | no | 0.1480 | 94 | 0.0532 | 5 of 6 | 0.8118 | 0.004909 | 0.020551 |
| 2017 | context | 0.012045 | 237 | 1303 | 0.9368 | no | 0.1539 | 86 | 0.0581 | 5 of 6 | 0.7988 | 0.005077 | 0.021297 |
| 2022 | control | 0.008994 | 415 | 10072 | 0.9857 | yes | 0.0396 | 622 | 0.0257 | 16 of 16 | 0.2800 | 0.007064 | 0.029196 |
| 2022 | flag | 0.009298 | 415 | 9868 | 0.9857 | yes | 0.0404 | 608 | 0.0263 | 16 of 16 | 0.2791 | 0.007064 | 0.029208 |
| 2022 | context | 0.009014 | 415 | 10192 | 0.9857 | yes | 0.0391 | 610 | 0.0262 | 16 of 16 | 0.2775 | 0.007043 | 0.029255 |
| 2023 | control | 0.018203 | 691 | 5992 | 0.8848 | no | 0.1034 | 475 | 0.0842 | 36 of 38 | 0.2206 | 0.011195 | 0.043996 |
| 2023 | flag | 0.018357 | 689 | 5973 | 0.8822 | no | 0.1034 | 474 | 0.0844 | 36 of 38 | 0.2205 | 0.011194 | 0.044039 |
| 2023 | context | 0.017289 | 686 | 6374 | 0.8784 | no | 0.0972 | 512 | 0.0781 | 36 of 38 | 0.2258 | 0.011145 | 0.044139 |

## Distance to the precision target

| year | candidate | TP | FP | precision | FP allowed for 0.30 | FP excess |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 2184 | 13886 | 0.1359 | 5096 | 8790 |
| 2014 | flag | 2183 | 13761 | 0.1369 | 5093 | 8668 |
| 2014 | context | 2202 | 14833 | 0.1293 | 5138 | 9695 |
| 2015 | control | 1346 | 11453 | 0.1052 | 3140 | 8313 |
| 2015 | flag | 1346 | 11551 | 0.1044 | 3140 | 8411 |
| 2015 | context | 1347 | 11297 | 0.1065 | 3143 | 8154 |
| 2016 | control | 176 | 2289 | 0.0714 | 410 | 1879 |
| 2016 | flag | 173 | 2234 | 0.0719 | 403 | 1831 |
| 2016 | context | 176 | 2380 | 0.0689 | 410 | 1970 |
| 2017 | control | 237 | 1287 | 0.1555 | 553 | 734 |
| 2017 | flag | 238 | 1370 | 0.1480 | 555 | 815 |
| 2017 | context | 237 | 1303 | 0.1539 | 553 | 750 |
| 2022 | control | 415 | 10072 | 0.0396 | 968 | 9104 |
| 2022 | flag | 415 | 9868 | 0.0404 | 968 | 8900 |
| 2022 | context | 415 | 10192 | 0.0391 | 968 | 9224 |
| 2023 | control | 691 | 5992 | 0.1034 | 1612 | 4380 |
| 2023 | flag | 689 | 5973 | 0.1034 | 1607 | 4366 |
| 2023 | context | 686 | 6374 | 0.0972 | 1600 | 4774 |

No candidate moves any year closer to precision 0.30 by more than 204 false-alarm windows, against an excess
of 734 to 9104 windows.

## Year without positive windows

| candidate | threshold | FP windows | episodes |
| --- | --- | --- | --- |
| control | 0.004351 | 359 | 30 |
| flag | 0.004148 | 374 | 32 |
| context | 0.004442 | 444 | 41 |

## Uncertainty

Paired full-HARP bootstrap intervals (1000 draws, seed 24) of differences against the control. A negative
false-alarm difference means fewer false-alarm windows. The intervals are conditional on the frozen thresholds
and exclude refitting and threshold-selection uncertainty; they are not corrected for multiple comparisons.

| year | candidate | episode precision diff lower | episode precision diff upper | FP window diff lower | FP window diff upper |
| --- | --- | --- | --- | --- | --- |
| 2014 | flag | 0.0005 | 0.0047 | -173.0 | -87.0 |
| 2014 | context | -0.0152 | 0.0011 | 659.0 | 1260.0 |
| 2015 | flag | -0.0012 | 0.0031 | 64.0 | 132.0 |
| 2015 | context | -0.0023 | 0.0071 | -277.0 | -34.0 |
| 2016 | flag | 0.0000 | 0.0175 | -95.0 | -25.0 |
| 2016 | context | -0.0045 | 0.0018 | -78.0 | 245.1 |
| 2017 | flag | -0.0251 | 0.0046 | 41.0 | 130.0 |
| 2017 | context | -0.0169 | 0.0156 | -79.0 | 94.0 |
| 2022 | flag | -0.0003 | 0.0017 | -261.0 | -155.0 |
| 2022 | context | -0.0009 | 0.0021 | -25.0 | 265.0 |
| 2023 | flag | -0.0015 | 0.0023 | -40.0 | 0.0 |
| 2023 | context | -0.0145 | 0.0017 | 197.0 | 576.1 |

## Why the context does not help

The SRS describes a numbered region once a day as of 24:00 UT of the previous day; the SHARP summaries describe
the same region's photospheric field hourly. Magnetic class and McIntosh class are coarse labels that the
continuous field measures already encode in large part, and 55% to 60% of windows have no SRS row at all.
The remaining difference between a flaring and a persistently alarmed quiet region is not captured by either
source at this cadence. The result rejects this feature set with this recipe; it does not show that no use of
the SRS can help.

## Limits

- Adaptive development evidence on already inspected years, not an independent test. Counts are overlapping
  forecast windows and groupings of them, not physical flares.
- The feature list was fixed after seeing where false alarms concentrate in these same years; this adaptivity
  would bias the result toward a pass, and the result is still negative.
- One recipe, one encoding and one availability margin were tested, as frozen.
- The SRS issue time proves issuance, not reception; the 30 minute margin is a project convention.

## Reproduction

```sh
python scripts/audit_region_context_features.py --output artifacts/region_context_20261109_r1
python -m pytest -q tests/test_region_context_features.py tests/test_region_context_protocol.py
```
