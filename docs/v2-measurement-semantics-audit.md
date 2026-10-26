# SWAN-SF-V2 measurement semantics audit

Audit date: 2026-10-26. Decision: **the 24 unweighted magnetic fields are
approved for dataset-native predictive use without conversion**. This decision
does not claim that Helio24 can reproduce the archive from raw magnetograms or
that the exact upstream production commit is known.

## Evidence and bounded provenance

The V2 paper identifies the definitive `hmi.sharp_cea_720s` series, publishes
the names and formulas of the 24 magnetic quantities, and states that they were
recalculated with `swdatatoolkit`. The official toolkit repository was inspected
at its public `V0.0.1` history. The last visible commit before the archive
timestamps is `69e6b65d48159078194e04a7ab4a784c03954fd2`, committed at
2026-10-01 15:15:45 UTC. The next visible commit is
`27b6e5a4cdc99c6d0be2f5ef329b6240c6578314` on 2026-10-02 13:03:55 UTC.
The four archives were last modified between 2026-10-01 17:52:32 and
17:56:22 UTC.

This timing bounds the public source state but does not prove which checkout
produced the data. Parquet metadata records Spark 4.2.0 and parquet-mr 1.17.0,
but no Git revision. The Lorentz implementation is byte-identical at the
March source change `c82ef1d`, the bounded `69e6b65` state and the inspected
public branch snapshot; its SHA-256 is
`bfb11c1dbe3d255811ca26ce0a723bc09998d156c2aeea4fda5077ce700b3959`.

## Numerical checks

Five frozen 2011 overlap windows supplied 296 finite V1/V2 pairs per variable
and 282 pairs after the historical V1 quality mask. The checks below are
diagnostic identities, not learned conversions.

| Check | All finite pairs | Historical-mask pairs |
| --- | ---: | ---: |
| `V2 TOTFX = V1 TOTFX / (4π)` | 296 / 296 | 282 / 282 |
| `V2 TOTFY = -V1 TOTFY / (4π)` | 296 / 296 | 282 / 282 |
| `V2 TOTFZ = V1 TOTFZ / (8π)` | 296 / 296 | 282 / 282 |
| `EPSX = TOTFX / TOTBSQ` within V2 | 296 / 296 | 282 / 282 |
| `EPSY = TOTFY / TOTBSQ` within V2 | 296 / 296 | 282 / 282 |
| `EPSZ = TOTFZ / TOTBSQ` within V2 | 296 / 296 | 282 / 282 |

Five timestamp-aligned JSOC header snapshots provide a separate bounded check.

| Measurement | V1–JSOC matches | V2–JSOC matches |
| --- | ---: | ---: |
| USFLUX | 5 / 5 | 5 / 5 |
| MEANPOT | 0 / 5 | 5 / 5 |
| TOTPOT | 0 / 5 | 5 / 5 |
| MEANSHR | 0 / 5 | 2 / 5 |
| SHRGT45 | 3 / 5 | 4 / 5 |

The first three results support the V2 recalculation at these points. Printed
header precision limits the final two comparisons. Five records cannot validate
the full archive or every formula.

## Frozen downstream contract

Helio24 treats the verified V2 archive values as the source of record. It uses
the 24 unweighted field names exactly as stored and applies no V1 scaling,
sign correction, empirical EPS conversion, weighted-field substitution or JSOC
header replacement. Each 60-row observation window produces mean, population
standard deviation, last value and end-to-start delta, for 96 features. Missing
and non-finite values follow the separately verified V2 quality policy; model
imputation fits on training data only.

Under this scoped contract, `measurement_semantics` is verified for predictive
use. “Verified” means the input identity, transformations and limitations are
fixed and auditable. It does not mean physical equivalence to V1 or complete
upstream computational reproducibility.

## Limitations and uncertainty

- The exact Git revision and environment used by the archive producer are not
  embedded in the data and remain unknown.
- The public source timing is provenance evidence, not proof of the production
  checkout.
- Internal equations can detect inconsistency but cannot independently prove
  physical correctness or units.
- The five JSOC records are a bounded spot check. One record has nonzero
  historical `QUALITY`; numerical availability is not historical quality
  equivalence.
- The contract supports model training on this frozen archive. A live pipeline
  must separately demonstrate matching fields, calculations and availability.

## Reproduction

```sh
.venv/bin/python scripts/trace_measurement_differences.py
git -C data/toolkit_source show 69e6b65:\
py_src/swdatatoolkit/magparam/_lorentz_calculator.py | shasum -a 256
.venv/bin/python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_semantics_20261026
```

The frozen numerical audit is `artifacts/measurement_trace/report.json` with
SHA-256 `d48a767cd81076c2bdbe4963a3e7bcb309e18cb109ccee975bb95b305ac5abcc`.

Sources: [SWAN-SF-V2 preprint](https://arxiv.org/abs/2610.04591),
[swdatatoolkit paper](https://arxiv.org/abs/2604.22741),
[official toolkit repository](https://bitbucket.org/gsudmlab/spaceweather_toolkit/).
