"""Check cached V2 schema without reading target values or scoring any model."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.compatibility import inspect_columns
from helio24.data import ROOT
from helio24.full_data import sha256


def run(root=ROOT):
    source = root / 'data/compatibility_probe'
    output = root / 'artifacts/v2_compatibility'
    if output.exists():
        raise RuntimeError('Preserve the existing compatibility assessment')
    snapshot = json.loads((source / 'schema.json').read_text())
    if sha256(source / 'first_member.parquet') != snapshot['member_sha256']:
        raise ValueError('Compatibility sample changed')
    report = inspect_columns(snapshot['columns'])
    report.update(scope='Schema-only assessment; no label values or model performance inspected',
                  source_hashes={str(p.relative_to(root)): sha256(p) for p in [
                      source / 'schema.json', source / 'first_member.parquet']},
                  code_hashes={name: sha256(root / name) for name in [
                      'helio24/compatibility.py', 'scripts/check_v2_compatibility.py']})
    output.mkdir(parents=True)
    (output / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    run()
