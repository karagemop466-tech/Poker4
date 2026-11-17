# -*- coding: utf-8 -*-
"""Hotels near the Las Vegas Strip poker venues — verified fields + dated rate log.
Values marked verified were read from official property pages on 2026-11-17.
Walk minutes were read from Google Maps walking directions (official addresses)
on 2026-11-17; each pair carries its own directions URL.

Tax: Clark County room tax 13.38% ("Daily rates do not include the applicable
Clark County Room Tax of 13.38%" — Venetian hotel terms, retrieved 2026-11-17).
True cost per night = (nightly rate + resort fee) x 1.1338, plus parking if used.
"""

RETRIEVED = "2026-11-17"
TAX = 0.1338
TAX_SOURCE = "https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html"

VEN_RESORT_FEE = "https://www.venetianlasvegas.com/resort/resort-fee.html"
VEN_TERMS = "https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html"
VEN_POKER_RATES = "https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html"
VEN_BOOK = "https://www.venetianlasvegas.com/booking?adults[]={adults}&arrival_date={in}&children[]=0&departure_date={out}&view=calendar"
WYNN_POKER = "https://www.wynnlasvegas.com/casino/poker"

def gmaps(origin, destination):
    return ("https://www.google.com/maps/dir/?api=1&origin=" + origin +
            "&destination=" + destination + "&travelmode=walking")

VEN_ADDR = "The+Venetian+Resort,+3355+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109"
WYNN_ADDR = "Wynn+Las+Vegas,+3131+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109"

# walk matrix: hotel -> (venue, minutes, miles, best-route note, directions URL, retrieved)
WALKS = [
    ("The Venetian / The Palazzo", "Venetian", None, None,
     "Poker room is inside the resort (Palazzo Level 2) — official directions from both resort lobbies.",
     "https://www.venetianlasvegas.com/resort/casino/poker.html", True),
    ("Wynn Las Vegas", "Venetian", 13, "0.6 mi",
     "Best via Wynn Main Gate Dr (13 min); via Las Vegas Blvd S 14 min; via Sands Ave 16 min.",
     gmaps(WYNN_ADDR, VEN_ADDR), True),
    ("Bellagio", "Venetian", 21, "0.9 mi",
     "Best via Las Vegas Blvd S (21 min); via Bellagio Dr 24 min.",
     gmaps("Bellagio,+3600+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", VEN_ADDR), True),
    ("ARIA", "Venetian", 31, "1.4 mi",
     "Best via Las Vegas Blvd S (31 min) — EXCEEDS the 30-minute limit; via Cosmopolitan Service Rd 32 min.",
     gmaps("Aria+Resort+%26+Casino,+3730+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", VEN_ADDR), True),
    ("Caesars Palace", "Venetian", 12, "0.5 mi",
     "Best via Las Vegas Blvd S (12 min); alternate 12 min.",
     gmaps("Caesars+Palace,+3570+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", VEN_ADDR), True),
    ("Treasure Island", "Venetian", 6, "0.2 mi",
     "Best via Las Vegas Blvd S (6 min); alternate 6 min via N Siegfried And Roy Dr.",
     gmaps("Treasure+Island+Las+Vegas,+3300+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", VEN_ADDR), True),
    ("Harrah's Las Vegas", "Venetian", 6, "0.3 mi",
     "Best via Las Vegas Blvd S (6 min).",
     gmaps("Harrah%27s+Las+Vegas,+3475+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", VEN_ADDR), True),
    ("Horseshoe Las Vegas", "Venetian", 16, "0.7 mi",
     "Best via Linq Ln (16 min); via Krueger Dr 16 min; via Las Vegas Blvd S 17 min.",
     gmaps("Horseshoe+Las+Vegas,+3645+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", VEN_ADDR), True),
    ("The Venetian / The Palazzo", "Wynn", 13, "0.6 mi",
     "Best via Wynn Main Gate Dr (13 min); via Las Vegas Blvd S 14 min.",
     gmaps(VEN_ADDR, WYNN_ADDR), True),
    ("Wynn Las Vegas", "Wynn", None, None,
     "Poker room is inside the resort (Encore at Wynn Las Vegas) — official poker page.",
     WYNN_POKER, True),
    # Cross-property hotel->Wynn routes rechecked on Google Maps 2026-11-17.
    ("Bellagio", "Wynn", 32, "1.4 mi", "Best via Las Vegas Blvd S (32 min); alternate via Las Vegas Blvd Overpass (33 min) or Bellagio Dr (36 min); over 30-minute limit.", gmaps("Bellagio,+3600+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", WYNN_ADDR), True),
    ("ARIA", "Wynn", 42, "1.9 mi", "Best via Las Vegas Blvd S (42 min); over 30-minute limit.", gmaps("Aria+Resort+%26+Casino,+3730+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", WYNN_ADDR), True),
    ("Caesars Palace", "Wynn", 23, "1.0 mi", "Best via Las Vegas Blvd S (23 min); alternate via Caesars Palace Dr (24 min).", gmaps("Caesars+Palace,+3570+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", WYNN_ADDR), True),
    ("Treasure Island", "Wynn", 11, "0.5 mi", "Best via Las Vegas Blvd S (11 min); alternate via Wynn Main Gate Dr (13 min).", gmaps("Treasure+Island+Las+Vegas,+3300+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", WYNN_ADDR), True),
    ("Harrah's Las Vegas", "Wynn", 18, "0.8 mi", "Best via Las Vegas Blvd S (18 min); alternate via Wynn Main Gate Dr (18 min).", gmaps("Harrah%27s+Las+Vegas,+3475+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", WYNN_ADDR), True),
    ("Horseshoe Las Vegas", "Wynn", 29, "1.3 mi", "Best via Las Vegas Blvd S (29 min); alternate via E Flamingo Rd (29 min), at the 30-minute limit.", gmaps("Horseshoe+Las+Vegas,+3645+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109", WYNN_ADDR), True),
]

HOTELS = [
    dict(name="The Venetian / The Palazzo", quality="Luxury (5-star resort)",
         address="3355 Las Vegas Blvd S, Las Vegas, NV 89109",
         resort_fee=55.0, resort_fee_note="$55 plus tax per night (official resort-fee page)",
         resort_fee_src=VEN_RESORT_FEE,
         parking="Hotel guests $20/day self-parking; valet $40/day; Venetian Rewards Sapphire+ free self-parking; NV residents 3 hrs free",
         parking_src=VEN_TERMS,
         cancellation="Deposit (suite + fee + tax) billed at booking; prepaid offers non-cancellable/non-refundable; early departure $100 + tax; check-out 11:00 AM",
         cancellation_src=VEN_TERMS,
         rate_log=[
             dict(label="Poker suite rate — starting rate (CONDITIONAL)", rate=119.0,
                  rate_note="'These rates will start as low as $119 and $209 and can be higher' — not a date-specific quote; requires 6 hrs live cash play or a $300+ tournament buy-in per night (code EPOKR25), single/double occupancy, subject to availability",
                  rate_src=VEN_POKER_RATES, retrieved=RETRIEVED, dated_quote=False),
             dict(label="Poker suite rate — alternate starting rate (CONDITIONAL)", rate=209.0,
                  rate_note="Same official page, second starting tier; not a date-specific quote",
                  rate_src=VEN_POKER_RATES, retrieved=RETRIEVED, dated_quote=False),
         ],
         booking_url=VEN_BOOK, booking_note="Official booking engine accepts arrival/departure dates in the URL; per-date links generated on the Hotels page.",
         notes="Best verified data quality: fee, tax, parking, cancellation and conditional poker rates all on official pages. TRUE cost examples (conditional): ($119+$55)x1.1338 = $197.28/night; ($209+$55)x1.1338 = $299.32/night."),
    dict(name="Wynn Las Vegas", quality="Luxury (5-star resort)",
         address="3131 Las Vegas Blvd S, Las Vegas, NV 89109",
         resort_fee=55.0, resort_fee_note="$55 + tax per night for bookings on or after Jan 15, 2025 (official terms page, per prior session's capture 2026-11-16)",
         resort_fee_src="https://www.wynnlasvegas.com/terms-and-conditions/850257",
         parking="", parking_src="",
         cancellation="", cancellation_src="",
         rate_log=[],
         booking_url="https://www.wynnlasvegas.com/book",
         booking_note="No dated quote captured; official booking link only.",
         notes="Wynn daily/WPT tournament terms verified 2026-11-17. Parking/cancellation terms not captured — flagged."),
    dict(name="Bellagio", quality="Luxury (5-star resort)",
         address="3600 Las Vegas Blvd S, Las Vegas, NV 89109",
         resort_fee=None, resort_fee_note="Not confirmed on an official page (prior sessions' fetch 404'd) — UNVERIFIED",
         resort_fee_src="https://bellagio.mgmresorts.com/en/casino/poker.html",
         parking="", parking_src="",
         cancellation="", cancellation_src="",
         rate_log=[],
         booking_url="https://www.bellagio.mgmresorts.com/en/booking.html",
         booking_note="No dated quote captured.",
         notes="Bellagio daily schedule has a $1,000 vs $1,100 buy-in conflict on official sources (flagged)."),
    dict(name="Caesars Palace", quality="Luxury (5-star resort)",
         address="3570 Las Vegas Blvd S, Las Vegas, NV 89109",
         resort_fee=None, resort_fee_note="Official page is marketing copy with no amount; third-party figures conflict ($49.95 vs $54.95) — UNVERIFIED",
         resort_fee_src="https://www.caesars.com/caesars-palace",
         parking="", parking_src="",
         cancellation="", cancellation_src="",
         rate_log=[],
         booking_url="https://www.caesars.com/caesars-palace",
         booking_note="No dated quote captured.",
         notes=""),
    dict(name="Treasure Island", quality="Mid-upper (4-star)",
         address="3300 Las Vegas Blvd S, Las Vegas, NV 89109",
         resort_fee=49.95, resort_fee_note="$49.95 + tax per night (official page); optional only for listed qualifying bookings",
         resort_fee_src="https://treasureisland.com/hotel/deluxe-rooms",
         parking="", parking_src="",
         cancellation="", cancellation_src="",
         rate_log=[],
         booking_url="https://treasureisland.com/hotel",
         booking_note="No dated quote captured.",
         notes="Official TI offer terms also establish 13.38% Clark County room tax (prior session, 2026-11-16)."),
    dict(name="Harrah's Las Vegas", quality="Mid (3.5-star)",
         address="3475 Las Vegas Blvd S, Las Vegas, NV 89109",
         resort_fee=None, resort_fee_note="Not confirmed on an official page — UNVERIFIED",
         resort_fee_src="https://www.caesars.com/harrahs-las-vegas",
         parking="", parking_src="",
         cancellation="", cancellation_src="",
         rate_log=[],
         booking_url="https://www.caesars.com/harrahs-las-vegas",
         booking_note="No dated quote captured.", notes=""),
    dict(name="Horseshoe Las Vegas", quality="Mid (3-star)",
         address="3645 Las Vegas Blvd S, Las Vegas, NV 89109",
         resort_fee=None, resort_fee_note="Not confirmed on an official page — UNVERIFIED",
         resort_fee_src="https://www.caesars.com/horseshoe-las-vegas",
         parking="", parking_src="",
         cancellation="", cancellation_src="",
         rate_log=[],
         booking_url="https://www.caesars.com/horseshoe-las-vegas",
         booking_note="No dated quote captured.", notes=""),
    dict(name="ARIA", quality="Luxury (5-star resort)",
         address="3730 Las Vegas Blvd S, Las Vegas, NV 89109",
         resort_fee=None, resort_fee_note="Third-party sources conflict ($50 vs $55) — UNVERIFIED",
         resort_fee_src="https://aria.mgmresorts.com/en.html",
         parking="", parking_src="",
         cancellation="", cancellation_src="",
         rate_log=[],
         booking_url="https://aria.mgmresorts.com/en/booking.html",
         booking_note="No dated quote captured.",
         notes="Walk to Venetian measured 31 min — over the 30-minute limit."),
]
