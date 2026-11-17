# Poker4 — Vegas Strip live-poker tournament & stay planner

Static, source-first planning dashboard for live poker tournaments on the Las Vegas Strip (Nov 16 – Dec 23, 2026) and the hotels around them. Every value shown as confirmed links to an official operator page or official PDF; unknown or conflicting values are **blank and flagged** — never inferred. Data snapshot dated **2026-11-17**.

- `index.html` — executive summary, verified snapshot, honesty caveats
- `tournaments.html` — master event table: search, date/venue/format filters, "single-entry confirmed only" toggle, brief-mandated sections (single-entry candidates · bounty/PKO · multi-entry & spending advantage · satellites), and the descriptive guarantee ÷ entry-fee ranking (not a forecast)
- `schedule.html` — date picker + day plan: one primary event + conditional fallback, overlap flags from start times / late-reg cutoffs / plausible durations, 8 AM goal-gap disclosure
- `hotels.html` — true nightly cost (rate + mandatory resort fee + 13.38% tax), dated rate logs, parking, cancellation deadlines, ≤30-min walk filter (verified walking times only), per-row Google Maps walking-route links
- `trip.html` — trip cost calculator: entries × buy-ins + nights × true hotel cost, all inputs traceable
- `venetian.html` / `wynn.html` / `others.html` — one page per venue with its events + hotels
- `flagged.html` — flagged irregularities & unverified values (published, never silently resolved)
- `questions.html` — open decisions/missing info with impact and resolution paths
- `suggestions.html` — decision-only suggestions (nothing implemented until chosen)
- `sources.html` — every official source with last-checked date
- `changelog.html` — change-monitoring log (dated, with changed values flagged)
- `decisions.html` / `review.html` — legacy redirects to `suggestions.html` / `flagged.html`

## Data & build pipeline

```
data/feature/dataset.py      canonical dataset: source registry, rule templates with verbatim
                             excerpts + retrieval dates, 37 Venetian DSE IV structure-sheet
                             groups (93 schedule rows), Wynn dailies + 58 WPT festival rows,
                             Bellagio/Caesars rows, hotels with dated rate logs
        │
        ▼
scripts/build_site2.py       expands + VALIDATES (hard gate): every row needs an official
                             https source + last-checked date; every "confirmed" rule needs a
                             verbatim excerpt; hotel totals must satisfy rate+fee+13.38% tax math
        │
        ▼
assets/data.js               embedded dataset consumed by assets/app.js (works on file:// too)
data/feature/*.json          auditable artifacts (events, hotels, sources, flagged, changes…)
```

Verify end-to-end with `python3 scripts/verify_site2.py` (rebuild + policy + link + element checks).

## Scheduled re-check (change monitoring)

`scripts/scrape_daily.py` (GitHub Actions cron via `.github/workflows/feature-recheck.yml`, 14:00 UTC daily, or run locally) fetches every official URL in the source registry, hashes the content, and on change: flags affected rows and appends a dated entry to `data/feature/changes.json` → surfaces on `changelog.html`. Hotel rate captures are append-only dated log entries, never overwritten.

## Research policy

- Official operator sources only (property pages, official CDN/PDF documents). Aggregators never feed rows.
- **No tournament is labeled single-entry unless official rules say so.** As of 2026-11-17, zero events are confirmed single-entry/freezeout: all 37 Venetian structure sheets, Wynn structures, Bellagio PDFs and the Caesars flyer were read line by line; only Venetian Events #18/#58 state entry-count terms (they price subsequent buy-ins), and omission of re-entry language is not confirmation. Candidates with no contrary evidence are labeled "unverified".
- Guarantee ÷ entry-fee ratios are descriptive only. Bounty guarantees include bounty money where the official sheet says so and are labeled non-comparable; satellites pay seats, not cash.
- The data is a point-in-time snapshot, not a live feed or booking quote.

## Run locally

Open `index.html` directly, or serve the repository root with any static-file server. No build tooling or third-party runtime dependencies. Deployed with GitHub Pages via `.github/workflows/pages.yml` → https://karagemop466-tech.github.io/Poker4/

## Preserved parallel dashboards, monitors & data sets (other sessions)

The root dashboard above is the d1d02f59 integration round. Earlier and parallel session outputs are preserved untouched and reachable at their own paths:

## Parallel build: `v2/` (session 98e4cb1c)

A parallel dashboard lives in **[`v2/`](v2/index.html)** and is generated from one verified data layer
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

## Pages

`index.html` (executive brief) · `tournaments.html` · `schedule.html` · `hotels.html` · `ratelog.html` ·
`calculator.html` · `venues.html` + `venues/*.html` · `monitor.html` · `workflow.html` · `questions.html` ·
`suggestions.html` · `review.html` · `sources.html` · `repo-review.html`

Prior research sets from parallel sessions are preserved under `c07371e3/`, `60fb62da/`, `df41f5c6/`, `strip/`,
`verified/`, `pages/` and are linked from the Flagged for Review page as independent snapshots.

## Build & verify

```bash
python3 tools/build_data.py     # canonical data generator (722a84d2): data/tournaments.json,
                                # data/flagged.json, data/rate-log.json — official facts only
python3 tools/build_site.py     # regenerate the parallel dashboard HTML (08f07d1d)
python3 tools/verify_site.py    # internal-link + row-source verification
```

No third-party dependencies. Deployed on GitHub Pages (source: `main`, path `/`) via `.github/workflows/pages.yml`;
the source monitor runs daily via `.github/workflows/monitor.yml`.

The canonical root dashboard (index/tournaments/schedule/hotels/venues/…) is the fully verified build from
session `arena/722a84d2-poker4`: all 37 Venetian DSE IV structure sheets read line-by-line, Wynn daily +
WPT official PDFs, 97 events + 7 satellites, every row with official source excerpts, retrieval dates and
last-checked. Parallel research sites from other sessions are preserved and linked from the root index
(`planner/`, `poker4/`, `v2/`, `venues.html`, `calculator.html`, `change-monitor.html`, `ratelog.html`,
`monitor.html`, `repo-review.html`), with their superseded root-page snapshots kept in `pages/parallel-main-*`.
The previous consolidated-data generator is preserved at `tools/build_data_consolidated.py`.

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

## Integration update (2026-11-17, d1d02f59 final integration)

The root dashboard is the **d1d02f59 integration build** described above. Root pages that earlier sessions
published at the root were superseded by it (the repo-wide precedent: an earlier integration archived its
predecessor at `prior_root_dashboard/`). Nothing is deleted from history or from session-owned folders:

- `prior_root_dashboard/` — archived root dashboard from before the 2026-11-17 integration rounds (pages, `assets/`, `data_v2_json/`)
- `planner/`, `poker4/`, `v2/`, `60fb62da/`, `c07371e3/`, `df41f5c6/`, `verified/`, `strip/`, `pages/` — parallel-session sites and research sets, untouched
- Builders per scope: this integration = `scripts/build_site2.py` (+ `scripts/verify_site2.py`); other sets keep their own builders (`tools/build_root_site.py`, `tools/build_site.py`, `tools/v2_build.py`, `tools/build_poker4.py`, …)

### Scheduled monitors (all preserved, none removed)

| Workflow | Scope | Cron |
|---|---|---|
| `.github/workflows/feature-recheck.yml` | **this site** (`data/feature/*`, `assets/data.js`) via `scripts/scrape_daily.py` | 14:00 UTC |
| `.github/workflows/recheck.yml` | session 0f6c627b (`tools/recheck.py`, `tools/daily_schedule.py`) | 06:00 UTC |
| `.github/workflows/monitor.yml` | session 98e4cb1c (`tools/monitor_sources.py`) | daily |
| `.github/workflows/source-recheck.yml`, `v2-monitor.yml`, `tournament-monitor.yml`, `poker4-site-verify.yml` | other sessions' data sets | as scheduled |

### Board irregularity noted

`README.md` on `main` briefly carried committed conflict-marker lines (an `<<<<<<< HEAD` / `>>>>>>> origin/main`
pair inside the "Scheduled monitors" section). The integration README above supersedes it and is marker-free.
Logged as irregularity F18 on the Flagged page.
