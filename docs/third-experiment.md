# Experiment 3: temporal discrimination results

The fixed temporal-feature candidate did not pass the preregistered development
rule. It reduced false alarms in two of three walk-forward folds at 90% empirical
recall, but average precision decreased in all three folds. The dashboard model
was not replaced.

## Data and design

All five temporal tables matched the existing full-data tables one-to-one, for
328,901 accepted forecast windows. Each of the 24 magnetic parameters gained
slopes, changes and consecutive-change standard deviations over the final 1, 3
and 6 hours, adding 216 features to the 96-feature control. Every feature ended
before the forecast time.

The [protocol](third-experiment-protocol.md) was committed before the feature
tables or results were generated. The development comparison used these folds:

| Fold | Training partitions | Evaluation | Training windows | Evaluation windows |
| --- | --- | --- | ---: | ---: |
| A | 1 | 2 | 72,613 | 86,546 |
| B | 1–2 | 3 | 159,247 | 42,452 |
| C | 1–3 | 4 | 201,485 | 51,160 |

Prediction intervals crossing a fold boundary removed 856, 768 and 982 training
windows respectively. No HARP identities crossed the cleaned boundaries. Both
models used the same records and fixed experiment-2 XGBoost settings. Only the
candidate received the new temporal features.

## Development comparison

At each fold's 90% empirical recall point:

| Fold | Model | Recall | Precision | False alarms | Misses | Average precision | Brier |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | Control | 90.01% | 11.18% | 10,021 | 140 | 0.3424 | 0.01283 |
| A | Temporal | 90.01% | 11.95% | 9,288 | 140 | 0.3390 | 0.01300 |
| B | Control | 90.03% | 23.70% | 4,128 | 142 | 0.4788 | 0.02323 |
| B | Temporal | 90.03% | 23.86% | 4,090 | 142 | 0.4763 | 0.02314 |
| C | Control | 90.04% | 19.57% | 4,311 | 116 | 0.5237 | 0.01501 |
| C | Temporal | 90.04% | 18.90% | 4,502 | 116 | 0.5121 | 0.01529 |

The temporal model produced 17,880 pooled false alarms versus 18,460 for the
control, a reduction of 580 (3.14%). It reduced false alarms in folds A and B but
added 191 in fold C. Average precision was lower in A, B and C. The fixed rule
required fewer pooled false alarms, fold-level false-alarm wins in at least two
folds, and non-lower average precision in at least two folds. The candidate
failed the last condition and is therefore not promoted.

The result is narrower than “time-series information is not useful.” It shows
that this fixed, unselected set of 216 recent summaries does not improve ranking
consistently enough to justify replacing the simpler feature set.

## Error audit

The experiment-2 calibrated model was audited on its partition-4 validation
records at the frozen 4.7999% threshold. Among 50,631 windows it produced 969
hits, 107 misses, 4,264 false alarms and 45,291 correct quiet forecasts.

Errors were concentrated by active region: the ten HARPs with the most errors
contained 36.01% of all misses and false alarms. Calendar behavior also varied.
The false-positive rate was highest in 2014 Q3 at 12.24%; the miss rate was
45.61% in the small 2014 Q2 positive sample (26 misses among 57 positives), then
7.05%–11.96% in the remaining quarters. These are descriptive rates with very
different denominators, not evidence of a causal seasonal effect.

Every validation window had more than 1% masked measurements under the existing
quality definition. Windows with over 5% masked measurements had a 14.67% miss
rate, compared with 8.12% for the 1%–5% group. False-positive rates were similar
(8.73% versus 8.55%). Missingness may coincide with harder regions or periods;
this audit does not establish that it causes misses.

## Previously inspected stability check

After the development verdict was written, both models were refit on partitions
1–4 and evaluated with their fold-C thresholds on partition 5:

| Model | Recall | Precision | False alarms | Misses | Average precision | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Control | 89.80% | 18.00% | 4,050 | 101 | 0.4716 | 0.00912 |
| Temporal | 91.82% | 17.59% | 4,258 | 81 | 0.4905 | 0.00898 |

Partition 5 was already inspected in earlier experiments, so this is a
retrospective stability description, not an untouched test. The fixed thresholds
also yielded different recall, so the false-alarm counts are not a matched-recall
comparison. The favorable average precision does not override the development
verdict.

## Reproduction and next decision

Commands are listed in the [README](../README.md#experiment-3-temporal-discrimination).
The ignored `artifacts/experiment3/report.html` contains the complete local
report. Machine-readable outputs include all recall targets, predictions, split
removals, error tables, model artifacts, source hashes, archive checksums,
package versions and the protocol hash.

The next experiment should begin from the region-level error concentration. A
useful next step is to measure persistence and event-level grouping of repeated
window alarms, then test a smaller, justified temporal feature set or a sequence
model under a new fixed walk-forward protocol. A genuinely final performance
claim still requires later data that has not influenced development.
