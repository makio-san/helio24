"""List the protocols on this checkout and whether each was executed and can run.

Usage: python3 agents/bin/protocol_status.py [--json] [--pending]

For every config/*.json with an id: its status, date, the reports that cite it, a ledger
line if any, and whether every evidence path it names exists in the owner's checkout or the
agent evidence store, and for Hale proposals whether the owner approved the exact file
with `hale approve --gate protocol`. Standard library only; reads nothing outside those places.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get('HELIO24_AGENTS_ROOT', '/Users/esma/Projects/helio24_orchestra_work'))
OWNER = Path(os.environ.get('HELIO24_OWNER_CHECKOUT', '/Users/esma/Developer/Helio24-restored'))
STORE = ROOT / 'evidence'
# Protocols dated before the agents started belong to the owner's history: the agents never
# execute them, whatever their citations say (that history has no ledger).
AGENTS_START = '2026-11-24'


def evidence_paths(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from evidence_paths(v)
    elif isinstance(value, list):
        for v in value:
            yield from evidence_paths(v)
    elif isinstance(value, str) and value.startswith(('artifacts/', 'data/')) and ' ' not in value:
        yield value


def present(path):
    parts = Path(path).parts
    if (OWNER / path).exists():
        return True
    return parts[0] == 'artifacts' and len(parts) > 1 and (STORE / Path(*parts[1:])).exists()


def hale_approvals():
    """(path, sha256) pairs the owner approved with `hale approve --gate protocol`."""
    approved = set()
    for record in sorted((OWNER / 'artifacts/hale_approvals').glob('*.json')):
        try:
            payload = json.loads(record.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict) or payload.get('gate') != 'protocol':
            continue
        for row in payload.get('files') or []:
            if isinstance(row, dict) and isinstance(row.get('path'), str):
                approved.add((row['path'], row.get('sha256')))
    return approved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--pending', action='store_true',
                        help='only agent-era protocols without a ledger line (the ones an experimenter may run)')
    args = parser.parse_args()

    repo = Path.cwd()
    reports = json.loads((repo / 'docs/reports.json').read_text())
    texts = {}
    for entry in reports:
        for lang in ('en', 'tr'):
            name = entry.get(lang)
            if name and (repo / 'docs' / name).exists():
                texts[name] = (repo / 'docs' / name).read_text(errors='replace')
    ledger_path = repo / 'agents/state/protocol-ledger.md'
    ledger = ledger_path.read_text() if ledger_path.exists() else ''

    approvals = hale_approvals()
    rows = []
    for path in sorted((repo / 'config').glob('*.json')):
        try:
            config = json.loads(path.read_text())
        except json.JSONDecodeError as error:
            rows.append(dict(file=f'config/{path.name}', error=str(error)))
            continue
        if not isinstance(config, dict) or 'id' not in config:
            continue
        cid = str(config['id'])
        cited = sorted(n for n, t in texts.items() if f'config/{path.name}' in t or cid in t)
        cited_en = [n for n in cited if not n.endswith('.tr.md')]
        needed = sorted(set(evidence_paths(config.get('evidence', {}))))
        missing = [p for p in needed if not present(p)]
        in_ledger = f'| {cid} |' in ledger
        rel = f'config/{path.name}'
        # A Hale proposal (status design_proposed, with supersedes) runs only after the owner
        # approved this exact file with `hale approve --gate protocol`, whatever its date.
        hale_proposal = config.get('status') == 'design_proposed' and 'supersedes' in config
        hale_approved = (rel, hashlib.sha256(path.read_bytes()).hexdigest()) in approvals
        legacy = not hale_proposal and (not isinstance(config.get('date'), str) or config['date'] < AGENTS_START)
        rows.append(dict(
            file=f'config/{path.name}', id=cid, status=config.get('status'), date=config.get('date'),
            reserved_test_accessed=config.get('reserved_test_accessed'),
            cited_by=cited_en, in_ledger=in_ledger, legacy=legacy,
            hale_proposal=hale_proposal, hale_approved=hale_approved,
            awaiting_owner_approval=hale_proposal and not hale_approved and not in_ledger,
            acceptance_rule=config.get('acceptance_rule'),
            executed=in_ledger or any('protocol' not in n for n in cited_en),
            executable=not legacy and not in_ledger and (hale_approved or not hale_proposal),
            evidence_missing=missing,
        ))
    if args.pending:
        rows = [r for r in rows if r.get('executable')]
    if args.json:
        print(json.dumps(rows, indent=1))
        return
    for r in rows:
        if 'error' in r:
            print(f"{r['file']}: unreadable ({r['error']})")
            continue
        state = ('legacy' if r['legacy'] else 'executed' if r['in_ledger']
                 else 'awaiting hale approve' if r['awaiting_owner_approval'] else 'pending')
        miss = f", missing {len(r['evidence_missing'])} inputs" if r['evidence_missing'] else ''
        print(f"{r['file']}: {r['status']}, {state}{miss}")


if __name__ == '__main__':
    main()
