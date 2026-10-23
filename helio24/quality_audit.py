"""Fail-closed parsing of historical JSOC quality and TAI clock strings."""
from datetime import datetime
import pandas as pd


def quality_value(value):
    text = str(value).strip()
    if text in {'MISSING', 'NaN', 'nan', '', 'None'}:
        return None
    number = int(text, 16 if text.lower().startswith('0x') else 10)
    if not 0 <= number <= 0xffffffff:
        raise ValueError('QUALITY must be an unsigned 32-bit value')
    return number


def tai_clock(value):
    """Parse a labelled TAI clock, without pretending to convert it to UTC."""
    return pd.Timestamp(datetime.strptime(value, '%Y.%m.%d_%H:%M:%S_TAI'))


def header_frame(payload, harp):
    if payload.get('status') != 0 or payload.get('count', 0) <= 0:
        raise ValueError('JSOC query returned no successful records')
    entries = payload['keywords']
    if len({item['name'] for item in entries}) != len(entries):
        raise ValueError('Duplicate JSOC keyword')
    values = {item['name']: item['values'] for item in entries}
    if any(len(v) != payload['count'] for v in values.values()):
        raise ValueError('JSOC column lengths disagree')
    frame = pd.DataFrame(values)
    if not pd.to_numeric(frame.HARPNUM).eq(harp).all():
        raise ValueError('Unexpected HARP in JSOC response')
    frame['Timestamp'] = frame.T_REC.map(tai_clock)
    frame['observation_clock'] = frame.T_OBS.map(tai_clock)
    frame['source_quality'] = pd.array(frame.QUALITY.map(quality_value), dtype='Int64')
    if frame.Timestamp.duplicated().any():
        raise ValueError('Duplicate JSOC record time')
    return frame
