"""Inspect local availability without opening cloud placeholder contents."""
from pathlib import Path


SF_DATALESS = 0x40000000


def is_placeholder(path):
    return bool(getattr(Path(path).stat(), 'st_flags', 0) & SF_DATALESS)


def inspect_storage(paths):
    """Metadata-only check. Availability does not establish content integrity."""
    checked = set()
    blockers = []
    files = 0
    placeholder_bytes = 0

    def visit(path):
        nonlocal files, placeholder_bytes
        path = Path(path)
        if path in checked:
            return
        checked.add(path)
        try:
            metadata = path.stat()
            if path.is_dir():
                for child in sorted(path.iterdir()):
                    visit(child)
                return
            files += 1
            if getattr(metadata, 'st_flags', 0) & SF_DATALESS:
                placeholder_bytes += metadata.st_size
                blockers.append({'path': str(path), 'reason': 'cloud_placeholder', 'bytes': metadata.st_size})
        except FileNotFoundError:
            blockers.append({'path': str(path), 'reason': 'missing'})
        except OSError as error:
            blockers.append({'path': str(path), 'reason': 'inaccessible', 'error': str(error)})

    for path in paths:
        visit(path)
    return {'available': not blockers, 'files_checked': files,
            'placeholder_bytes': placeholder_bytes, 'blockers': blockers,
            'integrity_verified': False}
