# Runtime recovery and resumption of temporal training

Training was resumed with a local Python environment outside the cloud-managed Desktop.
The existing experiment and frozen execution protocol were retained. This is an
operational recovery snapshot; no new precision, recall or annual comparison is reported.

## Observed failure and recovery

The worker failed before training 2015/chronological/seed42, while Python imported its
site module and read virtual-environment configuration. The exception was
`TimeoutError: [Errno 60] Operation timed out`. macOS marked `.venv/pyvenv.cfg` and
`.git/config` as `dataless`; File Provider reported the configuration as not downloaded.
The original scan found 2136 dataless virtual-environment files. After Keep Downloaded
was enabled and download requests submitted, the critical configuration became local
and Python started, but 2097 environment files remained unavailable and scientific-package
imports still timed out. Keep Downloaded was confirmed enabled. We did not establish why
the remaining cloud downloads stalled; neither RAM exhaustion nor a full disk was proved.

A new environment was created at
`/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101`.
Python remained 3.14.3 and all 87 distribution versions were pinned from the original
installation's dist-info directory names. Installed metadata in the replacement was
compared against every pin, with no version mismatches. Existing virtual-environment
files, experiment inputs, checkpoints and frozen reports were preserved.

| field | value |
| --- | --- |
| original_python | 3.14.3 |
| replacement_python | 3.14.3 |
| pinned_packages | 87 |
| package_version_mismatches | 0 |
| tests_passed | 6 |
| completed_fits_retained | 7 |
| planned_fits | 42 |
| resumed_year | 2015 |
| resumed_arm | chronological |
| resumed_seed | 42 |
| completed_epochs_current_fit | 1 |
| prediction_files_identical | 2 |
| cloud_venv_dataless_before_rebuild | 2097 |


The epoch count is the state at snapshot creation, not a live counter. The seven retained
fits comprise six fits for 2014 and one for 2015. Resumption continues with
2015/chronological/seed42. The original runner verifies code, protocol, input/cache hashes
and completed output hashes; it skips completed annual evaluations and completed fits.
The new launcher is `artifacts/runtime_recovery_20261101_r1/launcher.json`; the initial
experiment launcher remains historical. The original failure was copied into this
recovery directory. The old failure.json in the active run records the earlier stop;
use the current process, worker progress and logs to assess resumed execution.

## Validation and limits

Six focused tests passed: three sequence preprocessing/cache tests, one isolated worker
interruption/recovery test and two annual-evaluation tests. No full-suite result is
claimed for this recovery. In addition, a completed 2014/chronological/seed24 checkpoint
was copied into a separate replay directory. The unchanged worker loaded its final-epoch
state and regenerated calibration and evaluation predictions without training again.
Both `.npy` files had exactly the same SHA-256 as the original outputs. Replay evidence
is in `verification.json` and `replay/result.json` under the recovery directory.

This verifies package-version agreement and prediction reproduction for one checkpoint;
it does not prove all future fits are invariant to environment installation details.
The runtime's files are outside the cloud-managed project, while source and data paths
still use the Desktop project. Keep Downloaded and source availability remain relevant.
Runtime process and worker CPU use were checked after launch. Completion still requires
monitoring. No architecture, optimizer, seed, split, threshold policy or reserved-test
access changed. No model was promoted.

## Reproduction and monitoring

```sh
/opt/homebrew/bin/python3.14 -m venv "/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101"
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -m pip install -r requirements-runtime-recovery-20261101.txt
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -m pytest tests/test_sequence_training.py tests/test_temporal_worker.py tests/test_temporal_evaluation.py -q
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -u scripts/run_temporal_years.py --protocol config/temporal-sequence-v2.json --output artifacts/temporal_years_20261101_r1 --cache artifacts/sequence_cache_20261101_r1
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/publish_reports.py --output artifacts/bilingual_reports_runtime-recovery-20261101
```

For a fresh independent recovery use a new runtime directory and evidence directory.
The training command above resumes the current run; do not launch it concurrently with
an active runner. Existing locks prevent duplicate runners. Record the chosen interpreter
and package pins. To repeat the prediction check, copy the completed job.json and its
checkpoint.pt to a fresh replay directory, invoke scripts/temporal_worker.py with that
job, then compare calibration.npy and evaluation.npy SHA-256 with the originals. Never
replace the original completed job files. When resuming an incomplete fit, checkpoints
restore optimizer and RNG state as specified by the unchanged protocol.

Inspect `artifacts/temporal_years_20261101_r1/progress.json` and
`2015/chronological_seed42/progress.json` plus worker.log. The process ID and actual
command are in the new recovery launcher. Preserve the original failure as historical
evidence; a later failure can update the active run's failure.json. New report publication
must use a new output directory. Both complete document editions are registered through
the bilingual index. Requirements and documentation are committed; environments, data,
replay outputs and checkpoints remain outside Git. Local app.py changes remain uncommitted.

| source | sha256 |
| --- | --- |
| config/temporal-sequence-v2.json | 76db8b565b8ad2ba9f0f322458dd30eb18f9d2c87d34c66ebffb76d055c7cdd0 |
| requirements-runtime-recovery-20261101.txt | 1b719da8aee31b78fd0bc511007132957247813e6a2533b72dcfe649f95aca87 |
| artifacts/runtime_recovery_20261101_r1/verification.json | 65d7e3d63ca0296ea547b0e7bd7758168723cea81ba4d085a786e3f3c2a0d118 |
| artifacts/runtime_recovery_20261101_r1/launcher.json | e9956651da33f1b30c6c81d9cbfebe311b69b0dbe3f2e873f60185082074068b |
| artifacts/runtime_recovery_20261101_r1/original_failure.json | 4490acb68df9684270293aed0d3040c7f98c8395925a3b69fadbd0066e1df8db |
| artifacts/runtime_recovery_20261101_r1/recovery_report.json | 718e7539b964d66b0b166a966913e39ca6353935cafe179dfef5f1daad0c2091 |

