"""Diagnose the cycle-25 ranking weakness of the frozen baseline (config/cycle25-diagnostic-v1.json)."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from sklearn.model_selection import GroupKFold

from helio24.data import FEATURE_COLUMNS
from helio24.v2_training import candidate_models, load_development
from scripts.audit_alarm_persistence import evaluate, sha

KEY = ['harp', 'forecast_time']
CAPACITY = 'USFLUX__last'


def composition(frame, reference_median):
    positive = frame[frame.target.eq(1)]
    flaring = positive.harp.unique()
    runs = evaluate(frame.assign(probability=0.0), 'probability', 1.0, 1)[0]['positive_runs']
    return dict(windows=len(frame), harps=frame.harp.nunique(), flaring_harps=len(flaring), positive_windows=len(positive),
                positive_runs=runs, positive_share=float(frame.target.mean()),
                median_windows_per_flaring_harp=float(frame[frame.harp.isin(flaring)].groupby('harp').size().median()),
                median_capacity_positive=float(positive[CAPACITY].median()), median_capacity_all=float(frame[CAPACITY].median()),
                positive_share_below_reference_capacity=float((positive[CAPACITY] < reference_median).mean()),
                mean_missing_fraction=float(frame.missing_fraction.mean()))


def decomposition(frame, threshold):
    """Overall, region ('which') and within-flaring-HARP ('when') AP plus the FP share from never-flaring HARPs."""
    region = frame.groupby('harp').agg(probability=('probability', 'max'), target=('target', 'max'))
    flaring = frame[frame.harp.isin(region.index[region.target.eq(1)])]
    fp = frame[frame.probability.ge(threshold) & frame.target.eq(0)]
    never = fp.harp.isin(region.index[region.target.eq(0)])
    return dict(overall_ap=float(average_precision_score(frame.target, frame.probability)),
                region_ap=float(average_precision_score(region.target, region.probability)),
                within_flaring_ap=float(average_precision_score(flaring.target, flaring.probability)),
                fp_windows=len(fp), fp_share_never_flaring_harps=float(never.mean()) if len(fp) else None)


def single_feature_ceiling(frame):
    rows = []
    for column in FEATURE_COLUMNS:
        values = frame[column].to_numpy(dtype=float)
        values = np.where(np.isfinite(values), values, np.nanmedian(values))
        rows.append(dict(feature=column, ap=float(average_precision_score(frame.target, values)),
                         ap_negated=float(average_precision_score(frame.target, -values))))
    table = pd.DataFrame(rows)
    table['best_ap'] = table[['ap', 'ap_negated']].max(axis=1)
    best = table.sort_values(['best_ap', 'feature'], ascending=[False, True]).iloc[0]
    capacity = table[table.feature == CAPACITY].iloc[0]
    return table, dict(best_feature=best.feature, best_feature_ap=float(best.best_ap), capacity_ap=float(capacity.best_ap))


def within_era_fit(frame, base, folds):
    """HARP-grouped out-of-fold raw ensemble probability of the unchanged recipes; a ceiling, never deployable."""
    x = frame[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    y = frame.target.to_numpy(dtype=np.int8)
    groups = frame.harp.to_numpy()
    weight = base['ensemble']['logistic_weight']
    out = np.full(len(frame), np.nan)
    fits = 0
    for train_index, test_index in GroupKFold(n_splits=folds).split(x, y, groups):
        scores = {}
        for name, model in candidate_models(base).items():
            model.fit(x[train_index], y[train_index])
            scores[name] = np.clip(model.predict_proba(x[test_index])[:, 1], 1e-9, 1-1e-9)
            fits += 1
            del model
        out[test_index] = weight*scores['logistic']+(1-weight)*scores['xgboost']
    if not np.isfinite(out).all():
        raise ValueError('Out-of-fold scores incomplete')
    return out, fits


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    source = Path(evidence['predictions'])
    if sha(source/'report.json') != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    if sha(Path(evidence['watch_tier_thresholds'])) != evidence['watch_tier_thresholds_sha256']:
        raise ValueError('Watch tier thresholds changed')
    thresholds = json.loads(Path(evidence['watch_tier_thresholds']).read_text())
    base = json.loads(Path(evidence['base_protocol']).read_text())
    original, _ = load_development(Path(evidence['frozen_shards']), evidence['frozen_shards_report_sha256'])
    table = pd.concat(original.values(), ignore_index=True)
    del original
    frames = {}
    for year in config['years']:
        predictions = pd.read_parquet(source/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'missing_fraction', 'baseline'])
        frame = predictions.merge(table[[*KEY, *FEATURE_COLUMNS]], on=KEY, how='inner')
        if len(frame) != len(predictions):
            raise ValueError(f'Evaluation keys do not match: {year}')
        frames[year] = frame.rename(columns={'baseline': 'probability'}).sort_values(KEY).reset_index(drop=True)
    output.mkdir(parents=True)
    reference = pd.concat([frames[y] for y in config['eras']['cycle24']])
    reference_median = float(reference[reference.target.eq(1)][CAPACITY].median())
    rows, features = [], []
    for year, frame in frames.items():
        row = dict(year=year, **composition(frame, reference_median),
                   **decomposition(frame, thresholds[str(year)]['0.9']))
        table_f, best = single_feature_ceiling(frame)
        features.append(table_f.assign(year=year))
        row.update(best)
        rows.append(row)
    fits = 0
    era_ap = {}
    for era, years in config['eras'].items():
        frame = pd.concat([frames[y] for y in years], ignore_index=True)
        scores, used = within_era_fit(frame, base, 5)
        fits += used
        frame = frame.assign(within_era=scores)
        for year in years:
            part = frame[frame.forecast_time.dt.year.eq(year)]
            era_ap[year] = float(average_precision_score(part.target, part.within_era))
        frame[[*KEY, 'target', 'within_era']].to_parquet(output/f'within_era_{era}.parquet', index=False)
    results = pd.DataFrame(rows)
    results['within_era_ap'] = results.year.map(era_ap)
    results['within_era_minus_walk_forward'] = results.within_era_ap-results.overall_ap
    results.to_csv(output/'results.csv', index=False)
    pd.concat(features).to_csv(output/'single_features.csv', index=False)
    gain = results.set_index('year').within_era_minus_walk_forward
    region = results.set_index('year')
    reading = {
        'R1_information_fell': bool((gain[config['eras']['cycle25']] < 0.10).all()),
        'R2_drift': bool((gain[config['eras']['cycle25']] >= 0.10).all()),
        'R3_timing_dominates_years': [int(y) for y in region.index if region.region_ap[y] >= 0.5 and region.within_flaring_ap[y] < 0.3],
    }
    result = {'config_sha256': sha(config_path), 'source_report_sha256': evidence['predictions_report_sha256'],
              'reference_capacity_median_cycle24_positive': reference_median, 'fits': fits, 'reading': reading,
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/cycle25-diagnostic-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, results = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(results.T.to_string())
    print(json.dumps({k: v for k, v in result.items() if k != 'artifact_hashes'}, indent=1))
