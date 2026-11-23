# Research policy

Helio24 learns by preregistered experiments: the question, the candidates, the data, the
measures and the reading rule are frozen in a protocol and merged before any result exists.
Agents follow the same discipline the project history shows, and are stricter where an
automated run could quietly bend it. A negative result is a result; it is reported with the
same care as a positive one.

## The two pull requests of an experiment

1. Protocol PR (`protocol-author`), titled `docs(research): freeze <topic> protocol.` or
   `feat(research): freeze <topic> protocol.`:
   - a new `config/<id>-v<n>.json` with `id`, `status` starting with `frozen_before_any`,
     `date`, `goal`, `why` (citing the report or idea issue that motivates it), `evidence`
     (every input path with the sha256 of its `report.json` where one exists), the candidates
     and the control, `budget` (number of fits, targets, thresholds), `years`, `measures`,
     `reading` (rules such as `W1`, `W2`, `W3` that decide the outcome, written so that any
     result falls into exactly one), `limits`, `prohibitions`, and
     `"reserved_test_accessed": false`;
   - the runner, usually `scripts/audit_<topic>.py` or `scripts/run_<topic>.py`, which
     refuses to overwrite its output directory, checks the input hashes, writes thresholds
     and selections to disk and hashes them before any evaluation label is read, and writes
     `report.json` with the protocol sha256;
   - tests on synthetic data only (`tests/test_<topic>.py`), including one for every
     prohibition the code can enforce.
   The protocol PR contains no result numbers of the new experiment. Its author may read
   existing reports and count rows and positives of the input tables, nothing that depends
   on a candidate's predictions.
2. Execution PR (`experimenter`), titled `feat(research): evaluate <topic>.`, only after the
   protocol PR is merged:
   - runs the runner once on the protocol exactly as merged, from a commit of `main` that
     contains it; records that commit;
   - writes the report in both languages (`docs/<topic>-<YYYYMMDD>.md` and `.tr.md`),
     registers both in `docs/reports.json` and `docs/reports.md`, and publishes the paired
     HTML with `scripts/publish_reports.py --output artifacts/bilingual_reports_<YYYYMMDD>_r<n>`;
   - appends one line to `agents/state/protocol-ledger.md`;
   - saves the new evidence directories with `evidence.sh save`.

Protocols dated before 2026-11-24 are the owner's history and were run without a ledger.
Agents never execute or rerun them; `agents/bin/protocol_status.py --pending` lists only the
protocols an experimenter may run.

A runner bug found during execution may be fixed in the execution PR as a separate
`fix(research): ...` commit with a test, only when the fix does not change what the protocol
says (inputs, candidates, measures, reading). The PR body explains it. Anything else needs a
new protocol version and a new protocol PR; the old protocol stays as it is.

## Protocols from Hale

The owner also proposes protocols with Hale: `propose_protocol` writes
`config/<id>-v<n>.json` with `status: design_proposed`, a `supersedes` link and a frozen
`acceptance_rule` (one metric, an operator and a value). Such a protocol may be executed by
the experimenter only when it is on `main` and the owner approved that exact file with
`hale approve --gate protocol <path>` (the approval in the owner's
`artifacts/hale_approvals/` binds its sha256). `agents/bin/protocol_status.py` checks this;
an unapproved proposal is listed as awaiting the owner and is never run.

The protocol-author uses `propose_protocol` too when an idea is a revision of an existing
protocol; that revision then waits for the owner's approval like any Hale proposal. A new
protocol that is decided by one metric also carries an `acceptance_rule` in Hale's format
next to its `reading` rules, so that `interpret_result` can decide it mechanically.

Whenever a protocol has an `acceptance_rule`, its outcome is what Hale's
`interpret_result` returns on the run's artifact. A report may explain the result; it may
never overrule that decision.

## Reserved period

The 2024 to 2025 period is reserved as the final independent test. No agent reads, loads,
counts, plots or downloads anything from it, in any role, and every protocol says
`"reserved_test_accessed": false`. Opening it is the owner's decision alone: an agent that
thinks the project is ready for it opens an `agents:needs-human` issue with the evidence and
does nothing else.

## Development basis

Development reports rest on the relabelled table and the adopted operating point
(`config/operating-point-v3.json`, `config/walk-forward-v2.json`), as `AGENTS.md` says:
state the development basis, give precision with delivered recall and missed positive runs
per year and tier, mark alert fallback years, and keep frozen-label results visible for
comparison. Already inspected years are adaptive development evidence, never an
independent test; say so in every report.

## Honesty rules

- Every candidate in the protocol is reported, also the ones that lose. No candidate,
  threshold, feature or year is added or dropped after results.
- The reading rule is applied as written. The outcome label on the idea or protocol issue is
  `result:goal-met`, `result:partial` or `result:no-gain` and must match the rule.
- Windows overlap and HARPs repeat: intervals are HARP-clustered, and counts are windows or
  positive runs, never presented as independent events.
- Oracle numbers (thresholds chosen on evaluation labels) are labelled oracle and descriptive.
- Numbers in both language editions are identical; model IDs, field names, commands and
  hashes are never translated.
- One execution per protocol. A rerun (`_r2`) is allowed only when the first run failed or
  was invalid for a reason written in the ledger, never because the result was disliked.

## Decisions agents do not make

Agents never adopt a model, operating point, threshold, label set or dashboard default, and
never change `config/operating-point-*.json` or what the app shows by default. When a result
meets a protocol's goal, the execution PR says so and an `agents:needs-human` issue asks the
owner whether to write an adoption protocol. Adoption, the reserved period, new data sources
that need an account or a large download, and changes to the project goal are the owner's.

## Budget

- At most one execution per run of the orchestra, and at most two new protocols per run.
- A protocol states its fit budget; a run that would exceed it stops and reports.
- A download is allowed only when the merged protocol names it with a size bound, and goes
  only to the worktree's `data/` or a saved evidence directory, never redistributed.
