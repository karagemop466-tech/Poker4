# Strip Poker Planner — Las Vegas Strip tournament & stay dashboard

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
