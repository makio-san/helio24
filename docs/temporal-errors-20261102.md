# Temporal-model false alarms: completed-year localization

**Finding:** the 2016 TCN deterioration is concentrated in persistent regional alarm
sequences and high measurement-level cohorts. Missing values alone do not explain the
extra alarms. The pattern varies by year, and chronological order has not shown a
consistent advantage over its shuffled control. Continue the frozen experiment; this
audit does not justify promotion, threshold tuning or changing the ongoing recipe.

## Scope and operating points

This is a fixed snapshot of completed 2014–2016 development folds. Later folds are still
being trained and are excluded even if they finish during reporting. Frozen fold/output
hashes, original feature-shard hashes, forecast keys, labels and annual split audits are
verified. Alarm counts and precision/recall must reproduce the frozen metrics. Neither
the 2024–2025 test nor raw outcome metadata is accessed. No new training is performed.

The plan was written after inspecting global results but before the granular audit.
This is adaptive descriptive analysis, not an independent prospective evaluation.
Candidate and control keep their own prior-year calibration thresholds: recall differs,
so these comparisons are not at matched recall. Fractional scores use a 0–1 scale.
Counts refer to overlapping forecast windows, not independent flares or notifications.

| year | candidate | candidate_precision | control_precision | candidate_recall | control_recall | candidate_fp | control_fp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | chronological | 0.100078 | 0.135905 | 0.945455 | 0.945455 | 19639 | 13886 |
| 2014 | shuffled_interior | 0.091195 | 0.135905 | 0.940260 | 0.945455 | 21645 | 13886 |
| 2015 | chronological | 0.105677 | 0.105164 | 0.971218 | 0.993358 | 11137 | 11453 |
| 2015 | shuffled_interior | 0.097865 | 0.105164 | 0.974170 | 0.993358 | 12168 | 11453 |
| 2016 | chronological | 0.026380 | 0.071400 | 0.955801 | 0.972376 | 6385 | 2289 |
| 2016 | shuffled_interior | 0.026896 | 0.071400 | 0.983425 | 0.972376 | 6440 | 2289 |


2015's small precision increase accompanies lower recall. In 2016 the chronological TCN
has recall 0.955801, versus 0.972376 for the baseline, yet produces 4096 more FP windows.
2014 has identical aggregate recall but more FP. Net FP alone is not a complete success
criterion; identify gained and lost positive windows as well.

## Paired additions and removals

| year | candidate | control | extra_fp | removed_fp | shared_fp | net_fp | extra_tp | removed_tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | chronological | baseline | 6773 | 1020 | 12866 | 5753 | 53 | 53 |
| 2014 | shuffled_interior | baseline | 8503 | 744 | 13142 | 7759 | 52 | 64 |
| 2014 | chronological | shuffled_interior | 1122 | 3128 | 18517 | -2006 | 24 | 12 |
| 2015 | chronological | baseline | 2541 | 2857 | 8596 | -316 | 1 | 31 |
| 2015 | shuffled_interior | baseline | 3014 | 2299 | 9154 | 715 | 2 | 28 |
| 2015 | chronological | shuffled_interior | 1280 | 2311 | 9857 | -1031 | 4 | 8 |
| 2016 | chronological | baseline | 4446 | 350 | 1939 | 4096 | 1 | 4 |
| 2016 | shuffled_interior | baseline | 4462 | 311 | 1978 | 4151 | 4 | 2 |
| 2016 | chronological | shuffled_interior | 1285 | 1340 | 5100 | -55 | 0 | 5 |


`extra_fp` means the candidate alarms on a negative window where the named control does
not; `removed_fp` is the reverse. `shared_fp` is alarmed by both. Net change equals
extra minus removed, with the equality checked for every group. `extra_tp` and
`removed_tp` describe the same switches on positive windows. These are window counts,
not counts of distinct flare events. In 2016, 4446 extra minus 350 removed FP gives
4096 net additional FP. One new TP is offset by four removed TP. In 2015, 2541 extra
minus 2857 removed FP gives a net reduction of 316, with one gained and 31 lost TP.

## Regional concentration and persistence

| year | top10_extra_fp | top10_extra_fp_share | top10_negative_share | complete_measurement_extra_fp | zero_positive_region_extra_fp | extra_fp_in_runs_ge6 | max_extra_run |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 1473 | 0.217481 | 0.038111 | 5052 | 6110 | 5695 | 110 |
| 2015 | 777 | 0.305785 | 0.041426 | 1892 | 2473 | 1852 | 70 |
| 2016 | 1557 | 0.350202 | 0.064080 | 3072 | 4233 | 3946 | 107 |


The ten HARPs with most extra FP are selected post hoc separately in each comparison.
Their extra-FP share must be assessed against their share of negative-window exposure.
For 2016 those shares are 0.350202 and 0.064080. They identify diagnostic priorities,
not an exclusion list. Region ranks and zero-positive status use future evaluation
outcomes and cannot be treated as predictors available at forecast time.

The three largest extra-FP contributors per year are:

| year | harp | positives | negatives | extra_fp | removed_fp | net_fp |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 3601 | 0 | 309 | 177 | 3 | 174 |
| 2014 | 3620 | 0 | 314 | 177 | 0 | 177 |
| 2014 | 4888 | 0 | 276 | 171 | 0 | 171 |
| 2015 | 5831 | 0 | 308 | 143 | 26 | 117 |
| 2015 | 5724 | 0 | 261 | 103 | 4 | 99 |
| 2015 | 5022 | 0 | 321 | 98 | 6 | 92 |
| 2016 | 6789 | 0 | 272 | 229 | 0 | 229 |
| 2016 | 6289 | 0 | 286 | 181 | 0 | 181 |
| 2016 | 6515 | 0 | 267 | 174 | 0 | 174 |


In 2016 HARP 6789 has 229 extra FP and no removed FP among 272 negative windows.
Of all 4446 extra FP that year, 3946 belong to runs of at least six hourly windows;
the longest run has 107 windows. Runs require exactly one-hour adjacency within a HARP;
any missing/excluded timestamp or nonmatching window breaks a run. Hourly forecasts
have overlapping 12-hour observations and 24-hour targets; these are not independent
repeated failures. Notification deduplication addresses presentation, not window precision.

## Missing measurements

| year | missing_bin | negatives | extra_fp | removed_fp | net_fp | candidate_fpr | control_fpr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | zero | 54389 | 5052 | 719 | 4333 | 0.253470 | 0.173804 |
| 2014 | (0,0.01] | 2758 | 279 | 88 | 191 | 0.731690 | 0.662437 |
| 2014 | (0.01,0.05] | 8852 | 923 | 94 | 829 | 0.271577 | 0.177926 |
| 2014 | (0.05,1] | 6919 | 519 | 119 | 400 | 0.206822 | 0.149010 |
| 2015 | zero | 51224 | 1892 | 2080 | -188 | 0.152370 | 0.156040 |
| 2015 | (0,0.01] | 3093 | 136 | 353 | -217 | 0.499838 | 0.569997 |
| 2015 | (0.01,0.05] | 6375 | 290 | 246 | 44 | 0.158588 | 0.151686 |
| 2015 | (0.05,1] | 7091 | 223 | 178 | 45 | 0.109293 | 0.102947 |
| 2016 | zero | 32227 | 3072 | 271 | 2801 | 0.136842 | 0.049927 |
| 2016 | (0,0.01] | 1653 | 402 | 16 | 386 | 0.388385 | 0.154870 |
| 2016 | (0.01,0.05] | 4056 | 447 | 28 | 419 | 0.149901 | 0.046598 |
| 2016 | (0.05,1] | 4870 | 525 | 35 | 490 | 0.148871 | 0.048255 |


The five fixed missingness categories include an unavailable category, retained in CSV
but omitted above when empty. FPR is FP divided by negative windows in the same bin.
In 2016 the small-missingness bin (0,0.01] has FPR 0.388385 versus baseline 0.154870.
Its relative risk is high, but zero-missingness windows contribute 3072 of 4446 extra FP
and 2801 of 4096 net extra FP. Fully measured windows also supply most extra FP in 2014
and 2015. Improving imputation alone is therefore not established as the main remedy.
Missingness associations can be confounded by region composition and measurement level;
no missingness bin or region is removed or relabeled.

## Measurement conditions using training-only cutpoints

Eight fields were fixed: last and delta of USFLUX, TOTUSJH, R_VALUE and MEANSHR.
Each year's original training data supplies finite-value 25/50/75 percentile cuts,
with duplicate cuts removed. Evaluation labels and scores do not choose cuts. Bins use
right-closed intervals; unavailable values are preserved. Evaluation exposure need not
be balanced between bins. Exact cutpoints are in measurement_cutpoints.csv. The highest
last-value bin in these data is bin4:

| year | field | negatives | extra_fp | removed_fp | net_fp | candidate_fpr | control_fpr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | USFLUX__last | 18235 | 2765 | 680 | 2085 | 0.783603 | 0.669262 |
| 2014 | TOTUSJH__last | 18618 | 2852 | 746 | 2106 | 0.794070 | 0.680954 |
| 2014 | R_VALUE__last | 15521 | 2081 | 667 | 1414 | 0.842729 | 0.751627 |
| 2014 | MEANSHR__last | 16661 | 4059 | 341 | 3718 | 0.753556 | 0.530400 |
| 2015 | USFLUX__last | 12927 | 548 | 1957 | -1409 | 0.607566 | 0.716562 |
| 2015 | TOTUSJH__last | 12839 | 631 | 2002 | -1371 | 0.646779 | 0.753563 |
| 2015 | R_VALUE__last | 11460 | 497 | 2069 | -1572 | 0.702705 | 0.839878 |
| 2015 | MEANSHR__last | 10097 | 1393 | 1008 | 385 | 0.649203 | 0.611073 |
| 2016 | USFLUX__last | 6397 | 2434 | 199 | 2235 | 0.645928 | 0.296545 |
| 2016 | TOTUSJH__last | 6088 | 2394 | 244 | 2150 | 0.685611 | 0.332457 |
| 2016 | R_VALUE__last | 7008 | 2505 | 328 | 2177 | 0.623288 | 0.312643 |
| 2016 | MEANSHR__last | 8833 | 2465 | 294 | 2171 | 0.442545 | 0.196762 |


In 2016 the upper USFLUX__last bin adds 2235 net FP among 6397 negative windows;
FPR is 0.645928 versus 0.296545. The upper TOTUSJH__last and R_VALUE__last bins add
2150 and 2177 net FP. Upper last-value bins also deteriorate in 2014; in 2015 the
USFLUX/TOTUSJH/R_VALUE upper bins improve, while upper MEANSHR still worsens.
This is not a stable universal high-value rejection rule.

For compact inspection, the following table selects the finite bin with largest net FP
for each field in 2016. This selection is post hoc; all bins remain in measurement_bins.csv:

| field | measurement_bin | negatives | extra_fp | removed_fp | net_fp | candidate_fpr | control_fpr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MEANSHR__delta | bin1 | 10822 | 1323 | 63 | 1260 | 0.173073 | 0.056644 |
| MEANSHR__last | bin4 | 8833 | 2465 | 294 | 2171 | 0.442545 | 0.196762 |
| R_VALUE__delta | bin1 | 9339 | 1877 | 88 | 1789 | 0.257951 | 0.066388 |
| R_VALUE__last | bin4 | 7008 | 2505 | 328 | 2177 | 0.623288 | 0.312643 |
| TOTUSJH__delta | bin4 | 8672 | 1788 | 222 | 1566 | 0.327837 | 0.147256 |
| TOTUSJH__last | bin4 | 6088 | 2394 | 244 | 2150 | 0.685611 | 0.332457 |
| USFLUX__delta | bin4 | 8370 | 1825 | 236 | 1589 | 0.353286 | 0.163441 |
| USFLUX__last | bin4 | 6397 | 2434 | 199 | 2235 | 0.645928 | 0.296545 |


The field views overlap: the same window can appear in several fields. Never sum their
counts as independent contributions. Delta is last minus first, not a slope or a complete
sequence pattern. High-value and changing-field associations do not establish a physical
cause, a label error or one unique model mechanism. A possible coarse activity shortcut
is a hypothesis for later ablation, not a demonstrated causal explanation.

## Ranking, probability scores and uncertainty

| year | candidate_average_precision | control_average_precision | candidate_brier | control_brier | candidate_log_loss | control_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.421566 | 0.507930 | 0.022812 | 0.020661 | 0.089042 | 0.076538 |
| 2015 | 0.461100 | 0.492441 | 0.014098 | 0.013564 | 0.052287 | 0.047847 |
| 2016 | 0.146877 | 0.366443 | 0.004133 | 0.003263 | 0.019767 | 0.014523 |


Chronological TCN AP is lower and Brier/log loss higher than the baseline in all three
years. AP does not depend on the alarm threshold; this makes a purely threshold-only
explanation insufficient for the observed ranking deficit. It does not isolate the
cause between representation, optimization, class weighting and distribution shift.
Chronological ordering outperforms shuffled AP in 2014 and 2015 but underperforms it in
2016 (0.146877 versus 0.187088). The ordering hypothesis is not consistently supported.

Existing paired HARP-bootstrap intervals for chronological minus baseline are reproduced
below. These use fixed models/thresholds, 1000 draws and seed 24; they exclude retraining
uncertainty and do not adjust for this audit's multiple views:

| year | metric | lower | upper | valid_draws |
| --- | --- | --- | --- | --- |
| 2014 | precision | -0.050744 | -0.023858 | 1000 |
| 2014 | recall | -0.038392 | 0.036012 | 1000 |
| 2014 | fp | 4488.800000 | 7035.675000 | 1000 |
| 2015 | precision | -0.007348 | 0.008657 | 1000 |
| 2015 | recall | -0.061816 | -0.002144 | 1000 |
| 2015 | fp | -1277.425000 | 554.250000 | 1000 |
| 2016 | precision | -0.082771 | 0.000000 | 1000 |
| 2016 | recall | -0.136364 | 0.000000 | 973 |
| 2016 | fp | 3057.900000 | 5347.175000 | 1000 |


The 2015 precision interval crosses zero; its small point gain is not established as a
reliable improvement. In 2016 some resamples have no positives, leaving 973 valid recall
draws, and the precision interval reaches zero. Do not infer a universal causal effect
or independent statistical confirmation from region ranks or selected measurement bins.

## Research consequence and reproduction

Keep the incumbent and the ongoing sequence recipe fixed. Complete the annual experiment
before changing direction. If the pattern persists, prioritize an ablation of discrimination
within high-measurement, mostly negative cohorts while preserving the strong summary-feature
reference; a hybrid/static-summary control is a candidate for a future frozen protocol.
This audit does not select or start that experiment. Further missing-value tweaks alone
and evaluation-based threshold retuning are not supported as sufficient remedies.

```sh
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/audit_temporal_errors.py --plan config/temporal-error-audit-v1.json --output artifacts/temporal_error_audit_20261102_r2
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/report_temporal_errors.py --source artifacts/temporal_error_audit_20261102_r2 --name temporal-errors-20261102
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -m pytest tests/test_temporal_errors.py tests/test_false_alarm_audit.py tests/test_bilingual_reports.py -q
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/publish_reports.py --output artifacts/bilingual_reports_temporal-errors-20261102
```

Use new output/report names for reruns; retain frozen outputs. The first audit revision
was preserved; r2 adds frozen ranking/probability context and explicit bin coverage checks.
Review both full editions, register the source hash and language links in docs/reports.json
and docs/reports.md, then publish paired HTML to a fresh directory. Full regional,
missingness, run and measurement tables remain in local ignored CSV artifacts. Only
analysis code, plan and documents enter Git; local app.py branding edits remain uncommitted.

| source | sha256 |
| --- | --- |
| artifacts/temporal_error_audit_20261102_r2/report.json | 4a4308bf4f9aa2703039c3679c7f0d26871cf2fbb2b211615939139d162b15f2 |
| config/temporal-error-audit-v1.json | f46c5bf147b1ac8c269128c4702acc12d35d9a7eb95566da45506586eff6d302 |


