import pytest
from helio24.spatial_review import disposition, validate_frame


def fixture():
    frame = dict(metadata=dict(status='downloaded'), image=dict(status='downloaded'), image_id='1',
                 requested_utc='2014-08-21T13:31:00Z', actual_utc='2014-08-21T13:31:00+00:00')
    metadata = dict(id='1', name='AIA 131', date='2014-08-21 13:31:00')
    return frame, metadata


def test_rendered_time_must_match_metadata():
    frame, metadata = fixture()
    assert validate_frame(frame, metadata, metadata['date']).endswith('+00:00')
    with pytest.raises(ValueError, match='watermark'):
        validate_frame(frame, metadata, '2014-08-21 13:31:12')
    frame['requested_utc'] = '2014-08-21T13:29:00Z'
    with pytest.raises(ValueError, match='tolerance'):
        validate_frame(frame, metadata, metadata['date'])


def test_incomplete_and_wrong_channel_evidence_rejected():
    frame, metadata = fixture()
    metadata['name'] = 'AIA 171'
    with pytest.raises(ValueError, match='channel'):
        validate_frame(frame, metadata, metadata['date'])
    frame['image']['status'] = 'unavailable'
    with pytest.raises(ValueError, match='Incomplete'):
        validate_frame(frame, metadata, metadata['date'])


def test_visual_candidate_never_authorizes_relabeling():
    for flare_id in [8765, 8864]:
        result = disposition(flare_id)
        assert not result['label_change_allowed']
        assert not result['definitive_spatial_adjudication']
        assert result['status'].endswith('harp_unresolved')
