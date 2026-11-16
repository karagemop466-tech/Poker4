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
