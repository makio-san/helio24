# EPS and quality compatibility audit

Date: 2026-10-23. **Decision: not ready for a V2 model adapter.**
The EPS implementation is now identified and quality coverage has expanded
from five individual headers to all 300 timestamps in the same five 2011
windows. No training, label changes or future-period evaluation occurred.

## Pinned source and EPS mechanism

The [official build instructions](https://dmlab.cs.gsu.edu/docs/spaceweather_toolkit/TEST_BUILD.html)
link to the [toolkit repository](https://bitbucket.org/gsudmlab/spaceweather_toolkit/).
We inspected commit `9f6e805d19077ab44d0ed8d2b546f207a8f155f7`, dated
2026-10-07, specifically `py_src/swdatatoolkit/magparam/_lorentz_calculator.py`.
The actual class is `LorentzCalculator`; the previous report's
`LorentzForceCalculator` name should be read as a naming error, not another implementation.

The implementation multiplies the force sums by pixel area `dA`, while
`TOTBSQ` is the sum of squared field components without that area factor.
It then computes `EPSX=TOTFX/TOTBSQ`, and likewise for Y and Z.
Consequently the area factor remains in EPS. This is consistent with the
previous overlap's force/TOTBSQ identities, but does not establish that this
commit produced the downloaded V2 archive. Package metadata says `0.0.1`;
that version alone cannot identify the production revision.

A diagnostic calls only this inspected module, without installing the package.
It holds a single-pixel field `(3, 4, 5)` and zero uncertainties fixed and
changes plate scale from `0.5` to `1.0`. This synthetic calculation tests
software behavior only; it is not solar training or evaluation data.

| Quantity | Ratio after doubling plate scale |
| --- | ---: |
| TOTBSQ | 1 |
| TOTFX | 4 |
| TOTFY | 4 |
| EPSX | 4 |
| EPSY | 4 |

EPSZ is zero for this particular field, so its ratio is undefined and was
not used as evidence. EPS in this implementation is area-dependent; it must
not be silently treated as the old dimensionless EPS. No conversion or fix
was applied to source data, feature tables, models or upstream code.

## Quality coverage and effect

Queries use the same five frozen 12-hour windows, not newly selected regions.
V2 reading projects only identifiers, time and 24 unweighted magnetic inputs,
with a pre-2019 filter. All historical source hashes are verified.

| HARP | Expected | JSOC quality records | Equal known old quality | Old quality + IS_TMFI pass | JSOC QUALITY=0 | V2 all finite | V2 finite but JSOC quality rejected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 334 | 60 | 60 | 60 | 56 | 56 | 60 | 4 |
| 344 | 60 | 60 | 56 | 55 | 58 | 56 | 1 |
| 356 | 60 | 60 | 60 | 58 | 58 | 60 | 2 |
| 359 | 60 | 60 | 60 | 56 | 56 | 60 | 4 |
| 372 | 60 | 60 | 60 | 57 | 57 | 60 | 3 |
| Total | 300 | 300 | 296 | 282 | 285 | 296 | 14 |

All 296 known old QUALITY values agree with JSOC. The other four values
are missing, not contradictory flags. They belong to HARP 344 at
2011-01-13 05:24, 05:36, 05:48 and 06:00. Both data versions lack magnetic
values there; JSOC now provides three zero quality flags and one `65536`.
Retrieval-time/source-processing differences are possible, but their cause
has not been established. Missing old fields are not filled automatically.

Using only current JSOC QUALITY=0 accepts 285 timestamps, compared with
282 under the original QUALITY/IS_TMFI rule. Requiring finite V2 measurements
as well leaves 282 in this sample, but this coincidence does not reconstruct
IS_TMFI or prove equivalence elsewhere. Fourteen finite V2 rows fail the
source quality rule and the old rule. Thus V2 finiteness is not a quality mask.
The pixel mask used inside magnetic calculations is also distinct from
record-level QUALITY and the dataset's IS_TMFI flag.

## Time and transport limitations

All 300 stored clock strings match JSOC T_REC when explicitly queried as TAI.
T_REC minus T_OBS ranges from 6 to 8 seconds. Parsing preserves the TAI
interpretation as a hypothesis; it performs no UTC conversion. A naive
V2 timestamp still does not document its time scale or observation availability.
No historical forecast times were shifted based on this audit.

HTTPS requests timed out in this run; the published HTTP endpoint returned
the records. TLS verification was not disabled. HTTP is not authenticated
transport; hashes preserve retrieved bytes, not publisher authenticity.
Request URLs, timestamps, failures and hashes are retained locally.

## Reproduction and remaining gates

```sh
git clone https://bitbucket.org/gsudmlab/spaceweather_toolkit.git data/toolkit_source
git -C data/toolkit_source checkout 9f6e805d19077ab44d0ed8d2b546f207a8f155f7
python scripts/fetch_quality_sources.py
python scripts/audit_eps_quality.py
python scripts/publish_reports.py --output artifacts/bilingual_reports_eps_quality
```

Existing source/output directories are preserved. The audit rejects a different
upstream commit or locally modified calculator. Outputs in
`artifacts/eps_quality_audit/` include `report.json`, `summary.csv` and all
300 aligned quality rows in `aligned_quality.csv`. Raw headers and the source
checkout stay in ignored `data/`; the manifest records source/code/output hashes.

Remaining work: verify the actual V2 production commit and EPS definition,
document the production timestamp conversion, and reconstruct IS_TMFI or
define and evaluate a separate versioned quality policy. Label inclusion and
temporal partition rules must also be frozen before new training. The
2024–2025 holdout remains untouched; the recall target remains at least 95%.
