# HARP 9152 and 9584: label, measurement and warning-time audit

Audit date: 2026-10-27. **No label or feature correction is justified by the
current evidence.** All 257 retained windows, their labels and 24672 feature
values reproduce from verified raw V2 observations. All 768 finite USFLUX pairs
match JSOC headers at relative tolerance 1e-5. The 34 missed positive windows
all have zero missing fraction. They are not 34 independent missed flares:
there are three attached M-class events, each with at least one earlier alarm.
This retrospective subset result does not establish overall event recall.

## Sources and scope

Two full compressed archives were verified against frozen SHA-256, ETag and
byte length; logical Parquet reads selected only HARP 9152/9584 and observation
times before 2024. The downloaded archives contain other periods, but reserved
test records were not logically read or scored. Predictions remain the frozen
2023 ensemble at threshold 0.00931081050648097. No retraining or relabeling occurred.

HEK/SWPC monthly responses were checked against their recorded hashes. Three
bounded definitive SHARP header queries supplied NOAA associations, timestamps,
QUALITY flags and USFLUX. JSOC HTTPS certificate verification failed; the
existing read-only HTTP fallback supplied the headers. Transport was therefore
unauthenticated, with response hashes and attempts preserved. TLS checks were
not disabled. This comparison checks separately retrieved metadata; JSOC and
V2 share underlying observations and are not independent instruments.

## Window reconstruction and missingness

| harp | raw_rows | retained_windows | positive_windows | tp | fn | fp | cadence_gaps | raw_rows_nonfinite | zero_flux_rows | missed_windows_without_missing_values | reproduced_feature_values |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9152 | 1363 | 106 | 24 | 2 | 22 | 14 | 0 | 25 | 8 | 22 | 10176 |
| 9584 | 1365 | 151 | 48 | 36 | 12 | 88 | 0 | 20 | 12 | 12 | 14496 |

There are 1363 and 1365 raw observation rows, with no non-12-minute cadence
steps. Nonfinite rows and zero flux values exist elsewhere in these region
lifetimes. All 34 missed positive windows nevertheless contain finite inputs;
missing-value imputation does not directly explain those misses. Finite values
do not guarantee a clean QUALITY flag or physically reliable measurements.

The raw quality policy retains 261 and 262 candidate windows before label
exclusions; only 106 and 151 remain in the frozen evaluation population.
Therefore gaps in the prediction scatter plots are not evidence of missing
raw observations. The audit does not reintroduce excluded evaluation windows.
The two regions contribute 102 of the incumbent's 8577 false-positive windows;
this audit alone does not explain the full precision problem.

## Event association and time checks

| harp | peak_utc | goes_class | confidence | harp_vote | max_pair_distance_deg | hek_noaa | jsoc_noaa | noaa_matches | header_offset_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9152 | 2023-03-04T07:10:00+00:00 | M1.0 | very_high | 3-0 | 1.414214 | 13243 | 13243 | True | 83.000000 |
| 9584 | 2023-05-24T18:00:00+00:00 | M1.0 | low | 2-1 | 54.203321 | 13315 | 13315 | True | 37.000000 |
| 9584 | 2023-05-30T13:38:00+00:00 | M1.4 | high | 3-0 | 5.099020 | 13315 | 13315 | True | 157.000000 |

The SWPC GOES classes and UTC peak times exactly match all three attached V2
events. JSOC NOAA_ARS maps HARP 9152 to NOAA 13243 and HARP 9584 to NOAA 13315,
matching SWPC. Archive observation times were converted from TAI to UTC using
the 37-second offset applicable here; all frozen labels reproduce with the
half-open target interval [forecast_time, forecast_time + 24h).

The 24 May association remains a limitation: V2 confidence is `low`, vote is
`2-1`, and maximum pairwise source separation is 54.203321 degrees. The matching
SWPC/JSOC NOAA number supports the assignment but does not resolve source-position
disagreement or prove exact spatial origin. No label is changed. The other
associations are `very_high` and `high`; these are source metadata, not new
independent confidence estimates. Nearest header offsets are reported explicitly.

## Window recall versus event warning

| harp | peak_utc | eligible_windows | alarm_windows | first_alarm_utc | lead_to_peak_hours | lead_to_start_hours |
| --- | --- | --- | --- | --- | --- | --- |
| 9152 | 2023-03-04T07:10:00+00:00 | 24 | 2 | 2023-03-04T05:35:23+00:00 | 1.576944 | 1.510278 |
| 9584 | 2023-05-24T18:00:00+00:00 | 24 | 12 | 2023-05-24T06:47:23+00:00 | 11.210278 | 11.093611 |
| 9584 | 2023-05-30T13:38:00+00:00 | 24 | 24 | 2023-05-29T13:47:23+00:00 | 23.843611 | 23.810278 |

For these three selected events, the first eligible retained alarm preceded
the reported event start by 1.510278, 11.093611 and 23.810278 hours. HARP 9152
has only 2 alarmed windows out of 24 positive windows, despite warning before
the flare. HARP 9584 has 12/24 and 24/24. Thus demanding 95% positive-window
recall is different from requiring at least one warning per flare.

This is a post-hoc audit of regions selected for errors, not an independent
3/3 event-detection benchmark. Excluded windows limit lead-time estimates.
The user objective and official metrics are unchanged: precision 0.079622 and
recall 0.950064 across the original validation population.

## Magnetic evolution and quality evidence

| harp | stage | forecast_utc | last_observation_utc | USFLUX | TOTUSJH |
| --- | --- | --- | --- | --- | --- |
| 9152 | first_positive_forecast | 2023-03-03T07:35:23+00:00 | 2023-03-03T07:23:23+00:00 | 2.66823332e+21 | 189.603973 |
| 9152 | first_alarm | 2023-03-04T05:35:23+00:00 | 2023-03-04T05:23:23+00:00 | 7.79794053e+21 | 642.218201 |
| 9584 | first_positive_forecast | 2023-05-23T18:47:23+00:00 | 2023-05-23T18:35:23+00:00 | 3.01531448e+21 | 200.157425 |
| 9584 | first_alarm | 2023-05-24T06:47:23+00:00 | 2023-05-24T06:35:23+00:00 | 7.96035666e+21 | 808.570312 |

Both first events show increasing unsigned flux and total unsigned current
helicity between the first retained positive forecast and the first alarm.
The model's probability also rises. This supports testing evolution-sensitive
features; it does not establish why the model missed earlier windows or prove
that emergence caused the flare. Values are reported in dataset-native units.

| harp | matched_header_times | finite_flux_pairs | flux_matches_rtol_1e5 | header_rows | nonzero_quality | noaa_ars | transport |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9152 | 300 | 300 | 300 | 300 | 9 | 13243 | http |
| 9584 | 468 | 468 | 468 | 477 | 20 | 13315 | http |

There are 9 nonzero QUALITY headers for HARP 9152 and 20 for HARP 9584 within
the queried intervals. The audit records the bits without interpreting them
as a blanket invalidity rule. All 300 and 468 finite time-matched USFLUX pairs
agree with JSOC; the remaining headers have no selected raw timestamp counterpart.
Agreement on USFLUX does not validate all 24 parameters or their physical units.

## Figures

[HARP 9152 — English figure](../artifacts/missed_regions_20261027_r2/harp_9152.en.png)

[HARP 9584 — English figure](../artifacts/missed_regions_20261027_r2/harp_9584.en.png)

Each figure contains frozen probabilities, raw USFLUX, raw TOTUSJH, window
missingness and nonzero QUALITY markers. Red points are positive windows;
red vertical lines are flare peaks; the dashed line is the frozen threshold.
Measurement axes use symmetric log scaling. Markers at -2 in the last panel
indicate QUALITY flags, not negative missingness. Future event markers are
retrospective annotations and are not model inputs.

## Decision and next experiment

Keep the labels, population, model and threshold unchanged. The most useful
next experiment is 24/48-hour evolution features from raw observations, with
training-only preprocessing and chronological comparison. Histories must not
be constructed solely from label-filtered windows. Independently investigate
the low-confidence 24 May spatial association before any proposed correction.
Also inspect the regions contributing most false positives; reducing late
misses in two regions is not itself proof of improved precision.

A separate event-level assessment should report warning lead time and alert
episodes alongside existing window metrics, with event matching and alert
merging rules fixed before evaluation. It must not replace the original recall
objective or rebrand this selected subset as a new success metric.

## Reproduction and evidence

```sh
.venv/bin/python scripts/extract_region_audit.py --output data/region_audit_20261027_r2
.venv/bin/python scripts/fetch_region_headers.py
.venv/bin/python scripts/audit_missed_regions.py --raw data/region_audit_20261027_r2 --output artifacts/missed_regions_20261027_r2
.venv/bin/python scripts/report_missed_regions.py
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_missed_regions_20261027
```

Existing outputs are protected. Repeats require new paths and corresponding
updates to dated report/header input paths. The accepted raw extraction is r2;
the first extraction attempt failed on network resolution. Audit r1 stopped
on a relative-path error before producing a report; r2 is the accepted audit.
Data, raw headers and PNG/CSV/JSON/HTML artifacts stay outside Git. Source code,
paired Markdown reports and the bilingual catalog are version controlled.

| source | SHA-256 |
| --- | --- |
| artifacts/missed_regions_20261027_r2/report.json | 08822ae3b0c90f1b5175d71dca40c198280d9558ea2f106e4480be78ed1ca6d8 |
| artifacts/experiment5_v2_development_20261026_r2/report.json | b57ce8e12de3d18740872b1504f97ff6a9dee22b272143836bb1a739d155ef03 |
| artifacts/experiment5_v2_development_20261026_r2/validation_predictions.parquet | 44a2852948b61cd8b42c77497588f16d76e601221ef1b2f8a923ede56b6d8bff |
| data/region_audit_20261027_r2/report.json | a179f054e2951ffb1d37544f9835f2b8af957ed71a7190e3dccc4fdd268a42f7 |
| config/swan_sf_v2_sources.verified.json | 4da23877d22c2676ab76950c69c016bbe8eaacd8049fc806dad078752feafa3d |
| artifacts/v2_development_features_20261025_r2/report.json | 62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82 |
| artifacts/v2_development_features_20261025_r2/shards/partition-1-d917a8a4fd4a.parquet | e526b9b806a8b85b34431b09cc47ac7a97a69f07c69b1ac6a71d91b61d9b1aef |
| artifacts/v2_development_features_20261025_r2/shards/partition-2-05b11f13de93.parquet | eb904ebc6e9370551c9f0f56e8bd43757764ed581992d590bbed32c417543cab |
| artifacts/hek_major_inventory_20261025_r2/report.json | 1d82d652504e162c35138ca19815f9c8dab9312eb18e1848c54123e837c0b4b5 |
| artifacts/hek_major_inventory_20261025_r2/events.csv | f0431c27d11abf7b2908f588634eccd61d960d5c1e67b1b4ffcfd2a5416afb0f |
| artifacts/hek_major_inventory_20261025_r2/raw/2023-03.json | 2e3c7a39c9ae0dde2164cd5df8f2bd1d624500f04b491c56b58817604fc894f3 |
| artifacts/hek_major_inventory_20261025_r2/raw/2023-05.json | 39da653a72b3ca30b9b5cdeaa4e57819460167c7fefd059f0fc5ca2c553a7984 |
| data/region_headers_20261027/manifest.json | 06a998be0e7ff3e6c7d4fa8dc764fb71ac24910ef0cdfd465c712294d7c6d6ae |
| data/region_headers_20261027/harp_9152_2023.03.02.json | d46152e407c8caccce03033621e8eab40baec30e60026dbd86e959090378f4f2 |
| data/region_headers_20261027/harp_9584_2023.05.23.json | a5e09376e15145fd55f2c96a884f0997c210bf547e69e44b5906e46926398b24 |
| data/region_headers_20261027/harp_9584_2023.05.29.json | b952d9e84be1bd7be66ba89b566a8d3610338d6d06c8e556d51666257ab8e9ae |
| artifacts/v2_label_inventory_20261025_r1/unassigned_major_events.csv | e584b58fbea9f1e03f025df75edae9312303f0dafd82db04347a5ba7fc71be8f |
| data/region_audit_20261027_r2/harp_9152.parquet | 4be4e9fac1807c09b5ec69f0b72a47fe5dd5280a53074d45a1b75ab270438aac |
| data/region_audit_20261027_r2/harp_9584.parquet | f50b5202e9aaba476e93b2f81e9ed8b9d73e5d9b3fd59869a0235b41c409ae5e |

