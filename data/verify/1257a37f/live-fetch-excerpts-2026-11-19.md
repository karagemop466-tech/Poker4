# Live re-check excerpts — 2026-11-19 (session arena/1257a37f-poker4)

Method: pages re-read live on 2026-11-19 (~05:50–06:40 UTC) through the session's page
fetcher (markdown extraction). This is a **value-level** re-check: the sentences below were
on the official pages that day and were compared against the committed values. It is not a
byte-hash comparison — that remains the scheduled CI job (`url-check.yml`,
`tools/sync_official_sources.py`), whose last successful run before this round captured
2026-11-18T21:39Z. No value in the dashboard changed because of this round; additions are
dated rate-log lines, one new flag (F39), one extended question (Q4) and one new
suggestion (S13).

Per-value comparison table: [`1257a37f_source_recheck_2026-11-19.tsv`](1257a37f_source_recheck_2026-11-19.tsv).

## Venetian

- **DSE IV series page** — https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html
  - "DeepStack Extravaganza IV · November 16 – December 23, 2026 · More than $3.6 Million in guaranteed tournament prize pools"
  - Full 4-chunk table read. Sampled rows (Event 47 $2,200 $1M GTD 1A Sat Dec 12 10:10 AM; Event 26 $800 $500K GTD 1A Thu Dec 3 11:10 AM; Event 19 $400 $75K GTD 1A Sun Nov 29 11:10 AM; Event 3 $200 RaceDay Thu Nov 19 10:10 AM) match the committed rows exactly, including structure-sheet links.
- **Poker suite rates** — https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html
  - "These rates will start as low as $119 and $209 and can be higher. … There is a $55 resort fee per night stayed."
  - "During your stay, you will be required to play six hours of active live cash gameplay or buy in to a $300 or higher tournament for each night stayed."
  - Booking by phone, code EPOKR25. → two dated rate-log entries (2026-11-19).
- **Booking endpoint** — https://www.venetianlasvegas.com/booking?adults[]=2&arrival_date=2026-12-10&children[]=0&departure_date=2026-12-15&view=calendar
  - Returns the booking shell ("Your Venice meets Vegas getaway is loading"); room rates render only in JavaScript. No checkout total retrievable → F4 stands, blank stays blank.
- **Structure sheet 21** ($2,200 PokerAtlas Championship, Event 47) — https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_21.pdf
  - "$225 of the $2,200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $1,975 of every $2,200 Buy In."
  - "Any player who bags chips for Day 2 may not play a subsequent flight."
  - Late registration "9 levels + Break (~ 4:55 PM)"; 40,000 chips; 40-minute levels; guarantee $1,000,000. **No entry-count / re-entry / add-on clause.**
- **Structure sheet 12** ($800, Event 26) — https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_12.pdf
  - "$110 of the $800 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $690 of every $800 Buy In."
  - Same bagging clause; late registration "6 levels + Break (~ 3:40 PM)". **No entry-count / re-entry / add-on clause.**

## Wynn Las Vegas

- **Poker room page** — https://wynnlasvegas.com/casino/poker
  - "WPT WORLD CHAMPIONSHIP · November 27–December 21 … New for 2026, the Super Gold Million brings a $400 buy-in featuring a $3,000,000 guarantee!" → matches WPT-19 rows.
  - "WYNN SIGNATURE SERIES · January 11–24. 2027" with official PDFs (`Wynn_Signature_Series_Schedule.pdf`, `Wynn_Signature_Series_Structures.pdf`) → outside the current window; decision logged as suggestion S13.
  - Contradiction on one page: daily section "offering a total of $200,000 in guaranteed prize pools weekly" vs FAQ "daily tournaments run each day and feature $95,000 per week in guaranteed prize pools" → new flag **F39**.
  - Contradiction on days: FAQ "run each day" vs daily section "suspended during each Wynn Signature, Wynn Millions, and Classic tournament series" vs structures PDF "offered Monday-Thursday and may be suspended" → F39/F24.
  - FAQ: "Are preferred poker room rates available? Yes, please contact us at poker.reservations@wynnlasvegas.com for assistance." → dated rate-log entry (channel only, no rate printed).
  - FAQ: "Both cash and tournament play is held in the poker room located at the Encore." (consistent with F37).
  - FAQ parking: "$25 per day with the first three (3) hours complimentary. Guests of the Wynn Poker room will receive complimentary same-day parking." (consistent with the hotels table).
- **Offer terms 850257** — https://www.wynnlasvegas.com/terms-and-conditions/850257
  - "A daily resort fee of $55 plus tax will be added to your room account for each room night" (again for Tower Suites) → F19 re-confirmed.
  - This offer's cancellation terms: "A full deposit of all room nights and tax will be charged at the time of booking. Reservations are non-cancellable, non-refundable, and non-changeable." Offer-specific; no general Wynn cancellation policy published on any captured page.

## Caesars Palace & Horseshoe

- **Explore article** — https://www.caesars.com/las-vegas/explore/casino/poker-tournaments-las-vegas-strip (article dated July 17, 2026)
  - "At Caesars Palace … four No-Limit Hold'em tournaments each day at 10 a.m., 2 p.m., 6 p.m. and 9 p.m. Every event carries a $100 buy-in, starts you with 20,000 chips, and features a $1,000 guaranteed prize pool. Blinds increase every 20 minutes … a $50 add-on at the first break gives you an extra 15,000 chips."
  - "Most sessions finish in four to six hours" → the only official generic duration statement found; cited on Q4.
  - "At Horseshoe Las Vegas … six daily No-Limit Hold'em games. The times at 9 a.m., 11 a.m., 2 p.m., 5 p.m., 8 p.m. and 11 p.m." (mixture of buy-ins/levels/guarantees; no amounts printed in the article).
  - The F25 conflict (article's blanket $100 vs flyer's $160 at 2 p.m./9 p.m.) is unchanged on the live pages.

## Treasure Island

- **Deluxe Rooms** — https://treasureisland.com/hotel/deluxe-rooms
  - "The $49.95 + tax daily resort fee at TI Las Vegas …" · "Always Free Valet Parking & Self Park Garage" → unchanged.
  - "01 · $69* NIGHT + NO RESORT FEE … this package includes Optional Resort Fee, 2 for 1 Draft Beers, Always Free Parking & More!" with printed conditions (My TI Guestbook members booking the exclusive TV Ad Special, or qualified Treasury Players Club members; bookings via all.accor.com) → dated rate-log entry (2026-11-19).

## Bellagio & ARIA (MGM reservation terms)

- **Bellagio** — https://bellagio.mgmresorts.com/en/terms-and-conditions.html
  - "A daily resort fee of $55.00 plus applicable tax will be applied to all reservations."
  - "The first night's deposit is fully refundable provided a timely notice of cancellation is received … at least 72 hours prior to the arrival date" · "$50 plus tax per occupant, per night, above 2 occupants."
- **ARIA** — https://aria.mgmresorts.com/en/terms-and-conditions.html
  - "A daily resort fee of $55.00 plus applicable tax will be applied to all reservations." (the old $50-vs-$55 marketing conflict resolves in favour of the terms page, as captured)
  - Cancellation: "less than 72 hours … forfeiture of the first night's deposit … $165 mid-week or $200 weekend (i.e., Friday, Saturday or Sunday night)" — note ARIA counts Sunday in "weekend"; Bellagio's page says "Friday or Saturday night". Both as captured.

## Verdict summary

- Every committed value compared today: **unchanged**.
- New dated rate-log lines: 4 (Venetian ×2 re-read endpoints, TI offer, Wynn player-rate channel).
- New flag: F39 (Wynn page self-contradiction). Re-check notes appended: F1, F4, F19, F24, F25, F38.
- Entry-rule verdict unchanged: **0 events confirmed single-entry**; "unverified" labels stay wherever the sheet is silent. The printed bagging restriction is now surfaced in the structured re-entry field (multi-flight rows).
- Booking engines remain JS-only: no dated checkout totals; F4 stands.
