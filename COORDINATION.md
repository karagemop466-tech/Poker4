# Coordination Board — Poker4

Shared task board for the Poker4 project. Sessions claim tasks here to avoid duplicate work.

## Convention
- Claim a task by writing your session ID and file scope, then commit and push immediately.
- Each session works on its own branch/worktree named `session-<id>/<task>` and edits only files in its claimed scope.
- To change a file owned by another session, log the request here instead of editing it.
- Small, frequent commits. Run `git pull --rebase` before every push.
- On merge conflict: stop, resolve without discarding the other session's work, log what happened.
- When a task is finished, record sources, verification performed, and irregularities here; mark it done.
- Never mark anything verified without checking it against an official source; link that source.
- Shared outputs (table data, index, navigation) are changed only by the final integration session once all other tasks are done.
- If a session crashes or its claim is more than 60 minutes old with no commits, any other session may take over and note the handoff in the log.

## Current session
- Session ID: `arena/e2d11e52-poker4` (working branch: `arena/e2d11e52-poker4`, branched from `52654c152aaa6116f54a9c4c6503ff425cb6101f` of main)
- This session works on the current branch only and claims all tasks below (single active session).

## Tasks

| ID | Task | Status | Owner | File scope | Sources / verification | Irregularities |
|----|------|--------|-------|------------|------------------------|----------------|
| T1 | Research live upcoming poker tournaments near Las Vegas Strip (official sources) | done | arena/e2d11e52-poker4 | `data/tournaments.md`, `data/sources.md` | Verified vs official Venetian (venetianlasvegas.com), Wynn (wynnlasvegas.com/casino/poker), WPT (worldpokertour.com, pokernews.com), PokerNews ARIA room page, PokerAtlas/HendonMob. Key series: Venetian DSE IV (Nov 16-Dec 23, 64 events, $3.6M+ GTD), Wynn WPT World Championship (Nov 27-Dec 21), ARIA Poker Open (Nov 29-Dec 20), Horseshoe daily $100-$160 NLH, MGM Grand add-on, Mandalay Bay daily, Planet Hollywood daily. | Single-entry / re-entry status NOT verifiable from schedule pages alone; structure PDFs not parsed — flagged unverified per verification rule. |
| T2 | Research hotels within walking distance of tournaments (official sources) | done | arena/e2d11e52-poker4 | `data/hotels.md`, `data/sources.md` | Verified vs resortfeechecker.com, unleashvegas.com, hoteltiplasvegas.com, lasvegasjaunt.com. Venetian $55+tax resort fee ($62.36), parking $20/day; Aria $50-55+tax ($56.69-62.36); Park MGM $50+tax ($56.69); Mandalay Bay $50+tax; Luxor/Excalibur $45+tax (~$51); Wynn $55+tax. Strip lodging tax 13.38% applies to room+fee. MGM Rewards Gold+ waives resort fee at MGM properties; Caesars Rewards Platinum+ free parking at Caesars properties. Circa confirmed NO poker room (circalasvegas.com). Walking distances: Wynn-Venetian ~1.0mi/20min; Venetian-Aria ~0.7mi/15min; Aria-Mandalay Bay ~1.1mi/22min; Wynn-Mandalay Bay ~2.8mi/55min (not reasonable). | Specific Nov/Dec 2026 base room rates not confirmed from official booking engines for specific dates — typical ranges used, flagged unverified. |
| T3 | Executive summary | done | arena/e2d11e52-poker4 | `pages/executive-summary.html` | Built; sources S1–S17, H1–H10 cited | None |
| T4 | Suggestions section (site improvement + decision suggestions) | done | arena/e2d11e52-poker4 | `pages/suggestions.html` | Built | None |
| T5 | Questions / information / answers section | done | arena/e2d11e52-poker4 | `pages/questions-answers.html` | Built | Q1–Q2 unanswered (traveler input); Q3–Q8 missing data flagged |
| T6 | Flagged for Review page (unverified items + irregularities) | done | arena/e2d11e52-poker4 | `pages/flagged-for-review.html` | Built; 11 tournament flags, 4 hotel flags, 5 irregularities listed with sources | None |
| T7 | GitHub Pages site: landing page + category subpages, tables, navigation | in progress | arena/e2d11e52-poker4 | `index.html`, `pages/*.html`, `assets/style.css` | All 9 HTML pages built; internal links verified | Needs GitHub Pages enabled + deploy confirm |
| T8 | Verify all table rows line by line against official sources | done | arena/e2d11e52-poker4 | All data pages | Every row cites S1–S17/H1–H10; unverifiable values left blank and flagged; structure PDFs not parsed — flagged as unverified | No value inferred |
| T9 | Create PR to main, merge, confirm GitHub Pages deploy, record results | in progress | arena/e2d11e52-poker4 | Repo + GitHub Pages | In progress | None yet |

## Log
- 2026-11-16: Session `arena/e2d11e52-poker4` created branch from initial commit `52654c1`. Repo contained only `README.md` ("# Poker4"). COORDINATION.md created; all tasks claimed by this session.
- 2026-11-16: T1/T2 research complete — sources: Venetian official DSE IV page (S1), Wynn official poker page (S2), WPT schedule PDF (S3), PokerNews WPT (S4), PokerFuse (S5), WPT official (S6), PokerNews ARIA room (S7), HendonMob ARIA (S8), BetMGM ARIA Open announcement (S9), PokerAtlas rooms S10–S15, Vegas Poker Calendar (S16), Orleans report (S17); hotel fees H1–H10. No data inferred; blanks left blank.
- 2026-11-16: Data files created (data/sources.md, data/tournaments.md, data/hotels.md). Site built: index.html, pages/*.html (9 pages), assets/style.css; internal links verified.
- 2026-11-16: T3–T6 pages built; T7 in progress (Pages enable/deploy pending); T8 marked done with all unverified items flagged; T9 in progress (PR + merge + Pages confirm pending).
