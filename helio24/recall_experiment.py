"""Frozen recall-first development experiment; no audit-period inputs."""
import numpy as np
import pandas as pd


def candidates():
    base = dict(n_estimators=600, max_depth=4, min_child_weight=5,
                reg_lambda=5, gamma=0, scale_pos_weight=1)
    variants = dict(control=dict(n_estimators=200, max_depth=3),
                    shallow=dict(max_depth=2), depth4={}, depth5=dict(max_depth=5),
                    depth6=dict(n_estimators=800, max_depth=6),
                    regularized=dict(min_child_weight=20, reg_lambda=20, gamma=.2),
                    positive_weight=dict(scale_pos_weight=3), region_weight={})
    return {name: base | changes for name, changes in variants.items()}


def region_weights(harp):
    counts = pd.Series(np.asarray(harp)).value_counts()
    weights = pd.Series(np.asarray(harp)).map(1 / counts).to_numpy()
    return weights / weights.mean()


def development_roles(table, frozen):
    if set(table.partition.unique()) != {1, 2, 3, 4}:
        raise ValueError('Only development partitions 1 through 4 are allowed')
    assignments = dict(train=[1, 2], calibration=[3], validation=[4])
    boundaries = {r['role']: pd.Timestamp(r['boundary']) for r in frozen['purge_audit'] if 'boundary' in r}
    groups, audit, seen = {}, [], set()
    for name, parts in assignments.items():
        frame = table[table.partition.isin(parts)].sort_values(['forecast_time', 'harp']).copy()
        before = len(frame)
        frame = frame[frame.prediction_end <= boundaries[name]].copy()
        removed = before - len(frame)
        shared = set(frame.harp) & seen
        shared_count = int(frame.harp.isin(shared).sum())
        frame = frame[~frame.harp.isin(shared)].copy()
        if (frame.groupby(['harp', 'forecast_time']).target.nunique() > 1).any():
            raise ValueError('Conflicting observation labels')
        duplicates = int(frame.duplicated(['harp', 'forecast_time']).sum())
        frame = frame.drop_duplicates(['harp', 'forecast_time'])
        expected = frozen['roles'][name]
        if (len(frame), int(frame.target.sum()), frame.harp.nunique()) != (expected['n'], expected['positives'], expected['harps']):
            raise ValueError(f'Frozen split mismatch: {name}')
        if frame.target.nunique() != 2:
            raise ValueError('Both classes are required')
        groups[name] = frame
        seen.update(frame.harp)
        audit.append(dict(role=name, boundary=str(boundaries[name]), boundary_removed=removed,
                          shared_harps=sorted(map(int, shared)), shared_harp_rows_removed=shared_count,
                          duplicates_removed=duplicates))
    for left, right in [('train', 'calibration'), ('calibration', 'validation')]:
        if groups[left].prediction_end.max() > groups[right].observation_start.min():
            raise ValueError('Temporal overlap remains')
    return groups, audit


def decision(row, control):
    checks = dict(recall_target=row['recall'] >= .95,
                  fewer_false_alarms=row['fp'] < control['fp'],
                  ap_noninferior=row['average_precision'] >= control['average_precision'],
                  brier_noninferior=row['brier'] <= control['brier'],
                  log_loss_noninferior=row['log_loss'] <= control['log_loss'])
    promising = all(checks.values())
    return dict(model=row['model'], checks=checks, promising=promising,
                stretch_target=promising and row['fp'] <= .9 * control['fp'],
                false_alarm_reduction=1-row['fp']/control['fp'])
