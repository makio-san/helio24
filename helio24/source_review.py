"""Strict parsers for a bounded 2014 source review; no training-label updates."""
import json
import re

import pandas as pd


def parse_events(text, date):
    if date.year != 2014:
        raise ValueError('Region normalization is scoped to the 2014 review')
    if f':Date: {date:%Y %m %d}' not in text:
        raise ValueError('NOAA event report date mismatch')
    columns = dict(event_number=(0, 4), begin=(10, 15), maximum=(17, 22), end=(27, 32),
                   observatory=(34, 37), quality=(39, 40), kind=(43, 46),
                   location_frequency=(48, 55), particulars=(58, 74), region=(76, 80))
    records = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith(('#', ':')):
            continue
        if line.strip() == 'NO EVENT REPORTS.':
            continue
        row = {key: line[start:end].strip() for key, (start, end) in columns.items()}
        if not row['event_number'].isdigit() or not re.fullmatch('[A-Z]{3}', row['kind']):
            raise ValueError(f'Unexpected NOAA event row {number}')
        if row['region'] and not re.fullmatch(r'\d{4}', row['region']):
            raise ValueError(f'Unexpected 2014 NOAA region at row {number}')
        if any(not re.fullmatch(r'(?:[ABU]?\d{4}|////)', row[key]) for key in ['begin', 'maximum', 'end']):
            raise ValueError(f'Unexpected NOAA time at row {number}')
        row.update(line_number=number, raw=line, noaa_region=10000+int(row['region']) if row['region'] else None)
        records.append(row)
    return records


def match_xra(records, event):
    wanted = {key: pd.Timestamp(event[column]).strftime('%H%M')
              for key, column in [('begin', 'start_time'), ('maximum', 'peak_time'), ('end', 'end_time')]}
    matches = [row for row in records if row['kind'] == 'XRA' and
               all(row[key] == value for key, value in wanted.items()) and
               row['particulars'].split()[0] == event['goes_class']]
    if len(matches) != 1:
        raise ValueError(f'Expected one exact NOAA XRA match, found {len(matches)}')
    event_number = matches[0]['event_number']
    return matches[0], [row for row in records if row['event_number'] == event_number]


def parse_harp_table(text):
    lines = text.splitlines()
    if not lines or lines[0].split() != ['HARPNUM', 'NOAA_ARS']:
        raise ValueError('Unexpected HARP table header')
    result = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        harp, regions = line.split()
        harp = int(harp)
        if harp in result:
            raise ValueError('Duplicate HARP in mapping table')
        result[harp] = [int(value) for value in regions.split(',')]
    return result


def parse_jsoc(text, harp):
    response = json.loads(text)
    if response.get('status') != 0:
        raise ValueError(f'JSOC query failed: {response.get("error", response.get("status"))}')
    count = response.get('count')
    if not isinstance(count, int) or count < 0:
        raise ValueError('Invalid JSOC record count')
    if not count:
        return []
    columns = {entry['name']: entry['values'] for entry in response['keywords']}
    if not {'HARPNUM', 'T_REC', 'NOAA_ARS'} <= columns.keys() or any(len(v) != count for v in columns.values()):
        raise ValueError('Incomplete JSOC keyword response')
    records = pd.DataFrame(columns).to_dict('records')
    for row in records:
        if int(row['HARPNUM']) != harp or not row['T_REC'].endswith('_TAI'):
            raise ValueError('JSOC HARP or time scale mismatch')
        value = row['NOAA_ARS']
        row['noaa_association_available'] = value not in ('MISSING', '', None)
        row['noaa_regions'] = [int(x) for x in value.split(',')] if row['noaa_association_available'] else []
    return records


def parse_srs(text):
    """Retain stated validity and reported positions; no time propagation."""
    active, validity, rows = False, None, []
    for line in text.splitlines():
        if line.startswith('I.'):
            active, validity = True, line.strip()
        elif line.startswith('IA.'):
            break
        elif active and re.match(r'^\d{4}\s', line):
            parts = line.split()
            if not re.fullmatch(r'[NS]\d{2}[EW]\d{2}', parts[1]):
                raise ValueError('Unexpected SRS location')
            rows.append(dict(noaa_region=10000+int(parts[0]), location=parts[1], raw=line))
    if validity is None:
        raise ValueError('Missing SRS position validity')
    return validity, rows
