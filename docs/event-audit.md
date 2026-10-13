# Alarm episodes and covered catalog events

The event audit is complete. Long alarm periods explain why a high event hit rate
can coexist with many false-alarm windows. The audit also found a disagreement
between one recovered catalog event and ten negative benchmark windows.

The [protocol](event-audit-protocol.md) was committed before aggregate results.
This analysis uses experiment 2's 50,631 partition-4 validation records, 470 HARPs,
full calibrated model and frozen 4.7999% threshold. It does not train or promote a
model. Partition 5 is not used.

## Alarm burden

| Measure | Result |
| --- | ---: |
| Monitored region-hours | 50,631 |
| Alarm region-hours | 5,233 |
| Benchmark false-alarm region-hours | 4,264 |
| False-alarm share of monitored region-hours | 8.42% |
| Alarm episodes | 333 |
| Entirely negative-label episodes | 280 |
| Episodes touching a data boundary or gap | 130 |
| Longest entirely negative-label episode | 127 hours |
| Top ten regions' share of false-alarm hours | 36.59% |

Each available forecast contributes at most one hour of alarm state, including
the final forecast. Consecutive alarm issues are merged only at exactly one-hour
spacing. Quiet issues and gaps split episodes. This hourly-state convention is
not a measured continuous user alert, and a 24-hour prediction horizon is not
counted as 24 hours of alarm exposure. Region-hours sum across regions; they are
not one observer's wall-clock time. Censored episodes may continue into gaps.

An entirely negative episode contains only benchmark target-zero windows.
Mixed episodes can contain both true and false hours. A count of 280 negative
episodes therefore does not replace the burden of 4,264 false hours, and event
mapping incompleteness prevents interpreting all-negative as proven physical
absence of a flare.

| HARP | False hours / monitored hours | Longest negative episode |
| --- | ---: | ---: |
| 4851 | 181 / 208 | 113 hours |
| 4321 | 169 / 203 | 87 hours |
| 4315 | 167 / 190 | 116 hours |
| 4225 | 153 / 214 | 127 hours |

HARP 4225's 127-hour negative episode starts about 23.58 hours after its preceding
mapped M1.0 peak. That timing is descriptive: the earlier flare is not in those
future forecast windows. The timeline shows persistent probabilities above the
low operating threshold during this interval.

## Event identity, timing and coverage

HARP identifiers were not equated with NOAA region identifiers. The verified
partition-4 archive supplied 105 unique HARP/flare-ID associations: 44 supported
by both filenames and location-history annotations, 42 by filenames only, and
19 by history only. No accepted event had multiple HARP mappings in this archive.
The latter 19 associations expose information omitted by strongest-window labels.

All 51,261 archive windows were scanned for association evidence, including those
excluded from model features. The model and its inputs were not changed. A
catalog-ID or magnitude discrepancy would reject the evidence; history peak
timestamps must also lie within six minutes of the annotation timestamp.

There were 45 rejected time associations and one unverified association. Their
annotation timestamps preceded catalog peaks by 7–11 minutes. The paper describes
annotations at the closest 12-minute timestamp, but these records do not meet
that rule. The fixed conservative filter remains in place; the discrepancies
are exported for investigation, not rounded away. Accepted filename evidence can
still support an event whose history evidence was rejected.

Within the overall forecast date span, the whole-Sun M/X catalog contains:

| Status | Unique events |
| --- | ---: |
| Uniquely mapped with at least one eligible forecast | 87 |
| Mapped but without eligible forecast coverage | 1 |
| No accepted mapping in this archive | 62 |

The 62 unmapped entries are not automatically regional misses: some may lie in
other regions or outside usable observation coverage. Neither these archive
associations nor the covered subset establish complete solar or HARP-event coverage.

Of the 87 covered mapped events, 86 had at least one alarm in an eligible
24-hour forecast, giving **98.85% conditional event recall**. All 86 also had an
alarm strictly before catalog start. Fourteen evaluated events came only from
history associations. The subset with all preceding 24 hours covered by hourly
forecast-state slots contains 47 events; all 47 were detected.

The missed event is M2.2, catalog ID 9053, HARP 4678, peaking at 2014-10-14 21:21
UTC. Only 10.15 of the preceding 24 hours have forecast-state coverage. Missing
coverage is reported separately from model misses.

For detected events, median lead to peak is 23.35 hours; median lead to catalog
start is 22.99 hours. These are the earliest qualifying issues inside the 24-hour
forecast horizon, not necessarily new episode onsets. Persistent alarms can
generate leads near 24 hours without precisely anticipating individual events.
High conditional event recall is therefore not evidence of low alarm burden.

## Label disagreement

Catalog event 8864 is an M2.5 flare peaking at 2014-09-03 13:54 UTC. Its verified
location-history annotation associates it with HARP 4502. Ten target-zero
forecasts issued from 2014-09-02 21:24 through 2014-09-03 06:24 UTC contain that
peak in their future intervals.

The audit preserves both sources: episode false hours use original benchmark
labels; event matching uses the accepted catalog associations. These are not
fully consistent reference definitions. No label repair or retraining occurred.
The ten conflicts are exported and displayed as a dashboard warning. Resolving
this provenance disagreement should precede claiming a complete event-level
benchmark or using the recovered events for model selection.

## Measurement patterns

| Window outcome | Median last USFLUX | Median last R_VALUE | Median last TOTUSJH |
| --- | ---: | ---: | ---: |
| Correct quiet | 1.530 × 10²¹ | 0.000 | 97.86 |
| False alarm | 2.920 × 10²² | 4.524 | 1,929.42 |
| Hit | 4.813 × 10²² | 4.836 | 3,647.69 |
| Miss | 2.728 × 10²² | 4.359 | 1,585.13 |

False-alarm windows tend to have larger magnetic summaries than correctly quiet
windows. All four groups have median masked-measurement fraction 3.33%, so this
summary does not identify missingness alone as the explanation. These overlapping
window distributions are descriptive, confounded by region and time, and do not
establish physical causes or statistical significance.

## Reproduction and interface

```sh
python scripts/prepare_event_mapping.py
python scripts/run_event_audit.py
python scripts/report_event_audit.py
```

The runner requires the existing experiment-2 outputs. It checks frozen
decisions, source features, mapping evidence and catalog identity. Existing event
audit directories are never overwritten by the analysis runner. Mapping
preparation can reuse a checksum-verified cache.

The ignored `artifacts/event_audit/report.html` embeds representative timelines,
counts, mapping conflicts, evaluated events and the protocol. CSV/Parquet outputs
preserve all episodes, all regions, catalog coverage, event/episode links, and
source and artifact hashes. Raw data, models and generated reports stay out of Git.

The dashboard's **Alarm & event audit** tab shows this development analysis
separately from experiment 1. Users can rank regions by false hours or longest
negative episode, select a magnetic variable, reveal mapped peaks, and download
tables. Curves break at unavailable forecasts; magnetic missing values remain
gaps. Changing region hides outcomes again.

Source: [SWAN-SF original paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7351763/),
flare-integration and slicing sections. The paper motivates separate HARP/NOAA
identities and maximum-flare window labels; the actual archive and catalog
provide the evidence and measured results in this audit.
