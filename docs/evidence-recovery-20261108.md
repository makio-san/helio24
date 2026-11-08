# Evidence recovery after local file eviction: inventories and development shards verified

## Summary

On 2026-11-08 many project files were found evicted from the local disk by the cloud sync of the Desktop folder
(flagged `dataless`, with content only in the cloud). Reads of them stalled and timed out. The Git history was
safe because every commit up to `1ad1f24` was already on the remote repository. The Git-ignored evidence was
recovered by regenerating it from the official sources or by copying it back, and each item was checked against
a hash frozen before the loss. The development feature shards, which the baseline arm needs, were regenerated and
all 20 matched their frozen SHA256 values. Nothing in this recovery changes a model, a threshold, a label or a
result of any earlier report. The reserved 2024–2025 test was not accessed.

## What was recovered and how it was checked

| item | quantity | check | result |
| --- | --- | --- | --- |
| HEK major-event inventory | 164 monthly responses (116 surviving, 48 re-fetched) | events.csv SHA256 equals the frozen value | match |
| V2 label inventory files | 3 | SHA256, reconciliation counts and archive SHA256 equal the frozen values | 3 of 3 |
| Development feature shards | 20 | SHA256 equals the frozen shard report | 20 of 20 |
| temporal_years_20261101_r1 | 429 files | listed artifact hashes | 292 of 292 |
| sequences_20261101_r2 | 5494 files | no frozen hash source exists | not verified |

The HEK inventory has 1356 events and `events.csv` SHA256
`f0431c27d11abf7b2908f588634eccd61d960d5c1e67b1b4ffcfd2a5416afb0f`. The label reconciliation has 723
exact peak-class matches, 0 conflicts and 622 external unassigned peak classes, and the unassigned-event
inventory SHA256 is `e584b58fbea9f1e03f025df75edae9312303f0dafd82db04347a5ba7fc71be8f`. The files of
`sequences_20261101_r2` are present on disk, but no hash list for them was found, so they must not be treated as
verified.

## Regenerated development shards

| role | rows | positives |
| --- | --- | --- |
| train | 484549 | 8698 |
| calibration | 50756 | 421 |
| validation | 60366 | 781 |

The regenerated report has 5983 HARPs and 595671 retained rows, and these counts equal the frozen shard report.
Its completion time, input paths and the hash of `helio24/v2_archive.py` differ from the frozen report. The
per-shard hashes do not differ, so the code difference did not change the output. The frozen shard report SHA256
is `62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82` and the regenerated report SHA256 is
`36e8484a1496f6f1d7e117143766bfa9a15c306f4ac3984be4de321d2b5f7086`. The verified shards were then placed in the
frozen directory and re-checked there: 20 of 20 matched.

## Downloads

The official SWAN-SF archives were streamed and verified twice: once for the label inventory and once for the
shard regeneration.

| partition | compressed bytes per pass |
| --- | --- |
| 1 | 1177434736 |
| 2 | 1284717836 |
| 3 | 1246106315 |
| 4 | 1302570086 |
| total of one pass | 5010828973 |
| total of two passes | 10021657946 |

Two earlier shard attempts exited with code 0, wrote no output and no log, and their cause is unknown. How much
data they transferred cannot be established, so the true total may be higher than the table. The 48 HEK months
were re-fetched with small queries.

## Limits and uncertainty

- About 18400 files of the original Desktop folder were still evicted when the work stopped, mostly Git objects
  and regenerable report outputs. The working copy used for the recovery is a fresh clone of the remote
  repository, which is outside the synced folder.
- The cause of the silent exits is not established. The evicted files and failing cloud downloads are the most
  likely explanation but were not proven.
- Hashes prove that regenerated files equal the frozen ones. They do not show that the frozen files were
  themselves correct, which is outside the scope of this recovery.
- The `sequences_20261101_r2` shards are unverified.

## Reproduction

The commands below recreate the three regenerated artifacts. Replace the placeholder with the directory of
surviving raw HEK responses. The download steps fetch about 5 GB each.

```sh
python scripts/rebuild_hek_inventory.py --source <surviving raw response directory> --output artifacts/hek_major_inventory_recovery_20261108_r1 --expected-events-sha256 f0431c27d11abf7b2908f588634eccd61d960d5c1e67b1b4ffcfd2a5416afb0f
python scripts/audit_v2_label_inventory.py --inventory artifacts/hek_major_inventory_recovery_20261108_r1 --output artifacts/v2_label_inventory_recovery_20261108_r1
python scripts/materialize_v2_development.py --output artifacts/v2_development_features_recovery_20261108_r1 --inventory-audit artifacts/v2_label_inventory_recovery_20261108_r1
```

Compare every `shards[].sha256` in the new `report.json` with the frozen
`artifacts/v2_development_features_20261025_r2/report.json` before using any shard.
