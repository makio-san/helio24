# Regional context sources: acquisition, provenance and coverage

## Decision and scope

Two public sources were acquired and audited under [the frozen source file](../config/region-context-sources-v1.json)
so that causal regional context can later be attached to HARP forecast windows without assuming availability.
No feature was built, no model was fitted, no label changed and the reserved 2024–2025 period was not
touched. This report says what the sources are, what they prove about availability and how much of the
development data they cover. It does not say that they improve any metric.

Decisions:

1. The NOAA SWPC Solar Region Summary (SRS) carries its own issue time in every product. It can be used
   causally: a forecast at time t may read the latest SRS issued at or before t minus a 30 minute margin.
2. The JSOC HARP to NOAA association (`NOAA_ARS`) has no stated availability time. It is used only on days
   when the NOAA number also appears in the SRS available at issue time, which bounds availability by the SRS.
3. Coverage is high where it matters: 97.5% of positive development windows belong to a HARP with a NOAA
   number and 90.8% have that number in the SRS available at issue time, against 59.1% and 43.5% of all
   windows. Numbered-region status alone does not remove false alarms, because the frozen baseline already
   rarely alarms in unnumbered HARPs (see the diagnostic below). Any gain must come from the SRS content.

## Sources

| source | files | retrieved | bytes | issue time in product |
| --- | --- | --- | --- | --- |
| SRS | 4993 | 4989 | 3703125 | yes |
| JSOC NOAA_ARS | 164 | 164 | 2150086 | no |

SRS files were fetched over HTTPS only from `ngdc.noaa.gov`. Four days were unavailable at the archive
(2016-07-19, 2019-04-27, 2019-08-02, 2022-12-17) and two archived files are empty (2019-08-04, 2019-08-07), so
4987 of 4993 days have a parseable issue time. The issue time is 00:30 UTC in 99.4% of files; the rest are
later the same day, up to 22:00 UTC. The JSOC queries used the HTTP fallback in all 164 months because the
server presents a self-signed certificate; the manifest records this per query. The SRS magnetic-class
vocabulary over the period is Alpha, Beta, Beta-Delta, Beta-Gamma, Beta-Gamma-Delta and Gamma; 17283 region
rows were parsed. 1960 HARPs carry at least one NOAA number.

## Coverage of the development data

A window counts as "in available SRS" when one of its HARP's NOAA numbers on that date appears in the latest
SRS issued at or before the forecast time minus 30 minutes.

| year | windows | positives | HARPs | windows with NOAA number | windows in available SRS | positives with NOAA number | positives in available SRS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2010 | 21176 | 124 | 175 | 63.9% | 43.4% | 100.0% | 75.0% |
| 2011 | 61553 | 1526 | 462 | 65.8% | 49.5% | 99.5% | 94.3% |
| 2012 | 65974 | 1309 | 550 | 58.2% | 43.3% | 97.8% | 92.7% |
| 2013 | 75184 | 1311 | 597 | 63.0% | 47.1% | 100.0% | 93.8% |
| 2014 | 76206 | 2363 | 638 | 52.3% | 41.1% | 92.1% | 86.7% |
| 2015 | 70341 | 1403 | 610 | 55.2% | 40.3% | 98.1% | 93.7% |
| 2016 | 43267 | 205 | 361 | 54.9% | 39.7% | 100.0% | 89.3% |
| 2017 | 19739 | 253 | 167 | 60.1% | 45.8% | 100.0% | 100.0% |
| 2018 | 7932 | 0 | 76 | 63.8% | 40.0% | — | — |
| 2019 | 4941 | 0 | 44 | 62.9% | 39.8% | — | — |
| 2020 | 9867 | 0 | 78 | 73.1% | 44.1% | — | — |
| 2021 | 28369 | 204 | 258 | 65.6% | 45.9% | 100.0% | 89.2% |
| 2022 | 50756 | 421 | 528 | 61.8% | 44.8% | 100.0% | 90.3% |
| 2023 | 60366 | 781 | 703 | 53.9% | 40.5% | 100.0% | 83.9% |

## Where the frozen baseline's false alarms fall

This diagnostic reads the frozen annual baseline predictions of already inspected years. It is adaptive and
descriptive; it was computed after the sources were acquired and informs the next protocol.

| year | FP windows | FP in available SRS | FP in unnumbered HARPs | TP | TP in available SRS | positives | positives in available SRS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 13886 | 11113 | 1734 | 2184 | 1921 | 2310 | 1996 |
| 2015 | 11453 | 10193 | 124 | 1346 | 1257 | 1355 | 1266 |
| 2016 | 2289 | 2060 | 62 | 176 | 159 | 181 | 159 |
| 2017 | 1287 | 1186 | 30 | 237 | 237 | 253 | 253 |
| 2018 | 359 | 347 | 0 | 0 | 0 | 0 | 0 |
| 2022 | 10072 | 8917 | 67 | 415 | 374 | 421 | 380 |
| 2023 | 5992 | 5708 | 2 | 691 | 602 | 781 | 655 |

Between 80.0% (2014) and 96.7% (2018) of false-alarm windows fall inside regions that are in the available
SRS, and false alarms in unnumbered HARPs are rare (2 of 5992 in 2023). A flag for "numbered region" would
therefore remove few false alarms. The information that could help is the SRS content of numbered regions:
magnetic class, McIntosh class, area and spot count. Positives outside the available SRS (16.1% in 2023) are
regions numbered later or windows before the day's SRS; their context must be treated as missing, not quiet.

## Limits

- The SRS issue time proves when the product was issued, not that every historical reader received it at that
  minute; the 30 minute margin is a project convention, not a measured latency.
- `NOAA_ARS` is a definitive-series association assigned by the HARP pipeline; its own availability is unknown
  and is bounded here by the SRS only.
- The archive versions were retrieved on 2026-11-09; later retrieval may differ. Compare manifests before
  attributing changes to code.
- The false-alarm diagnostic uses evaluation outcomes of already inspected years and is not evidence of any
  improvement.

## Reproduction

```sh
python scripts/fetch_region_summaries.py --output data/region_summaries_20261109_r1
python scripts/fetch_harp_noaa_mapping.py --output data/harp_noaa_mapping_20261109_r1
python scripts/audit_region_context_sources.py --srs data/region_summaries_20261109_r1 --mapping data/harp_noaa_mapping_20261109_r1 --output artifacts/region_context_sources_20261109_r1
python -m pytest -q tests/test_region_context_sources.py
```
