# COORDINATION.md — Shared task board

Repo: `karagemop466-tech/Poker4` · Branch: `arena/df41f5c6-poker4` (base `52654c1` on `main`)
Session ID: `df41f5c6` (single session on this branch; no other sessions were observed on this branch at claim time)

Status values: `unclaimed` · `in progress` · `done` · `needs review` (published on the Flagged for Review page; does not block)

Note on process: the session brief asks for per-task branches (`session-<id>/<task>`). The session rules for this run restrict all work to the single branch `arena/df41f5c6-poker4`, so every task below is claimed and completed on that branch, in one ordered sequence, with commits after each task.

## Task board

| ID | Task | Status | Owner | Files / scope | Notes |
|----|------|--------|-------|---------------|-------|
| T1 | Repo review (line by line, sources, irregularities) | done | df41f5c6 | `data/repo_review.json`, `docs/repo-review.html` | See log entry 2026-11-16 T1 |
| T2 | Live poker tournaments near the Strip (single-entry, spend-more, satellites, unverified) | done | df41f5c6 | `data/tournaments.json`, `data/venues.json` | Official sources only; third-party used only for flags |
| T3 | Hotels near tournament venues (resort fees, verified snapshot, distances) | done | df41f5c6 | `data/hotels.json`, `data/distances.json` | Walking times NOT verified; straight-line distances computed |
| T4 | Daily schedule (8 AM – all day) | done | df41f5c6 | `docs/schedule.html` (generated) | No verified event starts before 10:00 AM |
| T5 | Executive summary | done | df41f5c6 | `data/summary.json`, `docs/index.html` (generated) | |
| T6 | Questions, information gaps and answers | done | df41f5c6 | `data/questions.json`, `docs/questions.html` (generated) | |
| T7 | Site improvement suggestions (decision-only, no implementation) | done | df41f5c6 | `data/suggestions.json`, `docs/suggestions.html` (generated) | |
| T8 | GitHub Pages site build + verification script | done | df41f5c6 | `scripts/`, `docs/` | Pages source switched to `/docs` on `main` |
| T9 | Flagged for Review page | done | df41f5c6 | `data/flagged.json`, `docs/flagged.html` | |
| T10 | Integration: merge, re-verify, build check, PR to `main`, merge, Pages deploy check | in progress | df41f5c6 | whole repo | See log |

## Log

### 2026-11-16 — Claim
- Session `df41f5c6` claimed T1–T10 on branch `arena/df41f5c6-poker4`. No other claims existed (repo contained only `README.md`).
- Scope rules applied: official sources only for table values; blank + flagged when not confirmed; computed values labeled as computed.

### 2026-11-16 — T1 Repo review
- Reviewed every tracked file (`README.md`, the only file) and git metadata (one commit, `52654c1 Initial commit`, author `karagemop466-tech`, Nov 16 2026). See `docs/repo-review.html`.
- Irregularities flagged for review (see Flagged for Review page).

### 2026-11-16 — T2–T3 Research (official sources)
- Official sources used: casino poker-room pages, official schedule/structure PDFs (Wynn, Venetian, MGM Grand, Caesars Palace), official resort-fee pages (Venetian, Wynn terms), Venetian booking page snapshot.
- Reference coordinates (non-official, Wikipedia) used only for straight-line distance screening.
- Sources list: `data/sources.json` (every source has an accessed date of 2026-11-16).
- Verification performed: every table row is tied to a source ID; rows with structure-sheet checks are labeled `structure verified`; rows that rely on the official schedule only are labeled `schedule only`.

### 2026-11-16 — T10 Integration (pending)
- Will re-run `scripts/verify.py`, build `docs/`, merge to `main` via PR, merge, and confirm GitHub Pages deployment.
