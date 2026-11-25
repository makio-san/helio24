"""Up-weight near-miss negatives of flaring HARPs in training, at the alert tier (config/near-miss-weighting-v1.json).

Run once from the repository root:
    OMP_NUM_THREADS=3 python -m scripts.audit_near_miss_weighting --config config/near-miss-weighting-v1.json --output artifacts/<name>_<YYYYMMDD>_r<n>
"""
import argparse
import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.calibration import SigmoidCalibration
from helio24.data import FEATURE_COLUMNS
from helio24.near_miss import near_miss_weights
from helio24.v2_training import candidate_models, load_development
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history_relabelled import acceptance, paired_precision_bootstrap, precision_at_recall
from scripts.audit_alarm_persistence import sha
from scripts.audit_cycle25 import decomposition
from scripts.audit_cycle25_relabelled import alert_false_positive_origin
from scripts.audit_two_tier import point
from scripts.rebuild_walk_forward_v2 import select_thresholds

KEY = ['harp', 'forecast_time']
TIERS = ['watch', 'alert']
META = [*KEY, 'observation_start', 'prediction_end', 'target', 'label_status', 'missing_fraction']
CANDIDATES = ['near_miss_w3', 'uniform_matched']
FACTOR, SPAN_HOURS = 3, 72
CYCLE25 = [2022, 2023]
RESERVED_START = pd.Timestamp('2024-01-01', tz='UTC')
READINGS = ['N1_near_miss_helps', 'N2_reweighting_only', 'N3_no_gain']


def check_protocol(config):
    """Refuse anything but the frozen candidates, weight factor, span, budget and development years."""
    if not str(config.get('status', '')).startswith('frozen_before_any') or config.get('reserved_test_accessed') is not False:
        raise ValueError('Protocol is not frozen or touches the reserved test')
    if [c['id'] for c in config['candidates']] != CANDIDATES:
        raise ValueError('Candidate set differs from the frozen one')
    weighting = config['weighting']
    if weighting['factor'] != FACTOR or weighting['span_hours'] != SPAN_HOURS:
        raise ValueError('Weight factor and span are fixed at 3 and 72 hours')
    years = config['years']
    if years != sorted(set(years)) or any(not 2012 <= year <= 2023 for year in years):
        raise ValueError('Only development years before the reserved test are allowed')
    if not set(CYCLE25) <= set(years):
        raise ValueError('The reading needs 2022 and 2023')
    if config['budget']['constituent_fits'] != len(years)*len(CANDIDATES)*2:
        raise ValueError('Fit budget differs from candidates x years x constituents')
    if not set(config['alert_fallback_years']) <= set(years):
        raise ValueError('Alert fallback years must be evaluated years')


def blind(meta, year):
    """The table with every label at or after the evaluation year hidden; folds do not depend on labels."""
    hidden = meta.forecast_time.ge(pd.Timestamp(f'{year}-01-01', tz='UTC'))
    return meta.assign(target=meta.target.where(~hidden, 0), label_status=meta.label_status.where(~hidden, 'hidden'))


def fit_weighted(base, x, y_train, y_cal, weight):
    """Unchanged recipes with a sample weight in both final estimators; unweighted sigmoid calibration, 0.45/0.55 ensemble."""
    share = base['ensemble']['logistic_weight']
    calibrated, evaluated, fits = {}, {}, 0
    for name, model in candidate_models(base).items():
        model.fit(x['train'], y_train, **{f'{model.steps[-1][0]}__sample_weight': weight})
        fits += 1
        raw = np.clip(model.predict_proba(x['calibration'])[:, 1], 1e-9, 1-1e-9)
        calibrator = SigmoidCalibration().fit(raw, y_cal)
        calibrated[name] = calibrator.transform(raw)
        evaluated[name] = calibrator.transform(np.clip(model.predict_proba(x['evaluation'])[:, 1], 1e-9, 1-1e-9))
        del model
    return (share*calibrated['logistic']+(1-share)*calibrated['xgboost'],
            share*evaluated['logistic']+(1-share)*evaluated['xgboost'], fits)


def fit_phase(config, base, pipeline, meta, features, control_folds, control_thresholds, fit=fit_weighted):
    """Phase 1: weights, fits and thresholds. Labels at or after each evaluation year are hidden before the fold is built."""
    budget = config['budget']['constituent_fits']
    thresholds, probabilities, weights, fits = {}, {}, [], 0
    for year in config['years']:
        split, audit = annual_fold(blind(meta, year), year)
        stored = control_folds[year]
        # The evaluation positives of the stored audit are a label count; they are compared in phase 2 only.
        if audit[:2] != stored[:2] or any(audit[2][k] != stored[2][k] for k in audit[2] if k != 'positives'):
            raise ValueError(f'Annual populations changed: {year}')
        if split['evaluation'].target.any() or max(g.prediction_end.max() for g in split.values()) > RESERVED_START:
            raise ValueError(f'Evaluation labels or reserved period reached phase 1: {year}')
        train, calibration = split['train'], split['calibration']
        evaluation = split['evaluation'].drop(columns=['target', 'label_status'])
        targeted, uniform, mask = near_miss_weights(train, FACTOR, SPAN_HOURS)
        negative = train.target.eq(0).to_numpy()
        row = dict(year=year, train_rows=len(train), train_positives=int((~negative).sum()), train_negatives=int(negative.sum()),
                   near_miss_negatives=int(mask.sum()), flaring_training_harps=int(train.harp[~negative].nunique()),
                   near_miss_weight=float(FACTOR), uniform_negative_weight=float(uniform[negative][0]),
                   negative_weight_total_near_miss_w3=float(targeted[negative].sum()),
                   negative_weight_total_uniform_matched=float(uniform[negative].sum()),
                   calibration_weight=1.0, evaluation_weight=1.0)
        expected = config['population'][str(year)]
        if any(row[k] != expected[k] for k in ['train_rows', 'train_positives', 'train_negatives', 'near_miss_negatives']):
            raise ValueError(f'Training population or near-miss membership differs from the protocol: {year}')
        weights.append(row)
        x = {role: features[group.index.to_numpy()] for role, group in [('train', train), ('calibration', calibration), ('evaluation', evaluation)]}
        y_train, y_cal = train.target.to_numpy(dtype=np.int8), calibration.target.to_numpy(dtype=np.int8)
        chosen = {'control': control_thresholds[year]}
        frame = evaluation[KEY].reset_index(drop=True)
        for candidate, weight in zip(CANDIDATES, [targeted, uniform]):
            if fits+2 > budget:
                raise RuntimeError('Fit budget of the protocol would be exceeded')
            p_cal, p_eval, used = fit(base, x, y_train, y_cal, weight)
            fits += used
            chosen[candidate] = select_thresholds(pipeline, y_cal, p_cal)
            frame[candidate] = p_eval
            gc.collect()
        thresholds[str(year)], probabilities[year] = chosen, frame
        print(f'{year}: alert thresholds ' + ', '.join(f'{c}={v["alert"]["threshold"]:.4f}' for c, v in chosen.items()), flush=True)
        del split, x
        gc.collect()
    if fits != budget:
        raise RuntimeError('Constituent fits differ from the protocol budget')
    return thresholds, probabilities, weights, fits


def freeze_phase(output, thresholds, probabilities, weights):
    """Write thresholds, weights and candidate probabilities and hash them; nothing after this may change them."""
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    pd.DataFrame(weights).to_csv(output/'weights.csv', index=False)
    for year, frame in probabilities.items():
        frame.to_parquet(output/f'probabilities_{year}.parquet', index=False)
    manifest = {p.name: sha(p) for p in sorted(output.iterdir())}
    (output/'phase1.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def entry(part, reference=None):
    """Per-candidate summary of the alert rows indexed by year."""
    out = {'years_precision_at_least_0.50': [int(y) for y in part.index if pd.notna(part.precision[y]) and part.precision[y] >= 0.5],
           'alert_fallback_years': [int(y) for y in part.index if part.fallback[y]]}
    if reference is not None:
        met = part.primary_met.astype(bool)
        out.update(met_years=[int(y) for y in part.index[met]], all_year_primary=bool(met.all()),
                   cycle25_primary=bool(met[CYCLE25].all()),
                   cycle25_bootstrap_lower_above_zero=bool((part.loc[CYCLE25, 'precision_difference_lower'].astype(float) > 0).all()))
    return out


def meets_goal(summary):
    return bool(summary['all_year_primary'] or (summary['cycle25_primary'] and summary['cycle25_bootstrap_lower_above_zero']))


def read(summary):
    """N1, N2 or N3, tried in this order; the first that holds is the reading."""
    near, uniform = summary['near_miss_w3'], summary['uniform_matched']
    specific = bool((near['all_year_primary'] and near['beats_uniform_all_years'])
                    or (near['cycle25_primary'] and near['cycle25_bootstrap_lower_above_zero'] and near['beats_uniform_cycle25']))
    meeting = [c for c in CANDIDATES if meets_goal(summary[c])]
    reading = READINGS[0] if specific else READINGS[1] if meeting else READINGS[2]
    return dict(reading=reading, near_miss_w3_goal_met_and_beats_uniform=int(specific), candidates_meeting_goal_against_control=meeting,
                outcome_label={'N1_near_miss_helps': 'result:goal-met', 'N2_reweighting_only': 'result:partial',
                               'N3_no_gain': 'result:no-gain'}[reading])


def evaluate_phase(config, meta, control_dir, control_folds, thresholds, output):
    """Phase 2: evaluation labels are read only here, after phase 1 was written and hashed."""
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    names = ['control', *CANDIDATES]
    rows, intervals = [], []
    for year in config['years']:
        split, audit = annual_fold(meta, year)
        if audit != control_folds[year]:
            raise ValueError(f'Annual populations changed: {year}')
        labels = split['evaluation'][[*KEY, 'target', 'missing_fraction']]
        stored = pd.read_parquet(control_dir/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'ensemble'])
        candidate = pd.read_parquet(output/f'probabilities_{year}.parquet')
        frame = labels.merge(stored.rename(columns={'ensemble': 'control', 'target': 'stored_target'}), on=KEY, how='inner')
        frame = frame.merge(candidate, on=KEY, how='inner')
        if not len(frame) == len(labels) == len(stored) == len(candidate):
            raise ValueError(f'Evaluation keys do not match: {year}')
        if not frame.target.eq(frame.stored_target).all():
            raise ValueError(f'Stored control labels differ from the relabelled table: {year}')
        if frame.forecast_time.max() >= RESERVED_START:
            raise ValueError('Reserved period reached the evaluation')
        frame = frame.drop(columns='stored_target').sort_values(KEY).reset_index(drop=True)
        year_rows, alarms = {}, {}
        for name in names:
            scored = frame[[*KEY, 'target', 'missing_fraction']].assign(probability=frame[name])
            chosen = thresholds[str(year)][name]
            parts = decomposition(scored, chosen['watch']['threshold'])
            origin = alert_false_positive_origin(scored, chosen['alert']['threshold'])
            alarms[name] = frame[name].ge(chosen['alert']['threshold']).to_numpy()
            for tier in TIERS:
                row = point(scored, tier, chosen[tier], year)
                row.update(candidate=name, average_precision=parts['overall_ap'], within_flaring_ap=parts['within_flaring_ap'],
                           region_ap=parts['region_ap'])
                if tier == 'alert':
                    row.update(alert_fp_share_never_flaring_harps=origin['alert_fp_share_never_flaring_harps'],
                           alert_fp_share_within_72h_of_positive=origin['alert_fp_share_within_72h_of_positive'])
                year_rows[(name, tier)] = row
        control = year_rows[('control', 'alert')]
        control['precision_at_control_recall'] = control['precision']
        for name in CANDIDATES:
            row = year_rows[(name, 'alert')]
            flags = acceptance(row, control, tolerance)
            row.update(flags)
            row['primary_met'] = bool(all(flags.values()))
            row['precision_at_control_recall'] = precision_at_recall(frame.target.to_numpy(), frame[name].to_numpy(), control['recall'])
            interval = paired_precision_bootstrap(frame, alarms['control'], alarms[name])
            intervals.append(dict(year=year, candidate=name, reference='control', metric='alert_precision_difference', **interval))
            row.update(precision_difference_lower=interval['lower'], precision_difference_upper=interval['upper'])
        near = year_rows[('near_miss_w3', 'alert')]
        near['beats_uniform'] = bool(all(acceptance(near, year_rows[('uniform_matched', 'alert')], tolerance).values()))
        interval = paired_precision_bootstrap(frame, alarms['uniform_matched'], alarms['near_miss_w3'])
        intervals.append(dict(year=year, candidate='near_miss_w3', reference='uniform_matched', metric='alert_precision_difference', **interval))
        near.update(precision_difference_to_uniform_lower=interval['lower'], precision_difference_to_uniform_upper=interval['upper'])
        rows.extend(year_rows.values())
        frame.to_parquet(output/f'predictions_{year}.parquet', index=False)
    table = pd.DataFrame(rows)
    table.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    alert = table[table.tier.eq('alert')]
    summary = {name: entry(alert[alert.candidate.eq(name)].set_index('year'), None if name == 'control' else 'control') for name in names}
    beats = alert[alert.candidate.eq('near_miss_w3')].set_index('year').beats_uniform.astype(bool)
    summary['near_miss_w3'].update(beats_uniform_years=[int(y) for y in beats.index[beats]], beats_uniform_all_years=bool(beats.all()),
                                   beats_uniform_cycle25=bool(beats[CYCLE25].all()))
    return table, summary


def run(config_path, output, fit=fit_weighted):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    check_protocol(config)
    evidence = config['evidence']
    control_dir = Path(evidence['control'])
    for path, expected in [(Path(evidence['table'])/'report.json', evidence['table_report_sha256']),
                           (control_dir/'report.json', evidence['control_report_sha256']),
                           (Path(evidence['pipeline_protocol']), evidence['pipeline_protocol_sha256']),
                           (Path(evidence['base_protocol']), evidence['base_protocol_sha256'])]:
        if sha(path) != expected:
            raise ValueError(f'Input changed: {path}')
    control_report = json.loads((control_dir/'report.json').read_text())
    control_folds = {f['year']: f['audit'] for f in control_report['folds'] if f['year'] in config['years']}
    control_thresholds = {}
    for year in config['years']:
        for name in ['thresholds.json', 'predictions.parquet']:
            if sha(control_dir/str(year)/name) != control_report['artifact_hashes'][f'{year}/{name}']:
                raise ValueError(f'Stored control file changed: {year}/{name}')
        control_thresholds[year] = json.loads((control_dir/str(year)/'thresholds.json').read_text())
    fallback = [year for year in config['years'] if control_thresholds[year]['alert']['fallback']]
    if fallback != config['alert_fallback_years']:
        raise ValueError('Stored alert fallback years differ from the protocol')
    pipeline = json.loads(Path(evidence['pipeline_protocol']).read_text())
    base = json.loads(Path(evidence['base_protocol']).read_text())
    groups, _ = load_development(Path(evidence['table']), evidence['table_report_sha256'])
    development = pd.concat(groups.values(), ignore_index=True)
    del groups
    if development.forecast_time.max() >= RESERVED_START:
        raise ValueError('Reserved period in the development table')
    meta = development[META].copy()
    features = development[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    del development
    gc.collect()
    output.mkdir(parents=True)
    thresholds, probabilities, weights, fits = fit_phase(config, base, pipeline, meta, features, control_folds, control_thresholds, fit)
    del features
    phase1 = freeze_phase(output, thresholds, probabilities, weights)
    del probabilities
    phase1_sha = sha(output/'phase1.json')
    table, summary = evaluate_phase(config, meta, control_dir, control_folds, thresholds, output)
    if {name: sha(output/name) for name in phase1} != phase1:
        raise RuntimeError('Phase 1 files changed after evaluation labels were read')
    decision = read(summary)
    result = {'config_sha256': sha(config_path), 'phase1_sha256': phase1_sha, 'thresholds_sha256': phase1['thresholds.json'],
              'years': config['years'], 'alert_fallback_years_control': fallback,
              'development_basis': 'relabelled table, walk-forward-v2, operating-point-v3',
              'weighting': {'factor': FACTOR, 'span_hours': SPAN_HOURS, 'per_year': weights},
              'acceptance': summary, 'decision': decision, 'reading': decision['reading'], 'constituent_fits': fits,
              'reserved_test_accessed': False, 'model_promoted': False, 'threshold_adopted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(table[['year', 'candidate', 'tier', 'fallback', 'tp', 'fp', 'recall', 'precision', 'accuracy', 'always_negative_accuracy',
                 'missed_positive_runs', 'positive_runs', 'average_precision', 'within_flaring_ap']].round(4).to_string(index=False))
    print(json.dumps({'acceptance': result['acceptance'], 'decision': result['decision']}, indent=1))
