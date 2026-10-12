"""Preserve experiment 1 before running another experiment."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def freeze():
    source = ROOT / 'artifacts'
    target = source / 'experiment1'
    manifest = target / 'snapshot.json'
    if manifest.exists():
        hashes = json.loads(manifest.read_text())
        for name, digest in hashes.items():
            if hashlib.sha256((target / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f'Frozen file changed: {name}')
        print('Existing experiment 1 snapshot verified; no files replaced.')
        return
    for name in ['report.json', 'model.joblib', 'predictions.parquet']:
        if not (source / name).exists():
            raise ValueError('Run the first experiment before freezing its results')
    target.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for path in source.iterdir():
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        destination = target / path.name
        if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Refusing to replace frozen file: {path.name}')
        if not destination.exists():
            shutil.copy2(path, destination)
        hashes[path.name] = digest
    manifest.write_text(json.dumps(hashes, indent=2))
    print(f'Experiment 1 frozen: {len(hashes)} files.')


if __name__ == '__main__':
    freeze()
