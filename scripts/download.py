"""Download official archives, verify MD5, retain a class-blind deterministic subset."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
API = 'https://dataverse.harvard.edu/api'


def download_catalog(metadata):
    info = next(f['dataFile'] for f in metadata['data']['latestVersion']['files']
                if f['dataFile']['filename'] == 'addenda.tar.gz')
    archive = ROOT / 'data/downloads/addenda.tar.gz'
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        subprocess.run(['curl', '-fsSL', '--retry', '3', f'{API}/access/datafile/{info["id"]}',
                        '-o', str(archive)], check=True)
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'md5').hexdigest() != info['checksum']['value']:
            raise ValueError('Addenda checksum mismatch')
    with tarfile.open(archive) as tar:
        content = tar.extractfile('integrated_flare_data/goes_flares_integrated.csv').read()
        (ROOT / 'data/flare_catalog.csv').write_bytes(content)


def download(partition, fraction, metadata, archives_only=False):
    filename = f'partition{partition}_instances.tar.gz'
    info = next(f['dataFile'] for f in metadata['data']['latestVersion']['files']
                if f['dataFile']['filename'] == filename)
    archive = ROOT / 'data/downloads' / filename
    archive.parent.mkdir(parents=True, exist_ok=True)
    destination = ROOT / 'data/raw' / f'partition{partition}'
    manifest_path = ROOT / 'data' / f'partition{partition}-manifest.json'
    if manifest_path.exists() and not archives_only:
        manifest = json.loads(manifest_path.read_text())
        if manifest['fraction'] == fraction and all((ROOT / p).exists() for p in manifest['files']):
            print(f'partition{partition}: verified download already processed', flush=True)
            return
    if not archive.exists():
        partial = archive.with_suffix('.part')
        subprocess.run(['curl', '-fSL', '--retry', '3', '--max-time', '900', '--continue-at', '-',
                        f'{API}/access/datafile/{info["id"]}', '-o', str(partial)],
                       check=True, stderr=subprocess.DEVNULL)
        partial.rename(archive)
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'md5').hexdigest()
    if digest != info['checksum']['value']:
        raise ValueError(f'Checksum mismatch: {archive}')
    if archives_only:
        print(f'partition{partition}: archive checksum verified', flush=True)
        return
    counts, kept, files = Counter(), Counter(), []
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith('.csv'):
                continue
            name = Path(member.name).name
            match = re.fullmatch(r'(.+)_ar(\d+)_s(.+)_e(.+)\.csv', name)
            if not match:
                raise ValueError(f'Unknown filename: {name}')
            label, region, start, _ = match.groups()
            cls = 'N' if label == 'FQ' else label[0]
            if cls not in 'NBCMX':
                raise ValueError(label)
            counts[cls] += 1
            # Selection uses only region and observation start; never the outcome.
            key = hashlib.sha256(f'{region}/{start}'.encode()).digest()
            if int.from_bytes(key[:8], 'big') / 2**64 >= fraction:
                continue
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tar.extractfile(member).read())
            files.append(str(target.relative_to(ROOT)))
            kept[cls] += 1
    manifest = dict(partition=partition, fraction=fraction, files=files,
                    source_url=f'{API}/access/datafile/{info["id"]}',
                    archive_md5=digest, full_class_counts=dict(counts),
                    sample_class_counts=dict(kept),
                    sampling='sha256(HARP/observation_start), class-blind')
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f'partition{partition}: full={dict(counts)} retained={dict(kept)}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--partitions', nargs='+', type=int, default=[1, 3, 5], choices=range(1, 6))
    parser.add_argument('--fraction', type=float, default=0.1)
    parser.add_argument('--archives-only', action='store_true', help='Verify compressed archives without extracting records')
    args = parser.parse_args()
    if not 0 < args.fraction <= 1:
        parser.error('fraction must be in (0, 1]')
    metadata_path = ROOT / 'data/dataverse-metadata.json'
    if not metadata_path.exists():
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['curl', '-fsSL', f'{API}/datasets/:persistentId/?persistentId=doi:10.7910/DVN/EBCFKM',
                        '-o', str(metadata_path)], check=True)
    metadata = json.loads(metadata_path.read_text())
    download_catalog(metadata)
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(lambda p: download(p, args.fraction, metadata, args.archives_only), args.partitions))
