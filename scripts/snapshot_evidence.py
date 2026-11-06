"""Copy explicit experiment directories into a new verified local snapshot.

Unavailable files are recorded, never silently treated as backed up.
Use a destination outside Desktop, Documents and iCloud Drive.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def snapshot(root, folders, output):
    root, output = root.resolve(), output.resolve()
    home = Path.home()
    for cloud in [home/'Desktop', home/'Documents', home/'Library/Mobile Documents']:
        if output.is_relative_to(cloud.resolve()):
            raise ValueError('Snapshot destination must be outside iCloud-managed folders')
    sources = []
    for name in folders:
        folder = (root/name).resolve()
        if not folder.is_relative_to(root) or not folder.is_dir():
            raise ValueError(f'Invalid source folder: {name}')
        if output.is_relative_to(folder):
            raise ValueError('Snapshot cannot be inside a source folder')
        sources.append(folder)
    output.mkdir(parents=True, exist_ok=False)
    copied, unavailable = {}, []
    for folder in sources:
        expected = {}
        report = folder/'report.json'
        if report.exists() and not report.stat().st_flags & 0x40000000:
            expected = json.loads(report.read_text()).get('artifact_hashes', {})
        for name in expected:
            if not (folder/name).exists():
                unavailable.append({'path':str((folder/name).relative_to(root)), 'reason':'missing'})
        for source in sorted(folder.rglob('*')):
            if source.is_symlink():
                unavailable.append({'path':str(source.relative_to(root)), 'reason':'symlink'})
                continue
            if not source.is_file():
                continue
            rel = source.relative_to(root)
            if source.stat().st_flags & 0x40000000:
                unavailable.append({'path':str(rel), 'reason':'cloud_placeholder'})
                continue
            before = digest(source)
            original = expected.get(str(source.relative_to(folder)))
            if original and before != original:
                raise ValueError(f'Frozen artifact hash mismatch: {rel}')
            target = output/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if sys.platform == 'darwin':
                subprocess.run(['/bin/cp', '-c', str(source), str(target)], check=True)
            else:
                shutil.copyfile(source, target)
            if digest(target) != before or digest(source) != before:
                raise ValueError(f'Snapshot verification failed: {rel}')
            target.chmod(0o444)
            copied[str(rel)] = before
    manifest = {'complete':not unavailable, 'artifact_hashes':copied, 'unavailable':unavailable,
                'scope':folders, 'source':str(root), 'same_disk_backup':True}
    (output/'snapshot.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'copied':len(copied), 'unavailable':unavailable, 'output':str(output)}, indent=2))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--folder', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    snapshot(args.root, args.folder, args.output)
