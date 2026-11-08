import numpy as np
import pandas as pd

from scripts.audit_region_context_features import CONTEXT, attach_context, srs_feature_table


def rows():
    t1, t2 = pd.Timestamp('2023-09-02 00:30', tz='UTC'), pd.Timestamp('2023-09-03 00:30', tz='UTC')
    return pd.DataFrame([
        dict(issued_utc=t1, noaa=13413, area=100, z='Dso', ll=5, nn=5, mag_type='Beta'),
        dict(issued_utc=t2, noaa=13413, area=150, z='Eki', ll=8, nn=12, mag_type='Beta-Gamma-Delta'),
        dict(issued_utc=t2, noaa=13417, area=80, z='Hsx', ll=2, nn=1, mag_type='Alpha'),
    ])


def test_feature_table_encodes_classes_and_counts_earlier_listings():
    table = srs_feature_table(rows()).set_index(['issued_utc', 'noaa'])
    second = table.loc[(pd.Timestamp('2023-09-03 00:30', tz='UTC'), 13413)]
    assert second.mag_rank == 4 and second.has_delta == 1 and second.has_gamma == 1
    assert second.zurich_rank == 4 and second.penumbra_rank == 5 and second.compact_rank == 2
    assert second.srs_history_days == 1
    first = table.loc[(pd.Timestamp('2023-09-02 00:30', tz='UTC'), 13413)]
    assert first.srs_history_days == 0 and first.has_delta == 0


def test_attach_context_uses_available_srs_and_marks_absence():
    table = srs_feature_table(rows())
    issued = pd.DataFrame({'issued_utc': sorted(table.issued_utc.unique())})
    mapping = pd.DataFrame({'harp': [1, 1, 2], 'date': [pd.Timestamp('2023-09-03').date()]*3, 'noaa': [13413, 13417, 99999]})
    frame = pd.DataFrame({'harp': [1, 1, 2, 3],
                          'forecast_time': pd.to_datetime(['2023-09-03 06:00', '2023-09-03 00:45', '2023-09-03 06:00', '2023-09-03 06:00'], utc=True)})
    out = attach_context(frame, mapping, issued, table)
    assert list(out.columns) == CONTEXT
    # HARP 1 at 06:00 sees the 03 Sep SRS with two regions
    assert out.srs_available[0] == 1 and out.n_regions[0] == 2 and out.mag_rank[0] == 4 and out.has_delta[0] == 1
    assert np.isclose(out.area_log[0], np.log1p(230)) and out.extent_max[0] == 8 and out.srs_history_days[0] == 1
    assert np.isclose(out.hours_since_issue[0], 5.5)
    # HARP 1 at 00:45 is inside the 30 minute margin: only the 02 Sep SRS is available, 13417 is not listed there
    assert out.n_regions[1] == 1 and out.mag_rank[1] == 1 and out.srs_history_days[1] == 0
    # HARP 2 has a NOAA number absent from the SRS, HARP 3 has no number: absence, not quiet
    assert out.srs_available[2] == 0 and out.srs_available[3] == 0
    assert out.loc[2, CONTEXT[1:]].isna().all() and out.loc[3, CONTEXT[1:]].isna().all()
