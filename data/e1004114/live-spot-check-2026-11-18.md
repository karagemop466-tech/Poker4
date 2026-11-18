# Live spot-check of official sources — session arena/e1004114-poker4 (E1)

Retrieved: 2026-11-18 (UTC), using the fetch tool against the live official pages and PDFs.
Scope: the trip-cost inputs and the single-entry evidence that the published pages depend on.
This is a **spot-check**, not the full 253-row re-verification (that was done on 2026-11-17 by b808eea0 and is recorded in COORDINATION.md).

| # | Official URL (operator domain) | What was read live | Compared with | Result |
|---|---|---|---|---|
| 1 | https://www.venetianlasvegas.com/resort/resort-fee.html | "Rates include a daily Resort Fee of $55 plus tax per night, payable upon check-in." | `data/hotel-facts.json` (venetian resort-fee page, captured 2026-11-17) | MATCH |
| 2 | https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html (page 2 of 2) | "Daily rates do not include the applicable Clark County Room Tax of 13.38%." · "$55 plus applicable tax per night" · parking: registered hotel guests $20/day; non-hotel guests $20 Mon–Thu, $25 Fri–Sun; valet $40/day; Sapphire members and above complimentary self-parking | `data/hotel-facts.json`, `data/room-facts.json`, `data/hotels.json` | MATCH (13.38% and $55 are used by the trip calculator; parking is flagged F32) |
| 3 | https://www.venetianlasvegas.com/resort/casino/poker.html | "Non-registered hotel guests who play for three hours or more in our tournaments or cash games receive complimentary self-parking." · "Open 24 hours daily." | `data/hotel-facts.json` (captured text) | MATCH — scope note F32 |
| 4 | https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_12.pdf (sheet for Event 26, $800 NLH, $500,000 GTD) | Rules 01–13 read in full. No clause about entries, re-entries, rebuys or add-ons. Rule 08: "Any player who bags chips for Day 2 may not play a subsequent flight." Late registration "6 levels + Break (~ 3:40 PM)". | `data/structure-audit.json` (V_S12: entry_policy `not_stated_in_sheet`); flag F1 and F15 | MATCH — single-entry stays **unverified** for Event 26; the bagging rule is the multi-flight question (F15), not a confirmation |
| 5 | https://cdn.wynnresorts.com/image/upload/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf (pages 1 and 3 of 3) | General T&C 3, 4, 9 (entry fee cash/chips, forfeiture after chips are in play). Nightly $160 NLH $10,000 GTD sheet: "beginning at 6 p.m."; "The tournament entry fee, as well as the re-entry fee, is $160"; "Registration, re-entries, and one (1) add-on per entry…" | `data/room-facts.json` WYNN-DAILY-4 (6 PM, re-entries allowed, add-on) and `data/site-events.json` | MATCH — the row is correctly excluded from the single-entry list |

## Captured-text checks (not re-read live in this session)

- The Friday $240 $40,000 GTD Wynn daily sheet ("Re-entry is NOT allowed"; rebuys and add-ons) and the Monday–Thursday $200 sheet: stored verbatim in `data/room-facts.json` from the same PDF; the published rows agree. Not re-read live.
- The other 36 Venetian structure sheets: read on 2026-11-17 (b808eea0 / 75757cc1). Not re-read in this session.

## Irregularities found in this spot-check (all recorded on the Flagged page)

- **F31** — `data/structure-audit.json` W_DAILY summary is incomplete (captures only the Friday rebuy line). The published rows are correct; the audit summary is not to be cited alone.
- **F32** — Venetian parking has two official rules for two different kinds of guest. Not a contradiction; a budgeting ambiguity.
- **F15 (confirmed wording)** — the bagging sentence is present on sheet 12 exactly as recorded; it is still not a single-entry confirmation.

## Result

No value in the published rows changed as a result of this spot-check. Three items were added to the Flagged page (F31, F32) and two monitor flags were updated (F21, F29), and the provenance fix in F28 was re-committed.
