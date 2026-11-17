# Poker Strip tournament & stay dashboard

Static, source-first planning dashboard for upcoming official poker-tournament listings around the Las Vegas Strip.

## Start here: the v2 build

The current dashboard lives in **[`v2/`](v2/index.html)** and is generated from one verified data layer
(`data/v2/*.json`, retrieval date **2026-11-17**). Everything below it in this README is the earlier,
narrower snapshot, kept for comparison.

| Page | What it answers |
|---|---|
| [`v2/index.html`](v2/index.html) | Executive dashboard: what the data supports, what it refuses to claim |
| [`v2/tournaments.html`](v2/tournaments.html) | 83 dated Venetian entries + 11 restarts, each linked to its own official structure sheet |
| [`v2/schedule.html`](v2/schedule.html) | One primary event per day, a conditional fallback, and 40 scored same-day pairs |
| [`v2/hotels.html`](v2/hotels.html) | Resort fee, tax, parking, cancellation and a dated rate log — never one price |
| [`v2/calculator.html`](v2/calculator.html) | Trip cost = entries × buy-in + nights × true nightly cost |
| [`v2/venues.html`](v2/venues.html) | One section per room: Venetian, Wynn, Caesars Palace, Bellagio |
| [`v2/separate.html`](v2/separate.html) | Every event where paying more buys chips (re-entry, rebuy, add-on) |
| [`v2/questions.html`](v2/questions.html) | 22 questions; which are answered, which gate a booking |
| [`v2/suggestions.html`](v2/suggestions.html) | 12 scoped improvements, none implemented |
| [`v2/flagged.html`](v2/flagged.html) | 25 unresolved items, each with the step that settles it |
| [`v2/about.html`](v2/about.html) | Method, 70-entry source table, repo irregularities |

### Rebuild it

```bash
python3 tools/v2_extract.py        # Venetian TSV + structure sheets -> data/v2/events.json
python3 tools/v2_extract_other.py  # Wynn WPT poster + hand rows    -> data/v2/events_other.json
python3 tools/v2_walk.py           # labelled OSRM matrix           -> hotels.json walk pairs
python3 tools/v2_build.py          # render                            -> v2/*.html
python3 tools/v2_verify.py         # link / source / empty-table audit
```

`.github/workflows/v2-monitor.yml` re-fetches every official URL in `data/v2/sources.json` daily,
hashes the normalised page, and opens an issue when a hash moves. It never rewrites a value.

### The headline finding

No official 2026 source on the Strip confirms a whole-event single-entry tournament.
The Venetian's 37 structure sheets state a late-registration window and nothing about entry —
and its own 2023/2024 sheets *did* print "Registration and Re-Entry is allowed", so the silence
is not a house convention. The only published single-entry statement found is the WPT's
"a single entry per starting flight" for the $10,400 World Championship at Wynn, which still
permits three entries across three flights. **Zero rows pass a strict single-entry filter.**

## Earlier snapshot (Nov 16, 2026)

The data snapshot for the pages below is dated **November 16, 2026 (UTC)**. They distinguish verified facts from unknowns and do not label a tournament single-entry unless official rules say so.

## Project pages

- `index.html` — executive summary and key decision blockers
- `tournaments.html` — dated tournament candidates and spending/bounty exclusions
- `schedule.html` — practical day-planning constraints
- `hotels.html` — official Venetian/Palazzo rates, resort-fee math, and unknown stay pricing
- `decisions.html` — questions, missing information, and staged suggestions
- `questions.html` — compact companion decision checklist, retained from the first integration and now source-linked row by row
- `review.html` — flagged items and verification limitations
- `trip-calculator.html` — trip cost form (entries × buy-in + nights × true nightly cost)
- `calculator.html` — event-picker trip calculator built from the verified schedule rows
- `change-monitor.html` / `recheck.html` — URL change monitor and the daily automated re-check log
- `venue-venetian.html`, `venue-wynn.html`, `venue-others.html` — one page per venue with its events and hotels
- `sources.html`, `suggestions.html` — source list and improvement suggestions

## Run locally

Open `index.html` directly, or serve the repository root with any static-file server. No build tooling or third-party runtime dependencies are required. The site is deployed with GitHub Pages via `.github/workflows/pages.yml`.

## Research policy

All values shown as confirmed link to the official operator source. Unknown or ambiguous values are blank and flagged. The available official tournament schedule does not explicitly establish whether entries or re-entries are allowed for the upcoming one-day events; consequently, **there are no tournaments classified as verified single-entry**. The data is a point-in-time snapshot, not a live feed or booking quote.
