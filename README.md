# Strip Poker Planner — Las Vegas Strip tournament & stay dashboard

<<<<<<< HEAD
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

- `data/0f6c627b/*.json` — canonical datasets: `events.json` (per-event structured rule fields with source excerpts + retrieval dates), `hotels.json`, `walking.json`, `rate_log.json`, `flagged.json`, `sources.json`
- `tools/build_data_v2.py` — rebuilds `data/0f6c627b/` from the verified research constants (Venetian DSE IV structure sheets 1–37, Wynn/WPT/Bellagio/Caesars structures, hotel terms, walking matrix)
- `tools/build_root_site.py` — regenerates every root page from `data/0f6c627b/`
- `tools/verify_root_site.py` — automated check: internal links resolve, every data row carries an official-source link, required features present (run before every publish)
- `tools/recheck.py` + `tools/daily_schedule.py` + `.github/workflows/recheck.yml` — daily (06:00 UTC) hash-based re-check of each official URL and morning live-schedule snapshots; changed sources get rows marked "source changed — recheck row"

Run locally: `python3 tools/build_data_v2.py && python3 tools/build_root_site.py && python3 tools/verify_root_site.py`, then open `index.html` or serve the repo root. No third-party dependencies.

## Research policy

All values shown as confirmed link to the official operator source, with retrieval dates. Unknown or ambiguous values are blank and flagged — never inferred. All 37 Venetian DeepStack Extravaganza IV structure sheets were read in full on 2026-11-17 and none states a single-entry, re-entry, or add-on limit; consequently **there is exactly one window-wide fact to plan around: no event is classified as verified single-entry.** Rooms that do publish rules (Wynn, Bellagio, Caesars) all allow some form of re-entry, rebuy, or add-on and are listed separately. The data is a point-in-time snapshot plus a daily change monitor — not a live feed or a booking quote.
=======
Source-first planning dashboard for live poker tournaments around the Las Vegas Strip and the hotels within walking
distance of them. Snapshot dated **2026-11-17**. Every confirmed value links an official operator page or structure PDF;
values that could not be confirmed from an official source are **left blank and flagged** — never inferred.

## What the site does

- **Tournaments** — every tracked event (Venetian DeepStack Extravaganza IV, Wynn daily + WPT World Championship,
  Bellagio weekly, Caesars Palace daily) with buy-in, house/staff fees, pool-per-entry, guarantee, and a descriptive
  guarantee ÷ entry-fee ratio. Ranked only after both values are confirmed; bounty, satellite and multi-flight events are
  labeled and ranked separately. Search box, date filter, and a **single-entry / freezeout confirmed toggle** (currently
  zero rows pass it — no official sheet states one-entry-only).
- **Entry rules per row** — stored as structured fields (single-entry, re-entry, add-on, fees) with the official excerpt
  and retrieval date. Confirmed rules are quoted; silence is labeled unverified.
- **Day plan** — one primary event per day plus conditional fallbacks, with overlap flags built from start time,
  late-registration cutoff and a plausible-duration estimate (estimates are marked as estimates).
- **Hotels & true cost** — true cost/night = (rate + resort fee) × 1.1338 Clark County room tax, parking, cancellation
  terms, and a ≤30-minute walking filter with live Google Maps routes between official addresses.
- **Rate log** — dated observations (checkout total, nightly average, fee, tax, parking, cancellation deadline, rate
  timestamp) instead of single overwritten values.
- **Trip calculator** — entries × buy-ins + nights × true hotel cost (+ parking), with the descriptive ratio.
- **Change monitor** — a scheduled GitHub Actions job (`.github/workflows/monitor.yml`) re-fetches every official URL each
  morning via `tools/monitor_sources.py`, stores hashes/excerpts, saves daily schedule snapshots under `data/feeds/`, and
  appends to `data/change_log.json` so rows whose source changed can be marked.
- **Q&A, Suggestions, Flagged for Review, Sources, Repo review** — decision support; suggestions are review-first and
  nothing is implemented without an explicit choice.

## Parallel build: `v2/` (session 98e4cb1c)

A parallel dashboard lives in **[`v2/`](v2/index.html)** and is generated from one verified data layer
(`data/0f6c627b/*.json`, retrieval date **2026-11-17**). Everything below it in this README is the earlier,
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
python3 tools/v2_extract.py        # Venetian TSV + structure sheets -> data/0f6c627b/events.json
python3 tools/v2_extract_other.py  # Wynn WPT poster + hand rows    -> data/0f6c627b/events_other.json
python3 tools/v2_walk.py           # labelled OSRM matrix           -> hotels.json walk pairs
python3 tools/v2_build.py          # render                            -> v2/*.html
python3 tools/v2_verify.py         # link / source / empty-table audit
```

`.github/workflows/v2-monitor.yml` re-fetches every official URL in `data/0f6c627b/sources.json` daily,
hashes the normalised page, and opens an issue when a hash moves. It never rewrites a value.

### The headline finding

No official 2026 source on the Strip confirms a whole-event single-entry tournament.
The Venetian's 37 structure sheets state a late-registration window and nothing about entry —
and its own 2023/2024 sheets *did* print "Registration and Re-Entry is allowed", so the silence
is not a house convention. The only published single-entry statement found is the WPT's
"a single entry per starting flight" for the $10,400 World Championship at Wynn, which still
permits three entries across three flights. **Zero rows pass a strict single-entry filter.**

## Pages

`index.html` (executive brief) · `tournaments.html` · `schedule.html` · `hotels.html` · `ratelog.html` ·
`calculator.html` · `venues.html` + `venues/*.html` · `monitor.html` · `workflow.html` · `questions.html` ·
`suggestions.html` · `review.html` · `sources.html` · `repo-review.html`

Prior research sets from parallel sessions are preserved under `c07371e3/`, `60fb62da/`, `df41f5c6/`, `strip/`,
`verified/`, `pages/` and are linked from the Flagged for Review page as independent snapshots.

## Build & verify

```bash
python3 tools/build_data.py    # regenerate data/*.json from verified facts
python3 tools/build_site.py    # regenerate the dashboard HTML
python3 tools/verify_site.py   # internal-link + row-source verification
```

No third-party dependencies. Deployed on GitHub Pages (source: `main`, path `/`) via `.github/workflows/pages.yml`;
the source monitor runs daily via `.github/workflows/monitor.yml`.

## Research policy

"Confirmed" means the value appears in an official operator document with a quoted excerpt and a retrieval date.
Omission of re-entry/add-on language is **not** confirmation of single entry. Ratios are arithmetic, not forecasts.
Walking minutes are map estimates (no official source publishes them) and carry live route links.

## Other preserved parallel sets

`planner/` (session 98e4cb1c), `c07371e3/`, `60fb62da/`, `df41f5c6/`, `strip/`, `verified/`, `pages/` — independent
snapshots from earlier parallel sessions, preserved untouched and linked from the root index. Root pages
`change-monitor.html`, `trip-calculator.html`, `venue-venetian.html`, `venue-wynn.html`, `venue-others.html` are also
parallel-session outputs kept at the root for their own navigation.

## Scheduled monitors

Two scheduled workflows run side by side (both preserved): `.github/workflows/monitor.yml` ("Monitor official sources",
session 98e4cb1c) and `.github/workflows/source-recheck.yml` (this dashboard's official-URL hash/excerpt re-check with
`data/change_log.json` + `data/feeds/` snapshots).
>>>>>>> origin/main

## Parallel research sets & tooling (preserved, never treated as confirmation)

- `planner/` — parallel planner site (session 98e4cb1c), `poker4/` — verified venue dashboard (session 98e4cb1c, CI-gated by `poker4-site-verify.yml`), `v2/` — parallel v2 dashboard (session 08f07d1d/b6421d6a) with its own `data/v2/` dataset and `v2-monitor.yml` change monitor
- `prior_root_dashboard/` — the previous root dashboard exactly as it was on `main` before this integration (pages, `assets/`, its `data_v2_json/`, its README/COORDINATION snapshots); it is also still browsable at its original root URLs (`venues.html`, `calculator.html`, `ratelog.html`, `change-monitor.html`, `workflow.html`, `repo-review.html`, `review.html`, `decisions.html`, `style.css`, `app.js`)
- `60fb62da/`, `c07371e3/`, `df41f5c6/`, `verified/`, `strip/`, `pages/` — earlier independent research sets
- Builders: root dashboard = `tools/build_root_site.py` (this session); prior root dashboard = `tools/build_site.py` + `tools/build_data.py`; `v2/` subsite = `tools/v2_build.py`; `poker4/` = `tools/build_poker4.py`. Each builder owns its own outputs only.
