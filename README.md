# Poker4 — Vegas Strip live-poker tournament & stay planner

Static, source-first planning dashboard for live poker tournaments on the Las Vegas Strip (Nov 16 – Dec 23, 2026) and the hotels around them. Every value shown as confirmed links to an official operator page or official PDF; unknown or conflicting values are **blank and flagged** — never inferred. Data snapshot dated **2026-11-17**.

- `index.html` — executive summary (every figure counted at build time), the ranked screening table, the hotels table, open questions/suggestions/flags entry points
- `tournaments.html` — master event table: global search, date/venue filters, "single-entry confirmed only" toggle, and the four sections the brief asks for — single-entry/freezeout · not confirmed · more-money-buys-an-advantage · Day-2 restarts — with the descriptive guarantee ÷ entry-fee figure beside each row (never a forecast)
- `compare.html` — the events that passed the gates, side by side: guaranteed pool, entry cost and fee split, starting stack and blind length, payout structure and daily schedule fit, with the date/venue selectors
- `plan.html` — day-by-day plan: one primary event and one conditional fallback per day, with the printed late-registration deadline as the only sequencing evidence and the printed Day-2 restart as the only end-of-day evidence
- `hotels.html` — true cost per night (published rate + mandatory resort fee, both taxed at 13.38%), the dated rate log, parking, the ≤30-minute walk filter and per-row walking-route links
- `calculator.html` — trip cost: entries × buy-ins + nights × true hotel cost
- `before-you-pay.html` — the re-confirmation step: the seven things to re-check before a non-refundable payment, the official document behind every planned entry and every hotel line, what is still unverified on each row, and the exact words to ask each room
- `venues/venetian.html`, `venues/wynn.html`, `venues/bellagio.html`, `venues/caesars.html` (plus `venues/aria.html`, `venues/others.html`) — one page per room with its events, hotels and sources
- `questions.html` — what is known, what is missing, and how each gap gets closed
- `suggestions.html` — decision-only proposals; nothing is adopted until chosen
- `flagged.html` — every irregularity and unverified value, with its source link
- `review.html` — source status, run log, value-change log, and the **value-level audit**

## Data & build pipeline (what actually produces the published pages)

```
data/tracked-sources.json    the official URL registry (Venetian series calendar + 37 structure
                             sheets, Wynn daily + WPT structure booklets, Bellagio sheets, hotel
                             fee/terms pages, room pages) — re-fetched by the scheduled job
        │
tools/sync_official_sources.py   fetch → hash → verbatim capture in data/raw/*, field extraction
        │                        → data/schedule-snapshot.json, structure-audit.json,
        │                          hotel-facts.json, url-checks.json, change-log.json
        │
tools/room_extract.py        reads the committed captures in data/raw/* and emits
        │                    data/room-facts.json: one record per printed play day with the printed
        │                    buy-in, the printed fee split, the printed entry/re-entry/add-on rule,
        │                    the sentence behind each, and the retrieval date
        │
scripts/integrate_data.py    merges room-facts.json + schedule-snapshot.json + the audited
        │                    structure sheets into data/site-events.json, data/day-plan.json,
        │                    data/rate-log.json, data/walks.json, data/search-index.json, and renders
        │                    every root page, venues/*.html, site.css and app.js
        ▼
root HTML + venues/*.html    published by GitHub Pages from the repository root
```

Gates that must pass before a page is publishable (all run in CI and locally):

```
python3 tools/room_extract.py        extraction integrity: every WPT sheet must yield a play day,
                                     a fee split and a registration clause; a failure stops the build
python3 scripts/audit_values.py      value-level audit: every published figure and every quoted
                                     rule sentence is matched, word for word, against the official
                                     captures and transcriptions committed in the repository
python3 scripts/integrate_data.py    rebuild; must be byte-stable on a second run
python3 scripts/verify_root.py       links, per-row official source, data files parse
python3 scripts/verify.py            policy: every table row links an official source, no invented value
python3 scripts/verify_markup.py     every page parses as HTML
python3 scripts/linkcheck.py         every internal link resolves
```

## The value-level audit

`scripts/verify_root.py` proves a row **has** a source. `scripts/audit_values.py` proves the value
**came from** it. It re-reads every official capture committed in `data/raw/` (each file headed by
the URL it came from and the SHA-256 of the response) and every committed verbatim transcription
of the official structure sheets, then looks for the literal evidence behind each published
buy-in, guarantee, starting stack, start time, registration deadline, house fee, prize-pool
contribution and every sentence shown in a "source text" panel. A value it cannot find is
reported, never corrected, and fails the deploy.

Two independent cross-checks run with it: every published Wynn `(date, time)` pair must be printed
in the official WPT structure booklet, and every published guarantee ÷ entry-fee ratio must
recompute from its own row. The result is committed to `data/audit-values.json` and summarised on
`review.html` (the *Value-level audit* section). The file is keyed to the snapshot rather than to
the run, so it is byte-stable and CI can prove the committed result is current.

A sentence the build assembled itself is never shown as a quote: it is labelled
*reworded from the printed figures*, and the audit checks it by content instead — every dollar
figure must be printed by the sheet, and the wording must be one the operator is proven to use
elsewhere in the same series.

On 2026-11-19 the audit found and this repository fixed three real defects: the Wynn WPT fee
quote printed its label twice and swallowed the next section's heading; the Venetian Valuetown
re-entry quote began and ended in the middle of a word; and the Venetian house-fee sentence was
assembled from the parsed numbers and presented as a copy of the sheet's line.

`data/feature/*` and `scripts/build_site2.py` / `verify_site2.py` remain in the tree as an earlier,
still-auditable dataset and validator; they do not build the pages that are published today.
`tools/verify_root_site.py` checks the superseded pre-integration page set and is no longer used as a gate.

## Scheduled re-check (change monitoring)

`scripts/scrape_daily.py` (GitHub Actions cron via `.github/workflows/feature-recheck.yml`, 14:00 UTC daily, or run locally) fetches every official URL in the source registry, hashes the content, and on change: flags affected rows and appends a dated entry to `data/feature/changes.json` → surfaces on `changelog.html`. Hotel rate captures are append-only dated log entries, never overwritten.

## Research policy

- Official operator sources only (property pages, official CDN/PDF documents). Aggregators never feed rows.
- **No tournament is labeled single-entry unless official rules say so.** As of 2026-11-17, zero events are confirmed single-entry/freezeout across all 252 published rows: the 37 Venetian structure sheets, the 69 Wynn WPT event sheets, the Wynn daily structures, the three Bellagio sheets and the Caesars page were read line by line. What those sheets *do* print is re-entry: Wynn prints unlimited re-entry on 67 of 69 WPT sheets and a one-entry-plus-one-re-entry cap on the other two (the $10,400 World Championship states "Four (4) Entries maximum"), Bellagio prints "buy-in and re-enter through the end of level 8", and the Venetian Valuetown sheet prices subsequent buy-ins. Those rows are published with the quote and kept out of the single-entry list. Omission is never confirmation, so a silent sheet is labelled "unverified", not "freezeout".
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
Walking minutes are measured Google Maps walking directions (mode=walking), retrieved 2026-11-17 for every hotel→Venetian poker-room pair and stored with the route distance, the "via" road, the exact directions URL and the retrieval date in `data/integrated/walks-google.json` (mirrored into `data/walks.json`). No Strip property publishes its own door-to-door walking time, so Google Maps is the measurement source; its durations run optimistic, so the route distance is shown beside every minute. The ≤30-minute filter is a hard filter on these measured values.

All values shown as confirmed link to the official operator source, with retrieval dates. Unknown or ambiguous values are blank and flagged — never inferred. All 37 Venetian DeepStack Extravaganza IV structure sheets were read in full on 2026-11-17 and none states a single-entry, re-entry, or add-on limit; consequently **there is exactly one window-wide fact to plan around: no event is classified as verified single-entry.** Rooms that do publish rules (Wynn, Bellagio, Caesars) all allow some form of re-entry, rebuy, or add-on and are listed separately. The data is a point-in-time snapshot plus a daily change monitor — not a live feed or a booking quote.

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

## 2026-11-17 policy notes added by this pass (source precedence and dead URLs)

- **A fee published by a hotel is taken from the property's reservation-terms page, not its marketing fee page.**
  Bellagio's and ARIA's `$55.00 plus applicable tax` daily resort fee, the `$50 plus tax per occupant, per night, above 2
  occupants` charge and the 72-hour cancellation deadline come from `bellagio.mgmresorts.com/en/terms-and-conditions.html`
  and `aria.mgmresorts.com/en/terms-and-conditions.html` (footer `Updated on August 26, 2026`); parking comes from the
  operator rate table at `mgmresorts.com/en/things-to-do/parking.html` that those pages point to. Bellagio's
  `/en/hotel/resort-fee.html` is a live HTTP 404 — the fee figure is *not* taken from a third-party site to fill it.
- **When a room's summary article and its schedule document disagree, both sentences are published and the row is flagged.**
  The Caesars Palace daily slate was rebuilt from the property's own 2026 flyer
  (`clv-poker-daily-nlh-tournament-flyer-2026.pdf`), which prices 2 PM and 9 PM at **$160** and splits the fee
  ($115/$45) while 10 AM and 6 PM stay $100 ($70/$30); Caesars' July 2026 article says "Every event carries a $100
  buy-in". Nothing silently picked one.
- **A dead official URL is repointed only to a live successor on the same operator's own path, and the dead one stays on the
  record** in `data/url-checks.json` with a `superseded_by` note, so the change is auditable on `review.html`.
- **Recurring slates publish their printed weekday.** Wynn's daily poster, Bellagio's weekend sheets and Caesars' flyer carry
  no calendar date, so their rows now state the weekdays the document prints (`data.site-events.json` → `recurrence`) and
  `tournaments.html`'s date filter can keep them when the chosen range covers one of those weekdays. A row with neither a
  date nor a printed weekday is still hidden by a date filter and says so.
- **The 8 AM–close plan lists the recurring evening slates as options, never as booked entries**: each day shows which
  weekday-printed events start at or after the lead event's printed registration deadline, with the arithmetic sentence and
  no invented finish time.
