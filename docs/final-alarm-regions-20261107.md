# Final annual false-alarm localization

## Scope and decision

This extends regional error localization to all seven completed annual periods. It
compares the chronological TCN with the frozen baseline at their own unchanged,
prior-year calibration thresholds. This is not a matched-recall comparison. No fitting,
threshold tuning, relabeling, model promotion or reserved 2024–2025 test access occurred.
Counts are overlapping forecast windows, not independent flare events or notifications.

The source report SHA256 is
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`.
Each included prediction, threshold and finished record was checked against that manifest.
All fourteen model/year FP totals also match the independently frozen final comparison.

Do not extend this TCN recipe with more epochs on the strength of isolated gains.
The newer years confirm substantial false-alarm costs. The causal-history direction
remains an untested hypothesis with an unresolved source-availability gate.

## Paired additions and removals

| year | extra_fp | removed_fp | shared_fp | extra_tp | removed_tp | candidate_fp | baseline_fp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 6773 | 1020 | 12866.000000 | 53 | 53 | 19639 | 13886 |
| 2015 | 2541 | 2857 | 8596.000000 | 1 | 31 | 11137 | 11453 |
| 2016 | 4446 | 350 | 1939.000000 | 1 | 4 | 6385 | 2289 |
| 2017 | 565 | 314 | 973.000000 | 0 | 0 | 1538 | 1287 |
| 2018 | 221 | 62 | 297.000000 | 0 | 0 | 518 | 359 |
| 2022 | 4034 | 1135 | 8937.000000 | 0 | 13 | 12971 | 10072 |
| 2023 | 6678 | 187 | 5805.000000 | 42 | 16 | 12483 | 5992 |

`extra_fp` counts negative windows alarmed only by TCN; `removed_fp` counts those
alarmed only by baseline; `shared_fp` counts both. TP columns use the same paired
switches on positive windows. Every year satisfies extra FP minus removed FP equals
candidate FP minus baseline FP. The original 2014–2016 paired counts are reproduced.

In 2022, there are 2899 net extra false alarms, no gained positive windows and 13 lost
positive windows. In 2023, there are 6491 net extra false alarms and 26 net gained
positive windows (42 gained, 16 lost). These are descriptive tradeoffs, not estimates
of the value of an operational warning. In 2018 no positive windows exist: the 159 net
extra false alarms remain measurable, while recall cannot be evaluated.

## Regional concentration

| year | top10_extra_fp | top10_extra_fp_share | top10_negative_share | zero_positive_region_extra_fp |
| --- | --- | --- | --- | --- |
| 2014 | 1473 | 0.217481 | 0.038111 | 6110 |
| 2015 | 777 | 0.305785 | 0.041426 | 2473 |
| 2016 | 1557 | 0.350202 | 0.064080 | 4233 |
| 2017 | 469 | 0.830088 | 0.137373 | 562 |
| 2018 | 211 | 0.954751 | 0.254392 | 221 |
| 2022 | 1141 | 0.282846 | 0.047839 | 3939 |
| 2023 | 1439 | 0.215484 | 0.038617 | 6006 |

The ten regions are selected after observing each year's extra FP, with HARP ID used
to break ties. Their shares are fractions on a 0–1 scale. Compare extra-FP share with
negative-window exposure, not with an equal-region assumption. In 2022 the top ten
account for 0.282846 of extra FP and 0.047839 of negative windows; in 2023 the shares
are 0.215484 and 0.038617. Concentration varies across years and is not confined to
2016. High concentration in 2018 does not establish useful positive-event discrimination.

`zero_positive_region_extra_fp` uses the entire evaluation period's outcomes; it does
not mean that a region had no past flares. These retrospective groups and rankings
must never become forecast-time features or an exclusion list. This audit cannot show
that flare-history features will help. No uncertainty intervals or significance tests
were added for these post-hoc shares. Existing paired metric intervals remain in the
[final evaluation](temporal-evaluation-final-20261106.md). Region-level data are retained
in the local `regions.csv`; no global average hides period differences.

## Source availability and recovery

NOAA's [historical report documentation](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/docs/SolarEventReport.pdf)
explicitly describes revisions to prior daily lists. It is a historical document, not
proof of current update cadence. The inspected [September 2023 index](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2023/09/)
lists daily files; it does not supply an intraday version history. Neither observation
establishes that no version archive exists elsewhere. First publication, exact content
availability and contemporaneous HARP association remain unverified; training stays
blocked under the selected protocol rather than assuming these timestamps.

The missing historical `2019/predictions.parquet` was still absent. iCloud Data Recovery
showed a loading indicator on this attempt; the later accessibility read could not
access the Safari window. No file list or successful restore was verified. This does
not establish permanent loss. The completed experiment and its existing local backup
remain usable; this audit does not depend on that missing historical control file.

## Reproduction

```sh
export PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261107
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/audit_final_alarm_regions.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --output artifacts/final_alarm_regions_20261107_r2
"$PY" -m pytest tests/test_final_alarm_regions.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261107_r2
```

Use fresh output names. Original results are in
`artifacts/final_alarm_regions_20261107_r1`; generated files remain outside Git. Both
language editions cover the same results and limitations. This analysis is adaptive
development evidence, not an independent test of the next proposed model.
