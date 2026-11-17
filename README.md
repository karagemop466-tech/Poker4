# Poker Strip tournament & stay dashboard

Static, source-first planning dashboard for upcoming official poker-tournament listings around the Las Vegas Strip. The data snapshot is dated **November 16, 2026 (UTC)**. It distinguishes verified facts from unknowns and does not label a tournament single-entry unless official rules say so.

## Project pages

- `index.html` — executive summary and key decision blockers
- `tournaments.html` — dated tournament candidates and spending/bounty exclusions
- `schedule.html` — practical day-planning constraints
- `hotels.html` — official Venetian/Palazzo rates, resort-fee math, and unknown stay pricing
- `decisions.html` — questions, missing information, and staged suggestions
- `questions.html` — compact companion decision checklist, retained from the first integration and now source-linked row by row
- `review.html` — flagged items and verification limitations

## Verified dashboard (`poker4/`)

`poker4/index.html` is the integration layer produced from re-read official sources: one page per venue, a per-event
structure-sheet rule audit, a dated hotel-rate log, a trip-cost estimator (entries × buy-ins + nights × (rate + resort
fee) × (1 + tax) + parking), date/venue/freezeout filters, a search box over every table, and a `last checked` +
`SOURCE CHANGED` mark on each row.

- Data: `data/08f07d1d/*.json` (schedule rows joined to structure sheets, flags, questions, suggestions).
- Re-check: `.github/workflows/tournament-monitor.yml` runs daily at 06:20 Las Vegas time, re-fetches all 57 official
  URLs, hashes each response, audits every structure sheet for entry/re-entry/add-on wording, scrapes the official
  calendar into `data/08f07d1d/feed/`, rebuilds the pages and commits only if verification passes.
- Build/verify: `python3 tools/build_poker4.py` then `python3 tools/verify_poker4.py`.
- Row audit: `python3 tools/check_rows.py` compares the stored schedule table with the officially re-read rows.

## Run locally

Open `index.html` directly, or serve the repository root with any static-file server. No build tooling or third-party runtime dependencies are required. The site is deployed with GitHub Pages via `.github/workflows/pages.yml`.

## Research policy

All values shown as confirmed link to the official operator source. Unknown or ambiguous values are blank and flagged. The available official tournament schedule does not explicitly establish whether entries or re-entries are allowed for the upcoming one-day events; consequently, **there are no tournaments classified as verified single-entry**. The data is a point-in-time snapshot, not a live feed or booking quote.
