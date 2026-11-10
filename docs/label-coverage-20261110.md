# Label coverage audit: which M/X flares reach a positive label (2026-11-10)

## Decision

Reading R1 of the [frozen protocol](../config/label-coverage-v1.json) holds: label coverage collapsed in solar
cycle 25. Of the SGAS M/X flares that the definitive JSOC `NOAA_ARS` association maps to a HARP, 90.1% (2014)
and 87.4% (2015) fall inside a positive development window, but only 29.6% (2022) and 28.9% (2023) do. The
missing flares are the HEK M/X events that SWAN-SF V2 attached to no HARP: 174 in 2022 and 293 in 2023, of which
132 and 272 map to a HARP through `NOAA_ARS`. The fail-closed rule excludes the windows that contain them, so the
flaring HARP keeps only negative windows. In 2022 and 2023 these hidden HARPs (28 and 52) produce 38.6% and 57.2%
of the false-alarm windows at the watch threshold; removing their windows raises precision from 0.0442 to 0.0701
and from 0.1186 to 0.2390, and AP from 0.2800 to 0.3500 and from 0.2206 to 0.3445. The training table carries the
same gap, so the baseline was fitted on fewer than a third of cycle-25 flares. A separate frozen protocol for an
independent HARP association of M/X events and a walk-forward rerun on the relabelled table is justified.
Nothing was relabelled here; no model, threshold or alert is changed; the reserved 2024–2025 test was not read.
The protocol was frozen and committed before any result.

## Why this audit

The cycle-25 diagnostic found that 83% (2022) and 74% (2023) of FP windows come from HARPs with no positive
window in the year, and only 12 and 27 flaring HARPs in 528 and 703. The frozen V2 label inventory audit had
already listed 622 HEK M/X events attached to no HARP; their distribution by year had not been examined.

## Method

Sources: the issued NOAA SGAS products (section A energetic events with region number, peak time and X-ray
class; the product of day D lists UT day D−1), the daily JSOC `NOAA_ARS` keyword per HARP, the frozen development
table, the stored baseline probabilities and the recall-0.90 watch thresholds, and the frozen list of HEK M/X
events unassigned by V2. An SGAS M/X event is mapped to every HARP whose `NOAA_ARS` on the peak date contains its
region number. It is `covered` if a development window of that HARP contains the peak and is positive, `hidden`
if such windows exist and are all negative, `no_window` if none contains the peak (excluded by the fail-closed
rule, removed at a fold boundary, or not observed). HEK unassigned events are matched to SGAS events by class and
a peak-time difference of at most 5 minutes. Hidden HARPs of an evaluation year are HARPs with a `hidden` or
`no_window` event and no positive window; their removal is a bound on the label effect, not a relabelling.

## Coverage by year

| year | SGAS M/X events | with region | mapped to HARP | covered | hidden | no_window | covered share | positive windows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 207 | 193 | 172 | 155 | 0 | 17 | 0.9012 | 2363 |
| 2015 | 130 | 124 | 119 | 104 | 2 | 13 | 0.8739 | 1403 |
| 2016 | 16 | 15 | 15 | 13 | 0 | 2 | 0.8667 | 205 |
| 2017 | 45 | 42 | 42 | 40 | 0 | 2 | 0.9524 | 253 |
| 2018 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 |
| 2019 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 |
| 2020 | 2 | 0 | 0 | 0 | 0 | 0 |  | 0 |
| 2021 | 29 | 28 | 26 | 16 | 0 | 10 | 0.6154 | 204 |
| 2022 | 178 | 156 | 152 | 45 | 2 | 105 | 0.2961 | 421 |
| 2023 | 359 | 343 | 342 | 99 | 26 | 217 | 0.2895 | 781 |

2018–2020 have no M/X flare in the development table; 2020 has two SGAS events without region number.

## HEK events unassigned by V2

| year | HEK unassigned | matched to an SGAS event | mapped to a HARP |
| --- | --- | --- | --- |
| 2014 | 45 | 40 | 25 |
| 2015 | 21 | 20 | 13 |
| 2016 | 6 | 6 | 5 |
| 2017 | 6 | 6 | 3 |
| 2020 | 2 | 2 | 0 |
| 2021 | 16 | 16 | 13 |
| 2022 | 174 | 157 | 132 |
| 2023 | 293 | 282 | 272 |

## Effect on the six evaluation years

| year | hidden HARPs | their windows | FP windows | FP windows of hidden HARPs | FP share | precision | precision without hidden | AP | AP without hidden |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 2 | 304 | 7634 | 167 | 0.0219 | 0.2082 | 0.2118 | 0.5079 | 0.5105 |
| 2015 | 8 | 1791 | 6294 | 528 | 0.0839 | 0.1721 | 0.1849 | 0.4924 | 0.4985 |
| 2016 | 0 | 0 | 1303 | 0 | 0.0000 | 0.1106 | 0.1106 | 0.3664 | 0.3664 |
| 2017 | 1 | 203 | 1035 | 51 | 0.0493 | 0.1850 | 0.1928 | 0.8117 | 0.8125 |
| 2022 | 28 | 5127 | 8949 | 3456 | 0.3862 | 0.0442 | 0.0701 | 0.2800 | 0.3500 |
| 2023 | 52 | 7708 | 4852 | 2773 | 0.5715 | 0.1186 | 0.2390 | 0.2206 | 0.3445 |

- In 2014 and 2015 the few hidden HARPs hold 2.2% and 8.4% of FP windows and removing them changes precision by
  less than 0.013. In 2022 and 2023 they hold 38.6% and 57.2%.
- Hidden flares that sit inside a negative window are rare (2 in 2022, 26 in 2023); the dominant case is
  `no_window`: the window containing the peak was excluded because V2 attached the flare to no region, while the
  HARP's other windows stayed negative.
- 2023 has 7 events mapped to more than one HARP; they are classified by their best outcome.

## Limits

SGAS region numbers and `NOAA_ARS` are associations, as is V2's; this audit measures their agreement, not truth,
and a flare that `NOAA_ARS` maps to a HARP may still be wrongly attributed. SGAS lists energetic events and may
omit some M-class flares. Development years only; the reserved test was not read. Removing hidden HARPs is an
upper bound on what a correct association would recover at the watch threshold, because a relabelled table would
also change the fitted model and the calibration-year threshold.

## Reproduction

```sh
python -m scripts.audit_label_coverage --output artifacts/label_coverage_20261110_r1
```

Config sha256 `6065e626e83ec2c241e5b695d372314569c154a6c040d43c2ae47594d5ea8927`. Use new output directories; existing output is not overwritten.
