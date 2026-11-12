# Project reporting requirements

- Write every user-facing research, evaluation and data-audit report in both
  Turkish and English. Both editions must cover the same findings, limitations,
  uncertainty, tables and reproduction instructions.
- Keep existing original report filenames and frozen experiment artifacts intact.
  Add the counterpart as `<report>.tr.md` or `<report>.en.md`.
- Register both editions in `docs/reports.json` and link them from
  `docs/reports.md`. Update the source hash only after reviewing both editions.
  Do not treat a summary as a full translation.
- Run `scripts/publish_reports.py` to publish paired HTML document editions.
  Use a new output directory for each revision; do not overwrite frozen outputs.
  Historical single-language experiment HTML remains preserved as evidence;
  deliver the paired document editions through the bilingual index.
- Keep all numerical findings and scope distinctions identical across languages.
  Technical metric identifiers may remain unchanged. Never translate model IDs,
  field names, commands or hashes.
- Development reports written after 2026-11-12 rest on the relabelled table and
  the adopted operating point (`config/operating-point-v3.json`,
  `config/walk-forward-v2.json`): state the development basis, give precision
  with delivered recall and missed positive runs per year and tier, mark alert
  fallback years, and keep frozen-label results visible for comparison.
- Commit completed work in clear, concise English conventional commits ending
  with a period. Keep datasets, model files and generated artifacts out of Git.
- The user's local Streamlit branding changes in `app.py` must remain uncommitted.
