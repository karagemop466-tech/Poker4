# Coordination board

Last updated: 2026-11-16 (UTC)

Session `6313b65a` is operating only on the fixed active branch `arena/6313b65a-poker4`. Work was handled sequentially because no separate worker sessions are available. Research and the first dashboard build are complete; final PR/deployment steps are pending.

| Task | Status | Owner | File scope | Notes |
|---|---|---|---|---|
| Verify official-source research for upcoming Strip-area tournaments and nearby hotel costs; record evidence and unknowns | complete | `6313b65a` | `research/`, `COORDINATION.md` | Full dated evidence and unresolved items are in `research/VERIFICATION.md`. No reviewed official terms prove a strict one-entry maximum. |
| Build the decision dashboard and verified data tables | complete | `6313b65a` | `site/`, `README.md`, `scripts/` | Responsive static dashboard, row-level official links, search/status filters, CSV export, print layout, hotel caveats, source register, and validator are implemented. |
| Final integration, link/build checks, GitHub Pages deployment, PR and merge | pending | `6313b65a` | `.github/`, `COORDINATION.md` | Local checks pass. Next: commit and push only this branch, open a PR to `main`, obtain confirmation before merging, then check the Pages workflow/deployment. None of those GitHub outcomes has happened yet. |

## Verification log

- Repository baseline contained only the starter `README.md`; no application or Pages workflow existed.
- `research/VERIFICATION.md` records the official-source evidence, method, limitations, and follow-up questions. The strict test requires one paid entry **for the whole event**, with no re-entry, rebuy, add-on, or paid extra chips. Unknown terms are never treated as freezeout terms.
- Current site data contains 8 reviewed dated event IDs represented by 9 scheduled start rows (Event #1 has two upcoming flights), 11 recurring room schedules, 3 selected WPT festival events, 7 hotel comparisons, and 43 official source links.
- The strict single-entry confirmed count is **zero**. All nine dated start rows remain unverified: Venetian Event #1 is multi-flight with no confirmed event-wide entry cap; the reviewed Venetian one-day sheets omit entry terms. Daily formats with explicit re-entry/add-on rules remain outside the strict-entry table.
- The dashboard schedule starts its day view at 8:00 a.m. without inventing an 8:00 event. Earliest recurring published start is 9:00 a.m. at Horseshoe (buy-in/rules unavailable in the reviewed official sources). Selected dated Venetian flights begin Nov. 17 at 11:10 a.m.; later RaceDay dates begin at 10:10 a.m.
- Official nightly fee evidence: Venetian, Wynn, ARIA, Bellagio $55 + tax; MGM Grand $50 + tax; Westgate $49.99 + tax, with a qualifying no-fee offer; Caesars’ generic $45–$60 + tax portfolio disclosure is not a property-specific quote. Exact all-in hotel totals are intentionally blank pending dates, stay length, room type, and occupancy.
- `python3 scripts/validate_site.py`, `node --check site/app.js`, and `git diff --check` pass. The validator checks required files, source IDs/HTTPS URLs, evidence links, date/status consistency, exact-fee caveats, and the zero-confirmed-entry assertion.
- Local preview is running as process `vegas-poker-research-dashboard-0153a62c` on port 4173; HTTP smoke checks returned 200 for the page, JavaScript, JSON, stylesheet, and favicon.

## Irregularities / handoffs

- “No confirmed strict single-entry event” is a statement about reviewed official evidence, not proof that no such event exists in Las Vegas. Unknown terms remain flagged.
- Official Bellagio content is inconsistent/stale in places: the main page contains old resumption wording, and the Saturday structure includes past dates and conflicting buy-in labels. Do not use its Saturday PDF as a future event without a corrected official source.
- MGM Grand’s official poker page lists daily times, but its linked schedule is titled “August Tournament Schedule”; its $120 structure offers extra chips and does not establish current re-entry terms.
- ARIA and Westgate confirm daily tournaments but lack reviewed event-level terms. Horseshoe lists six daily starts but not buy-ins/rules. Confirm current schedules directly before travel.
- Venetian/Palazzo poker-player starting rates are conditional and not date-specific; a $300+ tournament buy-in for the hotel rate does not verify an event’s entry limit. Exact room ranking/all-in totals await trip dates and a same-date official booking search.
- Researcher-selected exploratory booking dates are not quoted. No 8:00 a.m. start has been verified.
- No PR has been opened, no commit/push for the dashboard has occurred, no merge has occurred, and GitHub Pages has not deployed this build. Do not report these outcomes until verified.
