"""Non-overlapping probability-fitting and threshold-selection periods."""
import pandas as pd


def split_calibration(frame, evaluation_year):
    if evaluation_year >= 2024:
        raise ValueError('Reserved test is closed')
    boundary = pd.Timestamp(f'{evaluation_year-1}-07-01', tz='UTC')
    early = frame[frame.prediction_end.le(boundary)].copy()
    late = frame[frame.observation_start.ge(boundary)].copy()
    shared = set(early.harp) & set(late.harp)
    before = len(late)
    late = late[~late.harp.isin(shared)].copy()
    audit = {'early_rows':len(early), 'early_positives':int(early.target.sum()),
             'late_rows':len(late), 'late_positives':int(late.target.sum()),
             'boundary_removed':len(frame)-len(early)-before,
             'shared_harp_rows_removed':before-len(late)}
    return early, late, audit
