"""Synthetic tests of config/srs-evolution-v1.json and its runner; no project data or evidence is read."""
import copy
import itertools
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import scripts.audit_srs_evolution as runner
from helio24.data import FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.v2_training import METADATA
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history_relabelled import fit_probabilities
from scripts.audit_region_context_features import CONTEXT, attach_context, srs_feature_table
from scripts.audit_srs_evolution import AVAILABLE, EVOLUTION, KEY, LISTED, attach_evolution, earlier_srs

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'config/srs-evolution-v1.json'
YEARS = [2022, 2023]
HOUR = pd.Timedelta(hours=1)
DAY = pd.Timedelta(days=1)
CHANGES = EVOLUTION[1:]
CLASSES = ['Axx', 'Bxo', 'Cso', 'Dai', 'Eki', 'Fkc', 'Eki', 'Dai', 'Cso', 'Bxo', 'Axx']
MAGNETIC = ['Alpha', 'Beta', 'Beta', 'Beta-Gamma', 'Beta-Gamma-Delta', 'Beta-Gamma-Delta', 'Beta-Delta', 'Beta-Gamma', 'Beta', 'Beta', 'Alpha']


def at(text):
    return pd.Timestamp(text, tz='UTC')


def small_sources():
    """Four products (03 Sep has two regions, 04 Sep is absent) and four HARPs: two numbers, one, an unlisted one, none."""
    rows = pd.DataFrame([
        dict(issued_utc=at('2023-09-01 00:30'), noaa=13413, area=100, z='Cso', ll=5, nn=5, mag_type='Beta'),
        dict(issued_utc=at('2023-09-02 00:30'), noaa=13413, area=150, z='Dko', ll=8, nn=9, mag_type='Beta-Gamma'),
        dict(issued_utc=at('2023-09-02 00:30'), noaa=13417, area=80, z='Hsx', ll=2, nn=1, mag_type='Alpha'),
        dict(issued_utc=at('2023-09-03 00:30'), noaa=13413, area=120, z='Eki', ll=9, nn=12, mag_type='Beta-Gamma-Delta'),
        dict(issued_utc=at('2023-09-03 00:30'), noaa=13417, area=60, z='Hax', ll=2, nn=2, mag_type='Alpha'),
        dict(issued_utc=at('2023-09-05 00:30'), noaa=13413, area=90, z='Dko', ll=7, nn=6, mag_type='Beta'),
    ])
    issued = pd.DataFrame({'issued_utc': sorted(rows.issued_utc.unique())})
    dates = [pd.Timestamp(f'2023-09-0{d}').date() for d in range(1, 6)]
    mapping = pd.DataFrame([dict(harp=harp, date=date, noaa=noaa) for date in dates
                            for harp, noaa in [(1, 13413), (1, 13417), (2, 13417), (3, 99999)]])
    return issued, srs_feature_table(rows), mapping


def windows(pairs):
    return pd.DataFrame({'harp': [harp for harp, _ in pairs], 'forecast_time': [at(time) for _, time in pairs]})


def test_earlier_product_is_the_one_issued_12_to_36_hours_before_and_nothing_older():
    issued = pd.Series([at('2023-09-01 00:30'), at('2023-09-02 00:50'), at('2023-09-03 00:30'), at('2023-09-05 00:30'), at('2023-09-05 06:30')])
    used = pd.Series([at('2023-09-01 00:30'), at('2023-09-02 00:50'), at('2023-09-03 00:30'), at('2023-09-05 00:30'), at('2023-09-05 06:30'), pd.NaT])
    earlier = earlier_srs(issued, used)
    assert earlier.isna().tolist() == [True, False, False, True, True, True]
    assert earlier[1] == at('2023-09-01 00:30') and earlier[2] == at('2023-09-02 00:50')
    # 04 Sep is absent: 03 Sep is 48 hours old and is not substituted; a product 6 hours after another has none 12 to 36 hours before it.
    assert pd.isna(earlier[3]) and pd.isna(earlier[4])
    assert (runner.EARLIER_MIN_HOURS, runner.EARLIER_MAX_HOURS) == (12, 36)


def test_evolution_follows_the_frozen_definitions():
    issued, table, mapping = small_sources()
    frame = windows([(1, '2023-09-02 06:00'), (1, '2023-09-03 06:00'), (1, '2023-09-03 00:45'), (2, '2023-09-02 06:00'),
                     (2, '2023-09-01 06:00'), (1, '2023-09-05 06:00'), (1, '2023-09-01 06:00'), (3, '2023-09-03 06:00'), (4, '2023-09-03 06:00')])
    out = attach_evolution(frame, mapping, issued, table)
    assert list(out.columns) == EVOLUTION and len(EVOLUTION) == 7
    # 02 Sep against 01 Sep, over 13413 only: 13417 is new on 02 Sep and never counts as growth of the sum.
    expected = [1, 1, 3, 0, 1, np.log1p(150)-np.log1p(100), np.log1p(9)-np.log1p(5)]
    assert np.allclose(out.loc[0].to_numpy(dtype=float), expected)
    # 03 Sep against 02 Sep, over both numbers: maxima 4, 5, 2, 4 against 3, 5, 1, 2; sums 180 against 230 and 14 against 10.
    expected = [1, 1, 0, 1, 2, np.log1p(180)-np.log1p(230), np.log1p(14)-np.log1p(10)]
    assert np.allclose(out.loc[1].to_numpy(dtype=float), expected)
    # 00:45 is inside the 30 minute margin of the 03 Sep product: the pair is still 02 Sep against 01 Sep.
    assert np.allclose(out.loc[2].to_numpy(dtype=float), out.loc[0].to_numpy(dtype=float))
    # A newly numbered region: the earlier product exists and does not list it. Flag 0, changes missing, never zero.
    assert out.loc[3, LISTED] == 0 and out.loc[3, CHANGES].isna().all()
    # No matched row in the SRS used, no earlier product (absent day, first product), unlisted number, no number: all missing.
    assert out.loc[[4, 5, 6, 7, 8]].isna().all().all()
    static = attach_context(frame, mapping, issued, table)
    assert static.srs_available.tolist() == [1, 1, 1, 1, 0, 1, 1, 0, 0]


def test_evolution_never_uses_a_product_issued_after_the_forecast_time_minus_30_minutes():
    issued, table, mapping = small_sources()
    frame = windows([(harp, time) for harp in [1, 2, 3] for time in
                     ['2023-09-02 00:59', '2023-09-02 01:00', '2023-09-02 18:00', '2023-09-03 00:59', '2023-09-03 01:00', '2023-09-05 12:00']])
    full = attach_evolution(frame, mapping, issued, table)
    before = (frame.forecast_time < at('2023-09-03 01:00')).to_numpy()
    # Changing or removing every product issued from 03 Sep on leaves every earlier forecast as it was.
    changed = table.copy()
    late = changed.issued_utc >= at('2023-09-03 00:30')
    changed.loc[late, ['zurich_rank', 'penumbra_rank', 'compact_rank', 'mag_rank']] = 0
    changed.loc[late, ['area', 'nn']] = 1
    assert attach_evolution(frame, mapping, issued, changed)[before].equals(full[before])
    assert not attach_evolution(frame, mapping, issued, changed)[~before].equals(full[~before])
    cut_issued, cut_table = issued[issued.issued_utc < at('2023-09-03 00:30')], table[table.issued_utc < at('2023-09-03 00:30')]
    assert attach_evolution(frame[before], mapping, cut_issued, cut_table).equals(full[before])
    # Row order and index do not matter, and another HARP changes nothing.
    shuffled = frame.sample(frac=1, random_state=3)
    assert attach_evolution(shuffled, mapping, issued, table).loc[frame.index].equals(full)
    assert attach_evolution(frame[frame.harp.eq(1)], mapping, issued, table).equals(full[frame.harp.eq(1).to_numpy()])


def test_availability_check_stops_on_a_late_product_a_wrong_order_and_the_reserved_period():
    forecast = pd.Series([at('2023-09-03 06:00')])
    used, earlier = pd.Series([at('2023-09-03 00:30')]), pd.Series([at('2023-09-02 00:30')])
    runner.check_availability(forecast, used, earlier)
    runner.check_availability(forecast, pd.Series([pd.NaT]), pd.Series([pd.NaT]))
    with pytest.raises(ValueError, match='after the forecast time minus 30 minutes'):
        runner.check_availability(forecast, pd.Series([at('2023-09-03 05:31')]), earlier)
    with pytest.raises(ValueError, match='after the forecast time minus 30 minutes'):
        runner.check_availability(pd.Series([at('2023-09-02 00:45')]), pd.Series([at('2023-09-01 00:30')]), earlier)
    with pytest.raises(ValueError, match='not earlier'):
        runner.check_availability(forecast, used, used)
    with pytest.raises(ValueError, match='not earlier'):
        runner.check_availability(forecast, pd.Series([pd.NaT]), earlier)
    with pytest.raises(ValueError, match='Reserved period'):
        runner.check_availability(pd.Series([at('2024-01-01 06:00')]), pd.Series([at('2023-12-31 00:30')]), pd.Series([at('2023-12-30 00:30')]))
    with pytest.raises(ValueError, match='Reserved period'):
        runner.check_availability(pd.Series([at('2024-01-01 06:00')]), pd.Series([pd.NaT]), pd.Series([pd.NaT]))


@pytest.mark.parametrize('column', ['target', 'label_status', 'label_status_v2', 'role'])
def test_evolution_refuses_labels_label_status_and_roles(column):
    issued, table, mapping = small_sources()
    frame = windows([(1, '2023-09-02 06:00')])
    with pytest.raises(ValueError, match='never see labels'):
        attach_evolution(frame.assign(**{column: 0}), mapping, issued, table)


def srs_text(issued, regions):
    lines = [':Product: SRS', f':Issued: {issued:%Y %b %d %H%M} UTC', 'I.  Regions with Sunspots.', 'Nmbr Location  Lo  Area  Z   LL   NN Mag Type']
    lines += [f'{number:04d} N10W05   100  {area:04d} {z}  05   {nn:02d} {mag}' for number, area, z, nn, mag in regions]
    return '\n'.join([*lines, 'IA. H-alpha Plages without Spots.', 'None', ''])


def harp_plan(harp):
    """HARP 1 to 48: eight a year from 2018 to 2023, 30 days apart, ten days of hourly windows each."""
    k = (harp-1) % 8
    start = pd.Timestamp(f'{2018+(harp-1)//8}-02-01', tz='UTC')+30*k*DAY
    return k, start


def write_sources(directory):
    """Daily SRS files and monthly HARP to NOAA files for the synthetic HARPs, with manifests.

    HARP k = 3 or 7 has no NOAA number; k = 1 or 5 is first listed on its third day; the product of the seventh
    day of k = 0, 3 or 6 is unavailable.
    """
    srs_dir, mapping_dir = directory/'srs', directory/'mapping'
    srs_dir.mkdir(parents=True)
    mapping_dir.mkdir()
    listed, numbered, skipped = {}, {}, set()
    for harp in range(1, 49):
        k, start = harp_plan(harp)
        for d in range(11):
            day = (start+d*DAY).date()
            numbered[(harp, day)] = 'MISSING' if k % 4 == 3 else str(12000+harp)
            if k % 4 != 3 and d >= (2 if k % 4 == 1 else 0):
                listed[day] = (2000+harp, 50+30*d+5*k, CLASSES[d], 1+d+k, MAGNETIC[d])
        if k % 3 == 0:
            skipped.add((start+6*DAY).date())
    records = []
    for moment in pd.date_range('2018-01-31', '2023-12-31', freq='D', tz='UTC'):
        day = moment.date()
        if day in skipped:
            records.append({'date': str(day), 'file': None, 'status': 'unavailable'})
            continue
        path = srs_dir/f'{moment:%Y%m%d}SRS.txt'
        issued = moment+pd.Timedelta(minutes=30)
        path.write_text(srs_text(issued, [listed[day]] if day in listed else []))
        records.append({'date': str(day), 'file': path.name, 'status': 'ok', 'sha256': sha256(path), 'issued_utc': issued.isoformat()})
    (srs_dir/'manifest.json').write_text(json.dumps({'records': records}))
    months = {}
    for (harp, day), number in numbered.items():
        months.setdefault(f'{day:%Y-%m}', []).append((harp, f'{day:%Y.%m.%d}_00:00:00_TAI', number))
    records = []
    for month, rows in sorted(months.items()):
        path = mapping_dir/f'{month.replace("-", "")}.json'
        path.write_text(json.dumps({'keywords': [{'name': name, 'values': [row[i] for row in rows]}
                                                 for i, name in enumerate(['HARPNUM', 'T_REC', 'NOAA_ARS'])]}))
        records.append({'month': month, 'file': path.name, 'status': 'ok', 'sha256': sha256(path)})
    (mapping_dir/'manifest.json').write_text(json.dumps({'records': records, 'http_fallback_months': 0}))
    return srs_dir, mapping_dir


def synthetic_development(seed=24):
    """The 48 HARPs of harp_plan with 240 hourly windows each; every second HARP has one positive day."""
    rng = np.random.default_rng(seed)
    parts = []
    for harp in range(1, 49):
        k, start = harp_plan(harp)
        frame = pd.DataFrame({'harp': harp, 'forecast_time': [start+h*HOUR for h in range(240)]})
        frame['target'] = [int(k % 2 == 0 and 100 <= h < 124) for h in range(240)]
        frame['observation_start'] = frame.forecast_time-12*HOUR
        frame['prediction_end'] = frame.forecast_time+24*HOUR
        frame['label_status'] = np.where(frame.target.eq(1), 'positive', 'negative')
        frame['missing_fraction'] = 0.0
        frame['flaring'] = int(k % 2 == 0)
        parts.append(frame)
    table = pd.concat(parts, ignore_index=True)
    values = rng.normal(size=(len(table), len(FEATURE_COLUMNS))).astype(np.float32)
    values[:, 0] += 2*table.target.to_numpy()+table.flaring.to_numpy()
    table = pd.concat([table.drop(columns='flaring'), pd.DataFrame(values, columns=FEATURE_COLUMNS)], axis=1)
    year = table.forecast_time.dt.year
    table['role'] = np.where(year <= 2021, 'train', np.where(year == 2022, 'calibration', 'validation'))
    return table


def population(development, features, years):
    out = {}
    for year in years:
        split, _ = annual_fold(runner.blind(development[runner.META], year), year)
        out[str(year)] = runner.fold_population(split, {role: features.loc[group.index] for role, group in split.items()})
    return out


def stored_thresholds(year):
    return {'watch': {'threshold': 0.2}, 'comparison_recall_0.95': {'threshold': 0.1},
            'alert': {'threshold': 0.6, 'calibration_recall': 0.5, 'calibration_precision': 0.4, 'fallback': year == 2022}}


def stub_fit(calls):
    def fit(base, groups, contexts, columns):
        calls.append(dict(columns=list(columns), rows={role: len(group) for role, group in groups.items()},
                          evaluation_columns=set(groups['evaluation'].columns),
                          aligned=all(contexts[role].index.equals(groups[role].index) for role in groups)))
        scale = 1+len(columns)/100
        score = {role: groups[role][FEATURE_COLUMNS[0]].to_numpy(dtype=float) for role in ['calibration', 'evaluation']}
        return 1/(1+np.exp(-scale*score['calibration'])), 1/(1+np.exp(-scale*score['evaluation']))
    return fit


@pytest.fixture(scope='module')
def development():
    return synthetic_development()


@pytest.fixture(scope='module')
def source_dirs(tmp_path_factory):
    return write_sources(tmp_path_factory.mktemp('srs_sources'))


@pytest.fixture(scope='module')
def features(development, source_dirs):
    issued, table, mapping = runner.load_sources(*source_dirs)
    return runner.srs_features(development[KEY], mapping, issued, table)


@pytest.fixture(scope='module')
def phase_inputs(development, features):
    table = development[[*runner.META, *FEATURE_COLUMNS]]
    config = {'years': YEARS, 'budget': {'constituent_fits': 8}, 'population': population(development, features, YEARS)}
    pipeline = json.loads((ROOT/'config/walk-forward-v2.json').read_text())
    folds = {year: annual_fold(table[runner.META], year)[1] for year in YEARS}
    return config, pipeline, table, features, folds, {year: stored_thresholds(year) for year in YEARS}


def phase(inputs, table=None, config=None, fit=None):
    base_config, pipeline, base_table, features, folds, thresholds = inputs
    return runner.fit_phase(config or base_config, {}, pipeline, base_table if table is None else table, features, folds, thresholds,
                            fit=fit or stub_fit([]))


def test_features_on_synthetic_files_mark_absence_new_regions_and_absent_products(development, features):
    assert list(features.columns) == [*CONTEXT, *EVOLUTION, AVAILABLE] and len(CONTEXT) == 13
    assert features.index.equals(development.index)
    hour = ((development.forecast_time-development.groupby('harp').forecast_time.transform('min'))/HOUR).astype(int)
    k = (development.harp-1) % 8
    # HARPs without a NOAA number have no context and no evolution at all.
    unnumbered = (k % 4 == 3).to_numpy()
    assert features.loc[unnumbered, 'srs_available'].eq(0).all() and features.loc[unnumbered, EVOLUTION].isna().all().all()
    # A region listed from its first day: the first product has no earlier listing (flag 0), later days carry a change.
    plain = (k == 2).to_numpy()
    assert features.loc[plain & (hour < 1), 'srs_available'].eq(0).all()
    assert features.loc[plain & hour.between(1, 24), LISTED].eq(0).all() and features.loc[plain & hour.between(1, 24), CHANGES].isna().all().all()
    later = plain & (hour >= 25).to_numpy()
    assert features.loc[later, AVAILABLE].all() and features.loc[later, LISTED].eq(1).all()
    assert np.allclose(features.loc[plain & hour.between(25, 48), 'evo__area_log_change'], np.log1p(50+30+10)-np.log1p(50+10))
    assert features.loc[plain & hour.between(25, 48), 'evo__zurich_rank_change'].eq(1).all()
    assert features.loc[plain & hour.between(169, 192), 'evo__zurich_rank_change'].eq(-1).all()
    # The seventh product of k = 0 is unavailable: the sixth is still used on day seven (its own pair), and on day eight
    # the SRS used has no product 12 to 36 hours before it, so everything is missing and nothing older is substituted.
    absent = (k == 0).to_numpy()
    assert features.loc[absent & hour.between(145, 168), AVAILABLE].all()
    assert features.loc[absent & hour.between(169, 192), 'srs_available'].eq(1).all()
    assert features.loc[absent & hour.between(169, 192), EVOLUTION].isna().all().all()
    assert features.loc[absent & hour.between(193, 216), AVAILABLE].all()
    # The coverage flag is the presence of the changes, and the flag is never 1 without them.
    assert features[AVAILABLE].equals(features[CHANGES].notna().all(axis=1)) and features[AVAILABLE].equals(features[LISTED].eq(1))
    assert 0 < features[AVAILABLE].mean() < features.srs_available.mean() < 1


def test_reserved_products_are_refused_before_a_file_is_opened(tmp_path, source_dirs):
    srs_dir, mapping_dir = source_dirs
    runner.refuse_reserved_sources(srs_dir, mapping_dir)
    records = json.loads((srs_dir/'manifest.json').read_text())['records']

    def srs_with(record, name):
        directory = tmp_path/name
        directory.mkdir()
        (directory/'manifest.json').write_text(json.dumps({'records': [*records[:3], record]}))
        return directory

    # The listed files do not exist in these directories: a refusal proves that nothing was opened.
    dated = srs_with({'date': '2024-01-01', 'file': '20240101SRS.txt', 'status': 'ok', 'sha256': '0'*64}, 'dated')
    issued = srs_with({'date': '2023-12-31', 'file': '20231231SRS.txt', 'status': 'ok', 'sha256': '0'*64,
                       'issued_utc': '2024-01-01T00:30:00+00:00'}, 'issued')
    for directory in [dated, issued]:
        with pytest.raises(ValueError, match='at or after 2024-01-01'):
            runner.load_sources(directory, mapping_dir)
    late_mapping = tmp_path/'mapping'
    late_mapping.mkdir()
    (late_mapping/'manifest.json').write_text(json.dumps({'records': [{'month': '2024-01', 'file': '202401.json', 'status': 'ok', 'sha256': '0'*64}],
                                                          'http_fallback_months': 0}))
    with pytest.raises(ValueError, match='at or after 2024-01'):
        runner.load_sources(srs_dir, late_mapping)
    # A file whose manifest entry looks early and whose text says it was issued in 2024 is refused after parsing.
    hidden = tmp_path/'hidden'
    hidden.mkdir()
    path = hidden/'20231231SRS.txt'
    path.write_text(srs_text(at('2024-01-01 00:30'), [(2001, 100, 'Cso', 5, 'Beta')]))
    (hidden/'manifest.json').write_text(json.dumps({'records': [{'date': '2023-12-31', 'file': path.name, 'status': 'ok', 'sha256': sha256(path)}]}))
    with pytest.raises(ValueError, match='issued at or after 2024-01-01'):
        runner.load_sources(hidden, mapping_dir)
    assert runner.RESERVED_START == at('2024-01-01')


def test_phase_one_is_identical_whatever_the_evaluation_labels_are(phase_inputs):
    config, _, table, _, _, _ = phase_inputs
    single = dict(config, years=[2023], budget={'constituent_fits': 4})
    flipped = table.assign(target=table.target.where(table.forecast_time.dt.year < 2023, 1-table.target))
    first, second = phase(phase_inputs, config=single), phase(phase_inputs, table=flipped, config=single)
    assert json.dumps(first[0], sort_keys=True) == json.dumps(second[0], sort_keys=True)
    assert first[1][2023].equals(second[1][2023]) and first[2] == second[2]
    assert list(first[1][2023].columns) == ['harp', 'forecast_time', *runner.CANDIDATES, AVAILABLE]


def test_phase_one_gives_each_candidate_its_frozen_columns_and_no_evaluation_label(phase_inputs):
    calls = []
    thresholds, probabilities, coverage, fits = phase(phase_inputs, fit=stub_fit(calls))
    assert fits == 8 and [c['columns'] for c in calls] == [CONTEXT, [*CONTEXT, *EVOLUTION]]*2
    assert all(c['aligned'] and not {'target', 'label_status'} & c['evaluation_columns'] for c in calls)
    assert len(FEATURE_COLUMNS)+len(calls[0]['columns']) == 109 and len(FEATURE_COLUMNS)+len(calls[1]['columns']) == 116
    assert AVAILABLE not in calls[1]['columns']
    assert all(thresholds[str(year)]['control'] == stored_thresholds(year) for year in YEARS)
    assert {(row['year'], row['role']) for row in coverage} == set(itertools.product(YEARS, ['train', 'calibration', 'evaluation']))
    row = next(r for r in coverage if r['year'] == 2023 and r['role'] == 'evaluation')
    assert row['evolution_available'] == int(probabilities[2023][AVAILABLE].sum()) == row['earlier_listed'] > 0
    assert row[f'missing__{LISTED}'] == row['rows']-row['earlier_listed']-row['earlier_not_listed']
    assert row['missing__evo__area_log_change'] == row['rows']-row['evolution_available'] and row['earlier_not_listed'] > 0


def test_phase_one_stops_on_budget_population_or_fold_changes(phase_inputs):
    config, pipeline, table, features, folds, thresholds = phase_inputs
    with pytest.raises(RuntimeError):
        phase(phase_inputs, config=dict(config, budget={'constituent_fits': 6}))
    with pytest.raises(RuntimeError):
        phase(phase_inputs, config=dict(config, budget={'constituent_fits': 10}))
    for key in runner.POPULATION:
        changed = copy.deepcopy(config)
        changed['population']['2022'][key] += 1
        with pytest.raises(ValueError):
            phase(phase_inputs, config=changed)
    other = copy.deepcopy(folds)
    other[2022][0]['rows'] += 1
    with pytest.raises(ValueError):
        runner.fit_phase(config, {}, pipeline, table, features, other, thresholds, fit=stub_fit([]))


def test_default_fit_is_the_unchanged_recipe_function_and_static_features_are_the_frozen_ones():
    assert runner.fit_probabilities is fit_probabilities
    assert runner.run.__defaults__ == (fit_probabilities,) and runner.fit_phase.__defaults__ == (fit_probabilities,)
    assert runner.CONSTITUENTS == 2 and runner.attach_context is attach_context and runner.srs_feature_table is srs_feature_table
    static = json.loads((ROOT/'config/region-context-v1.json').read_text())
    assert list(static['context_features']) == CONTEXT == runner.CANDIDATES['srs_static']
    assert runner.SAFETY == pd.Timedelta(minutes=30)


def test_every_result_falls_into_exactly_one_reading():
    keys = ['all_year_primary', 'cycle25_primary', 'cycle25_bootstrap_lower_above_zero']
    seen = set()
    for values in itertools.product([False, True], repeat=8):
        evolution = dict(zip(keys, values[:3]), beats_srs_static_all_years=values[3], beats_srs_static_cycle25=values[4])
        static = dict(zip(keys, values[5:]))
        if (evolution['all_year_primary'] and not evolution['cycle25_primary']) or (static['all_year_primary'] and not static['cycle25_primary']) \
                or (evolution['beats_srs_static_all_years'] and not evolution['beats_srs_static_cycle25']):
            continue
        decision = runner.read({'srs_evolution': evolution, 'srs_static': static})
        specific = (evolution['all_year_primary'] and evolution['beats_srs_static_all_years']) or (
            evolution['cycle25_primary'] and evolution['cycle25_bootstrap_lower_above_zero'] and evolution['beats_srs_static_cycle25'])
        goal = {'srs_static': runner.meets_goal(static), 'srs_evolution': runner.meets_goal(evolution)}
        expected = 'S1_evolution_helps' if specific else 'S2_refit_or_static_only' if any(goal.values()) else 'S3_no_gain'
        assert decision['reading'] == expected and decision['reading'] in runner.READINGS
        assert decision['srs_evolution_goal_met_and_beats_srs_static'] == int(decision['reading'] == 'S1_evolution_helps')
        assert decision['candidates_meeting_goal_against_control'] == [c for c in runner.CANDIDATES if goal[c]]
        assert decision['outcome_label'] == runner.LABELS[decision['reading']]
        seen.add(decision['reading'])
    assert seen == set(runner.READINGS)
    passing, failing = dict(zip(keys, [False, True, True])), dict(zip(keys, [False, True, False]))
    beats = dict(beats_srs_static_all_years=False, beats_srs_static_cycle25=True)
    loses = dict(beats_srs_static_all_years=False, beats_srs_static_cycle25=False)
    assert runner.read({'srs_evolution': {**passing, **beats}, 'srs_static': passing})['outcome_label'] == 'result:goal-met'
    assert runner.read({'srs_evolution': {**passing, **loses}, 'srs_static': failing})['outcome_label'] == 'result:partial'
    assert runner.read({'srs_evolution': {**failing, **beats}, 'srs_static': passing})['outcome_label'] == 'result:partial'
    assert runner.read({'srs_evolution': {**failing, **beats}, 'srs_static': failing})['outcome_label'] == 'result:no-gain'


def test_evolution_subset_counts_windows_with_and_without_a_change():
    frame = pd.DataFrame({'target': [1, 1, 0, 0, 1, 0], AVAILABLE: [True, True, True, True, False, False]})
    alarm = np.array([True, False, True, False, True, True])
    row = runner.evolution_subset(frame, alarm, 2023, 'srs_evolution', True)
    assert row['subset'] == 'change_available' and (row['windows'], row['positives'], row['tp'], row['fp'], row['fn']) == (4, 2, 1, 1, 1)
    assert row['precision'] == 0.5 and row['recall'] == 0.5 and np.isclose(row['window_share'], 4/6) and np.isclose(row['positive_share'], 2/3)
    other = runner.evolution_subset(frame, alarm, 2023, 'srs_evolution', False)
    assert other['subset'] == 'change_missing' and (other['windows'], other['tp'], other['fp'], other['fn']) == (2, 1, 1, 0)
    quiet = runner.evolution_subset(frame.assign(target=0), np.zeros(6, dtype=bool), 2023, 'control', True)
    assert quiet['precision'] is None and quiet['recall'] is None and quiet['positive_share'] is None


def test_frozen_protocol_matches_the_idea_and_the_adopted_basis():
    text = CONFIG.read_text()
    config = json.loads(text)
    v2 = json.loads((ROOT/'config/activity-history-v2.json').read_text())
    life = json.loads((ROOT/'config/life-phase-v1.json').read_text())
    static = json.loads((ROOT/'config/region-context-v1.json').read_text())
    runner.check_protocol(config)
    assert config['id'] == 'srs-evolution-v1' and config['status'] == 'frozen_before_any_candidate_result'
    assert config['reserved_test_accessed'] is False and not {chr(0x2013), chr(0x2014)} & set(text)
    assert not {chr(0x2013), chr(0x2014)} & set(Path(runner.__file__).read_text()+Path(__file__).read_text())
    assert config['years'] == v2['years'] == [2014, 2015, 2016, 2017, 2022, 2023] and config['alert_fallback_years'] == [2022]
    assert [c['id'] for c in config['candidates']] == ['srs_static', 'srs_evolution'] and config['control']['id'] == 'control'
    features = config['features']
    assert features['added']['srs_static'] == list(static['context_features']) == CONTEXT
    assert features['added']['srs_evolution'] == [*CONTEXT, *EVOLUTION]
    assert features['changed_fields'] == ['zurich_rank', 'penumbra_rank', 'compact_rank', 'mag_rank', 'area_log', 'spots_log']
    assert EVOLUTION == ['evo__earlier_listed', *[f'evo__{name}_change' for name in features['changed_fields']]]
    assert config['budget']['added_features'] == {'srs_static': 13, 'srs_evolution': 20}
    assert config['budget']['constituent_fits'] == 24 and config['budget']['hyperparameter_search'] == 0 and config['budget']['downloads'] == 0
    assert config['srs_issue_dates_before'] == '2024-01-01' and features['safety_margin_minutes'] == 30
    assert '30 minutes' in static['availability_rule'] and set(config['availability_rule']) == {'source', 'both_products', 'absence', 'reserved'}
    evidence = config['evidence']
    assert evidence['table'] == 'artifacts/relabelled_development_20261111_r1' and evidence['control'] == 'artifacts/walk_forward_v2_20261112_r1'
    assert evidence['srs_directory'] == static['evidence']['srs_directory'] == 'data/region_summaries_20261109_r1'
    assert evidence['mapping_directory'] == static['evidence']['mapping_directory'] == 'data/harp_noaa_mapping_20261109_r1'
    # The table, the stored control and the two source directories are the only evidence directories named as inputs.
    assert set(re.findall(r'(?:artifacts|data)/[A-Za-z0-9_]+', text)) \
        == {evidence['table'], evidence['control'], evidence['srs_directory'], evidence['mapping_directory']}
    assert evidence['table_report_sha256'] == v2['evidence']['table_report_sha256']
    assert evidence['control_report_sha256'] == v2['evidence']['control_report_sha256']
    assert evidence['mapping_manifest_sha256'] == v2['evidence']['mapping_manifest_sha256']
    assert re.fullmatch(r'[0-9a-f]{64}', evidence['srs_manifest_sha256'])
    assert sha256(ROOT/evidence['pipeline_protocol']) == evidence['pipeline_protocol_sha256']
    assert sha256(ROOT/evidence['base_protocol']) == evidence['base_protocol_sha256']
    assert config['acceptance']['per_year_primary'] == v2['acceptance']['per_year_primary']
    assert config['acceptance']['bootstrap'] == life['acceptance']['bootstrap']
    assert set(config['reading']) == {*runner.READINGS, 'exclusive'}
    assert all(runner.LABELS[name] in config['reading'][name] for name in runner.READINGS)
    assert config['acceptance_rule'] == {**config['acceptance_rule'], 'metric_path': 'decision.srs_evolution_goal_met_and_beats_srs_static',
                                         'op': '>=', 'value': 1}
    assert set(config['population'])-{'source', 'coverage_counts'} == {str(year) for year in config['years']}
    for year in config['years']:
        counts = config['population'][str(year)]
        assert set(counts) == set(runner.POPULATION)
        # Rows and positives are those of the same table and folds in the life-phase protocol.
        assert all(counts[key] == life['population'][str(year)][key] for key in runner.POPULATION[:5])
        assert 0 < counts['train_evolution_available'] < counts['train_srs_available'] < counts['train_rows']
        assert 0 < counts['evaluation_evolution_available'] < counts['evaluation_srs_available'] < counts['evaluation_rows']/2


@pytest.mark.parametrize('change', [
    lambda c: c['candidates'].append({'id': 'srs_evolution_48h'}),
    lambda c: c['candidates'].reverse(),
    lambda c: c['features']['added']['srs_static'].append('evo__earlier_listed'),
    lambda c: c['features']['added']['srs_evolution'].append(AVAILABLE),
    lambda c: c['features']['added']['srs_evolution'].pop(),
    lambda c: c['features']['added'].update(extra=CONTEXT),
    lambda c: c['features']['changed_fields'].append('extent_max'),
    lambda c: c['features']['earlier_product_hours'].update(max=60),
    lambda c: c['features'].update(safety_margin_minutes=0),
    lambda c: c['features']['reporting_flag'].update(model_input=True),
    lambda c: c.update(srs_issue_dates_before='2025-01-01'),
    lambda c: c['years'].append(2024),
    lambda c: c['years'].remove(2022),
    lambda c: c['budget'].update(constituent_fits=48),
    lambda c: c['budget'].update(downloads=1),
    lambda c: c.update(reserved_test_accessed=True),
    lambda c: c.update(status='design_proposed'),
    lambda c: c.update(alert_fallback_years=[2021]),
])
def test_runner_refuses_a_changed_protocol(change):
    config = json.loads(CONFIG.read_text())
    change(config)
    with pytest.raises(ValueError):
        runner.check_protocol(config)


def write_inputs(directory, development, source_dirs, features):
    """A materialized table, a stored control and a protocol copy that point at synthetic files only."""
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
    base = json.loads((ROOT/'config/walk-forward-v1.json').read_text())
    base['candidates']['xgboost']['n_estimators'] = 8
    (directory/'base.json').write_text(json.dumps(base))
    srs_dir, mapping_dir = source_dirs
    config = json.loads(CONFIG.read_text())
    config.update(years=YEARS, population=population(development, features, YEARS))
    config['budget']['constituent_fits'] = 8
    config['evidence'].update(table=str(table_dir), table_report_sha256=sha256(table_dir/'report.json'), control=str(control_dir),
                              control_report_sha256=sha256(control_dir/'report.json'), base_protocol=str(directory/'base.json'),
                              base_protocol_sha256=sha256(directory/'base.json'),
                              pipeline_protocol=str(ROOT/'config/walk-forward-v2.json'),
                              srs_directory=str(srs_dir), srs_manifest_sha256=sha256(srs_dir/'manifest.json'),
                              mapping_directory=str(mapping_dir), mapping_manifest_sha256=sha256(mapping_dir/'manifest.json'))
    (directory/'config.json').write_text(json.dumps(config))
    return directory/'config.json'


@pytest.fixture(scope='module')
def executed(tmp_path_factory, development, source_dirs, features):
    directory = tmp_path_factory.mktemp('srs_evolution')
    config_path = write_inputs(directory, development, source_dirs, features)
    result, table = runner.run(config_path, directory/'output')
    return directory, config_path, result, table


def test_run_on_synthetic_inputs_freezes_phase_one_before_labels(executed):
    directory, config_path, result, table = executed
    output = directory/'output'
    phase1 = json.loads((output/'phase1.json').read_text())
    assert set(phase1) == {'thresholds.json', 'features.json', 'srs_coverage.csv', 'probabilities_2022.parquet', 'probabilities_2023.parquet'}
    assert all(sha256(output/name) == value for name, value in phase1.items())
    assert result['phase1_sha256'] == sha256(output/'phase1.json') and result['thresholds_sha256'] == phase1['thresholds.json']
    assert result['features_sha256'] == phase1['features.json']
    assert result['config_sha256'] == sha256(config_path) and result['constituent_fits'] == 8
    assert result['feature_counts'] == {'srs_static': 109, 'srs_evolution': 116}
    written = json.loads((output/'features.json').read_text())
    assert written == {'srs_static': [*FEATURE_COLUMNS, *CONTEXT], 'srs_evolution': [*FEATURE_COLUMNS, *CONTEXT, *EVOLUTION]}
    for year in YEARS:
        assert list(pd.read_parquet(output/f'probabilities_{year}.parquet').columns) == ['harp', 'forecast_time', *runner.CANDIDATES, AVAILABLE]
    thresholds = json.loads((output/'thresholds.json').read_text())
    assert all(set(thresholds[str(year)]) == {'control', *runner.CANDIDATES} for year in YEARS)
    assert all(thresholds[str(year)]['control'] == stored_thresholds(year) for year in YEARS)
    assert result['reserved_test_accessed'] is False and result['model_promoted'] is False and result['threshold_adopted'] is False
    assert result['alert_fallback_years_control'] == [2022] and result['srs_issue_dates_before'] == '2024-01-01'
    assert result['artifact_hashes'].keys() >= {'results.csv', 'intervals.csv', 'evolution_subset.csv', 'phase1.json', 'predictions_2022.parquet'}


def test_run_reports_every_candidate_and_one_reading(executed):
    directory, _, result, table = executed
    assert set(zip(table.year, table.candidate, table.tier)) == set(itertools.product(YEARS, ['control', *runner.CANDIDATES], ['watch', 'alert']))
    alert = table[table.tier.eq('alert')].set_index(['year', 'candidate'])
    assert bool(alert.loc[(2022, 'control'), 'fallback']) and not bool(alert.loc[(2023, 'control'), 'fallback'])
    assert alert.loc[(2022, 'control'), 'threshold'] == 0.6
    assert alert.missed_positive_runs.notna().all() and alert.alert_fp_share_within_72h_of_positive.dropna().between(0, 1).all()
    decision = result['decision']
    assert result['reading'] == decision['reading'] and decision['reading'] in runner.READINGS
    assert decision['srs_evolution_goal_met_and_beats_srs_static'] == int(decision['reading'] == 'S1_evolution_helps')
    assert set(result['acceptance']) == {'control', *runner.CANDIDATES}
    assert {'beats_srs_static_all_years', 'beats_srs_static_cycle25', 'all_year_primary', 'cycle25_primary'} <= set(result['acceptance']['srs_evolution'])
    subsets = pd.read_csv(directory/'output/evolution_subset.csv')
    assert set(zip(subsets.year, subsets.candidate, subsets.subset)) == set(itertools.product(
        YEARS, ['control', *runner.CANDIDATES], ['change_available', 'change_missing']))
    assert subsets.window_share.between(0, 1, inclusive='neither').all()
    assert np.allclose(subsets.groupby(['year', 'candidate']).window_share.sum(), 1)
    intervals = pd.read_csv(directory/'output/intervals.csv')
    assert set(zip(intervals.candidate, intervals.reference)) == {('srs_static', 'control'), ('srs_evolution', 'control'), ('srs_evolution', 'srs_static')}


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
    refused(lambda c: c['evidence'].update(srs_manifest_sha256='0'*64), 'srs_hash')
    refused(lambda c: c['evidence'].update(mapping_manifest_sha256='0'*64), 'mapping_hash')
    refused(lambda c: c.update(alert_fallback_years=[2023]), 'fallback')
    refused(lambda c: c['years'].append(2024), 'reserved')
    refused(lambda c: c['features']['added']['srs_evolution'].append(AVAILABLE), 'flag_input')
    refused(lambda c: c.update(srs_issue_dates_before='2026-01-01'), 'srs_cutoff')


def test_run_refuses_reserved_srs_changed_files_and_changed_labels(tmp_path, development, source_dirs, features):
    config_path = write_inputs(tmp_path, development, source_dirs, features)
    config = json.loads(config_path.read_text())
    # A source directory whose manifest lists a 2024 product stops the run before any fit, even with a matching hash.
    srs_dir = tmp_path/'srs_2024'
    srs_dir.mkdir()
    manifest = json.loads((source_dirs[0]/'manifest.json').read_text())
    manifest['records'].append({'date': '2024-01-01', 'file': '20240101SRS.txt', 'status': 'ok', 'sha256': '0'*64})
    (srs_dir/'manifest.json').write_text(json.dumps(manifest))
    reserved = copy.deepcopy(config)
    reserved['evidence'].update(srs_directory=str(srs_dir), srs_manifest_sha256=sha256(srs_dir/'manifest.json'))
    (tmp_path/'reserved.json').write_text(json.dumps(reserved))
    calls = []
    with pytest.raises(ValueError, match='at or after 2024-01-01'):
        runner.run(tmp_path/'reserved.json', tmp_path/'reserved_output', fit=stub_fit(calls))
    assert not calls and not (tmp_path/'reserved_output').exists()
    thresholds = tmp_path/'control/2023/thresholds.json'
    original = thresholds.read_text()
    thresholds.write_text(original.replace('0.6', '0.7'))
    with pytest.raises(ValueError, match='Stored control file changed'):
        runner.run(config_path, tmp_path/'changed_thresholds')
    thresholds.write_text(original)
    # A control whose stored labels differ from the table is refused, even with consistent hashes.
    predictions = tmp_path/'control/2023/predictions.parquet'
    frame = pd.read_parquet(predictions)
    frame['target'] = 1-frame.target
    frame.to_parquet(predictions, index=False)
    report_path = tmp_path/'control/report.json'
    report = json.loads(report_path.read_text())
    report['artifact_hashes']['2023/predictions.parquet'] = sha256(predictions)
    report_path.write_text(json.dumps(report))
    config['evidence']['control_report_sha256'] = sha256(report_path)
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='Stored control labels differ'):
        runner.run(config_path, tmp_path/'changed_labels', fit=stub_fit([]))
