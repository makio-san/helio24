# Spatial review of events 8765 and 8864

Date: 2026-10-23. **The new images favor an eastern-limb source in both
cases, but do not establish a corrected HARP label.** No benchmark label,
model, threshold or performance result was changed.

## Evidence and scope

Six full-disk SDO/AIA 131 browse images were retrieved over verified HTTPS
from Helioviewer: five minutes before catalog start, at catalog peak, and
at catalog end for each event. Source ID 9 was verified against the service's
data-source listing. The nearest-image tolerance was 60 seconds. All six
images are within 15 seconds of the requested time.

The assistant visually inspected all six original PNGs and their time
watermarks. This is a qualitative, model-assisted source review, not expert
adjudication, calibrated photometry or an automated flare-localization result.
The watermark times match the separately fetched image metadata.

| Event | Stage | Requested UTC | Image UTC | Absolute offset, seconds |
| --- | --- | --- | --- | ---: |
| 8765 | before | 2014-08-21 13:14:00 | 2014-08-21 13:13:45 | 15 |
| 8765 | peak | 2014-08-21 13:31:00 | 2014-08-21 13:31:00 | 0 |
| 8765 | end | 2014-08-21 13:42:00 | 2014-08-21 13:41:48 | 12 |
| 8864 | before | 2014-09-03 13:15:00 | 2014-09-03 13:14:45 | 15 |
| 8864 | peak | 2014-09-03 13:54:00 | 2014-09-03 13:54:12 | 12 |
| 8864 | end | 2014-09-03 14:23:00 | 2014-09-03 14:23:09 | 9 |

Original frames: 8765 [before](../data/spatial_review/8765_before.png),
[peak](../data/spatial_review/8765_peak.png), [end](../data/spatial_review/8765_end.png);
8864 [before](../data/spatial_review/8864_before.png),
[peak](../data/spatial_review/8864_peak.png), [end](../data/spatial_review/8864_end.png).
These local links require the downloaded data, which are not committed.

## Findings and revised interpretation

For **8765**, the peak frame shows a prominent saturated brightening near
the northeastern limb, with bright structure still visible at the end.
This is qualitatively consistent with the catalog's SSW position near
(-930, 176) arcseconds. The GOES/Hinode positions near x=-580 arcseconds
are further inside the disk. Interior active regions are also visible;
the three frames do not establish that they were inactive.

For **8864**, the peak frame shows a pronounced brightening near the
southeastern limb, persisting at the end. This is qualitatively consistent
with SSW near (-917, -250) arcseconds. GOES/Hinode positions near x=+285
arcseconds are on the other side of the disk. Other bright regions remain
visible and concurrent events cannot be ruled out.

The earlier [primary-source review](event-source-review.md) proposed studying
12148 and 12152 from optical coordinates and later daily region positions.
The new image context weakens those candidates as explanations of the
dominant peak brightening, and strengthens the eastern-limb NOAA/SSW
candidates 12149 and 12155. This revises an exploratory interpretation;
it does not erase the conflicting optical/radio evidence or certify a
single physical source for every record grouped under the same NOAA event ID.

| Event | Favored NOAA candidate | Disputed archive HARP | Corrected HARP established | Label change allowed |
| --- | ---: | ---: | --- | --- |
| 8765 | 12149 | 4466 | No | No |
| 8864 | 12155 | 4502 | No | No |

An image-plane location is not a NOAA or HARP identifier. No FITS/WCS
registration, time-aware heliographic conversion or HARP-boundary projection
was performed. Missing NOAA metadata for HARPs 4466/4502 remains unresolved.
The original 19 and 10 negative-label conflicts under the containing/location
rule are therefore not repaired or reclassified as model errors here.

## Limitations and next gate

Browse rendering, exposure changes, saturation and blooming prevent using
PNG brightness as a calibrated flux comparison. Three timestamps are not a
complete movie. Helioviewer metadata and rendering use separate requests;
watermarks were checked to ensure the reviewed times agree. This analysis
uses post-event evidence for label investigation only, never predictive inputs.
Model probabilities were not used to choose a region.

Next, register calibrated, time-stamped spatial observations to definitive
HARP boundaries with explicit coordinate frames and UTC/TAI handling. Until
that establishes identity, keep these cases in the unresolved association
review queue. Any future accepted corrections require a separate versioned
label set and a frozen inclusion policy before model training. Original labels
and the reserved 2024–2025 evaluation period remain untouched.

## Reproduction and preservation

```sh
python scripts/fetch_spatial_review.py
python scripts/review_spatial_evidence.py
python scripts/publish_reports.py --output artifacts/bilingual_reports_spatial
```

The commands preserve existing output directories. `data/spatial_review/`
contains original PNGs, metadata and a manifest with URLs, UTC retrieval
times and SHA-256 hashes. `artifacts/spatial_review/` contains `frames.csv`,
`case_dispositions.csv` and `report.json`, including the visual-review status
and an explicit prohibition on automatic relabeling. The review verifies
the previous source report and all image hashes. The earlier incomplete
SolarSoft archive download was not used as evidence.

API sources: [image metadata](https://api.helioviewer.org/docs/v2/api/api_groups/official_clients.html)
and [rendered screenshots](https://api.helioviewer.org/docs/v2/api/api_groups/screenshots.html).
The qualitative findings above come from the six inspected images and the
already frozen NOAA/SWAN-SF records, not from a new performance evaluation.
