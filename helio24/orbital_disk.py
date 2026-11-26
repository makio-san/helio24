"""Orbital phase and disk position features of a forecast window (config/orbital-disk-v1.json).

Orbital phase depends only on the UTC time of day of the forecast time. Disk position comes from the latest
NOAA SRS issued at or before the forecast time minus 30 minutes (the availability rule of
config/region-context-v1.json), rotated from the time its locations are valid to the forecast time at a fixed rate.
No function here reads a label, a label status, a role or a date feature.
"""
import numpy as np
import pandas as pd

KEY = ['harp', 'forecast_time']
FORBIDDEN = {'target', 'label_status', 'label_status_v2', 'role'}
SAFETY = pd.Timedelta('30min')
ROTATION_DEG_PER_DAY = 13.2
PERIODS_HOURS = [24, 12]
ORBITAL = ['orbit__sin_24h', 'orbit__cos_24h', 'orbit__sin_12h', 'orbit__cos_12h']
FLAG = 'disk__srs_available'
POSITION = [FLAG, 'disk__abs_cmd_deg', 'disk__abs_latitude_deg', 'disk__cos_heliocentric_angle']
BAND = 'disk_band'
SIDE = 'disk_side'
BANDS = ['cmd_0_30', 'cmd_30_60', 'cmd_over_60', 'no_srs_location']
SIDES = ['east', 'west', 'no_srs_location']


def _refuse_labels(frame):
    found = FORBIDDEN & set(frame.columns)
    if found:
        raise ValueError(f'Orbital and disk features never see labels, label status or roles: {sorted(found)}')
    if not set(KEY) <= set(frame.columns):
        raise ValueError('The frame needs harp and forecast_time')
    if frame.duplicated(KEY).any():
        raise ValueError('Duplicate forecast keys')


def utc_hour(times):
    """Fractional UTC hour of day in [0, 24); the calendar date is dropped."""
    times = pd.to_datetime(pd.Series(times), utc=True)
    return (times-times.dt.floor('D')).dt.total_seconds().to_numpy()/3600


def orbital_phase_features(frame):
    """Sine and cosine of the UTC hour of the forecast time at 24 and 12 hour periods."""
    _refuse_labels(frame)
    hour = utc_hour(frame.forecast_time)
    out = pd.DataFrame(index=frame.index)
    for period in PERIODS_HOURS:
        angle = 2*np.pi*hour/period
        out[f'orbit__sin_{period}h'] = np.sin(angle)
        out[f'orbit__cos_{period}h'] = np.cos(angle)
    return out[ORBITAL]


def parse_location(location):
    """'N12W50' -> (12.0, 50.0): latitude positive north, central meridian distance positive west, degrees."""
    text = str(location)
    if len(text) != 6 or text[0] not in 'NS' or text[3] not in 'EW' or not (text[1:3]+text[4:6]).isdigit():
        raise ValueError(f'Unknown SRS location: {location}')
    latitude = float(text[1:3])*(1 if text[0] == 'N' else -1)
    longitude = float(text[4:6])*(1 if text[3] == 'W' else -1)
    return latitude, longitude


def srs_positions(issued, rows):
    """Per (issued_utc, noaa) SRS row: latitude, central meridian distance and the time the locations are valid.

    SRS locations are valid at 00:00 UTC of the product date (the header line 'Locations Valid at DD/2400Z' of the
    day before); `issued` carries the product date of each issue time.
    """
    if issued.issued_utc.duplicated().any():
        raise ValueError('Two SRS products share one issue time')
    valid = pd.Series(pd.to_datetime(issued.date.astype(str)).dt.tz_localize('UTC').to_numpy(), index=issued.issued_utc)
    table = rows[['issued_utc', 'noaa', 'location', 'area']].copy()
    parsed = [parse_location(value) for value in table.location]
    table['latitude'] = [p[0] for p in parsed]
    table['longitude'] = [p[1] for p in parsed]
    table['valid_utc'] = pd.to_datetime(valid.reindex(table.issued_utc).to_numpy(), utc=True)
    if table.valid_utc.isna().any():
        raise ValueError('SRS row without a product date')
    return table[['issued_utc', 'noaa', 'area', 'latitude', 'longitude', 'valid_utc']]


def latest_issue(issued_times, forecast_times, safety=SAFETY):
    """Latest SRS issue time at or before each forecast time minus the safety margin (NaT if none)."""
    order = np.sort(pd.to_datetime(pd.Series(issued_times), utc=True).to_numpy())
    cutoff = (pd.to_datetime(pd.Series(forecast_times), utc=True)-safety).to_numpy()
    index = np.searchsorted(order, cutoff, side='right')-1
    out = pd.Series(pd.NaT, index=range(len(cutoff)), dtype='datetime64[ns, UTC]')
    valid = index >= 0
    out[valid] = pd.to_datetime(order[index[valid]], utc=True)
    return out


def disk_position_features(frame, mapping, issued, positions):
    """Causal disk position per window from the latest available SRS row of the HARP's NOAA numbers.

    The NOAA numbers are those of the HARP's NOAA_ARS on the forecast date. With several matched rows the row with
    the largest area is used (ties: lowest NOAA number). Its central meridian distance is rotated from the valid
    time of the SRS locations to the forecast time at ROTATION_DEG_PER_DAY and clipped to -90 to 90 degrees.
    Without a matched row disk__srs_available is 0 and every other value is missing. Also returns the reporting-only
    band and side of the rotated position, which are never model inputs.
    """
    _refuse_labels(frame)
    base = frame[KEY].copy().reset_index(drop=True)
    base['forecast_time'] = pd.to_datetime(base.forecast_time, utc=True)
    base['date'] = base.forecast_time.dt.date
    base['available'] = latest_issue(issued.issued_utc, base.forecast_time).to_numpy()
    merged = base.reset_index().merge(mapping[['harp', 'date', 'noaa']], on=['harp', 'date'], how='inner')
    merged = merged.merge(positions, left_on=['available', 'noaa'], right_on=['issued_utc', 'noaa'], how='inner')
    chosen = merged.sort_values(['index', 'area', 'noaa'], ascending=[True, False, True]).drop_duplicates('index').set_index('index')
    days = (chosen.forecast_time-chosen.valid_utc).dt.total_seconds()/86400
    longitude = np.clip(chosen.longitude+ROTATION_DEG_PER_DAY*days, -90, 90)
    latitude = chosen.latitude
    out = pd.DataFrame(index=base.index)
    out[FLAG] = out.index.isin(chosen.index).astype(float)
    out['disk__abs_cmd_deg'] = longitude.abs().reindex(out.index)
    out['disk__abs_latitude_deg'] = latitude.abs().reindex(out.index)
    out['disk__cos_heliocentric_angle'] = (np.cos(np.radians(latitude))*np.cos(np.radians(longitude))).reindex(out.index)
    out[BAND] = disk_band(out['disk__abs_cmd_deg'])
    out[SIDE] = np.where(out[FLAG].eq(0), 'no_srs_location', np.where(longitude.reindex(out.index) >= 0, 'west', 'east'))
    out.index = frame.index
    return out[[*POSITION, BAND, SIDE]]


def disk_band(abs_cmd):
    """Reporting band of the absolute central meridian distance: 0 to 30, 30 to 60, over 60 degrees, or no location."""
    value = pd.Series(abs_cmd).to_numpy(dtype=float)
    return np.select([np.isnan(value), value <= 30, value <= 60], ['no_srs_location', 'cmd_0_30', 'cmd_30_60'], 'cmd_over_60')
