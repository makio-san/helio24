# Alarm persistence protocol: frozen before any result

## Decision and scope

The alarm episode audit showed that false alarms arrive as many short, all-negative
episodes, with median length of 2 to 7 hours ([audit](alarm-episodes-20261107.md)).
The flare-history direction remains blocked because historical event reports were created
days after the events ([timing probe](history-publication-probe-20261107.md)). This protocol
therefore freezes one cheap, training-free hypothesis: require several consecutive
threshold exceedances before issuing an alarm. This document and
`config/alarm-persistence-v1.json` were written before any persistence result was computed.
Nothing has been run. No training, threshold change, relabeling or access to the reserved
2024–2025 test is part of this protocol.

Disclosure: the two candidate values were chosen after seeing the descriptive median
all-negative episode lengths. They were not tuned on any persistence outcome.

## Hypothesis

Requiring k consecutive threshold exceedances removes short all-negative episodes and raises
episode and window precision without losing positive runs. This is unproven. The rule can lower
recall and delays every alarm by at least k minus one hours. Alert suppression is not model
improvement and does not change probabilities.

## Rule

An alarm is issued at hour t of one HARP only if the windows t−k+1 to t are exactly one hour
apart and all have probability at or above the unchanged frozen annual threshold. Only the
current and past windows are used, so the rule is causal. The control k=1 is the existing
behaviour. Episodes, hit episodes, positive runs and alarmed positive runs keep the definitions of
the alarm episode audit. A hit episode contains a positive-labelled window; these are groupings of
overlapping windows, not physical flares.

## Candidates, data and budget

| candidate | k | budget |
| --- | --- | --- |
| control | 1 | 0 |
| persist_3h | 3 | 1 |
| persist_6h | 6 | 1 |

Primary arm is `baseline`, the frozen 96-feature ensemble; `chronological` is reported as a
secondary descriptive arm. The evidence is the frozen annual predictions and thresholds of the
completed seven-year comparison (report SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`) and the episode audit
(SHA256 `9d6b5c02d370f0b08ecc0dc3083d2df88d65a39469907077192666b143306788`). Years: 2014, 2015,
2016, 2017, 2018, 2022 and 2023. The six years with positive windows are gated; 2018 reports
episodes and false alarms only. No other k value, cooldown, merging or hysteresis is allowed
after seeing results. Model fits: 0. Threshold changes: 0.

## Reported measures

Per year, arm and candidate: tp, fp, fn, tn, recall, precision, alarm windows, episodes, hit
episodes, episode precision, all-negative episodes, positive runs, alarmed positive runs,
positive-run recall, and the median and maximum alarm delay. Alarm delay is the hours from the
first positive-labelled window of an alarmed positive run to the first alarm window inside it.
It is reported, not gated.

## Acceptance rules

| rule | required value |
| --- | --- |
| episode precision versus control | higher |
| fp windows versus control | lower |
| alarmed positive runs versus control | not below |
| window recall drop versus control | at most 0.02 |
| positive years that must pass for the same k | 6 |

These are project comparison rules, not universal ranges. An all-year pass requires every
positive year for the same k. AP, Brier and log loss are unchanged by this rule and are not
claimed as improvements. Some years, such as 2017 and 2023, may fail because the control already
misses positive runs.

## Uncertainty

Per-year and pooled counts are reported. Differences against the control in episode precision and
fp windows use 1000 paired full-HARP bootstrap draws with seed 24. Intervals are conditional on
frozen predictions and thresholds, ignore retraining uncertainty and are not corrected for
multiple comparisons.

## Interpretation limits

The result is adaptive development evidence on already inspected years, not an independent
test. A pass would only justify a separate prospective protocol; it would never change alerts or
models automatically. A failure is also informative: it would show that short episodes are not a
removable part of the alarm burden. Delayed alarms may cost warning time that this window-level
audit cannot value.

## Next step and reproduction

After review of this protocol, add a script `scripts/audit_alarm_persistence.py` with tests, run it
once into a new output directory and report the result in both languages. Do not edit the
frozen config afterwards; a revision needs a new config version. The frozen file can be inspected with:

```sh
cat config/alarm-persistence-v1.json
```
