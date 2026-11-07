"""Count frozen annual alarms as consecutive-hour alarm episodes instead of windows."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from helio24.events import alarm_episodes

ARMS = ['baseline', 'short_training', 'chronological', 'shuffled_interior']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positive_runs(windows):
    """Consecutive-hour runs of positive-labelled windows and how many contain an alarm."""
    windows = windows.sort_values(['harp', 'forecast_time'])
    previous = windows.groupby('harp').forecast_time.shift()
    continues = windows.target.eq(1) & windows.groupby('harp').target.shift().eq(1) \
        & windows.forecast_time.sub(previous).eq(pd.Timedelta(hours=1))
    run_id = (~continues).cumsum()
    runs = windows[windows.target.eq(1)].groupby(run_id[windows.target.eq(1)]).alarm.any()
    return len(runs), int(runs.sum())


def summarize(frame, arm, threshold):
    """Episode-level counts for one arm at its frozen threshold."""
    data = frame[['harp', 'forecast_time', 'target', 'missing_fraction']].assign(probability=frame[arm])
    windows, episodes = alarm_episodes(data, threshold)
    hit = ~episodes.all_negative
    positives = int(windows.target.sum())
    alarm_windows = int(windows.alarm.sum())
    tp = int((windows.alarm & windows.target.eq(1)).sum())
    fp = alarm_windows-tp
    runs, runs_alarmed = positive_runs(windows)
    out = dict(arm=arm, threshold=threshold, windows=len(windows), positive_windows=positives,
        alarm_windows=alarm_windows, tp_windows=tp, fp_windows=fp,
        window_precision=tp/alarm_windows if alarm_windows else None,
        episodes=len(episodes), hit_episodes=int(hit.sum()),
        all_negative_episodes=int((~hit).sum()),
        episode_precision=float(hit.mean()) if len(episodes) else None,
        episode_false_alarm_ratio=float((~hit).mean()) if len(episodes) else None,
        positive_runs=runs, positive_runs_alarmed=runs_alarmed,
        positive_run_recall=runs_alarmed/runs if runs else None,
        regions_with_alarm=int(episodes.harp.nunique()),
        median_episode_hours=float(episodes.state_hours.median()) if len(episodes) else None,
        max_episode_hours=float(episodes.state_hours.max()) if len(episodes) else None,
        median_all_negative_hours=float(episodes.loc[~hit, 'state_hours'].median()) if (~hit).any() else None,
        left_or_right_censored=int((episodes.left_censored | episodes.right_censored).sum()))
    return out


def run(source, expected, output, years=None):
    if output.exists():
        raise FileExistsError(output)
    if sha(source/'report.json') != expected:
        raise ValueError('Final experiment manifest changed')
    report = json.loads((source/'report.json').read_text())
    available = [y for y in report['protocol']['evaluation_years'] if f'{y}/finished.json' in report['artifact_hashes']]
    years = years or available
    rows = []
    for year in years:
        for name in ['predictions.parquet', 'thresholds.json', 'finished.json']:
            rel = f'{year}/{name}'
            if sha(source/rel) != report['artifact_hashes'][rel]:
                raise ValueError(f'Changed annual evidence: {rel}')
        frame = pd.read_parquet(source/str(year)/'predictions.parquet')
        thresholds = json.loads((source/str(year)/'thresholds.json').read_text())
        for arm in ARMS:
            rows.append({'year': year, **summarize(frame, arm, thresholds[arm])})
    output.mkdir(parents=True)
    table = pd.DataFrame(rows)
    table.to_csv(output/'episodes.csv', index=False)
    result = {'source_report_sha256': expected, 'years': years, 'summary': rows,
        'scope': ('Post-hoc grouping of overlapping hourly forecast windows into consecutive-hour alarm '
                  'episodes. A hit episode contains at least one positive-labelled window; this is not a '
                  'physical flare match and not an independent event count.'),
        'reserved_test_accessed': False, 'model_promoted': False,
        'artifact_hashes': {p.name: sha(p) for p in output.iterdir()}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.source, args.source_sha256, args.output)
    cols = ['year', 'arm', 'alarm_windows', 'window_precision', 'episodes', 'hit_episodes',
            'episode_precision', 'median_episode_hours', 'max_episode_hours']
    print(pd.DataFrame(result['summary'])[cols].to_string(index=False))
