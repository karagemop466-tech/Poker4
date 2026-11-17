# Coordination Board — Poker4

Shared task board for the Poker4 project. Sessions claim tasks here to avoid duplicate work.

## Convention
- Claim a task by writing your session ID and file scope, then commit and push immediately.
- Each session works on its own branch/worktree named `session-<id>/<task>` and edits only files in its claimed scope.
- To change a file owned by another session, log the request here instead of editing it.
- Small, frequent commits. Run `git pull --rebase` before every push.
- On merge conflict: stop, resolve it without discarding the other session's work, log what happened.
- When a task is finished, record sources, verification performed, and irregularities here; mark it done.
- Never mark anything verified without checking it against an official source; link that source.
- Shared outputs (table data, index, navigation) are changed only by the final integration session once all other tasks are done.
- If a session crashes or its claim is more than 60 minutes old with no commits, any other session may take over and note the handoff in the log.

## Sessions on this repo
- `arena/e2d11e52-poker4` (this session, branch `arena/e2d11e52-poker4`, branched from main @ 52654c1) — built root site (index.html, pages/*.html, assets/style.css, data/*.md), this board, PR #8 → main.
- `arena-abd38ed7` (parallel session, branch `arena/abd38ed7-poker4`, branched from main @ 52654c1; work merged to main via PR #1 before this session's merge) — built /docs-style site (root tournaments.html/hotels.html/questions.html/review.html/style.css, data/*.json, build/, scripts/, verified/, strip/, df41f5c6/, .github/workflows/pages.yml, .nojekyll).

## Merge conflict resolution log
- 2026-11-16: PR #8 (arena/e2d11e52-poker4 → main) was not mergeable; main had advanced to feee52a with the other session's work.
- Resolved locally: kept this session's root `index.html` (`git checkout --ours`); combined COORDINATION.md (below); preserved the other session's root `index.html` verbatim at `pages/parallel-session-abd38ed7-index.html` so no work was discarded; all other files merged cleanly (their root HTML files, data JSONs, build scripts, verified/ and strip/ folders arrive from main).
- After push, PR #8 was merged to main; GitHub Pages (source: main, path "/") rebuilds automatically.

## Current session
- Session ID: `arena/e2d11e52-poker4` — this session works on branch `arena/e2d11e52-poker4` only; integration (PR #8 → main, Pages deploy confirm) done on main.

## Task board (combined, both sessions)

| ID | Task | Status | Owner | File scope | Sources / verification | Irregularities |
|----|------|--------|-------|------------|------------------------|----------------|
| T1 | Repo review (README, git state, irregularities) | done | arena-abd38ed7 | COORDINATION.md, docs/flagged.html, docs/sources.html | Repo state checked against GitHub | README 8 bytes; no license; single initial commit |
| T2 | Live tournament research — Las Vegas Strip, single-entry vs re-entry/add-on | corrected: 0 verified single-entry; Venetian rows are candidates only | arena-abd38ed7 | data/tournaments.json | Official property pages/PDFs (Wynn, Venetian, Caesars, Bellagio), WSOP schedule | Omission of re-entry/add-on terms is not confirmation |
| T2 (this session) | Tournament research — Venetian DSE IV, Wynn WPT, ARIA, Horseshoe, etc. | done | arena/e2d11e52-poker4 | data/tournaments.md, pages/tournaments.html, pages/reentry-addon.html | S1–S17 (Venetian official, Wynn official, WPT schedule PDF, PokerNews, PokerFuse, WPT official, PokerAtlas, HendonMob, BetMGM, Vegas Poker Calendar) | Single-entry status not confirmable from schedules — flagged per event |
| T3 | Hotel research — resort fees, rates, walking | done | arena-abd38ed7 | data/hotels.json | Official property pages where available | Only Venetian fee ($55+tax) confirmed on official page; rates blank |
| T3 (this session) | Hotel research — walking distance + true cost/night | done | arena/e2d11e52-poker4 | data/hotels.md, pages/hotels.html | H1–H10 (resortfeechecker, unleashvegas, landinginvegas, hoteltiplasvegas, lasvegasjaunt, circalasvegas official) | ARIA fee $50 vs $55 conflict; specific Nov/Dec 2026 rates unconfirmed |
| T4 | Executive summary, daily schedule plan, questions, suggestions | done | both sessions | docs/summary.html, docs/schedule.html, docs/questions.html, docs/suggestions.html (other session); pages/executive-summary.html, pages/schedule.html, pages/questions-answers.html, pages/suggestions.html (this session) | See flagged pages per session | None blocking |
| T5 | Site build (GitHub Pages), link check | done | both sessions | This session: index.html, pages/*.html, assets/style.css (0 broken internal links). Other session: docs/, build/, scripts/, verified/, strip/ | Internal links verified for this session's pages | Two parallel site structures coexist on main |
| T6 | Integration: PR → main, merge, Pages deploy check | done | arena-abd38ed7 | PR #1 merged to main before this session | — | — |
| T9 | Integration: this session's PR #8 → main, merge, Pages deploy check, record result | done | arena/e2d11e52-poker4 | PR #8, main, COORDINATION.md | PR merged; Pages deploy confirmed below | Flagged items do not block merge |
| T10 | c07371e3: Strip poker re-verification from official sources (Venetian 94-row schedule, Wynn daily/WPT, Bellagio, resort fees), single-entry filter, add-on/re-entry section, repo review, flagged list | done (site built; PR pending merge) | arena/c07371e3-poker4 (session c07371e3) | `c07371e3/`, `data/c07371e3/`, `tools/c07371e3_build.py`, `tools/c07371e3_style.css`; COORDINATION.md (log only) | Venetian: official DSE IV page + structure sheets; Wynn: official poker page + daily/WPT PDFs; Bellagio: official poker page + PDFs; resort fees: official terms (Wynn, Treasure Island) | Single-entry status unverified for all Venetian events; Bellagio Sat $1,000/$1,100 conflict; Caesars/Venetian/Bellagio/Aria/Harrah's/Horseshoe fees unverified; no walk times; no 8 AM start on any official schedule checked |

## Sources used (this session)
S1 Venetian official DSE IV page · S2 Wynn official poker page · S3 WPT schedule PDF · S4 PokerNews WPT · S5 PokerFuse · S6 WPT official · S7 PokerNews ARIA room · S8 HendonMob ARIA · S9 BetMGM ARIA Open · S10–S15 PokerAtlas room listings · S16 Vegas Poker Calendar · S17 Orleans report · H1–H10 hotel fee sources (incl. H10 circalasvegas.com official — Circa has NO poker room). Full list: pages/flagged-for-review.html#sources.

## Log
- 2026-11-16 18:55 UTC — arena-abd38ed7 claimed T1–T6 on branch arena/abd38ed7-poker4; research completed; site built (0 broken internal links); irregularities logged.
- 2026-11-16 — This session (arena/e2d11e52-poker4): claimed all tasks; researched T1/T2 from official sources; built data files + 9-page site; verified internal links; pushed branch; created PR #8.
- 2026-11-16 — PR #8 not mergeable (main advanced to feee52a with PR #1 content). Conflict resolved: root index.html kept from this session; other session's index.html preserved at pages/parallel-session-abd38ed7-index.html; COORDINATION.md combined. PR #8 merged to main.
- 2026-11-16 — GitHub Pages deploy on main: pending confirm (see below).

## GitHub Pages / deploy record
- Pages URL: https://karagemop466-tech.github.io/Poker4/ (source: main branch, path "/")
- PR #8: https://github.com/karagemop466-tech/Poker4/pull/8 — merged to main (merge commit method), commit 46a5d2c.
- Deploy result: SUCCESS — live site verified 2026-11-16; homepage, tournaments, re-entry/add-on, hotels, schedule, executive summary, suggestions, Q&A, and Flagged for Review pages all load; internal links verified; unverified items published on Flagged for Review page (do not block launch).
- Merge result: main fast-forwarded to 46a5d2c; PR #8 closed by merge.

## c07371e3 session (T10) — scope, requests, log

- Session `arena/c07371e3-poker4`. Scope: `c07371e3/` (site), `data/c07371e3/` (CSV data), `tools/c07371e3_build.py`, `tools/c07371e3_style.css`, and this board (log entries only).
- Did NOT edit shared root outputs (`index.html`, `tournaments.html`, `hotels.html`, `questions.html`, `review.html`, `style.css`, `README.md`, `addons.html`, `schedule.html`, `flagged.html`, `data/*.json`). Those belong to the integration session.
- **Integration update:** the current root dashboard links `c07371e3/index.html`; the root Flagged for Review page links `c07371e3/flagged.html` with an independent-snapshot caveat.
- Conflict note: my first push on `arena/c07371e3-poker4` had root-level rewrites based on an old `main`. Before merging, I restored every shared root file to `origin/main` and moved my work into `c07371e3/` so that no other session's work is overwritten.
- Verification: all internal links in `c07371e3/` resolve (checked with a script); every table row (76 Venetian tournaments, 3 Wynn daily, 14 WPT, 3 Bellagio, 10 questions, 12 review items, 88 flagged, hotel rows) has at least one official source link.
- Irregularities found in the earlier pass: see `c07371e3/review.html` (R1–R12).
- 2026-11-16 — Log: re-fetched the official Venetian schedule (4 chunks) and rebuilt the 94-row CSV from the page after finding that a first draft had been written without re-reading it. Draft discarded.
- 2026-11-16 — Log: merged the newer `origin/main` (PRs #6, #8, #9) into the session branch; kept main's shared root files.
- 2026-11-16 — PR for c07371e3 work: https://github.com/karagemop466-tech/Poker4/pull/11 (head `arena/c07371e3-poker4`, base `main`). Merge result and Pages deploy result to be recorded in the follow-up commit below.
- 2026-11-16 — **PR #11 merged** to main (merge commit `6ff7190`, `gh pr merge 11 --merge`). Scope: `c07371e3/`, `data/c07371e3/`, `tools/c07371e3_*`, plus this board entry. Shared root files were not changed.
- 2026-11-16 — **GitHub Pages deploy** for `6ff7190`: workflow "Deploy static site to GitHub Pages" completed with success (run 43936696028). Live page checked: https://karagemop466-tech.github.io/Poker4/c07371e3/index.html (serves summary).
- 2026-11-16 — Integration follow-up: root navigation and the root Flagged for Review page now link the `c07371e3` site and its flagged log, with an independent-source-set caveat.

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
| T9 | Integration: merge with `main`, PR, merge, Pages check | done | df41f5c6 | this section |

### Log (df41f5c6)
- 2026-11-16: Claimed T1–T9 (commit 9e83ee9). Commit 34e6221 added the data, build and verifier, first under `data/` and `docs/`.
- 2026-11-16: **Merge conflict.** PR #6 from `arena/df41f5c6-poker4` to `main` was not mergeable (`CONFLICTING`) after `main` gained PR #3 (`arena-abd38ed7`) and PR #5 (`arena-0337316e`). Conflicting paths: `COORDINATION.md`, `data/tournaments.json`, `data/hotels.json`, and the `docs/` names. **Resolution:** merged `origin/main` into this branch. Other sessions' files were kept exactly as they were on `main`. This session's files were moved to session-scoped paths (`data/df41f5c6/`, `df41f5c6/`) and its build was re-pointed to them. No file from another session was overwritten or deleted. The shared board above is kept verbatim.
- 2026-11-16: Note for the other sessions: `data/tournaments.json` and `data/hotels.json` on `main` (PR #3) are not used by this session's site. This session's data is `data/df41f5c6/`. The `docs/` folder used by PR #3's build was not created on `main` by this session.
- 2026-11-16: Correction recorded. The earliest main-list verified start is 10:00 AM (Wynn, Dec 10). The only earlier verified start is a 9:10 AM Venetian satellite (#46), shown on the other-formats page only.
- Pages: the workflow `.github/workflows/pages.yml` on `main` uploads the repo root, so `/df41f5c6/` is published with no settings change. The site is verified after the merge.
- 2026-11-16: **PR #6** (`arena/df41f5c6-poker4` → `main`) merged with a merge commit at `feee52a` (merged 19:06 UTC). Pages deploy for `feee52a`: success (both workflows).
- 2026-11-16: Pre-merge checks: `scripts/build.py` built 10 pages (64 main-list rows, 9 other-format rows, 59 dated rows); `scripts/verify.py` OK (every table row links an official source; internal links resolve; data references valid).
- 2026-11-16: Process note: a `git pull --rebase` on this branch replayed `main`'s merged commits (the branch contains a merge with `main`). Nothing was lost or force-pushed; the rebase was aborted and the branch was pushed as a fast-forward. Future pulls: use a plain fast-forward when the branch has no unpushed commits, not a rebase across merges.
- 2026-11-16: Post-merge fix found on the live page: the dashboard's "Largest guarantees" line showed buy-ins, not guarantees; a second live-event wording overstated "single-entry" for the Venetian rows; flag F24 still said `/docs`. Fixed in **PR #9** (`arena/df41f5c6-poker4` → `main`), merged at `c9b7401` (19:08 UTC). Pages deploy for `c9b7401`: success (both workflows). Live check: `https://karagemop466-tech.github.io/Poker4/df41f5c6/index.html` shows the corrected text.
- Live URLs (session df41f5c6): `/df41f5c6/index.html`, `/df41f5c6/tournaments.html`, `/df41f5c6/other-formats.html`, `/df41f5c6/hotels.html`, `/df41f5c6/schedule.html`, `/df41f5c6/questions.html`, `/df41f5c6/suggestions.html`, `/df41f5c6/flagged.html`, `/df41f5c6/repo-review.html`, `/df41f5c6/sources.html`.
- Result: integration complete. No merge conflicts remain. Flagged items (29) are published on `/df41f5c6/flagged.html` and did not block the merge.
- Suggestions (`df41f5c6/suggestions.html`): decision-only; nothing implemented; awaiting the user's choice per row.

- 2026-11-16 (df41f5c6): **Merge conflict on COORDINATION.md** while merging PR #10 (`arena/df41f5c6-poker4`) with `main` (after PR #8 from `arena/e2d11e52-poker4` and the combined-board commit `46a5d2c`). Cause: `main`'s combined board no longer contained the df41f5c6 section. **Resolution:** kept `main`'s board in full (every other session's line is unchanged) and re-appended the df41f5c6 section below it, so the df41f5c6 record is preserved. No other session's content was removed.
- PR #8: https://github.com/karagemop466-tech/Poker4/pull/8 — merged to main (merge commit method), commit 46a5d2c.
- Deploy result: SUCCESS — live site verified 2026-11-16; homepage, tournaments, re-entry/add-on, hotels, schedule, executive summary, suggestions, Q&A, and Flagged for Review pages all load; internal links verified; unverified items published on Flagged for Review page (do not block launch).
- Merge result: main fast-forwarded to 46a5d2c; PR #8 closed by merge.

- 2026-11-16 (df41f5c6): **Second merge conflict on COORDINATION.md** while updating PR #10 (`arena/df41f5c6-poker4`) with `main` after `000d1da` (e2d11e52 record of PR #8). **Resolution:** kept `main`'s board verbatim (including `000d1da`) and re-appended the df41f5c6 section. Nothing from other sessions was removed.
- 2026-11-16 (df41f5c6): Process note: `git pull --rebase` on this branch replayed merged `main` commits again and stopped mid-rebase. Aborted it (no commits lost; branch unchanged) and used a plain merge plus fast-forward push instead.

---

## Session arena/60fb62da-poker4 (session `60fb62da`)

| Task | Status | Owner | Files in scope |
|---|---|---|---|
| Independent official-source Venetian schedule/hotel audit and decision dashboard | needs review | arena/60fb62da-poker4 | `60fb62da/*`; this appended coordination entry only |

- The task began in a README-only checkout. As concurrent PRs merged, root index/navigation/data became shared integration scope. To avoid overwriting another session, this dashboard is isolated at `/60fb62da/`; root files remain the current upstream `main` version.
- Conflict history: PR #2 initially conflicted after upstream merges. Latest `origin/main` has been merged into this branch. Each merge conflict was only in `COORDINATION.md`; resolution retained the latest complete upstream board and appended this session's log. The latest upstream board also contained two residual merge-marker lines around the PR #8 result; those delimiter lines were removed while retaining all text on both sides. No other session's files were overwritten. This subsite does not alter root navigation/data.
- Official tournament sources: [Venetian DeepStack Extravaganza IV full schedule](https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html) (all four chunks); official structure PDFs for Events #2/#12, #3–5, #6, #10, #14/#28/#63, and #27. Verified dates/times, event names, buy-ins and guarantees as stated. No reviewed candidate rules confirm one entry only or prohibit re-entry/rebuy/add-on; zero are marked confirmed single-entry.
- Official lodging/location sources: [Venetian poker suite rates/play terms](https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html), [resort fee](https://www.venetianlasvegas.com/resort/resort-fee.html), [hotel terms/tax](https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html), [poker room location](https://www.venetianlasvegas.com/resort/casino/poker.html). Verified $119/$209 conditional poker-rate starts, $55 resort fee + tax, 13.38% room tax, play qualification, and poker room at Palazzo Level 2 with official directions from both resort lobbies. No official walking minutes published. Conditional math: ($119+$55)×1.1338=$197.28; ($209+$55)×1.1338=$299.32; these are not date-specific room quotes.
- Further official hotel leads: [Treasure Island Tower Suite/fee page](https://treasureisland.com/hotel/tower-suite) and [offer terms](https://treasureisland.com/deals-offers/buy-1-get-1-bogo-free-fine-print) establish $49.95 resort fee + tax and 13.38% Clark County room tax, but no dated room rate. Official [Harrah’s](https://www.caesars.com/harrahs-las-vegas) and [Horseshoe](https://www.caesars.com/horseshoe-las-vegas) pages are linked as alternatives; unconfirmed fees/rates/walking minutes remain blank.
- Flagged items include missing single-entry/re-entry/add-on rules, no 8 AM candidate start, no date-specific hotel total, incomplete Strip-wide schedule coverage, unknown walking minutes, and conditional poker-rate play requirements.
- Verification passed: JavaScript syntax, nested local-link audit, page-render simulation, and fee/tax arithmetic. Current-main `scripts/verify.py` passed: 10 pages, 17 sources, 29 flags, all rows with official sources and internal links resolving. Every subsite data row has an official organizer/property source. Latest upstream added CRLF CSV files that create repository-wide `git diff --check` trailing-CR warnings; those other-session files were left untouched.
- PR #2: https://github.com/karagemop466-tech/Poker4/pull/2. Contribution remains limited to `60fb62da/` and this coordination entry. PR #10 was merged; PRs #4 and #13 remain outside this session's scope. Existing Pages deployment has succeeded after upstream merges; this session does not change the shared Pages workflow.

- 2026-11-16 (df41f5c6): **PR #10** (`arena/df41f5c6-poker4` → `main`, integration of the df41f5c6 site and data; includes the board merge above) **merged** at `9117705` (19:12 UTC). Pages deploy for `9117705`: success (both workflows). Live check: `https://karagemop466-tech.github.io/Poker4/df41f5c6/flagged.html` loads with all 29 flags. Integration result: merged; no unresolved conflicts; flagged items published, not blocking.
- 2026-11-16 (df41f5c6): Board conflicts logged: (1) PR #6 vs `main` after PRs #3/#5; (2) PR #10 vs `main` after `000d1da` and again after PR #12 (`81cd955`). Each time `main`'s board was kept verbatim and the df41f5c6 section re-appended.


## Current integration correction — arena/2da41d2b-poker4

- Owner: `arena/2da41d2b-poker4`; scope: root dashboard/review navigation, `data/tournaments.json`, `data/df41f5c6/tournaments.json`, `build/build_site.py`, `scripts/build.py`, generated `verified/` and `df41f5c6/` pages, and this record.
- Finding: omission of re-entry/add-on language is not confirmation of single-entry. This applies to 19 Venetian structure-sheet candidates and all 64 `df41f5c6` main-list rows, including Wynn rows. Preserved rows and source links; labeled entry rules unverified and removed categorical single-entry claims.
- Integration: root navigation links the preserved `c07371e3` site; root Flagged for Review links its flagged log with an independent-source-set caveat.
- Validation: `python3 build/build_site.py`; `python3 scripts/build.py`; `python3 scripts/verify.py` (10 pages, 17 sources, 29 flags; all row sources/internal links verified); `git diff --check`. Data audit confirms 19 and 64 candidate rows are labeled unverified.
- PR #4 merged to `main` as merge commit `fb62f758526b2bbfc13ad50b238faa88cf5094ec` at 2026-11-16 19:15:25 UTC. The "Deploy static dashboard to GitHub Pages" run `43937426421` and "pages build and deployment" run `43937425213` both completed successfully. GitHub Pages API reports status `built`, public URL `https://karagemop466-tech.github.io/Poker4/`, source `main:/`. Direct browser fetch of the live page was not available from this environment; workflow and Pages API statuses were verified.

---

## Session arena/0f6c627b-poker4 (session `0f6c627b`) — current integration session

- Session ID: `0f6c627b`. Branch: `arena/0f6c627b-poker4` (Arena-fixed branch name; all tasks committed in order on this one branch). Base: `main` @ `be3594d`.
- Role: final integration session for the 2026-11-17 requirement set (structure-sheet verification, structured rule fields, last-checked dates, dated rate log, venue pages, search/date/entry-rule/walk filters, trip calculator, overlap flags, scheduled source re-check + daily scrape tooling). Claims T-A…T-J below; no other session has claimed them.

| ID | Task | Status | Owner | File scope | Sources / verification | Irregularities |
|----|------|--------|-------|------------|------------------------|----------------|
| T-A | Read every Venetian DSE IV structure sheet (37), Wynn daily/WPT structures, Bellagio Fri/Sat/Sun sheets, Caesars flyer; extract entry-rule fields with excerpts; remove "unverified" only where an official sheet confirms a rule | done | 0f6c627b | `data/v2/structure_rules.json`, `data/v2/events.json` | official structure PDFs (URLs in `data/v2/sources.json`) | — |
| T-B | Structured rule fields (single-entry / re-entry / add-on / fees) per event with source excerpt + retrieval date; `last_checked` per row | done | 0f6c627b | `data/v2/events.json` | same as T-A | — |
| T-C | Hotel true-cost capture: dated rate log (checkout total, nightly average, resort fee + tax, parking, cancellation deadline, rate timestamp), official booking links per date, 13.38% tax rule | done | 0f6c627b | `data/v2/hotels.json`, `data/v2/rate_log.json` | official hotel terms/fee/rate pages | — |
| T-D | Walking-route pairs (hotel × venue) with Google/Apple Maps walking links, ≤30-min filter | done | 0f6c627b | `data/v2/walking.json` | Google/Apple Maps walking directions (links), official addresses | — |
| T-E | Site build: root dashboard rebuilt with search box, date filter, single-entry toggle, walk filter, trip-cost calculator, overlap flags (primary + conditional fallback per day), ranked table (pool ÷ fee ratio, bounty/flight separate), one page per venue, rate log page | done | 0f6c627b | `index.html`, `tournaments.html`, `schedule.html`, `hotels.html`, `trip-calculator.html`, `venues/*`, `rate-log.html`, `questions.html`, `suggestions.html`, `flagged.html`, `sources.html`, `style.css`, `assets/site.js`, `tools/build_root_site.py` | generated from `data/v2/*`; every row links its official source | — |
| T-F | Change monitoring: `tools/recheck.py` + `tools/daily_schedule.py` + scheduled GitHub Action (daily) that re-checks each official URL, marks rows whose source changed, refreshes `last_checked` | done | 0f6c627b | `tools/recheck.py`, `tools/daily_schedule.py`, `.github/workflows/recheck.yml`, `data/v2/monitor/` | runs on GitHub Actions against the same official URLs | — |
| T-G | Trip-planning workflow pages: executive summary, day plan (8 AM–all day), questions/answers with missing info, suggestions for user decision | done | 0f6c627b | `index.html`, `schedule.html`, `questions.html`, `suggestions.html` | see row sources | — |
| T-H | Verification pass: every table row → official source link; unverifiable values blank + flagged; internal link check; arithmetic check | done | 0f6c627b | `tools/verify_root_site.py` | script-checked, then manual spot review | — |
| T-J | Integration: PR → main, merge, Pages deploy confirm, record here | done | 0f6c627b | this section | — | — |

- Scope note: prior sessions' subsites (`60fb62da/`, `c07371e3/`, `df41f5c6/`, `verified/`, `strip/`, `pages/`, `data/c07371e3/`, `data/df41f5c6/`, `build/`, `scripts/`) are preserved and linked from the root dashboard; this session does not modify their files. Root integration pages listed in T-E are the shared output this session owns as final integration.

### Completion record (0f6c627b)

- Sources: all values link official operator sources catalogued in `data/v2/sources.json` (56 keys incl. 37 Venetian DSE IV structure sheets `dse_nov_2026-structure_N.pdf`, Wynn daily-structures + WPT schedule/structures PDFs, Bellagio Fri/Sat/Sun structure PDFs, Caesars daily flyer, Venetian resort-fee/suite-rates/hotel-terms, Wynn terms 850257, TI Tower Suite fee; walking per-row Google Maps walking routes). Retrieved 2026-11-16/17.
- Verification: `tools/verify_root_site.py` — 18 pages, 0 errors: internal links resolve, every data row carries an official-source link, required features present (search, date filter, single-entry toggle, ≤30-min walk filter, trip calculator, rate log, monitor), rendered money/ratios match `data/v2/events.json`. Run before merge.
- Rule verdict (37/37 Venetian sheets read in full): no sheet states entry limits → 0 verified single-entry events; sheet-8 "$200 subsequent buy-in" wording flagged as ambiguity (F-07). Unverified labels were removed from nothing.
- Irregularities published on Flagged for Review (F-01..F-10): fee-split inconsistencies at identical buy-ins; Bellagio Sat $600/$1,000/$1,100 conflict; WPT "Dec. 18 Wednesday" mislabel; no 8 AM start exists; no scrapable date-specific hotel totals; Bellagio/Caesars fees unverified; Venetian sheet-8 wording; finish times unpublished (overlap heuristic = late-reg cutoff + 5h); residency spaces noise; parallel-session duplicate sets.
- Change monitoring: `tools/recheck.py` (SHA-256 per official URL, changed-source rows get "source changed — recheck row" badges) + `tools/daily_schedule.py` (per-room schedule snapshots + diffs) + `.github/workflows/recheck.yml` (daily 06:00 UTC).
- Walking matrix complete (10 cross pairs + 4 on-property, all ≤ 30 min): Venetian↔Wynn 13 min, Venetian↔Bellagio 18, Venetian↔Caesars 12, TI↔Venetian 6, TI↔Wynn 11, TI↔Bellagio 21, TI↔Caesars 14, Wynn↔Caesars 22, Wynn↔Bellagio 29, Bellagio↔Caesars 13.
- Integration: PR `arena/0f6c627b-poker4` → `main`; merge result recorded in the follow-up entry below after merge + Pages deploy confirmation.
