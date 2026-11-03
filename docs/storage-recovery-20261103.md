# Training storage recovery, 2026-11-03

## State and evidence

No annual TCN runner or worker was active when checked. The last verified
experiment snapshot contains 29 completed fits out of 42, with annual evaluations
for 2014, 2015, 2016 and 2017. The next fit is
`2018/shuffled_interior_seed97`; 13 fits remain. This is the last verified
snapshot, not a fresh validation of every result: some experiment files are now
cloud placeholders. The root `progress.json` saying `training` does not prove
that a process is alive. There are no new model scores from this recovery work.

The preceding failure was a source file read timeout. Inspection now also finds
cloud placeholders in experiment manifests and cache files. The 3,431,065,088
byte `values.npy` was initially a placeholder and subsequently became local.
Downloading this file alone does not establish that the complete run is usable.
macOS accepted download requests; completion must be checked separately.

## Restored files and protected inputs

The previously restored `config/research-direction-v1.json` matches the frozen
direction SHA256 `31eda27d68bb1b63e4047027f7c20acf3adfc9b1e9aa4783b758c4ecb59f04cb`.
Eight further missing files were recovered from published commit
`a854bf32965518d74086dbde0ecb097be48d620b`:

* `config/temporal-sequence-v1.json`
* `docs/temporal-execution-20261101.md`
* `helio24/sequence_training.py`
* `scripts/check_sequence_readiness.py`
* `scripts/consolidate_experiments.py`
* `scripts/materialize_sequences.py`
* `scripts/run_recency_training.py`
* `tests/test_temporal_worker.py`

A separate checkout was created at
`/Users/esma/Library/Application Support/Helio24/execution-20261103-r1`.
All 11 `runner_code_hashes` match the frozen protocol in that checkout.
Its `artifacts` and `data` entries point to the original Desktop locations;
this is a source checkout outside iCloud, not a migration of the experiment data.
No checkpoints or frozen result files were rewritten. The reserved 2024–2025
test dataset remains closed. Local branding edits in `app.py` remain uncommitted.

## Changes and verification

`scripts/check_temporal_storage.py` inspects file metadata without opening
placeholder contents. It exits with status 2 when files are missing,
inaccessible or marked `SF_DATALESS`, and status 0 when the inspected paths
are locally available. This is a conservative directory check of development
resume inputs, not dependency tracing or a hash verification. Availability can
change after inspection; the existing runner must still verify frozen hashes
and completed outputs before resuming.

The dashboard now distinguishes inaccessible required records from an experiment
that never started. It hides unverified completion counts and process status.
Optional placeholder JSON records are skipped without attempting a blocking
read. A runner outside the Desktop folder is recognized using its launcher
script path and matching experiment output; an unrelated PID is rejected.

All 20 focused storage, monitor, dashboard and bilingual publication tests passed. These tests validate
failure handling and process identification; they do not establish model quality
or prove that iCloud has finished downloading all experiment files.

## Reproduction and remaining work

Run from the local checkout with the recovered runtime:

```sh
cd '/Users/esma/Library/Application Support/Helio24/execution-20261103-r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' scripts/check_temporal_storage.py --root '/Users/esma/Desktop/Helio24' --run '/Users/esma/Desktop/Helio24/artifacts/temporal_years_20261101_r1' --cache '/Users/esma/Desktop/Helio24/artifacts/sequence_cache_20261101_r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' -m pytest tests/test_storage_preflight.py tests/test_experiment_monitor.py tests/test_experiment_views.py tests/test_bilingual_reports.py -q -p no:cacheprovider
```

Wait for required files to become local, rerun the availability check, then let
the unchanged runner verify hashes and resume saved work. Confirm a new epoch
checkpoint before reporting training progress. After all 42 fits and seven
annual evaluations are verified, produce the complete bilingual comparison of
precision, recall, false alarms, calibration and uncertainty. Do not promote a
model from the current incomplete development results.
