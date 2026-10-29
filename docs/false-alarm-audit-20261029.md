# False-alarm localization and next model selection

This audit compares frozen annual development predictions and selects a controlled
hard-negative-weighted XGBoost experiment. **The new model has not been trained and no
precision improvement is claimed.** Labels, forecasts, dashboard model and the reserved
2024–2025 test remain unchanged. The design is `config/hard-negative-v1.json`, explicitly
marked `design_frozen_not_executed`.

## Evidence and scope

Inputs are the completed 2014–2018, 2022 and 2023 folds of
`artifacts/walk_forward_20261028_r1`. Every registered artifact hash is checked, alarms
are reconstructed from each frozen calibration threshold, and ensemble FP totals must
match the original metrics. Years 2019–2021 have no completed fold because their preceding
calibration populations lack positive examples. In the retained 2018 evaluation population
there are no positives; false alarms remain measurable, but recall is undefined.

These are adaptive, retrospective development diagnostics, not independent validation of
a new model. Counts describe overlapping forecast windows, not independent solar flares,
notifications or spacecraft impacts. All proportions below use a 0–1 scale.

## Regional concentration, adjusted for exposure

| year | negatives | fp | fpr | top10_fp | top10_fp_share | top10_negative_share |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 72918 | 13886 | 0.190433 | 2729 | 0.196529 | 0.040923 |
| 2015 | 67783 | 11453 | 0.168966 | 2696 | 0.235397 | 0.042120 |
| 2016 | 42806 | 2289 | 0.053474 | 1478 | 0.645697 | 0.060763 |
| 2017 | 19276 | 1287 | 0.066767 | 1198 | 0.930847 | 0.123055 |
| 2018 | 7799 | 359 | 0.046032 | 358 | 0.997214 | 0.237338 |
| 2022 | 50335 | 10072 | 0.200099 | 2430 | 0.241263 | 0.052210 |
| 2023 | 59585 | 5992 | 0.100562 | 1836 | 0.306409 | 0.039238 |

`fpr` is FP divided by negative windows. The top ten HARPs are selected post hoc by FP
count within each year. Their FP share must be compared with their negative-window share,
not with a uniform-region assumption. In 2023 these regions account for 0.306409 of FP
but only 0.039238 of negative windows. In 2017 the corresponding shares are 0.930847 and
0.123055. Concentration is therefore not explained solely by those regions having more
observed negative windows. This does not identify a physical cause.

The three largest contributors per year are:

| year | harp | rows | positives | negatives | fp | fpr | mean_missing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 4851 | 300 | 0 | 300 | 291 | 0.970000 | 0.011481 |
| 2014 | 4000 | 337 | 24 | 313 | 290 | 0.926518 | 0.004014 |
| 2014 | 4296 | 321 | 0 | 321 | 284 | 0.884735 | 0.006557 |
| 2015 | 5039 | 330 | 0 | 330 | 326 | 0.987879 | 0.002635 |
| 2015 | 6178 | 300 | 0 | 300 | 296 | 0.986667 | 0.009708 |
| 2015 | 6027 | 291 | 0 | 291 | 287 | 0.986254 | 0.003866 |
| 2016 | 6558 | 309 | 0 | 309 | 267 | 0.864078 | 0.005753 |
| 2016 | 6483 | 290 | 24 | 266 | 257 | 0.966165 | 0.004701 |
| 2016 | 6327 | 320 | 87 | 233 | 210 | 0.901288 | 0.004622 |
| 2017 | 6975 | 278 | 0 | 278 | 240 | 0.863309 | 0.004701 |
| 2017 | 7075 | 279 | 43 | 236 | 225 | 0.953390 | 0.005376 |
| 2017 | 7107 | 264 | 0 | 264 | 213 | 0.806818 | 0.067030 |
| 2018 | 7237 | 295 | 0 | 295 | 177 | 0.600000 | 0.049675 |
| 2018 | 7275 | 183 | 0 | 183 | 105 | 0.573770 | 0.001184 |
| 2018 | 7269 | 301 | 0 | 301 | 31 | 0.102990 | 0.002224 |
| 2022 | 8737 | 299 | 0 | 299 | 284 | 0.949833 | 0.002174 |
| 2022 | 8724 | 307 | 0 | 307 | 276 | 0.899023 | 0.002242 |
| 2022 | 8844 | 265 | 0 | 265 | 265 | 1.000000 | 0.009670 |
| 2023 | 9250 | 263 | 0 | 263 | 242 | 0.920152 | 0.004188 |
| 2023 | 10413 | 278 | 0 | 278 | 229 | 0.823741 | 0.003864 |
| 2023 | 10430 | 228 | 0 | 228 | 216 | 0.947368 | 0.004389 |

These are post-hoc diagnostic priorities, never a region exclusion list. Different HARP
identifiers across years are different catalogued regions; the recurring finding is
concentration, not proof that one physical region repeats across years.

## Missing measurements

| missing_bin | rows | negatives | fp | positives | fpr | year |
| --- | --- | --- | --- | --- | --- | --- |
| zero | 55626 | 54389 | 9453 | 1237 | 0.173804 | 2014 |
| (0,0.01] | 3214 | 2758 | 1827 | 456 | 0.662437 | 2014 |
| (0.01,0.05] | 9266 | 8852 | 1575 | 414 | 0.177926 | 2014 |
| (0.05,1] | 7122 | 6919 | 1031 | 203 | 0.149010 | 2014 |
| zero | 52029 | 51224 | 7993 | 805 | 0.156040 | 2015 |
| (0,0.01] | 3351 | 3093 | 1763 | 258 | 0.569997 | 2015 |
| (0.01,0.05] | 6505 | 6375 | 967 | 130 | 0.151686 | 2015 |
| (0.05,1] | 7253 | 7091 | 730 | 162 | 0.102947 | 2015 |
| zero | 32362 | 32227 | 1609 | 135 | 0.049927 | 2016 |
| (0,0.01] | 1699 | 1653 | 256 | 46 | 0.154870 | 2016 |
| (0.01,0.05] | 4056 | 4056 | 189 | 0 | 0.046598 | 2016 |
| (0.05,1] | 4870 | 4870 | 235 | 0 | 0.048255 | 2016 |
| zero | 14970 | 14827 | 823 | 143 | 0.055507 | 2017 |
| (0,0.01] | 644 | 633 | 111 | 11 | 0.175355 | 2017 |
| (0.01,0.05] | 1654 | 1633 | 114 | 21 | 0.069810 | 2017 |
| (0.05,1] | 2261 | 2183 | 239 | 78 | 0.109482 | 2017 |
| zero | 5799 | 5799 | 229 | 0 | 0.039490 | 2018 |
| (0,0.01] | 215 | 215 | 56 | 0 | 0.260465 | 2018 |
| (0.01,0.05] | 755 | 755 | 31 | 0 | 0.041060 | 2018 |
| (0.05,1] | 1030 | 1030 | 43 | 0 | 0.041748 | 2018 |
| zero | 36828 | 36605 | 6411 | 223 | 0.175140 | 2022 |
| (0,0.01] | 3499 | 3351 | 2102 | 148 | 0.627275 | 2022 |
| (0.01,0.05] | 4512 | 4491 | 814 | 21 | 0.181251 | 2022 |
| (0.05,1] | 5917 | 5888 | 745 | 29 | 0.126529 | 2022 |
| zero | 44871 | 44332 | 3708 | 539 | 0.083642 | 2023 |
| (0,0.01] | 4003 | 3891 | 1442 | 112 | 0.370599 | 2023 |
| (0.01,0.05] | 5197 | 5161 | 375 | 36 | 0.072660 | 2023 |
| (0.05,1] | 6295 | 6201 | 467 | 94 | 0.075310 | 2023 |

Missingness bins were fixed before this comparison: exactly zero, (0,0.01], (0.01,0.05]
and (0.05,1]. `missing_fraction` measures missing entries in the original observation
window; it is not a complete instrument-quality flag. Compare each bin's FP with its
negative denominator. In every completed year the (0,0.01] bin has the highest observed
FPR, but the pattern is not a monotonic increase with missingness. In 2023 it is 0.370599
versus 0.083642 for zero missingness. Region composition, measurement timing and label
selection may confound this association; this audit does not establish causation.

Moreover, most FP windows in every year have zero missingness. In 2023, 3708 of 5992 FP
windows have no missing entries. Improving imputation alone is therefore not established
as the main solution. Do not drop the small-missingness bin to manufacture better scores.

## Persistence and model agreement

| year | zero_positive_region_fp | complete_measurement_fp | both_models_alarm_fp | fp_windows_in_runs_ge6 | max_fp_run_windows |
| --- | --- | --- | --- | --- | --- |
| 2014 | 7646 | 9453 | 11798 | 13190 | 263 |
| 2015 | 7607 | 7993 | 9728 | 10793 | 325 |
| 2016 | 1642 | 1609 | 1470 | 2041 | 140 |
| 2017 | 998 | 823 | 1064 | 1184 | 178 |
| 2018 | 359 | 229 | 245 | 306 | 129 |
| 2022 | 8510 | 6411 | 8228 | 9429 | 258 |
| 2023 | 4576 | 3708 | 5600 | 5474 | 145 |

`zero_positive_region_fp` counts errors in regions with no retained positive evaluation
window; it does not prove those regions never flared. `both_models_alarm_fp` requires
both component models to alarm at their own frozen calibration thresholds, as well as
the ensemble being wrong. In 2023 this occurs in 5600 of 5992 FP windows: simply relying
on agreement between the two models would not remove most observed errors.

A run requires consecutive FP windows from the same HARP at exactly one-hour spacing.
A missing/excluded timestamp, non-FP window or region change breaks it. The at-least-six
criterion counts six forecast windows, not six independent events or a physical duration
of six hours. In 2023, 5474 of 5992 FP windows belong to such runs; the longest has 145
windows. In 2018 the longest has 129 windows. This is a descriptive persistence measure,
not a retrospectively applied alarm-suppression rule. Fewer repeated notifications would
be a separate operational metric and would not itself improve window-level precision.

## Selected model experiment and controls

The working hypothesis is that some persistently flare-like negative examples are not
adequately separated by the current decision boundary. This is an inference from the
error structure, not a proven cause. Choose **training-only out-of-time hard-negative
mining**, followed by a weighted XGBoost student, keeping the same 96 input features and
existing hyperparameters. This tests a different learning emphasis rather than another
large parameter search.

For each evaluation year Y, outer training still ends before Y-1. Fit a teacher XGBoost
before January 1 of Y-3; mine only the final two outer-training years. Purge overlapping
observation/prediction intervals and remove mining HARPs seen in teacher training.
Rank eligible known-negative training windows by teacher raw score and select exactly
ceil(0.10 * eligible_count), with forecast time and HARP as deterministic tie-breakers.
No evaluation-year scores, labels or error lists enter this selection. Those outer-training
labels are available when the final student is fitted; they are not forecast inputs.

Compare three fixed arms on the same annual splits:

1. Existing unweighted baseline ensemble.
2. Hard-negative student: selected negatives have training weight 3; every other training
   window has weight 1. All original outer-training rows remain.
3. Matched uniform-negative control: all outer-training negatives have weight
   `1 + 2 * hard_negative_count / outer_training_negative_count`, positives have weight 1.
   Its total negative weight equals arm 2, separating targeted mining from simply putting
   more weight on the negative class.

Keep the logistic component unchanged and replace only XGBoost in the fixed 0.45/0.55
blend. Refit each student's sigmoid calibration on the unchanged outer calibration year;
choose its ensemble threshold there at recall >=0.95 and transfer it unchanged. Keeping
the calibration scheme fixed isolates weighting; separating probability fitting and
threshold fitting remains a different, unexecuted experiment. If a teacher lacks both
classes or eligible negatives are absent, mark the candidate arms unavailable rather
than silently substituting baseline. Preserve the original outer-fold skip rules.

There is no automatic promotion. The frozen design requires higher precision and
recall >=0.95 in every comparable positive evaluation year, no lower AP and no higher
Brier/log loss per year versus baseline. Report all arms and failed years, including
FP/FPR in zero-positive years. Use 1000 paired whole-HARP bootstrap draws with seed 24;
intervals are conditional on trained models and frozen thresholds. Improvement over the
matched uniform control is needed to attribute benefit to targeted mining. This demanding
gate may reject the candidate. Weighting can worsen recall or calibration; success is
not guaranteed. All evaluation remains adaptive development, and the reserved test stays
closed until the complete policy is frozen.

## Reproduction and limitations

```sh
.venv/bin/python scripts/audit_false_alarms.py --output artifacts/false_alarm_audit_20261029_r1
.venv/bin/python scripts/report_false_alarm_audit.py --source artifacts/false_alarm_audit_20261029_r1 --report-name false-alarm-audit-20261029
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_false-alarm-audit-20261029
```

Use fresh output directories and report names for reruns, preserving frozen evidence.
If the audit report hash changes, create a new design revision and update the reporting
script's design path; never overwrite the frozen protocol. Review both editions, register
the source hash and links in `docs/reports.json` and `docs/reports.md`, then publish to a
new HTML directory. Data and generated artifacts remain outside Git. There is no training
command for the selected design yet: implementation and execution are the next task.

The audit is descriptive, with correlated windows, changing yearly prevalence and
pre-existing label/quality exclusions. It reports observed counts and rates, not confidence
intervals or causal effects for the missingness association. It does not verify physical
region identities across rotations, resolve event associations or prove any label is wrong.

| source | SHA-256 |
| --- | --- |
| artifacts/false_alarm_audit_20261029_r1/report.json | 2da6a2804b33e7c7d0f26d7c43fccd9d00c79e4550221560fc162409d108bb23 |
| config/hard-negative-v1.json | cb016d8ff9d1942d9410332c9e639ba475f1365ca88d301c735d326d189e8730 |

