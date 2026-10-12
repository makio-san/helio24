# Helio24

A research prototype for estimating whether a solar active region will produce
an M- or X-class flare within the next 24 hours.

## Current status

Initial setup and a SWAN-SF download script are available. Data acquisition is
incomplete. Model training, evaluation, and the replay dashboard are not yet implemented.

## Setup

Requires Python 3.11 or newer and `curl`.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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

Datasets, local environments, generated outputs, and credentials are excluded
from Git. Downloaded data is not redistributed in this repository.

## Planned evaluation

- Verify label windows before training.
- Use chronological partitions and check overlap between regions and windows.
- Compare a constant baseline, logistic regression, and XGBoost.
- Select alarm thresholds on validation data only.
- Report recall, precision, false alarms, and probability calibration.

The first version uses historical data. Flare probability does not estimate
damage to a satellite or the impact on Earth.
