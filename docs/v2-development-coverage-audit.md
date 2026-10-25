# SWAN-SF-V2 development coverage audit

Audit date: 2026-10-25. Decision: **pre-2024 measurement coverage is
quantified, but label completeness and the development coverage gate remain
pending**. This audit fitted no model, computed no prediction metric and did
not read reserved 2024–2025 rows.

## Scope and controls

The four pinned V2 archives were downloaded one at a time into temporary local
files. Each complete compressed file matched its frozen `Content-Length`, ETag
and SHA-256 before any Parquet member was inspected. Temporary archive and
member files were deleted after processing. The logical Parquet scan applied
`obs_start < 2024-01-01T00:00:37 TAI`, the frozen TAI equivalent of the test
boundary, and projected the 24 unweighted magnetic measurements plus fields
needed for attached-event auditing.

The scan used the frozen 12-hour observation, 24-hour prediction, five-row
stride, UTC role-boundary, HARP ownership and finite-value quality rules. A
window fails quality when any one measurement has more than 12 missing or
non-finite positions among its 60 observations. Outcome fields were used only
for label coverage checks and never as model inputs.

All four archives, 20 Parquet members and 5,010,828,973 compressed bytes passed
their pinned hashes. The scan found 4,183,021 joined rows, 4,182,825 distinct
HARP/time observations and 5,983 HARPs. No cadence window was removed. Role
boundaries removed 1,085 windows and leap-second crossings removed 215.

## Measurement coverage

Counts below follow role boundaries and earliest-role HARP ownership. The
retained missing fraction uses all `retained windows × 60 rows × 24 fields`
measurement positions as its denominator.

| Role | Candidate windows | Quality retained | Quality rejected | Retained rate | Missing fraction in retained positions |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 573,509 | 506,493 | 67,016 | 88.31% | 1.4940% |
| calibration | 80,187 | 69,933 | 10,254 | 87.21% | 1.6681% |
| validation | 114,190 | 100,882 | 13,308 | 88.35% | 1.5805% |
| **Total** | **767,886** | **677,308** | **90,578** | **88.20%** | **1.5249%** |

The aggregate missing-position count in retained windows is 14,872,489 out of
975,323,520. HARP ownership additionally removed 183 calibration candidates
(174 would pass quality) and 1,174 validation candidates (946 would pass
quality). These later-role windows cannot re-enter the data even when an
earlier-role HARP has no retained later window.

| Role | First retained forecast (UTC) | Last retained forecast (UTC) |
| --- | --- | --- |
| train | 2010-05-01 12:59:26 | 2021-12-30 23:35:23 |
| calibration | 2022-01-01 12:23:23 | 2022-12-30 23:59:23 |
| validation | 2023-01-01 12:35:23 | 2023-12-30 23:59:23 |

The final forecast in each role precedes its boundary because the complete
24-hour half-open target interval must fit inside the same role.

## Attached-event audit and provisional labels

The scan retained 24,132 valid attached event associations. Twenty-three other
deduplicated attached-event rows had `start_time > peak_time` or
`peak_time > end_time`; the fail-closed validator excluded all 23 with the
reason `Flare start/peak/end order is invalid`. They were not repaired or used
for labels.

There are 723 attached GOES M/X associations: 678 M and 45 X. Of these, 722
use an accepted HARP confidence and one M event is `very_low`, which is
ambiguous under the frozen contract.

| GOES class | very_high | high | moderate | low | very_low | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M | 380 | 231 | 30 | 36 | 1 | 678 |
| X | 18 | 20 | 4 | 3 | 0 | 45 |
| **Total** | **398** | **251** | **34** | **39** | **1** | **723** |

Known positives below mean that at least one accepted, attached GOES M/X peak
falls in the quality-retained window's half-open 24-hour target interval.
“Unresolved nonpositive” deliberately does not mean negative: an independent
inventory is still needed to identify M/X events with no trusted HARP.

| Role | Quality retained | Known positive | Ambiguous HARP | Unresolved nonpositive |
| --- | ---: | ---: | ---: | ---: |
| train | 506,493 | 8,698 | 0 | 497,795 |
| calibration | 69,933 | 421 | 0 | 69,512 |
| validation | 100,882 | 781 | 24 | 100,077 |
| **Total** | **677,308** | **9,900** | **24** | **667,384** |

## Gate decision

The full pre-2024 measurement scan succeeds and shows non-empty, quality-retained
coverage in every development role. It does not yet establish negative labels.
The `development_coverage_audit` gate remains
`pending_unassigned_major_event_inventory` until a complete, immutable and
independently checked GOES M/X inventory is frozen for the full development
period. That inventory must distinguish attached accepted events, ambiguous
HARP assignments and events with no trusted HARP before class counts are final.

`measurement_semantics` and `training_runner_review` also remain pending.
Therefore the result does not authorize Experiment 5 fitting. The 9,900 known
positive windows are overlapping forecast windows, not 9,900 independent solar
flares. No accuracy, recall, precision, false-alarm or calibration result is
reported here.

## Limitations and uncertainty

- The audit evaluates the versioned V2 finite-value policy. It does not prove
  equivalence to the V1 `QUALITY`/`IS_TMFI` mask or resolve measurement formulas
  and EPS semantics.
- Missing fractions count repeated measurement positions across overlapping
  windows. They are not the fraction of unique raw rows with missing values.
- Attached event rows establish known positives but cannot establish complete
  negatives. The unresolved group mixes true negatives with any major events
  missing a trusted HARP association.
- Invalid event intervals are reported and excluded. Their correct repaired
  values are unknown, and the audit makes no assumption about them.
- Counts are deterministic for the recorded source and code hashes. Any source,
  contract, boundary or scanner change requires a new output directory and
  review.

## Reproduction

Run from the repository root with enough temporary disk space and network access:

```sh
.venv/bin/python scripts/audit_v2_development_coverage.py \
  --output artifacts/v2_development_coverage_20261025_r3 --workers 1
```

The accepted machine report is
`artifacts/v2_development_coverage_20261025_r3/report.json`. It records these
code hashes:

| Code | SHA-256 |
| --- | --- |
| `helio24/v2_archive.py` | `bde85ba5b4659995941cc4ace06c0088a21a67a1048b0c9c623d4f37dd1ce5e0` |
| `helio24/v2_contract.py` | `e195bbc33d1afc2aed417229369723194413eca5c5ac461c38bb22916a9ad9cd` |
| `helio24/v2_coverage.py` | `7ff70591ccf621cc6a8f12403b3f81c08adf5bb88753240a943bd699f4dd733e` |
| `scripts/audit_v2_development_coverage.py` | `cedd5bf40b08dc85431d688c506aa9bec43ea5db2d65fc9f396f24af19aaac25` |

Publish the reviewed language pair into a new directory:

```sh
.venv/bin/python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_coverage_20261025
```
