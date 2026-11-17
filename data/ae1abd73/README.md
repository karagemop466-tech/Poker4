# ae1abd73 — X1: independent re-check of Venetian DSE IV structure sheets

Retrieved 2026-11-17 from the official Venetian Las Vegas structure-sheet PDFs
(`https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_N.pdf`, N = 1–37).

## Result
- **37 of 37 sheets read.**
- **0 sheets** state single-entry, freezeout, or "no re-entry / no rebuy / no add-on" as such.
- **0 sheets** state re-entry, rebuy or add-on as such.
- **1 sheet with explicit subsequent-buy-in wording:** sheet 8 (events 18 and 58, Valuetown Bounty), rule 7: *"All subsequent buy in's after the initial buy in will be $200."* This is the one line that points to a multi-entry option on the official sheet.
- **13 sheets with a flight rule:** sheets 2, 3, 4, 9, 10, 12, 13, 14, 20, 21, 35, 36, 37 state *"Any player who bags chips for Day 2 may not play a subsequent flight."* The wording implies that a player who did not bag for Day 2 may play a later flight. That is a possible re-entry path. It is not a stated re-entry rule, so the events stay **unverified** for single-entry.
- **Discrepancies vs. `data/feature/structure-extract.md`:** 0. Start time, chips, level length, late-registration, guarantee and house fee match the extract on all 37 sheets.

## Verdict
The existing verdict in `data/feature/structure-extract.md` holds: **no Venetian DSE IV event is confirmed single-entry from the official structure sheets.** Labels stay "unverified." This session did not edit `data/feature/*`.

## Files
- `structure_recheck.json` — per-sheet record (events, start, chips, level length, late reg, guarantee, house fee, entry wording, flighted flag).

## Not covered
- The official DSE IV schedule page and the structure sheets were not re-read in this pass beyond what is needed for the rule check.
- Event-level single-entry for non-Venetian rooms (Wynn, Bellagio, Caesars, Aria, Horseshoe) is not covered here.
- Walking times, hotel rates, and monitoring are not covered here.
