"""Direction split of alert false positives and a fixed causal alert cooldown (config/alert-cooldown-v1.json)."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.full_data import sha256
from scripts.audit_activity_history_relabelled import acceptance, paired_precision_bootstrap
from scripts.audit_alarm_persistence import evaluate, persistent_alarm, sha
from scripts.audit_cycle25_relabelled import alert_false_positive_origin
from scripts.audit_two_tier import point

KEY = ['harp', 'forecast_time']
CONTROL = 'control'
COOLDOWN_HOURS = {'cooldown_24h': 24, 'cooldown_48h': 48}
CANDIDATES = [CONTROL, *COOLDOWN_HOURS]
CLASSES = ['early', 'lingering', 'between', 'flaring_harp_other', 'never_flaring_harp']
OFFSETS = ['hours_since_last_positive', 'hours_to_next_positive', 'hours_to_nearest_positive']
QUANTILES = [0, .10, .25, .50, .75, .90, 1]
BIN_EDGES = [0, 6, 12, 24, 48, 72, 120, np.inf]
BIN_LABELS = ['(0,6]', '(6,12]', '(12,24]', '(24,48]', '(48,72]', '(72,120]', 'above 120']
RESERVED_START = pd.Timestamp('2024-01-01', tz='UTC')
LAST_DEVELOPMENT_YEAR = 2023
OUTCOME = {'C1_goal_met': 'result:goal-met', 'C2_partial': 'result:partial', 'C3_no_gain': 'result:no-gain'}
HOUR_NS = 3_600_000_000_000


def assert_development_period(times):
    """The reserved 2024 to 2025 period is never evaluated: stop on any timestamp at or after 2024-01-01."""
    times = pd.to_datetime(pd.Series(times), utc=True)
    if len(times) and times.max() >= RESERVED_START:
        raise ValueError('Timestamp in the reserved 2024-2025 period')


def cooldown_alarm(frame, threshold, hours):
    """Alert while above the threshold for at most `hours` consecutive hourly windows of one HARP.

    Uses only harp, forecast_time and probability of the current and earlier windows; never a label.
    """
    ordered = frame[[*KEY, 'probability']].sort_values(KEY)
    if ordered.duplicated(KEY).any():
        raise ValueError('Duplicate forecast key')
    above = ordered.probability.ge(threshold)
    alarm = above & ~persistent_alarm(ordered, 'probability', threshold, hours+1)
    return alarm.reindex(frame.index)


def alarm_states(frame, threshold):
    """Alert state of the control and of every frozen cooldown, from stored probabilities and the stored threshold."""
    states = {CONTROL: frame.probability.ge(threshold)}
    for name, hours in COOLDOWN_HOURS.items():
        states[name] = cooldown_alarm(frame, threshold, hours)
    return pd.DataFrame(states, index=frame.index)


def direction_classes(frame, alarm, near_hours=72):
    """One row per alert false-positive window with its direction class and the hours to the positive windows of its HARP.

    Uses evaluation labels: descriptive only, never an input of a candidate rule.
    """
    alarm = np.asarray(alarm, dtype=bool)
    target = frame.target.eq(1).to_numpy()
    time = pd.to_datetime(frame.forecast_time, utc=True).astype('datetime64[ns, UTC]').astype('int64').to_numpy()
    harp = frame.harp.to_numpy()
    positive = {h: np.sort(time[target & (harp == h)]) for h in np.unique(harp[target])}
    fp = frame.loc[alarm & ~target, KEY].copy()
    since, until = np.full(len(fp), np.nan), np.full(len(fp), np.nan)
    flaring = np.zeros(len(fp), dtype=bool)
    for i, (h, t) in enumerate(zip(fp.harp.to_numpy(), time[alarm & ~target])):
        times = positive.get(h)
        if times is None:
            continue
        flaring[i] = True
        after = np.searchsorted(times, t, side='right')
        before = np.searchsorted(times, t, side='left')-1
        if after < len(times):
            until[i] = (times[after]-t)/HOUR_NS
        if before >= 0:
            since[i] = (t-times[before])/HOUR_NS
    past, future = since <= near_hours, until <= near_hours
    fp['hours_since_last_positive'], fp['hours_to_next_positive'] = since, until
    fp['hours_to_nearest_positive'] = np.fmin(since, until)
    fp['direction'] = np.select([~flaring, past & future, past, future], ['never_flaring_harp', 'between', 'lingering', 'early'],
                                'flaring_harp_other')
    return fp


def direction_rows(fp, year, candidate, fallback):
    rows = []
    for name in CLASSES:
        part = fp[fp.direction.eq(name)]
        rows.append(dict(year=year, candidate=candidate, alert_fallback=fallback, direction=name, fp_windows=len(part),
                         share_of_alert_fp=len(part)/len(fp) if len(fp) else None, harps=int(part.harp.nunique())))
    return rows


def offset_rows(fp, year, candidate):
    """Quantiles and fixed-bin counts of the hour offsets of false-positive windows of flaring HARPs."""
    quantiles, bins = [], []
    for measure in OFFSETS:
        values = fp[measure].dropna()
        row = dict(year=year, candidate=candidate, measure=measure, windows=len(values))
        row.update({f'q{int(q*100):03d}': float(values.quantile(q)) if len(values) else None for q in QUANTILES})
        quantiles.append(row)
        counts = pd.cut(values, BIN_EDGES, labels=BIN_LABELS).value_counts().reindex(BIN_LABELS, fill_value=0)
        bins.extend(dict(year=year, candidate=candidate, measure=measure, bin=label, windows=int(counts[label])) for label in BIN_LABELS)
    return quantiles, bins


def tier_row(frame, alarm, tier, chosen, year, candidate):
    """Tier measures of one alert state, with the existing tier and episode code."""
    scored = frame[[*KEY, 'target', 'missing_fraction']].assign(probability=np.asarray(alarm, dtype=float))
    row = point(scored, tier, dict(chosen, threshold=.5), year)
    values, _ = evaluate(scored, 'probability', .5, 1)
    row.update(candidate=candidate, threshold=chosen['threshold'], hit_episodes=values['hit_episodes'],
               median_alarm_delay_hours=values['median_alarm_delay_hours'], max_alarm_delay_hours=values['max_alarm_delay_hours'])
    return row


def summarize(alert, years, cycle25=(2022, 2023)):
    """Per candidate: the years that meet the per-year primary acceptance and the goal conditions."""
    summary = {}
    for candidate in CANDIDATES:
        part = alert[alert.candidate.eq(candidate)].set_index('year').loc[years]
        entry = {'years_precision_at_least_0.50': [int(y) for y in years if pd.notna(part.precision[y]) and part.precision[y] >= 0.5],
                 'alert_fallback_years': [int(y) for y in years if part.fallback[y]]}
        if candidate != CONTROL:
            met = part.primary_met.astype(bool)
            lower = part.loc[list(cycle25), 'precision_difference_lower']
            entry.update(met_years=[int(y) for y in years if met[y]], all_year_primary=bool(met.all()),
                         cycle25_primary=bool(met[list(cycle25)].all()),
                         cycle25_bootstrap_lower_above_zero=bool(all(pd.notna(v) and v > 0 for v in lower)))
            entry['goal_met'] = bool(entry['all_year_primary']
                                     or (entry['cycle25_primary'] and entry['cycle25_bootstrap_lower_above_zero']))
        summary[candidate] = entry
    return summary


def read(summary):
    """Exactly one reading for any result; the rules are applied in order."""
    cooldowns = [summary[name] for name in COOLDOWN_HOURS]
    if any(entry['all_year_primary'] or (entry['cycle25_primary'] and entry['cycle25_bootstrap_lower_above_zero'])
           for entry in cooldowns):
        return 'C1_goal_met'
    if any(entry['cycle25_primary'] for entry in cooldowns):
        return 'C2_partial'
    return 'C3_no_gain'


def decision(summary):
    goal = [name for name in COOLDOWN_HOURS if summary[name]['goal_met']]
    partial = [name for name in COOLDOWN_HOURS if summary[name]['cycle25_primary']]
    return dict(candidates_meeting_goal=len(goal), goal_candidates=goal,
                candidates_meeting_cycle25_primary=len(partial), cycle25_primary_candidates=partial)


def check_protocol(config):
    """Stop when the protocol asks for anything the frozen runner does not implement."""
    if any(not 2012 <= int(year) <= LAST_DEVELOPMENT_YEAR for year in config['years']):
        raise ValueError('Only development years before the reserved 2024-2025 period are allowed')
    frozen = {c['id']: c.get('cooldown_hours') for c in config['candidates']}
    if frozen != {CONTROL: None, **COOLDOWN_HOURS}:
        raise ValueError('Candidate set differs from the frozen protocol')
    if list(config['descriptive']['classes']) != ['never_flaring_harp', 'early', 'lingering', 'between', 'flaring_harp_other'] \
            or config['descriptive']['near_hours'] != 72:
        raise ValueError('Direction classes differ from the frozen protocol')
    if config['budget']['model_fits'] != 0 or config['budget']['downloads'] != 0 or config['budget']['new_thresholds'] != 0:
        raise ValueError('This runner fits nothing, downloads nothing and selects no threshold')
    if config['reserved_test_accessed'] is not False:
        raise ValueError('Protocol must not access the reserved period')


def load_labels(directory, expected):
    """Targets of the relabelled development table; every shard is checked against the table report."""
    if sha256(directory/'report.json') != expected:
        raise ValueError(f'Input changed: {directory/"report.json"}')
    report = json.loads((directory/'report.json').read_text())
    frames = []
    for item in report['shards']:
        path = directory/'shards'/item['file']
        if path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
            raise ValueError(f'Materialized shard changed: {item["file"]}')
        frames.append(pd.read_parquet(path, columns=[*KEY, 'target']))
    labels = pd.concat(frames, ignore_index=True)
    labels['forecast_time'] = pd.to_datetime(labels.forecast_time, utc=True).astype('datetime64[ns, UTC]')
    assert_development_period(labels.forecast_time)
    if labels.duplicated(KEY).any():
        raise ValueError('Duplicate development HARP/forecast key')
    return labels


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    check_protocol(config)
    evidence = config['evidence']
    control_dir, column = Path(evidence['control']), evidence['probability_column']
    if sha(control_dir/'report.json') != evidence['control_report_sha256']:
        raise ValueError(f'Input changed: {control_dir/"report.json"}')
    stored_hashes = json.loads((control_dir/'report.json').read_text())['artifact_hashes']
    years = [int(year) for year in config['years']]
    for year in years:
        for name in ['predictions.parquet', 'thresholds.json']:
            if sha(control_dir/str(year)/name) != stored_hashes[f'{year}/{name}']:
                raise ValueError(f'Input changed: {year}/{name}')
    output.mkdir(parents=True)
    # Phase 1: alert states from stored probabilities and stored thresholds only. No label column is read.
    selections = {}
    for year in years:
        chosen = json.loads((control_dir/str(year)/'thresholds.json').read_text())
        frame = pd.read_parquet(control_dir/str(year)/'predictions.parquet', columns=[*KEY, 'prediction_end', column, 'alert_alarm'])
        frame['forecast_time'] = pd.to_datetime(frame.forecast_time, utc=True).astype('datetime64[ns, UTC]')
        assert_development_period(frame.forecast_time)
        assert_development_period(pd.to_datetime(frame.prediction_end, utc=True)-pd.Timedelta(nanoseconds=1))
        if not frame.forecast_time.dt.year.eq(year).all() or len(frame) != config['population']['windows'][str(year)]:
            raise ValueError(f'Evaluation population changed: {year}')
        frame = frame.sort_values(KEY).reset_index(drop=True).rename(columns={column: 'probability'})
        states = alarm_states(frame, chosen['alert']['threshold'])
        if not np.array_equal(states[CONTROL].to_numpy(dtype=bool), frame.alert_alarm.to_numpy(dtype=bool)):
            raise ValueError(f'Stored alert state not reproduced: {year}')
        pd.concat([frame[KEY], states], axis=1).to_parquet(output/f'alarms_{year}.parquet', index=False)
        selections[str(year)] = dict(alert=chosen['alert'], watch=chosen['watch'], alarms_sha256=sha(output/f'alarms_{year}.parquet'),
                                     alert_windows={name: int(states[name].sum()) for name in CANDIDATES})
    fallback_years = [year for year in years if selections[str(year)]['alert']['fallback']]
    if fallback_years != config['alert_fallback_years']:
        raise ValueError('Stored alert fallback years differ from the protocol')
    (output/'selections.json').write_text(json.dumps(selections, indent=2)+'\n')
    selections_sha = sha(output/'selections.json')
    # Phase 2: evaluation labels are read only now.
    labels = load_labels(Path(evidence['table']), evidence['table_report_sha256'])
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    rows, intervals, directions, quantiles, bins = [], [], [], [], []
    for year in years:
        chosen = selections[str(year)]
        if sha(output/f'alarms_{year}.parquet') != chosen['alarms_sha256']:
            raise ValueError(f'Alert states changed after selection: {year}')
        stored = pd.read_parquet(control_dir/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'missing_fraction', column])
        stored['forecast_time'] = pd.to_datetime(stored.forecast_time, utc=True).astype('datetime64[ns, UTC]')
        frame = stored.merge(pd.read_parquet(output/f'alarms_{year}.parquet'), on=KEY, how='inner', validate='one_to_one')
        frame = frame.merge(labels.rename(columns={'target': 'table_target'}), on=KEY, how='left', validate='one_to_one')
        if len(frame) != len(stored) or not frame.table_target.eq(frame.target).all():
            raise ValueError(f'Evaluation labels do not match the relabelled table: {year}')
        if int(frame.target.sum()) != config['population']['positive_windows'][str(year)]:
            raise ValueError(f'Positive windows changed: {year}')
        frame = frame.sort_values(KEY).reset_index(drop=True).rename(columns={column: 'probability'})
        fallback = bool(chosen['alert']['fallback'])
        watch = tier_row(frame, frame.probability.ge(chosen['watch']['threshold']), 'watch', chosen['watch'], year, CONTROL)
        year_rows, classes = {}, {}
        for candidate in CANDIDATES:
            alarm = frame[candidate].to_numpy(dtype=bool)
            row = tier_row(frame, alarm, 'alert', chosen['alert'], year, candidate)
            fp = direction_classes(frame, alarm, config['descriptive']['near_hours'])
            origin = alert_false_positive_origin(frame.assign(probability=alarm.astype(float)), .5)
            if len(fp) != row['fp'] or int(fp.direction.isin(['early', 'lingering', 'between']).sum()) \
                    != round((origin['alert_fp_share_within_72h_of_positive'] or 0)*len(fp)):
                raise ValueError(f'Direction classes do not add up: {year} {candidate}')
            classes[candidate] = fp
            directions.extend(direction_rows(fp, year, candidate, fallback))
            q, b = offset_rows(fp, year, candidate)
            quantiles.extend(q)
            bins.extend(b)
            year_rows[candidate] = row
        control = year_rows[CONTROL]
        control_fp = classes[CONTROL].copy()
        for candidate in COOLDOWN_HOURS:
            row = year_rows[candidate]
            flags = acceptance(row, control, tolerance)
            row.update(flags)
            row['primary_met'] = bool(all(flags.values()))
            interval = paired_precision_bootstrap(frame, frame[CONTROL].to_numpy(dtype=bool), frame[candidate].to_numpy(dtype=bool))
            intervals.append(dict(year=year, candidate=candidate, metric='alert_precision_difference', **interval))
            row.update(precision_difference_lower=interval['lower'], precision_difference_upper=interval['upper'],
                       alert_windows_removed=control['alarm_windows']-row['alarm_windows'],
                       tp_windows_removed=control['tp']-row['tp'], fp_windows_removed=control['fp']-row['fp'])
            control_fp[f'{candidate}_keeps_alert'] = frame.loc[control_fp.index, candidate].to_numpy(dtype=bool)
            kept = control_fp[control_fp[f'{candidate}_keeps_alert']].direction.value_counts()
            for entry in directions:
                if entry['year'] == year and entry['candidate'] == candidate:
                    total = int(control_fp.direction.eq(entry['direction']).sum())
                    entry['control_fp_windows_removed'] = total-int(kept.get(entry['direction'], 0))
        rows.extend([watch, *year_rows.values()])
        control_fp.to_parquet(output/f'control_fp_windows_{year}.parquet', index=False)
    table = pd.DataFrame(rows)
    table.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    pd.DataFrame(directions).to_csv(output/'directions.csv', index=False)
    pd.DataFrame(quantiles).to_csv(output/'offset_quantiles.csv', index=False)
    pd.DataFrame(bins).to_csv(output/'offset_bins.csv', index=False)
    summary = summarize(table[table.tier.eq('alert')], years)
    reading = read(summary)
    protocol_sha = sha(config_path)
    result = {'protocol': config['id'], 'protocol_sha256': protocol_sha, 'config_sha256': protocol_sha,
              'control_report_sha256': evidence['control_report_sha256'], 'table_report_sha256': evidence['table_report_sha256'],
              'selections_sha256': selections_sha, 'years': years, 'alert_fallback_years': fallback_years,
              'development_basis': 'relabelled table, walk-forward-v2, operating-point-v3',
              'candidates': CANDIDATES, 'cooldown_hours': COOLDOWN_HOURS, 'acceptance': summary, 'decision': decision(summary),
              'reading': reading, 'outcome_label': OUTCOME[reading], 'descriptive_part_has_reading': False,
              'model_fits': 0, 'constituent_fits': 0, 'downloads': 0, 'new_thresholds': 0,
              'reserved_test_accessed': False, 'model_promoted': False, 'threshold_changed': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/alert-cooldown-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(table[['year', 'candidate', 'tier', 'fallback', 'tp', 'fp', 'recall', 'precision', 'missed_positive_runs', 'positive_runs',
                 'episodes', 'median_alarm_delay_hours']].round(4).to_string(index=False))
    print(json.dumps({'acceptance': result['acceptance'], 'decision': result['decision'], 'reading': result['reading']}, indent=1))
