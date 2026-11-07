# Threshold selection protocol: frozen before any result

## Decision and scope

The [threshold versus persistence results](threshold-tradeoff-results-20261107.md) showed that an oracle
threshold has large false-alarm headroom inside the frozen recall tolerance, but that fixed multipliers of the
frozen threshold break recall in 2016 and 2023. The open problem is choosing such a threshold without
evaluation labels. This protocol freezes four selection rules that use only the prior-year calibration windows.
It was written before any selection-rule result was computed. Nothing has been run. No training,
recalibration, relabeling or access to the reserved 2024–2025 test is part of it.

Evidence: frozen annual predictions and thresholds (source report SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`), the threshold tradeoff report (SHA256
`e0cf54967cf89e68865ee13843b24383f5d1fa2106ab33a574ba3cfdd351f14c`) and the baseline walk-forward report
(SHA256 `6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c`).

Disclosure: the targets 0.93 and 0.90 and the run-level basis were chosen after seeing the tradeoff results.
They were not tuned on any selection-rule result.

## Question

Can a threshold chosen from the prior-year calibration windows alone, with a rule fixed in advance, reach a
better precision and recall trade than the existing window-recall rule at 0.95, without exceeding the frozen
recall tolerance of 0.02?

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

Window rules use the existing `recall_threshold` function on calibrated calibration probabilities. Run rules use
the same grid and tie order: among the distinct calibrated calibration probabilities whose positive-run recall
is at or above the target, take the fewest calibration false-alarm windows, then the larger threshold. A
positive run is a sequence of consecutive-hour positive-labelled windows of one HARP and counts as alarmed when
any of its windows is at or above the threshold. The control must reproduce the stored thresholds exactly.
No other target, basis, multiplier, persistence or combined rule is allowed after seeing results. Model fits: 0.

## Arms and feasibility gate

The primary arm is `baseline`. Its calibration probabilities are not stored, so they are recomputed by
inference with the stored frozen models and must reproduce the stored baseline threshold under `control_w95`
in every year. If any year fails, the baseline arm is excluded and reported as not evaluable, and
`chronological` becomes the primary arm. No retraining is allowed. The `chronological` and `shuffled_interior`
arms use the stored per-seed calibration scores and calibrators, and must also reproduce their stored
thresholds. Years: 2014, 2015, 2016, 2017, 2018, 2022 and 2023. The six years with positive windows are gated;
2018 reports thresholds, false-alarm windows and episodes only.

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

## Interpretation limits

The result is adaptive development evidence on already inspected years, not an independent test. Counts are
overlapping forecast windows and groupings of them, not physical flares. Calibration years contain few positive
runs in some cases, so the selected thresholds may be noisy; a failure would show that a prior-year recall target
is an unreliable guide in this record, not that no better threshold exists.

## Next step and reproduction

After review, add `scripts/audit_threshold_selection.py` with tests, run it once into a new output directory and
report the result in both languages. The frozen config is not edited afterwards; a revision needs a new version.
The frozen file can be inspected with:

```sh
cat config/threshold-selection-v1.json
```
