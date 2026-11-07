# Threshold versus persistence protocol: frozen before any result

## Decision and scope

The [persistence results](alarm-persistence-results-20261107.md) showed that requiring 3 or 6 consecutive
exceedances removes false alarms but costs more window recall than the frozen limit of 0.02. They did not
compare persistence with simply raising the alarm threshold, which also trades recall for fewer false alarms.
This protocol freezes that comparison on the same frozen annual predictions and thresholds (source report
SHA256 `e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`; persistence report SHA256
`242b78592fb9c64d1a20809be5179874783bde54a7bc4731fc960fa43841f175`). It was written before any threshold
result was computed. Nothing has been run. No training, relabeling or access to the reserved 2024–2025 test
is part of it.

Disclosure: the persistence results were already known. The three multipliers were chosen after seeing them,
to span a range of false-alarm reductions comparable to or larger than persistence. They were not tuned on
any threshold result.

## Question

Is persistence a better precision and recall trade than simply raising the threshold? Two readings are
needed: what a fixed threshold rule achieves without using labels, and what the best possible threshold would
achieve at the same recall as persistence.

## Deployable candidates

An alarm is issued when the probability is at least a multiplier m times the unchanged frozen annual threshold,
capped at 1. No labels or outcomes set m. The multipliers are 1.25, 1.5 and 2.0; no other value is allowed.
Each is judged by the per-year conditions of the persistence protocol against the unchanged control: higher
episode precision, fewer false-alarm windows, no fewer alarmed positive runs, and a window recall drop of at
most 0.02. A multiplier passes only if all six positive years hold. Differences against the control carry
paired full-HARP bootstrap intervals (1000 draws, seed 24), conditional on frozen predictions and thresholds,
without a multiple-comparison correction.

## Oracle references

Thresholds in this section are chosen using the evaluation labels. They are diagnostic references, not
deployable rules; they have no uncertainty interval and cannot be adopted. The grid is the set of distinct
probabilities of the year's evaluation windows, with alarm at probability at or above t.

- Matched recall: for each persistence candidate and year, the largest t whose window recall is at least the
  persistence recall. The achieved recall is reported, and ties favour the threshold.
- Tolerance reference: the largest t whose window recall is at least the control recall minus 0.02. It shows how
  much false-alarm reduction fits inside the frozen recall tolerance.

For each reference the report gives t, recall, precision, false-alarm windows, episodes, hit episodes, episode
precision and alarmed positive runs.

## Candidates and budget

| candidate | rule | budget |
| --- | --- | --- |
| mult_1.25 | threshold times 1.25 | 1 |
| mult_1.5 | threshold times 1.5 | 1 |
| mult_2.0 | threshold times 2.0 | 1 |
| matched_3h | oracle threshold matching persist_3h recall | 0 |
| matched_6h | oracle threshold matching persist_6h recall | 0 |
| tolerance_ref | oracle threshold at control recall minus 0.02 | 0 |

Primary arm is `baseline`; `chronological` is a secondary descriptive arm. Years are 2014, 2015, 2016, 2017,
2018, 2022 and 2023. The six years with positive windows are gated. 2018 reports false-alarm windows and episodes
for deployable candidates only, because recall-based rules are undefined there. Model fits: 0.

## Verdict rules

For the same k, persistence adds value only if in all six positive years it has fewer false-alarm windows and
fewer episodes than the matched-recall threshold. The threshold is at least as good if in all six positive years
its false-alarm windows are less than or equal to persistence. Anything else is mixed and is reported as
per-year wins and losses without a single verdict. No verdict changes alerts, thresholds or models.

## Interpretation limits

The result is adaptive development evidence on already inspected years, not an independent test. Counts are
overlapping forecast windows and groupings of them, not physical flares. The oracle references use the
evaluation labels and therefore favour the threshold; a threshold win there does not say that a threshold can be
chosen in advance. A deployable multiplier passing would only justify a separate prospective protocol. AP, Brier
and log loss are unchanged by both families of rules.

## Next step and reproduction

After review, add `scripts/audit_threshold_tradeoff.py` with tests, run it once into a new output directory and
report the result in both languages. The frozen config is not edited afterwards; a revision needs a new version.
The frozen file can be inspected with:

```sh
cat config/threshold-tradeoff-v1.json
```
