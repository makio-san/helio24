"""Purged annual development folds with calibration-only alarm thresholds."""
import pandas as pd


def annual_fold(table, year):
    if not 2012 <= year <= 2023:
        raise ValueError('Only development years before the reserved test are allowed')
    calibration_start = pd.Timestamp(f'{year-1}-01-01', tz='UTC')
    evaluation_start = pd.Timestamp(f'{year}-01-01', tz='UTC')
    evaluation_end = pd.Timestamp(f'{year+1}-01-01', tz='UTC')
    masks = {
        'train': table.forecast_time.lt(calibration_start),
        'calibration': table.forecast_time.ge(calibration_start) & table.forecast_time.lt(evaluation_start),
        'evaluation': table.forecast_time.ge(evaluation_start) & table.forecast_time.lt(evaluation_end),
    }
    bounds = {'train': (None, calibration_start), 'calibration': (calibration_start, evaluation_start),
              'evaluation': (evaluation_start, evaluation_end)}
    groups, audit, seen = {}, [], set()
    for role, mask in masks.items():
        frame = table.loc[mask].copy()
        before = len(frame)
        start, end = bounds[role]
        frame = frame[frame.prediction_end.le(end)]
        if start is not None:
            frame = frame[frame.observation_start.ge(start)]
        boundary_removed = before-len(frame)
        shared = set(frame.harp) & seen
        before_shared = len(frame)
        frame = frame[~frame.harp.isin(shared)].sort_values(['forecast_time', 'harp']).copy()
        frame['role'] = role
        seen.update(frame.harp)
        groups[role] = frame
        audit.append({'role': role, 'rows': len(frame), 'positives': int(frame.target.sum()),
                      'boundary_removed': boundary_removed, 'shared_harp_rows_removed': before_shared-len(frame),
                      'shared_harps': sorted(map(int, shared))})
    return groups, audit


def evaluable_metrics(row):
    """Never interpret an absent positive class as measured zero recall."""
    row = dict(row)
    if not row['recall_defined']:
        for name in ['recall', 'balanced_accuracy', 'tss', 'average_precision']:
            row[name] = None
    if not row['precision_defined']:
        row['precision'] = row['false_alarm_ratio'] = None
    return row
