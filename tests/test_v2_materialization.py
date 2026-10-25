import pandas as pd

from helio24.v2_contract import EVENT_COLUMNS, V2_MEASUREMENTS
from scripts.materialize_v2_development import inspect_member


def test_member_materialization_labels_and_excludes_windows(tmp_path):
    frame = pd.DataFrame({
        'harp_number': 7,
        'obs_start': pd.date_range('2022-06-01 00:00:37', periods=65, freq='12min'),
    })
    for column in V2_MEASUREMENTS.values():
        frame[column] = 1.0
    for column in EVENT_COLUMNS[1:]:
        frame[column] = pd.NA
    frame.loc[0, ['start_time', 'peak_time', 'end_time', 'goes_class',
                  'confidence', 'has_goes', 'has_ssw', 'has_xrt', 'harp_vote',
                  'max_pair_distance_deg']] = [
        pd.Timestamp('2022-06-01 12:55'), pd.Timestamp('2022-06-01 13:00'),
        pd.Timestamp('2022-06-01 13:05'), 'M1.0', 'high', True, False, False,
        '1-0', 0.0]
    path = tmp_path / 'member.parquet'
    frame.to_parquet(path)
    roles = {
        'train': (pd.Timestamp('2022-01-01T00:00Z'), pd.Timestamp('2023-01-01T00:00Z')),
        'calibration': (pd.Timestamp('2023-01-01T00:00Z'), pd.Timestamp('2024-01-01T00:00Z')),
        'validation': (pd.Timestamp('2024-01-01T00:00Z'), pd.Timestamp('2025-01-01T00:00Z')),
        'test': (pd.Timestamp('2025-01-01T00:00Z'), pd.Timestamp('2026-01-01T00:00Z')),
    }
    unassigned = pd.DataFrame(columns=['event_id', 'peak_time', 'goes_class'])
    shards = tmp_path / 'shards'
    shards.mkdir()
    result = inspect_member(path, 'member.parquet', path.stat().st_size, 1,
                            roles, unassigned, shards)
    assert result['retained_rows'] == 2
    assert result['label_status'] == {'positive': 2}
    materialized = pd.read_parquet(shards / result['shard']['file'])
    assert materialized.target.tolist() == [1, 1]
    assert not set(EVENT_COLUMNS) & set(materialized.columns)
