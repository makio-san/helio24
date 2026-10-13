"""Audit frozen development predictions without fitting or threshold selection."""
import json
from importlib.metadata import version
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from helio24.data import ROOT
from helio24.events import alarm_episodes, match_events, regional_summary
from helio24.full_data import sha256


def run(root=ROOT):
    output = root / 'artifacts/event_audit'
    if output.exists():
        raise RuntimeError('Preserve the existing event audit before another run')
    exp2 = root / 'artifacts/experiment2'
    frozen = json.loads((exp2 / 'frozen_decisions.json').read_text())
    reference = json.loads((exp2 / 'report.json').read_text())
    if frozen != reference['protocol']:
        raise ValueError('Experiment-2 frozen decisions differ from its report')
    source = root / 'data/full/partition4.parquet'
    if sha256(source) != reference['source_features'][source.name]:
        raise ValueError('Partition-4 feature source changed')
    manifest_path = root / 'data/event_mapping/manifest.json'
    mapping_manifest = json.loads(manifest_path.read_text())
    if mapping_manifest['source']['catalog_sha256'] != sha256(root / 'data/flare_catalog.csv'):
        raise ValueError('Mapping catalog changed')
    for name, digest in mapping_manifest['files'].items():
        if sha256(manifest_path.parent / name) != digest:
            raise ValueError('Mapping evidence changed')
    predictions = pd.read_parquet(exp2 / 'predictions.parquet')
    predictions = predictions[(predictions.split == 'validation') & (predictions.model == 'full_calibrated')]
    keys = ['harp', 'forecast_time', 'prediction_end', 'label', 'target']
    frame = pd.read_parquet(source).merge(predictions[keys+['probability']], on=keys, validate='one_to_one')
    if len(frame) != len(predictions) or len(frame) != reference['roles']['validation']['n']:
        raise ValueError('Validation predictions fail exact feature matching')
    threshold = frozen['thresholds']['full_calibrated']['0.9']
    windows, episodes = alarm_episodes(frame, threshold)
    mapping = pd.read_csv(manifest_path.parent / 'associations.csv')
    catalog = pd.read_csv(root / 'data/flare_catalog.csv')
    events = match_events(windows, mapping, catalog)
    regions, episodes = regional_summary(windows, episodes, events)
    eligible = events[events.status == 'evaluated']
    fully = eligible[eligible.fully_covered]
    false = windows.alarm & windows.target.eq(0)
    total_false = float(windows.loc[false, 'state_hours'].sum())
    summary = dict(
        scope='Experiment-2 full-calibrated partition-4 development audit; no new test or model',
        threshold=threshold, windows=len(windows), regions=int(windows.harp.nunique()),
        monitored_region_hours=float(windows.state_hours.sum()),
        alarm_region_hours=float(windows.loc[windows.alarm, 'state_hours'].sum()),
        false_alarm_region_hours=total_false,
        false_alarm_hour_fraction=total_false/float(windows.state_hours.sum()),
        episodes=len(episodes), all_negative_episodes=int(episodes.all_negative.sum()),
        boundary_or_gap_censored_episodes=int((episodes.left_censored | episodes.right_censored).sum()),
        longest_all_negative_hours=float(episodes.loc[episodes.all_negative, 'state_hours'].max()) if episodes.all_negative.any() else 0.,
        catalog_status_counts={str(k): int(v) for k, v in events.status.value_counts().items()},
        covered_mapped_events=len(eligible), detected_events=int(eligible.detected.sum()),
        covered_event_recall=float(eligible.detected.mean()) if len(eligible) else None,
        before_start_events=int(eligible.before_start.sum()),
        fully_covered_events=len(fully), fully_covered_detected=int(fully.detected.sum()),
        fully_covered_recall=float(fully.detected.mean()) if len(fully) else None,
        median_peak_lead_hours=float(eligible.peak_lead_hours.median()) if eligible.detected.any() else None,
        median_start_lead_hours=float(eligible.start_lead_hours.median()) if eligible.before_start.any() else None,
        covered_history_only_events=int((eligible.evidence == 'history_location').sum()),
        top10_region_false_hour_share=float(regions.head(10).false_hours.sum()/total_false) if total_false else None,
        mapping_audit=mapping_manifest,
    )
    # Episode/event links retain multiplicity separately from unique-event recall.
    links = []
    for event in eligible.itertuples(index=False):
        candidates = windows[(windows.harp == event.harp) & windows.alarm &
                             (windows.forecast_time <= event.peak_time) & (windows.prediction_end > event.peak_time)]
        for episode_id, group in candidates.groupby('episode_id'):
            links.append(dict(episode_id=int(episode_id), flare_id=event.flare_id, alarm_windows=len(group)))
    links = pd.DataFrame(links, columns=['episode_id', 'flare_id', 'alarm_windows'])
    episodes['matched_events'] = episodes.episode_id.map(links.groupby('episode_id').flare_id.nunique()).fillna(0).astype(int)
    # Mapped event disagreement is reported, not silently used to relabel the benchmark.
    overlaps = []
    for event in eligible.itertuples(index=False):
        inconsistent = windows[(windows.harp == event.harp) & windows.target.eq(0) &
                               (windows.forecast_time <= event.peak_time) & (windows.prediction_end > event.peak_time)]
        for row in inconsistent.itertuples(index=False):
            overlaps.append(dict(harp=int(row.harp), forecast_time=row.forecast_time, flare_id=event.flare_id))
    summary['mapped_event_negative_label_conflicts'] = len(overlaps)
    windows['outcome'] = np.select([windows.alarm & windows.target.eq(1), ~windows.alarm & windows.target.eq(1), false],
                                   ['hit', 'miss', 'false_alarm'], default='correct_quiet')
    descriptions = windows.groupby('outcome').agg(
        windows=('target', 'size'), missing_fraction_median=('missing_fraction', 'median'),
        usflux_last_median=('USFLUX__last', 'median'), r_value_last_median=('R_VALUE__last', 'median'),
        totusjh_last_median=('TOTUSJH__last', 'median'))
    source_paths = [source, exp2 / 'report.json', exp2 / 'frozen_decisions.json', exp2 / 'predictions.parquet',
                    root / 'data/flare_catalog.csv', manifest_path, root / 'docs/event-audit-protocol.md']
    summary['source_hashes'] = {str(p.relative_to(root)): sha256(p) for p in source_paths}
    summary['code_hashes'] = {name: sha256(root / name) for name in [
        'helio24/events.py', 'helio24/event_mapping.py', 'scripts/run_event_audit.py']}
    summary['versions'] = {name: version(name) for name in ['numpy', 'pandas', 'pyarrow']}
    output.mkdir(parents=True)
    retained = keys+['probability', 'missing_fraction', 'alarm', 'state_end', 'state_hours', 'episode_id', 'outcome',
                     'USFLUX__last', 'R_VALUE__last', 'TOTUSJH__last']
    windows[retained].to_parquet(output / 'windows.parquet', index=False)
    episodes.to_csv(output / 'episodes.csv', index=False)
    events.to_csv(output / 'events.csv', index=False)
    regions.to_csv(output / 'regions.csv', index=False)
    links.to_csv(output / 'episode_event_links.csv', index=False)
    descriptions.to_csv(output / 'outcome_features.csv')
    pd.DataFrame(overlaps, columns=['harp', 'forecast_time', 'flare_id']).to_csv(output / 'label_conflicts.csv', index=False)
    (output / 'protocol.md').write_text((root / 'docs/event-audit-protocol.md').read_text())
    summary['artifact_hashes'] = {p.name: sha256(p) for p in output.iterdir() if p.is_file()}
    (output / 'report.json').write_text(json.dumps(summary, indent=2, allow_nan=False))
    print(json.dumps({k: v for k, v in summary.items() if not isinstance(v, dict)}, indent=2))
    return summary


if __name__ == '__main__':
    run()
