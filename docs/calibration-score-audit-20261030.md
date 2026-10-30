# Calibration score distributions and regional threshold sensitivity

The audit identifies two concrete sources of threshold sensitivity: positive windows
can be concentrated in very few HARPs, and the lower tail of positive scores can change
substantially between halves of a year. This is descriptive evidence, not proof of a
physical cause or a newly improved model. No model, label, deployed threshold or evaluation
population was changed; the reserved 2024–2025 test remains closed.

## Scope and method

The frozen annual models from `artifacts/walk_forward_20261028_r1` are verified by hashes.
For each completed evaluation year, inspect its preceding calibration year: full year,
early half and late half. The July boundary purges crossing observation/prediction windows
and excludes late HARPs shared with the early half, exactly as in the previous experiment.
This changes half-year composition; the full-year population need not equal the sum of
the purged halves. The 2019–2021 outer skips remain as previously documented.

All three periods are scored with the same frozen full-year sigmoid calibrators and
0.45 logistic/0.55 XGBoost blend for that year. This avoids changing the score mapping
while comparing halves; it does not provide prospective early-half estimates, because
the full-year calibrators have seen that year's labels. Scores are in-sample with respect
to calibration, while the underlying classifiers were trained earlier. No new classifiers
or calibrators are fitted and no evaluation-year prediction results are used in this audit.

## How many positive regions support each period?

| evaluation_year | calibration_year | period | rows | positives | positive_regions | top1_positive_share | top3_positive_share | concentration_equivalent_regions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 2013 | full | 74149 | 1287 | 31 | 0.107226 | 0.253302 | 21.683344 |
| 2014 | 2013 | early | 33718 | 406 | 14 | 0.160099 | 0.354680 | 11.851884 |
| 2014 | 2013 | late | 39614 | 881 | 17 | 0.156640 | 0.370034 | 12.422352 |
| 2015 | 2014 | full | 75228 | 2310 | 44 | 0.130736 | 0.282684 | 20.992730 |
| 2015 | 2014 | early | 36445 | 1215 | 27 | 0.179424 | 0.362140 | 14.148624 |
| 2015 | 2014 | late | 37472 | 1054 | 16 | 0.286528 | 0.519924 | 7.497577 |
| 2016 | 2015 | full | 69138 | 1355 | 24 | 0.118081 | 0.346125 | 15.251277 |
| 2016 | 2015 | early | 38615 | 692 | 13 | 0.228324 | 0.510116 | 8.401418 |
| 2016 | 2015 | late | 29912 | 663 | 11 | 0.241327 | 0.553544 | 6.934687 |
| 2017 | 2016 | full | 42987 | 181 | 4 | 0.480663 | 0.878453 | 2.996524 |
| 2017 | 2016 | early | 26232 | 111 | 2 | 0.783784 | 1.000000 | 1.512707 |
| 2017 | 2016 | late | 16505 | 70 | 2 | 0.685714 | 1.000000 | 1.757532 |
| 2018 | 2017 | full | 19529 | 253 | 3 | 0.573123 | 1.000000 | 2.362043 |
| 2018 | 2017 | early | 10352 | 65 | 1 | 1.000000 | 1.000000 | 1.000000 |
| 2018 | 2017 | late | 9078 | 188 | 2 | 0.771277 | 1.000000 | 1.545160 |
| 2022 | 2021 | full | 28125 | 204 | 9 | 0.205882 | 0.495098 | 7.468772 |
| 2022 | 2021 | early | 9997 | 75 | 3 | 0.560000 | 1.000000 | 2.323420 |
| 2022 | 2021 | late | 17462 | 129 | 6 | 0.271318 | 0.643411 | 5.281181 |
| 2023 | 2022 | full | 50756 | 421 | 12 | 0.175772 | 0.441805 | 9.559409 |
| 2023 | 2022 | early | 24198 | 192 | 5 | 0.375000 | 0.750000 | 4.114286 |
| 2023 | 2022 | late | 25733 | 229 | 7 | 0.323144 | 0.580786 | 5.473437 |

`positives` counts overlapping windows, not independent flares. `positive_regions` counts
HARPs with at least one retained positive window. The top shares show concentration of
positive windows. `concentration_equivalent_regions` is 1/sum(p_h**2), where p_h is each
region's share of positives. It is a concentration index expressed as equally sized
regions, not an estimated independent sample size or a count of physical flares.

For evaluation 2017, the late half of calibration 2016 has 70 positive windows from only
2 HARPs; the largest contributes 0.685714. For evaluation 2018, the early half of calibration
2017 has 65 positive windows from a single HARP. For evaluation 2023, the late half of
calibration 2022 has 229 positive windows from 7 HARPs; the top three contribute 0.580786.
Hundreds of windows therefore need not provide broad region diversity.

## Score distributions on the common mapping

| evaluation_year | period | positive_q05 | positive_q50 | positive_q95 | negative_q05 | negative_q50 | negative_q95 | threshold | negative_alarm_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | full | 0.011580 | 0.167211 | 0.586696 | 0.000077 | 0.000430 | 0.070068 | 0.011475 | 0.174096 |
| 2014 | early | 0.004390 | 0.095331 | 0.539138 | 0.000078 | 0.000535 | 0.072008 | 0.004389 | 0.289655 |
| 2014 | late | 0.037206 | 0.224362 | 0.592614 | 0.000077 | 0.000359 | 0.069333 | 0.037206 | 0.081094 |
| 2015 | full | 0.018840 | 0.273278 | 0.770197 | 0.000269 | 0.001158 | 0.117030 | 0.018839 | 0.218739 |
| 2015 | early | 0.010665 | 0.173029 | 0.772194 | 0.000270 | 0.001083 | 0.113298 | 0.010411 | 0.298098 |
| 2015 | late | 0.048547 | 0.369536 | 0.769026 | 0.000267 | 0.001171 | 0.114980 | 0.048456 | 0.107776 |
| 2016 | full | 0.030884 | 0.272912 | 0.823479 | 0.000042 | 0.000194 | 0.062607 | 0.030831 | 0.083398 |
| 2016 | early | 0.038605 | 0.232619 | 0.804585 | 0.000042 | 0.000169 | 0.068693 | 0.038226 | 0.076840 |
| 2016 | late | 0.029660 | 0.319682 | 0.831958 | 0.000043 | 0.000221 | 0.051984 | 0.029657 | 0.076379 |
| 2017 | full | 0.012000 | 0.156537 | 0.508341 | 0.000001 | 0.000011 | 0.009410 | 0.012000 | 0.042728 |
| 2017 | early | 0.033673 | 0.314764 | 0.522029 | 0.000001 | 0.000011 | 0.009871 | 0.027813 | 0.025573 |
| 2017 | late | 0.006642 | 0.094330 | 0.249638 | 0.000001 | 0.000010 | 0.009149 | 0.006265 | 0.067721 |
| 2018 | full | 0.005685 | 0.643340 | 0.977143 | 0.000001 | 0.000010 | 0.020389 | 0.004351 | 0.086273 |
| 2018 | early | 0.001537 | 0.438571 | 0.896121 | 0.000001 | 0.000018 | 0.010618 | 0.001514 | 0.121610 |
| 2018 | late | 0.059476 | 0.833817 | 0.978899 | 0.000000 | 0.000004 | 0.032197 | 0.058659 | 0.038695 |
| 2022 | full | 0.009002 | 0.053421 | 0.166537 | 0.000133 | 0.000543 | 0.031512 | 0.008994 | 0.133161 |
| 2022 | early | 0.008219 | 0.020485 | 0.053921 | 0.000132 | 0.000475 | 0.018915 | 0.008212 | 0.115299 |
| 2022 | late | 0.024713 | 0.095064 | 0.171570 | 0.000134 | 0.000582 | 0.044298 | 0.023981 | 0.073790 |
| 2023 | full | 0.018203 | 0.077292 | 0.605342 | 0.000022 | 0.000212 | 0.032203 | 0.018203 | 0.079706 |
| 2023 | early | 0.030897 | 0.077042 | 0.414994 | 0.000022 | 0.000206 | 0.030738 | 0.030397 | 0.050821 |
| 2023 | late | 0.006854 | 0.080588 | 0.640864 | 0.000023 | 0.000234 | 0.033747 | 0.006393 | 0.180011 |

Quantiles are the 5th, 50th and 95th percentiles computed separately for positive and
negative windows. The threshold is the existing exact threshold-selection routine at
recall >=0.95 within that period; it need not equal an interpolated 5th percentile.
`negative_alarm_rate` is the negative-window fraction at or above that period's threshold.
These are calibration diagnostics, not fresh evaluation metrics. All scores and shares
use a 0–1 scale.

For evaluation 2023, early/late thresholds are 0.030397 and 0.006393. Positive 5th percentiles
fall from 0.030897 to 0.006854, while negative 95th percentiles are 0.030738 and 0.033747.
The lower positive tail shifts much more than this negative-tail summary. A lower threshold
is consequently needed to retain 95% of the late-half positives. In evaluation 2022 the
direction reverses: early/late thresholds are 0.008212 and 0.023981. The direction of
within-year change is not stable across these years. Differences in region composition,
activity and retained labels may contribute; this audit does not distinguish their causes.

## Leave-one-positive-region-out sensitivity

| evaluation_year | period | threshold | loro_min | loro_max | loro_valid | loro_undefined |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | full | 0.011475 | 0.009165 | 0.013358 | 31 | 0 |
| 2014 | early | 0.004389 | 0.003704 | 0.006606 | 14 | 0 |
| 2014 | late | 0.037206 | 0.031652 | 0.049829 | 17 | 0 |
| 2015 | full | 0.018839 | 0.015741 | 0.022836 | 44 | 0 |
| 2015 | early | 0.010411 | 0.006395 | 0.014823 | 27 | 0 |
| 2015 | late | 0.048456 | 0.040604 | 0.055010 | 16 | 0 |
| 2016 | full | 0.030831 | 0.028395 | 0.036676 | 24 | 0 |
| 2016 | early | 0.038226 | 0.027657 | 0.064856 | 13 | 0 |
| 2016 | late | 0.029657 | 0.027115 | 0.036002 | 11 | 0 |
| 2017 | full | 0.012000 | 0.007103 | 0.043831 | 4 | 0 |
| 2017 | early | 0.027813 | 0.016567 | 0.043831 | 2 | 0 |
| 2017 | late | 0.006265 | 0.003033 | 0.077669 | 2 | 0 |
| 2018 | full | 0.004351 | 0.001779 | 0.058659 | 3 | 0 |
| 2018 | early | 0.001514 | undefined | undefined | 0 | 1 |
| 2018 | late | 0.058659 | 0.041224 | 0.299917 | 2 | 0 |
| 2022 | full | 0.008994 | 0.008509 | 0.016213 | 9 | 0 |
| 2022 | early | 0.008212 | 0.007776 | 0.013187 | 3 | 0 |
| 2022 | late | 0.023981 | 0.023561 | 0.033569 | 6 | 0 |
| 2023 | full | 0.018203 | 0.011763 | 0.023175 | 12 | 0 |
| 2023 | early | 0.030397 | 0.029032 | 0.039608 | 5 | 0 |
| 2023 | late | 0.006393 | 0.005466 | 0.020886 | 7 | 0 |

For each positive HARP, temporarily exclude all its windows, including its negative
windows, from the period. Recompute only the recall threshold on the remaining rows,
keeping model scores and calibrators fixed. Restore the region for the next calculation.
No permanent exclusion, policy update or evaluation-year optimization occurs. `loro_min`
and `loro_max` are observed perturbation extrema, not confidence intervals. `loro_undefined`
counts cases where both target classes no longer remain.

In evaluation 2017's late calibration half, removing one positive HARP changes the threshold
from 0.006265 to values ranging from 0.003033 to 0.077669. In evaluation 2023's late half,
the corresponding range is 0.005466–0.020886 around 0.006393. In evaluation 2018's early
half, removing the only positive HARP makes recall-threshold selection undefined. These
examples establish sensitivity to region composition conditional on the fitted scores;
they do not estimate future recall or prove that any region is mislabeled.

Largest absolute threshold change per period:

| evaluation_year | period | harp | removed_positives | removed_rows | threshold_without_region | threshold_delta |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | early | 2809 | 24 | 181 | 0.006606 | 0.002217 |
| 2014 | full | 3291 | 138 | 232 | 0.009165 | -0.002311 |
| 2014 | late | 3437 | 24 | 289 | 0.049829 | 0.012624 |
| 2015 | early | 3779 | 15 | 212 | 0.014823 | 0.004411 |
| 2015 | full | 4186 | 24 | 240 | 0.022836 | 0.003997 |
| 2015 | late | 4698 | 302 | 331 | 0.040604 | -0.007852 |
| 2016 | early | 5456 | 24 | 241 | 0.064856 | 0.026631 |
| 2016 | full | 5456 | 24 | 241 | 0.036676 | 0.005845 |
| 2016 | late | 6078 | 24 | 276 | 0.036002 | 0.006345 |
| 2017 | early | 6327 | 87 | 320 | 0.043831 | 0.016018 |
| 2017 | full | 6870 | 22 | 261 | 0.043831 | 0.031831 |
| 2017 | late | 6870 | 22 | 261 | 0.077669 | 0.071405 |
| 2018 | early | 6972 | 65 | 253 | undefined | undefined |
| 2018 | full | 6972 | 65 | 253 | 0.058659 | 0.054308 |
| 2018 | late | 7075 | 43 | 279 | 0.299917 | 0.241258 |
| 2022 | early | 7570 | 24 | 279 | 0.013187 | 0.004976 |
| 2022 | full | 7570 | 24 | 279 | 0.016213 | 0.007220 |
| 2022 | late | 7770 | 24 | 277 | 0.033569 | 0.009589 |
| 2023 | early | 8206 | 24 | 190 | 0.039608 | 0.009211 |
| 2023 | full | 8155 | 72 | 196 | 0.011763 | -0.006440 |
| 2023 | late | 8882 | 24 | 100 | 0.020886 | 0.014493 |

The full list is preserved in `region_influence.csv`. For a period with no defined
perturbation, the table shows an undefined row rather than inventing an influence value.

## Decision and next experiment boundary

Do not repeatedly move the half-year boundary until past precision looks better. This
audit motivates evaluating calibration support by region diversity, as well as window
count. It does not establish a universal minimum region count or an optimal calibration
duration. A future candidate should compare fixed multi-year calibration windows and
their region diversity using earlier inner chronological folds; any longer calibration
window must remain entirely after classifier training, with temporal and HARP separation.
Comparisons must control for altered training history and evaluate the final fixed policy
on the same outer periods. No such new training or duration search has been run here.

Lack of calibration support should be reported explicitly rather than promising 95%
future recall. Calibration adjusts probability interpretation and operating points; it
does not guarantee better separation of hard positive and negative examples. The current
dashboard model remains unchanged. This is adaptive retrospective development, not an
independent test; associated windows and prior label/quality exclusions limit inference.

## Reproduction and evidence

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/audit_calibration_scores.py \
  --output artifacts/calibration_score_audit_20261030_r1
.venv/bin/python scripts/report_calibration_scores.py --source artifacts/calibration_score_audit_20261030_r1 --report-name calibration-score-audit-20261030
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_calibration-score-audit-20261030
```

Use fresh artifact directories and report names; preserve all frozen outputs. Review
both full editions and register their source hash and links in `docs/reports.json` and
`docs/reports.md` before publishing to a new HTML directory. Score tables and generated
HTML remain local ignored artifacts. Original model/threshold hashes, audit code hashes
and result hashes support reproducibility. No causal significance test is claimed.

| source | SHA-256 |
| --- | --- |
| artifacts/calibration_score_audit_20261030_r1/report.json | 37d4773a865824d034d4701b220686575820918b4461e9c33f7c02ef4e0414dd |
| artifacts/calibration_score_audit_20261030_r1/summary.csv | 72f3d3fd48e4bc5ade803e693bde049a69f064991e0a666fc3cf09cf2b69d24c |
| artifacts/calibration_score_audit_20261030_r1/region_influence.csv | 2607f3e89c9ad2280ead59f0868677b009a1f5f91b9548661dcdefbf38928882 |

