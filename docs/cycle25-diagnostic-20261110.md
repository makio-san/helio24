# Cycle-25 ranking diagnostic: why 2022–2023 are weaker (2026-11-10)

## Decision

Reading R1 of the [frozen protocol](../config/cycle25-diagnostic-v1.json) holds: the information that the 96
magnetic summaries carry about the next 24 hours fell in solar cycle 25; drift of the training distribution is not
the main cause. A HARP-grouped fit inside the 2022–2023 era, which sees that era's own future and is therefore a
ceiling, ranks no better than the walk-forward baseline (AP 0.1877 against 0.2800 in 2022, 0.2190 against 0.2206
in 2023). The best single raw summary ranks 2022 and 2023 at AP 0.2089 and 0.1823 against 0.4900 and 0.7216 in
2014 and 2017. Reading R2 (drift) is false and reading R3 (timing dominates) holds in no year. A cycle-25-aware
training protocol is not justified by this evidence. No model, threshold or alert is changed; the reserved
2024–2025 test was not accessed. The protocol was frozen and committed before any result.

## Why this review

The two-tier review showed that even a precision-targeted alert tier fails in 2022 and 2023, where the baseline's
AP is 0.2800 and 0.2206 against 0.4924–0.8117 in 2014, 2015 and 2017. The question was whether the model, the
training distribution, or the data itself is weaker in cycle 25.

## Method

Frozen baseline probabilities of the annual folds; evaluation-year windows joined to the frozen shards' 96
summaries. D1: composition per year. D2: decomposition of the baseline ranking into a region problem (maximum
probability per HARP against whether the HARP has any positive window) and a timing problem (window ranking
inside flaring HARPs only), plus the share of FP windows at the recall-0.90 watch threshold that come from HARPs
with no positive window in the year. D3: AP of every summary and its negation as a raw ranking; the best one and
`USFLUX__last` as a capacity proxy. D4: HARP-grouped 5-fold cross-validation of the unchanged walk-forward-v1
logistic and xgboost recipes inside each era (2014–2017 and 2022–2023), raw probabilities combined 0.45/0.55,
20 fits; a ceiling for the era, never deployable. The reference capacity median is the median
`USFLUX__last` of cycle-24 positive windows, 3.63e+22.

## D1 Composition

| year | windows | HARPs | flaring HARPs | positive windows | positive runs | positive share | median windows per flaring HARP | median USFLUX__last positive | median USFLUX__last all | positive share below cycle-24 median | mean missing_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 75228 | 629 | 44 | 2310 | 83 | 0.0307 | 260 | 4.34e+22 | 2.80e+21 | 0.4281 | 0.0139 |
| 2015 | 69138 | 599 | 24 | 1355 | 51 | 0.0196 | 274 | 3.18e+22 | 1.84e+21 | 0.5934 | 0.0138 |
| 2016 | 42987 | 357 | 4 | 181 | 7 | 0.0042 | 285 | 3.77e+22 | 1.63e+21 | 0.4641 | 0.0155 |
| 2017 | 19529 | 163 | 3 | 253 | 6 | 0.0130 | 253 | 3.79e+22 | 2.24e+21 | 0.4466 | 0.0156 |
| 2022 | 50756 | 528 | 12 | 421 | 16 | 0.0083 | 193 | 3.86e+22 | 3.02e+21 | 0.4466 | 0.0167 |
| 2023 | 60366 | 703 | 27 | 781 | 38 | 0.0129 | 134 | 3.38e+22 | 2.53e+21 | 0.5493 | 0.0148 |

## D2 Decomposition of the baseline ranking

| year | overall AP | region AP | within-flaring-HARP AP | FP windows at watch threshold | FP share from never-flaring HARPs |
| --- | --- | --- | --- | --- | --- |
| 2014 | 0.5079 | 0.7618 | 0.5609 | 7634 | 0.4353 |
| 2015 | 0.4924 | 0.8266 | 0.5469 | 6294 | 0.5261 |
| 2016 | 0.3664 | 0.4958 | 0.4371 | 1303 | 0.6078 |
| 2017 | 0.8117 | 1.0000 | 0.8821 | 1035 | 0.7459 |
| 2022 | 0.2800 | 0.7187 | 0.3860 | 8949 | 0.8301 |
| 2023 | 0.2206 | 0.5951 | 0.4024 | 4852 | 0.7422 |

## D3 and D4 Ceilings

| year | walk-forward AP | best raw summary | best raw summary AP | USFLUX__last AP | within-era fit AP | within-era minus walk-forward |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.5079 | `TOTUSJH__mean` | 0.4900 | 0.4362 | 0.4270 | -0.0810 |
| 2015 | 0.4924 | `R_VALUE__mean` | 0.3960 | 0.2181 | 0.4569 | -0.0355 |
| 2016 | 0.3664 | `TOTFX__mean` | 0.4637 | 0.1407 | 0.2376 | -0.1289 |
| 2017 | 0.8117 | `TOTUSJH__mean` | 0.7216 | 0.5602 | 0.8011 | -0.0106 |
| 2022 | 0.2800 | `ABSNJZH__last` | 0.2089 | 0.1390 | 0.1877 | -0.0924 |
| 2023 | 0.2206 | `ABSNJZH__std` | 0.1823 | 0.0825 | 0.2190 | -0.0016 |

- D4: the within-era fit does not beat the walk-forward baseline in any year; in 2022 it is 0.0924 below and in
  2023 0.0016 below. The 2022–2023 era holds 1202 positive windows in 39 flaring HARPs, so a fit inside it is
  also small; this is why R1 is read as "not justified by this evidence" rather than "excluded".
- D3: the best raw summary falls from AP 0.49–0.72 (2014, 2017) to 0.21 and 0.18 (2022, 2023); the capacity
  proxy `USFLUX__last` falls from 0.44 and 0.56 to 0.14 and 0.08. The best features in cycle 25 are current-helicity
  summaries (`ABSNJZH`), not flux or current totals.
- D2: the region problem is still partly solvable in cycle 25 (region AP 0.72 and 0.60), but 83% and 74% of FP
  windows come from HARPs that never flare in the year, against 44% and 53% in 2014 and 2015. Cycle 25 has many
  regions that look flare-capable by the summaries and do not flare within the year: 528 and 703 HARPs with 12
  and 27 flaring, against 629 with 44 in 2014.
- Positive windows in cycle 25 are not from smaller regions: the median capacity of positive windows is
  3.86e+22 and 3.38e+22 against 3.18e+22–4.34e+22 in cycle 24, and 45–55% lie below the cycle-24 median in every
  year. Flaring HARPs are observed for fewer windows (median 193 and 134 against 253–285).

## Limits

Already inspected years: adaptive development description, not an independent test. Counts are overlapping
forecast windows and groupings of them, not physical flares. The within-era ceiling uses only two years of
cycle 25 and is itself a small-sample estimate. Single-feature AP is a raw ranking without any fit. The
diagnostic bounds the 96 summaries, not other data about cycle 25.

## Reproduction

```sh
python -m scripts.audit_cycle25 --output artifacts/cycle25_diagnostic_20261110_r1
```

Config sha256 `e9466137c619a72ae420e017e59b1f38ce2e42f583f364b7d36225677e92543a`. Use new output directories; existing output is not overwritten.
