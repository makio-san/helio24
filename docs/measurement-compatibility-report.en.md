# V2 measurement compatibility: source trace report

Date: 20 October 2026. Decision: **V2 cannot yet be connected directly to the
existing model.** This is not a training experiment; model metrics did not change.

## Data examined

The previous audit's five 2011 windows were retained: HARPs 334, 344, 356,
359 and 372. There are 300 timestamps and 296 finite pairs per variable.
The old quality-pass subset contains 282 timestamps. Only HARP, observation
time and 24 unweighted magnetic measurements were read; V2 outcomes and
2024–2025 data were not opened. Source SHA-256 hashes were verified.

## Force-column differences

The following fixed factors were tested as diagnostic hypotheses. No
regression coefficients were fitted. Matching tolerance is rtol=1e-5,
atol=1e-8; it is not a scientific equivalence standard.

| V2 measurement | Tested V1 transformation | Matches among finite pairs |
| --- | --- | ---: |
| TOTFX | V1 TOTFX / (4π) | 296 / 296 |
| TOTFY | −V1 TOTFY / (4π) | 296 / 296 |
| TOTFZ | V1 TOTFZ / (8π) | 296 / 296 |

All three relationships also match 282/282 in the quality-pass subset.
Scaling and sign differences are systematic in this sample. The relationships
must not become production conversions before the exact calculation-code
version used to produce the data is established.

Within V2, EPSX=TOTFX/TOTBSQ, EPSY=TOTFY/TOTBSQ and EPSZ=TOTFZ/TOTBSQ
each match 296/296. Direct matches against the old EPS columns are zero.
For example, the first HARP-334 record has V1 EPSX=0.265604 and V2 EPSX
approximately −2.806969e13. Internal consistency does not establish that
EPS means the same normalization as before; no automatic scaling or column
substitution was applied to hide the large discrepancy.

## JSOC source records

`hmi.sharp_cea_720s` headers were fetched for the first timestamp in each
window. Stored clock strings were interpreted as TAI in the query: an explicit
alignment hypothesis. Five headers do not validate the entire time series.

| Measurement | V1–JSOC matches | V2–JSOC matches |
| --- | ---: | ---: |
| USFLUX | 5 / 5 | 5 / 5 |
| MEANPOT | 0 / 5 | 5 / 5 |
| TOTPOT | 0 / 5 | 5 / 5 |
| MEANSHR | 0 / 5 | 2 / 5 |
| SHRGT45 | 3 / 5 | 4 / 5 |

Matches use the same numerical tolerance. Printed header precision limits
interpretation, particularly for the final two measurements. MEANPOT/TOTPOT
results support V2 values at these five points; they do not establish that
all V1 data are wrong or that all V2 measurements have been validated.

HTTPS certificate verification failed during retrieval; the published HTTP
endpoint was used. TLS verification was not disabled. HTTP content is not
transport-authenticated; attempts and content hashes are retained in the
manifest. This limitation must remain visible for independent verification.

## Quality and time

HARP 372's 2011-02-10 18:24 JSOC record has QUALITY `0x00010400`; the
other four headers have zero. V2 contains finite magnetic values at that
point. Therefore, a numeric V2 value cannot be assumed to have passed
quality checks. Equivalence to the existing preprocessing cannot be claimed
without reconstructing its QUALITY=0 and IS_TMFI rules.

For all five queries, T_REC matches the stored clock, while T_OBS is 7–8
seconds earlier. T_REC and T_OBS are distinct concepts; this does not verify
UTC/TAI conversion or V2's time-generation procedure. Observation time,
data availability and forecast issue time must remain separate.

## Relation to documentation

[Section 2.2.1 of the V2 paper](https://arxiv.org/html/2610.04591v1#S2.SS2.SSS1)
describes a move from GPU calculations to a new CPU library. This motivates
investigating numerical changes; it does not causally prove the factors above.
The [LorentzForceCalculator documentation](https://dmlab.cs.gsu.edu/docs/spaceweather_toolkit/magparam.html)
describes forces in dynes, TOTBSQ in Gauss² and EPS as normalized forces.
How that description relates to the downloaded EPS values still requires
verification against calculation code and the data-generation version.

## Reproduction and next step

```sh
python scripts/fetch_measurement_sources.py
python scripts/trace_measurement_differences.py
```

Commands refuse to overwrite existing output. Local `data/measurement_sources/`
holds headers and the retrieval manifest; `artifacts/measurement_trace/`
holds per-variable diagnostics, source comparisons and SHA-256 hashes.
Data are not committed to Git. Missing values do not count as finite matches.

Next, trace the calculation version and EPS normalization, then recover
old-period quality fields and measure the masking effect. After time scale
and label inclusion rules are verified, a separate V2 preprocessing version
and training protocol can be frozen. The user's primary objective remains
**recall ≥95% with fewer false alarms**.
