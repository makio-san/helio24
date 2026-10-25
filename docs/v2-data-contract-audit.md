# SWAN-SF-V2 data contract audit

Date: 2026-10-25. Decision: **the UTC conversion, V2 quality policy and
GOES label policy are frozen; training remains blocked by three other gates.**
This is a development-data audit, not a model experiment. It contains no new
prediction scores and does not inspect 2024-2025 rows or outcomes.

## Scope and source identity

The bounded local source is the previously frozen first Parquet member from raw
archive partition 1. Only rows with `obs_start < 2019-01-01` were projected.
The scan contains 131,290 joined rows, 131,284 distinct observation rows and
186 HARPs. Event columns were read for this development-only contract audit;
they remain forbidden as model inputs.

The four raw archive identities were checked over verified HTTPS on 2026-10-25:

| Partition | Content length (bytes) | ETag | Last modified (UTC) | SHA-256 |
| ---: | ---: | --- | --- | --- |
| 1 | 1,177,434,736 | 462e3a70-65ccb14823788 | 2026-10-01 17:52:32 | 26fbe84600dcbd2600bced76eeff9df097b5de2bc78328160342869827b1dd3b |
| 2 | 1,284,717,836 | 4c933d0c-65ccb20b27a70 | 2026-10-01 17:55:56 | 1fc49bff4e61ea2ac608d1c08dd45f335463f8b31e828afc60eaa283e8d50692 |
| 3 | 1,246,106,315 | 4a4612cb-65ccb20d79562 | 2026-10-01 17:55:59 | c829699b0afecb88b5cc1743e620096a21565a5127ea76be9fb9cfa6be69783f |
| 4 | 1,302,570,086 | 4da3a466-65ccb2236ed31 | 2026-10-01 17:56:22 | 35e86b7e27b52bfba83f6bdf3d39b1b15bc03fa0b52552a590472a4ceed0bf72 |
| Total | 5,010,828,973 | — | — | verified |

The ETags, lengths and dates were checked before streaming all 5,010,828,973
bytes through SHA-256. Archive bodies were not saved. The four complete hashes
now freeze byte identity, so `versioned_dataset_manifest` is verified. The V2
paper is still preprint v1 and says the final Dataverse DOI will follow peer
review. The exact toolkit commit used to produce the archives is also
unidentified, so `measurement_semantics` remains pending. The verified source
inventory is `config/swan_sf_v2_sources.verified.json`; the earlier pending
inventory remains preserved.

## Observation clock conversion

The pinned toolkit documentation says HARP clocks parsed from JSOC `*_TAI`
strings are returned as timezone-naive values and must be converted when UTC is
needed. Helio24 now interprets `obs_start` as TAI, applies the historical
TAI-UTC offset and emits timezone-aware UTC. The IERS/USNO record supports
34 seconds before 2012-07-01, 35 before 2015-07-01, 36 before 2017-01-01 and
37 seconds thereafter in this dataset period.

| TAI-UTC offset (seconds) | Distinct observation rows |
| ---: | ---: |
| 34 | 35,342 |
| 35 | 68,223 |
| 36 | 17,558 |
| 37 | 10,161 |
| Total | 131,284 |

The contract rejects timezone-aware input in the TAI field, times outside
2010-2025 and the unrepresentable leap-second instant. It also excludes a
12-hour observation window that crosses a leap-second transition instead of
silently changing its duration. This gives a deterministic UTC issue time.

V2 flare clocks are treated as timezone-naive source-catalog UTC. Among 501
attached GOES event rows, 496 have an exact peak-time and class match in the
frozen V1 integrated catalog. All 49 M/X GOES rows match exactly; the five
unmatched rows are B-class. This is strong old-period evidence for the event
clock interpretation, but not a completeness claim for the full V2 release.

## Versioned V2 quality policy

V2 has no record-level `QUALITY` or `IS_TMFI` fields. Helio24 therefore freezes
a separate policy rather than claiming to reproduce the historical mask:

1. Require exactly 60 rows from one HARP at a unique 12-minute TAI cadence.
2. Convert non-numeric and infinite values to missing.
3. Reject a window if any of the 24 unweighted magnetic parameters is more
   than 20% missing.
4. Compute mean, population standard deviation, last value and delta from
   finite values only. Later model imputation and missing indicators fit on
   training only.
5. Exclude observation windows crossing a leap-second transition.

The same five frozen 2011 overlap windows were evaluated under native V2
finiteness and under the old `QUALITY=0` plus `IS_TMFI` mask applied to V2
values:

| Quantity | Native V2 policy | Historical mask on V2 |
| --- | ---: | ---: |
| Windows retained | 5 | 5 |
| Missing measurement positions | 96 | 432 |
| Summary values compared | 480 | 480 |
| Summary values changed between policies | 280 | 280 |

Both policies retain these five windows, but 280 of 480 summaries change.
The result proves that retention agreement on this sample is not feature
equivalence. The new policy is versioned as V2-specific and must be reported
as such. Full-period missingness and retention remain part of the pending
development coverage audit.

## GOES label inclusion policy

The primary target is at least one GOES M/X flare peak for the same HARP in
the half-open UTC interval `[forecast_time, prediction_end)`. The V2 paper
defines this half-open interval, while the pinned slicer implementation uses
an inclusive last sampled timestamp. Helio24 regenerates labels from event
rows and follows the paper definition; it does not trust `peak_class` at the
right boundary.

Only rows with `has_goes=True` contribute primary events. SSW/XRT-only rows
remain available for separate sensitivity work. `very_high`, `high`,
`moderate` and `low` HARP assignments are accepted because the paper calls
all non-`very_low`, non-`unverified` assignments verified. A `very_low` M/X
row blocks a negative label for its candidate HARP. A complete external GOES
M/X inventory is mandatory; every strong event without a trusted HARP blocks
negative labels for all concurrent HARP windows. Label construction refuses
to run when that inventory has not been certified complete.

| GOES class | very_high | high | moderate | low | very_low | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M | 29 | 14 | 1 | 1 | 0 | 45 |
| X | 1 | 2 | 0 | 1 | 0 | 4 |
| Total | 30 | 16 | 1 | 2 | 0 | 49 |

All 49 bounded-overlap M/X GOES rows satisfy the accepted confidence policy.
This does not show that the full development period has no ambiguous or
unassigned major events. That completeness check is required before labels
are materialized.

## Gate state after this revision

| Gate | Status | Reason |
| --- | --- | --- |
| measurement_semantics | pending | Production calculation revision and exact EPS semantics are unresolved |
| quality_policy | verified | A distinct V2 policy is implemented, tested and bounded-audited |
| utc_conversion | verified | Explicit TAI-to-UTC conversion is implemented and tested |
| label_inclusion_policy | verified | GOES source, confidence, ambiguity and half-open boundary rules are frozen |
| versioned_dataset_manifest | verified | All four compressed archives have full SHA-256 identities |
| development_coverage_audit | pending | All rows before 2024 have not been scanned |
| training_runner_review | pending | No Experiment 5 V2 training runner exists |

Verified here means the rule and evidence are frozen for this project. It does
not mean V2 reproduces V1, that upstream production is fully reproducible, or
that model performance is known. `config/experiment5-v3.json` supersedes the
previous designs only for future execution and still has status
`design_frozen_data_contract_pending`.

## Reproduction

```sh
python scripts/audit_v2_contract.py --output artifacts/v2_contract_audit_20261025_r2
python scripts/check_evaluation_protocol.py \
  --config config/experiment5-v3.json \
  --output artifacts/experiment5_v3_preflight_20261025
python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_contract_20261025
```

The audit refuses to overwrite an existing directory. The preflight must exit
with code 2 and list three pending gates. Raw data and generated artifacts stay
outside Git. Next, build a projection/filtering reader that scans only rows
before 2024, then audit development coverage before any model fitting.

Sources: [SWAN-SF-V2 preprint v1](https://arxiv.org/html/2610.04591v1),
[Space Weather Toolkit slicer documentation](https://dmlab.cs.gsu.edu/docs/spaceweather_toolkit/slicer.html),
[USNO leap-second information](https://maia.usno.navy.mil/products/leap-second),
[IERS Bulletin C](https://datacenter.iers.org/data/html/bulletinc-058.html).
