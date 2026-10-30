"""Nested calendar calibration windows following a shared classifier fit period."""
import pandas as pd
from helio24.walk_forward import annual_fold


def calibration_windows(table, year):
    original, _ = annual_fold(table, year)
    start = pd.Timestamp(f'{year-2}-01-01', tz='UTC')
    recent = pd.Timestamp(f'{year-1}-01-01', tz='UTC')
    end = pd.Timestamp(f'{year}-01-01', tz='UTC')
    train = table[table.forecast_time.lt(start) & table.prediction_end.le(start)].copy()
    two = table[table.observation_start.ge(start) & table.forecast_time.lt(end) & table.prediction_end.le(end)].copy()
    two = two[~two.harp.isin(train.harp)].copy()
    one = two[two.observation_start.ge(recent)].copy()
    evaluation = original['evaluation']
    before = len(evaluation)
    evaluation = evaluation[~evaluation.harp.isin(set(train.harp) | set(two.harp))].copy()
    groups = {'train':train,'one_year':one,'two_year':two,'evaluation':evaluation}
    audit = {'additional_evaluation_rows_removed':before-len(evaluation),'roles':{}}
    for role, frame in groups.items():
        groups[role] = frame.sort_values(['forecast_time','harp']).copy()
        audit['roles'][role] = {'rows':len(frame),'positives':int(frame.target.sum()),
            'regions':int(frame.harp.nunique()),'positive_regions':int(frame.loc[frame.target.eq(1),'harp'].nunique())}
    return groups, audit
