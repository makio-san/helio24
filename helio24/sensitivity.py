"""Compare association conventions using immutable forecasts and catalog peaks."""
import json

import pandas as pd

from helio24.event_mapping import parse_annotations
from helio24.events import match_events
from helio24.full_data import sha256

VARIANTS = [(timing, channel) for timing in ['nearest', 'containing']
            for channel in ['noaa', 'location', 'union']]
REFERENCE = 'nearest_location'
CHANNELS = {'noaa': ['MFLARE_LABEL', 'XFLARE_LABEL'],
            'location': ['MFLARE_LABEL_LOC', 'XFLARE_LABEL_LOC']}


def verify_report(root, directory, check_code=False):
    report = json.loads((directory / 'report.json').read_text())
    for key, base in [('source_hashes', root), ('artifact_hashes', directory)]:
        for name, digest in report[key].items():
            if sha256(base / name) != digest:
                raise ValueError(f'Sensitivity input changed: {name}')
    if check_code:
        for name, digest in report['code_hashes'].items():
            if sha256(root / name) != digest:
                raise ValueError(f'Generating code changed: {name}')
    return report


def build_mapping(annotations, filenames, catalog, timing, channel):
    if (timing, channel) not in VARIANTS:
        raise ValueError('Unknown sensitivity variant')
    if catalog.flare_id.duplicated().any():
        raise ValueError('Duplicate catalog event')
    catalog = catalog.set_index('flare_id')
    pairs = {}

    def peak_for(flare_id, magnitude):
        if flare_id not in catalog.index or catalog.loc[flare_id, 'goes_class'] != magnitude:
            raise ValueError(f'Catalog mismatch for event {flare_id}')
        return pd.Timestamp(catalog.loc[flare_id, 'peak_time'])

    def add(harp, flare_id, source):
        pairs.setdefault((int(harp), int(flare_id)), set()).add(source)

    for row in filenames[filenames.target.eq(1)].itertuples(index=False):
        parsed = parse_annotations(row.label)
        if len(parsed) != 1 or parsed[0][1] != row.flare_id:
            raise ValueError('Invalid positive filename label')
        magnitude, flare_id, verification = parsed[0]
        if verification not in ('Primary', 'Secondary'):
            continue
        peak = peak_for(flare_id, magnitude)
        if not pd.Timestamp(row.forecast_time) <= peak < pd.Timestamp(row.prediction_end):
            raise ValueError('Filename event outside forecast interval')
        add(row.harp, flare_id, 'filename')

    sources = CHANNELS['noaa'] + CHANNELS['location'] if channel == 'union' else CHANNELS[channel]
    accepted = annotations[annotations.source.isin(sources) &
                           annotations.verification.isin(['Primary', 'Secondary'])]
    for row in accepted.itertuples(index=False):
        peak, stamp = peak_for(row.flare_id, row.magnitude), pd.Timestamp(row.timestamp)
        compatible = (abs(peak-stamp) <= pd.Timedelta(minutes=6) if timing == 'nearest'
                      else stamp <= peak < stamp+pd.Timedelta(minutes=12))
        if compatible:
            source = 'history_noaa' if row.source in CHANNELS['noaa'] else 'history_location'
            add(row.harp, row.flare_id, source)
    return pd.DataFrame([dict(harp=harp, flare_id=flare_id, evidence=';'.join(sorted(sources)))
                         for (harp, flare_id), sources in sorted(pairs.items())],
                        columns=['harp', 'flare_id', 'evidence'])


def compare(windows, annotations, filenames, catalog):
    """Return metrics and complete evidence tables, without modifying any input."""
    mappings, matches = [], []
    for timing, channel in VARIANTS:
        variant = timing+'_'+channel
        mapping = build_mapping(annotations, filenames, catalog, timing, channel)
        mappings.append(mapping.assign(variant=variant))
        matches.append(match_events(windows, mapping, catalog).assign(variant=variant))
    events = pd.concat(matches, ignore_index=True)
    evaluated = events[events.status.eq('evaluated')]
    groups = evaluated.groupby('flare_id').agg(variants=('variant', 'nunique'), harps=('harp', 'nunique'))
    common_ids = groups.index[(groups.variants == len(VARIANTS)) & (groups.harps == 1)]
    events['common_same_harp'] = events.flare_id.isin(common_ids)
    conflicts = []
    by_region = dict(tuple(windows.groupby('harp')))
    for event in evaluated.itertuples(index=False):
        local = by_region[event.harp]
        negative = local[local.target.eq(0) & (local.forecast_time <= event.peak_time) &
                         (local.prediction_end > event.peak_time)]
        for stamp in negative.forecast_time:
            conflicts.append(dict(variant=event.variant, flare_id=event.flare_id,
                                  harp=int(event.harp), forecast_time=stamp))
    conflicts = pd.DataFrame(conflicts, columns=['variant', 'flare_id', 'harp', 'forecast_time'])
    metrics = []
    for variant, group in events.groupby('variant', sort=False):
        eligible = group[group.status.eq('evaluated')]
        fully = eligible[eligible.fully_covered]
        common = eligible[eligible.common_same_harp]
        metrics.append(dict(
            variant=variant, catalog_events=len(group), evaluated=len(eligible),
            detected=int(eligible.detected.sum()), recall=float(eligible.detected.mean()) if len(eligible) else None,
            before_start=int(eligible.before_start.sum()), fully_covered=len(fully),
            fully_detected=int(fully.detected.sum()),
            fully_covered_recall=float(fully.detected.mean()) if len(fully) else None,
            common_events=len(common), common_detected=int(common.detected.sum()),
            common_recall=float(common.detected.mean()) if len(common) else None,
            negative_label_conflicts=int(conflicts.variant.eq(variant).sum()),
            **{status: int(group.status.eq(status).sum())
               for status in ['unmapped', 'ambiguous', 'no_forecast_coverage']}))
    columns = ['flare_id', 'status', 'harp', 'detected']
    reference = events[events.variant.eq(REFERENCE)][columns]
    transitions = events[['variant', *columns]].merge(reference, on='flare_id', suffixes=('', '_reference'),
                                                    validate='many_to_one')
    same_harp = transitions.harp.eq(transitions.harp_reference) | (
        transitions.harp.isna() & transitions.harp_reference.isna())
    transitions['changed'] = (~same_harp | transitions.status.ne(transitions.status_reference) |
                              transitions.detected.ne(transitions.detected_reference))
    return dict(metrics=pd.DataFrame(metrics), events=events,
                mappings=pd.concat(mappings, ignore_index=True), transitions=transitions, conflicts=conflicts)


def assert_reference(events, original):
    columns = ['flare_id', 'harp', 'status', 'detected', 'before_start', 'available_forecasts',
               'coverage_hours', 'fully_covered', 'alarm_windows', 'alarm_episodes']
    def normalized(frame):
        return frame[columns].sort_values('flare_id').reset_index(drop=True)
    pd.testing.assert_frame_equal(normalized(events[events.variant.eq(REFERENCE)]),
                                  normalized(original), check_dtype=False)


def load_sensitivity(root):
    directory = root / 'artifacts/label_sensitivity'
    report = verify_report(root, directory)
    return report, pd.read_csv(directory / 'metrics.csv'), pd.read_csv(directory / 'transitions.csv')
