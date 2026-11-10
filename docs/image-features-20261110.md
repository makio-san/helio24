# SHARP Br map CNN features: acquisition and results (2026-11-10)

## Decision

Negative result. Adding a score learned by a small CNN from daily SHARP CEA radial-field (Br) maps to the 96
magnetic summaries does not raise precision at the project operating point (prior-year threshold at window recall
0.90). The primary candidate `image_lag24` meets the primary acceptance in 1 of 6 years, `flag_lag24` in 0 of
6, and the sensitivity candidates `image_same` and `flag_same` in 0 and 0 of 6. Accuracy stays below the
always-negative accuracy for every candidate in every year. No model is promoted and no alert or threshold is
changed. The reserved 2024–2025 test was not accessed. The acquisition protocol
[`config/sharp-maps-v1.json`](../config/sharp-maps-v1.json) was frozen and committed before any download, and the
experiment protocol [`config/image-features-v1.json`](../config/image-features-v1.json) before any candidate
result.

## Why this source

Nine earlier routes built on scalar summaries, context and issued flare history did not raise precision. The 96
summaries reduce each magnetogram to scalars; the map itself is the remaining information from the same
instrument. The download was approved by the user after a measured size estimate of 12.4 GB.

| item | value |
| --- | --- |
| series / segment | `hmi.sharp_cea_720s` / `Br` |
| index | `http://jsoc.stanford.edu/cgi-bin/ajax/jsoc_info` (`op=rs_list`) |
| files | `https://jsoc1.stanford.edu` |
| cadence | one record per HARP per day at `T_REC` 00:00:00 TAI |
| period | 2010-05-01 to 2023-12-31 |
| development HARP-days | 33249 |
| HARP-days with a record | 32717 |
| maps retrieved | 32717 |
| unavailable | 0 |
| raw bytes transferred | 12280512960 |
| maps without a valid pixel | 20 |
| maps used | 32697 |
| maps with NaN fraction above 0.5 | 878 |
| `records.jsonl` sha256 | `4a631c976c3f840dfbcf457718f59c35b68aaf8aa35a4864d4c9c83a1dbfb416` |

Each map is resized to 128 × 256 by an area mean over valid pixels and stored as float16 in gauss; cells without a
valid pixel are stored as 0. Raw FITS files were deleted after hashing; raw sha256, raw bytes, original width and
height and NaN fraction are kept per map. No record with `T_REC` on or after 2024-01-01 was indexed or requested.

## Method

Availability rules. `lag24` (primary): a window at forecast time t uses the latest map of the same HARP with
`T_REC` at or before t minus 24 hours and no older than t minus 48 hours. `same` (sensitivity only): the latest
map with `T_REC` at or before t and no older than t minus 24 hours. No publication latency was measured, so a pass
under `same` alone could justify only a latency measurement. A window without such a map has `map_available` = 0
and missing age and score; absence is never encoded as a quiet region.

CNN. Input is the map divided by 500 G and clipped to [-6, 6]. Four blocks of 3×3 convolution (16, 32, 64, 128
channels), batch normalisation, ReLU and 2×2 max pooling; global mean and max pooling joined with three scalars
(log(width/500), log(height/250), NaN fraction); dropout 0.3; one linear output. The label of a map is 1 if the
HARP has a positive training-role window with forecast time in [`T_REC`, `T_REC` + 48 h). Adam, learning rate
0.001, weight decay 0.0001, batch 64, 6 epochs, random left-right flip and polarity sign flip, seed 24. Stacking
uses three folds by HARP number modulo 3 inside the training role: a training-role HARP gets the score of the fold
model that never saw it; calibration and evaluation HARPs get the mean logit of the three fold models. No
calibration or evaluation label reaches the CNN.

Features per rule: `map_available_<rule>`, `map_age_hours_<rule>`, `cnn_logit_<rule>`. `flag_<rule>` refits the
unchanged `config/walk-forward-v1.json` recipes on the 96 summaries plus the first two; `image_<rule>` adds
`cnn_logit_<rule>`. `control` is the frozen baseline without refit. Thresholds come from calibration-year
probabilities at window recall 0.90 and were hashed before any evaluation label was read. No hyperparameter
search; 18 CNN fits and 48 constituent fits; device `mps`.

Evaluation-year map coverage:

| year | evaluation windows | map share lag24 | map share same | positive windows with a map lag24 | positive windows with a map same |
| --- | --- | --- | --- | --- | --- |
| 2014 | 75228 | 0.8907 | 0.9848 | 0.9498 | 0.9879 |
| 2015 | 69138 | 0.8926 | 0.9919 | 0.9365 | 0.9801 |
| 2016 | 42987 | 0.8572 | 0.9820 | 0.8785 | 1.0000 |
| 2017 | 19529 | 0.8390 | 0.9709 | 1.0000 | 1.0000 |
| 2022 | 50756 | 0.8604 | 0.9945 | 0.9121 | 1.0000 |
| 2023 | 60366 | 0.8401 | 1.0000 | 0.7823 | 1.0000 |

CNN training sets (range over the three folds):

| year | maps | positive maps | final loss |
| --- | --- | --- | --- |
| 2014 | 4884–5276 | 157–188 | 0.0938–0.0993 |
| 2015 | 7567–7843 | 228–266 | 0.0938–0.1006 |
| 2016 | 10279–10756 | 380–405 | 0.0968–0.1085 |
| 2017 | 12910–13143 | 455–502 | 0.0909–0.1053 |
| 2022 | 15769–16129 | 479–526 | 0.0825–0.0922 |
| 2023 | 16814–17077 | 494–544 | 0.0808–0.0917 |

## Results

| year | candidate | TP | FP | FN | recall | precision | accuracy | always-negative accuracy | episode precision | positive runs alarmed | AP | Brier | log loss | primary met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 2007 | 7634 | 303 | 0.8688 | 0.2082 | 0.8945 | 0.9693 | 0.1636 | 77/83 | 0.5079 | 0.0207 | 0.0765 |  |
| 2014 | flag_lag24 | 1996 | 7381 | 314 | 0.8641 | 0.2129 | 0.8977 | 0.9693 | 0.1685 | 76/83 | 0.5086 | 0.0206 | 0.0765 | no |
| 2014 | image_lag24 | 1992 | 7585 | 318 | 0.8623 | 0.2080 | 0.8949 | 0.9693 | 0.1549 | 76/83 | 0.5092 | 0.0206 | 0.0765 | no |
| 2014 | flag_same | 2002 | 7600 | 308 | 0.8667 | 0.2085 | 0.8949 | 0.9693 | 0.1601 | 76/83 | 0.5074 | 0.0207 | 0.0766 | no |
| 2014 | image_same | 2002 | 7584 | 308 | 0.8667 | 0.2088 | 0.8951 | 0.9693 | 0.1584 | 76/83 | 0.5077 | 0.0207 | 0.0765 | no |
| 2015 | control | 1308 | 6294 | 47 | 0.9653 | 0.1721 | 0.9083 | 0.9804 | 0.1138 | 51/51 | 0.4924 | 0.0136 | 0.0478 |  |
| 2015 | flag_lag24 | 1309 | 6311 | 46 | 0.9661 | 0.1718 | 0.9081 | 0.9804 | 0.1128 | 51/51 | 0.4934 | 0.0136 | 0.0479 | no |
| 2015 | image_lag24 | 1321 | 6444 | 34 | 0.9749 | 0.1701 | 0.9063 | 0.9804 | 0.1065 | 51/51 | 0.4953 | 0.0135 | 0.0477 | no |
| 2015 | flag_same | 1308 | 6272 | 47 | 0.9653 | 0.1726 | 0.9086 | 0.9804 | 0.1125 | 51/51 | 0.4951 | 0.0136 | 0.0478 | no |
| 2015 | image_same | 1318 | 6526 | 37 | 0.9727 | 0.1680 | 0.9051 | 0.9804 | 0.1093 | 51/51 | 0.4840 | 0.0137 | 0.0482 | no |
| 2016 | control | 162 | 1303 | 19 | 0.8950 | 0.1106 | 0.9692 | 0.9958 | 0.0347 | 7/7 | 0.3664 | 0.0033 | 0.0145 |  |
| 2016 | flag_lag24 | 161 | 1300 | 20 | 0.8895 | 0.1102 | 0.9693 | 0.9958 | 0.0342 | 7/7 | 0.3648 | 0.0033 | 0.0146 | no |
| 2016 | image_lag24 | 161 | 1293 | 20 | 0.8895 | 0.1107 | 0.9695 | 0.9958 | 0.0350 | 7/7 | 0.3317 | 0.0033 | 0.0144 | yes |
| 2016 | flag_same | 162 | 1314 | 19 | 0.8950 | 0.1098 | 0.9690 | 0.9958 | 0.0338 | 7/7 | 0.3648 | 0.0033 | 0.0146 | no |
| 2016 | image_same | 161 | 1341 | 20 | 0.8895 | 0.1072 | 0.9683 | 0.9958 | 0.0352 | 7/7 | 0.3549 | 0.0033 | 0.0143 | no |
| 2017 | control | 235 | 1035 | 18 | 0.9289 | 0.1850 | 0.9461 | 0.9870 | 0.0781 | 5/6 | 0.8117 | 0.0049 | 0.0205 |  |
| 2017 | flag_lag24 | 236 | 1093 | 17 | 0.9328 | 0.1776 | 0.9432 | 0.9870 | 0.0649 | 5/6 | 0.8117 | 0.0049 | 0.0205 | no |
| 2017 | image_lag24 | 235 | 1051 | 18 | 0.9289 | 0.1827 | 0.9453 | 0.9870 | 0.0735 | 5/6 | 0.8156 | 0.0049 | 0.0210 | no |
| 2017 | flag_same | 235 | 1024 | 18 | 0.9289 | 0.1867 | 0.9466 | 0.9870 | 0.0725 | 5/6 | 0.8129 | 0.0049 | 0.0204 | no |
| 2017 | image_same | 234 | 1035 | 19 | 0.9249 | 0.1844 | 0.9460 | 0.9870 | 0.0685 | 5/6 | 0.8014 | 0.0051 | 0.0212 | no |
| 2022 | control | 414 | 8949 | 7 | 0.9834 | 0.0442 | 0.8235 | 0.9917 | 0.0316 | 16/16 | 0.2800 | 0.0071 | 0.0292 |  |
| 2022 | flag_lag24 | 414 | 9024 | 7 | 0.9834 | 0.0439 | 0.8221 | 0.9917 | 0.0311 | 16/16 | 0.2794 | 0.0071 | 0.0292 | no |
| 2022 | image_lag24 | 414 | 9042 | 7 | 0.9834 | 0.0438 | 0.8217 | 0.9917 | 0.0312 | 16/16 | 0.2740 | 0.0071 | 0.0293 | no |
| 2022 | flag_same | 414 | 8956 | 7 | 0.9834 | 0.0442 | 0.8234 | 0.9917 | 0.0314 | 16/16 | 0.2811 | 0.0071 | 0.0292 | no |
| 2022 | image_same | 414 | 8843 | 7 | 0.9834 | 0.0447 | 0.8256 | 0.9917 | 0.0314 | 16/16 | 0.2818 | 0.0070 | 0.0290 | no |
| 2023 | control | 653 | 4852 | 128 | 0.8361 | 0.1186 | 0.9175 | 0.9871 | 0.0905 | 35/38 | 0.2206 | 0.0112 | 0.0440 |  |
| 2023 | flag_lag24 | 655 | 4944 | 126 | 0.8387 | 0.1170 | 0.9160 | 0.9871 | 0.0875 | 35/38 | 0.2210 | 0.0112 | 0.0441 | no |
| 2023 | image_lag24 | 648 | 4671 | 133 | 0.8297 | 0.1218 | 0.9204 | 0.9871 | 0.0938 | 33/38 | 0.2246 | 0.0112 | 0.0438 | no |
| 2023 | flag_same | 652 | 4860 | 129 | 0.8348 | 0.1183 | 0.9174 | 0.9871 | 0.0894 | 34/38 | 0.2205 | 0.0112 | 0.0440 | no |
| 2023 | image_same | 653 | 4764 | 128 | 0.8361 | 0.1205 | 0.9190 | 0.9871 | 0.0870 | 34/38 | 0.2374 | 0.0111 | 0.0435 | no |

Primary acceptance per year: episode precision higher, FP windows lower, alarmed positive runs not below, window
recall drop at most 0.02, all against control.

- Precision: `image_lag24` is above control only in 2016 (0.1107 against 0.1106) and 2023 (0.1218 against 0.1186)
  and below it in the other four years. Across all candidates and years precision lies between 0.0438 and 0.2129.
- Accuracy stays below the always-negative accuracy for every candidate in every year. Exceeding it requires TP
  greater than FP, that is precision above 0.50.
- The single pass of `image_lag24` is 2016: 10 fewer FP windows out of 1303 and episode precision 0.0350 against
  0.0347, while AP falls from 0.3664 to 0.3317. Both bootstrap intervals for that year include zero.
- In 2023 `image_lag24` removes 181 FP windows and its FP interval excludes zero, but it alarms 33 of 38 positive
  runs against 35 for control and therefore fails.
- `flag_lag24` and `flag_same` differ from control only by refitting noise and pass in no year.
- The `same` rule, which gives the CNN a fresher map, does not help: `image_same` passes in no year.

Paired full-HARP bootstrap 95% intervals for `image_lag24` minus control (1000 draws, seed 24):

| year | episode precision difference | FP window difference |
| --- | --- | --- |
| 2014 | [-0.0179, +0.0013] | [-114.0, +17.0] |
| 2015 | [-0.0185, +0.0016] | [+70.0, +244.0] |
| 2016 | [-0.0041, +0.0044] | [-73.0, +53.0] |
| 2017 | [-0.0216, +0.0077] | [-11.0, +54.0] |
| 2022 | [-0.0022, +0.0011] | [+31.0, +168.0] |
| 2023 | [-0.0051, +0.0122] | [-265.1, -109.0] |

Intervals for all candidates are in `intervals.csv`.

Average precision of the CNN score alone on evaluation windows that have a map, against control on the same
windows:

| year | rule | covered share | CNN-only AP | control AP same windows |
| --- | --- | --- | --- | --- |
| 2014 | lag24 | 0.8907 | 0.4156 | 0.5119 |
| 2014 | same | 0.9848 | 0.4762 | 0.5065 |
| 2015 | lag24 | 0.8926 | 0.3562 | 0.5018 |
| 2015 | same | 0.9919 | 0.4118 | 0.4962 |
| 2016 | lag24 | 0.8572 | 0.1649 | 0.4153 |
| 2016 | same | 0.9820 | 0.2170 | 0.3702 |
| 2017 | lag24 | 0.8390 | 0.5271 | 0.8170 |
| 2017 | same | 0.9709 | 0.6598 | 0.8126 |
| 2022 | lag24 | 0.8604 | 0.0931 | 0.2966 |
| 2022 | same | 0.9945 | 0.1792 | 0.2800 |
| 2023 | lag24 | 0.8401 | 0.1196 | 0.2282 |
| 2023 | same | 1.0000 | 0.1699 | 0.2206 |

The CNN score alone ranks worse than the 96-summary control in every year under both rules.

## Limits

Already inspected years: adaptive development evidence, not an independent test. Counts are overlapping forecast
windows and groupings of them, not physical flares. One map per day at a fixed 128 × 256 shape; resizing changes
the pixel scale differently for each HARP. One small CNN with one frozen recipe and no search; a negative result
bounds this recipe and cadence, not every image model. Maps come from the definitive series, not the near-real-time
one, and no publication latency was measured. Under `lag24` about 84–89% of evaluation windows have a map. Seeds
are fixed, but the Apple MPS backend is not bitwise deterministic; the scores actually used are stored and hashed
in the artifact.

## Reproduction

```sh
pip install -r requirements-maps.txt
python -m scripts.fetch_sharp_maps --output data/sharp_br_maps_20261109_r1 --index-cache data/sharp_dims_probe_20261109_r1
python -m scripts.audit_image_features --output artifacts/image_features_20261110_r1
```

Acquisition config sha256 `37a182bf146dc4b76e6bad6d8181fb0379db2434dbe8a6b0339d2e803d7098d8`; config sha256 `56f1baa57522793d000bc4bedf8ab6e766af3d236e3a2e03c473b3bf70d986c5`; thresholds sha256 `bf3fcbfe54c35c9790a2ede0d2c7e56662ef18d3c3f6e7c6b4f2ace97badf37c`. Use new output directories;
existing output is not overwritten.
