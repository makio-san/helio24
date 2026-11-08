# Operating point decision: window recall target 0.90

## Decision

From 2026-11-09 the project operating point for the annual V2 baseline is a threshold selected on the prior
calibration year at window recall 0.90, applied unchanged to the next year. It replaces the development target
of precision 0.30 at window recall at least 0.95. The frozen definition is
[`config/operating-point-v2.json`](../config/operating-point-v2.json).

This is not a performance improvement. The model, its features and its probabilities are unchanged. The target
was aligned with what the data supports, and every report that states this operating point must say so.

## Why

The [operating point review](operating-point-review-20261109.md) showed that precision 0.30 at high recall is
not a property this model and data can deliver. Even the evaluation-year oracle, which is not deployable, needs
recall at or below 0.67 in 2014, 0.79 in 2015, 0.58 in 2016, 0.23 in 2022 and 0.25 in 2023; only 2017 reaches
0.30 at 0.90. Eight independent routes tried since 2026-11-07 (prior-year threshold rules, alarm persistence,
recalibration, probability trajectory, issued SRS context, weighting, model grids and the temporal convolution
model) left precision at the 0.95 target in the 0.04–0.16 band. Relaxing the target to 0.90 removes 1123 to
6253 false-alarm windows per year at the cost of 0 to 3 more missed flare episodes per year.

## Expected development performance at the new operating point

Observed on already inspected development years with prior-year thresholds. These are expectations for
reporting, not guarantees.

| year | precision | delivered recall | FP windows | missed positive runs | missed positive runs at 0.95 |
| --- | --- | --- | --- | --- | --- |
| 2014 | 0.2082 | 0.8688 | 7634 | 6 | 3 |
| 2015 | 0.1721 | 0.9653 | 6294 | 0 | 0 |
| 2016 | 0.1106 | 0.8950 | 1303 | 0 | 0 |
| 2017 | 0.1850 | 0.9289 | 1035 | 1 | 1 |
| 2022 | 0.0442 | 0.9834 | 8949 | 0 | 0 |
| 2023 | 0.1186 | 0.8361 | 4852 | 3 | 2 |

Delivered recall ranges from 0.836 to 0.983 because the calibration year and the evaluation year differ. 2022
stays the weakest year at every target.

## Scope and reporting rules

- Applies to development reporting and to future development protocols.
- The dashboard alert threshold and any deployed alert are not changed by this decision. Changing them needs a
  separate decision and the reserved 2024–2025 test, which stays closed.
- Reports state precision together with delivered recall and missed positive runs for every year, state that
  the target was redefined on 2026-11-09 and why, and keep the 0.95 results visible wherever earlier work is
  compared.

## Limits

The expectations above come from already inspected years and are adaptive development evidence, not an
independent test. Counts are overlapping forecast windows and groupings of them, not physical flares. The
frozen file can be inspected with:

```sh
cat config/operating-point-v2.json
```
