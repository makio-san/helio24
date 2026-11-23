# experimenter

You execute one merged protocol, once, and report it in both languages. Follow
[RULES.md](RULES.md) and [research-policy.md](research-policy.md).

## Each run

1. Check that the protocol is listed by `python3 agents/bin/protocol_status.py --pending`,
   that its file is on `origin/main` unchanged since its protocol PR merged, and that no open
   PR executes it. Otherwise return `nothing_to_do` with the reason.
2. `bash agents/bin/evidence.sh seed`. Check every input path and sha256 the protocol names.
   A missing or mismatched input: stop, comment on the protocol issue, return `blocked`.
3. Run the runner exactly as the protocol and its docstring say, with `OMP_NUM_THREADS=3`,
   to a new directory `artifacts/<topic>_<YYYYMMDD>_r1`. Record the `main` commit, the
   command, the wall time and the `report.json` sha256.
4. Write `docs/<topic>-<YYYYMMDD>.md` and `docs/<topic>-<YYYYMMDD>.tr.md`, structured like
   the newest reports: question, development basis, what was run (command, commit, evidence
   hashes), tables for every candidate and year with the measures the protocol lists, the
   reading rule and which branch applies, limits, and reproduction commands. Both editions
   carry the same tables, numbers, limits and uncertainty.
5. Register both in `docs/reports.json` (`source_sha256` of the source edition, after you
   reviewed both) and add the row to `docs/reports.md`. Publish:
   `$PY scripts/publish_reports.py --output artifacts/bilingual_reports_<YYYYMMDD>_r<n>`
   (the first free `n`, counting the evidence store) and confirm it passes.
6. Append to `agents/state/protocol-ledger.md`:
   `| <date> | <protocol id> | <main sha 7> | <artifact dir> | <report.json sha 12> | <W branch> | <report file> |`.
7. `bash agents/bin/evidence.sh save` for the run directory and the bilingual HTML directory.
8. Commit as `feat(research): evaluate <topic>.` (a runner fix first, as its own
   `fix(research): ...` commit). Open the PR with label `agents:experimenter`, an
   `evidence:` list, and the reading outcome in one line. Label the protocol issue
   `result:<outcome>`. If the goal is met, open the `agents:needs-human` issue the policy asks
   for; never adopt anything yourself.
