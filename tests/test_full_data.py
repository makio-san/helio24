import hashlib
import io
import json
from pathlib import Path
import tarfile

import numpy as np
import pandas as pd
import pytest

from helio24 import full_data
from helio24.data import MAGNETIC_COLUMNS


def test_archive_preparation_validates_and_caches_without_extracting_raw_files(tmp_path, monkeypatch):
    (tmp_path / 'data/downloads').mkdir(parents=True)
    (tmp_path / 'helio24').mkdir()
    (tmp_path / 'helio24/data.py').write_text('test feature implementation fingerprint')
    pd.DataFrame([dict(flare_id=1, peak_time='2011-01-01 15:00:00', goes_class='M1.0')]).to_csv(tmp_path / 'data/flare_catalog.csv', index=False)
    archive = tmp_path / 'data/downloads/partition1_instances.tar.gz'
    frame = pd.DataFrame({**{name: np.arange(60, dtype=float) for name in MAGNETIC_COLUMNS},
                          'Timestamp': pd.date_range('2011-01-01', periods=60, freq='12min'),
                          'QUALITY': 0, 'IS_TMFI': True})
    with tarfile.open(archive, 'w:gz') as tar:
        for i, label in enumerate(['FQ', 'M1.0@1:Primary', 'FQ']):
            record = frame.copy()
            if i == 2:
                record['QUALITY'] = 1
            payload = record.to_csv(sep='\t', index=False).encode()
            member = tarfile.TarInfo(f'partition1/{label}_ar{i}_s2011-01-01T00:00:00_e2011-01-01T11:48:00.csv')
            member.size = len(payload)
            tar.addfile(member, io.BytesIO(payload))
    metadata = {'data': {'latestVersion': {'files': [{'dataFile': {'filename': archive.name, 'checksum': {'value': hashlib.md5(archive.read_bytes()).hexdigest()}}}]}}}
    (tmp_path / 'data/dataverse-metadata.json').write_text(json.dumps(metadata))
    monkeypatch.setattr(full_data, 'ROOT', tmp_path)
    audit = full_data.prepare_partition(1)
    assert (audit['inspected'], audit['accepted'], audit['excluded']) == (3, 2, 1)
    assert not (tmp_path / 'data/raw').exists()
    stored = pd.read_parquet(tmp_path / 'data/full/partition1.parquet')
    assert stored.target.tolist() == [0, 1]
    assert full_data.prepare_partition(1) == audit
    archive.write_bytes(b'corrupt archive')
    with pytest.raises(ValueError, match='checksum'):
        full_data.prepare_partition(1)
