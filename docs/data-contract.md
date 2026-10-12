# SWAN-SF data contract

Sources checked before training:

- [Angryk et al. (2020), Methods and Data Records](https://pmc.ncbi.nlm.nih.gov/articles/PMC7351763/)
- [Ahmadzadeh et al. (2021), section 2.1](https://arxiv.org/pdf/2103.07542)
- [Official dataset](https://doi.org/10.7910/DVN/EBCFKM), archive checksums and actual files.

The published benchmark uses 12-hour observations followed immediately by a
24-hour prediction window. The outcome is the strongest flare in that window.
M and X map to 1; B, C and flare-quiet (FQ) map to 0. C-class records are retained.

Files are tab-separated despite their `.csv` extension. The filename contains
the outcome, HARP identifier, first timestamp, and last timestamp. Sixty samples
at 12-minute cadence span 11h48m between their first and last timestamps.
The forecast starts 12 hours after the first timestamp, **not at the last row**.
Intervals are `[observation_start, forecast_time)` and
`[forecast_time, forecast_time + 24h)`. Times are treated as the source's UTC
timeline. The code does not convert them to local time.

A HARP can contain multiple NOAA active regions. The application therefore
labels its selector as HARP, rather than claiming a one-to-one NOAA mapping.
These are definitive SHARP archive products, not measurements proven to have
been available in real time. Replay is a retrospective experiment.

## Implementation decisions

The inspected instance files have 55 columns including `Timestamp`; this differs
from the publication's count for the original region series. Only 24 explicitly
listed magnetic columns enter the model. IDs, filename labels, flare histories,
coordinates, X-ray measurements, and catalog information are excluded.

Means, population standard deviations, final values, and endpoint differences
use the observation window only. Rows with nonzero QUALITY or false/missing
IS_TMFI are masked. Non-numeric and infinite measurements become missing.
A window is rejected if any magnetic parameter is more than 20% missing after
masking. Remaining feature gaps are imputed using training medians only.

For each labeled flare, its identifier and magnitude are checked against the
official integrated catalog. Records whose catalog peak lies outside the exact
forecast interval are excluded, including boundary-rounding ambiguities.
This checks the recorded event, not the completeness of every FQ label or whether
another stronger event was omitted. FQ labels rely on the published benchmark.

The first experiment uses a class-blind 10% sample of partitions 1, 3 and 5.
Training uses 1, validation uses 3, and final testing uses 5. Partitions 2 and 4
are reserved for later work. This is a development sample, not a full benchmark.
Sampling is not a random train/test split. The official partitions remain intact.
Actual date ranges are reported from downloaded files, not copied from other
dataset versions. Windows crossing the next set's observation start are purged;
HARP identifiers already seen in an earlier set are excluded from later sets.

Metrics count forecast windows, not unique flare events. Windows within one
split can overlap. Confidence intervals must account for this dependence.
An archive probability is not a prediction of satellite damage or Earth impact.
