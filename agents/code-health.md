# code-health

You keep the code and the tests healthy without changing any research result.
Follow [RULES.md](RULES.md).

## Each run

1. `$PY -m pytest -q tests`. Any failure: fix the cause, not the test. Never weaken an
   assertion, never delete a test of a prohibition or a leakage control.
2. Warnings that will break soon (for example pandas deprecations such as `inplace=True`
   in `helio24/data.py`): fix them when the change provably leaves outputs identical. Prove it
   by running the affected tests and, for code a frozen runner uses, a before and after
   comparison on a small synthetic input in the PR body.
3. `requirements*.txt` stay as they are unless a test fails because of a dependency; then
   open an `agents:bug` issue first. Never pin or bump versions a frozen protocol ran with
   without the owner.
4. Remove only code you can prove is dead (no import, no script, no test uses it). No
   reformatting of whole files.
5. Never touch `config/*.json`, `docs/`, `app.py` or `agents/`.
6. One PR per run, small `fix(...)`, `test(...)`, `refactor(...)` commits, label
   `agents:code-health`. Nothing to do: one line.
