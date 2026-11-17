# Poker Strip tournament & stay dashboard

Static, source-first planning dashboard for upcoming official poker-tournament listings around the Las Vegas Strip, integrated with hotel true-cost comparison, a day planner with honest overlap flags, a trip-cost calculator, and a daily change monitor. The verified data snapshot is dated **November 17, 2026 (UTC)** (rates captured Nov 16). Every value links its official operator source; unverified values are blank and flagged. The site never labels a tournament single-entry unless official rules say so.

## Pages (GitHub Pages root)

- `index.html` — executive summary, key constraints, recommended decision sequence
- `tournaments.html` — all tournaments with search, date filter, "single-entry confirmed" toggle, ranking screen (guarantee ÷ total entry fee as a descriptive ratio only), and separate sections for re-entry/add-on, bounty/PKO, flight, and satellite events
- `schedule.html` — day plan (Nov 17 – Dec 23, 2026): one primary event per day + conditional fallback, overlap flags from start time, late-reg cutoff and plausible duration
- `hotels.html` — true cost/night = (rate + resort fee) × 1.1338, ≤30-min-walk filter (Google/Apple Maps verified), per-hotel calculators and official booking deep links
- `trip-calculator.html` — entries × buy-ins + nights × true hotel cost
- `rate-log.html` — dated hotel-rate log (never a single value): checkout total, nightly average, fee + tax, parking, cancellation deadline, timestamps
- `venues/` — one page per venue (Venetian, Wynn, Bellagio, Caesars, other rooms) with its events and nearest hotels
- `monitor.html` — source-change monitor status
- `questions.html` — explicit questions / missing-information list with how to discover each value
- `suggestions.html` — proposals awaiting review (nothing implemented from this page without approval)
- `flagged.html` — "Flagged for Review" irregularities & unverified values (non-blocking)
- `sources.html` — full official-source catalog with last-checked dates

Preserved independent research sets (never treated as confirmation): `60fb62da/`, `c07371e3/`, `df41f5c6/`, `verified/`, `strip/`, `pages/`.

## Data & tooling

- `data/v2/*.json` — canonical datasets: `events.json` (per-event structured rule fields with source excerpts + retrieval dates), `hotels.json`, `walking.json`, `rate_log.json`, `flagged.json`, `sources.json`
- `tools/build_data_v2.py` — rebuilds `data/v2/` from the verified research constants (Venetian DSE IV structure sheets 1–37, Wynn/WPT/Bellagio/Caesars structures, hotel terms, walking matrix)
- `tools/build_root_site.py` — regenerates every root page from `data/v2/`
- `tools/verify_root_site.py` — automated check: internal links resolve, every data row carries an official-source link, required features present (run before every publish)
- `tools/recheck.py` + `tools/daily_schedule.py` + `.github/workflows/recheck.yml` — daily (06:00 UTC) hash-based re-check of each official URL and morning live-schedule snapshots; changed sources get rows marked "source changed — recheck row"

Run locally: `python3 tools/build_data_v2.py && python3 tools/build_root_site.py && python3 tools/verify_root_site.py`, then open `index.html` or serve the repo root. No third-party dependencies.

## Research policy

All values shown as confirmed link to the official operator source, with retrieval dates. Unknown or ambiguous values are blank and flagged — never inferred. All 37 Venetian DeepStack Extravaganza IV structure sheets were read in full on 2026-11-17 and none states a single-entry, re-entry, or add-on limit; consequently **there is exactly one window-wide fact to plan around: no event is classified as verified single-entry.** Rooms that do publish rules (Wynn, Bellagio, Caesars) all allow some form of re-entry, rebuy, or add-on and are listed separately. The data is a point-in-time snapshot plus a daily change monitor — not a live feed or a booking quote.
