# Helio24 agents

Twelve agents, run as workers of one conductor workflow, extend Helio24's research the way
the project already works: ideas become frozen protocols, merged protocols are executed once
and reported in Turkish and English, and every pull request passes two independent reviews
before a merger lands it on `main`. Each agent is one file here; the rules they all share are
in [RULES.md](RULES.md), the research discipline in [research-policy.md](research-policy.md).
The conductor lives outside the repository, in `/Users/esma/Desktop/helio24_orchestra/`.

## The agents

| Agent | Job | Output |
|---|---|---|
| [research-scout](research-scout.md) | Reads recent flare forecasting work and files testable ideas | issues `agents:idea` |
| [protocol-author](protocol-author.md) | Freezes one idea as a protocol: config, runner, synthetic tests, no results | protocol PR |
| [experimenter](experimenter.md) | Executes one merged protocol once, writes the bilingual report, saves evidence | execution PR |
| [report-keeper](report-keeper.md) | Keeps both editions of every report complete, equal and registered | `docs(reports)` PRs |
| [data-watch](data-watch.md) | Watches SWAN-SF, SWAN-SF-V2, SWPC, JSOC and HEK, and the local evidence | issues `agents:data` |
| [code-health](code-health.md) | Tests, warnings and hygiene, never a research result | `fix`, `test`, `refactor` PRs |
| [dashboard-qa](dashboard-qa.md) | Checks the local Streamlit dashboard on `main` | fix PRs, issues |
| [docs-keeper](docs-keeper.md) | Keeps `README.md` true to the tracked reports | `docs(readme)` PRs |
| [pr-reviewer](pr-reviewer.md) | Two reviewers per PR, rules lens and science lens | verdict comments, labels |
| [release-merger](release-merger.md) | Merges approved PRs, promotes their evidence | `main`, `agents/reports/merge-log.md` |
| [weekly-digest](weekly-digest.md) | Monday page for the owner, in Turkish | issue `agents:digest` |

The conductor itself is the twelfth: it senses the repository, the evidence and the sources,
plans the run, and writes the run log.

## Flow

1. `research-scout` files `agents:idea` issues. The owner can add a thumbs up to push one,
   or `agents:hold` to park it.
2. `protocol-author` freezes an idea as a protocol PR. Once reviewed and merged, the protocol
   cannot change; a change is a new version.
3. `experimenter` runs a merged protocol, reports it in both languages, logs it in
   `agents/state/protocol-ledger.md` and labels the outcome `result:goal-met`,
   `result:partial` or `result:no-gain`. Adoption is always the owner's decision.
4. `report-keeper`, `docs-keeper`, `code-health`, `dashboard-qa` and `data-watch` keep the
   record, the code and the inputs sound.
5. Two `pr-reviewer` workers approve or reject each PR for its exact head commit; a rejected
   PR gets one repair round.
6. `release-merger` merges approved PRs and copies their evidence into the owner's
   `artifacts/` without overwriting anything.

## Hale

The agents work through [Hale](https://github.com/makio-san/hale-agent), the project's
research agent, installed in their Python environment from a clean clone. They call its
tools without a model (`agents/bin/hale_call.py`), so Hale's policy guards every read of a
frozen artifact, every new report pair and every protocol revision. The two meet in both
directions:

- A protocol the owner proposes with Hale and approves with
  `hale approve --gate protocol <path>` is executed by the orchestra once it is on `main`.
- A protocol revision the orchestra writes with Hale's `propose_protocol` waits for the same
  approval. The run summary names the exact command.
- `hale replay` is a review gate: a PR that changes a published number of an archived
  decision is rejected.

Hale's gates stay with the owner: no agent approves, merges `hale/*` branches without
`owner:merge-ok`, lifts the test-role redaction or calls a model through Hale.

## Paths each agent may change

The reviewer rejects and the merger skips any PR that touches a path outside its agent's
list. No agent may change `AGENTS.md`, `agents/*.md`, `agents/bin/**`, `.gitignore`,
`app.py`, anything in `artifacts/hale_approvals/`, or modify an existing `config/*.json`.

| Agent | Paths |
|---|---|
| protocol-author | new `config/*.json`, new or extended `scripts/audit_*.py` and `scripts/run_*.py`, `helio24/**` (additions; existing behaviour unchanged), `tests/**` |
| experimenter | new `docs/*.md` reports, `docs/reports.json`, `docs/reports.md`, `agents/state/protocol-ledger.md`, and for a runner fix the protocol's own script, `helio24/**`, `tests/**` |
| report-keeper | `docs/*.tr.md`, `docs/*.en.md`, `docs/reports.json`, `docs/reports.md` |
| code-health | `helio24/**`, `scripts/**`, `tests/**`, `pytest.ini`, `conftest.py` |
| dashboard-qa | `helio24/*_views.py`, `helio24/experiment_monitor.py`, `helio24/review.py`, `tests/**`, `.streamlit/config.toml` |
| docs-keeper | `README.md` |
| release-merger | `agents/reports/merge-log.md`, revert commits |
| research-scout, data-watch, pr-reviewer, weekly-digest | no files; issues and comments only |

## Gates before anything reaches `main`

A PR is merged only when both reviewers approved its current head commit, all commits are
authored by `svarts <killbillbeatrixx@gmail.com>` with Conventional Commit subjects ending
in a period and no AI attribution, the paths are allowed for its agent, it merges cleanly,
the tests and the report publisher pass on the merged result, and an execution PR's protocol
is already on `main`.

## Owner pull requests

The owner can hand a pull request of their own (any branch that is not `agents/*`) to the
agents by adding the label `owner:merge-ok`. Only the owner sets that label; an agent never
does. Such a PR gets the same review and gates, without a path list. Without the label, the
agents leave the owner's PRs alone.

## Workspace and evidence

Agents never work in the owner's checkouts. `/Users/esma/Projects/helio24_orchestra_work/`
(outside iCloud) holds a clone (`base/`), one worktree per worker (`work/<name>/`), the
agents' Python environment (`venv/`) and the evidence store (`evidence/`): every artifact
directory an agent produced, read only, never overwritten. `agents/bin/evidence.sh seed`
gives a worktree free APFS clones of the owner's `artifacts/` and `data/` plus the store.

## Turning things off

The scheduled task `helio24-conductor` starts every run. Disable it to stop everything. To
stop only merging, remove the Release phase from the conductor or run it with `maxTasks: 0`.
