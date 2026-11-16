# Coordination

| Task | Status | Owner / session | Scope |
|---|---|---|---|
| Integrated official-source research, tournament/hotel decision dashboard, review flags, and Pages workflow | done | `arena/60fb62da-poker4` (session `60fb62da`) | Entire repository except `.git`; single active Arena branch is fixed by platform |

## Coordination constraints
- Checked the repository before work: only `README.md` was present; no existing coordination board or claimed tasks were found.
- Arena requires this session to remain on `arena/60fb62da-poker4`; separate task branches/worktrees and an independent integration branch cannot be created or used in this session. The task was handled as one integrated scope on the assigned branch, with explicit source attribution and review flags.
- Shared data and site navigation were developed in this single integration scope because there were no other active session claims in the repository.

## Source and verification log
- Official tournament series schedule: [Venetian DeepStack Extravaganza IV, Nov 16–Dec 23, 2026](https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html). Read all four page chunks. Used for dates, local start times, event numbers/names, buy-ins and guarantees as stated; same page links each official structure sheet.
- Tournament structures opened and reviewed: [Event 02/12 $300 structure](https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_5.pdf), [Events 03–05 $200 RaceDay](https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_18.pdf), [Event 06 $200](https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_29.pdf), [Event 10 $400](https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_6.pdf), [Events 14/28/63 $600](https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_7.pdf), and [Event 27 $600 BIG O](https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_28.pdf). Verified buy-ins, guarantees where disclosed, start/registration times, event format and disclosed rake splits. No reviewed candidate structure confirms single-entry or a no-re-entry/no-rebuy/no-add-on rule; all are therefore explicitly unverified and flagged.
- Hotel rates/fees: [Venetian 2026 poker suite rates and play requirements](https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html), [official resort fee](https://www.venetianlasvegas.com/resort/resort-fee.html), [hotel tax/fee terms](https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html). Verified $119/$209 starting poker rates, $55 nightly fee plus tax, 13.38% room tax, availability/occupancy qualifications, and six hours of live cash play or a $300+ tournament buy-in per night for poker-rate qualification. Math checked: ($119+$55)×1.1338=$197.28; ($209+$55)×1.1338=$299.32. These are conditional starting floors, not real dated quotes.
- Venue location: [official Venetian poker room page](https://www.venetianlasvegas.com/resort/casino/poker.html). Verified poker room at Palazzo Level 2, Grand Canal Shoppes; official directions from both Palazzo and Venetian lobbies. No minutes published; dashboard deliberately shows no invented walking times.
- Site verification: `node --check data.js`, `node --check site.js`, `git diff --check`, local HTML-relative-link existence scan (six pages), and hotel floor arithmetic all passed. Static implementation uses no data backend or build dependency.

## Irregularities and unresolved items (published on Flagged for Review)
- No reviewed official event rules say one entry only or prohibit re-entry/rebuy/add-on. This is the blocking fact for a strict single-entry recommendation; zero candidates are marked verified single-entry.
- The series calendar does not offer an 8:00 AM candidate start; earliest non-satellite candidate start found is 10:10 AM. Only the Venetian forward series is fully verified here, not every Strip room.
- Some entries do not publish a guarantee in the linked structure; those cells remain blank. The bounty-event guarantee includes bounties and is not compared as a plain prize-pool amount.
- No travel dates, guest count or room type were provided; actual hotel quote/total is unknown. No independently verified walking-minute estimates or quality score for alternative hotels are available.
- Hotel poker-suite rate has a play threshold; the $200 events do not alone meet the published $300 tournament threshold.
- Official Venetian schedule/structure sheets reserve the right to change or cancel events. Re-check before travel or registration.

## Publication / integration
- The static Pages workflow is `.github/workflows/pages.yml` and deploys on `main` after Pages is configured to use GitHub Actions. Pull request, merge, and successful deployment details will be recorded here after the integration is published.
