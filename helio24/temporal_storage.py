"""Discover frozen resume dependencies without opening cloud placeholders."""
import json
from pathlib import Path

from helio24.storage_preflight import inspect_storage


def inspect_temporal_inputs(root, run, cache, protocol_path=None):
    root, run, cache = map(Path, (root, run, cache))
    protocol_path = Path(protocol_path or root/'config/temporal-sequence-v2.json')
    required = set()
    errors = []

    def require(path):
        path = Path(path)
        required.add(path)
        return path

    def manifest(path):
        path = require(path)
        if not inspect_storage([path])['available']:
            return None
        try:
            value = json.loads(path.read_text())
            if not isinstance(value, dict):
                raise ValueError('Expected a JSON object')
            return value
        except (OSError, ValueError) as error:
            errors.append({'path': str(path), 'reason': 'invalid_manifest', 'error': str(error)})
            return None

    def relative(base, name):
        name = Path(name)
        if name.is_absolute() or '..' in name.parts:
            raise ValueError('Manifest paths must remain inside their input directory')
        return require(base/name)

    def artifacts(base, record):
        hashes = record['artifact_hashes']
        if not isinstance(hashes, dict):
            raise ValueError('Expected artifact_hashes object')
        for name in hashes:
            relative(base, name)

    protocol = manifest(protocol_path)
    prepared = manifest(run/'prepared.json')
    cached = manifest(cache/'report.json')
    try:
        if protocol is not None:
            for name in protocol['runner_code_hashes']:
                relative(root, name)
            for key in ['direction', 'base_protocol', 'smoke']:
                relative(root, protocol[key])
            for key in ['baseline_artifact', 'short_control']:
                relative(root, str(Path(protocol[key])/'report.json'))
            # Include local Python imports, excluding disposable bytecode caches.
            required.update((root/'helio24').glob('*.py'))
        if cached is not None:
            artifacts(cache, cached)
        if prepared is not None:
            artifacts(run, prepared)
        if protocol is not None and prepared is not None:
            for fold in prepared['folds']:
                if fold['status'] != 'complete':
                    continue
                directory = run/str(fold['year'])
                finished = directory/'finished.json'
                if finished.exists():
                    record = manifest(finished)
                    if record is not None:
                        artifacts(directory, record)
                    continue
                for key in ['baseline_artifact', 'short_control']:
                    for name in ['predictions.parquet', 'thresholds.json']:
                        relative(root, str(Path(protocol[key])/str(fold['year'])/name))
                for arm in protocol['arms']:
                    for seed in protocol['seeds']:
                        job = directory/f'{arm}_seed{seed}'
                        result = job/'result.json'
                        if result.exists():
                            require(job/'job.json')
                            record = manifest(result)
                            if record is not None:
                                artifacts(job, record)
                        else:
                            for name in ['job.json', 'checkpoint.pt', 'worker.log']:
                                if (job/name).exists():
                                    require(job/name)
    except (KeyError, TypeError, ValueError) as error:
        errors.append({'path': str(protocol_path), 'reason': 'invalid_manifest', 'error': str(error)})
    result = inspect_storage(sorted(required))
    result['blockers'].extend(errors)
    result['available'] = not result['blockers']
    result['scope'] = 'Manifest-declared temporal resume inputs; availability only, not hash verification.'
    return result
