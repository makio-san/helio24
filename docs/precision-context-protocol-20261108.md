# Precision context protocol: causal regional trajectory as a second stage, frozen before any result

## Decision and scope

Window precision of the frozen baseline stays near 0.10 at the recall target, and the project target is
0.30 at recall 0.95. This protocol freezes one bounded experiment that adds causal, catalog-free regional
context to the frozen baseline ensemble as a small second stage. It was written before any candidate result
was computed. Nothing has been run. No stage-one model is refitted, no label changes and the reserved
2024–2025 test stays closed. One step is not expected to reach the target; the protocol measures the distance.

Evidence: frozen annual predictions and thresholds (source report SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`), the baseline walk-forward report
(SHA256 `6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c`) and the frozen shard report
(SHA256 `62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82`), all verified by the
[v2 baseline gate](threshold-selection-v2-results-20261108.md).

## Why this experiment

In the frozen baseline predictions most false-alarm windows fall inside HARPs that have no positive window in
that year, and a few regions that stay alarmed for long carry a large share of them.

| year | FP windows | FP in zero-positive HARPs | share | FP in the ten worst HARPs |
| --- | --- | --- | --- | --- |
| 2014 | 13886 | 7646 | 55% | 2729 |
| 2015 | 11453 | 7607 | 66% | 2696 |
| 2016 | 2289 | 1642 | 72% | 1478 |
| 2017 | 1287 | 998 | 78% | 1198 |
| 2022 | 10072 | 8510 | 84% | 2430 |
| 2023 | 5992 | 4576 | 76% | 1836 |

The [research direction](research-next-20261106.md) selected causal flare-history context for the same
hypothesis, that persistently high measurements can be told from regions approaching a flare, but its stop
rule forbids training until publication-time provenance is established, and the
[publication probe](history-publication-probe-20261107.md) left `availability_verified=false`. This protocol
tests the hypothesis through context that needs no external catalog: the region's own past stage-one
probabilities and its age in the record. Fixed alarm persistence, threshold multipliers, prior-year recall
targets, raw-history summaries, weighting, pooling, splines, Extra Trees and histogram boosting were tested
earlier and did not pass.

## Stage one and context features

Stage one is the stored frozen annual ensemble, inference only, with zero fits. Its calibration-year and
evaluation-year probabilities are out of sample for stage one. Context features use only windows of the same
HARP with a forecast time strictly before the current one, in the same annual-fold role, plus the current
window. No labels, events, future windows or other HARPs are used.

| feature | definition |
| --- | --- |
| logit_p | logit of the current stage-one probability |
| age_log_hours | log(1 + hours since the first window of this HARP in the record) |
| past24_max_logit, past24_mean_logit | over windows in (t−24h, t) |
| past72_max_logit, past72_mean_logit | over windows in (t−72h, t) |
| past72_hours_above_control | windows in (t−72h, t) at or above the frozen control threshold of that year |
| slope6 | logit_p minus the mean logit over (t−6h, t) |
| coverage24, coverage72 | number of past windows found in each lookback |
| missing_fraction | of the current window |

A lookback with no past window gives coverage 0 and past statistics equal to the current logit. The coverage
features carry the information that history is absent; history is never assumed quiet.

## Candidates and stage two

| candidate | definition | budget |
| --- | --- | --- |
| control | stage-one probability with the frozen prior-year threshold; identical to the baseline arm | 0 |
| recal | stage two on logit_p and missing_fraction only | 1 |
| context | stage two on all context features | 1 |

Stage two is a StandardScaler followed by LogisticRegression with C 1.0, lbfgs, 2000 iterations, no class
weight and seed 24, with no search. It is fitted on the calibration year of the annual fold only; the training
years are in sample for stage one and are not used. Five HARP-group folds on the calibration year (fold = rank of
the HARP id among sorted calibration HARPs modulo 5) give every calibration window a cross-fitted stage-two
probability. The threshold is selected on these cross-fitted probabilities with `recall_threshold` at target
0.95. The stage-two model refitted on the whole calibration year is applied to the evaluation year. Fits: 7
years × 2 candidates × 6 = 84 small logistic fits. For every year the thresholds of all candidates are written
to disk and hashed before any evaluation label is read.

The `recal` candidate exists to make one difference visible: stage two uses calibration-year labels to fit,
where the control uses them only to select a threshold. A pass of `context` that `recal` does not share is
attributed to trajectory information; a pass shared by both is attributed to refitting, not to context.

## Acceptance rules

A candidate counts in a year if it satisfies all four conditions against the control, with the same definitions
as the persistence protocol: higher episode precision, fewer false-alarm windows, no fewer alarmed positive
runs, and a window recall drop of at most 0.02. An all-year pass needs all six positive years for the same
candidate. 2018 has no positive windows and reports thresholds, false-alarm windows and episodes only. For
every year the report gives the window precision and the number of false-alarm windows that would give
precision 0.30 at the achieved true positives. These are project comparison rules, not universal ranges. A
pass justifies only a separate prospective protocol and never changes alerts, thresholds or models.

## Reported metrics and uncertainty

Per year and candidate: tp, fp, fn, tn, precision, recall, alarm windows, episodes, episode precision, positive
runs, alarmed positive runs, average precision, Brier and log loss. Paired full-HARP bootstrap intervals (1000
draws, seed 24) for episode precision and false-alarm window differences against the control are conditional
on the frozen thresholds. They do not include the uncertainty of stage-two fitting or threshold selection and
are not corrected for multiple comparisons.

## Disclosure and limits

The context features were chosen after seeing where false alarms concentrate in the frozen baseline predictions
of the same years, which is adaptive. They were not chosen on any stage-two result; none had been computed when
the configuration was frozen. The result is adaptive development evidence on already inspected years, not an
independent test. Counts are overlapping forecast windows and groupings of them, not physical flares. The
calibration year has few positive windows in some folds (181 for 2017), so stage two may be noisy there.

## Next step and reproduction

After review, add `scripts/audit_precision_context.py` with tests, run it once into a new output directory and
report the result in both languages. The frozen configuration is not edited afterwards; a revision needs a new
version. The frozen file can be inspected with:

```sh
cat config/precision-context-v1.json
```
