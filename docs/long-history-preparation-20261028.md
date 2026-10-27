# Long-history precision experiment: preparation and storage blocker

## Status

No new model has been trained. Validation precision remains **7.9622%**, recall **95.0064%**: 742 true positives, 8577 false positives, 39 false negatives and 51008 true negatives across 60366 windows. These are the frozen incumbent's results, not results from the new features. Increasing precision while retaining recall >= 95% remains the research objective, not a guaranteed outcome.

## Implemented change

The new extractor uses raw magnetic observations preceding each forecast, independently of outcome-label filtering. It adds 196 features to the existing 96: mean, population standard deviation, endpoint change and normalized change for 24 measurements over each of 24 and 48 hours, plus availability and missing-fraction indicators. A complete history requires 120 or 240 observations at 12-minute cadence. Normalized change divides endpoint change by absolute mean plus standard deviation and is clipped to [-100, 100]. Zero denominator yields a missing value.

Forecast-time and later observations are excluded. Histories crossing a role's start boundary, a cadence gap or a leap-second transition are unavailable. Each measurement needs at least 80% finite values; otherwise its statistics are missing. Availability describes temporal coverage, not an assurance of instrument quality. Missing histories retain their forecast rows, with missing features and an availability flag. This prevents improving precision simply by dropping difficult forecasts.

## Local verification

Hash-verified snapshots from the prior audit were used. Every eligible USFLUX mean was compared with a direct raw-interval calculation; changing the target labels left the features unchanged.

| HARP | Retained windows | Available 24-hour histories | Available 48-hour histories |
| --- | ---: | ---: | ---: |
| 9152 | 106 | 106 | 86 |
| 9584 | 151 | 144 | 127 |
| Total | 257 | 250 | 213 |

This is an implementation check on two previously selected regions, not a representative performance estimate. It does not establish that the added features improve precision. Evidence is stored locally in `artifacts/long_history_readiness_20261028/report.json`, including input and code hashes. The checks do not resolve the earlier event-association uncertainty for HARP 9584.

## Full-data blocker and next experiment

The first full materialization attempt, `artifacts/long_history_20261028_r1`, failed during archive download with `ENOSPC`. Temporary downloads were cleaned; existing datasets and experiment evidence were preserved. The readiness snapshot recorded 215805952 free bytes against a conservative requirement of 5368709120 bytes (5 GiB). Downloads now run sequentially by default, check free space before starting and do not retry disk-full errors. Space estimates are a preflight guard, not a guarantee that every subsequent training step will fit.

Full materialization of the intended 595671 development windows is **not complete**. Once storage is available, use a fresh output directory and verify exact forecast-key correspondence. Freeze a new protocol revision with the actual history-report hash before training; `config/precision-long-history-v1.json` deliberately has a pending hash and is not ready for execution.

The frozen search budget contains three candidates (`history_logistic`, `history_xgboost`, `history_hist`) and four new-model blend weights (0.25, 0.5, 0.75, 1.0). Selection uses calibration precision at recall >= 0.95, with AP as a tie-breaker. Promotion requires higher validation precision at recall >= 0.95, no reduction in AP and no increase in Brier score or log loss. The 2024–2025 reserved test is not used. Repeated development comparisons can overfit validation; a successful development comparison would not by itself prove generalization.

## Reproduction

From the repository root, with the existing hash-verified audit snapshots and Python environment:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_long_history_readiness.py
# After freeing at least 5 GiB:
.venv/bin/python scripts/materialize_long_history.py --output artifacts/long_history_20261028_r2 --workers 1
```

The readiness script refuses to overwrite its existing output. For another run, change its output path to a fresh revision and preserve the original evidence; its code hash will consequently differ. The full materialization command is a pending next step, not a completed result. No training command is prescribed until the verified materialization hash is frozen in the next protocol revision. Generated artifacts and raw data remain outside Git.
