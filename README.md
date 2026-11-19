# Poker4 — Vegas Strip poker and stay planner

**Live dashboard:** <https://karagemop466-tech.github.io/Poker4/>

This is a source-first planner for live poker tournaments and hotels on and around the Las Vegas Strip. The current event window is November–December 2026. Official-source snapshots and per-row last-checked dates are shown in the site; use those timestamps rather than assuming a scheduled fetch has already completed. Unknown, conflicting, or unavailable values are left blank and flagged—not inferred.

## Dashboard pages

- [`index.html`](index.html) — executive summary, current findings, ranked screening ratios, and open decisions.
- [`tournaments.html`](tournaments.html) — event table with global search, date and venue filters, and a strict single-entry-confirmed filter. Date filters default to the upcoming part of the published window; “whole window” restores historical rows. The 7- and 30-day presets count inclusively. It separates events with re-entry/add-on or other extra-spend formats, flights, satellites, and restarts.
- [`compare.html`](compare.html) — side-by-side comparison of rows with confirmed entry fee and guarantee, including stack, blind length, payout details, and schedule fit; its date controls use the same upcoming default and whole-window reset.
- [`plan.html`](plan.html) — one primary event per day and a conditional fallback; it does not assume an unprinted finish time.
- [`hotels.html`](hotels.html) — property fees, dated rate log, parking/cancellation fields, route evidence, official booking links, and true nightly-cost calculations where inputs are available.
- [`calculator.html`](calculator.html) — entries × buy-ins + nights × true hotel cost; missing inputs are not filled with guesses.
- [`venues/`](venues/) — individual Venetian, Wynn, Bellagio, Caesars Palace, ARIA, and other-room pages.
- [`before-you-pay.html`](before-you-pay.html) — final re-confirmation checklist and the fields still missing before a non-refundable booking.
- [`questions.html`](questions.html) and [`suggestions.html`](suggestions.html) — answered/unanswered decision questions and proposed improvements.
- [`flagged.html`](flagged.html) — irregularities and unverified facts, with links to the relevant sources.
- [`review.html`](review.html) — source status, run/change log, and value-level audit.

## Research and comparison rules

- A confirmed table value must have an official operator source and evidence excerpt. Unknown or conflicting values remain blank and are marked for review. Third-party listings do not supply tournament or hotel facts.
- A tournament is not called single-entry merely because its structure sheet is silent. In the current 253-row snapshot, **zero rows are confirmed single-entry/freezeout**; the strict filter therefore returns none. Re-entry, rebuy, add-on, flight, bounty, and satellite formats are labeled separately.
- Events are ranked only when the total entry fee and guarantee are supported by the official source. Guaranteed pool ÷ entry fee is descriptive arithmetic, not a forecast. Bounty and satellite pools are not treated as directly comparable cash guarantees.
- Hotel rate history is a dated log, not a single overwritten price. The site provides official date-specific booking links. If an official booking engine does not expose a checkout total to the capture process, the total stays blank; resort fees, tax basis, parking, cancellation terms, and rate timestamps are shown separately when sourced.
- The 13.38% room-tax basis is sourced from official property terms and the Clark County letter; its application is not assumed for a property whose tax jurisdiction has not been confirmed (see F27).
- Walking minutes are Google Maps walking-route measurements to the Venetian poker room, not hotel-published travel times. The route distance, link, and retrieval date accompany the measured value; the 30-minute filter applies only to measured pairs.
- No official 8:00 AM tournament start or verified finish time is filled in where the schedules do not print one. The day plan uses printed start/late-registration information and labels fallbacks as conditional.

## Data pipeline and verification

The published root pages are generated from the committed official captures and curated data:

```text
data/tracked-sources.json
  → tools/sync_official_sources.py       re-fetch, hash, capture, and extract official URLs
  → tools/room_extract.py                derive printed room schedule/rule facts
  → scripts/audit_values.py --strict     verify published values against evidence
  → scripts/integrate_data.py            build the root tables and venue pages
  → scripts/verify_root.py, verify.py,
    verify_markup.py, linkcheck.py         enforce source, data, markup, and link gates
```

Run the local verification gates from the repository root:

```bash
python3 tools/room_extract.py
python3 scripts/audit_values.py --strict
python3 scripts/integrate_data.py
python3 scripts/verify_root.py
python3 scripts/verify.py
python3 scripts/verify_markup.py
python3 scripts/linkcheck.py
```

The value-level audit checks figures and quoted rule excerpts against the captured official text and committed structure-sheet transcriptions. On the 2026-11-19 snapshot it located **1,807 of 1,807** checked values with zero blocking failures. Re-run the audit after updating a source snapshot; the committed audit result must match the current snapshot.

### Scheduled monitoring and its limits

- `.github/workflows/url-check.yml` is the canonical daily official-source re-check. It refreshes captured sources, reruns extraction and the value audit, rebuilds the pages, and verifies the result. `data/url-checks.json`, `data/change-log.json`, `data/sync-status.json`, and each row's `last_checked` value show what was checked and whether a change was detected.
- `.github/workflows/maintenance.yml` saves a dated snapshot/report for its listed official schedule endpoints. Coverage is limited to sources recorded in the repository; it is **not** evidence that every Strip poker room publishes a machine-readable daily schedule. The dashboard and [`flagged.html`](flagged.html) identify schedule coverage gaps rather than inventing events.
- Schedules and hotel booking results can change between checks. Reconfirm event rules, rates, fees, occupancy, and cancellation terms directly with the operator before paying.

## GitHub Pages and repository layout

GitHub Pages publishes the repository root from **`main:/`**: <https://karagemop466-tech.github.io/Poker4/>. GitHub's branch-source Pages build is the deployment lane; the dashboard is not a booking service or a live rate guarantee. See [`COORDINATION.md`](COORDINATION.md) for the shared task board and integration/verification record.

The root pages and `scripts/integrate_data.py` are the canonical dashboard. Earlier parallel or superseded snapshots are retained for provenance and comparison in `archive/`, `prior_root_dashboard/`, `planner/`, `poker4/`, `v2/`, `strip/`, `verified/`, `60fb62da/`, `c07371e3/`, `df41f5c6/`, and `pages/`. Those archived pages are not the current root build or a substitute for the current verified data.
