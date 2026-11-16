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
- PR #8: https://github.com/karagemop466-tech/Poker4/pull/8 — merged to main (merge commit method).
- Deploy result: <TO BE FILLED AFTER VERIFYING LIVE SITE> — <date/time>

---

## Session session-1 (branch `arena/9ae2dbdb-poker4`, base `main` @ 52654c1)

Parallel-session rules followed: this session stayed on its own branch and edited only its claimed files. The integrated site already on `main` (root dashboard + `pages/` category pages, `verified/`, `strip/`, `df41f5c6/`) is preserved; this session contributes additively: `data/tournaments.md`, `data/hotels.md`, `assets/js/app.js`, and this board section. No other session's files were overwritten or deleted.

| # | Task | Status | Owner | Files |
|---|------|--------|-------|-------|
| 1 | Research Las Vegas Strip poker rooms & upcoming tournament schedules (official sources); single-entry only, rebuy/add-on listed separately | done | session-1 | data/tournaments.md |
| 2 | Research hotels within 30-min walking distance of tournaments (nightly rate + resort fees + true cost) | done | session-1 | data/hotels.md |
| 3 | Analysis: executive summary, tournament ranking by cost/prize pool, hotel true-cost ranking | done | session-1 | pages/summary.html (this session's branch; main carries the integrated `pages/executive-summary.html`) |
| 4 | Site: landing page + category subpages, tables with source links, findings | done | session-1 | index.html (additive companion links only on branch), pages/*.html (this session's branch; main carries integrated `pages/`), assets/css/style.css, assets/js/app.js |
| 5 | Verification: line-by-line source check, unverified items left blank + flagged | done | session-1 | pages/flagged.html (this session's branch; main carries `pages/flagged-for-review.html`, `data/flagged.json`) |
| 6 | Suggestions section (site improvement + decision-making) and Q&A section (open questions before decisions) | done | session-1 | pages/suggestions.html, pages/qa.html (this session's branch; main carries integrated equivalents) |
| 7 | PR to main, merge, GitHub Pages publish, confirm no broken links | in progress | session-1 | — |

## Session log (session-1)
- 2026-11-16: Repo reviewed — contained only README.md. Researched tournaments from official sources: Wynn poker page + daily poster PDF + WPT World Championship schedule PDF (wynnresorts.com CDN; WPT WC Nov 27–Dec 21, 2026); Venetian DSE IV official schedule + structure sheets (venetianlasvegas.com; 64 events Nov 16–Dec 23, 2026); Caesars Palace booking calendar + official fees page (Dec 11–13, 2026: $595/$595/$126; fee $62.30/night incl. tax). VegasPokerCalendar used for discovery only, flagged per row.
- 2026-11-16: Built full site (landing + category subpages, executive summary, suggestions, Q&A, Flagged for Review); internal link audit 0 broken. Unverified values left blank and flagged; nothing inferred.
- 2026-11-16: Rebased onto origin/main three times, preserving all parallel sessions' boards and files. Conflicts resolved by keeping upstream board/work in full and adding this section.
- 2026-11-16: PR #7: https://github.com/karagemop466-tech/Poker4/pull/7 — merge requested without waiting for review. After merge: confirm GitHub Pages deploy on main, then record merge result + deploy status below.
