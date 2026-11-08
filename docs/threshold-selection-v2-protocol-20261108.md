# Threshold selection protocol v2: baseline arm, frozen before any result

## Decision and scope

The [threshold selection results](threshold-selection-results-20261108.md) could not evaluate the baseline arm,
because all 20 frozen development feature shards were missing. The shards have since been regenerated from the
verified official archives, and all 20 matched their frozen SHA256 values. This protocol adds a new version for
the baseline arm only. Version 1 stays frozen and its reported results are unchanged. This file was written
before any baseline selection-rule result was computed. Nothing has been run. No training, recalibration,
relabeling or access to the reserved 2024–2025 test is part of it.

Evidence: frozen annual predictions and thresholds (source report SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`), the version 1 results report (SHA256
`dae49d81c516a8a3bc512ccf5ef10081cc252fa162b8d0274fba97e4ff54a6b1`), the baseline walk-forward report (SHA256
`6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c`), the frozen shard report (SHA256
`62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82`) and the regenerated shard report
(SHA256 `36e8484a1496f6f1d7e117143766bfa9a15c306f4ac3984be4de321d2b5f7086`).

## Question

With the shards restored and verified, does the baseline arm pass the feasibility gate? If it does, can a
threshold chosen from the prior-year calibration windows alone, with the rules fixed in version 1, reach a better
precision and recall trade than the existing window-recall rule at 0.95, without exceeding the frozen recall
tolerance of 0.02?

## Arm definition

The baseline arm is the original 96-summary-feature ensemble, stored as `ensemble` in each year of the
walk-forward artifact: calibrated logistic and XGBoost probabilities combined with the stored ensemble weight.
It is not the walk-forward `baseline` candidate, which is the training prevalence constant. The chronological
and shuffled_interior arms are not recomputed. Their version 1 results were already seen and stay as reported.

## Data rule

Each rule sees only the calibration windows of the year before the evaluation year, which is the calibration
role of the original annual fold, and their labels. Earlier years were training data of the same models and are
in-sample, so they are not used. The evaluation windows and labels are not read until the thresholds of every
rule are written to disk and hashed. No selection rule uses evaluation labels or outcomes.

## Rules and budget

| rule | basis | target | budget |
| --- | --- | --- | --- |
| control_w95 | window recall | 0.95 | 0 |
| w93 | window recall | 0.93 | 1 |
| w90 | window recall | 0.90 | 1 |
| run95 | positive-run recall | 0.95 | 1 |
| run90 | positive-run recall | 0.90 | 1 |

The rules, targets and selection procedure are identical to version 1. Window rules use the existing
`recall_threshold` function on calibrated calibration probabilities. Run rules take, among the distinct
calibrated calibration probabilities whose positive-run recall is at or above the target, the fewest calibration
false-alarm windows, then the larger threshold. A positive run is a sequence of consecutive-hour
positive-labelled windows of one HARP and counts as alarmed when any of its windows is at or above the
threshold. No other target, basis, multiplier, persistence or combined rule is allowed after seeing results.
Model fits: 0.

## Feasibility gate

The gate has four steps and is computed and written to disk before any selection rule is evaluated.

| step | check |
| --- | --- |
| G1 | Every regenerated shard hash equals its frozen SHA256. All 20 are required. |
| G2 | The stored `models.joblib` of each evaluated year matches its SHA256 in the frozen walk-forward report. |
| G3 | Calibration probabilities recomputed by inference give, under `control_w95`, a threshold equal to the stored baseline threshold in every year (relative tolerance 1e-12). |
| G4 | Label-free identity check: recomputed evaluation probabilities equal the `baseline` column of the frozen predictions on the key (harp, forecast_time), with identical key sets and a maximum absolute difference of at most 1e-6. |

If any step fails in any year, the baseline arm is reported as not evaluable with the failing step and year, and
no selection rule is evaluated for it. There is no fallback to another candidate model, no retraining, no
recalibration and no rule change. Years: 2014, 2015, 2016, 2017, 2018, 2022 and 2023. The six years with
positive windows are gated; 2018 reports thresholds, false-alarm windows and episodes only.

## Acceptance rules

A rule counts in a year if it satisfies all four conditions against the control, with the same definitions as the
persistence protocol: higher episode precision, fewer false-alarm windows, no fewer alarmed positive runs, and a
window recall drop of at most 0.02. An all-year pass needs all six positive years for the same rule. These are
project comparison rules, not universal ranges. A pass justifies only a separate prospective protocol and never
changes alerts, thresholds or models. AP, Brier and log loss are unchanged by threshold choice.

## Stability reporting

For each rule and year the report gives the number of calibration positive windows and positive runs, the
selected threshold, its ratio to the control threshold, the calibration recall, the evaluation recall and their
difference. The difference shows how well the calibration year predicts the evaluation year.

## Uncertainty

Paired full-HARP bootstrap intervals (1000 draws, seed 24) for episode precision and false-alarm window
differences against the control are conditional on the frozen selected thresholds. They do not include the
uncertainty of the threshold selection itself, nor retraining uncertainty, and are not corrected for multiple
comparisons.

## Disclosure

The rules, targets and acceptance conditions are identical to version 1 and are not tuned for the baseline arm.
They were chosen after the threshold tradeoff results, and none of the four rules passed for the chronological
and shuffled_interior arms in version 1. This is known before this protocol and is a reason to expect a negative
result, not evidence of tuning. No baseline selection-rule result had been computed when this file was frozen.
The regenerated shard report differs from the frozen shard report in its completion time, input paths and the
hash of `helio24/v2_archive.py`. The per-shard hashes, row counts, positive counts and HARP count are identical.

## Interpretation limits

The result is adaptive development evidence on already inspected years, not an independent test. Counts are
overlapping forecast windows and groupings of them, not physical flares. Calibration years contain few positive
runs in some cases, so the selected thresholds may be noisy; a failure would show that a prior-year recall target
is an unreliable guide in this record, not that no better threshold exists.

## Next step and reproduction

After review, add the baseline evaluation to `scripts/audit_threshold_selection.py` (or a new script) with tests,
run it once into a new output directory and report the result in both languages. The frozen config is not edited
afterwards; a revision needs a new version. The frozen file can be inspected with:

```sh
cat config/threshold-selection-v2.json
```
