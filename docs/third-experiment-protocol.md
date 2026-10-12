# Experiment 3: temporal discrimination

This protocol is fixed before temporal features are generated or their model
results are inspected. Experiment 2 remains unchanged. Partition 5 has already
been inspected and cannot be presented as an untouched test.

## Question

Does recent magnetic evolution improve M/X-flare discrimination over the
existing 12-hour summary features, especially by reducing false alarms at the
same empirical recall?

For every magnetic parameter, retain the existing 12-hour mean, population
standard deviation, last value and endpoint change. Add the following summaries
over the final 1, 3 and 6 hours of the observation window:

- ordinary least-squares slope per hour, using trusted finite samples;
- change between the first and last trusted finite samples in the interval;
- population standard deviation of consecutive trusted-sample changes.

The intervals contain 5, 15 and 30 measurements at the dataset's 12-minute
cadence. A slope or change needs at least two trusted values. Change volatility
needs at least two finite consecutive differences. Otherwise the feature is
missing and is imputed from training data. All values end at the forecast time;
no outcome, flare-catalog or future measurement enters a feature.

## Walk-forward comparison

Use three chronological development folds:

| Fold | Training partitions | Evaluation partition |
| --- | --- | --- |
| A | 1 | 2 |
| B | 1, 2 | 3 |
| C | 1, 2, 3 | 4 |

Before each fold, remove training windows whose 24-hour prediction interval
reaches the evaluation observations. Remove evaluation HARP identities already
present in training, and report every removal. Fit two XGBoost pipelines with
identical fixed experiment-2 settings and training records. The control uses
only the 96 existing features; the candidate adds the 216 temporal features.
Median imputation is fitted separately inside each training pipeline. There is
no hyperparameter search and no probability calibration in this comparison.

Within each evaluation fold, report average precision and Brier score. At 80%,
90% and 95% empirical recall, select the threshold that yields the fewest false
alarms and report recall, precision, false-positive rate, false-alarm ratio and
counts. These thresholds measure ranking trade-offs on development data; they
are not deployable thresholds or estimates of future operating performance.

The candidate is considered promising only if, at the 90% recall target, it has
fewer false alarms in at least two of three folds and fewer false alarms after
summing all folds, while its average precision is no lower in at least two of
three folds. This rule controls the next modeling decision; it does not create a
new final-test claim.

After all development results and the decision are saved, refit each model on
partitions 1–4 and apply the fold-C 90%-recall thresholds to partition 5 as a
descriptive stability check. Do not use partition 5 to choose features,
hyperparameters, thresholds or the winning model. Clearly label this period as
previously inspected.

## Error audit

Use the experiment-2 full calibrated model and its frozen 90%-recall threshold
to describe validation-partition errors before interpreting temporal-model
results. Report hit, miss, false-alarm and correct-quiet counts by calendar
quarter and measurement-missingness band, including denominators and rates.
Also report how errors are concentrated across HARP regions. This is an
exploratory audit, not an independent hypothesis test.

Stream verified compressed archives into bounded Parquet batches. Do not expand
the archives. Record archive checksums, feature-table hashes, source-code hashes,
package versions, split removals and the protocol hash. Store generated data,
models and reports only in the ignored `data/` and `artifacts/` directories.
