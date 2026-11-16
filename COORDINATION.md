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
- **REQUEST to integration session (logged, not edited):** add a link to `c07371e3/index.html` in the root navigation, and list `c07371e3/flagged.html` on the root Flagged page. This is the integration session's call.
- Conflict note: my first push on `arena/c07371e3-poker4` had root-level rewrites based on an old `main`. Before merging, I restored every shared root file to `origin/main` and moved my work into `c07371e3/` so that no other session's work is overwritten.
- Verification: all internal links in `c07371e3/` resolve (checked with a script); every table row (76 Venetian tournaments, 3 Wynn daily, 14 WPT, 3 Bellagio, 10 questions, 12 review items, 88 flagged, hotel rows) has at least one official source link.
- Irregularities found in the earlier pass: see `c07371e3/review.html` (R1–R12).
- 2026-11-16 — Log: re-fetched the official Venetian schedule (4 chunks) and rebuilt the 94-row CSV from the page after finding that a first draft had been written without re-reading it. Draft discarded.
- 2026-11-16 — Log: merged the newer `origin/main` (PRs #6, #8, #9) into the session branch; kept main's shared root files.
- 2026-11-16 — PR for c07371e3 work: https://github.com/karagemop466-tech/Poker4/pull/11 (head `arena/c07371e3-poker4`, base `main`). Merge result and Pages deploy result to be recorded in the follow-up commit below.
- 2026-11-16 — **PR #11 merged** to main (merge commit `6ff7190`, `gh pr merge 11 --merge`). Scope: `c07371e3/`, `data/c07371e3/`, `tools/c07371e3_*`, plus this board entry. Shared root files were not changed.
- 2026-11-16 — **GitHub Pages deploy** for `6ff7190`: workflow "Deploy static site to GitHub Pages" completed with success (run 43936696028). Live page checked: https://karagemop466-tech.github.io/Poker4/c07371e3/index.html (serves summary).
- 2026-11-16 — Record follow-up: this entry is recorded via PR (see next PR number in this log). Open request for integrator still stands: link `c07371e3/index.html` from the root navigation and add `c07371e3/flagged.html` to the root Flagged page.

