# Next evaluation: compatibility before model selection

Status on 2026-10-16: the metrics report is complete; no new model has been
trained. Source review supports HARP 4941 for event 9529 more strongly, while
8765 and 8864 remain unresolved. Preserve the original labels and prior reports.
The objective is reliable probability and alarm performance, not maximizing
accuracy by exploiting class imbalance. No finite experiment proves that a
model is the best possible model.

## A new data candidate, not a drop-in replacement

The [SWAN-SF-V2 preprint, v1](https://arxiv.org/html/2610.04591v1), posted
3 October 2026, describes data through December 2025, changed flare association
rules and calendar-quarter partitions. Its final Dataverse release is pending
peer review. The [authors' download directory](https://dmlab.cs.gsu.edu/solar/swan-sf/)
offers raw and sliced archives. These published claims motivate a compatibility
study; they do not validate this project's future model results.

The official first raw archive responded over verified HTTPS with byte ranges
and a total length of 1,177,434,736 bytes. A bounded probe streamed 225,669,120
compressed bytes to recover its first Parquet member (269,888,724 bytes), then
closed the connection. Metadata reports 246,621 rows and three row groups.
Only schema/metadata were read, not label values, predictions or performance.

The real schema contains all 24 existing magnetic measurement names in lowercase,
including `usflux` and `r_value`. The weighted `w_*` variants are distinct fields.
The sample lacks `QUALITY` and `IS_TMFI`, which the existing preprocessing uses
to mask measurements. `obs_start` is a timezone-naive nanosecond timestamp;
its type does not establish a UTC/TAI convention. Outcome and confidence fields
are present and are explicitly excluded from predictive input mappings.

**Current decision: not ready for the model.** Matching column names is only a
schema result. The missing quality fields and unresolved time semantics prevent
a claim that old preprocessing can be applied unchanged. No zero-filled quality
flags, silent weighted-feature substitutions, or guessed time conversions are
permitted by the compatibility checker.

Reproduce the bounded, local check:

```sh
python scripts/probe_swan_v2.py
python scripts/check_v2_compatibility.py
```

The probe limits transfer and extracted member size to 400 MiB, refuses to
overwrite an existing sample, checks HTTP range semantics and records hashes.
It never extracts an archive-supplied path. The checker writes its findings to
ignored `artifacts/v2_compatibility/`; all downloaded data remain ignored.

## Gates before evaluating a new period

1. Compare the 24 unweighted measurements on an already inspected pre-2019
   overlap: units, values, missingness, duplicates and sampling cadence. Inspect
   only that development overlap while designing the adapter.
2. Establish the quality policy from release documentation and source records.
   Recover original quality metadata where feasible; otherwise version the new
   policy and quantify its effect on the old overlap. Do not claim equivalence
   from missing fields.
3. Resolve timestamp scale and observation/forecast endpoint conventions.
   Every input must precede issue time. Keep the 12-hour observation and 24-hour
   forecast question explicit; do not interpolate using future observations.
4. Reconcile flare identities, confidence tiers and ambiguous HARP mappings.
   Unverified or ambiguously associated events must not silently become negative
   examples. Freeze inclusion/exclusion and sensitivity rules before fitting.
   Spatial adjudication of 8765/8864 remains an outstanding, separate task.
5. Freeze a dataset manifest, temporal roles, candidate budget and selection
   criteria before any new model scores are inspected.

## Bounded old-period overlap result

The next check has now been run on five already inspected 2011 HARP windows:
334, 344, 356, 359 and 372. Selection was ascending HARP and the first overlapping
observation window, not flare outcome or model score. The reader projects only
HARP, observation time and the 24 unweighted measurements, with a pre-2019
date filter. It never loads V2 outcome columns.

All 300 old timestamps matched identical naive clock strings in the sample.
That establishes alignment of stored strings, not a physical UTC/TAI conversion.
Of 7,200 measurement positions, 96 are missing on both sides. Among 7,104 pairs
finite on both sides, 4,310 agree at rtol=1e-5, atol=1e-8; **2,794 differ**.
The CSV's `close_samples` includes the 96 matching missing positions, so its
total is 4,406. This numerical tolerance is a diagnostic, not a scientific
equivalence criterion.

The strongest differences include TOTFX/TOTFY/TOTFZ, EPSX/EPSY/EPSZ, MEANPOT
and TOTPOT. For example, HARP 334 at stored time 2011-01-05 21:24 has old EPSX
0.265604 and new epsx approximately −2.806969e13. The old USFLUX value
5.041301e19 is close to the new usflux 5.041302e19 at the same stored time.
These mixed results rule out treating all columns as interchangeable. They do
not establish whether the differences originate in units, formulas, sign
conventions, source revisions or dataset processing.

Only 282 of the 300 old samples pass the original QUALITY/IS_TMFI rules.
The new schema cannot reproduce those decisions directly. No replacement
quality flag or fitted numerical conversion has been invented.

```sh
python scripts/audit_v2_overlap.py
```

This immutable audit writes per-HARP/per-variable differences and source hashes
under `artifacts/v2_overlap/`. It remains a five-window diagnostic, not evidence
of parity throughout the dataset. New-period model evaluation is still gated.

## Reserved periods and promotion rules

Reserve **2024–2025** for a future final evaluation. No target values or model
scores from that period have been examined in this compatibility probe. Do not
train, calibrate, choose thresholds or revise preprocessing based on its results.
Calendar-quarter archive numbers are not chronological train/test roles: split
by verified timestamps instead.

The intended earlier roles are training/development through 2021, calibration
in 2022 and selection in 2023, conditional on compatibility and coverage checks.
These are preparation decisions, not a finalized executable experiment protocol.
Record any coverage-driven revision before performance is computed. Purge
overlapping observation/target intervals and shared HARP identities across roles.

Keep the frozen experiment-2 model as a reference only if the feature bridge
passes its checks. Compare it with a training-prevalence baseline and a bounded
candidate set specified in the final protocol. Select thresholds on validation
at recall targets of 80%, 90% and 95%, with 90% as the principal operating point.
Report all targets regardless of outcome.

Use false-alarm burden at the principal recall target, AP, Brier, log loss,
reliability-bin counts and HARP-cluster uncertainty jointly. Accuracy, F1, TSS
and confusion counts remain in the report. A candidate needs reproducible
development evidence of better alarm discrimination and acceptable probability
quality; exact promotion/noninferiority criteria and fitting budget must be
committed before training. Do not repeatedly tune against a final period until
the numbers look favorable. After the final evaluation is inspected, further
iterations require a new holdout or must be labeled retrospective.

Immediate next investigation: trace the disagreeing magnetic parameters to
documented units/formulas and JSOC source values on these same old windows, then
establish quality and time semantics. Bulk ingestion and training follow only
after those gates. The bounded overlap check has advanced this task, but has
not established a valid feature bridge.
