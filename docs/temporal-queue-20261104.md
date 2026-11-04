# Remaining temporal fits, 2026-11-04

## Verified state

The earlier `2018/shuffled_interior_seed97` job completed all 10 epochs and
its saved outputs passed verification. This brings the experiment to 30
completed fits out of 42. The annual coordinator remained blocked by eight
historical reference files, not by a failed neural fit.

A serial queue now runs the remaining 12 prescribed fits for 2022 and 2023.
At 2026-11-04 22:22:14 +03:00, `2022/chronological_seed24` had saved epoch
1 of 10 and a new checkpoint; its worker process was independently verified.
The dashboard snapshot reported `queue_running`, 30/42 completed fits and
no record warnings. Progress after this snapshot must be checked live.

There are no new annual precision, recall, false-alarm or calibration results.
Only the 2014, 2015, 2016 and 2017 annual evaluations are complete. All 2018
fits are saved, but its annual evaluation is still pending. Model training
completion must not be reported as completed annual evaluation or a precision
improvement. The reserved 2024–2025 test data remain closed.

## Queue contract and safeguards

`scripts/resume_temporal_queue.py` uses the existing prepared folds, original
arm/seed order and original job serialization. The prepared manifest must
match SHA256
`35b38dba22048b32e82a1e6068d136d553c10a4cd486204fef71770e99e62711`.
The queue checks the protocol, source hashes and fit budget before proceeding.
It verifies completed annual artifacts, preserves existing job identities,
and lets the existing resume validator verify each fit's cache, inputs and
completed outputs. An unchanged worker runs in a fresh subprocess for each
unfinished fit. The shared experiment lock is held across the entire queue;
orphan workers are rejected and an error stops later jobs.

The orchestration change postpones annual evaluation while independent,
already prescribed fits continue. It does not change the architecture,
optimizer, seeds, epoch count, populations, probability calibration or alarm
threshold rules. It introduces no additional model candidates or neural fits
beyond the frozen budget. Evaluation labels are not passed to the worker.
The original annual coordinator must still verify the complete experiment
and perform its original calibration and evaluation after recovery.

When all fits finish, the queue records
`fits_complete_awaiting_annual_evaluation`; it does not create `report.json`
or mark the scientific experiment complete. Existing completed fits are
verified and skipped when recovery is restarted.

## Remaining dependency and monitoring

Eight historical files totaling 104,401 bytes remain cloud placeholders:
the baseline and short-control `report.json` files and their 2018, 2022 and
2023 `thresholds.json` files. The queue does not require these files for
independent neural fits. The final comparisons still require them.

The earlier waiter was retired after verifying its command and confirming
that it had no coordinator child. A replacement waiter is bounded to
172,800 seconds (48 hours), checks every 30 seconds, and waits for both
available inputs and a free experiment. It then invokes the unchanged annual
coordinator. This is conditional handoff, not a guarantee of file recovery or
completion within 48 hours. The source checkout is outside iCloud; the
experiment and cache still reside on Desktop and can become unavailable again.

The dashboard now distinguishes an identified queue from an orphan worker
and from the annual coordinator. PID reuse or a mismatched output path is
rejected. An active queue with no checkpoint activity for 15 minutes receives
a stale-progress warning; the dashboard does not infer process liveness from
saved JSON alone.

## Validation, evidence and reproduction

All 44 focused tests passed. Coverage includes unchanged job serialization,
preserved finished outputs, preparation hash rejection, queue failure
propagation, shared locks, individual job validation, missing manifest inputs,
handoff waiting, queue process identity, dashboard rendering and bilingual
publication. These are software and recovery checks, not model-quality scores.

Evidence is stored in `artifacts/runtime_recovery_20261104_r3/`:
`status.json`, `current_job.json`, `confirmation.json`,
`previous_waiter.json` and `handoff-supervisor.json`. Queue launch arguments
are in `artifacts/runtime_recovery_20261104_r1/launcher-queue.json`.
The new handoff state is in `artifacts/runtime_recovery_20261104_r4/`.
The worker writes its checkpoint and epoch history under the original
`artifacts/temporal_years_20261101_r1/2022/chronological_seed24/` path.

Read-only checks can be reproduced with the recovered runtime and local
checkout. The storage check returns status 2 while required reference files
are unavailable; this does not mean the independent fit queue has failed.

```sh
cd '/Users/esma/Library/Application Support/Helio24/execution-20261103-r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' scripts/check_temporal_storage.py --root '/Users/esma/Library/Application Support/Helio24/execution-20261103-r1' --protocol '/Users/esma/Desktop/Helio24/config/temporal-sequence-v2.json' --run '/Users/esma/Desktop/Helio24/artifacts/temporal_years_20261101_r1' --cache '/Users/esma/Desktop/Helio24/artifacts/sequence_cache_20261101_r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' -m pytest tests/test_resume_temporal_queue.py tests/test_await_temporal_resume.py tests/test_resume_temporal_job.py tests/test_temporal_storage.py tests/test_storage_preflight.py tests/test_experiment_monitor.py tests/test_experiment_views.py tests/test_bilingual_reports.py -q -p no:cacheprovider
```

To reproduce queue recovery after interruption, use the recorded queue
arguments with a fresh `--recovery` directory and the same frozen prepared
hash. Keep the original protocol, experiment and cache paths so saved job
identities remain valid. Confirm process identity before starting another
recovery process. Do not overwrite earlier recovery evidence or frozen
experiment outputs.

The next research deliverable remains the complete bilingual annual
comparison after all 42 fits and seven evaluable years are verified. No model
promotion is justified by this operational progress alone.
