"""Report every metric per year for the frozen baseline at the v2 operating point (config/full-metrics-v1.json)."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from scripts.audit_alarm_persistence import sha


def counts(y, alarm):
    tp = int(((y == 1) & alarm).sum())
    fp = int(((y == 0) & alarm).sum())
    fn = int(((y == 1) & ~alarm).sum())
    tn = int(((y == 0) & ~alarm).sum())
    return tp, fp, fn, tn


def threshold_metrics(y, p, threshold):
    tp, fp, fn, tn = counts(y, p >= threshold)
    n = tp+fp+fn+tn
    recall = tp/(tp+fn) if tp+fn else float('nan')
    precision = tp/(tp+fp) if tp+fp else float('nan')
    fpr = fp/(fp+tn) if fp+tn else float('nan')
    tnr = tn/(fp+tn) if fp+tn else float('nan')
    f1 = 2*precision*recall/(precision+recall) if tp else 0.0
    return dict(threshold=threshold, windows=n, positives=tp+fn, tp=tp, fp=fp, fn=fn, tn=tn,
                accuracy=(tp+tn)/n, always_negative_accuracy=(fp+tn)/n, recall=recall, precision=precision, f1=f1,
                balanced_accuracy=(recall+tnr)/2, fpr=fpr, far=1-precision if tp+fp else float('nan'), tss=recall-fpr)


def ranking_metrics(y, p):
    eps = 1e-15
    clipped = np.clip(p, eps, 1-eps)
    return dict(ap=float(average_precision_score(y, p)), roc_auc=float(roc_auc_score(y, p)),
                brier=float(brier_score_loss(y, p)), log_loss=float(log_loss(y, clipped, labels=[0, 1])),
                prevalence=float(y.mean()))


def bootstrap(frame, threshold, draws, seed):
    """Whole-HARP resampling; report the 95% interval for threshold metrics only."""
    rng = np.random.default_rng(seed)
    groups = {h: g for h, g in frame.groupby('harp')}
    harps = np.array(list(groups))
    out = []
    for _ in range(draws):
        pick = rng.choice(harps, size=len(harps), replace=True)
        sample = pd.concat([groups[h] for h in pick], ignore_index=True)
        if sample.target.sum() == 0:
            continue
        out.append(threshold_metrics(sample.target.to_numpy(), sample.probability.to_numpy(), threshold))
    table = pd.DataFrame(out)
    cols = ['recall', 'precision', 'f1', 'balanced_accuracy', 'fpr', 'far', 'tss']
    return {c: [float(table[c].quantile(0.025)), float(table[c].quantile(0.975))] for c in cols}


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    source = Path(config['predictions'])
    thresholds_path = Path(config['thresholds'])
    thresholds = json.loads(thresholds_path.read_text())
    rows, intervals = [], {}
    for year in config['years']:
        frame = pd.read_parquet(source/str(year)/'predictions.parquet',
                                columns=['harp', 'target', config['probability_column']])
        frame = frame.rename(columns={config['probability_column']: 'probability'})
        threshold = thresholds[str(year)][config['recall_target']]
        y, p = frame.target.to_numpy(), frame.probability.to_numpy()
        row = dict(year=year, **threshold_metrics(y, p, threshold), **ranking_metrics(y, p))
        rows.append(row)
        intervals[str(year)] = bootstrap(frame, threshold, config['bootstrap']['draws'], config['bootstrap']['seed'])
    output.mkdir(parents=True)
    table = pd.DataFrame(rows)
    table.to_csv(output/'metrics.csv', index=False)
    (output/'intervals.json').write_text(json.dumps(intervals, indent=2)+'\n')
    report = {'config_sha256': sha(config_path), 'thresholds_sha256': sha(thresholds_path),
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report, table, intervals


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/full-metrics-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    _, table, intervals = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(table.round(4).T.to_string())
    print(json.dumps(intervals, indent=1))
