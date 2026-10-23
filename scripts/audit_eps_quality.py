"""Audit pinned upstream EPS behavior and the frozen historical quality windows."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from helio24.data import ROOT, MAGNETIC_COLUMNS, parse_name, read_observation
from helio24.full_data import sha256
from helio24.quality_audit import header_frame

COMMIT = '9f6e805d19077ab44d0ed8d2b546f207a8f155f7'
MODULE = 'py_src/swdatatoolkit/magparam/_lorentz_calculator.py'


def run():
    repository = ROOT / 'data/toolkit_source'
    revision = subprocess.check_output(['git', '-C', str(repository), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != COMMIT:
        raise ValueError('Unexpected upstream revision')
    source = repository / MODULE
    committed = subprocess.check_output(['git', '-C', str(repository), 'show', f'{COMMIT}:{MODULE}'])
    if source.read_bytes() != committed:
        raise ValueError('Upstream calculator changed locally')
    # Only this inspected, self-contained calculator is loaded; no package installation.
    spec = importlib.util.spec_from_file_location('reviewed_lorentz', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fields = [np.ma.array([[v]], mask=False) for v in [3., 4., 5.]]
    errors = [np.ma.array([[0.]], mask=False) for _ in range(3)]
    first = module.LorentzCalculator.calc(*fields, *errors, 6.96e8, 960., .5).iloc[0]
    second = module.LorentzCalculator.calc(*fields, *errors, 6.96e8, 960., 1.).iloc[0]
    experiment = {k: dict(base=float(first[k]), double_plate_scale=float(second[k]),
                          ratio=float(second[k]/first[k]) if first[k] else None)
                  for k in ['TOTBSQ', 'TOTFX', 'TOTFY', 'EPSX', 'EPSY', 'EPSZ']}
    if not np.isclose(experiment['EPSX']['ratio'], 4) or not np.isclose(experiment['TOTBSQ']['ratio'], 1):
        raise ValueError('Pinned EPS behavior changed')
    manifest_path = ROOT / 'data/quality_sources/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    overlap_path = ROOT / 'artifacts/v2_overlap/report.json'
    if sha256(overlap_path) != manifest['selection_sha256']:
        raise ValueError('Historical selection changed')
    overlap = json.loads(overlap_path.read_text())
    for name, digest in overlap['source_hashes'].items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f'Historical source changed: {name}')
    sample = pd.read_parquet(ROOT / 'data/compatibility_probe/first_member.parquet',
                             columns=['harp_number', 'obs_start', *[c.lower() for c in MAGNETIC_COLUMNS]],
                             filters=[('obs_start', '<', pd.Timestamp('2019-01-01'))]).drop_duplicates()
    if sample.duplicated(['harp_number', 'obs_start']).any():
        raise ValueError('Conflicting V2 timestamps')
    rows, frames, source_hashes = [], [], {}
    for selection in overlap['selected']:
        harp = selection['harp']
        item = next(s for s in manifest['sources'] if s['harp'] == harp)
        if item['status'] != 'downloaded':
            raise ValueError(f'Missing JSOC source: {harp}')
        path = manifest_path.parent / item['file']
        if sha256(path) != item['sha256']:
            raise ValueError('JSOC snapshot changed')
        source_hashes[str(path.relative_to(ROOT))] = sha256(path)
        header = header_frame(json.loads(path.read_text()), harp)
        original_path = ROOT / selection['source']
        old = read_observation(original_path, parse_name(original_path), magnetic_only=True)
        frame = old.merge(header[['Timestamp', 'source_quality', 'observation_clock']], on='Timestamp',
                          how='left', validate='one_to_one')
        new = sample[sample.harp_number.eq(harp)].rename(columns={'obs_start': 'Timestamp'})
        frame = frame.merge(new, on='Timestamp', how='left', validate='one_to_one')
        frame['old_quality'] = pd.to_numeric(frame.QUALITY, errors='coerce')
        frame['tmfi'] = frame.IS_TMFI.astype(str).str.lower().isin(['true', '1', '1.0'])
        frame['old_pass'] = frame.old_quality.eq(0) & frame.tmfi
        frame['source_quality_pass'] = frame.source_quality.eq(0).fillna(False)
        frame['v2_all_finite'] = np.isfinite(frame[[c.lower() for c in MAGNETIC_COLUMNS]].to_numpy(dtype=float)).all(axis=1)
        offsets = (frame.Timestamp-frame.observation_clock).dt.total_seconds().dropna()
        row = dict(harp=harp, expected=len(old), matched_headers=int(frame.source_quality.notna().sum()),
                   quality_equal=int(frame.old_quality.eq(frame.source_quality).fillna(False).sum()),
                   old_pass=int(frame.old_pass.sum()), source_quality_pass=int(frame.source_quality_pass.sum()),
                   tmfi_false=int((~frame.tmfi).sum()), v2_finite=int(frame.v2_all_finite.sum()),
                   v2_finite_quality_rejected=int((frame.v2_all_finite & ~frame.source_quality_pass).sum()),
                   missing_quality=int(frame.source_quality.isna().sum()),
                   rec_minus_obs_min=float(offsets.min()) if len(offsets) else None,
                   rec_minus_obs_max=float(offsets.max()) if len(offsets) else None)
        rows.append(row)
        frames.append(frame[['Timestamp', 'old_quality', 'source_quality', 'tmfi', 'old_pass',
                             'source_quality_pass', 'v2_all_finite', 'observation_clock']].assign(harp=harp))
    output = ROOT / 'artifacts/eps_quality_audit'
    output.mkdir(exist_ok=False)
    pd.DataFrame(rows).to_csv(output / 'summary.csv', index=False)
    pd.concat(frames).to_csv(output / 'aligned_quality.csv', index=False)
    report = dict(ready_for_model=False, upstream_commit=revision, upstream_module=MODULE,
                  upstream_module_sha256=sha256(source), upstream_remote='https://bitbucket.org/gsudmlab/spaceweather_toolkit',
                  release_commit_verified=False, synthetic_diagnostic=experiment, quality_summary=rows,
                  scope='Five frozen 2011 windows; no flare outcomes or future test data; clock-as-TAI alignment only',
                  unresolved=['V2 production revision', 'V2 timestamp scale', 'IS_TMFI reproduction', 'label policy'],
                  sources=source_hashes | {str(manifest_path.relative_to(ROOT)): sha256(manifest_path),
                                           str(overlap_path.relative_to(ROOT)): sha256(overlap_path)},
                  code_hashes={p: sha256(ROOT / p) for p in ['scripts/audit_eps_quality.py', 'helio24/quality_audit.py']},
                  artifact_hashes={p.name: sha256(p) for p in output.glob('*.csv')})
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(dict(synthetic_diagnostic=experiment, quality_summary=rows), indent=2))


if __name__ == '__main__':
    run()
