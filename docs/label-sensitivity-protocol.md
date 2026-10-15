# Label association sensitivity protocol

Record these rules before computing the comparison. This is a descriptive
partition-4 development analysis of experiment 2's frozen predictions and
threshold. Previous provenance findings motivated the design; this is not an
independent test or a search for the highest event recall.

## Fixed inputs and six variants

Reuse the verified event-audit windows and provenance exports. Verify their
source and artifact hashes before use. Keep model probabilities, benchmark
targets, forecast intervals, alarm states and catalog peak times unchanged.

Every variant includes verified positive filename associations, checked against
catalog ID, magnitude and exact forecast interval. Cross two history rules:

* `nearest`: annotation timestamp is within six minutes of catalog peak.
* `containing`: peak is in [annotation timestamp, timestamp + 12 minutes).

with three association channels:

* `noaa`: MFLARE_LABEL and XFLARE_LABEL.
* `location`: MFLARE_LABEL_LOC and XFLARE_LABEL_LOC.
* `union`: either of these channels.

Only Primary/Secondary evidence qualifies. Deduplicate event/HARP pairs; retain
all accepted evidence sources. Multiple distinct HARPs for one event make it
ambiguous, even when one association comes from a filename. Do not prefer a
method or resolve ambiguity using model predictions. Recompute timing from
timestamps rather than trusting precomputed compatibility flags.

`nearest_location` is the reference and must reproduce the original event audit
for every catalog event, including status, HARP, detection and coverage.

## Outcomes and denominator checks

Apply the original half-open forecast interval and hourly coverage rules without
modification. Report whole-catalog status counts, evaluated and detected events,
conditional event recall, warnings before catalog start, and the fully covered
24-hour subset. Unmapped, ambiguous and uncovered events are not automatic misses.

Export every event's status and mapping in each variant, plus transitions from
the reference. For a denominator-controlled comparison, also report recall on
the intersection of evaluated events assigned to the **same HARP** in all six
variants. Flag events whose status or HARP changes even if detection is unchanged.

Count event/window pairs where an evaluated mapped event falls inside a window
with benchmark target zero. Export those pairs; do not relabel them or treat the
alternative association as physical ground truth. Report benchmark false-alarm
hours once, since neither predictions nor benchmark labels change.

## Outputs and interpretation

Write new outputs only under ignored `artifacts/label_sensitivity/`; refuse to
overwrite an existing run. Include the protocol, source/code/artifact hashes,
metrics, event matches, mappings, transitions, conflicts and a standalone HTML
report. Show a verified summary in the existing dashboard audit tab.

Differences measure sensitivity to association conventions and event eligibility,
not improvement in the model. Do not select a winning convention from recall or
infer complete catalog coverage. No retraining, threshold tuning, benchmark
relabeling, partition-5 evaluation or live-data connection is part of this step.
