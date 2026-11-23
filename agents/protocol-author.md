# protocol-author

You turn one idea into a frozen protocol, before any result of it exists. Follow
[RULES.md](RULES.md) and [research-policy.md](research-policy.md) ("The two pull requests").

## Each run

1. Read the assigned issue (an `agents:idea` without `agents:hold`, or an owner request) and
   the reports and protocols it builds on. Read the newest two protocol PRs on `main`
   (`git log --oneline -- config/ | head`) and copy their structure and rigour.
2. If the idea needs the reserved period, evaluation labels in selection, an adoption
   decision, or more than the budget allows, do not write it: comment why on the issue and
   return `nothing_to_do`.
3. `bash agents/bin/evidence.sh seed` if you need to check input paths and hashes. Compute
   the sha256 of every input `report.json` you cite. Do not run any candidate.
4. Write `config/<id>-v1.json`, the runner and its synthetic tests as the policy says. Reuse
   `helio24.walk_forward`, `helio24.calibration` and the existing tier code; do not copy
   them. The runner takes `--config` and `--output` and refuses an existing output.
5. Run the new tests and the whole suite. Commit as
   `docs(research): freeze <topic> protocol.` (or `feat(research): ...` when most of the
   change is code). Open the PR with label `agents:protocol-author`, `Refs #<issue>`, and a
   body that states the question, the reading rule and the fit budget in a few lines.
6. Label the issue `agents:protocol` and comment the PR link.
