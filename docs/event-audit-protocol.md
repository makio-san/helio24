# Event and alarm episode audit

Fix these rules before inspecting aggregate results. This is a descriptive
development audit of experiment 2's partition-4 validation predictions, using
the saved full-calibrated model and its frozen 90%-recall threshold. No training,
threshold adjustment, candidate selection, or new final-test claim is involved.

## Alarm state and exposure

Sort unique HARP/forecast-time records. Equality with the threshold is an alarm.
Merge successive alarm records only when their issue times differ by exactly
one hour, the observed nominal sliding cadence. A quiet record or any different
spacing breaks an episode. Do not bridge unavailable or quality-excluded records.
For duration accounting assign each forecast one hour of state, truncated if
another forecast arrives sooner. The last record also contributes one hour.
This is an explicit hourly-state convention, not a measured continuous alert
duration and not the union of overlapping 24-hour prediction horizons.

Record episode start, end, window count, state hours, false-alarm state hours
(benchmark target zero), and left/right censoring at gaps or data boundaries.
An all-negative episode contains only target-zero alarm windows; a mixed episode
may still contain false-alarm hours. Report both, with monitored region-hours
as denominator. Do not infer quiet state inside gaps or add time across regions
as though it were one observer's wall-clock time.

## Flare identity and coverage

HARP and NOAA identifiers are different systems. Build HARP/flare-ID evidence
from every filename and verified M/X location-based history annotation in the
official partition-4 archive, including quality-excluded windows for association
only. Check each ID and magnitude against the official integrated catalog.
Check filename peak membership in its exact future interval and historical
annotations against the nearest 12-minute timestamp (at most six minutes).
Only Primary/Secondary annotations qualify. Unexpected annotation syntax fails
closed. Preserve evidence sources and ambiguous multi-HARP mappings separately.

Deduplicate by catalog flare ID. Evaluate only uniquely mapped events with at
least one available forecast satisfying t <= peak < t + 24h. Deduplicate alarms
per event even when many windows or episodes warn of the same event. Also count
events recovered from history annotations but absent from strongest-window
labels. Export catalog M/X events in the overall forecast date span with their
mapping/evaluation status; unmatched catalog entries are not automatic misses,
because they may belong to other regions or have no forecast coverage. This
procedure does not prove complete solar-event or HARP-event coverage.

Report covered mapped-event recall and a separate fully covered 24-hour subset.
Coverage is the union of hourly forecast-state slots intersecting the preceding
24 hours; missing intervals reduce it. Report issue counts and coverage hours.
First-warning lead is peak minus earliest qualifying alarm issue. Separately
report alarms issued strictly before catalog start, with start-time lead, so an
ongoing flare is not presented as advance warning. Exact 24-hour lead is excluded
by the half-open forecast interval; peak-time equality is allowed for benchmark
matching but is not advance warning.

## Region review and presentation

Rank regions by false-alarm hours, and separately by longest all-negative episode.
Report denominators, quality missingness, magnetic feature summaries (USFLUX,
R_VALUE, TOTUSJH) and time to the nearest mapped peak before/after each episode.
Associations are descriptive and do not establish causality. Retain every region,
not only selected examples. Plot probability, hourly alarm spans, window-ending
magnetic summaries and mapped flare peaks on a shared UTC axis. Break lines at
missing forecasts. Label outcomes as retrospective and reveal peaks explicitly.

Save source hashes, protocol hash, mapping exclusions, episodes, event matches,
regional tables and a standalone report under ignored artifacts. Add an optional
dashboard tab for this full-data development audit, distinct from experiment 1.

Source semantics: [SWAN-SF original paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7351763/),
sections on flare integration and slicing. Archive annotations use compact strings
in this release; their actual schema is validated, not inferred from paper examples.
