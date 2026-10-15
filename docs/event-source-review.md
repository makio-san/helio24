# Primary-source review of three disputed flare associations

The separately retrieved NOAA records reproduce all three SWAN-SF events'
X-ray class and start, peak and end times exactly. They do **not** establish
equally reliable region associations. Event 9529 has stronger source support
for HARP 4941; events 8765 and 8864 remain unresolved. Original labels and all
model evaluation results remain unchanged.

This review follows the [source-review protocol](source-review-protocol.md).
It is exploratory, and the NOAA material is upstream of SWAN-SF: separate
retrieval is a provenance check, not three new independent validation events.

## Source findings

| SWAN-SF ID | Date and peak UTC | Class | NOAA daily event ID | Source findings | Review disposition |
| --- | --- | --- | --- | --- | --- |
| 8765 | 2014-08-21 13:31 | M3.4 | 9490 | NOAA region 12149, optical position N06E38; HARP 4466 has missing NOAA metadata | Unresolved position/region inconsistency |
| 8864 | 2014-09-03 13:54 | M2.5 | 3300 | XRA assigns 12155; optical/radio rows assign 12152; HARP 4502 has missing NOAA metadata | Explicit source conflict |
| 9529 | 2014-12-18 21:58 | M6.9 | 550 | NOAA rows agree on 12241; JSOC links it to HARP 4941, not HARP 4920 | HARP 4941 is the source-supported candidate; no relabeling |

NOAA daily event IDs and SWAN-SF catalog IDs are different identifiers. The
four-digit region numbers in these 2014 NOAA files are normalized by adding
10000. This is not a universal conversion rule for every solar cycle.

### Event 8765: agreement on a number does not resolve the location

The [21 August NOAA event report][aug-events] identifies M3.4 at 13:19–13:42 UTC,
peaking at 13:31, under region 2149. Its optical report at 13:29–13:36 places the
flare at N06E38 while retaining region 2149. However, the next-day
[Solar Region Summary][aug-srs], valid at 21/2400 UTC, places region 2149 at
N12E77 and region 2148 at N05E27.

**Interpretation:** the optical location and the named region are difficult to
reconcile with those daily positions. Region 2148 is a candidate for further
image-based investigation, not a corrected label. The daily positions are later
than the flare and have not been propagated to peak time.

Five official SHARP records for HARP 4466 during 13:00–13:48 TAI return
NOAA_AR=0, NOAA_NUM=0 and NOAA_ARS=MISSING. HARP 4466 is also absent from the
retrieved current all-HARP association table. Missing metadata cannot settle
the region identity. The separate location annotation in SWAN-SF remains
evidence of a geometric association, not a verified NOAA assignment.

### Event 8864: the disagreement exists inside the NOAA report

The [3 September NOAA report][sep-events] assigns the M2.5 XRA record
(13:20–14:23 UTC, peak 13:54) to region 2155. Under the same daily event ID 3300,
four radio records and the optical flare report instead identify region 2152.
The optical report, 14:07–14:20 UTC, places it at S14W18. These optical times
follow the X-ray peak and must not be presented as a simultaneous image.

The [next-day region summary][sep-srs], valid at 03/2400 UTC, places region 2152
at S15W26 and region 2155 at S20E75. **Interpretation:** the optical location
supports investigating region 12152. It does not justify automatically replacing
the XRA region 12155 or treating every record grouped under 3300 as conclusive
evidence of one physical source.

All five queried HARP-4502 SHARP records have missing NOAA associations. At
13:48 TAI its native longitude bounds are 8.314208 to 30.087482 and latitude
bounds −24.940029 to −11.550781, numerically consistent with the integrated
catalog's (18, −14) location. A bounding box and missing NOAA metadata cannot
resolve the disagreement. The ten conflicting forecast labels remain intact.

### Event 9529: HARP 4941 has stronger source support

The [18 December NOAA report][dec-events] assigns the M6.9 event
(21:41–22:25 UTC, peak 21:58) and its associated radio/optical records to region
2241. The optical position is S11E15. Its start is **B2217**, meaning before
22:17, not precisely 22:17; the parser retains this qualifier.

The official [HARP/NOAA table][harp-table] and five queried SHARP records per
HARP agree on these associations:

| HARP | NOAA_ARS | NOAA_AR in queried records |
| --- | --- | --- |
| 4941 | 12241 | 12241 |
| 4920 | 12235, 12237, 12238, 12242 | 12242 |

The [19 December SRS][dec-srs], valid at 18/2400 UTC, distinguishes region 2241
(S09E04) from 2242 (S18W16). These are contextual positions, not flare-peak
coordinates.

There is also a plausible geometric explanation for SWAN-SF's duplicate
location association. Its integrated catalog uses (−5.1917867, −9) as fl_lon,
fl_lat for this event; goes_location is (0, 0). At 21:48 TAI, the JSOC boxes are:

| HARP | Longitude bounds | Latitude bounds | Catalog point inside bounds |
| --- | --- | --- | --- |
| 4920 | −6.855653 to 60.014801 | −32.148258 to −2.606695 | Yes |
| 4941 | −19.317751 to 1.365474 | −15.254949 to −5.500595 | Yes |

**Interpretation:** overlapping boxes can account for a two-HARP location
association without implying two physical sources. The region-number evidence
supports HARP 4941. This remains a candidate association rather than a manually
certified spatial identification; the sensitivity study's ambiguity exclusion
and original labels have not been revised.

## Source limitations and preservation

NOAA's [event-format documentation][event-format] describes these as edited
preliminary reports that may contain errors or omissions. Optical region numbers
come from the observatory; X-ray assignments come from SWPC staff. A shared daily
event number groups reports according to the forecaster, not an independent
physical-source guarantee.

The snapshot contains 12 small source files retrieved on 2026-10-15 UTC
(16 October in Istanbul): three event lists, three region summaries, the NOAA
format document, the HARP table, and four JSOC keyword responses. NOAA downloads
use verified HTTPS. The official JSOC HTTPS endpoint failed certificate
validation; the published HTTP endpoint supplied the metadata. This limitation
is recorded in the manifest. TLS checks were not disabled, and HTTP responses
must not be described as transport-authenticated. SHA-256 preserves the fetched
bytes but does not authenticate their publisher.

The HARP table is a current lifetime association summary, not a historical
snapshot. Queried records retain explicit TAI timestamps; NOAA times are UTC.
No simultaneous-time comparison, TAI-to-UTC conversion or coordinate propagation
is performed here. No spatial SDO/AIA image review has yet adjudicated these
cases. The machine-generated report consequently leaves adjudication unresolved;
the stronger candidate support for 9529 is this document's interpretation.

## Reproduce the evidence review

```sh
python scripts/fetch_source_review.py
python scripts/review_event_sources.py
```

The fetch command limits each request to 1 MB and 25 seconds and records URLs,
retrieval times, hashes, transport and errors in `data/source_review/manifest.json`.
Both commands refuse to overwrite an existing directory. The review verifies
the provenance and sensitivity reports and all downloaded source hashes, then
writes `artifacts/source_review/` with the three case summaries, NOAA event rows,
NOAA region positions, JSOC keywords, original annotations and protocol. Raw data
and generated outputs stay ignored by Git.

For further evaluation, preserve the existing benchmark and report these cases
as association uncertainty. Before any revised training labels, spatial evidence
must be reviewed with explicit coordinate frames and time scales, and any
accepted decisions must form a separate versioned label set. No model retraining
is warranted solely by this source review.

[aug-events]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2014/08/20140821events.txt
[sep-events]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2014/09/20140903events.txt
[dec-events]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2014/12/20141218events.txt
[aug-srs]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_region_summaries/2014/08/20140822SRS.txt
[sep-srs]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_region_summaries/2014/09/20140904SRS.txt
[dec-srs]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_region_summaries/2014/12/20141219SRS.txt
[harp-table]: http://jsoc.stanford.edu/doc/data/hmi/harpnum_to_noaa/all_harps_with_noaa_ars.txt
[event-format]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/docs/SolarEventReport.pdf
