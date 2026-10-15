import pandas as pd
import pytest

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


def test_investigation_preserves_disagreeing_archive_methods(tmp_path, capsys):
    import hashlib
    import io
    import json
    import shutil
    import tarfile
    from helio24.data import ROOT
    from scripts.investigate_event_provenance import run

    for folder in ['data/downloads', 'artifacts/event_audit', 'helio24', 'scripts']:
        (tmp_path / folder).mkdir(parents=True)
    for name in ['helio24/provenance.py', 'helio24/event_mapping.py', 'helio24/data.py',
                 'scripts/investigate_event_provenance.py']:
        shutil.copyfile(ROOT / name, tmp_path / name)
    (tmp_path / 'artifacts/event_audit/report.json').write_text('{}')
    pd.DataFrame([dict(flare_id=8864, goes_class='M2.5', peak_time='2014-09-03 13:54')]).to_csv(
        tmp_path / 'data/flare_catalog.csv', index=False)
    archive = tmp_path / 'data/downloads/partition4_instances.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for harp, column in [(4502, 'MFLARE_LABEL_LOC'), (4503, 'MFLARE_LABEL')]:
            row = dict(Timestamp='2014-09-03 13:48', MFLARE_LABEL=None, XFLARE_LABEL=None,
                       MFLARE_LABEL_LOC=None, XFLARE_LABEL_LOC=None, LAT_MIN=-20, LAT_MAX=-10,
                       LON_MIN=10, LON_MAX=30, IS_TMFI=True, QUALITY=0)
            row[column] = 'M2.5@8864:Primary'
            payload = pd.DataFrame([row]).to_csv(sep='\t', index=False).encode()
            member = tarfile.TarInfo(f'FQ_ar{harp}_s2014-09-03T06:00:00_e2014-09-03T17:48:00.csv')
            member.size = len(payload)
            tar.addfile(member, io.BytesIO(payload))
    metadata = dict(data=dict(latestVersion=dict(files=[dict(dataFile=dict(
        filename=archive.name, checksum=dict(value=hashlib.md5(archive.read_bytes()).hexdigest())))])))
    (tmp_path / 'data/dataverse-metadata.json').write_text(json.dumps(metadata))
    run(tmp_path)
    report = json.loads((tmp_path / 'artifacts/event_provenance/report.json').read_text())
    assert report['inspected'] == 2
    assert [x['association_method'] for x in report['case_associations']] == ['location_only', 'noaa_only']
    assert report['case_filename_harps'] == []
    assert report['case_region_forecasts_covering_peak'] == 0
    assert (tmp_path / 'artifacts/event_audit/report.json').read_text() == '{}'
    from helio24.event_views import load_investigation
    assert load_investigation(tmp_path) == report
    (tmp_path / 'artifacts/event_provenance/associations.csv').write_text('changed')
    with pytest.raises(ValueError, match='evidence changed'):
        load_investigation(tmp_path)
