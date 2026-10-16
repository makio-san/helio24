import pytest

from helio24.compatibility import inspect_columns
from helio24.data import MAGNETIC_COLUMNS


def test_schema_match_never_claims_numerical_or_quality_parity():
    columns = [name.lower() for name in MAGNETIC_COLUMNS]+['goes_class', 'peak_time', 'confidence', 'w_usflux']
    result = inspect_columns(columns)
    assert len(result['magnetic_column_mapping']) == 24
    assert result['magnetic_column_mapping']['USFLUX'] == 'usflux'
    assert result['missing_quality_columns'] == ['QUALITY', 'IS_TMFI']
    assert set(result['outcome_columns_excluded']) == {'goes_class', 'peak_time', 'confidence'}
    assert not result['ready_for_model']


def test_weighted_features_are_not_silent_replacements():
    result = inspect_columns(['w_usflux', 'quality', 'is_tmfi'])
    assert 'USFLUX' in result['missing_magnetic_columns']
    assert result['magnetic_column_mapping'] == {}
    assert result['missing_quality_columns'] == []
    assert not result['ready_for_model']
    with pytest.raises(ValueError, match='Ambiguous'):
        inspect_columns(['USFLUX', 'usflux'])


def test_overlap_reads_only_old_measurements_and_keeps_quality_unresolved(tmp_path, monkeypatch):
    import json
    import shutil
    import pandas as pd
    from helio24.data import ROOT
    from helio24.full_data import sha256
    from scripts.audit_v2_overlap import run

    for name in ['data/compatibility_probe', 'data/raw/partition1', 'scripts']:
        (tmp_path / name).mkdir(parents=True)
    shutil.copyfile(ROOT / 'scripts/audit_v2_overlap.py', tmp_path / 'scripts/audit_v2_overlap.py')
    stamps = pd.date_range('2011-01-01', periods=60, freq='12min')
    old = pd.DataFrame({name: 1. for name in MAGNETIC_COLUMNS}, index=range(60))
    old['Timestamp'], old['QUALITY'], old['IS_TMFI'] = stamps, 0, True
    old.to_csv(tmp_path / 'data/raw/partition1/FQ_ar1_s2011-01-01T00:00:00_e2011-01-01T11:48:00.csv',
               sep='\t', index=False)
    new = pd.DataFrame({name.lower(): 1. for name in MAGNETIC_COLUMNS}, index=range(61))
    new['harp_number'] = 1
    new['obs_start'] = [*stamps, pd.Timestamp('2025-01-01')]
    new['goes_class'] = 'must_not_be_read'
    path = tmp_path / 'data/compatibility_probe/first_member.parquet'
    new.to_parquet(path)
    (path.parent / 'schema.json').write_text(json.dumps(dict(member_sha256=sha256(path))))
    original = pd.read_parquet
    calls = []
    def checked_read(*args, **kwargs):
        calls.append(kwargs)
        assert 'goes_class' not in kwargs['columns']
        assert kwargs['filters'] == [('obs_start', '<', pd.Timestamp('2019-01-01'))]
        return original(*args, **kwargs)
    monkeypatch.setattr(pd, 'read_parquet', checked_read)
    report = run(tmp_path)
    assert len(calls) == 1
    assert report['matched_samples'] == 60
    assert report['close_comparisons'] == 60*24
    assert report['ready_for_model'] is False
