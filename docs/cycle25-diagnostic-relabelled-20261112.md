# Cycle-25 ranking diagnostic on the adopted relabelled pipeline (2026-11-12)

## Decision

Development basis: the relabelled table `artifacts/relabelled_development_20261111_r1` and the adopted pipeline
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)); the basis changed on 2026-11-12 because the
frozen labels covered under 30% of the mapped 2022–2023 M/X flares. This report repeats the
[first cycle-25 diagnostic](cycle25-diagnostic-20261110.md) on that basis under
[`config/cycle25-diagnostic-v2.json`](../config/cycle25-diagnostic-v2.json), frozen and committed before any result.

Three findings:

- The label correction removed a large part of the cycle-25 deficit that the first diagnostic described. Walk-forward AP
  rose from 0.2800 and 0.2206 to 0.4622 and 0.3626, the best raw summary from 0.2089 and
  0.1823 to 0.3984 and 0.3254, and region AP from 0.7187 and 0.5951 to 0.8315 and
  0.8655, which is at the cycle-24 level (0.7600 and 0.8264 in 2014 and 2015).
- By the frozen rule the "information fell" statement of the first diagnostic still stands, in a weaker form: the
  best raw summary and the within-era fit do not both reach the lowest 2014, 2015 and 2017 value in both years
  (best summary 0.3984 and 0.3254 against a floor of 0.3895; within-era fit 0.3590 and 0.3402 against
  0.4487). R1 holds, R2 (drift) is false, R3 (timing dominates) holds in no year.
- The remaining alert-tier gap is a timing problem inside flaring regions, not a region problem: only 0.0823 and
  0.1320 of alert FP windows in 2022 and 2023 come from HARPs with no positive window in the year, while
  0.7139 and 0.7561 lie within 72 hours of a positive window of the same HARP. The within-flaring-HARP AP
  is 0.4968 and 0.4057.

A cycle-25-aware training protocol is not justified by this evidence. No model, threshold or alert is changed; the
dashboard threshold in `app.py` is untouched; the reserved 2024–2025 test was not accessed.

## Operating point on this basis

Copied from `artifacts/walk_forward_v2_20261112_r1/metrics.csv`; frozen rows are the frozen-label reference of
that run. The two label sets are measured on different window sets and are not pooled. 2022 is an alert fallback
year.

### Alert tier (prior-year precision 0.50, recall floor 0.10)

| year | labels | fallback | recall | precision | accuracy | always-negative accuracy | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled | no | 0.2824 | 0.6825 | 0.9736 | 0.9689 | 66 / 88 |
| 2014 | frozen | no | 0.2788 | 0.7220 | 0.9746 | 0.9693 | 63 / 83 |
| 2015 | relabelled | no | 0.3730 | 0.5439 | 0.9805 | 0.9793 | 27 / 57 |
| 2015 | frozen | no | 0.4066 | 0.5365 | 0.9815 | 0.9804 | 24 / 51 |
| 2016 | relabelled | no | 0.4393 | 0.4631 | 0.9947 | 0.9950 | 3 / 8 |
| 2016 | frozen | no | 0.4199 | 0.4043 | 0.9950 | 0.9958 | 2 / 7 |
| 2017 | relabelled | no | 0.6679 | 0.8676 | 0.9942 | 0.9866 | 3 / 6 |
| 2017 | frozen | no | 0.7194 | 0.8089 | 0.9942 | 0.9870 | 2 / 6 |
| 2022 | relabelled | yes | 0.4822 | 0.4727 | 0.9648 | 0.9666 | 32 / 72 |
| 2022 | frozen | yes | 0.5249 | 0.1659 | 0.9742 | 0.9917 | 2 / 16 |
| 2023 | relabelled | no | 0.3879 | 0.4263 | 0.9522 | 0.9578 | 68 / 159 |
| 2023 | frozen | no | 0.1012 | 0.4270 | 0.9866 | 0.9871 | 30 / 38 |

### Watch tier (prior-year recall 0.90)

| year | labels | fallback | recall | precision | accuracy | always-negative accuracy | missed / positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled |  | 0.8810 | 0.1922 | 0.8812 | 0.9689 | 6 / 88 |
| 2014 | frozen |  | 0.8688 | 0.2082 | 0.8945 | 0.9693 | 6 / 83 |
| 2015 | relabelled |  | 0.9555 | 0.1473 | 0.8846 | 0.9793 | 1 / 57 |
| 2015 | frozen |  | 0.9653 | 0.1721 | 0.9083 | 0.9804 | 0 / 51 |
| 2016 | relabelled |  | 0.9393 | 0.1045 | 0.9598 | 0.9950 | 0 / 8 |
| 2016 | frozen |  | 0.8950 | 0.1106 | 0.9692 | 0.9958 | 0 / 7 |
| 2017 | relabelled |  | 0.9170 | 0.1868 | 0.9456 | 0.9866 | 1 / 6 |
| 2017 | frozen |  | 0.9289 | 0.1850 | 0.9461 | 0.9870 | 1 / 6 |
| 2022 | relabelled |  | 0.9242 | 0.1452 | 0.8158 | 0.9666 | 5 / 72 |
| 2022 | frozen |  | 0.9834 | 0.0442 | 0.8235 | 0.9917 | 0 / 16 |
| 2023 | relabelled |  | 0.9032 | 0.1874 | 0.8307 | 0.9578 | 10 / 159 |
| 2023 | frozen |  | 0.8361 | 0.1186 | 0.9175 | 0.9871 | 3 / 38 |

## Method

Stored `ensemble` probabilities of the adopted annual folds; evaluation-year windows joined to the 96 summaries of
the relabelled table. D1–D4 are the measures of `config/cycle25-diagnostic-v1.json`, computed by the unchanged
functions of `scripts/audit_cycle25.py`: composition; decomposition into a region problem (maximum probability per
HARP against whether the HARP has any positive window) and a timing problem (window ranking inside flaring HARPs),
with the FP share from never-flaring HARPs at each year's stored watch threshold; AP of every raw summary and its
negation; and a HARP-grouped 5-fold fit of the unchanged walk-forward-v1 recipes inside each era, raw
probabilities combined 0.45/0.55, 20 fits, a ceiling that is never deployable. D5 is new and was frozen with the
protocol: at each year's stored alert threshold, the share of FP windows from never-flaring HARPs and the share
within 72 hours of a positive window of the same HARP. Frozen-label rows are copied unchanged from
`artifacts/cycle25_diagnostic_20261110_r1`; nothing was recomputed on frozen labels. The reference capacity median
(cycle-24 positive windows, `USFLUX__last`) is 3.54e+22.

## D1 Composition

| year | labels | windows | HARPs | flaring HARPs | positive windows | positive runs | positive share | median windows per flaring HARP | median USFLUX__last positive | median USFLUX__last all | positive share below cycle-24 median | mean missing_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled | 78351 | 637 | 45 | 2436 | 88 | 0.0311 | 276.0 | 4.23e+22 | 2.77e+21 | 0.4257 | 0.0141 |
| 2014 | frozen | 75228 | 629 | 44 | 2310 | 83 | 0.0307 | 260.0 | 4.34e+22 | 2.80e+21 | 0.4281 | 0.0139 |
| 2015 | relabelled | 70554 | 600 | 28 | 1461 | 57 | 0.0207 | 275.5 | 3.09e+22 | 1.83e+21 | 0.5941 | 0.0140 |
| 2015 | frozen | 69138 | 599 | 24 | 1355 | 51 | 0.0196 | 274.5 | 3.18e+22 | 1.84e+21 | 0.5934 | 0.0138 |
| 2016 | relabelled | 43142 | 357 | 4 | 214 | 8 | 0.0050 | 301.5 | 3.77e+22 | 1.64e+21 | 0.4346 | 0.0155 |
| 2016 | frozen | 42987 | 357 | 4 | 181 | 7 | 0.0042 | 285.0 | 3.77e+22 | 1.63e+21 | 0.4641 | 0.0155 |
| 2017 | relabelled | 19843 | 163 | 3 | 265 | 6 | 0.0134 | 253.0 | 3.67e+22 | 2.28e+21 | 0.4566 | 0.0163 |
| 2017 | frozen | 19529 | 163 | 3 | 253 | 6 | 0.0130 | 253.0 | 3.79e+22 | 2.24e+21 | 0.4466 | 0.0156 |
| 2022 | relabelled | 65593 | 544 | 39 | 2190 | 72 | 0.0334 | 282.0 | 3.09e+22 | 3.05e+21 | 0.5475 | 0.0168 |
| 2022 | frozen | 50756 | 528 | 12 | 421 | 16 | 0.0083 | 193.0 | 3.86e+22 | 3.02e+21 | 0.4466 | 0.0167 |
| 2023 | relabelled | 96991 | 751 | 73 | 4091 | 159 | 0.0422 | 283.0 | 3.31e+22 | 2.82e+21 | 0.5363 | 0.0160 |
| 2023 | frozen | 60366 | 703 | 27 | 781 | 38 | 0.0129 | 134.0 | 3.38e+22 | 2.53e+21 | 0.5493 | 0.0148 |

## D2 Decomposition of the ranking

| year | labels | overall AP | region AP | within-flaring-HARP AP | FP windows at watch threshold | FP share from never-flaring HARPs |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled | 0.5015 | 0.7600 | 0.5528 | 9020 | 0.4425 |
| 2014 | frozen | 0.5079 | 0.7618 | 0.5609 | 7634 | 0.4353 |
| 2015 | relabelled | 0.4823 | 0.8264 | 0.5331 | 8079 | 0.5368 |
| 2015 | frozen | 0.4924 | 0.8266 | 0.5469 | 6294 | 0.5261 |
| 2016 | relabelled | 0.4060 | 0.6333 | 0.4853 | 1722 | 0.6533 |
| 2016 | frozen | 0.3664 | 0.4958 | 0.4371 | 1303 | 0.6078 |
| 2017 | relabelled | 0.7975 | 1.0000 | 0.8727 | 1058 | 0.7410 |
| 2017 | frozen | 0.8117 | 1.0000 | 0.8821 | 1035 | 0.7459 |
| 2022 | relabelled | 0.4622 | 0.8315 | 0.4968 | 11917 | 0.4922 |
| 2022 | frozen | 0.2800 | 0.7187 | 0.3860 | 8949 | 0.8301 |
| 2023 | relabelled | 0.3626 | 0.8655 | 0.4057 | 16022 | 0.3722 |
| 2023 | frozen | 0.2206 | 0.5951 | 0.4024 | 4852 | 0.7422 |

## D3 and D4 Ceilings

| year | labels | walk-forward AP | best raw summary | best raw summary AP | USFLUX__last AP | within-era fit AP | within-era minus walk-forward |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | relabelled | 0.5015 | `TOTUSJH__mean` | 0.4850 | 0.4306 | 0.4576 | -0.0440 |
| 2014 | frozen | 0.5079 | `TOTUSJH__mean` | 0.4900 | 0.4362 | 0.4270 | -0.0810 |
| 2015 | relabelled | 0.4823 | `R_VALUE__mean` | 0.3895 | 0.2093 | 0.4487 | -0.0336 |
| 2015 | frozen | 0.4924 | `R_VALUE__mean` | 0.3960 | 0.2181 | 0.4569 | -0.0355 |
| 2016 | relabelled | 0.4060 | `TOTFX__mean` | 0.4428 | 0.1506 | 0.2801 | -0.1259 |
| 2016 | frozen | 0.3664 | `TOTFX__mean` | 0.4637 | 0.1407 | 0.2376 | -0.1289 |
| 2017 | relabelled | 0.7975 | `ABSNJZH__std` | 0.7092 | 0.5192 | 0.7878 | -0.0098 |
| 2017 | frozen | 0.8117 | `TOTUSJH__mean` | 0.7216 | 0.5602 | 0.8011 | -0.0106 |
| 2022 | relabelled | 0.4622 | `ABSNJZH__std` | 0.3984 | 0.2808 | 0.3590 | -0.1032 |
| 2022 | frozen | 0.2800 | `ABSNJZH__last` | 0.2089 | 0.1390 | 0.1877 | -0.0924 |
| 2023 | relabelled | 0.3626 | `ABSNJZH__std` | 0.3254 | 0.2326 | 0.3402 | -0.0224 |
| 2023 | frozen | 0.2206 | `ABSNJZH__std` | 0.1823 | 0.0825 | 0.2190 | -0.0016 |

## D5 Origin of alert-tier false positives (relabelled)

| year | alert fallback | alert windows | alert FP windows | FP share from never-flaring HARPs | FP share within 72 h of a positive window of the same HARP |
| --- | --- | --- | --- | --- | --- |
| 2014 | no | 1008 | 320 | 0.1437 | 0.7063 |
| 2015 | no | 1002 | 457 | 0.0853 | 0.8249 |
| 2016 | no | 203 | 109 | 0.2569 | 0.5688 |
| 2017 | no | 204 | 27 | 0.1111 | 0.8889 |
| 2022 | yes | 2234 | 1178 | 0.0823 | 0.7139 |
| 2023 | no | 3723 | 2136 | 0.1320 | 0.7561 |

## Reading

- R1 (`R1_information_fell`): true. The within-era fit is -0.1032 (2022) and -0.0224 (2023) against the
  walk-forward AP, below the 0.10 limit in both years. R2 (`R2_drift`): false. Training on earlier years is not
  what holds cycle 25 back; the walk-forward model ranks 2022 and 2023 at least as well as a fit that sees the era
  itself.
- R3: no year has region AP at least 0.50 with within-flaring-HARP AP below 0.30. The frozen limit is not met,
  yet the direction is clear in cycle 25: region AP 0.8315 and 0.8655 against within-flaring-HARP AP
  0.4968 and 0.4057.
- Label effect: `first_diagnostic_information_statement` is `stands`. The best raw summary in 2022 (0.3984) reaches
  the cycle-24 floor (0.3895); 2023 (0.3254) does not, and the within-era fit reaches it in neither year. The
  deficit described on 2026-11-10 was roughly halved by the label correction, not removed.
- Composition changed with the labels: flaring HARPs in 2022 and 2023 rose from 12 and 27 to 39 and 73,
  positive runs from 16 and 38 to 72 and 159, and the share of watch-tier FP windows from
  never-flaring HARPs fell from 0.8301 and 0.7422 to 0.4922 and 0.3722. Many "regions that look
  flare-capable and do not flare" of the first diagnostic were flaring regions whose flares had not been attached.
- D5: in every year more than half of the alert FP windows (0.57 to 0.89) sit in flaring HARPs within 72 hours
  of a positive window. The alert tier raises its alarm on the right regions and misses the right day.

## What this means for the project goal

- More data about which region will flare is not what the alert tier lacks; the summaries already find the
  regions in cycle 25. A new data source is worth its cost only if it carries information about when a flaring
  region flares.
- The next candidate direction is timing information inside an active region, for example the region's own
  recent flare history from the GOES event list that the project already holds, or the change of the summaries
  over the preceding days. This needs its own frozen protocol with a fit budget and acceptance rule; it is a
  proposal here, not a result.
- The share of alert FP windows within 72 hours of a positive window also means that a strict 24-hour window
  label counts near-in-time alarms as fully wrong. That is a property of the target, reported here as is; the
  target is not changed.

## Limits

Already inspected years: adaptive development description, not an independent test. Counts are overlapping
forecast windows and groupings of them, not physical flares. Relabelled labels are an association by NOAA SGAS
region numbers and JSOC `NOAA_ARS`, not ground truth; 133 unassigned events remain excluded fail-closed. The
within-era ceiling uses two years of cycle 25 (6281 positive windows) and is itself a small-sample estimate.
Single-feature AP is a raw ranking without any fit. D5 is descriptive, has no limit and no reading in the protocol,
and its 72-hour span is a fixed choice made before results. The first run of the script stopped on a timestamp
type error in D5 before writing any result; the empty output directory was removed, the fix was committed and the
run was repeated. The diagnostic bounds the 96 summaries, not other data about cycle 25.

## Reproduction

```sh
python -m scripts.audit_cycle25_relabelled --output artifacts/cycle25_diagnostic_relabelled_20261112_r1
python -m pytest -q tests
```

Config sha256 `01a91bff4b899316d31c700194ab736fa2dda25e865eed5d0356e063dd63d89f`. Use new output directories; existing output is not overwritten.
