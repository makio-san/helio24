import pytest
from helio24.quality_audit import header_frame, quality_value, tai_clock


def test_quality_missing_is_not_clean():
    assert quality_value('MISSING') is None
    assert quality_value('0x00010400') == 66560
    assert quality_value('00000000') == 0
    for value in ['-1', '4294967296', 'invalid']:
        with pytest.raises(ValueError):
            quality_value(value)


def test_tai_parser_does_not_accept_or_claim_utc():
    assert tai_clock('2011.01.05_21:24:00_TAI').tzinfo is None
    with pytest.raises(ValueError):
        tai_clock('2011.01.05_21:24:00_UTC')


def test_header_identity_duplicates_and_unknown_quality():
    payload = dict(status=0, count=1, keywords=[dict(name=k, values=[v]) for k, v in
        dict(HARPNUM='334', T_REC='2011.01.05_21:24:00_TAI', T_OBS='2011.01.05_21:23:52_TAI', QUALITY='MISSING').items()])
    assert header_frame(payload, 334).source_quality.isna().all()
    with pytest.raises(ValueError, match='Unexpected HARP'):
        header_frame(payload, 335)
    payload['keywords'].append(payload['keywords'][0])
    with pytest.raises(ValueError, match='Duplicate'):
        header_frame(payload, 334)
