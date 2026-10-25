# SWAN-SF-V2 development layout audit

Audit date: 2026-10-25. Status: **identifier layout verified; measurement and
outcome coverage still pending**. This audit produced no model performance
result and did not open the reserved 2024–2025 final-test columns.

## Question and boundary

The audit asks whether the verified V2 archives can supply chronologically
separated HARP windows for the frozen training, calibration and validation
roles. The Parquet reader projected only `harp_number` and `obs_start`, with
`obs_start < 2024-01-01T00:00:37 TAI` applied at the storage scan boundary.
The cutoff is the TAI representation of `2024-01-01T00:00:00 UTC` under the
frozen 37-second offset. Outcome, measurement, quality and model columns were
not read.

Every candidate uses 60 observations at a 12-minute cadence, giving a
12-hour interval from its first observation to forecast time. Candidate starts
advance by five rows. A window is retained only when its observation and
24-hour target intervals fit one frozen UTC role. When a HARP appears in more
than one role, the earliest role owns it and later-role windows are excluded.

## Verified archive scan

All four HTTPS responses matched the pinned `Content-Length`, ETag and complete
compressed-file SHA-256 before their results were accepted. Twenty Parquet
members were inspected. Spark `_SUCCESS` markers were allowed only as zero-byte
regular files. No archive body or extracted Parquet member was retained.

| Partition | Members | Compressed bytes | SHA-256 |
| ---: | ---: | ---: | --- |
| 1 | 5 | 1,177,434,736 | `26fbe84600dcbd2600bced76eeff9df097b5de2bc78328160342869827b1dd3b` |
| 2 | 5 | 1,284,717,836 | `1fc49bff4e61ea2ac608d1c08dd45f335463f8b31e828afc60eaa283e8d50692` |
| 3 | 5 | 1,246,106,315 | `c829699b0afecb88b5cc1743e620096a21565a5127ea76be9fb9cfa6be69783f` |
| 4 | 5 | 1,302,570,086 | `35e86b7e27b52bfba83f6bdf3d39b1b15bc03fa0b52552a590472a4ceed0bf72` |
| **Total** | **20** | **5,010,828,973** | — |

## Findings

| Check | Result |
| --- | ---: |
| Joined rows before within-member key deduplication | 4,183,021 |
| Distinct `harp_number` / `obs_start` rows within members | 4,182,825 |
| Difference removed by within-member key deduplication | 196 |
| HARP identifiers | 5,983 |
| HARPs spanning multiple archive members | 0 |
| 12-minute cadence breaks inside each deduplicated HARP series | 0 |
| Windows removed at role boundaries or outside roles | 1,085 |
| Windows removed because their 12-hour interval crosses a leap-second offset | 215 |
| Calibration windows removed by earlier-role HARP ownership | 183 |
| Validation windows removed by earlier-role HARP ownership | 1,174 |

The identifier layout passed the prerequisite for a measurement scan: no HARP
was split across archive members, every deduplicated series had an uninterrupted
12-minute cadence, and all three development roles contained candidate windows.

| Role after boundaries and HARP ownership | Candidate windows |
| --- | ---: |
| train | 573,509 |
| calibration | 80,187 |
| validation | 114,190 |
| **Total** | **767,886** |

## Interpretation and decision

The audit verifies that the frozen chronological rules can be applied to the
identifier and time layout. It does **not** mark `development_coverage_audit`
as verified yet. The reported windows are candidates before measurement
quality checks, missing-value policy, label construction and class-count
checks. They are not training examples, and their counts must not be compared
with V1 sample counts as evidence of improved coverage or performance.

The next controlled step is a pre-2024 measurement-and-outcome scan using the
same storage predicate. It must report retained rows, missingness, finite-value
quality exclusions, label ambiguity, positive/negative class counts and date
coverage for each role. Only then may the development coverage gate be reviewed.
The separate `measurement_semantics` and `training_runner_review` gates also
remain pending, so model fitting is still blocked.

## Limitations and uncertainty

- The scan checked identifier and timestamp columns only; it says nothing about
  feature units, formulas, EPS interpretation, label correctness or class balance.
- Distinct-row counting occurred within each Parquet member. The absence of a
  HARP in multiple members means cross-member HARP/time duplication was not
  possible under the observed layout.
- Cadence continuity does not establish measurement validity. NaN, infinity,
  sentinel and quality-field exclusions can reduce the final population.
- The complete compressed archives necessarily passed through the streaming
  reader, but the Parquet logical scan did not project reserved-period outcomes,
  measurements or model columns. This is a workflow control, not a security
  boundary against arbitrary direct access.
- The result is tied to the manifest and code hashes below. A changed archive,
  protocol, time conversion or scanner requires a new audit output.

## Reproduction

Run from the repository root with network access:

```sh
.venv/bin/python scripts/audit_v2_layout.py \
  --output artifacts/v2_layout_audit_20261025_r4 --workers 4
```

The command refuses to overwrite an existing output. The accepted machine
report is `artifacts/v2_layout_audit_20261025_r4/report.json` and records:

| Input or code | SHA-256 |
| --- | --- |
| `config/swan_sf_v2_sources.verified.json` | `4da23877d22c2676ab76950c69c016bbe8eaacd8049fc806dad078752feafa3d` |
| `config/experiment5-v3.json` | `e447ec51797cd14b0e44b85f0fae4e46ef2c67f3f981c23b2bd7b47f41c09ae4` |
| `helio24/v2_archive.py` | `c43557b531e826e5ec265acec82fee0ad694fd1b0748622b5dd571be0aff36c1` |
| `helio24/v2_contract.py` | `e195bbc33d1afc2aed417229369723194413eca5c5ac461c38bb22916a9ad9cd` |
| `scripts/audit_v2_layout.py` | `84981b6b3225b4b758779640e673f31db3f89f69903ddc280598a4020698dd8d` |

Publish the reviewed language pair into a new directory:

```sh
.venv/bin/python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_layout_20261025
```
