# Annual temporal experiment: integration and launch

The sequence reader, training-only preprocessing, isolated neural worker and annual
evaluation orchestrator are implemented. All seven eligible annual folds passed exact
population checks against both the original ensemble and the shorter-training control.
The actual experiment has started. This document freezes a launch-status snapshot;
it does not report improved precision or finished annual results.

## Prepared populations

| year | preparation | train_rows | train_positives | calibration_rows | calibration_positives | evaluation_rows | evaluation_positives |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | ready | 148508 | 2959 | 74149 | 1287 | 75228 | 2310 |
| 2015 | ready | 223647 | 4246 | 75228 | 2310 | 69138 | 1355 |
| 2016 | ready | 299785 | 6633 | 69138 | 1355 | 42987 | 181 |
| 2017 | ready | 370351 | 8036 | 42987 | 181 | 19529 | 253 |
| 2018 | ready | 413604 | 8241 | 19529 | 253 | 7799 | 0 |
| 2019 | skipped | 433399 | 8494 | 7799 | 0 | 4919 | 0 |
| 2020 | skipped | 441344 | 8494 | 4919 | 0 | 9813 | 0 |
| 2021 | skipped | 446303 | 8494 | 9813 | 0 | 28125 | 204 |
| 2022 | ready | 456126 | 8494 | 28125 | 204 | 50756 | 421 |
| 2023 | ready | 484549 | 8698 | 50756 | 421 | 60366 | 781 |

`ready` means input preparation passed, not that training or evaluation finished.
The ten calendar years yield seven eligible folds. Preserve the zero-positive 2018
evaluation with undefined recall; skip 2019–2021 under the original baseline rules.
Every fold uses the original boundary purging and HARP separation. The complete cache
retains 595671 forecast keys, 60 steps and 24 magnetic values per key. Disk-backed arrays
allow indexed access without constructing every fold as a full in-memory tensor.

Scaling uses signed log1p and float64 channel statistics from training windows only.
Repeated observations count as they occur in those windows. Missing values are filled
by zero after scaling, with separate masks; finite scaled values are clipped to [-8,8].
Each fold has one shared scaler for both input arms and all three seeds. Input shuffles
are deterministic from seed/HARP/UTC forecast key, preserve first/last steps, and move
measurement/mask channels together. Batch order cannot change a window's permutation.

## Fixed experiment and current state

| field | value |
| --- | --- |
| year | 2014 |
| arm | chronological |
| seed | 24 |
| completed_epochs_current_fit | 1 |
| completed_annual_evaluations | 0 |

The v2 execution protocol retains v1's model, optimizer, 10 epochs, batch size 128,
seeds 24/42/97, chronological/shuffled arms and annual folds: 42 neural fits in total.
CPU training uses four threads in a fresh Python exec process for each fit. No sklearn
or XGBoost is imported in neural workers. The previously observed native-runtime crash
is addressed by isolation; its exact underlying cause remains unresolved.

Evaluation targets are read during preparation only for frozen population audits;
they are never passed to neural workers. Workers receive training targets and unlabeled
calibration/evaluation indices. The parent calibrates the equal mean of three raw sigmoid
probabilities and persists the recall >=0.95 threshold using the prior calibration year
before computing evaluation metrics. Individual seeds are separately reported, never
selected. The original and shorter-training references must have identical evaluation
keys; their different training histories remain explicit. Paired HARP bootstrap and
chronological-versus-shuffled comparisons run after all six fits of a year finish.

No annual metric comparison is complete at this snapshot. Training loss, when available
in progress files, is an optimization diagnostic and is not precision, recall or evidence
of better probabilities. The earlier synthetic CPU estimate was approximately 18.31
compute hours, excluding loading, preprocessing, inference and evaluation. This is not
a promised completion time. The reserved 2024–2025 test remains closed.

## Recovery and validation

Each completed epoch atomically saves model parameters, AdamW state, torch RNG state,
NumPy batch RNG state and epoch history. Intermediate checkpoints are solely recovery
state; only the final epoch is evaluated. Synthetic testing forcibly interrupts a fit,
resumes it and checks exact prediction equality with an uninterrupted fit. Final-checkpoint
reuse also reproduces predictions, and changed input hashes fail closed. Additional tests
verify training-only scaling, missingness, stable keyed permutations, key alignment and
cache corruption detection. The suite passed 140 tests; the strengthened interruption
test passed separately after that suite run.

Resume verifies the protocol, runner code, prepared inputs, cache and completed jobs.
A runner lock prevents duplicate execution. A failed worker aborts the parent and records
failure.json; completed annual outputs are verified before reuse. No completed experiment
is overwritten. Process survival and eventual completion still require monitoring.

## Reproduction and monitoring

```sh
.venv/bin/python -m pip install -r requirements-sequence.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_temporal_years.py --protocol config/temporal-sequence-v2.json --output artifacts/temporal_years_20261101_r1 --cache artifacts/sequence_cache_20261101_r1 --prepare-only
.venv/bin/python scripts/run_temporal_years.py --protocol config/temporal-sequence-v2.json --output artifacts/temporal_years_20261101_r1 --cache artifacts/sequence_cache_20261101_r1
.venv/bin/python scripts/report_temporal_execution.py --source artifacts/temporal_years_20261101_r1 --output artifacts/temporal_execution_start_20261101_r1 --name temporal-execution-20261101
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_temporal-execution-20261101
```

The foreground execution command also resumes an interrupted run from its last completed
epoch. Do not start another runner while the existing one holds the lock. Inspect
`artifacts/temporal_years_20261101_r1/progress.json`, `run.log` and each
`year/arm_seed/worker.log` and `progress.json`; inspect `failure.json` if a process exits.
Completed annual results appear in `year/finished.json`; the final report.json and
metrics.csv are produced only after all eligible years finish. The active launch uses
a detached local process recorded in launcher.json. This snapshot is not a live monitor.

For independent reruns use new output/cache directories. Freeze a new protocol revision
for changes to design or hashed runner code. Use new snapshot directories/document names;
register both reviewed editions in docs/reports.json and docs/reports.md, then publish
paired HTML. Datasets, caches, checkpoints, predictions and generated HTML remain outside
Git. Local app.py branding changes remain uncommitted.

| source | sha256 |
| --- | --- |
| config/temporal-sequence-v2.json | 76db8b565b8ad2ba9f0f322458dd30eb18f9d2c87d34c66ebffb76d055c7cdd0 |
| artifacts/temporal_years_20261101_r1/prepared.json | 35b38dba22048b32e82a1e6068d136d553c10a4cd486204fef71770e99e62711 |
| artifacts/temporal_execution_start_20261101_r1/report.json | ef9a2c845e8d067d2cefbdd1f442235407ea186de48dfa518e4bb393738279a1 |

