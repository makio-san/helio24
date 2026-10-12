# Helio24

A research prototype for estimating whether a solar active region will produce
an M- or X-class flare within the next 24 hours.

## Current status

The first real-data experiment and local Streamlit dashboard are implemented.
The experiment uses a deterministic 10% sample from SWAN-SF partitions 1, 3,
and 5. It is a development evaluation, not a full-dataset benchmark.

See [the first experiment](docs/first-experiment.md) for measured results and
[the data contract](docs/data-contract.md) for label semantics and leakage controls.

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

The probabilities are raw model estimates. Additional probability calibration,
group-aware uncertainty intervals, a full-data experiment, and temporal models
remain future work. The test set is now inspected; future changes must not be
presented as another untouched evaluation on the same test records.

The first version uses historical data. Flare probability does not estimate
damage to a satellite or the impact on Earth.
