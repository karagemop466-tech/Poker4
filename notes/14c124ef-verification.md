# Session 14c124ef — independent verification record (2026-11-17)

Session: `arena/14c124ef-poker4` · branch `arena/14c124ef-poker4` · from `main` @ `ff3fa36`.
Machine copy: [`data/14c124ef/verification.json`](../data/14c124ef/verification.json).
Every sentence below was fetched live from the linked official page on **2026-11-17** and is copied verbatim.
Nothing was inferred; canonical files were **not edited** — findings are recorded here for the integration sessions.

## Why this session exists

Two other sessions hold active claims that converge on the shared root files (open PR #65 from `arena/e281a2cc-poker4`; a full-root rewrite branch from `arena/a3838778-poker4`). This session therefore took the verification lane the build environment could not do itself: several official hotel pages (flag F11) and PDF chunks (flag F7) were unreachable from the sandbox scraper, and one fee source was an expired promo (flag F19). This session's web tooling reached all of them.

## V1 — Hotel lane (flags F9, F11, F19)

| # | Property | Field | Official value read today | Verbatim (official page) | Source for manual review |
|---|----------|-------|---------------------------|--------------------------|--------------------------|
| H1 | Venetian/Palazzo | Resort fee | **$55 + tax per night** (matches canonical) | "Rates include a daily Resort Fee of $55 plus tax per night, payable upon check-in." | [resort-fee.html](https://www.venetianlasvegas.com/resort/resort-fee.html) |
| H2 | Venetian/Palazzo | Room tax | **13.38%** (matches canonical; F9 re-verified independently) | "Daily rates do not include the applicable Clark County Room Tax of 13.38%." | [hotel-terms-and-conditions.html](https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html) |
| H3 | Venetian/Palazzo | Parking | **$20/day guests, valet $40** (matches; adds non-guest Fri–Sun $25) | "The daily fee for registered hotel guests is $20/day, seven days a week. For non-hotel guests, the fee is $20, Monday – Thursday, and $25/day Friday – Sunday. Valet parking is $40/day." | same terms page |
| H4 | Venetian/Palazzo | Cancellation | Deposit at confirmation; prepaid offers non-cancellable; $100 early check-out charge (canonical blank stands) | "A deposit for your stay, including suite, fee, and tax, will be billed upon reservation confirmation. … bookings made using a prepaid offer are non-cancellable and non-refundable … Check-out prior to your scheduled departure date will result in an additional charge of $100 plus tax." | same terms page |
| H5 | Bellagio | Resort fee | **$55.00 + applicable tax** (fills canonical blank) | "Daily Resort Fee. A daily resort fee of $55.00 plus applicable tax will be applied to all reservations." | [Bellagio reservation terms](https://bellagio.mgmresorts.com/en/terms-and-conditions.html) |
| H6 | Bellagio | Cancellation | First night refundable if cancelled **72 h** before arrival | "The first night's deposit is fully refundable provided a timely notice of cancellation is received … at least 72 hours prior to the arrival date, unless specifically excluded by booked offer." | same |
| H7 | ARIA | Resort fee | **$55.00 + applicable tax** (fills canonical blank) | "Daily Resort Fee. A daily resort fee of $55.00 plus applicable tax will be applied to all reservations." | [ARIA reservation terms](https://aria.mgmresorts.com/en/terms-and-conditions.html) |
| H8 | ARIA | Cancellation | First night refundable if cancelled **72 h** before arrival | "The first night's deposit is fully refundable provided a timely notice of cancellation is received by Room Reservations at 866.359.7757 at least 72 hours prior to the arrival date…" | same |
| H9 | Wynn/Encore | Resort fee | **$55 + tax** (bookings on/after Jan 15 2025; $50 before); Tower Suites $55 (F19: value now confirmed on live pages with an active window) | "Reservations booked prior to January 15, 2025, will be charged a daily resort fee of $50 plus tax; reservations booked on or after January 15, 2025, will be charged a daily resort fee of $55 plus tax." | [Wynn terms 850014](https://www.wynnlasvegas.com/terms-and-conditions/850014), [Wynn terms DK26WLV2](https://www.wynnlasvegas.com/terms-and-conditions/DK26WLV2) (offer valid Oct 2 2026 – Mar 31 2027) |
| H10 | Wynn/Encore | Parking | **Free self-park for registered guests incl. poker-room guests; $25/day non-guests; valet $40** (fills blank) | "Self-parking at the resort is complimentary for all Wynn and Encore Resort and Tower Suite registered guests … For non-registered guests the daily parking fee is $25 per day, with the first three (3) hours free. … Valet parking is $40 per day up to 24 hours (no grace period, no re-entry)." | Wynn terms 850014 |
| H11 | Wynn/Encore | Cancellation | 48-h baseline; **F1 week 11/15–11/21/2026: full deposit + 3-week cancellation; 12/29–12/31/2026: 30-day** (fills blank) | "cancellations must be received at least 48 hours prior to arrival date … For all reservations that include a stay on 11/15/2026 through 11/21/2026, a full deposit of all room nights and tax will be charged … and a three-week cancellation policy is applied." | Wynn terms DK26WLV2 |
| H12 | Treasure Island | Resort fee | **$49.95 + tax, REQUIRED** for standard bookings; optional only for qualified bookings (canonical wording "Optional…" should be tightened) | "The $49.95 + tax daily resort fee* at TI Las Vegas … Resort fees are required, and in addition to the room rates displayed online with the exception that resort fees are optional only for My TI Guestbook members that book our exclusive TV Ad Special offer, qualified Treasury Players Club casino members, and qualified meeting groups…" | [TI tower-suite](https://treasureisland.com/hotel/tower-suite) |
| H13 | Treasure Island | Parking | Always Free Valet & Self Park (fee inclusion; matches homepage headline) | "Inclusions: Always Free Valet Parking & Self Park Garage; High Speed (up to 20 Mbps) WiFi…" | same |
| H14 | Caesars Palace / Harrah's / LINQ / Flamingo / Horseshoe | Resort fee | **Official corporate range $45–$60 + applicable tax**; waived Diamond/Seven Stars (per-property exact amounts remain unpublished — blanks stay blank) | "Room reservations are subject to a daily resort fee between $45-$60 plus applicable tax. Resort fees are waived for Diamond and Seven Stars." | [Caesars corporate disclaimer](https://www.caesars.com/corporate/disclaimer) (Hotel Disclaimer section) |
| H15 | Caesars properties | Cancellation | Complimentary-room no-show $50 unless cancelled by 6 pm arrival day; paid rates follow hotel policy; booking flow advertises "FREE 48-Hour Cancellation*" | "Complimentary room no-show fee of $50 unless reservation cancelled by 6pm of arrival date. Paid reservations are subject to hotel cancellation polices." | same |

Notes: `caesars.com/caesars-palace/resort-fee` and `caesars.com/harrahs-las-vegas/resort-fee` redirect to the property homepages and print **no fee text** — that is why per-property Caesars amounts stay blank (irregularity IR4).

## V2 — WPT World Championship structures booklet (flag F7 → closed for this booklet)

All 8 chunks of the official structures PDF were read line-by-line today: [WPT_World_Championship_Structures.pdf](https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf)

13 events are covered. Registration clauses, verbatim:

| Event | Date(s) | Fee split printed | Registration clause (verbatim) |
|---|---|---|---|
| $600 NLH $400K GTD | Nov 27–30 (1A–1F + Day 2) | $510 pool + $65 fee + $25 staff | "Unlimited re-entry for each starting flight will be available until the start of level 9." |
| $600 TORSE | Nov 27, 12 p.m. | $510 + $65 + $25 | "Unlimited re-entry will be available until the start of level 9" |
| $400 PLO | Nov 27, 1 p.m. | $337 + $45 + $18 | "Unlimited re-entry will be available until the start of level 9 (approximately 5:30 p.m.)." |
| $600 Mixed Triple Draw (A-5, 2-7, Badugi) | Nov 28, 12 p.m. & Dec 20, 1 p.m. | $510 + $65 + $25 | "Unlimited re-entry will be available until the start of level 9." |
| $800 NLH $1M GTD | Nov 30 – Dec 4 | $695 + $72 + $33 | "Unlimited re-entry for each starting flight will be available until the start of level 9." |
| $600 Limit Omaha 8 | Nov 30, 12 p.m. | $510 + $65 + $25 | "Unlimited re-entry will be available until the start of level 9" |
| $600 Limit Omaha 8/Stud 8 | Dec 1, 12 p.m. | $510 + $65 + $25 | "Unlimited re-entry will be available until the start of level 9" |
| $1,100 PLO | Dec 1, 1 p.m. | $975 + $85 + $45 | "Unlimited re-entry will be available until the start of level 9 (approximately 5:30 p.m.)." |
| $1,600 NLH $1M GTD | Dec 3–5 | $1,430 + $120 + $50 | "Unlimited re-entry for each starting flight will be available until the start of level 10." |
| $600 HORSE | Dec 4, 12 p.m. | $510 + $65 + $25 | "Unlimited re-entry will be available until the start of level 9 (approximately 4:30 p.m.)." |
| **$1,100 WPT Prime Championship $5M GTD** | Dec 5–12 | $970 + $90 + $40 | **"One (1) Entry and One (1) re-entry for each starting flight will be available until the start of level 10 (approximately 6:45 p.m.)."** — still re-entry, five starting flights, so not single-entry |
| $600 NLH Turbo $50K GTD | Dec 5/6/7/8/9/12/14 9 p.m.; Dec 21 6 p.m. | $515 + $60 + $25 | "Unlimited re-entry will be available until the start of level 9." |
| $1,600 PLO Mystery Bounty $500K GTD | Dec 6–7 | $930 pool + $500 bounty + $120 fee + $50 staff | "Unlimited re-entry for each starting flight will be available until the start of level 10." |

Extra facts read verbatim from the same booklet:
- "All Tournament and Bounty prizes are included in the Tournament guaranteed prize pool of $500,000 … $325,000 of the Guarantee will be designated for the Tournament prize pool and $175,000 … for the Bounty prize pool." → bounty-row ratios stay labeled non-comparable.
- "$10,400 will be withheld from the prize pool and issued to first place in the form of an entry to the December 2027 WPT World Championship." (Prime Championship)
- No add-on is stated for any of the 13 events. **Zero single-entry confirmations — the standing 0-of-253 finding holds.**

## V3 — Spot re-checks of published rows

| Check | Result | Source |
|---|---|---|
| Caesars Palace 4 daily rows (10 am/2 pm/6 pm/9 pm, $100, 20,000 chips, $1,000 GTD, 20-min levels, $50 add-on → 15,000 chips) | **match exactly**, add-on already classified spend-advantage | [Caesars poker-tournaments page](https://www.caesars.com/las-vegas/explore/casino/poker-tournaments-las-vegas-strip) |
| Bellagio Friday $600 sheet (30,000 chips incl. optional gratuity; $510/$50/$40 split; re-entry through L8) | **match**; gratuity-for-chips mechanic missing from canonical add_on (IR1) | [Friday PDF](https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt9cf95b0e60ec253e/6af491a3a9851d75c40be840/mgm-bellagio-poker-fridays-$600-nlh.pdf) |
| Bellagio Saturday sheet | three-way conflict confirmed live ($1,100 title / $1,000 page label / $600 in rule 7) — canonical blank+flag stands; plus IR1 (gratuity) and IR2 (stale 9/13/26 Day-2 reference) | [Saturday PDF](https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt6d47974bf5a7d9b6/6af491a391a6e8e4230c9e07/mgm-bellagio-poker-saturdays-$1000-nlh.pdf), [Bellagio poker page](https://bellagio.mgmresorts.com/en/casino/poker.html) |
| Bellagio Sunday $400 H.O.R.S.E. sheet (30,000 incl. optional gratuity; $340/$35/$25 split; re-entry through L8) | **match**; same IR1 | [Sunday PDF](https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt07fcf1244a6da661/6af491a339e2b4f6b76a86ad/mgm-bellagio-poker-sundays-$400-horse.pdf) |
| WPT schedule PDF weekday labels | **F4 confirmed live**: the current PDF prints both "Dec. 18 Wednesday" rows and "Dec. 18 Friday" rows; Dec 18, 2026 is a Friday | [WPT schedule PDF](https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf) |
| Horseshoe daily slate | six daily NLH at 9/11/2/5/8/11 pm officially printed, **no buy-ins printed** on any official page reached → no rows built (no-inference policy) | [Caesars poker-tournaments page](https://www.caesars.com/las-vegas/explore/casino/poker-tournaments-las-vegas-strip) |

## Flags touched

- **F7** — closed for the WPT WC structures booklet (all chunks read; E1).
- **F9** — 13.38% room tax independently re-verified on the live official terms page (H2).
- **F11** — partially addressed: Bellagio + ARIA fees/cancellation now officially verified (H5–H8); Caesars properties have an official range only (H14, IR4); per-property blanks stay blank.
- **F19** — replacement evidence: $55 Wynn fee confirmed on current official pages with an active validity window (H9); re-pointing the canonical source is an integration-session edit.
- **F4** — confirmed still live with fresh evidence (E6/IR5).

## Irregularities for review (published here; nothing edited)

1. **IR1 — Bellagio gratuity-for-chips (moderate).** All three current Bellagio sheets print an optional at-registration staff gratuity that buys extra chips ($40→+15,000 FRI; $40→+20,000 SAT; $25→+15,000 SUN). Canonical `add_on` fields say "not_stated_in_sheet", so these rows miss the spend-more-advantage class. Starting stacks are printed *inclusive* of the optional gratuity (15,000 + 15,000), so a player who declines starts short-stacked — a like-for-like comparison caveat.
2. **IR2 — stale date on the current Bellagio Saturday sheet (moderate).** Rule 4 references "Combined Final Day 2 (9/13/26)" on a sheet still linked from the live page.
3. **IR3 — Wynn F1-week cancellation (info).** Stays including 11/15–11/21/2026: full deposit at confirmation + 3-week cancellation; 12/29–12/31/2026: 30-day (offer terms, active window).
4. **IR4 — Caesars fee is an official range (info).** "$45–$60 plus applicable tax" is the only official value; per-property exact amounts remain unpublished; the per-property /resort-fee URLs redirect without fee text.
5. **IR5 — WPT PDF mixed weekday labels (info).** F4 evidence refreshed; consumers must not silently correct the label.

## Adopted-elsewhere note

Per the coordination rules, shared outputs change only via the final integration sessions. The values above are recorded session-scoped so whichever session next owns the canonical data can:
- fill the Bellagio/ARIA fee + cancellation blanks (H5–H8),
- re-point the Wynn fee source and add parking/cancellation (H9–H11),
- tighten the TI fee wording (H12),
- attach the official Caesars range with a "range, not per-property" caveat (H14),
- add the Bellagio gratuity mechanic to the spend-advantage classification (IR1).
