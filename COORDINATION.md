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

## Integration record (arena-abd38ed7)
- PR: https://github.com/karagemop466-tech/Poker4/pull/3 (`arena/abd38ed7-poker4` → `main`)
- Merge: merge commit `176a1a00eaff74d60e3d24fe234a120d593598c3`, merged with `--merge` (no `--auto`) on 2026-11-16.
- Merge conflict: first attempt failed ("merge commit cannot be cleanly created") because PR #1 changed `main` (COORDINATION.md add/add). Resolved by merging `origin/main` into the branch and keeping both logs; logged above.
- Pages: `pages.yml` run for `176a1a0` completed **success**. Live URLs not checked from the sandbox (outbound access to github.io is not allowed here): https://karagemop466-tech.github.io/Poker4/ and https://karagemop466-tech.github.io/Poker4/verified/
- Branch naming: the branch is `arena/abd38ed7-poker4`, which does not match `session-<id>/<task>`. Renaming is not possible in this session (the branch name is fixed by the workspace). Logged as an open item.
- Post-merge note: the record above was committed on the session branch after the merge; it reaches `main` with the next merge.
