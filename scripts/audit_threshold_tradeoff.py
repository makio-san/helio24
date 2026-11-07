"""Evaluate the frozen threshold versus persistence protocol (config/threshold-tradeoff-v1.json)."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.audit_alarm_persistence import acceptance, evaluate, paired_bootstrap, sha

METRICS = ['recall', 'precision', 'fp', 'episodes', 'hit_episodes', 'episode_precision', 'positive_runs_alarmed']


def largest_threshold(frame, arm, target_recall):
    """Largest probability t whose window recall is at least target_recall (alarm when p >= t)."""
    positives = np.sort(frame.loc[frame.target.eq(1), arm].to_numpy())[::-1]
    needed = max(1, math.ceil(target_recall*len(positives)-1e-12))
    if needed > len(positives):
        raise ValueError('Target recall cannot be reached')
    return float(positives[needed-1])


def verdict(wins, at_least_as_good, years):
    if len(wins) == years and all(wins):
        return 'persistence_adds_value'
    if len(at_least_as_good) == years and all(at_least_as_good):
        return 'threshold_at_least_as_good'
    return 'mixed'


def run(source, expected, config_path, audit, persistence, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    if sha(source/'report.json') != expected or expected != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    if sha(audit/'report.json') != evidence['episode_audit_report_sha256']:
        raise ValueError('Episode audit changed')
    if sha(persistence/'report.json') != evidence['persistence_report_sha256']:
        raise ValueError('Persistence report changed')
    persisted = pd.read_csv(persistence/'persistence.csv')
    persistence_config = json.loads(Path(evidence['persistence_config']).read_text())
    tolerance = persistence_config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    ks = {c['id']: c['k'] for c in persistence_config['candidates'] if c['id'] != 'control'}
    multipliers = config['deployable_candidates']['multipliers']
    report = json.loads((source/'report.json').read_text())
    arms = [config['primary_arm']]+config['secondary_arms']
    deployable, intervals, oracle, comparison = [], [], [], []
    for year in config['years']:
        for name in ['predictions.parquet', 'thresholds.json', 'finished.json']:
            rel = f'{year}/{name}'
            if sha(source/rel) != report['artifact_hashes'][rel]:
                raise ValueError(f'Changed annual evidence: {rel}')
        frame = pd.read_parquet(source/str(year)/'predictions.parquet')
        thresholds = json.loads((source/str(year)/'thresholds.json').read_text())
        for arm in arms:
            base = thresholds[arm]
            control, control_harp = evaluate(frame, arm, base, 1)
            kept = {}
            for pid, k in ks.items():
                values, _ = evaluate(frame, arm, base, k)
                old = persisted[(persisted.year == year) & (persisted.arm == arm) & (persisted.candidate == pid)].iloc[0]
                if (old.fp, old.episodes, old.hit_episodes) != (values['fp'], values['episodes'], values['hit_episodes']):
                    raise ValueError(f'Persistence does not reproduce: {year} {arm} {pid}')
                kept[pid] = values
            for m in multipliers:
                threshold = min(1.0, base*m)
                values, per_harp = evaluate(frame, arm, threshold, 1)
                flags = acceptance(values, control, tolerance)
                deployable.append(dict(year=year, arm=arm, candidate=f'mult_{m}', multiplier=m, **values, **flags,
                    primary_met=bool(all(flags.values()) and year in config['positive_years'])))
                for metric, interval in paired_bootstrap(control_harp, per_harp).items():
                    intervals.append(dict(year=year, arm=arm, candidate=f'mult_{m}', metric=metric, **interval))
            if control['recall'] is None:
                continue
            references = {f'matched_{pid.split("_")[1]}': kept[pid]['recall'] for pid in ks}
            references['tolerance_ref'] = control['recall']-tolerance
            for name, target in references.items():
                t = largest_threshold(frame, arm, target)
                values, _ = evaluate(frame, arm, t, 1)
                oracle.append(dict(year=year, arm=arm, reference=name, target_recall=target, t=t, **values))
            for pid, k in ks.items():
                matched = next(o for o in oracle if o['year'] == year and o['arm'] == arm
                               and o['reference'] == f'matched_{pid.split("_")[1]}')
                persist = kept[pid]
                comparison.append(dict(year=year, arm=arm, candidate=pid, k=k,
                    persistence_fp=persist['fp'], matched_fp=matched['fp'],
                    persistence_episodes=persist['episodes'], matched_episodes=matched['episodes'],
                    persistence_recall=persist['recall'], matched_recall=matched['recall'],
                    persistence_wins=bool(persist['fp'] < matched['fp'] and persist['episodes'] < matched['episodes']),
                    threshold_at_least_as_good=bool(matched['fp'] <= persist['fp'])))
    deployable, comparison = pd.DataFrame(deployable), pd.DataFrame(comparison)
    positive = config['positive_years']
    summary = []
    for (arm, candidate), group in deployable.groupby(['arm', 'candidate'], sort=False):
        gated = group[group.year.isin(positive)]
        summary.append(dict(kind='deployable', arm=arm, candidate=candidate, years_met=int(gated.primary_met.sum()),
            required_years=len(positive), result='pass' if gated.primary_met.all() else 'fail'))
    for (arm, candidate), group in comparison.groupby(['arm', 'candidate'], sort=False):
        gated = group[group.year.isin(positive)]
        summary.append(dict(kind='matched_recall', arm=arm, candidate=candidate,
            years_met=int(gated.persistence_wins.sum()), required_years=len(positive),
            result=verdict(gated.persistence_wins.tolist(), gated.threshold_at_least_as_good.tolist(), len(positive)),
            years_threshold_at_least_as_good=int(gated.threshold_at_least_as_good.sum())))
    output.mkdir(parents=True)
    deployable.to_csv(output/'deployable.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    pd.DataFrame(oracle).to_csv(output/'oracle.csv', index=False)
    comparison.to_csv(output/'comparison.csv', index=False)
    pd.DataFrame(summary).to_csv(output/'summary.csv', index=False)
    result = {'config_sha256': sha(config_path), 'source_report_sha256': expected,
        'episode_audit_report_sha256': evidence['episode_audit_report_sha256'],
        'persistence_report_sha256': evidence['persistence_report_sha256'], 'years': config['years'],
        'summary': summary, 'bootstrap': {'draws': 1000, 'seed': 24, 'unit': 'full HARP, paired with control'},
        'oracle_note': 'Oracle thresholds use evaluation labels; diagnostic only, not deployable.',
        'reserved_test_accessed': False, 'model_promoted': False,
        'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, deployable, oracle, comparison


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--config', type=Path, default=Path('config/threshold-tradeoff-v1.json'))
    parser.add_argument('--episode-audit', type=Path, required=True)
    parser.add_argument('--persistence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, *_ = run(args.source, args.source_sha256, args.config, args.episode_audit, args.persistence, args.output)
    print(pd.DataFrame(result['summary']).to_string(index=False))
