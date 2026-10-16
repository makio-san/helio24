"""Bounded old-period measurement check; never read V2 flare labels or score models."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from helio24.data import ROOT, MAGNETIC_COLUMNS, parse_name, read_observation
from helio24.full_data import sha256


def run(root=ROOT):
    source = root / 'data/compatibility_probe/first_member.parquet'
    output = root / 'artifacts/v2_overlap'
    if output.exists():
        raise RuntimeError('Preserve the existing overlap audit')
    schema_path = source.parent / 'schema.json'
    schema = json.loads(schema_path.read_text())
    if sha256(source) != schema['member_sha256']:
        raise ValueError('V2 sample changed')
    # Explicit column projection prevents outcome data from being loaded.
    columns = [name.lower() for name in MAGNETIC_COLUMNS]
    sample = pd.read_parquet(source, columns=['harp_number', 'obs_start', *columns],
                             filters=[('obs_start', '<', pd.Timestamp('2019-01-01'))])
    sample = sample.rename(columns={'harp_number': 'harp', 'obs_start': 'Timestamp',
                                    **dict(zip(columns, MAGNETIC_COLUMNS))}).drop_duplicates()
    if sample.duplicated(['harp', 'Timestamp']).any():
        raise ValueError('Conflicting measurements at the same HARP/time')
    coverage = sample.groupby('harp').Timestamp.agg(['min', 'max'])
    candidates = []
    for path in (root / 'data/raw').glob('partition*/*.csv'):
        meta = parse_name(path)
        harp = meta['harp']
        if (harp in coverage.index and meta['observation_start'] >= coverage.loc[harp, 'min'] and
                meta['observation_last'] <= coverage.loc[harp, 'max'] and
                meta['observation_last'] < pd.Timestamp('2019-01-01')):
            candidates.append((harp, meta['observation_start'], path, meta))
    pairs, selected, seen = [], [], set()
    for harp, stamp, path, meta in sorted(candidates, key=lambda item: (item[0], item[1])):
        if harp in seen:
            continue
        old = read_observation(path, meta, magnetic_only=True)
        new = sample[sample.harp.eq(harp)]
        joined = old.merge(new, on='Timestamp', suffixes=('_v1', '_v2'), validate='one_to_one')
        if joined.empty:
            continue
        seen.add(harp)
        selected.append(dict(harp=harp, source=str(path.relative_to(root)), sha256=sha256(path),
                             observation_start=str(stamp), matched_samples=len(joined)))
        for name in MAGNETIC_COLUMNS:
            left = pd.to_numeric(joined[name+'_v1'], errors='coerce').to_numpy(dtype=float)
            right = pd.to_numeric(joined[name+'_v2'], errors='coerce').to_numpy(dtype=float)
            finite = np.isfinite(left) & np.isfinite(right)
            close = np.isclose(left, right, rtol=1e-5, atol=1e-8, equal_nan=True)
            trusted = joined.IS_TMFI.astype(str).str.lower().isin(['true', '1', '1.0']) & joined.QUALITY.eq(0)
            pairs.append(dict(harp=harp, measurement=name, samples=len(joined), both_finite=int(finite.sum()),
                              close_samples=int(close.sum()), old_trusted_samples=int(trusted.sum()),
                              max_absolute_difference=float(np.abs(left[finite]-right[finite]).max()) if finite.any() else None))
        if len(selected) == 5:
            break
    if not selected:
        raise ValueError('No old-period overlap found in the bounded local sample')
    output.mkdir(parents=True)
    pd.DataFrame(pairs).to_csv(output / 'measurement_comparison.csv', index=False)
    report = dict(scope='Up to five old-period HARP windows; no V2 outcomes or model scores read',
                  selection='First overlapping window per HARP, ascending HARP and observation time',
                  timestamp_match='Identical naive clock strings only; UTC/TAI equivalence is not established',
                  tolerance=dict(rtol=1e-5, atol=1e-8), selected=selected,
                  matched_samples=sum(row['matched_samples'] for row in selected),
                  numeric_comparisons=sum(row['samples'] for row in pairs),
                  close_comparisons=sum(row['close_samples'] for row in pairs),
                  ready_for_model=False,
                  source_hashes={str(p.relative_to(root)): sha256(p) for p in [source, schema_path]} |
                  {row['source']: row['sha256'] for row in selected},
                  code_hashes={'scripts/audit_v2_overlap.py': sha256(root / 'scripts/audit_v2_overlap.py')},
                  artifact_hashes={'measurement_comparison.csv': sha256(output / 'measurement_comparison.csv')})
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps({k: v for k, v in report.items() if k not in ['source_hashes', 'code_hashes']}, indent=2))
    return report


if __name__ == '__main__':
    run()
