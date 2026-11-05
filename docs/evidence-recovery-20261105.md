# Completed fits and reference evidence recovery

## State on 2026-11-05

All 42 prescribed neural fits finished. The queue recorded completion at
2026-11-05T04:14:24.549819+00:00. Annual evaluations exist for 2014, 2015,
2016 and 2017; evaluations for 2018, 2022 and 2023 remain pending. Training
completion does not establish a precision improvement. No new final metrics
are available, and the reserved 2024–2025 test remains closed.

## Exact baseline recovery

The historical baseline report was reconstructed from saved predictions,
trusted local fitted models, prepared fold audits and the original metric
functions. Its 63,294 bytes match the frozen report SHA256 exactly:
`6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c`.

We restored 26 missing or cloud-only baseline files, totaling 184,785 bytes.
Every restored file matches its original report manifest hash; the report
itself matches the frozen protocol. Existing readable files were checked
rather than overwritten. Cloud placeholders were moved to the recovery
backup before replacement. No model was retrained and no threshold changed.
The local restoration inventory is
`artifacts/runtime_recovery_20261105_r1/baseline-restoration.json`.

## Remaining storage limitation

The annual coordinator's unavailable reference inputs decreased from eight
to four: the short calibration control's `report.json` and the 2018, 2022
and 2023 `thresholds.json` files. An independent attempt to reconstruct that
report is blocked by its cloud-only `2019/predictions.parquet` file. That
file is needed to reproduce the historical report, not to add a new annual
evaluation or fit.

macOS reports `isKeepDownloaded=1` for the project and this prediction file,
but the file is not downloaded. Its provider metadata reports an upload
error, `NSFileProviderErrorDomain -1005`, with an underlying
`open error: 45 (Operation not supported)` and the message “Dosya yok.”
This does not prove that a usable remote copy exists. We requested project
and targeted downloads, restarted `fileproviderd` and `bird`, and requested
the critical files again. At this snapshot they remain placeholders.
The global Optimize Mac Storage setting was not successfully changed or
verified. Keep Downloaded is a retention request, not evidence of recovery.

The existing supervisor continues waiting for verified local inputs before
invoking the original annual coordinator. It must not bypass frozen hashes
or fabricate missing probabilities. The original float64 feature summaries
cannot be assumed identical to summaries reconstructed from the float32
sequence cache. No final experiment completion or model promotion is claimed.

## Reproduction

Use the recovered Python runtime and a new staging directory:

```sh
export PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261105
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/reconstruct_baseline_evidence.py --output /tmp/helio24-baseline-review-new
"$PY" scripts/check_temporal_storage.py --run artifacts/temporal_years_20261101_r1 --cache artifacts/sequence_cache_20261101_r1 --protocol config/temporal-sequence-v2.json
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261105_r2
```

The reconstruction command only writes a new candidate directory and fails
if its report differs from the frozen hash. It loads trusted local joblib
models and requires saved predictions; it does not automatically restore
files. The storage check exits unsuccessfully while inputs remain unavailable.
Use a fresh publication directory on subsequent runs. Generated evidence,
models and datasets remain outside Git.

Verification: the committed reconstruction command reproduced the exact frozen
report hash in a fresh directory. The bilingual report and storage checks passed
13 tests. The external Python cache avoids cloud-only bytecode files; it does
not change model inputs or metrics.
