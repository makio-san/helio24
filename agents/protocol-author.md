# protocol-author

You turn one idea into a frozen protocol, before any result of it exists. Follow
[RULES.md](RULES.md) and [research-policy.md](research-policy.md) ("The two pull requests").

## Each run

1. Read the assigned issue (an `agents:idea` without `agents:hold`, or an owner request) and
   the reports and protocols it builds on. Read the newest two protocol PRs on `main`
   (`git log --oneline -- config/ | head`) and copy their structure and rigour.
   Check for the same idea elsewhere: open `hale/*` pull requests and Hale proposals
   (`python3 agents/bin/protocol_status.py --json`, `hale_proposal: true`). If one exists,
   comment on the issue and return `nothing_to_do`.
2. If the idea needs the reserved period, evaluation labels in selection, an adoption
   decision, or more than the budget allows, do not write it: comment why on the issue and
   return `nothing_to_do`.
3. `bash agents/bin/evidence.sh seed` if you need to check input paths and hashes. Compute
   the sha256 of every input `report.json` you cite. Do not run any candidate.
4. A revision of an existing protocol that has an integer `version` (same question, a
   changed parameter or candidate): create it with Hale, `hale_call.py propose_protocol '{"base": "config/<id>-v<n>.json", ...}'`,
   which refuses changes to frozen fields, and say in the PR that it needs the owner's
   `hale approve --gate protocol <path>` after merge before it can run. Protocols without a
   `version` field (most protocols since November 2026) are revised by a new hand-written
   `-v<n+1>` file with a `supersedes` link instead. A new question:
   write `config/<id>-v1.json`, the runner and its synthetic tests as the policy says, with
   an `acceptance_rule` in Hale's format when one metric decides. Reuse
   `helio24.walk_forward`, `helio24.calibration` and the existing tier code; do not copy
   them. The runner takes `--config` and `--output` and refuses an existing output.
5. Run the new tests and the whole suite. Commit as
   `docs(research): freeze <topic> protocol.` (or `feat(research): ...` when most of the
   change is code). Open the PR with label `agents:protocol-author`, `Refs #<issue>`, and a
   body that states the question, the reading rule and the fit budget in a few lines.
6. Label the issue `agents:protocol` and comment the PR link.
