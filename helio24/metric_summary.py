"""Validate saved confusion counts and derive explicitly named summary scores."""
import math


def enrich(row):
    row = dict(row)
    for key in ['n', 'positives', 'tp', 'fp', 'fn', 'tn', 'alarms']:
        value = row[key]
        if not math.isfinite(value) or value < 0 or int(value) != value:
            raise ValueError(f'Invalid metric count: {key}')
    n, tp, fp, fn, tn = (row[k] for k in ['n', 'tp', 'fp', 'fn', 'tn'])
    if n == 0 or tp+fp+fn+tn != n or tp+fn != row['positives'] or tp+fp != row['alarms']:
        raise ValueError('Confusion counts disagree with totals')
    recall = tp/(tp+fn) if tp+fn else 0.
    precision = tp/(tp+fp) if tp+fp else 0.
    fpr = fp/(fp+tn) if fp+tn else 0.
    expected = dict(recall=recall, precision=precision, false_positive_rate=fpr,
                    false_alarm_ratio=fp/(tp+fp) if tp+fp else 0., tss=recall-fpr)
    for key, value in expected.items():
        if not math.isclose(row[key], value, rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError(f'Saved {key} disagrees with confusion counts')
    row.update(accuracy=(tp+tn)/n,
               balanced_accuracy=(recall+1-fpr)/2 if tp+fn and fp+tn else None,
               f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
               always_quiet_accuracy=(tn+fp)/n,
               precision_defined=bool(tp+fp), recall_defined=bool(tp+fn))
    return row
