# Poker Strip tournament & stay dashboard

Static, source-first planning dashboard for upcoming official poker-tournament listings around the Las Vegas Strip. The data snapshot is dated **November 16, 2026 (UTC)** and the official schedule, resort-fee, hotel-terms, suite-rate, Wynn and Treasure Island pages were **re-verified on November 17, 2026**. It distinguishes verified facts from unknowns and does not label a tournament single-entry unless official rules say so.

## Project pages

- `index.html` — executive summary and key decision blockers
- `tournaments.html` — dated tournament candidates, search box, date filter, single-entry toggle, per-row "last checked" dates
- `schedule.html` — day-planning constraints plus a generated same-day overlap check
- `hotels.html` — official Venetian/Palazzo rates, resort-fee math, and the dated hotel rate log
- `calculator.html` — trip cost calculator: entries × buy-ins + nights × true hotel cost
- `venue-venetian.html`, `venue-wynn.html`, `venue-other.html` — one page per venue with its events and hotels
- `decisions.html` — questions, missing information, and staged suggestions
- `questions.html` — compact companion decision checklist, source-linked row by row
- `review.html` — flagged items and verification limitations
- `recheck.html` — status of the daily automatic re-check of every official source URL

## Run locally

Open `index.html` directly, or serve the repository root with any static-file server. No build tooling or third-party runtime dependencies are required. The site is deployed with GitHub Pages via `.github/workflows/pages.yml`.

## Research policy

All values shown as confirmed link to the official operator source. Unknown or ambiguous values are blank and flagged. The available official tournament schedule does not explicitly establish whether entries or re-entries are allowed for the upcoming one-day events; consequently, **there are no tournaments classified as verified single-entry**. The data is a point-in-time snapshot, not a live feed or booking quote.

## Vegas Field Notes sub-site

A separate, official-source-checked dashboard from session `arena/6313b65a-poker4` lives in [`site/`](site/). It preserves the existing root dashboard and shared Pages workflow. Once this contribution is merged and the existing Pages workflow finishes, browse the sub-site at [`/site/`](https://karagemop466-tech.github.io/Poker4/site/).

The sub-site's dated verification report is [`research/VERIFICATION.md`](research/VERIFICATION.md). Its reviewed strict single-entry count is zero confirmed; unknown entry rules remain unknown. Local run and validation instructions are in [`site/README.md`](site/README.md).
