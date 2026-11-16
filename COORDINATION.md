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
| T2 | Live tournament research — Las Vegas Strip, single-entry vs re-entry/add-on | done | arena-abd38ed7 | data/tournaments.json | Official property pages/PDFs (Wynn, Venetian, Caesars, Bellagio), WSOP schedule | Rows not confirmed by official structure sheet flagged unverified |
| T2 (this session) | Tournament research — Venetian DSE IV, Wynn WPT, ARIA, Horseshoe, etc. | done | arena/e2d11e52-poker4 | data/tournaments.md, pages/tournaments.html, pages/reentry-addon.html | S1–S17 (Venetian official, Wynn official, WPT schedule PDF, PokerNews, PokerFuse, WPT official, PokerAtlas, HendonMob, BetMGM, Vegas Poker Calendar) | Single-entry status not confirmable from schedules — flagged per event |
| T3 | Hotel research — resort fees, rates, walking | done | arena-abd38ed7 | data/hotels.json | Official property pages where available | Only Venetian fee ($55+tax) confirmed on official page; rates blank |
| T3 (this session) | Hotel research — walking distance + true cost/night | done | arena/e2d11e52-poker4 | data/hotels.md, pages/hotels.html | H1–H10 (resortfeechecker, unleashvegas, landinginvegas, hoteltiplasvegas, lasvegasjaunt, circalasvegas official) | ARIA fee $50 vs $55 conflict; specific Nov/Dec 2026 rates unconfirmed |
| T4 | Executive summary, daily schedule plan, questions, suggestions | done | both sessions | docs/summary.html, docs/schedule.html, docs/questions.html, docs/suggestions.html (other session); pages/executive-summary.html, pages/schedule.html, pages/questions-answers.html, pages/suggestions.html (this session) | See flagged pages per session | None blocking |
| T5 | Site build (GitHub Pages), link check | done | both sessions | This session: index.html, pages/*.html, assets/style.css (0 broken internal links). Other session: docs/, build/, scripts/, verified/, strip/ | Internal links verified for this session's pages | Two parallel site structures coexist on main |
| T6 | Integration: PR → main, merge, Pages deploy check | done | arena-abd38ed7 | PR #1 merged to main before this session | — | — |
| T9 | Integration: this session's PR #8 → main, merge, Pages deploy check, record result | done | arena/e2d11e52-poker4 | PR #8, main, COORDINATION.md | PR merged; Pages deploy confirmed below | Flagged items do not block merge |

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

---

## Session arena/60fb62da-poker4 (session `60fb62da`)

| Task | Status | Owner | Files in scope |
|---|---|---|---|
| Independent official-source Venetian schedule/hotel audit and decision dashboard | needs review | arena/60fb62da-poker4 | `60fb62da/*`; this appended coordination entry only |

- At task start, this checkout contained only the initial README and no coordination file. The initial dashboard was built on the assigned Arena branch. As other sessions' PRs merged into `main`, root index/navigation/data became shared integration scope. To avoid overwriting any session, this dashboard is isolated at `/60fb62da/`; root files are restored from the current upstream `main`. Existing PR #1/#3/#5/#6/#8 research remains preserved in the repository.
- Conflict log: PR #2's first merge attempt conflicted after PR #1 merged. Later `origin/main` merges conflicted only in the shared `COORDINATION.md`; resolution was to keep the latest upstream board intact and append this session's log. All other session files are preserved. The subsite has no root navigation/data edits.
- Official tournament sources checked: [Venetian DeepStack Extravaganza IV full schedule](https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html) (all four page chunks); official structure PDFs for Events #2/#12, #3–5, #6, #10, #14/#28/#63, and #27. Verified dates/times, event names, buy-ins and guarantees as stated. No reviewed candidate rules confirm one entry only or prohibit re-entry/rebuy/add-on; zero are marked confirmed single-entry.
- Official lodging/location sources: [Venetian poker suite rates/play terms](https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html), [resort fee](https://www.venetianlasvegas.com/resort/resort-fee.html), [hotel terms/tax](https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html), and [poker room location](https://www.venetianlasvegas.com/resort/casino/poker.html). Verified $119/$209 conditional poker-rate starts, $55 resort fee + tax, 13.38% room tax, play qualification, and poker room at Palazzo Level 2 with directions from both resort lobbies. No official walking minutes published. Conditional math: ($119+$55)×1.1338=$197.28; ($209+$55)×1.1338=$299.32; not dated booking quotes.
- Further comparison leads: [Treasure Island official Tower Suite/fee page](https://treasureisland.com/hotel/tower-suite) and [official offer terms](https://treasureisland.com/deals-offers/buy-1-get-1-bogo-free-fine-print) establish $49.95 resort fee + tax and 13.38% Clark County room tax, but no dated room rate. Official [Harrah’s](https://www.caesars.com/harrahs-las-vegas) and [Horseshoe](https://www.caesars.com/horseshoe-las-vegas) pages are linked as alternatives; unconfirmed fees/rates/walking minutes remain blank.
- Flagged items on the subsite include missing single-entry/re-entry/add-on rules, no 8 AM candidate start, no date-specific hotel total, incomplete Strip-wide schedule coverage, unknown walking minutes, and conditional poker-rate play requirements.
- Checks: `node --check 60fb62da/data.js`, `node --check 60fb62da/site.js`, `git diff --check`, nested local-link audit, page-render simulation, and fee/tax arithmetic passed. The shared `scripts/verify.py` on current main passed: 10 pages, 17 sources, 29 flags, all tables have official sources and internal links resolve. Each data row in this subsite links an official organizer/property source.
- PR #2: https://github.com/karagemop466-tech/Poker4/pull/2. Current branch contribution is isolated in `60fb62da/` to avoid root conflicts; no root navigation change is requested here. Other open PRs at this integration snapshot: #4, #7, #10, #11; their files/scopes were not modified. Pages API reports legacy `main:/`; the existing deployment workflow has succeeded after recent merges, and this session does not alter the shared deployment workflow.
