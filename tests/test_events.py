import numpy as np
import pandas as pd
import pytest

from helio24.event_mapping import parse_annotations
from helio24.events import alarm_episodes, match_events


def windows(hours, probabilities, targets=None):
    stamps = pd.Timestamp('2014-01-01')+pd.to_timedelta(hours, unit='h')
    return pd.DataFrame(dict(harp=1, forecast_time=stamps, prediction_end=stamps+pd.Timedelta(hours=24),
                             probability=probabilities, target=targets or [0]*len(hours), missing_fraction=0.))


def test_episodes_stop_at_quiet_windows_gaps_and_region_boundaries():
    frame = windows([0, 1, 2, 4, 5, 6], [.5, .8, .1, .9, .9, .1], [0, 1, 0, 0, 0, 0])
    frame = pd.concat([frame, windows([0], [.9]).assign(harp=2)])
    states, runs = alarm_episodes(frame, .5)
    assert runs.windows.tolist() == [2, 2, 1]
    assert runs.state_hours.tolist() == [2, 2, 1]
    assert runs.false_hours.tolist() == [1, 2, 1]
    assert runs.all_negative.tolist() == [False, True, True]
    assert runs.left_censored.tolist() == [True, True, True]
    assert runs.right_censored.tolist() == [False, False, True]
    assert states.state_hours.sum() == 7
    with pytest.raises(ValueError, match='Duplicate'):
        alarm_episodes(pd.concat([frame, frame]), .5)


def test_event_boundaries_deduplication_and_pre_start_warning():
    states, _ = alarm_episodes(windows([0, 1, 23, 24], [.9, .1, .9, .9]), .5)
    mapping = pd.DataFrame(dict(harp=[1, 1, 1, 2], flare_id=[1, 2, 3, 3], evidence='filename'))
    catalog = pd.DataFrame(dict(flare_id=[1, 2, 3, 4], goes_class='M1.0',
        start_time=pd.to_datetime(['2014-01-01 22:00', '2014-01-01 23:30', '2014-01-01 22:00', '2014-01-01 22:00']),
        peak_time=pd.to_datetime(['2014-01-02', '2014-01-02', '2014-01-02', '2014-01-02'])))
    events = match_events(states, mapping, catalog).set_index('flare_id')
    assert events.loc[1, 'alarm_windows'] == 2  # t=0 at exactly 24h lead is excluded.
    assert events.loc[1, 'available_forecasts'] == 3
    assert events.loc[1, 'detected'] and not events.loc[1, 'before_start']
    assert events.loc[1, 'peak_lead_hours'] == 1
    assert events.loc[2, 'before_start'] and events.loc[2, 'start_lead_hours'] == .5
    assert events.loc[3, 'status'] == 'ambiguous'
    assert events.loc[4, 'status'] == 'unmapped'
    assert events.loc[1, 'coverage_hours'] == 3


def test_full_coverage_and_missing_data_are_distinct_from_misses():
    states, _ = alarm_episodes(windows(list(range(25)), [0.]*25), .5)
    catalog = pd.DataFrame(dict(flare_id=[1, 2], goes_class='X1.0',
        start_time=pd.to_datetime(['2014-01-01 23:50']*2), peak_time=pd.to_datetime(['2014-01-02']*2)))
    mapping = pd.DataFrame(dict(harp=[1, 99], flare_id=[1, 2], evidence='history_location'))
    events = match_events(states, mapping, catalog).set_index('flare_id')
    assert events.loc[1, 'fully_covered'] and not events.loc[1, 'detected']
    assert events.loc[2, 'status'] == 'no_forecast_coverage'
    _, no_alarms = alarm_episodes(windows([0], [0.]), .5)
    assert no_alarms.empty


def test_annotation_parser_accepts_verified_lists_and_fails_closed():
    assert parse_annotations('[M1.0@12:Primary; X2.0@13:Secondary]') == [
        ('M1.0', 12, 'Primary'), ('X2.0', 13, 'Secondary')]
    assert parse_annotations(np.nan) == []
    with pytest.raises(ValueError, match='Unrecognized'):
        parse_annotations('M1.0@12:Primary unexpected payload')


def test_archive_mapping_verifies_catalog_time_and_detects_ambiguity(tmp_path):
    import hashlib
    import io
    import json
    import tarfile
    from helio24.event_mapping import prepare_mapping

    (tmp_path / 'data/downloads').mkdir(parents=True)
    (tmp_path / 'helio24').mkdir()
    (tmp_path / 'helio24/data.py').write_text('fixture')
    pd.DataFrame(dict(flare_id=[1, 2], goes_class=['M1.0', 'X1.0'],
                      peak_time=['2014-01-01 01:00', '2014-01-01 01:07'])).to_csv(
                          tmp_path / 'data/flare_catalog.csv', index=False)
    archive = tmp_path / 'data/downloads/partition4_instances.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for harp in [1, 2]:
            payload = pd.DataFrame(dict(Timestamp=['2014-01-01 01:00'],
                                        MFLARE_LABEL_LOC=['M1.0@1:Primary'],
                                        XFLARE_LABEL_LOC=['X1.0@2:Secondary'])).to_csv(sep='\t', index=False).encode()
            member = tarfile.TarInfo(f'FQ_ar{harp}_s2014-01-01T00:00:00_e2014-01-01T11:48:00.csv')
            member.size = len(payload)
            tar.addfile(member, io.BytesIO(payload))
    info = dict(data=dict(latestVersion=dict(files=[dict(dataFile=dict(
        filename=archive.name, checksum=dict(value=hashlib.md5(archive.read_bytes()).hexdigest())))])))
    (tmp_path / 'data/dataverse-metadata.json').write_text(json.dumps(info))
    audit = prepare_mapping(tmp_path)
    assert audit['rejected'] == 2 and audit['associations'] == 2
    mapping = pd.read_csv(tmp_path / 'data/event_mapping/associations.csv')
    assert mapping.ambiguous.all()
    assert prepare_mapping(tmp_path) == audit
    archive.write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='checksum'):
        prepare_mapping(tmp_path)


def test_timeline_keeps_gaps_and_hides_peaks_until_revealed():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from helio24.event_views import timeline

    frame = windows([0, 1, 4], [.9, .9, .1]).assign(USFLUX__last=[1., np.nan, 3.])
    states, runs = alarm_episodes(frame, .5)
    events = pd.DataFrame(dict(harp=[1], status=['evaluated'],
                               peak_time=[pd.Timestamp('2014-01-01 03:00')], goes_class=['M1.0']))
    hidden = timeline(states, runs, events, 1, .5)
    assert len(hidden.axes[0].lines) == 3  # Two disjoint steps and one threshold.
    assert len(hidden.axes[1].lines) == 2
    assert np.isnan(hidden.axes[1].lines[0].get_ydata()[1])
    assert len(hidden.axes[0].texts) == 0
    shown = timeline(states, runs, events, 1, .5, reveal=True)
    assert len(shown.axes[0].lines) == 4
    assert len(shown.axes[0].texts) == 1
    plt.close(hidden)
    plt.close(shown)
