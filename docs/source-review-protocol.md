# Three-event source review

Scope: independently retrieve primary-source records for SWAN-SF catalog IDs
8765 (2014-08-21 M3.4), 8864 (2014-09-03 M2.5), and 9529 (2014-12-18 M6.9).
This is an exploratory review following the sensitivity study, not a preregistered
test. NOAA records also contribute to SWAN-SF; retrieving them separately does
not make them statistically independent observations.

Match a NOAA XRA record by date, exact start/peak/end times and class. Preserve
all associated rows with the same daily NOAA event number. NOAA daily event
numbers and SWAN-SF catalog IDs are different namespaces. Keep disagreement
between XRA, optical FLA and radio reports visible. A shared event number alone
does not prove that each observation has the same physical source.

Use next-day NOAA Solar Region Summaries for positional context. Their stated
validity is the preceding day's 24:00 UTC, not flare peak time. Do not compare
longitudes as though they were simultaneous or substitute a region centroid for
a flare location. Four-digit NOAA region numbers in these 2014 reports are
normalized by adding 10000; this rule is specific to these cases.

Retrieve official JSOC HARP/NOAA mapping and narrow SHARP keyword records around
the events for HARPs 4466, 4502, 4920 and 4941. Record returned T_REC strings with
their explicit TAI scale; do not silently call them UTC. Empty results and
MISSING NOAA associations are unavailable evidence, not proof of nonassociation.
The all-HARP table is a current, lifetime summary, not an event-time measurement.

Save raw responses, retrieval UTC, final URL, transport, SHA-256, and errors under
ignored data/source_review/. Use verified HTTPS where available. If the official
JSOC HTTPS endpoint fails certificate validation, its published HTTP endpoint
may provide public metadata, explicitly marked as unauthenticated transport.
Never disable TLS verification or silently treat HTTP evidence as authenticated.

Export a separate review under ignored artifacts/source_review/, with code and
input hashes. Distinguish source agreement, source conflict, missing evidence,
and human interpretation. Do not infer a corrected HARP from the highest model
probability, bounding-box inclusion alone, or a missing table entry.

Preserve original benchmark labels, predictions, thresholds and previous reports.
No retraining or revised performance claim belongs to this review. Stronger
source support can identify a candidate association without authorizing automatic
relabeling. Unresolved cases remain unresolved pending spatial observations.
