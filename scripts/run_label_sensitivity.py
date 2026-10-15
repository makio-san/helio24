"""Run the fixed six-variant association study without refitting or relabeling."""
from html import escape
from importlib.metadata import version
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.sensitivity import assert_reference, compare, verify_report


def render_html(report, tables, protocol):
    metrics = tables['metrics'].copy()
    for column in ['recall', 'fully_covered_recall', 'common_recall']:
        metrics[column] = metrics[column].map(lambda x: f'{x:.2%}' if pd.notna(x) else 'Not evaluated')
    changed = tables['transitions'].query('changed')
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<title>Helio24 — label association sensitivity</title>'
            '<style>body{font:16px system-ui;margin:2rem;color:#172b3a}table{border-collapse:collapse;'
            'font-size:13px}td,th{padding:8px;border:1px solid #ccd5da}pre{white-space:pre-wrap}'
            '.table{overflow:auto}h1{font-size:26px}</style>'
            '<h1>Helio24 · label association sensitivity</h1>'
            '<p>Partition-4 development analysis. Probabilities, thresholds and benchmark labels are fixed. '
            'Conditional event recall is not final-test performance or complete solar-event coverage.</p>'
            f'<p>{report["windows"]:,} windows; threshold {report["threshold"]:.6%}; '
            f'{report["false_alarm_region_hours"]:,.0f} benchmark false-alarm region-hours in every variant.</p>'
            '<p>Every variant includes positive filename evidence. The two timing rules change only which '
            'history annotations qualify; catalog peak times stay fixed. Ambiguous events are excluded. '
            'Common-event recall uses events assigned to the same HARP in all six variants.</p>'
            '<h2>Comparison</h2><div class="table">'+metrics.to_html(index=False, border=0)+'</div>'
            '<h2>Changes from nearest_location</h2><div class="table">'+changed.to_html(index=False, border=0)+'</div>'
            '<p>Negative-label conflicts count event/window pairs, not unique flares. '
            'Association changes do not establish physical truth or justify automatic relabeling.</p>'
            '<details><summary>Frozen protocol</summary><pre>'+escape(protocol)+'</pre></details></html>')


def run(root=ROOT):
    output = root / 'artifacts/label_sensitivity'
    if output.exists():
        raise RuntimeError('Preserve the existing sensitivity run before rerunning')
    audit_dir = root / 'artifacts/event_audit'
    provenance_dir = root / 'artifacts/event_provenance'
    audit = verify_report(root, audit_dir, check_code=True)
    verify_report(root, provenance_dir, check_code=True)
    windows = pd.read_parquet(audit_dir / 'windows.parquet')
    if not windows.alarm.eq(windows.probability.ge(audit['threshold'])).all():
        raise ValueError('Frozen alarm states differ from probabilities and threshold')
    tables = compare(windows, pd.read_csv(provenance_dir / 'annotations.csv'),
                     pd.read_csv(provenance_dir / 'filenames.csv'), pd.read_csv(root / 'data/flare_catalog.csv'))
    assert_reference(tables['events'], pd.read_csv(audit_dir / 'events.csv'))
    false_hours = float(windows.loc[windows.alarm & windows.target.eq(0), 'state_hours'].sum())
    if false_hours != audit['false_alarm_region_hours']:
        raise ValueError('Benchmark alarm burden changed')
    paths = [audit_dir / name for name in ['report.json', 'windows.parquet', 'events.csv']]
    paths += [provenance_dir / name for name in ['report.json', 'annotations.csv', 'filenames.csv']]
    paths += [root / 'data/flare_catalog.csv', root / 'docs/label-sensitivity-protocol.md']
    report = dict(scope='Fixed partition-4 development association sensitivity; no model change or new test',
                  threshold=audit['threshold'], windows=len(windows),
                  false_alarm_region_hours=false_hours, reference_reproduced=True,
                  source_hashes={str(p.relative_to(root)): sha256(p) for p in paths},
                  code_hashes={name: sha256(root / name) for name in [
                      'helio24/sensitivity.py', 'helio24/events.py', 'helio24/event_mapping.py',
                      'scripts/run_label_sensitivity.py']},
                  versions={name: version(name) for name in ['pandas', 'numpy', 'pyarrow']})
    protocol = (root / 'docs/label-sensitivity-protocol.md').read_text()
    output.mkdir(parents=True)
    for name, frame in tables.items():
        frame.to_csv(output / (name+'.csv'), index=False)
    (output / 'protocol.md').write_text(protocol)
    (output / 'report.html').write_text(render_html(report, tables, protocol))
    report['artifact_hashes'] = {p.name: sha256(p) for p in output.iterdir()}
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(tables['metrics'].to_string(index=False))
    return report


if __name__ == '__main__':
    run()
