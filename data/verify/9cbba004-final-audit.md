# Final request audit — `arena/9cbba004-poker4`

**Date:** 2026-11-19 (UTC)  
**Current data snapshot:** `2026-11-19T19:48:43Z` (`data/sync-status.json`)  
**Scope:** independent check of the integrated dashboard and repository against the request; no tournament or hotel value was changed by this audit.

## Verification performed

The source-sync, extraction, audit, build, and site gates were run on the rebased tree (which includes the latest hotel curation and official-source sync):

| Check | Result |
|---|---|
| `python3 tools/room_extract.py` | WPT 69, Wynn daily 4, Bellagio 3, Caesars 4 printed start times; 0 unparsed WPT blocks. WPT-08's printed fee split is inconsistent (1105 vs 1100) and remains verbatim and flagged. |
| `python3 scripts/audit_values.py --strict` | 1,807/1,807 values located; 0 blocking failures; 148/148 Wynn date-time pairs and 166/166 guarantee ratios cross-checked. Evidence: 56 hashed captures and 37 transcribed structure sheets. |
| `python3 scripts/integrate_data.py` | 253 events, 38 plan days, 147 dated rate-log lines, 12 measured walk records, 71 tracked sources. Generated pages stayed byte-for-byte unchanged relative to the committed tree. |
| `python3 scripts/verify_root.py` | 16 pages, 253 rows, 147 rate-log lines, 71 tracked sources, 0 warnings. Every row has an official source or an explicit unverified marker. |
| `python3 scripts/verify.py` | Pass: table rows link official sources; internal references and data references are valid. |
| `python3 scripts/verify_markup.py` / `scripts/linkcheck.py` | 39 pages parse; 32 pages' internal links resolve; 0 problems. |
| Additional compatibility checks | `node --check app.js`, `scripts/validate_site.py`, `tools/check_rows.py`, `tools/verify_poker4.py`, and `tools/poker4_monitor.py --selftest` all pass. The row check found 0 mismatches among 93 checked official rows. |

The daily official-source sync is run by GitHub Actions. The latest completed sync on the preceding main commit is run [44602157558](https://github.com/karagemop466-tech/Poker4/actions/runs/44602157558); the current snapshot and row-level check dates are committed with the resulting pages. This session did not independently re-fetch every operator domain; source assertions remain tied to the official captures and dated live re-reads recorded under `data/verify/` and in `COORDINATION.md`.

## Request coverage and limits

The current root dashboard includes the executive summary; tournament search, date and venue filters, and the strict single-entry filter; event rule fields with source excerpts and retrieval dates; guaranteed-pool/entry-fee descriptive ratios; separate re-entry/add-on, bounty, flight, restart, and satellite sections; per-venue pages; a daily primary/fallback plan; trip-cost calculator; hotel fees, rate log, official booking links, and walking-route filter; source-change monitoring; questions, suggestions, and a Flagged for Review page.

The checks confirm these features are present, but they do not make unavailable source facts appear:

- **0 of 253 events are confirmed single-entry/freezeout.** Silent sheets remain unverified; the toggle therefore returns no qualifying rows. Do not treat this as a recommendation to enter a multi-entry event.
- **No dated checkout total is captured for most properties.** Official booking pages that require an interactive booking session are linked; checkout total, nightly average, and cancellation deadline remain blank unless an official dated capture exists. The dated rate log preserves rate/fee-only observations instead of inventing a stay total.
- **There is no fixed owner-specific booking scenario.** Exact trip dates, occupancy, maximum nightly budget, and hotel quality floor were not provided. The displayed event window is the official schedule window, not an asserted vacation booking; the calculator does not present a personalized hotel choice.
- **The current schedule feed covers the official sources recorded in the repository, not every Strip poker room.** Where a property does not publish a dated public schedule or the source has not been verified, the dashboard leaves the schedule blank and records the coverage gap. The daily scraper does not establish comprehensive Strip-wide coverage.
- **No verified 8:00 AM start and no official finish times are printed in the current window.** The planner uses printed start/late-registration information and marks possible overlap; it does not promise that an event can finish in time for another.
- **Walking measurements are currently hotel-to-Venetian routes.** They are Google Maps route measurements, not operator-published times. The 30-minute filter only applies where the route record exists.
- **13.38% tax basis and the WPT-08 printed fee-split mismatch remain flagged.** Neither was silently corrected or generalized beyond its evidence.

These limitations are already listed on the public [`Flagged for Review`](https://karagemop466-tech.github.io/Poker4/flagged.html) and [`Open Questions`](https://karagemop466-tech.github.io/Poker4/questions.html) pages. See flags F1, F4, F10, F16, F22, F27, F38, F44–F47 and the questions page for the supporting excerpts and steps needed to close them.

## Deployment check and repair

The repository's Pages API reported the site as **built**, with source `main:/` (branch publishing). On main commit `caa06b6062e78d3b7cb0482bef229b7a6f9b7044`, the GitHub-managed `pages-build-deployment` run [44602314553](https://github.com/karagemop466-tech/Poker4/actions/runs/44602314553) succeeded, and the live overview was fetched successfully.

A separate custom deploy workflow, `.github/workflows/pages.yml`, failed on run [44602157621](https://github.com/karagemop466-tech/Poker4/actions/runs/44602157621) with `No artifacts named "github-pages" were found for this workflow run`, while the branch-source Pages build succeeded. Because the repository is configured to publish `main:/`, this PR removes the redundant custom deploy lane rather than changing the live publishing source. After merge, confirm the next `pages-build-deployment` run is successful and the live URL still serves the current snapshot.

## Official source index for manual review

The full 71-URL registry, current check state, raw captures, and event-specific source links are in [`data/tracked-sources.json`](../tracked-sources.json), [`data/url-checks.json`](../url-checks.json), and [`data/raw/`](../raw/). Primary operator documents include:

- [Venetian DeepStack IV schedule](https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html) and its [official schedule PDF](https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/dse-nov-2026-schedule.pdf); individual structure-sheet URLs are in the tracked-source registry.
- [Wynn poker room](https://www.wynnlasvegas.com/casino/poker), [daily tournament poster](https://cdn.wynnresorts.com/image/upload/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf), and [WPT World Championship structures](https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf).
- [Bellagio poker room](https://bellagio.mgmresorts.com/en/casino/poker.html) and its three official Friday/Saturday/Sunday structure PDFs, listed in `data/tracked-sources.json` as `B_SHEET_FRI`, `B_SHEET_SAT`, and `B_SHEET_SUN`.
- [Caesars Palace 2026 daily tournament flyer](https://www.caesars.com/content/dam/empire/clv/casino/poker/tournament-schedule/clv-poker-daily-nlh-tournament-flyer-2026.pdf) and its [poker-tournament summary page](https://www.caesars.com/las-vegas/explore/casino/poker-tournaments-las-vegas-strip); disagreements are retained and flagged.
- Official hotel fee, tax, parking, and cancellation terms are linked by property on [`hotels.html`](https://karagemop466-tech.github.io/Poker4/hotels.html) and indexed in `data/tracked-sources.json`. The county room-tax letter and walking-route records are linked from the relevant hotel rows.
