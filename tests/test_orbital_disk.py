"""Synthetic tests of config/orbital-disk-v1.json, helio24.orbital_disk and the runner; no project data or evidence is read."""
import copy
import itertools
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import scripts.audit_orbital_disk as runner
from helio24.data import FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.orbital_disk import (BAND, FLAG, KEY, ORBITAL, POSITION, SIDE, disk_band, disk_position_features, latest_issue,
                                  orbital_phase_features, parse_location, srs_positions, utc_hour)
from helio24.v2_training import METADATA
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history_relabelled import fit_probabilities
from scripts.audit_region_context_sources import available_srs, parse_srs

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'config/orbital-disk-v1.json'
YEARS = [2022, 2023]
HOUR = pd.Timedelta(hours=1)
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def ts(text):
    return pd.Timestamp(text, tz='UTC')


def location(latitude, longitude):
    return f'{"N" if latitude >= 0 else "S"}{abs(int(latitude)):02d}{"W" if longitude >= 0 else "E"}{abs(int(longitude)):02d}'


def srs_text(day, regions, issued_hhmm='0030'):
    """One SRS product in the NOAA layout; `regions` are (noaa, latitude, longitude, area)."""
    lines = [f':Product: {day:%m%d}SRS.txt', f':Issued: {day:%Y} {MONTHS[day.month-1]} {day:%d} {issued_hhmm} UTC',
             'Joint USAF/NOAA Solar Region Summary', f'I.  Regions with Sunspots.  Locations Valid at {(day-pd.Timedelta(days=1)):%d}/2400Z',
             'Nmbr Location  Lo  Area  Z   LL   NN Mag Type']
    lines += [f'{noaa % 10000:04d} {location(lat, lon)}   100  {area:04d} Dao  06   05 Beta' for noaa, lat, lon, area in regions]
    lines += ['IA. H-alpha Plages without Spots.  Locations Valid at 14/2400Z', 'Nmbr  Location  Lo']
    return '\n'.join(lines)+'\n'


def sources_from(texts, mapping_rows):
    """In-memory issued, rows and mapping frames as the loaders of scripts.audit_region_context_sources return them."""
    issued, rows = [], []
    for day, text in texts.items():
        when, regions = parse_srs(text)
        issued.append({'date': day.strftime('%Y-%m-%d'), 'issued_utc': when})
        rows.extend({'issued_utc': when, **region} for region in regions)
    mapping = pd.DataFrame(mapping_rows, columns=['harp', 'date', 'noaa'])
    return pd.DataFrame(issued), pd.DataFrame(rows), mapping


def keys(harp, times):
    return pd.DataFrame({'harp': harp, 'forecast_time': [ts(t) if isinstance(t, str) else t for t in times]})


def harp_windows(harp, start, hours, positive_hours=()):
    frame = pd.DataFrame({'harp': harp, 'forecast_time': [pd.Timestamp(start, tz='UTC')+int(h)*HOUR+pd.Timedelta(minutes=11) for h in hours]})
    frame['target'] = [int(h in set(positive_hours)) for h in hours]
    frame['observation_start'] = frame.forecast_time-12*HOUR
    frame['prediction_end'] = frame.forecast_time+24*HOUR
    frame['label_status'] = np.where(frame.target.eq(1), 'positive', 'negative')
    frame['missing_fraction'] = 0.0
    return frame


def synthetic_world(seed=24):
    """Eight HARPs a year from 2018 to 2023, 240 hourly windows each, every second HARP with one positive day.

    HARPs with k < 6 carry a NOAA number and an SRS listing that moves 13 degrees per day from E60; the others have none.
    """
    rng = np.random.default_rng(seed)
    parts, texts, mapping, harp = [], {}, [], 0
    for year in range(2018, 2024):
        for k in range(8):
            harp += 1
            start = pd.Timestamp(f'{year}-02-01')+pd.Timedelta(days=30*k)
            part = harp_windows(harp, start, range(240), range(100, 124) if k % 2 == 0 else ())
            part['flaring'] = int(k % 2 == 0)
            parts.append(part)
            for d in range(11):
                day = start+pd.Timedelta(days=d)
                if k < 6:
                    mapping.append((harp, day.date(), 12000+harp))
                    texts.setdefault(day, []).append((12000+harp, 10+k, -60+13*d, 50+10*k))
    for day in pd.date_range('2018-01-01', '2023-12-31', freq='15D'):
        texts.setdefault(day, [])
    table = pd.concat(parts, ignore_index=True)
    values = rng.normal(size=(len(table), len(FEATURE_COLUMNS))).astype(np.float32)
    values[:, 0] += 2*table.target.to_numpy()+table.flaring.to_numpy()
    table = pd.concat([table.drop(columns='flaring'), pd.DataFrame(values, columns=FEATURE_COLUMNS)], axis=1)
    year = table.forecast_time.dt.year
    table['role'] = np.where(year <= 2021, 'train', np.where(year == 2022, 'calibration', 'validation'))
    texts = {day: srs_text(day, regions) for day, regions in sorted(texts.items())}
    return table, texts, mapping


def population(development, context, years):
    out = {}
    for year in years:
        split, _ = annual_fold(runner.blind(development[runner.META], year), year)
        out[str(year)] = runner.fold_population(split, {role: context.loc[group.index] for role, group in split.items()})
    return out


def stored_thresholds(year):
    return {'watch': {'threshold': 0.2}, 'comparison_recall_0.95': {'threshold': 0.1},
            'alert': {'threshold': 0.6, 'calibration_recall': 0.5, 'calibration_precision': 0.4, 'fallback': year == 2022}}


def stub_fit(calls):
    def fit(base, groups, contexts, columns):
        calls.append(dict(columns=list(columns), evaluation_columns=set(groups['evaluation'].columns),
                          aligned=all(contexts[role].index.equals(groups[role].index) for role in groups)))
        scale = 1+len(columns)/100
        score = {role: groups[role][FEATURE_COLUMNS[0]].to_numpy(dtype=float) for role in ['calibration', 'evaluation']}
        return 1/(1+np.exp(-scale*score['calibration'])), 1/(1+np.exp(-scale*score['evaluation']))
    return fit


@pytest.fixture(scope='module')
def world():
    return synthetic_world()


@pytest.fixture(scope='module')
def context(world):
    table, texts, mapping = world
    issued, rows, mapped = sources_from(texts, mapping)
    return runner.context_features(table[KEY], mapped, issued, rows)


@pytest.fixture(scope='module')
def phase_inputs(world, context):
    table = world[0][[*runner.META, *FEATURE_COLUMNS]]
    config = {'years': YEARS, 'budget': {'constituent_fits': 16}, 'population': population(table, context, YEARS)}
    pipeline = json.loads((ROOT/'config/walk-forward-v2.json').read_text())
    folds = {year: annual_fold(table[runner.META], year)[1] for year in YEARS}
    return config, pipeline, table, context, folds, {year: stored_thresholds(year) for year in YEARS}


def phase(inputs, table=None, config=None, fit=None):
    base_config, pipeline, base_table, context, folds, thresholds = inputs
    return runner.fit_phase(config or base_config, {}, pipeline, base_table if table is None else table, context, folds, thresholds,
                            fit=fit or stub_fit([]))


def test_orbital_features_depend_only_on_the_utc_time_of_day():
    frame = keys(1, ['2015-03-01 00:00', '2015-03-01 06:00', '2015-03-01 12:00', '2015-03-01 18:00', '2015-03-02 03:30'])
    orbit = orbital_phase_features(frame)
    assert list(orbit.columns) == ORBITAL and not orbit.isna().any().any()
    assert np.allclose(orbit['orbit__sin_24h'], [0, 1, 0, -1, np.sin(2*np.pi*3.5/24)])
    assert np.allclose(orbit['orbit__cos_12h'], [1, -1, 1, -1, np.cos(2*np.pi*3.5/12)])
    assert np.allclose(utc_hour(frame.forecast_time), [0, 6, 12, 18, 3.5])
    # Whole days later, in another year or season, the features are identical: no calendar information.
    for days in [1, 37, 365, 3000]:
        shifted = frame.assign(forecast_time=frame.forecast_time+pd.Timedelta(days=days))
        assert np.allclose(orbital_phase_features(shifted).to_numpy(), orbit.to_numpy())
    assert not np.allclose(orbital_phase_features(frame.assign(forecast_time=frame.forecast_time+HOUR)).to_numpy(), orbit.to_numpy())


@pytest.mark.parametrize('column', ['target', 'label_status', 'label_status_v2', 'role'])
def test_features_refuse_labels_label_status_and_roles(column):
    frame = keys(1, ['2015-03-01 00:00', '2015-03-01 01:00']).assign(**{column: 0})
    issued, rows, mapping = one_region_sources()
    with pytest.raises(ValueError, match='never see labels'):
        orbital_phase_features(frame)
    with pytest.raises(ValueError, match='never see labels'):
        disk_position_features(frame, mapping, issued, srs_positions(issued, rows))
    with pytest.raises(ValueError):
        orbital_phase_features(pd.concat([frame.drop(columns=column)]*2))


def test_locations_parse_with_west_and_north_positive():
    assert parse_location('N12W50') == (12, 50) and parse_location('S07E33') == (-7, -33) and parse_location('N00W00') == (0, 0)
    for bad in ['N12X50', 'N1W50', 'Q12W50', None, 'N12W5A']:
        with pytest.raises(ValueError):
            parse_location(bad)


def test_latest_issue_equals_the_availability_rule_of_region_context():
    issued = pd.Series([ts('2015-03-01 00:30'), ts('2015-03-02 00:30'), ts('2015-03-03 01:10')])
    times = pd.Series([ts('2015-03-01 00:59'), ts('2015-03-01 01:00'), ts('2015-03-02 12:00'), ts('2015-03-03 01:39'), ts('2015-03-03 01:40')])
    ours, theirs = latest_issue(issued, times), available_srs(issued, times)
    assert ours.equals(theirs)
    assert ours.isna().iloc[0] and ours.iloc[1] == issued[0] and ours.iloc[3] == issued[1] and ours.iloc[4] == issued[2]


def one_region_sources(longitude=-40, latitude=15, harp=7, noaa=12345):
    day = pd.Timestamp('2015-03-01')
    texts = {day: srs_text(day, [(noaa, latitude, longitude, 120), (noaa+1, -30, 10, 40)]),
             day+pd.Timedelta(days=1): srs_text(day+pd.Timedelta(days=1), [(noaa, latitude, longitude+20, 120)])}
    mapping = [(harp, day.date(), noaa), (harp, (day+pd.Timedelta(days=1)).date(), noaa)]
    return sources_from(texts, mapping)


def test_disk_position_follows_the_frozen_definitions():
    issued, rows, mapping = one_region_sources()
    positions = srs_positions(issued, rows)
    assert positions.valid_utc.eq(positions.issued_utc.dt.floor('D')).all()
    frame = keys(7, ['2015-03-01 00:45', '2015-03-01 01:00', '2015-03-01 12:00', '2015-03-02 06:00'])
    disk = disk_position_features(frame, mapping, issued, positions)
    assert list(disk.columns) == [*POSITION, BAND, SIDE]
    # 00:45 is before the first issue time plus 30 minutes: no SRS is available yet.
    assert disk[FLAG].tolist() == [0, 1, 1, 1] and disk.loc[0, POSITION[1:]].isna().all()
    # E40 at 00:00, rotated 13.2 degrees per day: one hour later -39.45, at noon -33.4; the next day's product says E20.
    expected = np.array([np.nan, 40-13.2/24, 40-13.2/2, 20-13.2/4])
    assert np.allclose(disk['disk__abs_cmd_deg'], expected, equal_nan=True)
    assert np.allclose(disk['disk__abs_latitude_deg'], [np.nan, 15, 15, 15], equal_nan=True)
    cosine = np.cos(np.radians(15))*np.cos(np.radians(expected))
    assert np.allclose(disk['disk__cos_heliocentric_angle'], cosine, equal_nan=True)
    assert disk[BAND].tolist() == ['no_srs_location', 'cmd_30_60', 'cmd_30_60', 'cmd_0_30']
    assert disk[SIDE].tolist() == ['no_srs_location', 'east', 'east', 'east']


def test_disk_position_uses_the_largest_matched_region_clips_at_the_limb_and_needs_the_harps_noaa_number():
    issued, rows, mapping = one_region_sources(longitude=85, latitude=-20)
    mapping = pd.concat([mapping, pd.DataFrame([(7, pd.Timestamp('2015-03-01').date(), 12346)], columns=mapping.columns)])
    disk = disk_position_features(keys(7, ['2015-03-01 23:00']), mapping, issued, srs_positions(issued, rows))
    # Area 120 beats area 40; W85 plus most of a day passes the limb and is clipped at 90.
    assert disk.loc[0, 'disk__abs_cmd_deg'] == 90 and disk.loc[0, 'disk__abs_latitude_deg'] == 20
    assert np.isclose(disk.loc[0, 'disk__cos_heliocentric_angle'], 0) and disk.loc[0, BAND] == 'cmd_over_60' and disk.loc[0, SIDE] == 'west'
    # Another HARP, or a date without a NOAA number in the mapping, is never located.
    other = disk_position_features(keys(8, ['2015-03-01 12:00']), mapping, issued, srs_positions(issued, rows))
    late = disk_position_features(keys(7, ['2015-03-05 12:00']), mapping, issued, srs_positions(issued, rows))
    assert other[FLAG].tolist() == [0] == late[FLAG].tolist() and other[POSITION[1:]].isna().all().all()
    assert list(disk_band([0, 30, 30.01, 60, 60.5, np.nan])) == ['cmd_0_30', 'cmd_0_30', 'cmd_30_60', 'cmd_30_60', 'cmd_over_60', 'no_srs_location']


def test_disk_position_never_uses_a_later_srs():
    issued, rows, mapping = one_region_sources()
    frame = keys(7, ['2015-03-01 12:00', '2015-03-02 00:59', '2015-03-02 01:00'])
    full = disk_position_features(frame, mapping, issued, srs_positions(issued, rows))
    # Changing or removing the second product leaves every window before its issue time plus 30 minutes as it was.
    second = issued.issued_utc.max()
    kept = rows.issued_utc.lt(second)
    cut = disk_position_features(frame, mapping, issued[issued.issued_utc.lt(second)], srs_positions(issued[issued.issued_utc.lt(second)], rows[kept]))
    assert cut.iloc[:2].equals(full.iloc[:2]) and not cut.iloc[2].equals(full.iloc[2])
    changed = rows.copy()
    changed.loc[~kept, 'location'] = 'S40W80'
    assert disk_position_features(frame, mapping, issued, srs_positions(issued, changed)).iloc[:2].equals(full.iloc[:2])


def test_context_over_the_world_has_no_calendar_column_and_rows_keep_their_order(world, context):
    table = world[0]
    assert list(context.columns) == [*ORBITAL, *POSITION, BAND, SIDE] and context.index.equals(table.index)
    located = context[FLAG].eq(1)
    assert 0 < located.mean() < 1 and context.loc[~located, POSITION[1:]].isna().all().all() and context.loc[located, POSITION[1:]].notna().all().all()
    assert not any(word in column for column in context.columns for word in runner.CALENDAR_WORDS)
    shuffled = table.sample(frac=1, random_state=3)
    issued, rows, mapping = sources_from(world[1], world[2])
    assert runner.context_features(shuffled[KEY], mapping, issued, rows).loc[table.index].equals(context)


def test_phase_one_is_identical_whatever_the_evaluation_labels_are(phase_inputs):
    config, _, table, _, _, _ = phase_inputs
    single = dict(config, years=[2023], budget={'constituent_fits': 8})
    flipped = table.assign(target=table.target.where(table.forecast_time.dt.year < 2023, 1-table.target))
    first, second = phase(phase_inputs, config=single), phase(phase_inputs, table=flipped, config=single)
    assert json.dumps(first[0], sort_keys=True) == json.dumps(second[0], sort_keys=True)
    assert first[1][2023].equals(second[1][2023]) and first[2] == second[2]
    assert list(first[1][2023].columns) == ['harp', 'forecast_time', *runner.CANDIDATES, BAND, SIDE]


def test_phase_one_gives_each_candidate_its_frozen_columns_and_no_evaluation_label(phase_inputs):
    calls = []
    thresholds, probabilities, coverage, fits = phase(phase_inputs, fit=stub_fit(calls))
    assert fits == 16 and [c['columns'] for c in calls] == [[FLAG], ORBITAL, POSITION, [*ORBITAL, *POSITION]]*2
    assert all(c['aligned'] and not {'target', 'label_status'} & c['evaluation_columns'] for c in calls)
    assert not any({BAND, SIDE} & set(c['columns']) for c in calls)
    assert all(thresholds[str(year)]['control'] == stored_thresholds(year) for year in YEARS)
    assert {(row['year'], row['role']) for row in coverage} == set(itertools.product(YEARS, ['train', 'calibration', 'evaluation']))
    row = next(r for r in coverage if r['year'] == 2023 and r['role'] == 'evaluation')
    assert row['srs_located'] == row['rows']-row['missing__disk__abs_cmd_deg'] > 0 and row['missing__orbit__sin_24h'] == 0
    assert row['band__no_srs_location'] == row['rows']-row['srs_located']


def test_phase_one_stops_on_budget_population_or_fold_changes(phase_inputs):
    config, pipeline, table, context, folds, thresholds = phase_inputs
    with pytest.raises(RuntimeError):
        phase(phase_inputs, config=dict(config, budget={'constituent_fits': 14}))
    with pytest.raises(RuntimeError):
        phase(phase_inputs, config=dict(config, budget={'constituent_fits': 18}))
    for key in runner.POPULATION:
        changed = copy.deepcopy(config)
        changed['population']['2022'][key] += 1
        with pytest.raises(ValueError):
            phase(phase_inputs, config=changed)
    other = copy.deepcopy(folds)
    other[2022][0]['rows'] += 1
    with pytest.raises(ValueError):
        runner.fit_phase(config, {}, pipeline, table, context, other, thresholds, fit=stub_fit([]))


def test_default_fit_is_the_unchanged_recipe_function():
    assert runner.fit_probabilities is fit_probabilities
    assert runner.run.__defaults__ == (fit_probabilities,) and runner.fit_phase.__defaults__ == (fit_probabilities,)
    assert runner.CONSTITUENTS == 2


def test_every_result_falls_into_exactly_one_reading():
    keys_ = ['all_year_primary', 'cycle25_primary', 'cycle25_bootstrap_lower_above_zero']
    seen = set()
    for flag, orbital, disk, both in itertools.product(itertools.product([False, True], repeat=3), repeat=4):
        parts = {'srs_flag': dict(zip(keys_, flag)), 'orbital_phase': dict(zip(keys_, orbital))}
        if any(p['all_year_primary'] and not p['cycle25_primary'] for p in [*parts.values(), dict(zip(keys_, disk)), dict(zip(keys_, both))]):
            continue
        for beats_d, beats_b in itertools.product([(False, False), (False, True), (True, True)], repeat=2):
            summary = dict(parts, disk_position=dict(zip(keys_, disk), beats_srs_flag_all_years=beats_d[0], beats_srs_flag_cycle25=beats_d[1]),
                           both=dict(zip(keys_, both), beats_srs_flag_all_years=beats_b[0], beats_srs_flag_cycle25=beats_b[1]))
            decision = runner.read(summary)
            effects = [runner.meets_goal(summary['orbital_phase'])]
            for name in runner.POSITION_CANDIDATES:
                p = summary[name]
                effects.append((p['all_year_primary'] and p['beats_srs_flag_all_years'])
                               or (p['cycle25_primary'] and p['cycle25_bootstrap_lower_above_zero'] and p['beats_srs_flag_cycle25']))
            goal = [c for c in runner.CANDIDATES if runner.meets_goal(summary[c])]
            expected = 'S1_systematics_help' if any(effects) else 'S2_refit_or_flag_only' if goal else 'S3_no_gain'
            assert decision['reading'] == expected and decision['systematics_effects_met'] == sum(effects)
            assert decision['candidates_meeting_goal_against_control'] == goal
            assert decision['outcome_label'] == runner.LABELS[expected]
            seen.add(expected)
    assert seen == set(runner.READINGS)
    passing, failing = dict(zip(keys_, [False, True, True])), dict(zip(keys_, [False, True, False]))
    beats, loses = dict(beats_srs_flag_all_years=False, beats_srs_flag_cycle25=True), dict(beats_srs_flag_all_years=False, beats_srs_flag_cycle25=False)
    # A position gain that the flag-only refit shares is not a systematics effect.
    shared = {'srs_flag': passing, 'orbital_phase': failing, 'disk_position': {**passing, **loses}, 'both': {**failing, **loses}}
    assert runner.read(shared)['outcome_label'] == 'result:partial'
    assert runner.read({**shared, 'disk_position': {**passing, **beats}})['effects_met'] == ['disk_position']
    assert runner.read({**shared, 'srs_flag': failing, 'disk_position': {**failing, **beats}})['outcome_label'] == 'result:no-gain'
    assert runner.read({**shared, 'orbital_phase': passing})['effects_met'] == ['orbital_phase']


def test_periodicity_measures_within_harp_harmonics_without_labels():
    times = [ts('2015-03-01')+h*HOUR for h in range(96)]
    frame = pd.DataFrame({'harp': np.repeat([1, 2], 96), 'forecast_time': times*2})
    hour = utc_hour(frame.forecast_time)
    level = np.where(frame.harp.eq(1), -3.0, 1.0)
    frame['pure_24h'] = 1/(1+np.exp(-(level+0.5*np.sin(2*np.pi*hour/24))))
    frame['pure_12h'] = 1/(1+np.exp(-(level+0.5*np.cos(2*np.pi*hour/12))))
    frame['flat'] = 1/(1+np.exp(-level))
    a, b = runner.periodicity(frame, 'pure_24h', 2015, 'a'), runner.periodicity(frame, 'pure_12h', 2015, 'b')
    assert np.isclose(a['within_harp_share_24h'], 1) and np.isclose(a['within_harp_share_12h'], 0, atol=1e-9)
    assert np.isclose(b['within_harp_share_12h'], 1) and np.isclose(b['within_harp_share_24h_and_12h'], 1)
    assert 0 < a['within_harp_share_of_total_variance'] < 0.1 and a['harps'] == 2 and a['windows'] == 192
    flat = runner.periodicity(frame, 'flat', 2015, 'c')
    assert flat['within_harp_share_24h'] is None and np.isclose(flat['within_harp_share_of_total_variance'], 0)


def test_group_counts_cover_every_group():
    frame = pd.DataFrame({'target': [1, 1, 0, 0, 1, 0], BAND: ['cmd_0_30', 'cmd_0_30', 'cmd_0_30', 'cmd_over_60', 'no_srs_location', 'no_srs_location']})
    rows = runner.group_counts(frame, np.array([True, False, True, True, False, False]), 2023, 'control', BAND, runner.BANDS)
    by = {r['group']: r for r in rows}
    assert [r['group'] for r in rows] == runner.BANDS and by['cmd_30_60']['windows'] == 0 and by['cmd_30_60']['precision'] is None
    assert (by['cmd_0_30']['tp'], by['cmd_0_30']['fp'], by['cmd_0_30']['fn']) == (1, 1, 1) and by['cmd_over_60']['precision'] == 0
    assert by['no_srs_location']['recall'] == 0 and sum(r['windows'] for r in rows) == 6


def test_frozen_protocol_matches_the_idea_and_the_adopted_basis():
    text = CONFIG.read_text()
    config = json.loads(text)
    v2 = json.loads((ROOT/'config/activity-history-v2.json').read_text())
    runner.check_protocol(config)
    assert config['id'] == 'orbital-disk-v1' and config['status'] == 'frozen_before_any_candidate_result'
    assert config['reserved_test_accessed'] is False and not {chr(0x2013), chr(0x2014)} & set(text)
    assert config['years'] == v2['years'] == [2014, 2015, 2016, 2017, 2022, 2023] and config['alert_fallback_years'] == [2022]
    assert [c['id'] for c in config['candidates']] == ['srs_flag', 'orbital_phase', 'disk_position', 'both'] and config['control']['id'] == 'control'
    added = config['features']['added']
    assert added['srs_flag'] == [FLAG] and added['orbital_phase'] == ORBITAL and added['disk_position'] == POSITION
    assert added['both'] == [*ORBITAL, *POSITION] and config['budget']['added_features'] == {k: len(v) for k, v in added.items()}
    assert config['budget']['constituent_fits'] == 48 and config['budget']['hyperparameter_search'] == 0 and config['budget']['downloads'] == 0
    assert config['features']['disk']['availability_safety_minutes'] == 30
    assert '<= t - 30 minutes' in json.loads((ROOT/'config/region-context-v1.json').read_text())['availability_rule']
    evidence = config['evidence']
    assert evidence['table'] == 'artifacts/relabelled_development_20261111_r1' and evidence['control'] == 'artifacts/walk_forward_v2_20261112_r1'
    # The table, the stored control and the two source directories of the issue are the only evidence directories named.
    assert set(re.findall(r'(?:artifacts|data)/[A-Za-z0-9_]+', text)) == {
        evidence['table'], evidence['control'], evidence['srs_directory'], evidence['mapping_directory']}
    assert evidence['srs_directory'] == 'data/region_summaries_20261109_r1' and evidence['mapping_directory'] == 'data/harp_noaa_mapping_20261109_r1'
    assert evidence['table_report_sha256'] == v2['evidence']['table_report_sha256']
    assert evidence['control_report_sha256'] == v2['evidence']['control_report_sha256']
    for key in ['pipeline_protocol', 'base_protocol', 'availability_protocol']:
        assert sha256(ROOT/evidence[key]) == evidence[f'{key}_sha256']
    assert config['acceptance']['per_year_primary'] == v2['acceptance']['per_year_primary']
    assert set(config['acceptance']['effects']) == {'orbital_phase', *runner.POSITION_CANDIDATES}
    assert set(config['reading']) == {*runner.READINGS, 'exclusive'}
    assert all(runner.LABELS[name] in config['reading'][name] for name in runner.READINGS)
    assert config['acceptance_rule'] == {**config['acceptance_rule'], 'metric_path': 'decision.systematics_effects_met', 'op': '>=', 'value': 1}
    assert config['descriptive']['feeds_rule'] is False and config['descriptive']['fits'] == 0
    assert set(config['population'])-{'source', 'coverage_counts'} == {str(year) for year in config['years']}
    for year in config['years']:
        counts = config['population'][str(year)]
        assert set(counts) == set(runner.POPULATION)
        assert 0 < counts['train_positives'] < counts['train_rows'] and 0 < counts['calibration_positives'] < counts['calibration_rows']
        for role in ['train', 'calibration', 'evaluation']:
            assert 0 < counts[f'{role}_srs_located'] < counts[f'{role}_rows']
        assert counts['train_positives_srs_located'] <= counts['train_positives']
    assert {'question', 'finding', 'decision', 'residual_risk'} == set(config['leak_question'])


@pytest.mark.parametrize('change', [
    lambda c: c['candidates'].append({'id': 'calendar'}),
    lambda c: c['candidates'].reverse(),
    lambda c: c['features']['added']['orbital_phase'].append('orbit__day_of_year'),
    lambda c: c['features']['added']['both'].append('disk__forecast_month'),
    lambda c: c['features']['added']['disk_position'].append(BAND),
    lambda c: c['features']['added']['srs_flag'].append(SIDE),
    lambda c: c['features']['added']['disk_position'].pop(),
    lambda c: c['features']['added'].update(extra=ORBITAL),
    lambda c: c['features']['reporting_only'].update(model_input=True),
    lambda c: c['features']['orbital'].update(periods_hours=[24, 12, 8]),
    lambda c: c['features']['disk'].update(rotation_deg_per_day=14.0),
    lambda c: c['features']['disk'].update(availability_safety_minutes=0),
    lambda c: c['features']['disk']['bands'].pop(),
    lambda c: c['descriptive'].update(feeds_rule=True),
    lambda c: c['years'].append(2024),
    lambda c: c['years'].remove(2022),
    lambda c: c['budget'].update(constituent_fits=36),
    lambda c: c.update(reserved_test_accessed=True),
    lambda c: c.update(status='design_proposed'),
    lambda c: c.update(alert_fallback_years=[2021]),
])
def test_runner_refuses_a_changed_protocol(change):
    config = json.loads(CONFIG.read_text())
    change(config)
    with pytest.raises(ValueError):
        runner.check_protocol(config)


def write_sources(directory, texts, mapping, extra_srs=None):
    """SRS and mapping directories with manifests in the layout of the fetch scripts."""
    srs_dir, map_dir = directory/'srs', directory/'mapping'
    srs_dir.mkdir(parents=True)
    map_dir.mkdir(parents=True)
    records = [{'date': '2017-12-31', 'file': '20171231SRS.txt', 'status': 'missing'}]
    for day, text in {**texts, **(extra_srs or {})}.items():
        path = srs_dir/f'{day:%Y%m%d}SRS.txt'
        path.write_text(text)
        records.append({'date': f'{day:%Y-%m-%d}', 'file': path.name, 'status': 'ok', 'sha256': sha256(path)})
    (srs_dir/'manifest.json').write_text(json.dumps({'period': ['2018-01-01', max(r['date'] for r in records)], 'records': records}))
    frame = pd.DataFrame(mapping, columns=['harp', 'date', 'noaa'])
    frame['month'] = [f'{d:%Y-%m}' for d in frame.date]
    records = []
    for month, part in frame.groupby('month'):
        payload = {'keywords': [{'name': 'HARPNUM', 'values': [str(h) for h in part.harp]},
                                {'name': 'T_REC', 'values': [f'{d:%Y.%m.%d}_00:00:00_TAI' for d in part.date]},
                                {'name': 'NOAA_ARS', 'values': [str(n) for n in part.noaa]}]}
        path = map_dir/f'{month.replace("-", "")}.json'
        path.write_text(json.dumps(payload))
        records.append({'month': month, 'file': path.name, 'status': 'ok', 'sha256': sha256(path)})
    (map_dir/'manifest.json').write_text(json.dumps({'period': ['2018-01-01', '2023-12-31'], 'records': records, 'http_fallback_months': []}))
    return srs_dir, map_dir


def write_inputs(directory, world):
    """A materialized table, a stored control, two source directories and a protocol copy that point at synthetic files only."""
    development, texts, mapping = world
    table_dir, control_dir = directory/'table', directory/'control'
    (table_dir/'shards').mkdir(parents=True)
    shard = table_dir/'shards/part-0.parquet'
    development[[*METADATA, *FEATURE_COLUMNS]].to_parquet(shard, index=False)
    roles = development.groupby('role').target
    (table_dir/'report.json').write_text(json.dumps({
        'shards': [{'file': shard.name, 'bytes': shard.stat().st_size, 'sha256': sha256(shard)}],
        'rows': {k: int(v) for k, v in roles.size().items()}, 'positives': {k: int(v) for k, v in roles.sum().items()}}))
    meta = development[runner.META]
    folds, hashes = [], {}
    for year in YEARS:
        split, audit = annual_fold(meta, year)
        (control_dir/str(year)).mkdir(parents=True)
        evaluation = split['evaluation']
        score = development.loc[evaluation.index, FEATURE_COLUMNS[0]].to_numpy(dtype=float)
        evaluation[['harp', 'forecast_time', 'target']].assign(ensemble=1/(1+np.exp(-score))).to_parquet(
            control_dir/str(year)/'predictions.parquet', index=False)
        (control_dir/str(year)/'thresholds.json').write_text(json.dumps(stored_thresholds(year)))
        folds.append({'year': year, 'audit': audit, 'status': 'complete'})
        hashes.update({f'{year}/{name}': sha256(control_dir/str(year)/name) for name in ['predictions.parquet', 'thresholds.json']})
    (control_dir/'report.json').write_text(json.dumps({'folds': folds, 'artifact_hashes': hashes}))
    srs_dir, map_dir = write_sources(directory, texts, mapping)
    base = json.loads((ROOT/'config/walk-forward-v1.json').read_text())
    base['candidates']['xgboost']['n_estimators'] = 8
    (directory/'base.json').write_text(json.dumps(base))
    ordered = pd.concat([development[development.role.eq(role)].sort_values(['forecast_time', 'harp'])
                         for role in ['train', 'calibration', 'validation']], ignore_index=True)
    issued, rows, mapped = sources_from(texts, mapping)
    config = json.loads(CONFIG.read_text())
    config.update(years=YEARS, population=population(ordered, runner.context_features(ordered[KEY], mapped, issued, rows), YEARS))
    config['budget']['constituent_fits'] = 16
    config['sources']['counts'] = dict(srs_products=len(texts), srs_rows=len(rows), srs_problems={'unavailable': 1}, mapping_problems={})
    config['evidence'].update(table=str(table_dir), table_report_sha256=sha256(table_dir/'report.json'), control=str(control_dir),
                              control_report_sha256=sha256(control_dir/'report.json'), base_protocol=str(directory/'base.json'),
                              base_protocol_sha256=sha256(directory/'base.json'), srs_directory=str(srs_dir),
                              srs_manifest_sha256=sha256(srs_dir/'manifest.json'), mapping_directory=str(map_dir),
                              mapping_manifest_sha256=sha256(map_dir/'manifest.json'),
                              pipeline_protocol=str(ROOT/'config/walk-forward-v2.json'),
                              availability_protocol=str(ROOT/'config/region-context-v1.json'))
    (directory/'config.json').write_text(json.dumps(config))
    return directory/'config.json'


@pytest.fixture(scope='module')
def executed(tmp_path_factory, world):
    directory = tmp_path_factory.mktemp('orbital_disk')
    config_path = write_inputs(directory, world)
    result, table = runner.run(config_path, directory/'output')
    return directory, config_path, result, table


def test_run_on_synthetic_inputs_freezes_phase_one_before_labels(executed):
    directory, config_path, result, table = executed
    output = directory/'output'
    phase1 = json.loads((output/'phase1.json').read_text())
    assert set(phase1) == {'thresholds.json', 'features.json', 'disk_coverage.csv', 'probabilities_2022.parquet', 'probabilities_2023.parquet'}
    assert all(sha256(output/name) == value for name, value in phase1.items())
    assert result['phase1_sha256'] == sha256(output/'phase1.json') and result['thresholds_sha256'] == phase1['thresholds.json']
    assert result['config_sha256'] == sha256(config_path) and result['constituent_fits'] == 16
    assert result['feature_counts'] == {'srs_flag': 97, 'orbital_phase': 100, 'disk_position': 100, 'both': 104}
    written = json.loads((output/'features.json').read_text())
    assert written == {name: [*FEATURE_COLUMNS, *columns] for name, columns in runner.CANDIDATES.items()}
    for year in YEARS:
        frame = pd.read_parquet(output/f'probabilities_{year}.parquet')
        assert list(frame.columns) == ['harp', 'forecast_time', *runner.CANDIDATES, BAND, SIDE] and 'target' not in frame
    thresholds = json.loads((output/'thresholds.json').read_text())
    assert all(set(thresholds[str(year)]) == {'control', *runner.CANDIDATES} for year in YEARS)
    assert all(thresholds[str(year)]['control'] == stored_thresholds(year) for year in YEARS)
    assert result['reserved_test_accessed'] is False and result['model_promoted'] is False and result['threshold_adopted'] is False
    assert result['descriptive_feeds_rule'] is False and result['alert_fallback_years_control'] == [2022]
    assert result['artifact_hashes'].keys() >= {'results.csv', 'intervals.csv', 'by_hour.csv', 'by_disk.csv', 'logit_periodicity.csv', 'phase1.json'}


def test_run_reports_every_candidate_the_descriptive_part_and_one_reading(executed):
    directory, _, result, table = executed
    names = ['control', *runner.CANDIDATES]
    assert set(zip(table.year, table.candidate, table.tier)) == set(itertools.product(YEARS, names, ['watch', 'alert']))
    alert = table[table.tier.eq('alert')].set_index(['year', 'candidate'])
    assert bool(alert.loc[(2022, 'control'), 'fallback']) and alert.loc[(2022, 'control'), 'threshold'] == 0.6
    assert alert.missed_positive_runs.notna().all() and alert.loc[(2023, 'disk_position'), 'beats_srs_flag'] in (True, False)
    decision = result['decision']
    assert result['reading'] == decision['reading'] and decision['reading'] in runner.READINGS
    assert decision['systematics_effects_met'] == len(decision['effects_met'])
    assert set(result['acceptance']) == set(names)
    assert {'beats_srs_flag_all_years', 'beats_srs_flag_cycle25'} <= set(result['acceptance']['disk_position']) & set(result['acceptance']['both'])
    output = directory/'output'
    hours = pd.read_csv(output/'by_hour.csv')
    assert set(zip(hours.year, hours.candidate, hours.group)) == set(itertools.product(YEARS, names, range(24)))
    disk = pd.read_csv(output/'by_disk.csv')
    assert set(disk.group) == {*runner.BANDS, *runner.SIDES} and set(disk.grouping) == {BAND, SIDE}
    for (year, name, grouping), part in disk.groupby(['year', 'candidate', 'grouping']):
        assert part.windows.sum() == hours[(hours.year == year) & (hours.candidate == name)].windows.sum()
    periodic = pd.read_csv(output/'logit_periodicity.csv')
    assert set(zip(periodic.year, periodic.candidate)) == set(itertools.product(YEARS, names))
    assert periodic[['within_harp_share_24h', 'within_harp_share_12h']].stack().between(-1e-9, 1+1e-9).all()
    intervals = pd.read_csv(output/'intervals.csv')
    assert set(zip(intervals.candidate, intervals.reference)) == {*((c, 'control') for c in runner.CANDIDATES),
                                                                   ('disk_position', 'srs_flag'), ('both', 'srs_flag')}


def test_run_refuses_an_existing_output_and_changed_inputs(executed, tmp_path):
    directory, config_path, _, _ = executed
    before = {p.name: sha256(p) for p in (directory/'output').iterdir()}
    with pytest.raises(FileExistsError):
        runner.run(config_path, directory/'output')
    assert before == {p.name: sha256(p) for p in (directory/'output').iterdir()}
    config = json.loads(config_path.read_text())

    def refused(change, name):
        changed = copy.deepcopy(config)
        change(changed)
        path = tmp_path/f'{name}.json'
        path.write_text(json.dumps(changed))
        with pytest.raises(ValueError):
            runner.run(path, tmp_path/f'{name}_output')
        assert not (tmp_path/f'{name}_output').exists()

    refused(lambda c: c['evidence'].update(control_report_sha256='0'*64), 'control_hash')
    refused(lambda c: c['evidence'].update(table_report_sha256='0'*64), 'table_hash')
    refused(lambda c: c['evidence'].update(base_protocol_sha256='0'*64), 'recipes_hash')
    refused(lambda c: c['evidence'].update(pipeline_protocol_sha256='0'*64), 'pipeline_hash')
    refused(lambda c: c['evidence'].update(availability_protocol_sha256='0'*64), 'availability_hash')
    refused(lambda c: c['evidence'].update(srs_manifest_sha256='0'*64), 'srs_hash')
    refused(lambda c: c['evidence'].update(mapping_manifest_sha256='0'*64), 'mapping_hash')
    refused(lambda c: c['sources']['counts'].update(srs_rows=c['sources']['counts']['srs_rows']+1), 'source_counts')
    refused(lambda c: c.update(alert_fallback_years=[2023]), 'fallback')
    refused(lambda c: c['years'].append(2024), 'reserved')
    refused(lambda c: c['features']['added']['orbital_phase'].append('orbit__day_of_year'), 'calendar')


def test_run_refuses_a_source_that_reaches_the_reserved_period(tmp_path, world):
    config_path = write_inputs(tmp_path, world)
    config = json.loads(config_path.read_text())
    day = pd.Timestamp('2024-01-02')
    # A product of the reserved period in the manifest is refused before any SRS file is opened, even an unreadable one.
    srs_dir, _ = write_sources(tmp_path/'reserved', world[1], world[2], extra_srs={day: srs_text(day, [])})
    (srs_dir/'20240102SRS.txt').write_bytes(b'\xff')
    config['evidence'].update(srs_directory=str(srs_dir), srs_manifest_sha256=sha256(srs_dir/'manifest.json'))
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='reserved period'):
        runner.run(config_path, tmp_path/'reserved_output', fit=stub_fit([]))
    assert not (tmp_path/'reserved_output').exists()


def test_run_refuses_changed_control_labels(tmp_path, world):
    config_path = write_inputs(tmp_path, world)
    predictions = tmp_path/'control/2023/predictions.parquet'
    frame = pd.read_parquet(predictions)
    frame['target'] = 1-frame.target
    frame.to_parquet(predictions, index=False)
    report_path = tmp_path/'control/report.json'
    report = json.loads(report_path.read_text())
    report['artifact_hashes']['2023/predictions.parquet'] = sha256(predictions)
    report_path.write_text(json.dumps(report))
    config = json.loads(config_path.read_text())
    config['evidence']['control_report_sha256'] = sha256(report_path)
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='Stored control labels differ'):
        runner.run(config_path, tmp_path/'changed_labels', fit=stub_fit([]))
