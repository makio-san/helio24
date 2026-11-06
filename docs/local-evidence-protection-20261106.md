# Local evidence recovery and protection

## Verified state

The annual coordinator finished successfully at 2026-11-06T08:19:14.767968+00:00
(11:19 in Europe/Istanbul). All 42 fits and all seven eligible annual evaluations
are complete. Both reference reports match the frozen protocol hashes. The final
comparison independently verified the completed experiment manifest and recomputed
metrics. See [the complete evaluation](temporal-evaluation-final-20261106.md).
No model was promoted and the reserved 2024–2025 test remains closed.

The chronological TCN beats baseline precision in only one of six positive years.
It passes the full comparison rule against baseline in zero years. This result
supports closing this prescribed experiment, not more epochs without a new hypothesis.

## Recovery and remaining gap

The four previously unavailable coordinator inputs are now local. The supervisor
resumed automatically; this inspection does not establish which download action
made them available. The missing short-control `metrics.csv` was reconstructed
from its frozen report and restored only after exact SHA256 equality:
`73fb4536374c125ee1e611a84ecb8d6207539d70ae6ab744042c7550e2314340`.

One historical file remains absent:
`artifacts/calibration_windows_20261030_r1/2019/predictions.parquet`.
No matching copy was found in the searched project, temporary recovery directories,
external runtime/execution directories or Finder Trash. Terminal access to Trash
was denied by macOS; Finder inspection succeeded. A remote recovery copy has not
been verified. Aggregate metrics cannot reconstruct the original row probabilities.
The file is not required by the completed seven-year TCN evaluation, but its absence
prevents claiming that the entire historical control experiment is fully restored.

## Protection applied

Created a new snapshot outside Desktop, Documents and iCloud Drive:
`/Users/esma/Library/Application Support/Helio24/backups/evidence-20261106-r1`.
It contains 503 verified files: the temporal experiment, sequence cache, baseline,
available short-control evidence, final comparison and configuration. Each copied
file was hashed, checked against its frozen manifest where available, copied with
APFS clone support, verified again and marked read-only. The snapshot manifest
explicitly records the missing historical prediction file; `complete` is false.
The complete temporal experiment itself has no missing manifest entries.

`scripts/snapshot_evidence.py` refuses an existing destination, cloud-managed
destinations, invalid source folders and modified frozen artifacts. It records
missing/cloud-only files rather than pretending they were backed up. Three focused
tests cover preservation, missing-file reporting, overwrite refusal, hash mismatch
and destination/source rejection. Generated artifacts stay outside Git.

This is an independent directory on the same disk, not an independent physical
backup. It protects these existing copies from Desktop iCloud eviction and source
file deletion, but not disk failure or deliberate deletion of the backup. Read-only
files are not undeletable. No global iCloud setting is claimed changed, and future
outputs are not automatically included. Take a fresh snapshot after each completed
experiment; add a separate disk or versioned remote backup for hardware protection.

## Reproduction and remaining work

```sh
export PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261106
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/snapshot_evidence.py --folder artifacts/temporal_years_20261101_r1 --folder artifacts/sequence_cache_20261101_r1 --folder artifacts/walk_forward_20261028_r1 --folder artifacts/calibration_windows_20261030_r1 --folder artifacts/temporal_evaluation_20261106_r1 --folder config --output '/Users/esma/Library/Application Support/Helio24/backups/evidence-20261106-r2'
"$PY" -m pytest tests/test_snapshot_evidence.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261106_r1
```

Use new output names on repetition. Remaining priorities are recovery of the one
historical file from a genuine backup if available, an independent physical backup,
and selecting the next research hypothesis from the final multi-year error analysis.
Dashboard presentation of the final comparison can follow. Further fitting needs a
new frozen experiment plan; the current experiment is complete.
