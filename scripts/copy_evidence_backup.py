"""Copy a verified snapshot to a mounted external disk without overwriting backups."""
import argparse
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.snapshot_evidence import digest


def copy_backup(source, output):
    source, output = source.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError(output)
    if not output.is_relative_to('/Volumes') or len(output.parts) < 4:
        raise ValueError('Destination must be on a mounted external disk under /Volumes')
    volume = Path('/Volumes')/output.parts[2]
    if not volume.is_mount():
        raise ValueError('External volume is not mounted')
    parent = output.parent
    while not parent.exists():
        parent = parent.parent
    info = plistlib.loads(subprocess.check_output(['/usr/sbin/diskutil', 'info', '-plist', str(volume)]))
    if info.get('Internal') is not False or parent.stat().st_dev == source.stat().st_dev:
        raise ValueError('Destination must be a verified external disk')
    manifest = json.loads((source/'snapshot.json').read_text())
    for relative, expected in manifest['artifact_hashes'].items():
        path = (source/relative).resolve()
        if not path.is_relative_to(source) or digest(path) != expected:
            raise ValueError(f'Source verification failed: {relative}')
    required = sum((source/name).stat().st_size for name in manifest['artifact_hashes'])
    if shutil.disk_usage(parent).free < required + 1024**3:
        raise ValueError('Insufficient external disk space including 1 GiB reserve')
    output.mkdir(parents=True, exist_ok=False)
    for relative, expected in manifest['artifact_hashes'].items():
        target = output/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source/relative, target)
        if digest(target) != expected:
            raise ValueError(f'Backup verification failed: {relative}')
        target.chmod(0o444)
    # Preserve the original snapshot manifest, including any missing historical file.
    shutil.copyfile(source/'snapshot.json', output/'snapshot.json')
    receipt = {'source_snapshot_sha256':digest(source/'snapshot.json'),
               'verified_files':len(manifest['artifact_hashes']),
               'external_disk':True, 'unavailable':manifest['unavailable']}
    (output/'external-backup.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    copy_backup(args.source, args.output)
