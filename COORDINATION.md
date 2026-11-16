# Coordination board

Shared task board for this repository. Status values: unclaimed · in progress · done · needs review.
"needs review" items are published on the **Flagged for Review** page and do not block anything.

## Task board

| Task | Status | Owner (session / branch) | Files in scope | Notes |
|---|---|---|---|---|
| Research official live Las Vegas poker schedules, formats, hotel costs, decision gaps; build sourced dashboard and review page | done | `arena/25b96c20-poker4` (PR #1, merged) | all project files | Earlier pass. Row-level status board was never updated to done; corrected here (see Irregularities R3). |
| Full re-verification of Strip tournaments (single-entry filter), hotel resort fees, daily plan, repo review, expanded site, PR + Pages deploy | in progress | `c07371e3` · `arena/c07371e3-poker4` | `*.html`, `style.css`, `data/*.csv`, `tools/build.py`, `COORDINATION.md`, `README.md`, `.github/workflows/pages.yml` (unchanged) | Claimed 2026-11-16 (UTC). Other session branches in this repo are not modified by this session. |

## Claim details: `c07371e3` (2026-11-16 UTC)

- Branch is fixed by the Arena workspace: `arena/c07371e3-poker4`. The `session-<id>/<task>` naming from the brief is superseded by that rule, so this session works on one branch only.
- Base: `main` (PR #1 merge `ccb79fa`), merged into this branch before editing. Main's history is a separate root commit from the original `52654c1`; the merge used `--allow-unrelated-histories`.
- Scope: this session edits only the files listed above. Pages that were produced by the earlier pass are rebuilt from `data/*.csv` by `tools/build.py`.

## Activity log

- 2026-11-16: Inspected repository. Found PR #1 (`arena/25b96c20-poker4`) already merged to `main` with a first-pass site. Read main, the PR #1 head, and the other session branches' `COORDINATION.md` files (read-only; no changes made to them).
- 2026-11-16: Claimed the task above in this file and merged `origin/main` into the session branch.

## Irregularities R3 (coordination)

- R3: PR #1's board row still says "in progress" after its PR merged; it is marked done here.
- R3b: Other session branches (`arena/0337316e…`, `2da41d2b…`, `60fb62da…`, `6313b65a…`, `9ae2dbdb…`, `abd38ed7…`, `e2d11e52…`, `2ab1e09`…) each claim the same research task on their own branch from the same base. Their claims do not appear on `main`. Possible duplicate work; flagged, not resolved here.
