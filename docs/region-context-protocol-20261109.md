# Regional context protocol: issued SRS features with annual refits, frozen before any result

## Decision and scope

The [source audit](region-context-sources-20261109.md) showed that the NOAA Solar Region Summary (SRS) carries
its own issue time and covers 90.8% of positive development windows at issue time. This protocol freezes one
bounded experiment: the fixed 96 magnetic summaries plus causal SRS context, refitted with the unchanged
walk-forward recipes in the same annual folds as the frozen baseline. It was written before any candidate result
was computed. Nothing has been run. No label changes and the reserved 2024–2025 test stays closed. One step
is not expected to reach the project target of precision 0.30 at recall 0.95; the distance is reported.

Evidence: the frozen annual predictions (source report SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`), the baseline walk-forward report (SHA256
`6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c`), the frozen shard report (SHA256
`62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82`) and the acquired SRS and HARP–NOAA
sources with their manifests.

## Why this experiment

In the frozen baseline, 80% to 97% of false-alarm windows fall inside numbered regions that are present in the
issued SRS, so the region's existence does not separate them; its content might. Magnetic class (Beta-Gamma,
Beta-Delta, Beta-Gamma-Delta), McIntosh class, area, spot count and region age are established flare indicators
in the literature and are not carried by the 96 SHARP summaries. Whether they add information on top of those
summaries in this record is the question.

## Availability rule

A window at forecast time t uses the latest SRS whose issue time is at or before t minus 30 minutes, and only
the SRS rows whose NOAA number is in the HARP's `NOAA_ARS` on the forecast date. A HARP with no such row has
`srs_available` 0 and every other context value missing. Missing values pass through the existing median imputer
with a missing indicator, so the model sees that context is absent. Absence is never encoded as quiet.

## Context features

| feature | definition |
| --- | --- |
| srs_available | 1 if at least one SRS row matched, else 0 |
| hours_since_issue | t minus the issue time of the SRS used, in hours |
| n_regions | number of matched SRS rows |
| mag_rank | max over rows of Alpha 0, Beta 1, Gamma 2, Beta-Gamma 2, Beta-Delta 3, Beta-Gamma-Delta 4 |
| has_delta | 1 if any matched magnetic class contains Delta |
| has_gamma | 1 if any matched magnetic class contains Gamma |
| zurich_rank | max over rows of the modified Zurich letter A 0, B 1, H 1, C 2, D 3, E 4, F 5 |
| penumbra_rank | max over rows of the second McIntosh letter x 0, r 1, s 2, a 3, h 4, k 5 |
| compact_rank | max over rows of the third McIntosh letter x 0, o 1, i 2, c 3 |
| area_log | log(1 + sum of matched areas) |
| spots_log | log(1 + sum of matched spot counts) |
| extent_max | max matched longitudinal extent in degrees |
| srs_history_days | max over rows of the number of earlier issued SRS products, strictly before the one used, listing the same NOAA number |

## Candidates and budget

| candidate | definition | fits |
| --- | --- | --- |
| control | frozen baseline ensemble predictions and prior-year thresholds, identical evaluation keys | 0 |
| flag | refit on the 96 summaries plus srs_available and hours_since_issue only | 2 per year |
| context | refit on the 96 summaries plus all 13 context features | 2 per year |

Training uses the annual folds of the frozen development shards; the audit of every fold must equal the frozen
baseline fold audit. Models, hyperparameters, imputer, scaler, sigmoid calibration on the calibration year and the
0.45/0.55 ensemble weight are those of `config/walk-forward-v1.json`, unchanged. Thresholds are selected on
calibration-year probabilities at window recall 0.95 and written to disk and hashed before any evaluation label
is read. Budget: 2 candidate recipes, 7 years, 28 constituent fits, no hyperparameter search, no feature set
added after results. The `flag` candidate exists so that a gain cannot be attributed to content when refitting or
availability alone produces it.

## Acceptance rules

A candidate counts in a year if it satisfies all four conditions against the control, with the same definitions
as the persistence protocol: higher episode precision, fewer false-alarm windows, no fewer alarmed positive
runs, and a window recall drop of at most 0.02. An all-year pass needs all six positive years for the same
candidate. A pass of `context` that `flag` does not share is attributed to SRS content. 2018 has no positive
windows and reports thresholds, false-alarm windows and episodes only. The report also gives, per year and
candidate, whether recall 0.95 is reached, AP, Brier, log loss and the number of false-alarm windows above the
largest count that would give precision 0.30 at the achieved true positives. A pass justifies only a separate
prospective protocol and never changes alerts, thresholds or models.

## Uncertainty

Paired full-HARP bootstrap intervals (1000 draws, seed 24) for episode precision and false-alarm window
differences against the control are conditional on the frozen thresholds. They exclude refitting and
threshold-selection uncertainty and are not corrected for multiple comparisons.

## Disclosure and limits

The feature list and the ordinal encodings were fixed from the SRS vocabulary and from where false alarms
concentrate in the frozen baseline of the same years, which is adaptive. No candidate result had been computed
when the configuration was frozen. The result is adaptive development evidence on already inspected years, not
an independent test. Counts are overlapping forecast windows and groupings of them, not physical flares. The SRS
issue time proves issuance, not reception; the 30 minute margin is a project convention.

## Next step and reproduction

After review, add `scripts/audit_region_context_features.py` with tests, run it once into a new output
directory and report the result in both languages. The frozen configuration is not edited afterwards; a revision
needs a new version. The frozen file can be inspected with:

```sh
cat config/region-context-v1.json
```
