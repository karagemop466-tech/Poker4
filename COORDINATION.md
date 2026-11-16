# Coordination board

Session: `arena/25b96c20-poker4` (current Arena branch; branch name is fixed by the workspace).

| Task | Status | Owner | Files |
|---|---|---|---|
| Research official live Las Vegas poker schedules, format limits, hotel costs, decision gaps; build sourced dashboard and review page | done | arena/25b96c20-poker4 | all project files |

## Activity log
- 2026-11-16: Inspected repository before work; no existing coordination file, tasks, or other session claims. Repository initially contained only README.md. Claim recorded here. This workspace is a single active branch; no separate session branch was created.
- 2026-11-16: Built static dashboard and category pages. Tournament evidence source: official Venetian DeepStack Extravaganza IV schedule (linked on each event row); captured future event dates/times, buy-ins, selected published guarantees and format labels. No single-entry assertion made because the listing does not confirm max entries/rebuy/add-on. Hotel properties link to official sites; prices/fees intentionally blank without dated official quote. Added decision checklist and flagged-review page.
- Verification: Checked the official Venetian schedule page and linked structure PDFs/listing directly. HTML local-link audit and `git diff --check` passed. Guarantee/buy-in arithmetic checked: $10,000/$300=33.3×; $8,000/$200=40×; $15,000/$400=37.5×; $30,000/$600=50×. Labeled as rough guarantee ratios, not expected value. No trip dates/occupancy supplied; hotel prices not asserted.
- Irregularities: an official future schedule does not prove events will operate unchanged; entry/add-on terms and future actual pools not confirmed; one venue schedule is not exhaustive of all Strip-area rooms; alternate hotel door-to-door walking times not confirmed. See `review.html`.
- PR #1: https://github.com/karagemop466-tech/Poker4/pull/1 — merged to `main` on 2026-11-16 (merge commit `ccb79faf59a3e8e2c94ea4044f10585ab5bfe13a`).
- GitHub Pages workflow run `43934149456` succeeded. Pages API reports public site `https://karagemop466-tech.github.io/Poker4/` and status `building` at first check; deployment workflow completed successfully.
