# Next research direction and delivery status

## Completed product work

The Experiment progress tab now includes the final annual comparison, a year selector,
precision/recall/false-alarm and probability metrics, a precision trend, acceptance
counts, full metric CSV download and both full report editions. The final report is
pinned by SHA256 in `config/dashboard-comparison-v1.json`; metric and comparison
files are verified before display. Missing or changed evidence shows an unavailable
message instead of unverified scores. The zero-positive 2018 period explicitly shows
undefined recall/AP. Historical replay is unchanged; this is a development comparison,
not a live prediction model or independent final test.

The completed chronological TCN beats baseline precision in only one of six positive
years and passes the full comparison in zero years. AP is worse in all six positive
years; Brier and log loss are worse in all seven eligible years. The small 2015 precision
gain has a paired uncertainty interval crossing zero. No model is promoted. Existing
false-alarm analysis localized persistent regional errors in 2014–2016; it must not be
presented as an all-year causal diagnosis.

## Selected direction

`config/research-direction-v2.json` selects an audit-first investigation of causal
regional flare-history context added to the fixed summary-feature ensemble. The
hypothesis is that activity known before issue time may help distinguish persistently
high magnetic measurements from impending strong flares. This is not demonstrated;
aggregate metric failures do not prove that these missing features are the cause.
The old sequence direction and all frozen experiments remain intact.

Candidate feature identifiers are `count_C_24h`, `count_MX_24h`, `count_C_72h`,
`count_MX_72h`, `hours_since_C_capped_72`, `hours_since_MX_capped_72`,
`history_coverage_24h`, and `history_coverage_72h`. All event completion, publication
and region-association availability times must strictly precede the forecast. Unknown
history is missing, not quiet. Future region outcomes, post-hoc region rankings,
retrospective associations and revised catalogs without availability evidence are
excluded from predictors. Coverage features must describe availability at issue time.

The first gate requires source versions, publication timestamps and contemporaneous
region associations across all required years. A header-only check of
`data/flare_catalog.csv` found event times and region information but no publication
or association-availability timestamps. Field-name aliases can map event identity,
end time and region; they cannot manufacture availability evidence. The local audit
is `artifacts/research_direction_20261106_r1/source-preflight.json`.
No catalog rows or reserved test were read for this header check. Training is not ready.

Only after provenance and coverage are established will an execution protocol freeze
one augmented ensemble recipe, with no hyperparameter search. Budget: seven annual
ensemble fits, fourteen constituent estimator fits. Compare against the frozen
96-feature ensemble on identical forecast keys. Preserve annual HARP separation,
boundary purging, prior-year calibration with target recall >=0.95, all seven eligible
years including zero-positive 2018, and paired HARP uncertainty. The six positive years
must each improve precision and FP at recall >=0.95; AP must not fall and Brier/log loss
must not rise. These are project comparison rules, not universal ranges. Already
inspected years remain adaptive development; the reserved 2024–2025 test stays closed.
If reliable source availability cannot be established, stop this direction as infeasible
rather than simulate historical knowledge. More TCN epochs, broad model grids and small
weight/calibration searches remain parked. Alert suppression is not window precision.

## Recovery and independent backup: pending dependencies

The historical `calibration_windows_20261030_r1/2019/predictions.parquet` remains
unrecovered. No Time Machine backup or local snapshot was listed. Safari opened
https://www.icloud.com/recovery/ but page automation could not read the contents:
Apple Events JavaScript is disabled and the accessibility query returned no content.
We did not change that browser security setting or claim to inspect the remote file list.
The user was asked to check Restore Files and restore only the matching historical file.
Any recovered candidate must match the original control report's artifact hash.
Apple documents recovery of eligible deleted files within 30 days; this is not evidence
that this particular file is available. [Apple recovery instructions](https://support.apple.com/en-asia/guide/icloud/mmae56ea1ca5/icloud).

No external physical disk was listed; `/Volumes` contained only Macintosh HD. The
503-file local verified snapshot remains available but is on the same disk.
`scripts/copy_evidence_backup.py` prepares the second-copy step: it requires a mounted
external volume, verifies source and copied hashes, refuses existing destinations,
checks space and retains the missing-file inventory. No external backup has been created.
A connected disk is required; a second internal folder does not fulfill this step.
Read-only backup files still can be deleted and do not protect against disk failure.

## Reproduction

```sh
export PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261106
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" -m pytest tests/test_final_comparison.py tests/test_experiment_views.py tests/test_copy_evidence_backup.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261106_r2
"$PY" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

After attaching a real external disk, substitute its actual volume name and a new
destination in this command. It does not format or erase the disk:

```sh
"$PY" scripts/copy_evidence_backup.py --source '/Users/esma/Library/Application Support/Helio24/backups/evidence-20261106-r1' --output '/Volumes/EXTERNAL_DISK/Helio24/evidence-20261106-r1'
```

Review both report editions, update the catalog source hash and publish into a fresh
directory. Datasets, models and generated evidence stay out of Git; local branding
changes in `app.py` remain uncommitted. No new fits or metric gains are claimed.
