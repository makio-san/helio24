"""Within-HARP ranking and timing scores stacked on the control, at the alert tier (config/within-harp-ranking-v1.json).

Run once from the repository root:
    OMP_NUM_THREADS=3 python -m scripts.audit_within_harp_ranking --config config/within-harp-ranking-v1.json --output artifacts/<name>_<YYYYMMDD>_r<n>
"""
import argparse
import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.calibration import SigmoidCalibration
from helio24.data import FEATURE_COLUMNS
from helio24.v2_training import candidate_models, load_development
from helio24.walk_forward import annual_fold
from helio24.within_harp import control_logit, fit_stack, margin, ranker_model, ranker_objective, ranking_rows
from scripts.audit_activity_history_relabelled import acceptance, paired_precision_bootstrap, precision_at_recall
from scripts.audit_alarm_persistence import evaluate, sha
from scripts.audit_alert_cooldown import CLASSES, direction_classes
from scripts.audit_cycle25 import decomposition
from scripts.audit_cycle25_relabelled import alert_false_positive_origin
from scripts.audit_horizon_72h import extend_labels
from scripts.audit_two_tier import point
from scripts.rebuild_walk_forward_v2 import select_thresholds

KEY = ['harp', 'forecast_time']
TIERS = ['watch', 'alert']
META = [*KEY, 'observation_start', 'prediction_end', 'target', 'label_status', 'missing_fraction']
CONTROL = 'control'
RESTACK = 'restack_control'
SPECIALISTS = ['harp_ranker', 'timing_specialist']
CANDIDATES = [RESTACK, *SPECIALISTS]
MARGINS = {'harp_ranker': 'ranker_margin', 'timing_specialist': 'timing_margin'}
CYCLE25 = [2022, 2023]
HORIZON_HOURS = 72
CONSTITUENTS_PER_YEAR = 4
STACKS_PER_YEAR = 3
RESERVED_START = pd.Timestamp('2024-01-01', tz='UTC')
READINGS = ['S1_within_harp_helps', 'S2_restack_or_unattributed', 'S3_no_gain']
OUTCOME = {'S1_within_harp_helps': 'result:goal-met', 'S2_restack_or_unattributed': 'result:partial', 'S3_no_gain': 'result:no-gain'}
STACK_LOGISTIC = {'C': 1.0, 'solver': 'lbfgs', 'max_iter': 2000, 'random_state': 24}
POPULATION_CHECKED = ['train_rows', 'train_positives', 'flaring_training_harps', 'ranker_rows', 'timing_rows', 'timing_positives']


def check_protocol(config):
    """Refuse anything but the frozen candidates, stack, objective, budget and development years."""
    if not str(config.get('status', '')).startswith('frozen_before_any') or config.get('reserved_test_accessed') is not False:
        raise ValueError('Protocol is not frozen or touches the reserved test')
    if [c['id'] for c in config['candidates']] != CANDIDATES or config['control']['id'] != CONTROL:
        raise ValueError('Candidate set differs from the frozen one')
    years = config['years']
    if years != sorted(set(years)) or any(not 2012 <= year <= 2023 for year in years):
        raise ValueError('Only development years before the reserved test are allowed')
    if not set(CYCLE25) <= set(years):
        raise ValueError('The reading needs 2022 and 2023')
    budget = config['budget']
    if budget['constituent_fits'] != len(years)*CONSTITUENTS_PER_YEAR or budget['stack_fits'] != len(years)*STACKS_PER_YEAR:
        raise ValueError('Fit budget differs from years x (2 control refits + 2 specialists) and years x 3 stacks')
    if budget['hyperparameter_search'] != 0 or budget['downloads'] != 0:
        raise ValueError('No search and no download')
    if config['timing_subset']['horizon_hours'] != HORIZON_HOURS:
        raise ValueError('The timing subset uses the 72-hour label only')
    stack = config['stack']
    if stack['inputs'] != {RESTACK: ['control_logit'], 'harp_ranker': ['control_logit', 'ranker_margin'],
                           'timing_specialist': ['control_logit', 'timing_margin']}:
        raise ValueError('Stack inputs differ from the frozen ones')
    if config['harp_ranker']['objective'].get('name') != 'rank:pairwise' or config['stack']['logistic'] != STACK_LOGISTIC:
        raise ValueError('Ranking objective or stack settings differ from the frozen ones')
    if not set(config['alert_fallback_years']) <= set(years):
        raise ValueError('Alert fallback years must be evaluated years')


def blind(meta, year):
    """The table with every label at or after the evaluation year hidden; folds do not depend on labels."""
    hidden = meta.forecast_time.ge(pd.Timestamp(f'{year}-01-01', tz='UTC'))
    return meta.assign(target=meta.target.where(~hidden, 0), label_status=meta.label_status.where(~hidden, 'hidden'))


def timing_rows(train, calibration_start):
    """Positions into `train` of the windows whose 72-hour label is positive, and their 24-hour targets.

    The 72-hour label is built from the training-role rows alone with scripts.audit_horizon_72h.extend_labels, so a
    label is known only when the window 48 hours later is itself a training window; a later window never enters.
    """
    if 'role' in train.columns and not train.role.eq('train').all():
        raise ValueError('Timing membership is computed inside the training role only')
    frame = train[[*KEY, 'target']].assign(position=np.arange(len(train)))
    extended = extend_labels(frame)
    # Purge: a window whose 72-hour horizon (forecast time plus 72 hours) reaches the calibration role never enters.
    reaching = extended.prediction_end.gt(calibration_start)
    subset = extended[extended.target.eq(1) & ~reaching].sort_values('position')
    y = subset.target24.to_numpy(dtype=np.int8)
    if set(np.unique(y)) != {0, 1}:
        raise ValueError('The timing subset needs both 24-hour classes')
    return subset.position.to_numpy(), y, dict(label_unknown=len(train)-len(extended), horizon_purged=int(reaching.sum()))


def fit_control(base, x, y_train, y_cal):
    """Refit of the two control constituents exactly as scripts.rebuild_walk_forward_v2 did; calibration and evaluation ensemble."""
    weights = base['ensemble']
    calibrated, evaluated = {}, {}
    for name, model in candidate_models(base).items():
        model.fit(x['train'], y_train)
        raw = model.predict_proba(x['calibration'])[:, 1]
        calibrator = SigmoidCalibration().fit(raw, y_cal)
        calibrated[name] = calibrator.transform(raw)
        evaluated[name] = calibrator.transform(model.predict_proba(x['evaluation'])[:, 1])
        del model
    return (weights['logistic_weight']*calibrated['logistic']+weights['xgboost_weight']*calibrated['xgboost'],
            weights['logistic_weight']*evaluated['logistic']+weights['xgboost_weight']*evaluated['xgboost'], 2)


def fit_ranker(base, x_train, harps, y_train, frozen_objective):
    model = ranker_model(base)
    model.fit(x_train, y_train, xgbranker__qid=harps)
    if ranker_objective(model) != frozen_objective:
        raise ValueError('The ranking objective XGBoost used differs from the frozen one')
    return model


def fit_timing(base, x_train, y_train):
    model = candidate_models(base)['xgboost']
    model.fit(x_train, y_train)
    return model


def same_thresholds(rebuilt, stored, tolerance):
    return (all(abs(rebuilt[tier]['threshold']-stored[tier]['threshold']) <= tolerance for tier in TIERS)
            and bool(rebuilt['alert']['fallback']) == bool(stored['alert']['fallback']))


def fit_phase(config, base, pipeline, meta, features, control_dir, control_folds, control_thresholds):
    """Phase 1: fits, stacks and thresholds. Labels at or after each evaluation year are hidden before the fold is built."""
    budget, tolerance = config['budget'], config['control_refit']['max_abs_difference']
    frozen_objective = config['harp_ranker']['objective']
    stack_params = config['stack']['logistic']
    thresholds, probabilities, stacks, population = {}, {}, {}, []
    fits = stack_fits = 0
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
        calibration_start = pd.Timestamp(f'{year-1}-01-01', tz='UTC')
        ranked, harps = ranking_rows(train)
        timed, y_timing, removed = timing_rows(train, calibration_start)
        row = dict(year=year, train_rows=len(train), train_positives=int(train.target.sum()),
                   flaring_training_harps=int(len(np.unique(harps))), ranker_rows=len(ranked),
                   ranker_positives=int(train.target.to_numpy()[ranked].sum()), timing_rows=len(timed),
                   timing_positives=int(y_timing.sum()), timing_negatives=int((y_timing == 0).sum()),
                   timing_label_unknown=removed['label_unknown'], timing_horizon_purged=removed['horizon_purged'], calibration_rows=len(calibration),
                   calibration_positives=int(calibration.target.sum()), evaluation_rows=len(evaluation))
        expected = config['population'][str(year)]
        if any(row[k] != expected[k] for k in POPULATION_CHECKED):
            raise ValueError(f'Training population, query groups or timing subset differ from the protocol: {year}')
        population.append(row)
        x = {role: features[group.index.to_numpy()] for role, group in [('train', train), ('calibration', calibration), ('evaluation', evaluation)]}
        y_train, y_cal = train.target.to_numpy(dtype=np.int8), calibration.target.to_numpy(dtype=np.int8)
        if fits+CONSTITUENTS_PER_YEAR > budget['constituent_fits'] or stack_fits+STACKS_PER_YEAR > budget['stack_fits']:
            raise RuntimeError('Fit budget of the protocol would be exceeded')
        p_cal, p_eval, used = fit_control(base, x, y_train, y_cal)
        fits += used
        stored_eval = pd.read_parquet(control_dir/str(year)/'predictions.parquet', columns=[*KEY, 'ensemble'])
        merged = evaluation[KEY].assign(refit=p_eval).merge(stored_eval, on=KEY, how='inner')
        if len(merged) != len(evaluation) or len(stored_eval) != len(evaluation) \
                or float(np.max(np.abs(merged.refit-merged.ensemble))) > tolerance:
            raise ValueError(f'The control refit does not reproduce the stored control probabilities: {year}')
        if not same_thresholds(select_thresholds(pipeline, y_cal, p_cal), control_thresholds[year], config['control_refit']['threshold_tolerance']):
            raise ValueError(f'The control refit does not reproduce the stored thresholds: {year}')
        ranker = fit_ranker(base, x['train'][ranked], harps, y_train[ranked], frozen_objective)
        timing = fit_timing(base, x['train'][timed], y_timing)
        fits += 2
        z = {'calibration': {'control_logit': control_logit(p_cal)}, 'evaluation': {'control_logit': control_logit(p_eval)}}
        for role in z:
            z[role]['ranker_margin'], z[role]['timing_margin'] = margin(ranker, x[role]), margin(timing, x[role])
        del ranker, timing
        chosen, coefficients = {CONTROL: control_thresholds[year]}, {}
        frame = evaluation[KEY].reset_index(drop=True)
        for column in ['control_logit', 'ranker_margin', 'timing_margin']:
            frame[column] = z['evaluation'][column]
        for candidate in CANDIDATES:
            inputs = config['stack']['inputs'][candidate]
            s_cal, s_eval, coefficients[candidate] = fit_stack(
                stack_params, np.column_stack([z['calibration'][c] for c in inputs]), y_cal,
                np.column_stack([z['evaluation'][c] for c in inputs]))
            stack_fits += 1
            coefficients[candidate]['inputs'] = inputs
            chosen[candidate] = select_thresholds(pipeline, y_cal, s_cal)
            frame[candidate] = s_eval
        thresholds[str(year)], stacks[str(year)], probabilities[year] = chosen, coefficients, frame
        print(f'{year}: alert thresholds ' + ', '.join(f'{c}={v["alert"]["threshold"]:.4f}' for c, v in chosen.items()), flush=True)
        del split, x
        gc.collect()
    if fits != budget['constituent_fits'] or stack_fits != budget['stack_fits']:
        raise RuntimeError('Fits differ from the protocol budget')
    return thresholds, probabilities, stacks, population, fits, stack_fits


def freeze_phase(output, thresholds, probabilities, stacks, population):
    """Write thresholds, stacks, populations and candidate scores and hash them; nothing after this may change them."""
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    (output/'stacks.json').write_text(json.dumps(stacks, indent=2)+'\n')
    pd.DataFrame(population).to_csv(output/'population.csv', index=False)
    for year, frame in probabilities.items():
        frame.to_parquet(output/f'probabilities_{year}.parquet', index=False)
    manifest = {p.name: sha(p) for p in sorted(output.iterdir())}
    (output/'phase1.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def direction_shares(scored, threshold):
    """Shares of alert FP windows by the direction classes of docs/alert-cooldown-20261125.md; descriptive only."""
    fp = direction_classes(scored, scored.probability.ge(threshold).to_numpy())
    return {f'alert_fp_share_{name}': (float(fp.direction.eq(name).mean()) if len(fp) else None) for name in CLASSES}


def entry(part, judged=False, specialist=False):
    """Per-candidate summary of the alert rows indexed by year."""
    out = {'years_precision_at_least_0.50': [int(y) for y in part.index if pd.notna(part.precision[y]) and part.precision[y] >= 0.5],
           'alert_fallback_years': [int(y) for y in part.index if part.fallback[y]]}
    if judged:
        met = part.primary_met.astype(bool)
        lower = part.loc[CYCLE25, 'precision_difference_lower']
        out.update(met_years=[int(y) for y in part.index[met]], all_year_primary=bool(met.all()),
                   cycle25_primary=bool(met[CYCLE25].all()),
                   cycle25_bootstrap_lower_above_zero=bool(all(pd.notna(v) and float(v) > 0 for v in lower)))
        out['goal_met'] = meets_goal(out)
    if specialist:
        beats = part.beats_restack.astype(bool)
        out.update(beats_restack_years=[int(y) for y in part.index[beats]], beats_restack_all_years=bool(beats.all()),
                   beats_restack_cycle25=bool(beats[CYCLE25].all()))
    return out


def meets_goal(summary):
    return bool(summary['all_year_primary'] or (summary['cycle25_primary'] and summary['cycle25_bootstrap_lower_above_zero']))


def specific_goal(summary):
    """Goal against control by a path, and beats restack_control in every year of that same path."""
    return bool((summary['all_year_primary'] and summary['beats_restack_all_years'])
                or (summary['cycle25_primary'] and summary['cycle25_bootstrap_lower_above_zero'] and summary['beats_restack_cycle25']))


def read(summary):
    """S1, S2 or S3, tried in this order; the first that holds is the reading."""
    specific = [c for c in SPECIALISTS if specific_goal(summary[c])]
    meeting = [c for c in CANDIDATES if meets_goal(summary[c])]
    reading = READINGS[0] if specific else READINGS[1] if meeting else READINGS[2]
    return dict(reading=reading, specific_candidates_meeting_goal=len(specific), specific_candidates=specific,
                candidates_meeting_goal_against_control=meeting, outcome_label=OUTCOME[reading])


def evaluate_phase(config, meta, control_dir, control_folds, thresholds, output):
    """Phase 2: evaluation labels are read only here, after phase 1 was written and hashed."""
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    names = [CONTROL, *CANDIDATES]
    rows, intervals = [], []
    for year in config['years']:
        split, audit = annual_fold(meta, year)
        if audit != control_folds[year]:
            raise ValueError(f'Annual populations changed: {year}')
        labels = split['evaluation'][[*KEY, 'target', 'missing_fraction']]
        stored = pd.read_parquet(control_dir/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'ensemble'])
        candidate = pd.read_parquet(output/f'probabilities_{year}.parquet')
        frame = labels.merge(stored.rename(columns={'ensemble': CONTROL, 'target': 'stored_target'}), on=KEY, how='inner')
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
            alarms[name] = frame[name].ge(chosen['alert']['threshold']).to_numpy()
            for tier in TIERS:
                row = point(scored, tier, chosen[tier], year)
                values, _ = evaluate(scored, 'probability', chosen[tier]['threshold'], 1)
                row.update(candidate=name, average_precision=parts['overall_ap'], within_flaring_ap=parts['within_flaring_ap'],
                           region_ap=parts['region_ap'], hit_episodes=values['hit_episodes'],
                           median_alarm_delay_hours=values['median_alarm_delay_hours'])
                if tier == 'alert':
                    origin = alert_false_positive_origin(scored, chosen['alert']['threshold'])
                    row.update(alert_fp_share_never_flaring_harps=origin['alert_fp_share_never_flaring_harps'],
                               alert_fp_share_within_72h_of_positive=origin['alert_fp_share_within_72h_of_positive'],
                               **direction_shares(scored, chosen['alert']['threshold']))
                    if name in MARGINS:
                        raw = frame[[*KEY, 'target', 'missing_fraction']].assign(probability=frame[MARGINS[name]])
                        row['margin_within_flaring_ap'] = decomposition(raw, np.inf)['within_flaring_ap']
                year_rows[(name, tier)] = row
        control = year_rows[(CONTROL, 'alert')]
        control['precision_at_control_recall'] = control['precision']
        for name in CANDIDATES:
            row = year_rows[(name, 'alert')]
            flags = acceptance(row, control, tolerance)
            row.update(flags)
            row['primary_met'] = bool(all(flags.values()))
            row['alert_windows_differing_from_control'] = int((alarms[name] != alarms[CONTROL]).sum())
            row['within_flaring_ap_above_control'] = bool(row['within_flaring_ap'] > control['within_flaring_ap'])
            row['precision_at_control_recall'] = precision_at_recall(frame.target.to_numpy(), frame[name].to_numpy(), control['recall'])
            interval = paired_precision_bootstrap(frame, alarms[CONTROL], alarms[name])
            intervals.append(dict(year=year, candidate=name, reference=CONTROL, metric='alert_precision_difference', **interval))
            row.update(precision_difference_lower=interval['lower'], precision_difference_upper=interval['upper'])
        restack = year_rows[(RESTACK, 'alert')]
        for name in SPECIALISTS:
            row = year_rows[(name, 'alert')]
            row['beats_restack'] = bool(all(acceptance(row, restack, tolerance).values()))
            interval = paired_precision_bootstrap(frame, alarms[RESTACK], alarms[name])
            intervals.append(dict(year=year, candidate=name, reference=RESTACK, metric='alert_precision_difference', **interval))
            row.update(precision_difference_to_restack_lower=interval['lower'], precision_difference_to_restack_upper=interval['upper'])
        rows.extend(year_rows.values())
        frame.to_parquet(output/f'predictions_{year}.parquet', index=False)
    table = pd.DataFrame(rows)
    table.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    alert = table[table.tier.eq('alert')]
    summary = {name: entry(alert[alert.candidate.eq(name)].set_index('year'), name != CONTROL, name in SPECIALISTS) for name in names}
    above = alert[alert.candidate.isin(SPECIALISTS) & alert.year.isin(CYCLE25)].groupby('candidate').within_flaring_ap_above_control.all()
    summary['descriptive'] = {'within_flaring_ap_above_control_in_2022_and_2023': {c: bool(above.get(c, False)) for c in SPECIALISTS}}
    summary['descriptive']['within_harp_route_closed_for_96_summaries'] = not any(
        summary['descriptive']['within_flaring_ap_above_control_in_2022_and_2023'].values())
    return table, summary


def run(config_path, output):
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
    thresholds, probabilities, stacks, population, fits, stack_fits = fit_phase(
        config, base, pipeline, meta, features, control_dir, control_folds, control_thresholds)
    del features
    phase1 = freeze_phase(output, thresholds, probabilities, stacks, population)
    del probabilities
    phase1_sha = sha(output/'phase1.json')
    table, summary = evaluate_phase(config, meta, control_dir, control_folds, thresholds, output)
    if {name: sha(output/name) for name in phase1} != phase1:
        raise RuntimeError('Phase 1 files changed after evaluation labels were read')
    decision = read(summary)
    result = {'config_sha256': sha(config_path), 'phase1_sha256': phase1_sha, 'thresholds_sha256': phase1['thresholds.json'],
              'years': config['years'], 'alert_fallback_years_control': fallback,
              'development_basis': 'relabelled table, walk-forward-v2, operating-point-v3',
              'population': population, 'stacks': stacks, 'acceptance': summary, 'decision': decision, 'reading': decision['reading'],
              'constituent_fits': fits, 'stack_fits': stack_fits, 'reserved_test_accessed': False, 'model_promoted': False,
              'threshold_adopted': False, 'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
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
