"""Call one Hale tool on this worktree, under Hale's policy, without a model.

Usage: $PY agents/bin/hale_call.py <tool> ['<json arguments>']
       $PY agents/bin/hale_call.py --list
       $PY agents/bin/hale_call.py check_parity '{"en": "docs/x.md", "tr": "docs/x.tr.md"}'

Hale (https://github.com/makio-san/hale-agent) enforces the read allowlist, the
reserved-test redaction, new-file-only writes and bilingual numeric parity in code.
The orchestra agents use it as their interface to protocols, reports and frozen
artifacts. Prints Hale's JSON envelope {"ok": ..., "result" | "error": ...} and exits 1
when ok is false.

Hale's human gates stay with the owner: this wrapper never lifts the test-role
redaction, never enables git, refuses open_pull_request, and refuses run_script for
anything but check scripts. Approvals are written only by the owner with `hale approve`.
"""
import json
import sys
from pathlib import Path

ALLOWED = {
    'list_experiments', 'get_experiment', 'search_reports', 'read_document', 'read_artifact',
    'list_scripts', 'run_script', 'interpret_result', 'propose_protocol', 'draft_report',
    'register_report',
}


def check_parity(raw):
    """Hale's bilingual table parity on an existing report pair, without writing anything."""
    from hale.policy import PolicyError, RepoPolicy
    from hale.tools.loop import _assert_numeric_parity
    try:
        args = json.loads(raw)
        policy = RepoPolicy(Path.cwd())
        _assert_numeric_parity(policy.read_text(args['en']), policy.read_text(args['tr']))
    except (KeyError, json.JSONDecodeError, PolicyError, FileNotFoundError) as error:
        print(json.dumps({'ok': False, 'error': type(error).__name__, 'details': str(error)}))
        return 1
    print(json.dumps({'ok': True, 'result': {'en': args['en'], 'tr': args['tr'], 'parity': 'tables match'}}))
    return 0


def main(argv):
    try:
        from hale.policy import RepoPolicy
        from hale.tools import default_registry
    except ImportError:
        print(json.dumps({'ok': False, 'error': 'hale is not installed in this Python'}))
        return 2
    registry = default_registry()
    if argv[:1] == ['--list']:
        for schema in registry.schemas():
            if schema['name'] in ALLOWED:
                print(f"{schema['name']}: {schema['description']}")
        return 0
    if not argv:
        print(__doc__)
        return 2
    tool, raw = argv[0], (argv[1] if len(argv) > 1 else '{}')
    if tool == 'check_parity':
        return check_parity(raw)
    if tool not in ALLOWED:
        print(json.dumps({'ok': False, 'error': f'{tool} is not available to the orchestra'}))
        return 1
    try:
        args = json.loads(raw)
    except json.JSONDecodeError as error:
        print(json.dumps({'ok': False, 'error': f'arguments are not JSON: {error}'}))
        return 1
    if tool == 'run_script':
        specs = registry.call(RepoPolicy(Path.cwd(), python=Path(sys.executable)), 'list_scripts', {})
        family = {s['name']: s.get('family') for s in specs.get('result', {}).get('scripts', [])}
        if family.get(args.get('name')) != 'check':
            print(json.dumps({'ok': False, 'error': 'the orchestra runs only check scripts through Hale'}))
            return 1
    root = Path.cwd()
    if not (root / 'config').is_dir() or not (root / 'docs/reports.json').is_file():
        print(json.dumps({'ok': False, 'error': 'run from the root of a Helio24 worktree'}))
        return 2
    policy = RepoPolicy(root, allow_test_role=False, python=Path(sys.executable), allow_git=False)
    outcome = registry.call(policy, tool, args)
    print(json.dumps(outcome, indent=1, ensure_ascii=False, default=str))
    return 0 if outcome.get('ok') else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
