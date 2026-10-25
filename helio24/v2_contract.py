"""Fail-closed SWAN-SF-V2 observation and label contract."""
from collections import Counter
import re

import numpy as np
import pandas as pd

from helio24.data import FEATURE_COLUMNS, MAGNETIC_COLUMNS

V2_MEASUREMENTS = {name: name.lower() for name in MAGNETIC_COLUMNS}
EVENT_COLUMNS = [
    'harp_number', 'start_time', 'peak_time', 'end_time', 'goes_class',
    'confidence', 'has_goes', 'has_ssw', 'has_xrt', 'harp_vote',
    'max_pair_distance_deg',
]
ACCEPTED_CONFIDENCE = {'very_high', 'high', 'moderate', 'low'}
AMBIGUOUS_CONFIDENCE = {'very_low'}
KNOWN_CONFIDENCE = ACCEPTED_CONFIDENCE | AMBIGUOUS_CONFIDENCE | {'unverified'}
FLARE_PATTERN = re.compile(r'^(?P<letter>[ABCMX])(?P<magnitude>\d+(?:\.\d+)?)$')

# Effective instants are expressed on the continuous TAI clock. The archive
# period starts in 2010, when TAI-UTC was 34 seconds.
TAI_TRANSITIONS = (
    (pd.Timestamp('2012-07-01 00:00:35'), 35),
    (pd.Timestamp('2015-07-01 00:00:36'), 36),
    (pd.Timestamp('2017-01-01 00:00:37'), 37),
)


def tai_utc_offset(value):
    """Return TAI-UTC seconds for a naive 2010-2025 TAI timestamp."""
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is not None:
        raise ValueError('V2 observation clocks must be timezone-naive TAI values')
    if not pd.Timestamp('2010-01-01') <= stamp < pd.Timestamp('2026-01-01'):
        raise ValueError('TAI clock is outside the frozen dataset period')
    offset = 34
    for effective_tai, candidate in TAI_TRANSITIONS:
        if effective_tai-pd.Timedelta(seconds=1) <= stamp < effective_tai:
            raise ValueError('A leap-second instant cannot be represented by pandas')
        if stamp >= effective_tai:
            offset = candidate
    return offset


def tai_to_utc(value):
    """Convert the archive's naive JSOC TAI clock to timezone-aware UTC."""
    stamp = pd.Timestamp(value)
    return (stamp-pd.Timedelta(seconds=tai_utc_offset(stamp))).tz_localize('UTC')


def utc_to_tai(value):
    """Convert explicit UTC to the archive's timezone-naive TAI clock."""
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        raise ValueError('UTC input must have an explicit time zone')
    stamp = stamp.tz_convert('UTC')
    if not pd.Timestamp('2010-01-01T00:00Z') <= stamp < pd.Timestamp('2026-01-01T00:00Z'):
        raise ValueError('UTC clock is outside the frozen dataset period')
    offset = 34
    for effective_utc, candidate in [
        (pd.Timestamp('2012-07-01T00:00Z'), 35),
        (pd.Timestamp('2015-07-01T00:00Z'), 36),
        (pd.Timestamp('2017-01-01T00:00Z'), 37),
    ]:
        if stamp >= effective_utc:
            offset = candidate
    return (stamp.tz_localize(None)+pd.Timedelta(seconds=offset))


def parse_flare_class(value):
    match = FLARE_PATTERN.fullmatch(str(value).strip().upper())
    if not match:
        raise ValueError(f'Invalid GOES class: {value!r}')
    return match['letter'], float(match['magnitude'])


def prepare_events(frame):
    """Validate attached event rows; interpret catalog event clocks as UTC."""
    missing = set(EVENT_COLUMNS)-set(frame.columns)
    if missing:
        raise ValueError(f'Missing V2 event columns: {sorted(missing)}')
    events = frame[EVENT_COLUMNS].dropna(subset=['peak_time', 'goes_class']).copy()
    if events.empty:
        return events.assign(peak_time_utc=pd.Series(dtype='datetime64[ns, UTC]'))
    if events[['start_time', 'end_time', 'confidence']].isna().any().any():
        raise ValueError('Attached flare events require complete times and confidence')
    events['confidence'] = events.confidence.astype(str).str.lower()
    unknown = sorted(set(events.confidence)-KNOWN_CONFIDENCE)
    if unknown:
        raise ValueError(f'Unknown confidence tiers: {unknown}')
    for value in events.goes_class:
        parse_flare_class(value)
    for name in ['has_goes', 'has_ssw', 'has_xrt']:
        if not events[name].isin([True, False]).all():
            raise ValueError(f'{name} must be boolean')
    harp = pd.to_numeric(events.harp_number, errors='coerce')
    if harp.isna().any() or (harp <= 0).any() or not np.equal(harp, np.floor(harp)).all():
        raise ValueError('Attached events require positive integer HARP IDs')
    events['harp_number'] = harp.astype('int64')
    for name in ['start_time', 'peak_time', 'end_time']:
        values = pd.to_datetime(events[name], errors='raise')
        if values.dt.tz is not None:
            raise ValueError('V2 event clocks must be timezone-naive UTC values')
        events[name+'_utc'] = values.dt.tz_localize('UTC')
    if (events.start_time_utc > events.peak_time_utc).any() or (events.peak_time_utc > events.end_time_utc).any():
        raise ValueError('Flare start/peak/end order is invalid')
    return events.drop_duplicates().sort_values(['peak_time_utc', 'harp_number']).reset_index(drop=True)


def audit_event_rows(frame):
    """Validate attached events individually and quarantine malformed rows."""
    raw = frame[EVENT_COLUMNS].dropna(subset=['peak_time', 'goes_class']).drop_duplicates()
    valid, errors = [], Counter()
    for index in range(len(raw)):
        try:
            valid.append(prepare_events(raw.iloc[[index]]))
        except ValueError as error:
            errors[str(error)] += 1
    events = (pd.concat(valid, ignore_index=True) if valid
              else prepare_events(pd.DataFrame(columns=EVENT_COLUMNS)))
    return events, dict(errors)


def prepare_unassigned_major_events(frame):
    """Validate the complete GOES M/X inventory that has no trusted HARP."""
    required = {'event_id', 'peak_time', 'goes_class'}
    if set(frame.columns) != required:
        raise ValueError('Unassigned inventory must contain event_id, peak_time and goes_class only')
    result = frame.copy()
    if result.empty:
        return result.assign(peak_time_utc=pd.Series(dtype='datetime64[ns, UTC]'))
    if result.event_id.isna().any() or result.event_id.duplicated().any():
        raise ValueError('Unassigned event IDs must be present and unique')
    peak = pd.to_datetime(result.peak_time, errors='raise')
    if peak.dt.tz is None:
        raise ValueError('Unassigned event peak times must have an explicit UTC zone')
    result['peak_time_utc'] = peak.dt.tz_convert('UTC')
    if not all(parse_flare_class(value)[0] in {'M', 'X'} for value in result.goes_class):
        raise ValueError('Unassigned inventory may contain only M/X events')
    return result.sort_values('peak_time_utc').reset_index(drop=True)


def label_windows(windows, attached_events, unassigned_major_events, *, inventory_complete=False):
    """Build GOES M/X labels using half-open intervals and fail-closed ambiguity rules."""
    if not inventory_complete:
        raise ValueError('Complete unassigned GOES M/X inventory is required before labeling')
    required = {'harp', 'forecast_time', 'prediction_end'}
    if not required <= set(windows.columns):
        raise ValueError(f'Missing window columns: {sorted(required-set(windows.columns))}')
    result = windows.copy()
    for name in ['forecast_time', 'prediction_end']:
        values = pd.to_datetime(result[name], errors='raise')
        if values.dt.tz is None:
            raise ValueError('Window times must have an explicit UTC zone')
        result[name] = values.dt.tz_convert('UTC')
    if (result.forecast_time >= result.prediction_end).any():
        raise ValueError('Prediction intervals must have positive duration')
    attached = prepare_events(attached_events)
    unassigned = prepare_unassigned_major_events(unassigned_major_events)
    result['target'] = 0
    result['label_status'] = 'negative'
    for index, window in result.iterrows():
        in_window = attached[
            attached.harp_number.eq(window.harp)
            & attached.peak_time_utc.ge(window.forecast_time)
            & attached.peak_time_utc.lt(window.prediction_end)
            & attached.has_goes
        ].copy()
        in_window['strong'] = [parse_flare_class(value)[0] in {'M', 'X'}
                               for value in in_window.goes_class]
        accepted = in_window[in_window.strong & in_window.confidence.isin(ACCEPTED_CONFIDENCE)]
        ambiguous = in_window[in_window.strong & in_window.confidence.isin(AMBIGUOUS_CONFIDENCE)]
        unknown_region = unassigned[
            unassigned.peak_time_utc.ge(window.forecast_time)
            & unassigned.peak_time_utc.lt(window.prediction_end)
        ]
        if not accepted.empty:
            result.at[index, 'target'] = 1
            result.at[index, 'label_status'] = 'positive'
        elif not ambiguous.empty:
            result.at[index, 'label_status'] = 'excluded_ambiguous_harp'
        elif not unknown_region.empty:
            result.at[index, 'label_status'] = 'excluded_unassigned_major_event'
    return result


def extract_window(frame):
    """Validate one 60-row V2 window and compute native finite-value summaries."""
    required = {'harp_number', 'obs_start', *V2_MEASUREMENTS.values()}
    missing = required-set(frame.columns)
    if missing:
        raise ValueError(f'Missing V2 observation columns: {sorted(missing)}')
    if len(frame) != 60 or frame.harp_number.nunique() != 1:
        raise ValueError('A window must contain 60 rows from one HARP')
    values = frame.copy().sort_values('obs_start')
    clocks = pd.to_datetime(values.obs_start, errors='raise')
    if clocks.dt.tz is not None:
        raise ValueError('V2 observation clocks must be timezone-naive TAI values')
    expected = pd.date_range(clocks.iloc[0], periods=60, freq='12min')
    if clocks.duplicated().any() or not np.array_equal(clocks.to_numpy(), expected.to_numpy()):
        raise ValueError('Observation window must have an exact 12-minute TAI cadence')
    forecast_tai = clocks.iloc[0]+pd.Timedelta(hours=12)
    if tai_utc_offset(clocks.iloc[0]) != tai_utc_offset(forecast_tai):
        raise ValueError('Observation windows crossing a leap second are excluded')
    numeric = values[list(V2_MEASUREMENTS.values())].apply(pd.to_numeric, errors='coerce')
    array = numeric.to_numpy(dtype=float, na_value=np.nan, copy=True)
    array[~np.isfinite(array)] = np.nan
    missing_fraction = np.isnan(array).mean(axis=0)
    if (missing_fraction > 0.2).any():
        raise ValueError('More than 20% missing values in at least one magnetic parameter')
    counts = np.isfinite(array).sum(axis=0)
    means = np.nansum(array, axis=0)/counts
    std = np.sqrt(np.nansum((array-means)**2, axis=0)/counts)
    summaries = np.column_stack([means, std, array[-1], array[-1]-array[0]])
    return ({'harp': int(values.harp_number.iloc[0]),
             'observation_start': tai_to_utc(clocks.iloc[0]),
             'forecast_time': tai_to_utc(forecast_tai),
             'prediction_end': tai_to_utc(forecast_tai)+pd.Timedelta(hours=24),
             'missing_fraction': float(np.isnan(array).sum()/array.size)}
            | dict(zip(FEATURE_COLUMNS, summaries.ravel())))
