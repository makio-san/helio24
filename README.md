# Helio24

A research prototype for estimating whether a solar active region will produce
an M- or X-class flare within the next 24 hours.

## Current status

The first real-data experiment and local Streamlit dashboard are implemented.
That experiment uses a deterministic 10% sample from partitions 1, 3 and 5.
A second experiment now covers all five archives, with chronological probability
calibration, recall targets and whole-region uncertainty intervals.

See [the first experiment](docs/first-experiment.md) for measured results and
[the data contract](docs/data-contract.md) for label semantics and leakage controls.
See [the second experiment](docs/second-experiment.md) for the full-data audit.
The [third experiment protocol](docs/third-experiment-protocol.md) fixes the
temporal-feature comparison before its results are generated.
Its [measured results](docs/third-experiment.md) reject the fixed temporal
candidate under the preregistered development rule.
An [event and alarm audit](docs/event-audit.md) now measures persistent alarm
periods, covered catalog events and disagreements with benchmark labels.
The [provenance investigation](docs/event-provenance.md) traces one disagreement
to distinct association channels and checks annotation timestamp conventions.

## Setup

Requires Python 3.11 or newer and `curl`.
The current experiment was run with Python 3.14 on macOS.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On macOS, XGBoost also requires the OpenMP runtime: `brew install libomp`.

## Data

Source: [SWAN-SF on Harvard Dataverse](https://doi.org/10.7910/DVN/EBCFKM).

```sh
python scripts/download.py
```

The script downloads partitions 1, 3, and 5 (about 3.3 GB in total), verifies
archive checksums, and retains a deterministic 10% sample from each partition.
Sampling uses the HARP identifier and observation start, without using the label.
The full archives remain on disk. Interrupted downloads resume on the next run.

Use `--partitions 1 2 3 4 5 --fraction 1` to retain all records from all partitions.
This requires additional download time and disk space.
The first notebook still uses partitions 1, 3 and 5; downloading more partitions
does not automatically change its experimental design.

Datasets, local environments, generated outputs, and credentials are excluded
from Git. Downloaded data is not redistributed in this repository.

## Run the experiment

```sh
python scripts/run_notebook.py
```

This executes [the notebook](notebooks/01_helio24_baseline.ipynb), inspects the
real files, builds observation-only features, fits three models, and reports
held-out metrics. Allow several minutes for the data inspection step.
The executed notebook, model, predictions, metrics, calibration bins, and error
analysis stay in the ignored `artifacts/` directory. Data-quality exclusions
are saved under `data/prepared/`.

The tracked notebook has no outputs, so raw measurement examples and local
execution details are not uploaded to GitHub. To work interactively, open it
with a notebook editor using the project's `.venv` interpreter.

## Open the dashboard

```sh
streamlit run app.py --server.address 127.0.0.1
```

Open http://localhost:8501. Select a HARP region and a historical date, inspect
the previous 12 hours, and reveal the next 24 hours' recorded outcome.
The performance tab compares the models and allows threshold exploration on
validation data without changing the fixed test evaluation.

Replay filters isolate misses, false alarms, hits, or correct quiet forecasts.
Only regions and times matching the selected outcome are offered. The evaluation
tab includes an error table and a CSV download without local paths or model inputs.
Outcome-based filtering is retrospective analysis; it does not change predictions.

## Commit style

Use short, descriptive English messages with a type, scope, and final period:
`fix(replay): preserve missing observation gaps.` Keep commits focused on one
verified change and exclude datasets, credentials, and generated artifacts.

## Verification

```sh
python -m pytest -q
```

Tests cover forecast boundaries, quality masking, exclusion of outcome features,
temporal and HARP separation, metric denominators, threshold selection, and
dashboard states. The real-data dashboard test is skipped if no local experiment
artifacts exist.

## Evaluation rules

- Training: partition 1; validation: partition 3; test: partition 5.
- No random train/test split; purge overlapping windows and shared HARP IDs.
- Fit imputation and scaling on training data only.
- Choose the model by validation average precision and its threshold by validation TSS.
- Report recall, precision, false alarms, Brier score, and calibration bins.
- Count forecast windows, not independent flare events.

The dashboard still shows experiment 1's raw model estimates. Experiment 2 adds
calibration and region-based uncertainty without automatically replacing that
model. The temporal-feature comparison and event audit are development analyses;
an untouched later-period evaluation remains future work. Reusing inspected test
records must not be presented as a fresh evaluation.

The first version uses historical data. Flare probability does not estimate
damage to a satellite or the impact on Earth.

## Experiment 2: full-data calibration

The [fixed protocol](docs/second-experiment-protocol.md) assigns partitions 1–2
to training, 3 to calibration, 4 to threshold selection, and 5 to a retrospective
audit. Partition 5 was already inspected; it is not an untouched final test.

```sh
python scripts/freeze_experiment.py
python scripts/download.py --partitions 1 2 3 4 5 --archives-only
python scripts/prepare_full.py --workers 2
python scripts/run_calibration.py
python scripts/report_calibration.py
```

Preparation streams compressed archives instead of extracting every raw file.
It writes bounded batches and verified per-partition feature caches; rerunning
preparation reuses complete caches when code, catalog and file hashes match.
The five compressed archives total about 5.7 GB. Feature tables and outputs need
additional space, but expanded raw archives are not required.

Results go to `artifacts/experiment2/`, including a standalone `report.html`,
PNG figures, metrics, probability-bin counts, frozen thresholds and HARP-cluster
intervals. Experiment 1 and the dashboard model remain unchanged. An existing
experiment 2 report is never silently replaced by the training command.

The comparison includes the frozen sample model, full-data raw XGBoost, its
sigmoid calibration and a constant reference. Calibration fits only on partition
3. Recall targets of 80%, 90% and 95% are selected on partition 4 before auditing
partition 5. A validation recall target is not guaranteed on a later period.
Strictly monotonic calibration preserves ordering; it cannot alone reduce false
alarms at an equivalent recall operating point.

Uncertainty uses 1,000 whole-HARP bootstrap resamples. These intervals account
for within-region window dependence but exclude model-fitting uncertainty and
do not capture every source of cross-region or solar-cycle dependence.

## Experiment 3: temporal discrimination

The fixed [temporal protocol](docs/third-experiment-protocol.md) compares the
existing 12-hour summaries with recent 1-, 3- and 6-hour slopes, changes and
change volatility. Generate its ignored feature caches without expanding the
archives:

```sh
python scripts/prepare_temporal.py --workers 2
python scripts/run_temporal_experiment.py
```

The command verifies every source archive and writes only bounded Parquet
batches under `data/temporal/`. It can safely reuse a complete cache whose data,
code and catalog hashes still match.
The experiment command first writes its development decision, then loads the
previously inspected fifth partition for a descriptive stability check. Results
stay under `artifacts/experiment3/`; an existing final report is not overwritten.

Render the standalone local report after a completed run:

```sh
python scripts/report_temporal.py
```

## Alarm periods and catalog event audit

After experiment 2, run the fixed [event audit protocol](docs/event-audit-protocol.md):

```sh
python scripts/prepare_event_mapping.py
python scripts/run_event_audit.py
python scripts/report_event_audit.py
```

Preparation scans the existing partition-4 archive for verified catalog/HARP
associations, including events omitted from strongest-window labels. The audit
uses frozen development predictions; no model fitting or threshold tuning occurs.
It preserves gaps in alarm periods, reports coverage-conditioned event recall,
and exports ambiguous, uncovered and conflicting associations separately.

Open `artifacts/event_audit/report.html` for the self-contained report or use the
dashboard's **Alarm & event audit** tab. Select a region, inspect probability and
magnetic measurements on a shared timeline, and explicitly reveal mapped peaks.
CSV downloads include region summaries, episodes and catalog coverage.

Durations use an explicit one-hour forecast-state convention. Region-hours sum
across regions. Event recall includes only uniquely mapped, forecast-covered
events; it is not a complete solar-event detection rate. Current data include ten
event/window label conflicts, detailed in the [results](docs/event-audit.md).

Investigate the association channels and timestamp conventions without changing
those results:

```sh
python scripts/investigate_event_provenance.py
```

Evidence stays under `artifacts/event_provenance/` and appears in the dashboard's
**Label provenance investigation** expander. The investigation preserves original
labels and explicitly distinguishes NOAA-based and location-based associations.
