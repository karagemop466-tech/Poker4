# Live-fetch excerpts — arena/61daf94a-poker4, 2026-11-19

Method caveat: reads were made through the session page fetcher (value-level
comparison). Byte-hash monitoring remains the scheduled CI job's role
(`.github/workflows/url-check.yml` → `tools/sync_official_sources.py`).
`data/url-checks.json` and `data/change-log.json` were deliberately not
hand-edited; per-value results are in
`61daf94a_source_recheck_2026-11-19.tsv` (31 sources).

Verdict: every compared committed value is unchanged, except two curation
gaps closed below (Encore fee/parking, TI parking) whose evidence was
already committed in `data/hotel-facts.json` and was re-read live today.

## 1. Encore — resort fee $55 + tax (newly confirmed)

Source: https://www.wynnlasvegas.com/terms-and-conditions/850070
(read live 2026-11-19, chunks 0–1).

Verbatim (resort fee section):

> "A daily resort fee of $55 plus tax will be added to your room account for
> each complimentary (if applicable) and purchased room night ..."

> "This resort fee is only applicable to reservations for the following room
> types: Wynn Resort King, Wynn Resort Two Queens, Wynn Panoramic View King,
> Wynn Panoramic View Two Queens, Wynn Panoramic Corner King, **Encore Resort
> King, Encore Resort Two Queens, Encore Panoramic View King, Encore Panoramic
> View Two Queens**."

Tower Suites section (same page):

> "A daily resort fee of $55 plus tax will be added to your room account ..."

> "The Tower Suite Resort Fee is only applicable to reservations for the
> following room types: Wynn Tower Suite King, ... **Encore Tower Suite King,
> Encore Tower Suite Two Queens, Encore Tower Suite Parlor, and Encore Tower
> Suite Salon**."

Committed evidence: `data/hotel-facts.json` → 850070 `resort_fee` facts
already contain both sentences (retrieved 2026-11-19T06:43:13Z). The curated
`data/poker4.json` Encore record still said "not confirmed" — a curation gap,
now closed. Encore true cost per night still cannot be computed: no dated
room rate is published (booking calendar only), so the blank stands.

## 2. Encore — parking (newly confirmed)

Same page, parking section:

> "Self parking at our resort is complimentary for all Wynn and Encore Resort
> and Tower Suite registered guests, subject to availability."

> "For non-registered guests, the daily parking fee is $25 per day, with the
> first three (3) hours free."

> "Valet parking is $40/day for up to 24 hours (no grace period)."

Corroborated by https://www.wynnlasvegas.com/about-us/parking (read live
2026-11-19): "complimentary parking for all Wynn and Encore Resort and Tower
Suite registered guests"; valet "$40 per day"; complimentary valet for Tower
Suites guests.

## 3. Treasure Island — free parking (newly confirmed)

Source A: https://treasureisland.com/hotel/deluxe-rooms (read live
2026-11-19), Resort Fee Amenities:

> "Always Free Valet Parking & Self Park Garage"

Source B: https://treasureisland.com/amenities/guest-services (read live
2026-11-19):

> "Always Free for Hotel & Casino Guests" (self-park garage)

> "Free (Gratuity Suggested) for Hotel & Casino Guests" (valet)

Committed evidence: `data/hotel-facts.json` → deluxe-rooms `parking` fact
already contains "Always Free Valet Parking & Self Park Garage". The curated
TI parking record still said "not printed" — now closed ($0 / $0).

## 4. What did NOT change (selected verbatim)

- Venetian suite rates: "rates will start as low as $119 and $209 ... There
  is a $55 resort fee per night stayed." Qualification: "six hours of active
  live cash gameplay or buy in to a $300 or higher tournament for each night
  stayed ... prior to 2 a.m. the last night stayed."
- Venetian structure sheet 10 (Event 1): "$60 of the $300 Buy-In is withheld
  for house fees (Rake + Staff). The prize pool consists of $240 of every
  $300 Buy In." Rule 8: "Any player who bags chips for Day 2 may not play a
  subsequent flight." No entry-count clause → single-entry still unverified.
- Venetian structure sheet 21 (Event 47): "$225 of the $2,200 Buy-In is
  withheld ... $1,975 of every $2,200 Buy In." Same rule 8; no entry-count
  clause.
- Wynn daily structures: Mon–Thu "$200 Entry Fee ... $26 for the Tournament
  fee, $12 for the poker staff service charge, and $162 for the Tournament
  prize pool"; Fri "Re-entry is NOT allowed. ... Unlimited $200 rebuys ...
  One (1) $100 addon ..."; Sat/Sun and nightly $160 with re-entries + add-on.
- Bellagio Saturday sheet: title "NLH $1100 BUY-IN" vs rule 7 "Of the $600
  Buy-in, $510 goes to the Prize Pool" (F16 unchanged); Day 2 "(9/13/26)".
- Caesars flyer: 10 AM $100 / 2 PM $160 / 6 PM $100 / 9 PM $160; "$50 add-on
  for 15,000 tournament chips"; "may re-enter ... upon elimination within the
  first break of play." Article still prints the blanket "$100 buy-in"
  (F25 unchanged) and "Most sessions finish in four to six hours."
- Venetian booking (`/book`): calendar shows "$XXX" placeholders with
  "*Pricing shown is best available suite and rate, includes daily resort
  fee, excludes taxes." No dated checkout total in a static fetch (F4
  stands). Caesars-owned hotel pages print no resort fee amount (F31
  stands); advertised "Rooms from $56" (Harrah's/LINQ/Flamingo) and "$139"
  (Caesars) are not used as rates without fee/tax.
- Walking minutes are 2026-11-17/18 Google Maps routing measurements
  (reproducible links in `data/walk-measurements.json`); official addresses
  re-confirmed (Venetian 3355 Las Vegas Blvd. South; TI 3300 Las Vegas Blvd
  S). Minutes were not re-measured this round (Maps is JS-only).

## 5. $0-parking render bug (fixed this round)

`scripts/integrate_data.py` used truthiness (`if pk.get("self_usd_per_day")`)
so a published $0 (Wynn self-parking, now also TI) rendered as "parking
unconfirmed" in the compact hotel tables. Fixed to explicit `is not None`
checks. The calculator (`app.js` `fillParking`) already handled $0 correctly
(`typeof v === "number"`).
