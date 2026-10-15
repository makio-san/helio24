# Event-label provenance investigation

The ten event/window conflicts are reproducible in the official partition-4
archive. Event 8864 is present in location-based history for HARP 4502, absent
from its NOAA-number history, and absent from positive filename labels throughout
this archive. This identifies a disagreement between association channels, not
an arithmetic error in the audit's 24-hour interval check. It does not identify
the physically correct association or prove the original slicing implementation.

## Evidence for catalog event 8864

The integrated catalog reports M2.5, start 2014-09-03 13:20 UTC, peak 13:54 UTC,
and NOAA region 12155. At 13:48 UTC, HARP 4502 contains `M2.5@8864:Primary` in
`MFLARE_LABEL_LOC`, but `MFLARE_LABEL` is empty. No other HARP in this archive
supplies history evidence for this event; no positive filename references it.

The catalog location is longitude 18°, latitude −14°. The HARP box at 13:48 UTC
spans longitude 8.314° to 30.087° and latitude −24.940° to −11.551°. The catalog
location falls inside that box. The row has QUALITY=0 and IS_TMFI=True; these
measurement flags do not adjudicate the flare's physical source.

Ten HARP-4502 forecasts issued hourly from 2014-09-02 21:24 through 2014-09-03
06:24 UTC contain the peak in their future 24 hours, yet all ten filenames are
FQ. The peak is far from the forecast boundaries. Its annotation is six minutes
earlier, compatible with both timing rules below. Discretization cannot explain
these ten negative labels.

The catalog also contains differing location evidence: its GOES position is
(18, −14), while its stored NOAA centroid is approximately (−80.84, −20).
The SSW association is not verified and the Hinode association is verified.
This warrants source adjudication; it does not justify choosing a corrected
NOAA ID or relabeling windows from coordinates alone.

## Annotation timestamps

All 214 distinct verified M/X history records in this archive satisfy
`annotation_time <= peak_time < annotation_time + 12 minutes`. Offsets are zero
to eleven minutes before peak. Only 125 satisfy the conservative nearest-sample
condition `abs(annotation_time - peak_time) <= 6 minutes`.

| History channel | Verified records | Within six minutes | Containing 12-minute interval |
| --- | ---: | ---: | ---: |
| NOAA M | 96 | 57 | 96 |
| Location M | 98 | 58 | 98 |
| NOAA X | 10 | 5 | 10 |
| Location X | 10 | 5 | 10 |

Records are deduplicated by HARP, timestamp, channel and flare ID; they are not
214 independent physical flares. All 45 location-history time exclusions from
the earlier audit satisfy the containing-interval rule. Their rejection does
not by itself establish bad identity. The pattern supports interval-start
placement for this release, rather than nearest-sample placement described in
the paper. It is not a claim about all releases or all flare classes.

## Association-method differences

Using verified histories without the six-minute restriction gives 105 HARP/event
pairs supported by both methods, three location-only pairs and one NOAA-only pair:

| Catalog event | HARP | History support |
| --- | --- | --- |
| 8765 | 4466 | Location only |
| 8864 | 4502 | Location only |
| 9053 | 4678 | NOAA number only |
| 9529 | 4920 | Location only |

Filename evidence supplies event 9053 for HARP 4678 despite its absent location
history. For event 9529, filenames instead identify HARP 4941. Combining filenames
and location histories therefore needs an explicit ambiguity policy. Changing
only the timing filter can expose additional associations.

The original audit used filenames plus conservatively filtered location history.
Its 86/87 detection result is conditional on that definition; it is not definitive
event-level performance while association methods remain unresolved.

## Reproduction and preservation

Run `python scripts/investigate_event_provenance.py` after the event audit.
It checks the official archive MD5, scans all 51,261 windows, checks catalog
IDs and magnitudes, and exports both histories, offsets, case measurements and
filenames to ignored `artifacts/event_provenance/`. Existing outputs are not replaced.

Source and artifact hashes link the investigation to the existing audit. The
dashboard's optional **Label provenance investigation** section verifies these
hashes before displaying evidence. Tests distinguish timing rules, retain
cross-region channel disagreements, exercise a synthetic archive end to end and
reject altered evidence.

Original labels, models, thresholds and historical audit outputs remain unchanged.
The next labeling study should version the containing-interval rule, keep the
NOAA and location channels separate, exclude or adjudicate multi-HARP events, and
report sensitivity before using new labels for training.

Source context: [SWAN-SF original paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7351763/),
flare integration and slicing sections. The numerical findings above come from
the checked archive and integrated catalog.
