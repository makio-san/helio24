import json
from pathlib import Path
import pandas as pd
import pytest
from helio24.evaluation_protocol import development_split, preflight, protocol_errors, require_training_ready


def protocol():
    return json.loads((Path(__file__).resolve().parents[1] / 'config/experiment5.json').read_text())


def row(harp, time):
    time = pd.Timestamp(time)
    return dict(harp=harp, observation_start=time-pd.Timedelta(hours=12), forecast_time=time,
                prediction_end=time+pd.Timedelta(hours=24))


def test_current_protocol_cannot_train_or_test():
    spec = protocol()
    assert len(preflight(spec)['pending_gates']) == 7
    with pytest.raises(ValueError, match='prerequisites'):
        require_training_ready(spec)
    spec['gates'] = {k: 'verified' for k in spec['gates']}
    assert not preflight(spec)['ready_for_training']
    assert not preflight(spec)['final_test_allowed']
    del spec['gates']['quality_policy']
    assert preflight(spec)['missing_gates'] == ['quality_policy']


def test_protocol_structure_is_validated_before_training():
    spec = protocol()
    assert protocol_errors(spec) == []
    spec['roles']['calibration'][0] = '2022-01-02T00:00:00Z'
    spec['primary_recall'] = 2
    spec['candidates'].pop('baseline')
    errors = protocol_errors(spec)
    assert 'train and calibration must be contiguous' in errors
    assert 'primary_recall must be in (0, 1]' in errors
    assert 'candidate set must be baseline, logistic and xgboost' in errors


def test_temporal_boundaries_and_shared_regions_are_purged():
    frame = pd.DataFrame([row(1, '2021-12-30T00:00Z'), row(2, '2021-12-31T12:00Z'),
                          row(3, '2022-01-01T06:00Z'), row(1, '2022-02-01T00:00Z'),
                          row(4, '2022-02-01T00:00Z'), row(5, '2023-02-01T00:00Z')])
    groups, audit = development_split(frame, protocol())
    assert list(groups['train'].harp) == [1]
    assert list(groups['calibration'].harp) == [4]
    assert list(groups['validation'].harp) == [5]
    assert audit['roles'][0]['boundary_removed'] == 1
    assert audit['roles'][1]['boundary_removed'] == 1
    assert audit['roles'][1]['shared_harp_rows_removed'] == 1


def test_holdout_naive_time_and_outcome_columns_are_rejected():
    with pytest.raises(ValueError, match='Reserved'):
        development_split(pd.DataFrame([row(1, '2024-01-02T00:00Z')]), protocol())
    with pytest.raises(ValueError, match='time zone'):
        development_split(pd.DataFrame([row(1, '2023-02-01')]), protocol())
    frame = pd.DataFrame([row(1, '2023-02-01T00:00Z')]).assign(target=1)
    with pytest.raises(ValueError, match='metadata only'):
        development_split(frame, protocol())


def test_exact_end_boundary_allowed_and_empty_roles_reported():
    groups, audit = development_split(pd.DataFrame([row(1, '2021-12-31T00:00Z')]), protocol())
    assert len(groups['train']) == 1
    assert audit['empty_roles'] == ['calibration', 'validation']


def test_frozen_v6_contract_is_ready_for_development_training_only():
    path = Path(__file__).resolve().parents[1] / 'config/experiment5-v6.json'
    state = preflight(json.loads(path.read_text()))
    assert state['ready_for_training'] is True
    assert state['pending_gates'] == []
    assert state['final_test_allowed'] is False


def test_frozen_v7_blend_contract_is_ready_for_development_training_only():
    path = Path(__file__).resolve().parents[1] / 'config/experiment5-v7.json'
    state = preflight(json.loads(path.read_text()))
    assert state['ready_for_training'] is True
    assert state['final_test_allowed'] is False
