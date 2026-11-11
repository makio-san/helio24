# Two-tier operating point on the relabelled table (2026-11-11)

## Decision

The [frozen protocol](../config/two-tier-v2.json) applies the two-tier rule of `config/two-tier-v1.json`, with
every target, floor and tie rule unchanged, to the relabelled table and the relabelled walk-forward models. The
alert tier at the primary precision target 0.50 meets it in the same three years as before (2014, 2015, 2017);
`cycle25_now_met` is false and `redefinition_supported` is false. What changed is the size of the miss in cycle 25.
In 2022 the alert tier is still a fallback year, because the relabelled 2021 calibration year (377 positive
windows) reaches precision 0.1996 at best; its evaluation precision is nevertheless 0.4727 [0.3482, 0.6021] at
recall 0.4822, against 0.1659 at recall 0.5249 on the frozen labels, and accuracy 0.9648 sits 0.0018 under
always-negative. In 2023 the rule is no longer a count fluke: it alarms on 1587 true windows instead of 79, at
recall 0.3879 instead of 0.1012, with precision 0.4263 [0.3483, 0.5053] against 0.4270 [0.0968, 0.7441] before;
the point misses 0.50 and accuracy 0.9522 is 0.0056 under always-negative. The relabelled evaluation-year oracle
reaches precision 0.50 at recall 0.4662 in 2022 (frozen: 0.1496) but only 0.0176 in 2023 (frozen: 0.0717). Zero
fits; no model, probability, alert or dashboard change; the reserved 2024–2025 test was not read. The protocol was
frozen and committed before any result.

## Why this protocol

On the frozen labels the alert tier held precision 0.50 only in cycle-24 years, and the 2022 and 2023 oracles
reached 0.50 at recall 0.15 and 0.07. The [relabelling](relabel-20261111.md) raised the 2022 and 2023 average
precision to 0.4622 and 0.3626, into the cycle-24 range, so the inherited prior-year precision rule was retested.

## Method

Arm: `relabelled_models` of `config/relabel-v1.json`, stage-one inference with the stored per-year models. Watch
tier: previous relabelled calibration year at window recall 0.90, reproduced bit for bit from the relabelled
walk-forward thresholds. Alert tier: `helio24.two_tier.precision_threshold` on the previous relabelled calibration
year with targets 0.30 and 0.50 and recall floor 0.10; when no threshold reaches the target the best-precision
threshold is used and the year is marked fallback. Thresholds for every tier and year were written and hashed
before any evaluation label was read. Intervals are 95% HARP-cluster bootstraps (1000 draws, seed 24). The frozen
two-tier result is copied beside each row as the old-label reference; the two runs use different window sets
(the relabelled 2022 and 2023 roles hold 65593 and 96991 windows against 50756 and 60366).

## Alert tier at precision target 0.50

| year | labels | fallback | calibration precision | calibration recall | TP | FP | recall | precision | 95% interval | accuracy | always-negative accuracy | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled | no | 0.5000 | 0.1326 | 688 | 320 | 0.2824 | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 66 / 88 |
| 2014 | frozen | no | 0.5000 | 0.1290 | 644 | 248 | 0.2788 | 0.7220 | [0.4414, 0.8625] | 0.9746 | 0.9693 | 63 / 83 |
| 2015 | relabelled | no | 0.5000 | 0.4906 | 545 | 457 | 0.3730 | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 27 / 57 |
| 2015 | frozen | no | 0.5000 | 0.5074 | 551 | 476 | 0.4066 | 0.5365 | [0.3109, 0.7080] | 0.9815 | 0.9804 | 24 / 51 |
| 2016 | relabelled | no | 0.5000 | 0.4969 | 94 | 109 | 0.4393 | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 3 / 8 |
| 2016 | frozen | no | 0.5000 | 0.5269 | 76 | 112 | 0.4199 | 0.4043 | [0.0000, 0.5249] | 0.9950 | 0.9958 | 2 / 7 |
| 2017 | relabelled | no | 0.5000 | 0.2196 | 177 | 27 | 0.6679 | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 3 / 6 |
| 2017 | frozen | no | 0.5000 | 0.2983 | 182 | 43 | 0.7194 | 0.8089 | [0.0000, 0.9691] | 0.9942 | 0.9870 | 2 / 6 |
| 2022 | relabelled | yes | 0.1996 | 0.2361 | 1056 | 1178 | 0.4822 | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 32 / 72 |
| 2022 | frozen | yes | 0.1447 | 0.3382 | 221 | 1111 | 0.5249 | 0.1659 | [0.0725, 0.2543] | 0.9742 | 0.9917 | 2 / 16 |
| 2023 | relabelled | no | 0.5000 | 0.4461 | 1587 | 2136 | 0.3879 | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 68 / 159 |
| 2023 | frozen | no | 0.5000 | 0.1710 | 79 | 106 | 0.1012 | 0.4270 | [0.0968, 0.7441] | 0.9866 | 0.9871 | 30 / 38 |

## Alert tier at precision target 0.30

| year | labels | fallback | calibration precision | calibration recall | TP | FP | recall | precision | 95% interval | accuracy | always-negative accuracy | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled | no | 0.3000 | 0.5533 | 1401 | 2480 | 0.5751 | 0.3610 | [0.2396, 0.4873] | 0.9551 | 0.9689 | 32 / 88 |
| 2014 | frozen | no | 0.3000 | 0.6014 | 1371 | 2436 | 0.5935 | 0.3601 | [0.2211, 0.4974] | 0.9551 | 0.9693 | 29 / 83 |
| 2015 | relabelled | no | 0.3000 | 0.6560 | 1065 | 2140 | 0.7290 | 0.3323 | [0.2160, 0.4524] | 0.9641 | 0.9793 | 9 / 57 |
| 2015 | frozen | no | 0.3000 | 0.6571 | 986 | 1953 | 0.7277 | 0.3355 | [0.2038, 0.4564] | 0.9664 | 0.9804 | 8 / 51 |
| 2016 | relabelled | no | 0.3000 | 0.7707 | 178 | 740 | 0.8318 | 0.1939 | [0.0000, 0.3532] | 0.9820 | 0.9950 | 1 / 8 |
| 2016 | frozen | no | 0.3000 | 0.7911 | 152 | 684 | 0.8398 | 0.1818 | [0.0000, 0.3302] | 0.9834 | 0.9958 | 1 / 7 |
| 2017 | relabelled | no | 0.3002 | 0.5935 | 233 | 466 | 0.8792 | 0.3333 | [0.0000, 0.7200] | 0.9749 | 0.9866 | 1 / 6 |
| 2017 | frozen | no | 0.3000 | 0.5967 | 215 | 401 | 0.8498 | 0.3490 | [0.0000, 0.7524] | 0.9775 | 0.9870 | 1 / 6 |
| 2022 | relabelled | yes | 0.1996 | 0.2361 | 1056 | 1178 | 0.4822 | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 32 / 72 |
| 2022 | frozen | yes | 0.1447 | 0.3382 | 221 | 1111 | 0.5249 | 0.1659 | [0.0725, 0.2543] | 0.9742 | 0.9917 | 2 / 16 |
| 2023 | relabelled | no | 0.3000 | 0.7539 | 3049 | 7653 | 0.7453 | 0.2849 | [0.2373, 0.3350] | 0.9104 | 0.9578 | 31 / 159 |
| 2023 | frozen | no | 0.3003 | 0.2162 | 123 | 225 | 0.1575 | 0.3534 | [0.0842, 0.6050] | 0.9854 | 0.9871 | 28 / 38 |

## Watch tier (recall 0.90)

| year | labels | fallback | calibration precision | calibration recall | TP | FP | recall | precision | 95% interval | accuracy | always-negative accuracy | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled | no |  |  | 2146 | 9020 | 0.8810 | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 6 / 88 |
| 2014 | frozen | no |  |  | 2007 | 7634 | 0.8688 | 0.2082 | [0.1327, 0.2868] | 0.8945 | 0.9693 | 6 / 83 |
| 2015 | relabelled | no |  |  | 1396 | 8079 | 0.9555 | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 1 / 57 |
| 2015 | frozen | no |  |  | 1308 | 6294 | 0.9653 | 0.1721 | [0.1069, 0.2401] | 0.9083 | 0.9804 | 0 / 51 |
| 2016 | relabelled | no |  |  | 201 | 1722 | 0.9393 | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 0 / 8 |
| 2016 | frozen | no |  |  | 162 | 1303 | 0.8950 | 0.1106 | [0.0000, 0.2039] | 0.9692 | 0.9958 | 0 / 7 |
| 2017 | relabelled | no |  |  | 243 | 1058 | 0.9170 | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1 / 6 |
| 2017 | frozen | no |  |  | 235 | 1035 | 0.9289 | 0.1850 | [0.0000, 0.4581] | 0.9461 | 0.9870 | 1 / 6 |
| 2022 | relabelled | no |  |  | 2024 | 11917 | 0.9242 | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 5 / 72 |
| 2022 | frozen | no |  |  | 414 | 8949 | 0.9834 | 0.0442 | [0.0222, 0.0724] | 0.8235 | 0.9917 | 0 / 16 |
| 2023 | relabelled | no |  |  | 3695 | 16022 | 0.9032 | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 10 / 159 |
| 2023 | frozen | no |  |  | 653 | 4852 | 0.8361 | 0.1186 | [0.0765, 0.1630] | 0.9175 | 0.9871 | 3 / 38 |

## Evaluation-year oracle (not deployable)

| year | precision target | frozen max recall | relabelled max recall |
| --- | --- | --- | --- |
| 2014 | 0.3 | 0.6693 | 0.6736 |
| 2014 | 0.5 | 0.4818 | 0.4598 |
| 2015 | 0.3 | 0.7889 | 0.7844 |
| 2015 | 0.5 | 0.4841 | 0.4661 |
| 2016 | 0.3 | 0.5801 | 0.6916 |
| 2016 | 0.5 | 0.3260 | 0.3224 |
| 2017 | 0.3 | 0.8972 | 0.8943 |
| 2017 | 0.5 | 0.8024 | 0.7887 |
| 2022 | 0.3 | 0.2280 | 0.7466 |
| 2022 | 0.5 | 0.1496 | 0.4662 |
| 2023 | 0.3 | 0.2458 | 0.7169 |
| 2023 | 0.5 | 0.0717 | 0.0176 |

## Reading

- `year_meets_primary`: 2014, 2015, 2017 on both label sets. 2016 misses on both (0.4043 and 0.4631, intervals
  from 0.0000); 2023 misses by 0.0737 instead of 0.0730 but now on 3723 alarm windows instead of 185; 2022 is a
  fallback year on both, with precision 0.4727 instead of 0.1659.
- The 2022 fallback has a new cause: the relabelled 2021 calibration year keeps only 377 positive windows after
  purging (the frozen one had 182), and its best precision at the recall floor is 0.1996. The rule is limited by a
  quiet calibration year, not by the 2022 ranking, whose oracle now reaches 0.50 at recall 0.4662.
- 2023 is the opposite case: the rule chooses a threshold that is precise on the relabelled 2022 calibration year
  (0.50 at recall 0.4461) and lands at 0.4263 in 2023, within 0.0737 of the target, while the 2023 oracle reaches
  0.50 only at recall 0.0176. The 2023 ranking still holds fewer separable positives than its calibration year.
- Watch tier: the relabelled watch tier reproduces the `relabelled_models` recall-0.90 result of the relabelling
  report in every year (2022 precision 0.1452, 2023 0.1874); the cycle-24 years move within their intervals.
- Accuracy above always-negative: no year of either label set at the watch tier; at the alert tier the same three
  years as before, 2022 and 2023 now 0.0018 and 0.0056 short instead of 0.0175 and 0.0005 (2023 was short on
  185 alarms).

## Limits

Adaptive description on inspected years; the relabelled labels are an association, not ground truth; counts are
overlapping windows, not flares. The old and new rows are measured on different window sets and the frozen rows
are copied, not recomputed. Precision at the alert tier in 2016 and 2017 rests on 8 and 6 positive runs and its
intervals reach 0.0000. The reserved test was not read; nothing here changes alerts or models.

## Reproduction

```sh
python -m scripts.audit_two_tier_relabelled --output artifacts/two_tier_relabelled_20261111_r1
```

Config sha256 `c769693a5cd0c531ff6c705fd613138392148313deef78fbf789d814f6ade10c`. Use new output directories; existing output is not overwritten.
