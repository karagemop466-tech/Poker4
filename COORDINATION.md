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
