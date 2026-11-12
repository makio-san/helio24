# Adoption of operating point v3 and rebuild of the development pipeline (2026-11-12)

## Decision

On 2026-11-12 the project owner adopted [`config/operating-point-v3.json`](../config/operating-point-v3.json): the
relabelled development table (`artifacts/relabelled_development_20261111_r1`, built under `config/relabel-v1.json`)
replaces the frozen-label table `artifacts/v2_development_features_20261025_r2` as the basis of development
reporting and future development protocols, with a watch tier (prior-year window recall 0.90) and an alert tier
(prior-year precision 0.50, recall floor 0.10, fallback flag). `config/operating-point-v2.json` is superseded; its
recall-0.90 rule continues as the watch tier and its frozen-label results stay visible for comparison. This report
records the adoption and the one condition it set that needed new work: a frozen protocol,
[`config/walk-forward-v2.json`](../config/walk-forward-v2.json), that rebuilds the development pipeline from the
relabelled table and reproduces `artifacts/relabel_walk_forward_20261111_r1`. The protocol, the runner and the
status change were committed before any result; the rebuild reproduced the relabelled walk-forward bit for bit in
every evaluated year (2014, 2015, 2016, 2017, 2022, 2023), so `pipeline_reproduced` and `adoption_effective` are true.

Nothing in production changed: the dashboard alert threshold in `app.py`, the deployed alert and the frozen
artifacts are untouched, and the reserved 2024–2025 test was not read. The adoption is a change of development
basis and operating point, not a performance improvement: the probabilities differ from the frozen pipeline only
because the training labels differ.

## What the rebuilt pipeline is

The recipes are those of `config/walk-forward-v1.json` unchanged (logistic regression and XGBoost with fixed
hyperparameters and seed 24, sigmoid calibration on the previous calendar year, ensemble weights 0.45/0.55,
expanding training with purge of boundary-crossing windows and of HARPs shared with earlier roles). The source is
the relabelled table (report sha256 `2847215ce5a5dedb9ebb93d7fa0ba1bcb7b4a7bf9fdcd80bab95e63726b9ac43`). Per evaluation year the runner fits the
recipes, selects three thresholds on the prior relabelled calibration year, writes them to disk before any
evaluation label is read, and stores models, calibrators, thresholds and predictions under
`artifacts/walk_forward_v2_20261112_r1/<year>/`. Folds 2018, 2019, 2020, 2021 are skipped because training or calibration
lacks both classes or the year has no evaluable positives, as in every earlier walk-forward run on these years.

## Reproduction of the relabelled walk-forward

Each rebuilt year was compared with the stored `relabelled_models` arm of `artifacts/relabel_walk_forward_20261111_r1`
and with `artifacts/two_tier_relabelled_20261111_r1`: same evaluation windows, calibrated ensemble probability
equal bit for bit (`np.array_equal`), recall-0.95 and recall-0.90 thresholds equal, alert threshold with its
calibration recall, precision and fallback flag equal, and tp, fp, fn, tn, positive runs and missed positive runs
equal in both tiers.

| year | same windows | probabilities identical | max abs Δp | recall thresholds identical | alert threshold identical | counts identical | reproduced |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yes | yes | 0.0e+00 | yes | yes | yes | yes |
| 2015 | yes | yes | 0.0e+00 | yes | yes | yes | yes |
| 2016 | yes | yes | 0.0e+00 | yes | yes | yes | yes |
| 2017 | yes | yes | 0.0e+00 | yes | yes | yes | yes |
| 2022 | yes | yes | 0.0e+00 | yes | yes | yes | yes |
| 2023 | yes | yes | 0.0e+00 | yes | yes | yes | yes |

## Alert tier (prior-year precision 0.50, recall floor 0.10)

Relabelled rows are the adopted pipeline; frozen rows are copied from `artifacts/two_tier_20261110_r1` as the
frozen-label reference. The two label sets are measured on different window sets and are not pooled.

| year | labels | fallback | tp | fp | recall | precision | precision 95% interval | accuracy | always-negative accuracy | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled | no | 688 | 320 | 0.2824 | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 66 / 88 |
| 2014 | frozen | no | 644 | 248 | 0.2788 | 0.7220 | [0.4414, 0.8625] | 0.9746 | 0.9693 | 63 / 83 |
| 2015 | relabelled | no | 545 | 457 | 0.3730 | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 27 / 57 |
| 2015 | frozen | no | 551 | 476 | 0.4066 | 0.5365 | [0.3109, 0.7080] | 0.9815 | 0.9804 | 24 / 51 |
| 2016 | relabelled | no | 94 | 109 | 0.4393 | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 3 / 8 |
| 2016 | frozen | no | 76 | 112 | 0.4199 | 0.4043 | [0.0000, 0.5249] | 0.9950 | 0.9958 | 2 / 7 |
| 2017 | relabelled | no | 177 | 27 | 0.6679 | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 3 / 6 |
| 2017 | frozen | no | 182 | 43 | 0.7194 | 0.8089 | [0.0000, 0.9691] | 0.9942 | 0.9870 | 2 / 6 |
| 2022 | relabelled | yes | 1056 | 1178 | 0.4822 | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 32 / 72 |
| 2022 | frozen | yes | 221 | 1111 | 0.5249 | 0.1659 | [0.0725, 0.2543] | 0.9742 | 0.9917 | 2 / 16 |
| 2023 | relabelled | no | 1587 | 2136 | 0.3879 | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 68 / 159 |
| 2023 | frozen | no | 79 | 106 | 0.1012 | 0.4270 | [0.0968, 0.7441] | 0.9866 | 0.9871 | 30 / 38 |

## Watch tier (prior-year recall 0.90)

Frozen rows are copied from `artifacts/two_tier_20261110_r1`.

| year | labels | fallback | tp | fp | recall | precision | precision 95% interval | accuracy | always-negative accuracy | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled |  | 2146 | 9020 | 0.8810 | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 6 / 88 |
| 2014 | frozen |  | 2007 | 7634 | 0.8688 | 0.2082 | [0.1327, 0.2868] | 0.8945 | 0.9693 | 6 / 83 |
| 2015 | relabelled |  | 1396 | 8079 | 0.9555 | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 1 / 57 |
| 2015 | frozen |  | 1308 | 6294 | 0.9653 | 0.1721 | [0.1069, 0.2401] | 0.9083 | 0.9804 | 0 / 51 |
| 2016 | relabelled |  | 201 | 1722 | 0.9393 | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 0 / 8 |
| 2016 | frozen |  | 162 | 1303 | 0.8950 | 0.1106 | [0.0000, 0.2039] | 0.9692 | 0.9958 | 0 / 7 |
| 2017 | relabelled |  | 243 | 1058 | 0.9170 | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1 / 6 |
| 2017 | frozen |  | 235 | 1035 | 0.9289 | 0.1850 | [0.0000, 0.4581] | 0.9461 | 0.9870 | 1 / 6 |
| 2022 | relabelled |  | 2024 | 11917 | 0.9242 | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 5 / 72 |
| 2022 | frozen |  | 414 | 8949 | 0.9834 | 0.0442 | [0.0222, 0.0724] | 0.8235 | 0.9917 | 0 / 16 |
| 2023 | relabelled |  | 3695 | 16022 | 0.9032 | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 10 / 159 |
| 2023 | frozen |  | 653 | 4852 | 0.8361 | 0.1186 | [0.0765, 0.1630] | 0.9175 | 0.9871 | 3 / 38 |

## Comparison point: prior-year recall 0.95

Kept visible because `config/operating-point-v2.json` requires it. Frozen rows are the `ensemble` rows of
`artifacts/walk_forward_20261028_r1`, which did not record positive runs or intervals.

| year | labels | fallback | tp | fp | recall | precision | precision 95% interval | accuracy | always-negative accuracy | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled |  | 2294 | 14074 | 0.9417 | 0.1402 | [0.0965, 0.1918] | 0.8186 | 0.9689 | 3 / 88 |
| 2014 | frozen |  | 2184 | 13886 | 0.9455 | 0.1359 |  | 0.8137 | 0.9693 |  |
| 2015 | relabelled |  | 1430 | 13784 | 0.9788 | 0.0940 | [0.0569, 0.1366] | 0.8042 | 0.9793 | 1 / 57 |
| 2015 | frozen |  | 1346 | 11453 | 0.9934 | 0.1052 |  | 0.8342 | 0.9804 |  |
| 2016 | relabelled |  | 211 | 3257 | 0.9860 | 0.0608 | [0.0000, 0.1182] | 0.9244 | 0.9950 | 0 / 8 |
| 2016 | frozen |  | 176 | 2289 | 0.9724 | 0.0714 |  | 0.9466 | 0.9958 |  |
| 2017 | relabelled |  | 245 | 1349 | 0.9245 | 0.1537 | [0.0000, 0.3707] | 0.9310 | 0.9866 | 1 / 6 |
| 2017 | frozen |  | 237 | 1287 | 0.9368 | 0.1555 |  | 0.9333 | 0.9870 |  |
| 2022 | relabelled |  | 2052 | 13825 | 0.9370 | 0.1292 | [0.0889, 0.1749] | 0.7871 | 0.9666 | 5 / 72 |
| 2022 | frozen |  | 415 | 10072 | 0.9857 | 0.0396 |  | 0.8014 | 0.9917 |  |
| 2023 | relabelled |  | 3939 | 25760 | 0.9628 | 0.1326 | [0.1052, 0.1604] | 0.7328 | 0.9578 | 1 / 159 |
| 2023 | frozen |  | 691 | 5992 | 0.8848 | 0.1034 |  | 0.8992 | 0.9871 |  |

## Reading

- `pipeline_reproduced`: true in all 6 evaluated years; the maximum absolute probability
  difference is 0 everywhere. The adopted operating point therefore rests on a pipeline that is reproducible from
  the relabelled table, the frozen recipes, the protocol hash and the code hashes alone.
- `years_meeting_alert_target`: 2014, 2015, 2017 (3 of 6). The alert tier is a fallback year in 2022
  (relabelled 2021 calibration year, best precision 0.1996 at the recall floor). In 2022 it delivers precision
  0.4727 at recall 0.4822 (frozen: 0.1659 at 0.5249); in 2023 0.4263 at recall
  0.3879 (frozen: 0.4270 at 0.1012). Both cycle-25 years miss 0.50 by less than 0.08 and accuracy sits
  under always-negative in both; the number of years meeting the target is reported, not required, by the protocol.
- Against the project goal (precision up, accuracy above always-negative every year): the alert tier meets the
  accuracy condition in 2014, 2015 and 2017 only; the watch tier in no year. The adoption moves the basis of
  measurement, which is what the label-coverage audit showed was wrong in cycle 25; it does not by itself close
  the remaining gap in 2022 and 2023.

## What changes for later work

- Development reports written after this date state that the development basis is the relabelled table and why,
  give precision with delivered recall and missed positive runs per year and tier, mark alert fallback years and
  keep frozen-label results visible (rule added to `AGENTS.md`).
- `artifacts/walk_forward_v2_20261112_r1` is the reference pipeline for future development protocols. The
  frozen-label artifacts remain intact as evidence.
- The dashboard alert threshold and any deployed alert are unchanged and need a separate decision with the
  reserved 2024–2025 test; `app.py` stays as it is.

## Limits

Adaptive description on already inspected development years, not an independent test. The relabelled labels are
an association by NOAA SGAS region numbers and JSOC `NOAA_ARS`, not ground truth; 133 unassigned events remain
excluded fail-closed. Counts are overlapping forecast windows and groupings of them, not physical flares. Alert
precision in 2016 and 2017 rests on 8 and 6 positive runs and its intervals reach 0.0000. Bit-for-bit
reproduction was obtained on the same machine and runtime (`runtime-py314-20261101`); on another platform
XGBoost histogram fits may differ in the last bits, in which case the protocol's identity checks fail by design
and the difference must be reported rather than tolerated.

## Reproduction

```sh
python -m scripts.rebuild_walk_forward_v2 --output artifacts/walk_forward_v2_20261112_r1
python -m pytest -q tests
```

Protocol sha256 `d6e08a575193162afe59e068c568b51dee5e34c3950dcb5b6ed98b817e63d3bb`. Code hashes recorded in `report.json`:

- `scripts/rebuild_walk_forward_v2.py` `59d757bb2fc4d89872dbec265af8f4be25c9c1399490e0973f90313bf9b44605`
- `scripts/audit_two_tier.py` `a2c871ca50dc187e64f2b8fc65d581990e53ec609c05c7408745a7e87b792a57`
- `helio24/two_tier.py` `0b94f907f1f3db4a05d799bb99e02cf9ead571279405e7ac54769868d001d60e`
- `helio24/walk_forward.py` `9c1ed05bc0e4456680faa5d4532303c098e22a86f811db435c78f31d12d43f44`
- `helio24/v2_training.py` `647289a915cf31a7fbd7e09277be0e75dc83292004b8b1b737a46439322c4618`
- `helio24/calibration.py` `0c43ad5027d20d50c233351829c4c13325cc65d140f1fb2bac2a44428b24dc16`

Use new output directories; existing output is not overwritten.
