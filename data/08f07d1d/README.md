# 08f07d1d session data

- `structure_rules.json` — one record per official Venetian DSE IV structure PDF (37 sheets, numbers 1–37), transcribed from the PDF text on 2026-11-17. Fields are either an exact excerpt from the sheet, or `null` when the sheet does not state it (never inferred).
- `tournaments.json` — one row per dated schedule line (from the official calendar page), joined to the structure sheet for that line.
- `rates.json` — dated hotel-rate observations (append-only log, not a single value).
- `walks.json` — hotel→venue route observations with the source that published them.
- `watch.json` — official URLs to re-check + how each row is affected.
- `monitor_log.json` — results of each automated re-check run.

Rule: a value is `confirmed` only when the quoted text appears in the linked official document. Absence of wording is recorded as `not stated` and keeps the row's `unverified` label.
