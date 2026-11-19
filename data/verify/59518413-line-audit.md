# Line-by-line audit — session arena/59518413-poker4

Run: 2026-11-19 06:04 UTC · script: `tools/audit_lines_59518413.py`

Rows audited: 253 events · 12 hotels · 12 walk pairs · 131 rate-log entries · 38 plan days · 71 tracked official URLs.

## Result

**No problems found.** Every published row carries an official source in the tracked registry, a `last_checked` date, structured rule fields with excerpt/retrieval provenance, and the arithmetic printed on the pages recomputes from the printed numbers.

## Confirmations

- events: weekday mismatches — 0 across all 253 rows
- events: rows without sources — 0 across all 253 rows
- events: sources outside the tracked registry — 0 across all 253 rows
- events: rows without last_checked — 0 across all 253 rows
- events: structured-rule gaps — 0 across all 253 rows
- events: fee-split arithmetic mismatches without a recorded marker — 0 across all 253 rows
- events: gtd_ratio arithmetic mismatches — 0 across all 253 rows
- events: gtd_over_pool mismatches — 0 across all 253 rows
- events: single-entry claims without a clause — 0 across all 253 rows
- events: 5 printed fee splits that do not add up are recorded verbatim and flagged (F16/F22/F40), never corrected — e.g. V35-2026-12-09-10:10am: printed split 80+510 != 600 (recorded verbatim, flagged)
- hotels: tax-rate conflicts — 0 across all 12 rows
- hotels: fee rows without source — 0 across all 12 rows
- hotels: hotels without a booking link — 0 across all 12 rows
- hotels: hotels without a measured walk — 0 across all 12 rows
- hotels: true-cost/night arithmetic mismatches — 0 across all 12 rows
- hotels: no room-rate slot is fed by a fee observation; every priced rate-log entry carries an explicit kind tag
- walks: all 12 pairs consistent (minutes vs <=30 flag, source URL present)
- rate-log: all 131 entries dated and sourced, no exact duplicates — append-only log intact
- day-plan: all 38 days carry a plan, referenced ids resolve, weekdays match
- room-facts: 5 stored source hashes match the current raw captures (F28 recurrence check)
- pages: 27 spot-checks (counts, search box, booking links, calculator, flags, questions, suggestions, day plan, 6 venue pages, 12 sampled event rows) all present

## Rule-status census (per structured rule field)

| field | status | rows |
|---|---|---|
| add_on | confirmed_allowed | 7 |
| add_on | not_stated_in_sheet | 246 |
| fee | confirmed | 248 |
| fee | unverified | 5 |
| re_entry | confirmed_allowed | 141 |
| re_entry | confirmed_limited | 16 |
| re_entry | forbidden | 1 |
| re_entry | indicated | 2 |
| re_entry | not_stated_in_sheet | 93 |
| single_entry | confirmed_not_single_entry | 4 |
| single_entry | unverified | 249 |

## Method

- Every event id, date/weekday, source URL, `last_checked`, and the four structured rule fields (single_entry / re_entry / add_on / fee, each with status + source + retrieved) were checked for all 253 rows; source URLs were required to appear in `data/tracked-sources.json` (the official registry, now 71 URLs — the three Bellagio structure PDFs were added to it by this session).
- Fee-split arithmetic: house fee + pool-per-entry must equal the printed buy-in wherever the sheet prints all three. Printed inconsistencies (Wynn WPT-08, flag F22; the five Venetian rows on sheets 31/32/33, flag F40) are recorded verbatim and flagged, never corrected; this audit reports a problem only where a mismatch carries no recorded marker.
- Guarantee ÷ entry-fee and guarantee ÷ pool-per-entry were recomputed for every rankable row (descriptive ratios only).
- Hotel rows: tax chain is 13.38% on rate + resort fee; true cost/night recomputed where a dated rate exists; every row needs an official source URL and a booking link; no room-rate slot may be fed by a fee observation, and every priced rate-log entry carries an explicit kind tag.
- Walk pairs: `meets_30_min` re-derived from the measured minutes (30-minute hard filter).
- Rate log: dated, sourced, no exact duplicates — the log is append-only.
- Day plan: every day carries a primary + conditional fallback; referenced ids resolve against the event table; weekdays match dates.
- Provenance: stored `sha256` of every room-facts source recomputed against the current raw captures (recurrence check for F28).
- Rendered pages: counts, search box, booking links, calculator, flags, questions, suggestions, day plan, all six venue pages, and 12 randomly sampled event rows were looked up in the built HTML.

Live venue pages could not be re-fetched from this sandbox (outbound HTTP reaches github.com / npm / PyPI only). The scheduled GitHub Actions jobs (`source-recheck.yml`, `url-check.yml`, `maintenance.yml`) perform the live re-checks at 06:00 Las Vegas and write the dated results; this audit verifies the committed captures and the published pages against each other.
