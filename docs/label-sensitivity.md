# Label association sensitivity results

This is a partition-4 development analysis, using 50,631 saved experiment-2
forecasts and the frozen threshold 0.0479986873703553. The
[protocol](label-sensitivity-protocol.md) was committed before computing these
comparisons, after the [provenance investigation](event-provenance.md). Neither
the model, benchmark targets, catalog peaks nor alarm states changed.

## Six fixed comparisons

Every variant includes verified positive filename evidence. History evidence
uses NOAA associations, location associations, or their union. `nearest` accepts
timestamps within six minutes of catalog peak; `containing` accepts peaks in
the 12-minute interval beginning at the annotation. These rules change evidence
eligibility, not the event's catalog peak time.

| Timing | History channel | Detected / evaluated | Conditional event recall | Unmapped | Ambiguous | No forecast coverage | Negative-label conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nearest | NOAA | 85 / 86 | 98.84% | 63 | 0 | 1 | 0 |
| Nearest | Location | 86 / 87 | 98.85% | 62 | 0 | 1 | 10 |
| Nearest | Union | 86 / 87 | 98.85% | 62 | 0 | 1 | 10 |
| Containing | NOAA | 90 / 91 | 98.90% | 57 | 0 | 2 | 0 |
| Containing | Location | 91 / 92 | 98.91% | 55 | 1 | 2 | 29 |
| Containing | Union | 91 / 92 | 98.91% | 55 | 1 | 2 | 29 |

Each row accounts for the same 150 whole-Sun catalog events in the forecast
date span. Recall includes only uniquely mapped events with an available
forecast covering the peak. Other statuses are not counted as misses.
Conflicts count event/window pairs with benchmark target zero, not unique flares.

The `nearest_location` reference reproduces the previous audit's per-event
status, HARP, detection, warning-before-start, forecast count and coverage.
The fully covered preceding-24-hour subsets contain 47 events for each nearest
variant and 51 for each containing variant, all detected. Every detected event
in this comparison also has a qualifying alarm strictly before catalog start.
This does not imply complete monitoring outside those subsets.

## A constant event denominator

Exactly 85 events are evaluated on the **same HARP in all six variants**.
All variants detect the same 84 of those events: 98.82% conditional recall.
The small increases in the table reflect changed event eligibility, not better
predictions. No convention is selected as a winner from this comparison.

Event 9053 (M2.2, HARP 4678) remains the only evaluated miss in every variant.
It has 10.15 hours of forecast-state coverage in the preceding 24 hours.
Benchmark false-alarm exposure remains 4,264 region-hours in every variant;
it is not recomputed against speculative replacement labels.

## Cases that change the denominator

* **8864 / HARP 4502:** location evidence makes the event evaluable; NOAA-only
  history leaves it unmapped. Its ten negative-label conflicts persist under
  either timestamp rule when location history is included.
* **8765 / HARP 4466:** the containing rule accepts its location annotation.
  The event is detected, but overlaps 19 target-zero windows. Together with
  event 8864 this produces 29 conflicting event/window pairs.
* **9529:** the containing rule reveals a location association with HARP 4920,
  in addition to HARP 4941's filename and location evidence. Location/union
  variants classify it as ambiguous and exclude it, rather than choosing the
  HARP that gives a convenient outcome. The nearest reference evaluates it on
  HARP 4941.
* **9035, 9097, 9150, 9159, 9235:** the containing rule adds these five evaluated
  events under every history channel. Each is detected.
* **9225 / HARP 4781:** the containing rule establishes an association, but
  there is no qualifying forecast. It remains outside the recall denominator.

NOAA-only variants have no negative-label conflicts in this comparison. That
does not prove that NOAA history is complete or physically correct; it also
leaves additional events unmapped. Association uncertainty needs independent
adjudication before any future training-label revision.

## Reproduction and delivery

Run `python scripts/run_label_sensitivity.py` after the event audit and provenance
investigation. The command checks their source, generating-code and artifact
hashes and refuses to overwrite an existing sensitivity run. Previous outputs
remain unchanged. Generated data stay under ignored `artifacts/label_sensitivity/`:

* `metrics.csv`: counts, conditional recall, common-event and full-coverage subsets.
* `events.csv`, `mappings.csv`: every variant's event matches and evidence.
* `transitions.csv`: every event's status/HARP/detection against the reference.
* `conflicts.csv`: negative-label event/window pairs, without relabeling.
* `report.html`, `report.json`, `protocol.md`: standalone report and provenance.

The dashboard's **Alarm & event audit → Label association sensitivity** expander
verifies these artifacts, shows the six comparisons and changed events, and
offers CSV and HTML downloads. No new final-test performance claim follows from
this descriptive comparison; an independent period is still needed for that.
