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
| T1 | Research live upcoming poker tournaments near Las Vegas Strip (official sources) | in progress | arena/e2d11e52-poker4 | `data/tournaments.md`, `data/sources.md` | In progress | None yet |
| T2 | Research hotels within walking distance of tournaments (official sources) | unclaimed | arena/e2d11e52-poker4 | `data/hotels.md`, `data/sources.md` | Not started | None yet |
| T3 | Executive summary | unclaimed | arena/e2d11e52-poker4 | `pages/executive-summary.md` | Not started | None yet |
| T4 | Suggestions section (site improvement + decision suggestions) | unclaimed | arena/e2d11e52-poker4 | `pages/suggestions.md` | Not started | None yet |
| T5 | Questions / information / answers section | unclaimed | arena/e2d11e52-poker4 | `pages/questions.md` | Not started | None yet |
| T6 | Flagged for Review page (unverified items + irregularities) | unclaimed | arena/e2d11e52-poker4 | `pages/flagged-for-review.md` | Not started | None yet |
| T7 | GitHub Pages site: landing page + category subpages, tables, navigation | unclaimed | arena/e2d11e52-poker4 | `index.html`, `pages/*.html`, `assets/*` | Not started | None yet |
| T8 | Verify all table rows line by line against official sources | unclaimed | arena/e2d11e52-poker4 | All data pages | Not started | None yet |
| T9 | Create PR to main, merge, confirm GitHub Pages deploy, record results | unclaimed | arena/e2d11e52-poker4 | Repo + GitHub Pages | Not started | None yet |

## Log
- 2026-11-16: Session `arena/e2d11e52-poker4` created branch from initial commit `52654c1`. Repo contained only `README.md` ("# Poker4"). COORDINATION.md created; all tasks claimed by this session. Research in progress for T1.
