# COORDINATION — shared task board

Repo: karagemop466-tech/Poker4 · Working branch: `arena/abd38ed7-poker4` (base `main` @ 52654c1)
Session ID: `arena-abd38ed7` (single active session on this branch)

Status values: unclaimed · in progress · done · needs review
"needs review" items are published on the **Flagged for Review** page and do not block anything.

## Task board

| # | Task | Status | Owner | Files (scope) |
|---|------|--------|-------|---------------|
| T1 | Repo review (README, git state, irregularities) | done | arena-abd38ed7 | `COORDINATION.md`, `docs/flagged.html`, `docs/sources.html` |
| T2 | Live tournament research — Las Vegas Strip, single-entry vs re-entry/add-on | done (19 verified single-entry rows; 31 schedule-only rows flagged) | arena-abd38ed7 | `data/tournaments.json` |
| T3 | Hotel research — resort fees, rates, walking (official sources only) | done (partial; rates & unconfirmed fees flagged) | arena-abd38ed7 | `data/hotels.json` |
| T4 | Executive summary, daily schedule plan, questions, suggestions | done | arena-abd38ed7 | `docs/summary.html`, `docs/schedule.html`, `docs/questions.html`, `docs/suggestions.html` |
| T5 | Site build (GitHub Pages, `/docs`), link check | done (10 pages; 0 broken internal links) | arena-abd38ed7 | `build/build_site.py`, `docs/*` |
| T6 | Integration: PR `arena/abd38ed7-poker4` → `main`, merge, Pages deploy check | pending | arena-abd38ed7 | this file |

## Task T1 — Repo review (done)
- Repo contents at base commit: `README.md` (`# Poker4`, 8 bytes) only. No code, no license, no CI, no `.gitignore`.
- Irregularities: README has no description; no license file; `main` has a single "Initial commit".
- Sources: GitHub repo itself (`https://github.com/karagemop466-tech/Poker4`).

## Task T2 — Tournament research (done)
- Sources: official property poker pages and PDFs (Wynn, Venetian, Caesars Palace, Bellagio) and WSOP official schedule. Full list in `docs/sources.html`.
- Verification: each row checked against the official schedule PDF/page and, where available, the official structure sheet (re-entry / add-on / guarantee / chips / prize-pool split).
- Rows not confirmed by an official structure sheet are NOT ranked; they appear on the Flagged for Review page with `unverified` labels.
- Irregularities logged on `docs/flagged.html`.

## Task T3 — Hotel research (done, partial)
- Only the Venetian resort fee ($55 + tax) was confirmed on an official property page.
- Wynn, Caesars Palace and Bellagio resort-fee figures could not be confirmed on official pages (third-party figures conflict: see Flagged).
- Nightly room rates are dynamic and were not confirmed from official sources → left blank.
- Walking times were not confirmed from an official map source → left blank; links to map directions are provided for manual review.

## Task T4 — Summary / questions / suggestions (done)

## Task T5 — Site build (done)
- Static site in `/docs`, built by `build/build_site.py` from `data/*.json`.
- Pages source: `main` branch, `/docs` folder (to be enabled after merge).

## Task T6 — Integration (pending)
- PR, merge, Pages verification and final record will be appended below.

## Session log
- 2026-11-16 18:55 UTC — arena-abd38ed7 claimed T1–T6 on branch `arena/abd38ed7-poker4`.
- 2026-11-16 — T1, T2, T3 research completed; official sources fetched on 2026-11-16 (see `docs/sources.html`).
- 2026-11-16 — T4 complete; T5 built with `python3 build/build_site.py` (0 broken internal links).
- Irregularities logged on `docs/flagged.html` (conflicting third-party resort fees, undated Bellagio/Caesars schedules, stale Bellagio notice, Bellagio $1,000 vs $1,100, Venetian event-number reuse, Wynn WPT footnote conflicts, unreachable venue pages).

## Other session preserved from `main` (PR #1, branch `arena/25b96c20-poker4`)

Merged to `main` before this session's PR. Kept verbatim below. Reconciliation is logged in the session log above and on the Flagged for Review page of the verified planner (`verified/`).

# Coordination board

Session: `arena/25b96c20-poker4` (current Arena branch; branch name is fixed by the workspace).

| Task | Status | Owner | Files |
|---|---|---|---|
| Research official live Las Vegas poker schedules, formats, hotel costs, decision gaps; build sourced dashboard and review page | in progress | arena/25b96c20-poker4 | all project files |

## Activity log
- 2026-11-16: Inspected repository before work; no existing coordination file, tasks, or other session claims. Repository initially contained only README.md. Claim recorded here. This workspace is a single active branch; no separate session branch will be created.
- 2026-11-16: Built static dashboard and category pages. Tournament evidence source: official Venetian DeepStack Extravaganza IV schedule (linked on each event row); facts captured are future event dates/times, buy-ins, published selected GTDs and format labels. No single-entry assertion made because schedule listing does not confirm max entries/rebuy/add-on. Hotel properties link official sites; prices/fees intentionally blank without dated official quote. Added explicit decision checklist and flagged-review page.
- Verification: HTML local-link audit run (see output in task session); checked official Venetian page content directly. Arithmetic ratios: $10,000/$300=33.3x; $8,000/$200=40x; $15,000/$400=37.5x; $30,000/$600=50x. These are labeled guarantee/buy-in ratios, not EV. No dates/occupancy supplied; official hotel pricing not asserted.
- Irregularities: an official future schedule does not prove events will operate unchanged; schedule gives no entry/add-on terms or future actual pools; no comprehensive all-room official source inventory or door-to-door route confirmation. See review.html.

## Reconciliation request (logged by arena-abd38ed7)
- The root dashboard (`index.html`, `tournaments.html`, `hotels.html`, `questions.html`, `review.html`) states "0 verified single-entry" because its tournament rows were not checked against structure sheets.
- This session checked structure sheets (Venetian structure sheets 1, 5, 6, 7, 29) and found 19 single-entry rows. Those are published in `verified/`.
- Both sites are kept. Root dashboard is unchanged except for a banner pointing to `verified/`. Owner of the root dashboard should confirm which set is authoritative before any further change.

---

## Session arena-0337316e (branch `arena/0337316e-poker4`)

Parallel-session rules: claim a task here before editing; use branch `session-<id>/<task>` where a parallel branch is allowed; small commits; `git pull --rebase` before push; log conflicts in the activity log below; only the integration session edits shared outputs (table data, index, navigation).

Note: this session's Arena branch is fixed as `arena/0337316e-poker4`. The `session-<id>/<task>` naming is superseded for this session by the branch rule, so the work is on that one branch.

Site location: this session publishes to `/strip/` (folder `strip/`) so it does not overwrite the root dashboard from `arena/25b96c20-poker4`.

| # | Task | Status | Owner | Files in scope |
|---|------|--------|-------|----------------|
| T1 | Repo review and irregularity log | in progress | arena-0337316e | `strip/flagged.html`, `strip/sources.html` |
| T2 | Strip poker tournament research (single-entry) | in progress | arena-0337316e | `strip/data/events.csv`, `strip/tournaments.html`, `strip/separate.html` |
| T3 | Hotel research (cost, resort fee, walking) | in progress | arena-0337316e | `strip/data/hotels.csv`, `strip/hotels.html` |
| T4 | Day schedule, analysis, executive summary | in progress | arena-0337316e | `strip/index.html`, `strip/schedule.html`, `strip/analysis.html` |
| T5 | Questions and site-improvement suggestions | in progress | arena-0337316e | `strip/questions.html`, `strip/suggestions.html` |
| T6 | Site build, link check, Pages publish, PR and merge | in progress | arena-0337316e | `strip/build.py`, `strip/assets/*`, `strip/*.html` |

## Activity log (arena-0337316e)
- 2026-11-16: Claimed T1–T6. Built `strip/` from official sources in `strip/data/*.csv`; `strip/build.py` regenerates all pages.
- 2026-11-16: Merge conflict (add/add) on COORDINATION.md with origin/main. Resolved by keeping the upstream board in full and appending this section. Upstream claims are not changed.
- 2026-11-16: Upstream irregularity: the `arena/25b96c20-poker4` log says "no separate session branch will be created". This session uses its own branch under the same board; both are listed here.
- 2026-11-16: PR from `arena/0337316e-poker4` to `main`: https://github.com/karagemop466-tech/Poker4/pull/5 (merge requested without waiting for review; unverified and flagged items are published on the Flagged for Review page, which does not block the merge).

- 2026-11-16: Upstream merged `arena/abd38ed7-poker4` (PR #3) with a `verified/` site. This session's `strip/` folder is a separate subsite, so the two do not overwrite each other. Both boards are kept in this file.

---

## Session df41f5c6 (branch `arena/df41f5c6-poker4`)

Session ID: `df41f5c6`. Site published at `/df41f5c6/` (folder `df41f5c6/`). Data in `data/df41f5c6/`. Build: `python3 scripts/build.py`; check: `python3 scripts/verify.py`.
Scope note: the session brief asks for `session-<id>/<task>` branches. The Arena branch is fixed as `arena/df41f5c6-poker4`, so all tasks are on that one branch, committed in order.

| # | Task | Status | Owner | Files in scope |
|---|------|--------|-------|----------------|
| T1 | Repo review and irregularity log | done | df41f5c6 | `df41f5c6/repo-review.html`, `df41f5c6/flagged.html` |
| T2 | Single-entry tournament research (live, upcoming, ranked by buy-in, then GTD) | done (42 Venetian + 22 Wynn main-list rows; 9 separate-section rows) | df41f5c6 | `data/df41f5c6/tournaments.json`, `df41f5c6/tournaments.html`, `df41f5c6/other-formats.html` |
| T3 | Hotel research (resort fees, all-in per night, walking) | done (partial; 1 official fee; walking not verified for any hotel) | df41f5c6 | `data/df41f5c6/hotels.json`, `df41f5c6/hotels.html` |
| T4 | Day schedule, executive summary | done | df41f5c6 | `df41f5c6/schedule.html`, `df41f5c6/index.html` |
| T5 | Questions and site-improvement suggestions (decision-only) | done | df41f5c6 | `df41f5c6/questions.html`, `df41f5c6/suggestions.html` |
| T6 | Site build and link check | done (10 pages; verify.py OK) | df41f5c6 | `scripts/build.py`, `scripts/verify.py`, `df41f5c6/*` |
| T7 | Flagged for Review page | done (29 items) | df41f5c6 | `df41f5c6/flagged.html`, `data/df41f5c6/flagged.json` |
| T8 | Sources list | done (17 official sources) | df41f5c6 | `data/df41f5c6/sources.json`, `df41f5c6/sources.html` |
| T9 | Integration: merge with `main`, PR, merge, Pages check | in progress | df41f5c6 | this section |

### Log (df41f5c6)
- 2026-11-16: Claimed T1–T9 (commit 9e83ee9). Commit 34e6221 added the data, build and verifier, first under `data/` and `docs/`.
- 2026-11-16: **Merge conflict.** PR #6 from `arena/df41f5c6-poker4` to `main` was not mergeable (`CONFLICTING`) after `main` gained PR #3 (`arena-abd38ed7`) and PR #5 (`arena-0337316e`). Conflicting paths: `COORDINATION.md`, `data/tournaments.json`, `data/hotels.json`, and the `docs/` names. **Resolution:** merged `origin/main` into this branch. Other sessions' files were kept exactly as they were on `main`. This session's files were moved to session-scoped paths (`data/df41f5c6/`, `df41f5c6/`) and its build was re-pointed to them. No file from another session was overwritten or deleted. The shared board above is kept verbatim.
- 2026-11-16: Note for the other sessions: `data/tournaments.json` and `data/hotels.json` on `main` (PR #3) are not used by this session's site. This session's data is `data/df41f5c6/`. The `docs/` folder used by PR #3's build was not created on `main` by this session.
- 2026-11-16: Correction recorded. The earliest main-list verified start is 10:00 AM (Wynn, Dec 10). The only earlier verified start is a 9:10 AM Venetian satellite (#46), shown on the other-formats page only.
- Pages: the workflow `.github/workflows/pages.yml` on `main` uploads the repo root, so `/df41f5c6/` is published with no settings change. The site is verified after the merge.

---

## Session arena/60fb62da-poker4 (session `60fb62da`)

| Task | Status | Owner | Files in scope |
|---|---|---|---|
| Independent official-source Venetian schedule/hotel audit and decision dashboard | needs review | arena/60fb62da-poker4 | `60fb62da/*`; this appended coordination entry only |

- At task start, this checkout contained only the initial README and no coordination file. The initial integrated dashboard was built on the assigned Arena branch. As other sessions' PRs began merging into `main`, the root index/navigation/data became shared integration scope. To avoid overwriting other sessions, this session's verified independent dashboard is isolated at `/60fb62da/`; root files are restored from upstream `main`. Existing PR #1/#3/#5/#6 research remains preserved in the repository and board.
- Conflict log: the initial PR #2 merge attempt was blocked after upstream PR #1 merged. A subsequent merge of the latest `origin/main` conflicted only in `COORDINATION.md`. Resolution: keep the latest upstream board verbatim and append this session's owner, findings, sources and verification log. All other sessions' files were preserved. The dashboard was moved to the session-scoped subdirectory and local links were retested.
- Official tournament sources checked directly: [Venetian DeepStack Extravaganza IV full schedule](https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html) (all four page chunks); official structure PDFs for Events #2/#12, #3–5, #6, #10, #14/#28/#63, and #27. Verified dates/times, event names, buy-ins and guarantees as published. No reviewed candidate rules confirm one entry only or prohibit re-entry/rebuy/add-on; zero are marked confirmed single-entry.
- Official lodging/location sources: [Venetian poker suite rates/play terms](https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html), [resort fee](https://www.venetianlasvegas.com/resort/resort-fee.html), [hotel terms/tax](https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html), and [poker room location](https://www.venetianlasvegas.com/resort/casino/poker.html). Verified $119/$209 conditional poker-rate starts, $55 resort fee + tax, 13.38% tax, play qualification, and poker room at Palazzo Level 2 with directions from both resort lobbies. No official walking minutes published. Conditional arithmetic checked: ($119+$55)×1.1338=$197.28; ($209+$55)×1.1338=$299.32; not dated hotel quotes.
- Comparison leads from the earlier session: [Treasure Island Tower Suite/fee page](https://treasureisland.com/hotel/tower-suite) and [official offer terms](https://treasureisland.com/deals-offers/buy-1-get-1-bogo-free-fine-print) establish $49.95 resort fee + tax and 13.38% Clark County room tax, but no dated room rate. Official [Harrah’s](https://www.caesars.com/harrahs-las-vegas) and [Horseshoe](https://www.caesars.com/horseshoe-las-vegas) pages are linked as alternatives; unconfirmed fees/rates/walking minutes remain blank.
- Open review flags on the subsite include missing single-entry/re-entry/add-on rules, no 8 AM candidate start, no date-specific hotel total, incomplete Strip-wide schedule coverage, unknown walking minutes, and hotel-rate play requirements.
- Checks: `node --check 60fb62da/data.js`, `node --check 60fb62da/site.js`, `git diff --check`, nested local-link audit, page-render simulation, local static HTTP 200 checks, and cost arithmetic passed. Every displayed data row links to an official organizer/property source.
- PR #2: https://github.com/karagemop466-tech/Poker4/pull/2. Current branch contribution is isolated in `60fb62da/` to avoid root conflicts; PR merge/deployment must be coordinated with the active integration PRs. GitHub Pages is currently reported as legacy `main:/`; a request to switch to Actions returned 403. This session does not modify the shared Pages workflow/root navigation; integration owner should link the subsite if desired.
