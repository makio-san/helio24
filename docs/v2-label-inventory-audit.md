# SWAN-SF-V2 major-flare label inventory audit

Audit date: 2026-10-25. Decision: **the frozen HEK/SWPC inventory is complete
for fail-closed pre-2024 V2 label construction**. All 723 distinct attached
GOES M/X peak/class events in V2 have an exact inventory match; there are no
V2-only events and no peak-time class conflicts. This audit fitted no model,
changed no prediction threshold and read no reserved 2024–2025 rows.

## Scope and method

The external inventory covers GOES flares with class `>= M1` and peak time in
`[2010-05-01, 2024-01-01)`. It was fetched from the official HEK endpoint in
164 non-overlapping monthly queries with `event_type=FL`,
`OBS_Observatory=GOES` and `FL_GOESCls>=M1`. Every response reported
`overmax=false`. Raw responses and normalized events were written to a new,
ignored artifact directory and hashed before reconciliation.

The V2 side scanned the four pinned archives with
`obs_start < 2024-01-01T00:00:37 TAI`. Every complete archive matched its
frozen `Content-Length`, ETag and SHA-256 before its five Parquet members were
read. Attached event rows were validated independently. Valid GOES M/X events
were compared with the external inventory by exact normalized
`(peak_time, goes_class)` identity. Source event IDs were preserved; repeated
HEK records were not silently discarded.

## Frozen HEK inventory

| Quantity | Result |
| --- | ---: |
| Monthly responses | 164 |
| Source event rows | 1,356 |
| Distinct peak/class events | 1,345 |
| M rows | 1,285 |
| X rows | 71 |
| Duplicate peak/class keys | 11 |
| Rows in duplicate keys | 22 |

The 1,356 source rows comprise 1,352 `SWPC`, two `SEC standard`, one
`SWPC standard` and one `SEC nonstandard` provider records. The 11 repeated
peak/class keys represent multiple source identities or revisions. Label
matching uses their 1,345 distinct peak/class identities while the frozen
inventory retains every source row.

## Reconciliation results

| Quantity | Result |
| --- | ---: |
| V2 attached associations | 723 |
| V2 distinct peak/class events | 723 |
| Exact peak/class matches | 723 |
| V2-only peak/class events | 0 |
| HEK events unassigned to V2 | 622 |
| Peak-time class conflicts | 0 |
| Invalid attached event rows excluded | 23 |

All V2 attached GOES M/X events are represented by the external inventory.
The 622 distinct HEK events absent from V2's attached-event set are the events
needed to keep unassigned major flares from being treated as ordinary
negatives. A downstream label builder must apply the frozen HARP association
policy: accepted attached events can create positives, `very_low` or otherwise
ambiguous assignments must be excluded, and unassigned events must exclude
affected forecast windows rather than assign them to a region.

The 23 invalid attached rows have `start_time > peak_time` or
`peak_time > end_time`. They remain quarantined and were neither repaired nor
used in reconciliation. Their exclusion does not create a V2-only major event:
the valid attached set still has zero events absent from HEK.

## Gate and precision implications

The `development_coverage_audit` gate can advance from
`pending_unassigned_major_event_inventory` to verified label-inventory
coverage. This does not authorize Experiment 5 fitting: `measurement_semantics`
and `training_runner_review` remain pending.

The audit does not report a new precision value. It removes a known source of
false-negative labels: 622 external major events were unavailable from V2's
trusted attached-event set. Treating all previously unresolved windows as
negative could count real events as false alarms and understate precision.
After the remaining gates close, candidate models will be selected by maximum
precision, then minimum false positives, among thresholds satisfying the
frozen `recall >= 0.95` constraint.

## Limitations and uncertainty

- HEK is a mutable service. Reproduction uses the frozen raw response hashes;
  a later live query may return revised records.
- Exact peak/class matching establishes inventory coverage for V2 attached
  major events. It does not prove that each HEK spatial association or each V2
  HARP association is physically correct.
- The 622 unassigned events cannot be assigned to a HARP by this audit. They
  support fail-closed exclusion, not positive regional labels.
- The test interval was excluded. This decision gives no evidence about
  2024–2025 performance, precision or calibration.
- No model was trained. Existing development metrics remain unchanged until a
  preregistered, reviewed training run produces new predictions.

## Reproduction and hashes

Run from the repository root with network access and enough temporary disk
space. Use new output directories; the scripts refuse to overwrite evidence.

```sh
.venv/bin/python scripts/fetch_hek_major_inventory.py \
  --output artifacts/hek_major_inventory_20261025_r2
.venv/bin/python scripts/audit_v2_label_inventory.py \
  --inventory artifacts/hek_major_inventory_20261025_r2 \
  --output artifacts/v2_label_inventory_20261025_r1 --workers 1
```

| Evidence | SHA-256 |
| --- | --- |
| HEK raw response set | `37969ae4da798f10e313790b35db9421f657eab18557bdfab8a1904ba0be1d11` |
| HEK normalized events | `f0431c27d11abf7b2908f588634eccd61d960d5c1e67b1b4ffcfd2a5416afb0f` |
| Unassigned major events | `e584b58fbea9f1e03f025df75edae9312303f0dafd82db04347a5ba7fc71be8f` |
| V2-only peak/class events | `804883bb801a590a5ccb80debb2ff274f9bb0dd674cdef33346a1a5505293d6d` |
| Peak/class conflicts | `da7b8c17324642cc2be91a47c800d88d087d705742a9048680e69d6fe515e683` |

The accepted machine reports are
`artifacts/hek_major_inventory_20261025_r2/report.json` and
`artifacts/v2_label_inventory_20261025_r1/report.json`. Publish the reviewed
language pair into a new directory:

```sh
.venv/bin/python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_labels_20261025
```

References: [HEK API documentation](https://hekapidocs.readthedocs.io/en/latest/hek_api.html),
[HEK API endpoint documentation](https://www.lmsal.com/hek/api.html).
