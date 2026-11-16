# Poker Trip Planner — Las Vegas

A source-linked decision dashboard for upcoming Las Vegas poker tournaments, single-entry rule verification, hotel costs, all-day scheduling limits, decision questions, and open research gaps. **Snapshot: November 16, 2026 (UTC).**

## Dashboard

- [Executive overview](index.html)
- [Tournament shortlist and special formats](schedule.html) ([legacy route](tournaments.html))
- [Hotels and true-cost method](hotels.html)
- [Decision checklist and site suggestions](decisions.html) ([legacy route](questions.html))
- [Flagged for Review](review.html)
- [Official sources and methodology](sources.html)

## Verified scope and important caveats

The current forward schedule fully reviewed is the official Venetian DeepStack Extravaganza IV (Nov 16–Dec 23, 2026). The tournament table is a screened candidate list, not a complete Strip-wide calendar. The official materials reviewed do **not** confirm a one-entry limit or rule out re-entry, rebuy, or add-ons, so **zero events are certified as single-entry**. No 8:00 AM event appears in the reviewed candidate schedule; the earliest candidate starts at 10:10 AM.

The poker room is at The Palazzo, Level 2 of Grand Canal Shoppes, within The Venetian Resort. The official room page gives directions from both lobbies but does not publish walking minutes. Dated hotel totals are unknown without travel dates and occupancy. Official starting poker-suite rates are conditional and are not a booking quote; unknown price, fee, and distance fields stay blank and are flagged.

Every data row in the dashboard links to an official organizer or property source. Review the [Flagged for Review page](review.html) before acting; schedules and terms can change.

## Implementation

The Pages source was already configured to deploy the repository root from `main` at [https://karagemop466-tech.github.io/Poker4/](https://karagemop466-tech.github.io/Poker4/). `.github/workflows/pages.yml` validates JavaScript syntax and local site links; the Pages publication itself uses the repository's existing branch-based deployment configuration. Site content is static HTML/CSS/JavaScript in the root and has no build dependency.

Run locally with `python3 -m http.server 8000`.
