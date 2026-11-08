"""Evaluate the frozen regional context feature protocol (config/region-context-v1.json)."""
import argparse
import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.calibration import SigmoidCalibration, recall_threshold
from helio24.data import FEATURE_COLUMNS
from helio24.modeling import metrics
from helio24.v2_training import load_development, candidate_models
from helio24.walk_forward import annual_fold
from scripts.audit_alarm_persistence import acceptance, evaluate, paired_bootstrap, sha
from scripts.audit_precision_context import fp_allowed
from scripts.audit_region_context_sources import available_srs, load_mapping, load_srs

KEY = ['harp', 'forecast_time']
MAG = {'Alpha': 0, 'Beta': 1, 'Gamma': 2, 'Beta-Gamma': 2, 'Beta-Delta': 3, 'Beta-Gamma-Delta': 4}
ZURICH = {'A': 0, 'B': 1, 'H': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5}
PENUMBRA = {'x': 0, 'r': 1, 's': 2, 'a': 3, 'h': 4, 'k': 5}
COMPACT = {'x': 0, 'o': 1, 'i': 2, 'c': 3}
CONTEXT = ['srs_available', 'hours_since_issue', 'n_regions', 'mag_rank', 'has_delta', 'has_gamma', 'zurich_rank',
           'penumbra_rank', 'compact_rank', 'area_log', 'spots_log', 'extent_max', 'srs_history_days']
FLAG = ['srs_available', 'hours_since_issue']
CANDIDATES = {'flag': FLAG, 'context': CONTEXT}


def srs_feature_table(rows):
    """Per (issued_utc, noaa) SRS row with ordinal encodings and the count of earlier listings of that NOAA number."""
    table = rows.copy()
    unknown = sorted(set(table.mag_type)-set(MAG))
    if unknown:
        raise ValueError(f'Unknown magnetic class: {unknown}')
    table['mag_rank'] = table.mag_type.map(MAG)
    table['has_delta'] = table.mag_type.str.contains('Delta').astype(int)
    table['has_gamma'] = table.mag_type.str.contains('Gamma').astype(int)
    table['zurich_rank'] = table.z.str[0].map(ZURICH)
    table['penumbra_rank'] = table.z.str[1].map(PENUMBRA)
    table['compact_rank'] = table.z.str[2].map(COMPACT)
    if table[['zurich_rank', 'penumbra_rank', 'compact_rank']].isna().any().any():
        raise ValueError('Unknown McIntosh letter')
    table = table.sort_values(['noaa', 'issued_utc'])
    table['srs_history_days'] = table.groupby('noaa').cumcount()
    return table[['issued_utc', 'noaa', 'mag_rank', 'has_delta', 'has_gamma', 'zurich_rank', 'penumbra_rank',
                  'compact_rank', 'area', 'nn', 'll', 'srs_history_days']]


def attach_context(frame, mapping, issued, table):
    """Causal SRS context per window: latest SRS issued <= t - 30 min, rows of the HARP's NOAA numbers that day."""
    base = frame[KEY].copy().reset_index(drop=True)
    base['forecast_time'] = pd.to_datetime(base.forecast_time, utc=True)
    base['date'] = base.forecast_time.dt.date
    base['available'] = available_srs(issued.issued_utc, base.forecast_time).to_numpy()
    merged = base.reset_index().merge(mapping, on=['harp', 'date'], how='left')
    merged = merged.merge(table, left_on=['available', 'noaa'], right_on=['issued_utc', 'noaa'], how='left')
    matched = merged[merged.mag_rank.notna()]
    agg = matched.groupby('index').agg(n_regions=('noaa', 'size'), mag_rank=('mag_rank', 'max'),
        has_delta=('has_delta', 'max'), has_gamma=('has_gamma', 'max'), zurich_rank=('zurich_rank', 'max'),
        penumbra_rank=('penumbra_rank', 'max'), compact_rank=('compact_rank', 'max'), area=('area', 'sum'),
        nn=('nn', 'sum'), extent_max=('ll', 'max'), srs_history_days=('srs_history_days', 'max'))
    out = pd.DataFrame(index=base.index)
    out['srs_available'] = out.index.isin(agg.index).astype(float)
    out['hours_since_issue'] = np.where(out.srs_available.eq(1),
        (base.forecast_time-pd.to_datetime(base.available, utc=True)).dt.total_seconds()/3600, np.nan)
    for column in ['n_regions', 'mag_rank', 'has_delta', 'has_gamma', 'zurich_rank', 'penumbra_rank', 'compact_rank',
                   'extent_max', 'srs_history_days']:
        out[column] = agg[column].reindex(out.index).astype(float)
    out['area_log'] = np.log1p(agg.area.reindex(out.index).astype(float))
    out['spots_log'] = np.log1p(agg.nn.reindex(out.index).astype(float))
    out = out[CONTEXT]
    out.index = frame.index
    return out


def fit_candidate(base, groups, contexts, columns):
    """Unchanged walk-forward recipes on 96 summaries plus the given context columns; calibrated 0.45/0.55 ensemble."""
    def matrix(role):
        return np.hstack([groups[role][FEATURE_COLUMNS].to_numpy(dtype=np.float32),
                          contexts[role][columns].to_numpy(dtype=np.float32)])
    x = {role: matrix(role) for role in ['train', 'calibration', 'evaluation']}
    y_train = groups['train'].target.to_numpy(dtype=np.int8)
    y_cal = groups['calibration'].target.to_numpy(dtype=np.int8)
    weight = base['ensemble']['logistic_weight']
    calibrated, evaluated = {}, {}
    for name, model in candidate_models(base).items():
        model.fit(x['train'], y_train)
        raw = np.clip(model.predict_proba(x['calibration'])[:, 1], 1e-9, 1-1e-9)
        calibrator = SigmoidCalibration().fit(raw, y_cal)
        calibrated[name] = calibrator.transform(raw)
        evaluated[name] = calibrator.transform(np.clip(model.predict_proba(x['evaluation'])[:, 1], 1e-9, 1-1e-9))
        del model
    p_cal = weight*calibrated['logistic']+(1-weight)*calibrated['xgboost']
    p_eval = weight*evaluated['logistic']+(1-weight)*evaluated['xgboost']
    return recall_threshold(y_cal, p_cal, base['required_recall']), p_eval


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    source = Path(evidence['predictions'])
    if sha(source/'report.json') != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    report = json.loads((source/'report.json').read_text())
    walk_dir = Path(evidence['baseline_artifact'])
    if sha(walk_dir/'report.json') != evidence['baseline_report_sha256']:
        raise ValueError('Baseline walk-forward report changed')
    walk_report = json.loads((walk_dir/'report.json').read_text())
    base = json.loads(Path(evidence['base_protocol']).read_text())
    issued, rows, _ = load_srs(Path(evidence['srs_directory']))
    mapping, _, _ = load_mapping(Path(evidence['mapping_directory']))
    table = srs_feature_table(rows)
    original, _ = load_development(Path(base['source']), evidence['frozen_shards_report_sha256'])
    development = pd.concat(original.values(), ignore_index=True)
    del original
    output.mkdir(parents=True)
    # Phase 1: folds, context, fits and thresholds; evaluation labels are dropped before any fit.
    thresholds, prepared, coverage = {}, {}, []
    for year in config['years']:
        rel = f'{year}/thresholds.json'
        if sha(source/rel) != report['artifact_hashes'][rel]:
            raise ValueError(f'Changed annual evidence: {rel}')
        control_threshold = json.loads((source/rel).read_text())['baseline']
        groups, audit = annual_fold(development, year)
        frozen_fold = next(f for f in walk_report['folds'] if f['year'] == year)
        if audit != frozen_fold['audit']:
            raise ValueError(f'Annual populations changed: {year}')
        groups['evaluation'] = groups['evaluation'].drop(columns=['target', 'label_status'])
        contexts = {role: attach_context(group, mapping, issued, table) for role, group in groups.items()}
        for role, context in contexts.items():
            coverage.append({'year': year, 'role': role, 'rows': len(context),
                             'srs_available_share': float(context.srs_available.mean())})
        chosen, probabilities = {'control': float(control_threshold)}, {}
        for candidate, columns in CANDIDATES.items():
            chosen[candidate], probabilities[candidate] = fit_candidate(base, groups, contexts, columns)
            gc.collect()
        thresholds[str(year)] = chosen
        prepared[year] = groups['evaluation'][KEY].reset_index(drop=True).assign(**probabilities)
        print(f'{year}: thresholds {chosen}', flush=True)
        del groups, contexts
        gc.collect()
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    pd.DataFrame(coverage).to_csv(output/'context_coverage.csv', index=False)
    thresholds_sha = sha(output/'thresholds.json')
    # Phase 2: evaluation labels are read only now.
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    candidates = [c['id'] for c in config['candidates']]
    rows_out, intervals = [], []
    for year in config['years']:
        for name in ['predictions.parquet', 'finished.json']:
            rel = f'{year}/{name}'
            if sha(source/rel) != report['artifact_hashes'][rel]:
                raise ValueError(f'Changed annual evidence: {rel}')
        labels = pd.read_parquet(source/str(year)/'predictions.parquet',
                                 columns=[*KEY, 'target', 'missing_fraction', 'baseline'])
        frame = labels.merge(prepared[year], on=KEY, how='inner').rename(columns={'baseline': 'control'})
        if len(frame) != len(labels) or len(frame) != len(prepared[year]):
            raise ValueError(f'Evaluation keys do not match: {year}')
        y = frame.target.to_numpy()
        results = {c: evaluate(frame, c, thresholds[str(year)][c], 1) for c in candidates}
        control, control_harp = results['control']
        for candidate in candidates:
            values, per_harp = results[candidate]
            scores = metrics(y, frame[candidate].to_numpy(), thresholds[str(year)][candidate])
            row = dict(year=year, candidate=candidate, **values, average_precision=scores['average_precision'],
                       brier=scores['brier'], log_loss=scores['log_loss'], tss=scores['tss'],
                       recall_ge_095=bool(values['recall'] is not None and values['recall'] >= 0.95),
                       fp_allowed_for_target_precision=fp_allowed(values['tp']),
                       fp_excess_over_target=values['fp']-fp_allowed(values['tp']))
            if candidate != 'control':
                flags = acceptance(values, control, tolerance)
                row.update(flags)
                row['primary_met'] = bool(all(flags.values()) and year in config['positive_years'])
                for metric, interval in paired_bootstrap(control_harp, per_harp).items():
                    intervals.append(dict(year=year, candidate=candidate, metric=metric, **interval))
            rows_out.append(row)
        frame.to_parquet(output/f'predictions_{year}.parquet', index=False)
    table_out = pd.DataFrame(rows_out)
    summary = []
    for candidate in candidates[1:]:
        gated = table_out[(table_out.candidate == candidate) & table_out.year.isin(config['positive_years'])]
        summary.append(dict(candidate=candidate, years_met=int(gated.primary_met.sum()),
                            required_years=len(config['positive_years']),
                            all_year_primary=bool(gated.primary_met.all() and len(gated) == len(config['positive_years'])),
                            met_years=[int(v) for v in gated.loc[gated.primary_met, 'year']]))
    table_out.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    pd.DataFrame(summary).to_csv(output/'acceptance.csv', index=False)
    result = {'config_sha256': sha(config_path), 'source_report_sha256': evidence['predictions_report_sha256'],
              'thresholds_sha256': thresholds_sha, 'years': config['years'], 'acceptance': summary,
              'constituent_fits': len(config['years'])*len(CANDIDATES)*2,
              'bootstrap': {'draws': 1000, 'seed': 24, 'unit': 'full HARP, paired with control'},
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table_out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/region-context-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.config, args.output)
    print(pd.DataFrame(result['acceptance']).to_string(index=False))
    print(table[['year', 'candidate', 'threshold', 'tp', 'fp', 'recall', 'precision', 'episode_precision',
                 'positive_runs_alarmed', 'average_precision', 'fp_excess_over_target']].to_string(index=False))
