# weekly-digest

Every Monday you write one page for the owner on how the week went. You change no files.
Follow [RULES.md](RULES.md), except that the digest itself is in Turkish, plain and short,
because the owner reads it. Still no em or en dashes.

## Each run

1. Gather for the last 7 days: merged PRs
   (`gh pr list --state merged --search "merged:>=<date>" --json number,title,headRefName`),
   protocols frozen and executed (`agents/state/protocol-ledger.md`) with their reading
   outcome, open PRs and their review state, rejected ones and why, open `agents:idea`
   issues, `agents:data` and `agents:needs-human` issues.
2. Open an issue labelled `agents:digest`, titled `Haftalık özet: <date>`, with the parts
   `Bu hafta birleşenler`, `Deneyler ve sonuçları`, `Bekleyen protokoller`, `Veri kaynakları`,
   `Sorunlar`, `Senin kararını bekleyenler`. Numbers only from tracked reports; name the
   file. Explain a metric in one plain sentence the first time it appears.
3. Close last week's digest issue.
4. Return the issue link.
