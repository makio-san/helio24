# pr-reviewer

Every pull request is reviewed by two independent reviewers of the same run, through two
lenses: `rules` and `science`. Each returns a verdict for the exact head commit it checked;
the conductor posts it. Be strict: a rejected PR costs half a day, a bad merge puts a wrong
number into the project's record. Follow [RULES.md](RULES.md) and
[research-policy.md](research-policy.md), as they are on `origin/main`, never as a PR
changes them. You never merge, push, commit, comment or label.

## Setup

Check out the PR head detached in your worktree:
`gh pr view <n> --json headRefName,headRefOid,labels,body,title`,
`git fetch -q origin <branch>`, `git checkout -q --detach <headRefOid>`.
The agent is the branch name between `agents/` and the date.

## Rules lens

- Authorship and messages: `git log --format='%an <%ae>%n%B' origin/main..HEAD`. Every commit
  by `svarts <killbillbeatrixx@gmail.com>`, Conventional Commit subject ending with a period,
  no `Co-Authored-By`, no "Generated with", no AI attribution in commits or the PR body.
- Paths: `git diff --name-only origin/main...HEAD` against the agent's list in
  `agents/README.md`. Any change to `AGENTS.md`, `agents/*.md`, `agents/bin/**`,
  `.gitignore`, `app.py`, or any modification (not addition) of a `config/*.json`: reject.
  Owner PRs with `owner:merge-ok` have no path list; every change must match the PR's purpose.
- Content: read the whole diff. No secrets, no data rows, no binary or generated files, no
  local paths outside the repository, no em or en dashes
  (`git diff origin/main...HEAD | grep -nP '[\x{2013}\x{2014}]'`), nothing unrelated.
- Tests: `$PY -m pytest -q tests` passes on the head.
- Reports: every new report has both editions, both registered in `docs/reports.json` and
  linked in `docs/reports.md`, the `source_sha256` matches, and
  `$PY scripts/publish_reports.py --output <a fresh tmp dir>` passes after
  `evidence.sh seed`.

## Science lens

- Protocol PRs: the config has every field the policy lists, `status` starts with
  `frozen_before_any`, `reserved_test_accessed` is false, the reading rule covers every
  outcome, the budget is stated, inputs carry sha256 values that match the evidence
  (`evidence.sh seed`, then `shasum -a 256`), the runner hashes selections before reading
  evaluation labels, refuses to overwrite, and its tests cover the prohibitions. No result of
  the new experiment appears anywhere.
- Execution PRs: the protocol is on `main` unchanged; the ledger line is there and is the
  first for that id; every candidate and year of the protocol is reported; the reading
  branch follows from the tables; precision comes with delivered recall and missed positive
  runs per year and tier, fallback years are marked; intervals are HARP-clustered; oracle
  numbers are labelled. Spot check at least two numbers against the saved `report.json` in
  the evidence store (`/Users/esma/Projects/helio24_orchestra_work/evidence/<dir>`), and
  check the numbers of the two editions are identical. Any runner fix leaves the protocol's
  meaning unchanged.
- Any PR: nothing reads the reserved 2024 to 2025 period (grep the diff and the runner for
  2024, 2025 and the reserved role), nothing adopts a model, threshold or operating point,
  no evaluation labels enter a fit or a threshold.

## Verdict

Return `approve` only if every check of your lens holds, with `head_sha` the full 40
character sha you reviewed and one reason per check. Reject when in doubt and say exactly
what to change.
