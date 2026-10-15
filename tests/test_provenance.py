import pandas as pd

from helio24.provenance import association_evidence, timing_evidence


def test_nearest_and_containing_interval_are_different_conventions():
    stamp = pd.Timestamp('2014-01-01 00:00')
    for minutes, nearest, containing in [(0, True, True), (6, True, True),
                                          (7, False, True), (11, False, True),
                                          (12, False, False), (-1, True, False)]:
        result = timing_evidence(stamp, stamp+pd.Timedelta(minutes=minutes))
        assert result['nearest_12min_compatible'] == nearest
        assert result['containing_12min_compatible'] == containing


def test_history_methods_are_not_merged_across_harp_identifiers():
    rows = pd.DataFrame(dict(flare_id=[1, 1, 2, 2], harp=[10, 20, 30, 30],
                             source=['MFLARE_LABEL', 'MFLARE_LABEL_LOC', 'XFLARE_LABEL', 'XFLARE_LABEL_LOC']))
    result = association_evidence(rows)
    assert result.association_method.tolist() == ['noaa_only', 'location_only', 'both']
