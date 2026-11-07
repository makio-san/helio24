# Flare-history source timing probe and recovery update

## Decision and scope

Continue provenance work, not model fitting. Seven small NOAA solar-event reports
were retrieved over HTTPS: September 3 in each eligible development year. This is a
fixed-date diagnostic sample motivated by the existing 2014 case, not a random sample,
full-year coverage audit or estimate of typical publication delay. No reserved
2024–2025 data were accessed, no labels changed and no new metrics were produced.

The archived `:Created:` header is later than the report date in every sampled file.
The interval below is measured from midnight at the start of the report day, not from
an individual flare and not from first publication.

| year | report_date | created_utc | hours_after_report_day_start |
| --- | --- | --- | --- |
| 2014 | 2014-09-03 | 2014-09-05T03:57:00+00:00 | 51.95 |
| 2015 | 2015-09-03 | 2015-09-04T15:27:00+00:00 | 39.45 |
| 2016 | 2016-09-03 | 2016-09-06T03:57:00+00:00 | 75.95 |
| 2017 | 2017-09-03 | 2017-09-05T03:57:00+00:00 | 51.95 |
| 2018 | 2018-09-03 | 2018-09-05T03:57:00+00:00 | 51.95 |
| 2022 | 2022-09-03 | 2022-09-06T03:57:00+00:00 | 75.95 |
| 2023 | 2023-09-03 | 2023-09-06T03:57:00+00:00 | 75.95 |

Official inputs: [2014](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2014/09/20140903events.txt),
[2015](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2015/09/20150903events.txt),
[2016](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2016/09/20160903events.txt),
[2017](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2017/09/20170903events.txt),
[2018](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2018/09/20180903events.txt),
[2022](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2022/09/20220903events.txt),
[2023](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2023/09/20230903events.txt).

## What this establishes and does not establish

These exact document versions cannot simply be assigned to every earlier event time.
`:Created:` is evidence of document generation, not proof of first public availability
or an immutable version history. Earlier operational versions may have existed. The
[SWPC user guide](https://www.swpc.noaa.gov/sites/default/files/images/u2/Usr_guide.pdf)
describes forecaster editing and subsequent weekly review of event lists; retrieving
the final archive does not recover all versions available to historical forecasts.

Adding an arbitrary fixed delay or substituting a download timestamp would not resolve
the provenance gap. Even using `:Created:` as an eligibility boundary needs evidence
that the exact content and region association were then available. All seven audit
rows retain `availability_verified=false`; `training_ready=false` remains explicit.
The next source requirement is versioned issue-time evidence and contemporaneous
region associations, followed by coverage over every train/calibration/evaluation
period. The existing causal-history hypothesis remains conditional, not validated.

`scripts/audit_history_publication.py` checks downloaded source hashes and parses
UTC report headers. Missing/unsupported headers and creation dates before the report
day are rejected. Three tests cover later creation without a publication claim,
missing timestamps and inconsistent dates. `scripts/fetch_history_probe.py` fixes the
same seven dates, preserves existing output directories and restricts retrieval to HTTPS.

## File recovery status

The authorized iCloud session now opens Drive. Son Silinenler (Recently Deleted)
remained on its loading indicator during inspection. The separate Veri Kurtarma
(Data Recovery) route again returned “Bu içerik yüklenirken bir sorun oluştu.”
The historical `calibration_windows_20261030_r1/2019/predictions.parquet` remains
absent locally. No remote file list was obtained and no restore action completed;
this does not establish that the remote copy is gone. We did not recover unrelated
files or use Restore All. The completed annual evaluation remains usable without
this historical control file. The local verified backup remains separate from iCloud.

## Reproduction

The inspected source snapshot is `data/history_source_probe_20261107_r1`; its manifest
records original URLs and SHA256 values. Results are preserved in
`artifacts/history_publication_audit_20261107_r1/report.json`. Generated source files
and results remain outside Git. For a fresh retrieval and audit use new directories:

```sh
export PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261107
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/fetch_history_probe.py --output data/history_source_probe_20261107_r2
"$PY" scripts/audit_history_publication.py --source data/history_source_probe_20261107_r2 --output artifacts/history_publication_audit_20261107_r2
"$PY" -m pytest tests/test_history_publication.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261107_r1
```

Later retrieval may yield different archived bytes. Compare manifests before attributing
changes to code; retain the original snapshot and do not silently replace evidence.
