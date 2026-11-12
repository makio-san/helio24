"""Repeat the cycle-25 ranking diagnostic on the adopted relabelled pipeline (config/cycle25-diagnostic-v2.json)."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from helio24.data import FEATURE_COLUMNS
from helio24.v2_training import load_development
from scripts.audit_alarm_persistence import sha
from scripts.audit_cycle25 import CAPACITY, KEY, composition, decomposition, single_feature_ceiling, within_era_fit

NEAR = pd.Timedelta(hours=72)


def alert_false_positive_origin(frame, threshold, near=NEAR):
    """Where alert-tier FP windows come from: never-flaring HARPs, or within `near` of a positive run of the same HARP."""
    alarm = frame.probability.ge(threshold)
    fp = frame[alarm & frame.target.eq(0)]
    flaring = set(frame.harp[frame.target.eq(1)])
    close = np.zeros(len(fp), dtype=bool)
    nanoseconds = pd.to_datetime(frame.forecast_time, utc=True).astype('datetime64[ns, UTC]').astype('int64')
    positive_times = {harp: part.to_numpy() for harp, part in nanoseconds[frame.target.eq(1)].groupby(frame.harp)}
    for i, (harp, time) in enumerate(zip(fp.harp, nanoseconds[fp.index].to_numpy())):
        times = positive_times.get(harp)
        if times is not None:
            close[i] = np.abs(times-time).min() <= near.value
    return dict(alert_windows=int(alarm.sum()), alert_fp_windows=len(fp),
                alert_fp_share_never_flaring_harps=float((~fp.harp.isin(flaring)).mean()) if len(fp) else None,
                alert_fp_share_within_72h_of_positive=float(close.mean()) if len(fp) else None)


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence, reference_config = config['evidence'], config['frozen_label_reference']
    source = Path(evidence['predictions'])
    if sha(source/'report.json') != evidence['predictions_report_sha256']:
        raise ValueError('Adopted pipeline manifest changed')
    reference_dir = Path(reference_config['diagnostic'])
    if sha(reference_dir/'report.json') != reference_config['diagnostic_report_sha256']:
        raise ValueError('Frozen-label diagnostic changed')
    base = json.loads(Path(evidence['base_protocol']).read_text())
    groups, _ = load_development(Path(evidence['table']), evidence['table_report_sha256'])
    table = pd.concat(groups.values(), ignore_index=True)
    del groups
    column = evidence['probability_column']
    frames, thresholds = {}, {}
    for year in config['years']:
        predictions = pd.read_parquet(source/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'missing_fraction', column])
        frame = predictions.merge(table[[*KEY, *FEATURE_COLUMNS]], on=KEY, how='inner')
        if len(frame) != len(predictions):
            raise ValueError(f'Evaluation keys do not match: {year}')
        frames[year] = frame.rename(columns={column: 'probability'}).sort_values(KEY).reset_index(drop=True)
        thresholds[year] = json.loads((source/str(year)/'thresholds.json').read_text())
    output.mkdir(parents=True)
    cycle24 = pd.concat([frames[y] for y in config['eras']['cycle24']])
    reference_median = float(cycle24[cycle24.target.eq(1)][CAPACITY].median())
    rows, features = [], []
    for year, frame in frames.items():
        row = dict(year=year, labels='relabelled', **composition(frame, reference_median),
                   **decomposition(frame, thresholds[year]['watch']['threshold']))
        table_f, best = single_feature_ceiling(frame)
        features.append(table_f.assign(year=year))
        row.update(best)
        row.update(alert_false_positive_origin(frame, thresholds[year]['alert']['threshold']))
        row['alert_fallback'] = bool(thresholds[year]['alert']['fallback'])
        rows.append(row)
    fits, era_ap = 0, {}
    for era, years in config['eras'].items():
        frame = pd.concat([frames[y] for y in years], ignore_index=True)
        scores, used = within_era_fit(frame, base, 5)
        fits += used
        frame = frame.assign(within_era=scores)
        for year in years:
            part = frame[frame.forecast_time.dt.year.eq(year)]
            era_ap[year] = float(average_precision_score(part.target, part.within_era))
        frame[[*KEY, 'target', 'within_era']].to_parquet(output/f'within_era_{era}.parquet', index=False)
    if fits != config['budget']['fits']:
        raise ValueError('Fit budget differs from the protocol')
    results = pd.DataFrame(rows)
    results['within_era_ap'] = results.year.map(era_ap)
    results['within_era_minus_walk_forward'] = results.within_era_ap-results.overall_ap
    frozen = pd.read_csv(reference_dir/'results.csv').assign(labels='frozen')
    pd.concat([results, frozen], ignore_index=True).to_csv(output/'results.csv', index=False)
    pd.concat(features).to_csv(output/'single_features.csv', index=False)
    indexed, old = results.set_index('year'), frozen.set_index('year')
    cycle25 = config['eras']['cycle25']
    gain = indexed.within_era_minus_walk_forward
    floor_years = [2014, 2015, 2017]
    label_effect = {measure: bool((indexed.loc[cycle25, measure] >= indexed.loc[floor_years, measure].min()).all())
                    for measure in ['best_feature_ap', 'within_era_ap']}
    reading = {
        'R1_information_fell': bool((gain[cycle25] < 0.10).all()),
        'R2_drift': bool((gain[cycle25] >= 0.10).all()),
        'R3_timing_dominates_years': [int(y) for y in indexed.index if indexed.region_ap[y] >= 0.5 and indexed.within_flaring_ap[y] < 0.3],
        'label_effect_reaches_cycle24_floor': label_effect,
        'first_diagnostic_information_statement': 'attributed_to_label_coverage' if all(label_effect.values()) else 'stands',
    }
    numeric = [c for c in old.columns if c in indexed.columns and pd.api.types.is_numeric_dtype(old[c])]
    (indexed[numeric]-old[numeric]).reset_index().to_csv(output/'change_from_frozen.csv', index=False)
    result = {'config_sha256': sha(config_path), 'source_report_sha256': evidence['predictions_report_sha256'],
              'development_basis': 'relabelled table, walk-forward-v2, operating-point-v3',
              'reference_capacity_median_cycle24_positive': reference_median, 'fits': fits, 'reading': reading,
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/cycle25-diagnostic-v2.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, results = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(results.T.to_string())
    print(json.dumps({k: v for k, v in result.items() if k != 'artifact_hashes'}, indent=1))
