"""Trace the frozen five-window overlap without changing training features."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT, MAGNETIC_COLUMNS, parse_name, read_observation
from helio24.full_data import sha256
from helio24.measurement_audit import compare_values, force_hypotheses, safe_ratio


def run():
    output = ROOT / 'artifacts/measurement_trace'
    output.mkdir(exist_ok=False)
    overlap_path = ROOT / 'artifacts/v2_overlap/report.json'
    overlap = json.loads(overlap_path.read_text())
    for name, digest in overlap['source_hashes'].items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f'Frozen source changed: {name}')
    sample = pd.read_parquet(ROOT / 'data/compatibility_probe/first_member.parquet',
                             columns=['harp_number', 'obs_start', *[c.lower() for c in MAGNETIC_COLUMNS]],
                             filters=[('obs_start', '<', pd.Timestamp('2019-01-01'))]).drop_duplicates()
    if sample.duplicated(['harp_number', 'obs_start']).any():
        raise ValueError('Conflicting HARP/time measurements')
    rows, headers = [], []
    manifest_path = ROOT / 'data/measurement_sources/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for selected in overlap['selected']:
        path = ROOT / selected['source']
        old = read_observation(path, parse_name(path), magnetic_only=True)
        new = sample[sample.harp_number.eq(selected['harp'])].rename(columns={'obs_start': 'Timestamp'})
        joined = old.merge(new, on='Timestamp', validate='one_to_one')
        if len(joined) != selected['matched_samples']:
            raise ValueError('Frozen timestamp alignment changed')
        trusted = joined.IS_TMFI.astype(str).str.lower().isin(['true', '1', '1.0']) & joined.QUALITY.eq(0)
        for subset, group in [('all', joined), ('old_quality_pass', joined[trusted])]:
            def append(kind, variable, reference, candidate):
                rows.append(dict(harp=selected['harp'], subset=subset, check=kind, measurement=variable,
                                 **compare_values(reference, candidate)))
            for column in MAGNETIC_COLUMNS:
                append('identity', column, group[column], group[column.lower()])
            for column, hypothesis in force_hypotheses(group).items():
                append('fixed_force_factor', column, hypothesis, group[column.lower()])
            for axis in ['x', 'y', 'z']:
                append('v2_force_over_totbsq', 'eps'+axis,
                       safe_ratio(group['totf'+axis], group.totbsq), group['eps'+axis])
        source = next(s for s in manifest['sources'] if s['harp'] == selected['harp'])
        if source['status'] != 'downloaded':
            continue
        source_path = manifest_path.parent / source['file']
        if sha256(source_path) != source['sha256']:
            raise ValueError('JSOC snapshot changed')
        payload = json.loads(source_path.read_text())
        if payload.get('status') != 0 or payload.get('count') != 1:
            raise ValueError('Expected exactly one successful JSOC record')
        values = {k['name']: k['values'][0] for k in payload['keywords']}
        first = joined[joined.Timestamp.eq(pd.Timestamp(selected['observation_start']))].iloc[0]
        for column in ['USFLUX', 'MEANPOT', 'TOTPOT', 'MEANSHR', 'SHRGT45']:
            raw = values[column]
            value = None if raw in ['MISSING', 'NaN'] else float(raw)
            headers.append(dict(harp=selected['harp'], clock=selected['observation_start'],
                                t_rec=values['T_REC'], t_obs=values['T_OBS'], quality=values['QUALITY'],
                                transport=source['transport'], measurement=column,
                                v1=float(first[column]), v2=float(first[column.lower()]), jsoc=value))
    pd.DataFrame(rows).to_csv(output / 'diagnostics.csv', index=False)
    pd.DataFrame(headers).to_csv(output / 'source_headers.csv', index=False)
    report = dict(scope='Frozen five old-period windows; clock-as-TAI source query, no time-scale equivalence claim',
                  ready_for_model=False, hypotheses='Fixed 1/(4pi), -1/(4pi), 1/(8pi) force factors; EPS=force/TOTBSQ. Diagnostic only.',
                  tolerance=dict(rtol=1e-5, atol=1e-8), checks=rows, source_headers=headers,
                  unresolved=['causal calculation provenance', 'quality equivalence', 'time scale', 'labels and inclusion rules'],
                  sources={str(overlap_path.relative_to(ROOT)): sha256(overlap_path),
                           str(manifest_path.relative_to(ROOT)): sha256(manifest_path)},
                  code_hashes={p: sha256(ROOT / p) for p in ['helio24/measurement_audit.py', 'scripts/trace_measurement_differences.py']},
                  artifact_hashes={p: sha256(output / p) for p in ['diagnostics.csv', 'source_headers.csv']})
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    frame = pd.DataFrame(rows).query('subset == "all"')
    print(frame.groupby(['check', 'measurement'])[['finite_pairs', 'close_finite']].sum().to_string())
    print(pd.DataFrame(headers).to_string(index=False))


if __name__ == '__main__':
    run()
