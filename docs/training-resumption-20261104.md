# Verified training resumption, 2026-11-04

## Outcome and scope

Training resumed for the existing `2018/shuffled_interior_seed97` job. At
2026-11-04 00:51:50 +03:00, its first epoch and a new checkpoint were saved.
The worker process was independently observed consuming CPU. The first epoch
took 201.77095866699892 seconds; this is not a completion-time forecast.

After restoring inputs, 220 declared preparation and completed-output files
were hash-verified. There are 29 completed fits out of 42, with completed annual
evaluations for 2014, 2015, 2016 and 2017. One of the 13 unfinished fits is now
running; the other 12 have not started. These counts do not claim the current
fit or its annual evaluation is complete.

There are no new precision, recall, false-alarm or calibration results. Training
loss describes optimization, not forecast quality. The reserved 2024–2025 test
data remain closed. The frozen architecture, seeds, epoch budget, thresholds
policy and scientific source code were not changed.

## Input recovery

The initial directory scan found 118 cloud placeholders totaling 6,806,451
bytes. Metadata inspection alone missed two absent files. The new check reads
available manifests and explicitly checks their declared paths, so deleted
inputs cannot be hidden by the presence of their parent directories.

Four inputs were reconstructed, with byte-identical SHA256 matches against
the original preparation manifest before installation:

| Path relative to the experiment | SHA256 |
| --- | --- |
| `2014/target.npy` | `95126a1a894ab59d85c755e74e40744da7874b3b5cb38b4fbeafbb83f91c373b` |
| `2017/evaluation.npy` | `643ad2b28997439e1b44d07321d9ff0e9dcc412cacb04ea1dd7abb9fc8ef5a3c` |
| `2018/calibration.npy` | `643ad2b28997439e1b44d07321d9ff0e9dcc412cacb04ea1dd7abb9fc8ef5a3c` |
| `2018/evaluation-metadata.parquet` | `a96e46105e28417aaff2e3a573d3c4d49cca9dd9d91cd7c10f86cf26e5bf68e2` |

The 2014 training targets came from the same indexed windows in the verified
2018 training arrays. The index arrays were recreated by aligning forecast
keys with saved metadata. The 2018 evaluation metadata were extracted from
the original baseline prediction table with the original column order and
serialization. The metadata recovery did not send evaluation labels to the
neural worker. Original content hashes, rather than approximate numerical
agreement, determined whether each restoration was accepted.

## Execution and automatic handoff

`scripts/resume_temporal_job.py` validates the existing job against the
prepared fold and protocol, verifies frozen scientific source hashes, the
direction/base/smoke references, the complete sequence cache and this fit's
input hashes, then starts the unchanged isolated worker. It holds the same
experiment lock as the annual coordinator and rejects an existing orphan
worker. Completed jobs require their original identity, epoch count and all
three output artifacts. It does not evaluate years or choose a new model.

The local execution checkout is
`/Users/esma/Library/Application Support/Helio24/execution-20261103-r1`.
The recovered Python runtime is
`/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python`.
Experiment and cache paths remain on Desktop; their future local availability
is not guaranteed by moving the code alone.

`scripts/await_temporal_resume.py` checks every 30 seconds for available
manifest-declared inputs, no active worker and a free experiment lock. When
these conditions hold, it invokes the unchanged annual coordinator, which
performs the complete frozen verification again and skips verified completed
work. Waiting is bounded to 86,400 seconds. If inputs remain unavailable, the
waiter records `waiting_timeout`; it does not claim that training started.
The original coordinator lock remains the final guard against a launch race.

At this snapshot, eight historical reference files totaling 104,401 bytes
still block the annual coordinator: the baseline and short-control
`report.json` files and their 2018, 2022 and 2023 `thresholds.json` files.
The current fit does not need these files; annual calibration, comparison and
the complete final report still require them. Automatic handoff is conditional
on their recovery, not a promise that all remaining training will finish.

## Evidence, verification and reproduction

The 37 focused tests passed across storage, manifest discovery, isolated job
resumption, handoff waiting, process monitoring, dashboard and bilingual
publication. They cover missing declared inputs, unavailable manifests,
changed cache/source/fold hashes, altered job identities, existing workers,
experiment locks and bounded waiting. They do not measure model performance.

Local evidence is in `artifacts/runtime_recovery_20261104_r1/`:
`restored_inputs.json`, `completed_verification.json`,
`progress_confirmation.json`, `launcher.json`, `status.json` and
`supervisor.json`. The handoff state and eventual coordinator launcher/log are
in `artifacts/runtime_recovery_20261104_r2/`. A saved PID is not proof that a
process remains active; verify its command and newly saved progress.

Run the following checks from the local checkout. Before manually launching
recovery, confirm that the existing worker/waiter is not already doing that
work, and choose a fresh status or recovery output path.

```sh
cd '/Users/esma/Library/Application Support/Helio24/execution-20261103-r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' scripts/check_temporal_storage.py --root '/Users/esma/Library/Application Support/Helio24/execution-20261103-r1' --protocol '/Users/esma/Desktop/Helio24/config/temporal-sequence-v2.json' --run '/Users/esma/Desktop/Helio24/artifacts/temporal_years_20261101_r1' --cache '/Users/esma/Desktop/Helio24/artifacts/sequence_cache_20261101_r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' -m pytest tests/test_await_temporal_resume.py tests/test_resume_temporal_job.py tests/test_temporal_storage.py tests/test_storage_preflight.py tests/test_experiment_monitor.py tests/test_experiment_views.py tests/test_bilingual_reports.py -q -p no:cacheprovider
```

The exact launch arguments are preserved in `launcher.json` and
`supervisor.json`. The next research deliverable is the complete paired annual
evaluation after all 42 fits and seven evaluable folds are verified. Neither
the partial training progress nor an individual seed should determine model
promotion.
