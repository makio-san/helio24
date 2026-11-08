# Operating point review: what relaxing the recall constraint buys

## Decision and scope

The [frozen review protocol](../config/operating-point-review-v1.json) was run once on the frozen baseline. For each
recall target from 0.95 down to 0.70 the threshold was selected on the prior calibration year only, exactly as
the project does at 0.95, and applied unchanged to the evaluation year (deployable curve). Deployable thresholds
were written to disk and hashed (SHA256 `bd4594e2ab0e5ebcdc58cc438b59f7a213828fa3dfdd5b5dfb9c7fcb0df3d6c0`) before any evaluation label was read. An oracle curve,
selected on the evaluation year itself, is reported only as an upper bound and is never deployable. No model or
threshold was changed and the reserved 2024–2025 test stayed closed. This is a decision aid, not a result that
promotes anything.

Findings:

1. Relaxing the target from 0.95 to 0.90 raises deployable precision from 0.040–0.156 to 0.044–0.208 and
   removes 1123 to 6253 false-alarm windows per year, at the cost of 0 to 3 more missed flare episodes
   (positive runs) per year. Precision 0.30 is not reached in any year at any target of 0.80 or higher.
2. The target transfers loosely. At target 0.90 the delivered recall ranges from 0.836 (2023) to 0.983
   (2022), because the calibration year and the evaluation year differ.
3. Even the oracle cannot reach precision 0.30 at a recall above 0.67 in 2014, 0.79 in 2015, 0.58 in 2016,
   0.23 in 2022 and 0.25 in 2023; only 2017 reaches it at 0.90. Precision 0.30 at high recall is therefore not a
   property this model and data can deliver, whatever the threshold rule.

## Summary: precision / recall / missed positive runs, deployable thresholds

| year | target 0.95 | target 0.90 | target 0.85 | target 0.80 |
| --- | --- | --- | --- | --- |
| 2014 | 0.136 / 0.945 / 3 | 0.208 / 0.869 / 6 | 0.243 / 0.810 / 9 | 0.263 / 0.748 / 14 |
| 2015 | 0.105 / 0.993 / 0 | 0.172 / 0.965 / 0 | 0.215 / 0.933 / 2 | 0.247 / 0.889 / 3 |
| 2016 | 0.071 / 0.972 / 0 | 0.111 / 0.895 / 0 | 0.144 / 0.873 / 0 | 0.176 / 0.845 / 1 |
| 2017 | 0.156 / 0.937 / 1 | 0.185 / 0.929 / 1 | 0.241 / 0.925 / 1 | 0.263 / 0.925 / 1 |
| 2022 | 0.040 / 0.986 / 0 | 0.044 / 0.983 / 0 | 0.052 / 0.974 / 0 | 0.063 / 0.960 / 0 |
| 2023 | 0.103 / 0.885 / 2 | 0.119 / 0.836 / 3 | 0.128 / 0.821 / 5 | 0.136 / 0.780 / 5 |

## Recall needed for a precision target (oracle upper bound)

The highest recall at which any threshold reaches the precision target on the evaluation year itself. These
values are not deployable; a prior-year rule can only do worse.

| year | max recall at precision 0.20 (oracle) | max recall at precision 0.30 (oracle) |
| --- | --- | --- |
| 2014 | 0.8797 | 0.6693 |
| 2015 | 0.9417 | 0.7889 |
| 2016 | 0.8343 | 0.5801 |
| 2017 | 0.9289 | 0.8972 |
| 2022 | 0.4323 | 0.2280 |
| 2023 | 0.4046 | 0.2458 |

## Deployable curve

| year | recall target | threshold | recall | precision | FP windows | episode precision | missed positive runs | positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.950 | 0.011475 | 0.9455 | 0.1359 | 13886 | 0.0977 | 3 | 83 |
| 2014 | 0.925 | 0.014002 | 0.9394 | 0.1462 | 12671 | 0.1037 | 4 | 83 |
| 2014 | 0.900 | 0.032374 | 0.8688 | 0.2082 | 7634 | 0.1636 | 6 | 83 |
| 2014 | 0.875 | 0.040884 | 0.8359 | 0.2278 | 6547 | 0.1731 | 9 | 83 |
| 2014 | 0.850 | 0.047627 | 0.8104 | 0.2429 | 5835 | 0.2010 | 9 | 83 |
| 2014 | 0.800 | 0.060577 | 0.7481 | 0.2631 | 4840 | 0.2114 | 14 | 83 |
| 2014 | 0.750 | 0.079256 | 0.6883 | 0.2879 | 3932 | 0.1944 | 24 | 83 |
| 2014 | 0.700 | 0.095980 | 0.6593 | 0.3132 | 3339 | 0.2138 | 24 | 83 |
| 2015 | 0.950 | 0.018839 | 0.9934 | 0.1052 | 11453 | 0.0669 | 0 | 51 |
| 2015 | 0.925 | 0.029956 | 0.9889 | 0.1385 | 8334 | 0.0850 | 0 | 51 |
| 2015 | 0.900 | 0.040687 | 0.9653 | 0.1721 | 6294 | 0.1138 | 0 | 51 |
| 2015 | 0.875 | 0.047388 | 0.9446 | 0.1930 | 5351 | 0.1272 | 1 | 51 |
| 2015 | 0.850 | 0.055043 | 0.9328 | 0.2154 | 4604 | 0.1433 | 2 | 51 |
| 2015 | 0.800 | 0.068355 | 0.8886 | 0.2472 | 3667 | 0.1753 | 3 | 51 |
| 2015 | 0.750 | 0.085267 | 0.8266 | 0.2771 | 2922 | 0.2278 | 4 | 51 |
| 2015 | 0.700 | 0.103241 | 0.7756 | 0.3098 | 2341 | 0.2442 | 5 | 51 |
| 2016 | 0.950 | 0.030831 | 0.9724 | 0.0714 | 2289 | 0.0196 | 0 | 7 |
| 2016 | 0.925 | 0.038928 | 0.9392 | 0.0872 | 1780 | 0.0281 | 0 | 7 |
| 2016 | 0.900 | 0.053871 | 0.8950 | 0.1106 | 1303 | 0.0347 | 0 | 7 |
| 2016 | 0.875 | 0.065347 | 0.8785 | 0.1304 | 1060 | 0.0526 | 0 | 7 |
| 2016 | 0.850 | 0.072957 | 0.8729 | 0.1440 | 939 | 0.0488 | 0 | 7 |
| 2016 | 0.800 | 0.090191 | 0.8453 | 0.1761 | 716 | 0.0297 | 1 | 7 |
| 2016 | 0.750 | 0.106615 | 0.8343 | 0.2103 | 567 | 0.0449 | 1 | 7 |
| 2016 | 0.700 | 0.132014 | 0.7238 | 0.2500 | 393 | 0.0952 | 1 | 7 |
| 2017 | 0.950 | 0.012000 | 0.9368 | 0.1555 | 1287 | 0.0588 | 1 | 6 |
| 2017 | 0.925 | 0.014660 | 0.9328 | 0.1628 | 1214 | 0.0581 | 1 | 6 |
| 2017 | 0.900 | 0.021853 | 0.9289 | 0.1850 | 1035 | 0.0781 | 1 | 6 |
| 2017 | 0.875 | 0.027813 | 0.9289 | 0.1990 | 946 | 0.0893 | 1 | 6 |
| 2017 | 0.850 | 0.046587 | 0.9249 | 0.2407 | 738 | 0.0806 | 1 | 6 |
| 2017 | 0.800 | 0.056778 | 0.9249 | 0.2629 | 656 | 0.0877 | 1 | 6 |
| 2017 | 0.750 | 0.066097 | 0.9170 | 0.2822 | 590 | 0.1373 | 1 | 6 |
| 2017 | 0.700 | 0.078902 | 0.9012 | 0.2973 | 539 | 0.1915 | 1 | 6 |
| 2022 | 0.950 | 0.008994 | 0.9857 | 0.0396 | 10072 | 0.0257 | 0 | 16 |
| 2022 | 0.925 | 0.009519 | 0.9857 | 0.0409 | 9734 | 0.0268 | 0 | 16 |
| 2022 | 0.900 | 0.010960 | 0.9834 | 0.0442 | 8949 | 0.0316 | 0 | 16 |
| 2022 | 0.875 | 0.011933 | 0.9834 | 0.0464 | 8507 | 0.0320 | 0 | 16 |
| 2022 | 0.850 | 0.014626 | 0.9739 | 0.0516 | 7536 | 0.0376 | 0 | 16 |
| 2022 | 0.800 | 0.020519 | 0.9596 | 0.0625 | 6057 | 0.0361 | 0 | 16 |
| 2022 | 0.750 | 0.024312 | 0.9572 | 0.0710 | 5276 | 0.0407 | 0 | 16 |
| 2022 | 0.700 | 0.027828 | 0.9549 | 0.0787 | 4706 | 0.0460 | 0 | 16 |
| 2023 | 0.950 | 0.018203 | 0.8848 | 0.1034 | 5992 | 0.0842 | 2 | 38 |
| 2023 | 0.925 | 0.021697 | 0.8553 | 0.1122 | 5284 | 0.0933 | 2 | 38 |
| 2023 | 0.900 | 0.024213 | 0.8361 | 0.1186 | 4852 | 0.0905 | 3 | 38 |
| 2023 | 0.875 | 0.026764 | 0.8220 | 0.1250 | 4496 | 0.0967 | 5 | 38 |
| 2023 | 0.850 | 0.027953 | 0.8207 | 0.1285 | 4349 | 0.0956 | 5 | 38 |
| 2023 | 0.800 | 0.031936 | 0.7798 | 0.1356 | 3881 | 0.1080 | 5 | 38 |
| 2023 | 0.750 | 0.039919 | 0.7081 | 0.1499 | 3136 | 0.1243 | 7 | 38 |
| 2023 | 0.700 | 0.046607 | 0.6569 | 0.1580 | 2733 | 0.1458 | 7 | 38 |

## Oracle curve (not deployable)

| year | recall target | threshold | recall | precision | FP windows | episode precision | missed positive runs | positive runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.950 | 0.009938 | 0.9502 | 0.1290 | 14825 | 0.0889 | 3 | 83 |
| 2014 | 0.925 | 0.018390 | 0.9251 | 0.1643 | 10873 | 0.1157 | 4 | 83 |
| 2014 | 0.900 | 0.025467 | 0.9000 | 0.1886 | 8947 | 0.1358 | 5 | 83 |
| 2014 | 0.875 | 0.030734 | 0.8753 | 0.2037 | 7902 | 0.1552 | 6 | 83 |
| 2014 | 0.850 | 0.036988 | 0.8502 | 0.2195 | 6985 | 0.1712 | 9 | 83 |
| 2014 | 0.800 | 0.049481 | 0.8000 | 0.2453 | 5687 | 0.2062 | 10 | 83 |
| 2014 | 0.750 | 0.060419 | 0.7502 | 0.2629 | 4858 | 0.2043 | 14 | 83 |
| 2014 | 0.700 | 0.074329 | 0.7000 | 0.2813 | 4131 | 0.1950 | 22 | 83 |
| 2015 | 0.950 | 0.045661 | 0.9506 | 0.1872 | 5592 | 0.1154 | 1 | 51 |
| 2015 | 0.925 | 0.056711 | 0.9255 | 0.2188 | 4477 | 0.1457 | 2 | 51 |
| 2015 | 0.900 | 0.064965 | 0.9004 | 0.2398 | 3867 | 0.1691 | 3 | 51 |
| 2015 | 0.875 | 0.072073 | 0.8753 | 0.2548 | 3469 | 0.1951 | 3 | 51 |
| 2015 | 0.850 | 0.078782 | 0.8502 | 0.2659 | 3181 | 0.2199 | 3 | 51 |
| 2015 | 0.800 | 0.092725 | 0.8000 | 0.2912 | 2638 | 0.2379 | 5 | 51 |
| 2015 | 0.750 | 0.111208 | 0.7506 | 0.3222 | 2139 | 0.2680 | 7 | 51 |
| 2015 | 0.700 | 0.130878 | 0.7004 | 0.3486 | 1773 | 0.2404 | 9 | 51 |
| 2016 | 0.950 | 0.037092 | 0.9503 | 0.0839 | 1878 | 0.0221 | 0 | 7 |
| 2016 | 0.925 | 0.047214 | 0.9282 | 0.1016 | 1485 | 0.0426 | 0 | 7 |
| 2016 | 0.900 | 0.052647 | 0.9006 | 0.1086 | 1338 | 0.0340 | 0 | 7 |
| 2016 | 0.875 | 0.066158 | 0.8785 | 0.1314 | 1051 | 0.0522 | 0 | 7 |
| 2016 | 0.850 | 0.086855 | 0.8508 | 0.1698 | 753 | 0.0381 | 0 | 7 |
| 2016 | 0.800 | 0.116495 | 0.8011 | 0.2283 | 490 | 0.0811 | 1 | 7 |
| 2016 | 0.750 | 0.122794 | 0.7514 | 0.2317 | 451 | 0.1000 | 1 | 7 |
| 2016 | 0.700 | 0.138977 | 0.7017 | 0.2602 | 361 | 0.0833 | 1 | 7 |
| 2017 | 0.950 | 0.006340 | 0.9526 | 0.1273 | 1652 | 0.0485 | 1 | 6 |
| 2017 | 0.925 | 0.036523 | 0.9289 | 0.2234 | 817 | 0.0820 | 1 | 6 |
| 2017 | 0.900 | 0.079505 | 0.9012 | 0.2980 | 537 | 0.1875 | 1 | 6 |
| 2017 | 0.875 | 0.086755 | 0.8775 | 0.3025 | 512 | 0.1591 | 1 | 6 |
| 2017 | 0.850 | 0.105767 | 0.8538 | 0.3349 | 429 | 0.1176 | 1 | 6 |
| 2017 | 0.800 | 0.191812 | 0.8024 | 0.5232 | 185 | 0.1944 | 2 | 6 |
| 2017 | 0.750 | 0.295983 | 0.7510 | 0.7631 | 59 | 0.3158 | 2 | 6 |
| 2017 | 0.700 | 0.369739 | 0.7036 | 0.8476 | 32 | 0.5714 | 2 | 6 |
| 2022 | 0.950 | 0.033534 | 0.9501 | 0.0903 | 4032 | 0.0540 | 0 | 16 |
| 2022 | 0.925 | 0.040275 | 0.9264 | 0.1022 | 3427 | 0.0603 | 0 | 16 |
| 2022 | 0.900 | 0.044162 | 0.9002 | 0.1083 | 3119 | 0.0787 | 0 | 16 |
| 2022 | 0.875 | 0.047001 | 0.8765 | 0.1116 | 2937 | 0.0791 | 0 | 16 |
| 2022 | 0.850 | 0.049326 | 0.8504 | 0.1140 | 2783 | 0.0827 | 0 | 16 |
| 2022 | 0.800 | 0.053513 | 0.8005 | 0.1195 | 2483 | 0.0814 | 1 | 16 |
| 2022 | 0.750 | 0.062180 | 0.7506 | 0.1374 | 1984 | 0.0943 | 2 | 16 |
| 2022 | 0.700 | 0.067579 | 0.7007 | 0.1443 | 1750 | 0.1313 | 2 | 16 |
| 2023 | 0.950 | 0.009311 | 0.9501 | 0.0796 | 8577 | 0.0679 | 0 | 38 |
| 2023 | 0.925 | 0.012760 | 0.9257 | 0.0900 | 7308 | 0.0794 | 0 | 38 |
| 2023 | 0.900 | 0.016103 | 0.9001 | 0.0985 | 6433 | 0.0887 | 1 | 38 |
| 2023 | 0.875 | 0.019212 | 0.8758 | 0.1061 | 5761 | 0.0839 | 2 | 38 |
| 2023 | 0.850 | 0.022520 | 0.8502 | 0.1145 | 5137 | 0.0948 | 2 | 38 |
| 2023 | 0.800 | 0.029984 | 0.8003 | 0.1324 | 4095 | 0.1018 | 5 | 38 |
| 2023 | 0.750 | 0.035614 | 0.7503 | 0.1428 | 3518 | 0.1190 | 5 | 38 |
| 2023 | 0.700 | 0.041239 | 0.7004 | 0.1530 | 3029 | 0.1269 | 7 | 38 |

## How to read this

- Window recall counts overlapping hourly windows; a missed positive run is a flare episode for which no window
  alarmed. The review should weigh missed runs, not only window recall. At target 0.80 the baseline misses 14
  of 83 runs in 2014 against 3 at 0.95; in 2022 it misses none at any target.
- The years differ strongly: 2022 and 2023 have the lowest precision at every target, and 2017 the highest.
  A single project-wide operating point hides this.
- Lower targets concentrate alarms on the strongest regions, so episode precision rises faster than window
  precision in some years (2014: 0.098 at 0.95, 0.201 at 0.85).

## Limits

- Adaptive development description on already inspected years, not an independent test. Counts are overlapping
  forecast windows and groupings of them, not physical flares.
- No uncertainty intervals are given; the curve is descriptive and no acceptance rule applies.
- Thresholds at lower targets are selected from the same calibration year with the same rule; their transfer is
  as loose as the control's, as the delivered recall column shows.

## Reproduction

```sh
python scripts/audit_operating_point.py --output artifacts/operating_point_review_20261109_r1
python -m pytest -q tests/test_operating_point.py
```
