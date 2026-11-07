"""Evaluate the frozen alarm persistence protocol (config/alarm-persistence-v1.json)."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.events import HOUR, alarm_episodes

DRAWS = 1000
SEED = 24


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def persistent_alarm(frame, arm, threshold, k):
    """Alarm at a window only if it and the k-1 preceding windows are consecutive hours above threshold."""
    above = frame[arm].ge(threshold)
    adjacent = frame.groupby('harp').forecast_time.diff().eq(HOUR)
    start = ~(above & above.shift(fill_value=False) & adjacent)
    run_length = above.astype(int).groupby(start.cumsum()).cumsum()
    return run_length.ge(k)


def positive_run_stats(windows):
    previous = windows.groupby('harp').forecast_time.shift()
    continues = windows.target.eq(1) & windows.groupby('harp').target.shift().eq(1) \
        & windows.forecast_time.sub(previous).eq(HOUR)
    run_id = (~continues).cumsum()
    positive = windows[windows.target.eq(1)]
    delays = []
    runs = alarmed = 0
    for _, run in positive.groupby(run_id[positive.index]):
        runs += 1
        hit = run[run.alarm]
        if len(hit):
            alarmed += 1
            delays.append((hit.forecast_time.min()-run.forecast_time.min()).total_seconds()/3600)
    return runs, alarmed, delays


def evaluate(frame, arm, threshold, k):
    """Window, episode and positive-run counts plus per-HARP counts for one rule."""
    frame = frame.sort_values(['harp', 'forecast_time']).reset_index(drop=True)
    if frame.duplicated(['harp', 'forecast_time']).any():
        raise ValueError('Duplicate forecast key')
    alarm = persistent_alarm(frame, arm, threshold, k)
    data = frame[['harp', 'forecast_time', 'target', 'missing_fraction']].assign(probability=alarm.astype(float))
    windows, episodes = alarm_episodes(data, .5)
    target = windows.target.eq(1)
    tp = int((windows.alarm & target).sum())
    fp = int((windows.alarm & ~target).sum())
    fn = int((~windows.alarm & target).sum())
    tn = int((~windows.alarm & ~target).sum())
    hit = ~episodes.all_negative
    runs, alarmed, delays = positive_run_stats(windows)
    out = dict(threshold=threshold, k=k, tp=tp, fp=fp, fn=fn, tn=tn,
        recall=tp/(tp+fn) if tp+fn else None, precision=tp/(tp+fp) if tp+fp else None,
        alarm_windows=tp+fp, episodes=len(episodes), hit_episodes=int(hit.sum()),
        episode_precision=float(hit.mean()) if len(episodes) else None,
        all_negative_episodes=int((~hit).sum()), positive_runs=runs, positive_runs_alarmed=alarmed,
        positive_run_recall=alarmed/runs if runs else None,
        median_alarm_delay_hours=float(np.median(delays)) if delays else None,
        max_alarm_delay_hours=float(np.max(delays)) if delays else None)
    harps = pd.Index(sorted(frame.harp.unique()), name='harp')
    per_harp = pd.DataFrame(index=harps)
    per_harp['fp'] = (windows.alarm & ~target).groupby(windows.harp).sum().reindex(harps, fill_value=0)
    per_harp['episodes'] = episodes.groupby('harp').size().reindex(harps, fill_value=0)
    per_harp['hit_episodes'] = episodes[hit].groupby('harp').size().reindex(harps, fill_value=0)
    return out, per_harp


def paired_bootstrap(control, candidate):
    """Full-HARP paired bootstrap of episode precision and FP-window differences."""
    n = len(control)
    weights = np.random.default_rng(SEED).multinomial(n, [1/n]*n, size=DRAWS)
    result = {}
    c_ep, k_ep = weights@control.episodes.to_numpy(), weights@candidate.episodes.to_numpy()
    with np.errstate(divide='ignore', invalid='ignore'):
        precision = (weights@candidate.hit_episodes.to_numpy())/k_ep-(weights@control.hit_episodes.to_numpy())/c_ep
    valid = np.isfinite(precision)
    fp = weights@candidate.fp.to_numpy()-weights@control.fp.to_numpy()
    for name, values, mask in [('episode_precision_diff', precision, valid),
                               ('fp_diff', fp.astype(float), np.ones(DRAWS, bool))]:
        draws = values[mask]
        lo, hi = np.percentile(draws, [2.5, 97.5]) if len(draws) else (None, None)
        result[name] = dict(lower=lo, upper=hi, valid_draws=int(mask.sum()), undefined_draws=int((~mask).sum()))
    return result


def acceptance(row, control, tolerance):
    return dict(
        episode_precision_higher=bool(row['episode_precision'] is not None and control['episode_precision'] is not None
                                      and row['episode_precision'] > control['episode_precision']),
        fp_lower=bool(row['fp'] < control['fp']),
        positive_runs_alarmed_not_below=bool(row['positive_runs_alarmed'] >= control['positive_runs_alarmed']),
        recall_drop_ok=bool(control['recall'] is None or control['recall']-row['recall'] <= tolerance+1e-12))


def run(source, expected, config_path, audit, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    if sha(source/'report.json') != expected or expected != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    if sha(audit/'report.json') != evidence['episode_audit_report_sha256']:
        raise ValueError('Episode audit changed')
    previous = pd.read_csv(audit/'episodes.csv')
    report = json.loads((source/'report.json').read_text())
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    arms = [config['primary_arm']]+config['secondary_arms']
    rows, intervals, checks = [], [], []
    for year in config['years']:
        for name in ['predictions.parquet', 'thresholds.json', 'finished.json']:
            rel = f'{year}/{name}'
            if sha(source/rel) != report['artifact_hashes'][rel]:
                raise ValueError(f'Changed annual evidence: {rel}')
        frame = pd.read_parquet(source/str(year)/'predictions.parquet')
        thresholds = json.loads((source/str(year)/'thresholds.json').read_text())
        for arm in arms:
            results = {}
            for candidate in config['candidates']:
                results[candidate['id']] = evaluate(frame, arm, thresholds[arm], candidate['k'])
            control, control_harp = results['control']
            old = previous[(previous.year == year) & (previous.arm == arm)].iloc[0]
            if (old.alarm_windows, old.episodes, old.hit_episodes) != (control['alarm_windows'], control['episodes'], control['hit_episodes']):
                raise ValueError(f'Control does not reproduce the episode audit: {year} {arm}')
            checks.append(dict(year=year, arm=arm, reproduced=True))
            for candidate in config['candidates']:
                values, per_harp = results[candidate['id']]
                row = dict(year=year, arm=arm, candidate=candidate['id'], **values)
                if candidate['id'] != 'control':
                    flags = acceptance(values, control, tolerance)
                    row.update(flags)
                    row['primary_met'] = bool(all(flags.values()) and year in config['positive_years'])
                    for metric, interval in paired_bootstrap(control_harp, per_harp).items():
                        intervals.append(dict(year=year, arm=arm, candidate=candidate['id'], metric=metric, **interval))
                rows.append(row)
    table = pd.DataFrame(rows)
    positive_years = config['positive_years']
    summary = []
    for (arm, candidate), group in table[table.candidate != 'control'].groupby(['arm', 'candidate'], sort=False):
        gated = group[group.year.isin(positive_years)]
        summary.append(dict(arm=arm, candidate=candidate, k=int(group.k.iloc[0]),
            years_met=int(gated.primary_met.sum()), required_years=len(positive_years),
            all_year_primary=bool(gated.primary_met.all() and len(gated) == len(positive_years))))
    pooled = table.groupby(['arm', 'candidate', 'k'], sort=False)[
        ['tp', 'fp', 'fn', 'tn', 'alarm_windows', 'episodes', 'hit_episodes', 'all_negative_episodes',
         'positive_runs', 'positive_runs_alarmed']].sum().reset_index()
    output.mkdir(parents=True)
    table.to_csv(output/'persistence.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    pd.DataFrame(summary).to_csv(output/'acceptance.csv', index=False)
    pooled.to_csv(output/'pooled.csv', index=False)
    result = {'config_sha256': sha(config_path), 'source_report_sha256': expected,
        'episode_audit_report_sha256': evidence['episode_audit_report_sha256'],
        'years': config['years'], 'acceptance': summary, 'control_reproduced': checks,
        'bootstrap': {'draws': DRAWS, 'seed': SEED, 'unit': 'full HARP, paired with control'},
        'reserved_test_accessed': False, 'model_promoted': False,
        'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--config', type=Path, default=Path('config/alarm-persistence-v1.json'))
    parser.add_argument('--episode-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.source, args.source_sha256, args.config, args.episode_audit, args.output)
    print(pd.DataFrame(result['acceptance']).to_string(index=False))
