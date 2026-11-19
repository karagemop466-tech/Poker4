#!/usr/bin/env python3
"""Apply the 2026-11-19 live re-verification round (arena/1257a37f-poker4) to data/poker4.json.

Everything added here was read live on 2026-11-19 from the official pages cited in each
entry. Nothing is inferred: rate-log additions record only what a page printed; flag and
question additions record only sentences that were actually on the page.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data" / "poker4.json"
d = json.loads(P.read_text(encoding="utf-8"))
R = "2026-11-19"

hotels = {h["id"]: h for h in d["hotels"]}

# ---- R2: dated rate-log additions (append-only; never overwrite a logged value) ----
hotels["venetian"]["rate_log"] += [
    {
        "observed_on": R,
        "label": "Advertised poker rate, starting endpoint A — re-read 2026-11-19",
        "amount_usd": 119,
        "qualifier": ("'as low as' starting endpoint re-read 2026-11-19 from the official poker "
                      "suite-rate page; unchanged since 2026-11-16. Still an advertised starting "
                      "point for a Luxury King Suite at The Venetian or The Palazzo under code "
                      "EPOKR25, subject to qualifying poker play (six hours cash or a $300+ "
                      "tournament buy-in per night) and availability; not a dated quote."),
        "source": "https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html",
        "quote_status": "advertised starting point — not a dated quote",
    },
    {
        "observed_on": R,
        "label": "Advertised poker rate, starting endpoint B — re-read 2026-11-19",
        "amount_usd": 209,
        "qualifier": ("second 'as low as' endpoint on the same official page, re-read 2026-11-19; "
                      "unchanged since 2026-11-16. Same conditions as endpoint A. The $55 per "
                      "night resort fee is stated on the same page."),
        "source": "https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html",
        "quote_status": "advertised starting point — not a dated quote",
    },
]
hotels["ti"]["rate_log"] += [
    {
        "observed_on": R,
        "label": "Official TV Ad Special offer price (no resort fee under this offer)",
        "amount_usd": 69,
        "qualifier": ("'$69* NIGHT + NO RESORT FEE' offer printed on the official Deluxe Rooms page "
                      "(read 2026-11-19, same page that prints the $49.95 + tax mandatory resort fee). "
                      "Printed conditions: resort fees are optional only for My TI Guestbook members "
                      "booking the exclusive TV Ad Special offer, or qualified Treasury Players Club "
                      "casino members; bookings go to all.accor.com. Asterisked price — not a dated "
                      "quote for a chosen stay, and the page warns fee price, tax and amenities can "
                      "change without notice."),
        "source": "https://treasureisland.com/hotel/deluxe-rooms",
        "quote_status": "advertised offer price — conditions apply; not a dated quote",
    },
]
hotels["wynn"]["rate_log"] += [
    {
        "observed_on": R,
        "label": "Poker player-rate channel (no rate printed)",
        "amount_usd": None,
        "qualifier": ("official poker page FAQ (read 2026-11-19): 'Are preferred poker room rates "
                      "available? Yes, please contact us at poker.reservations@wynnlasvegas.com for "
                      "assistance.' The page prints no amount; a rate is quoted per stay by the room. "
                      "The same page's 'Reserve your stay' links for the WPT series use the same "
                      "poker.reservations mailbox."),
        "source": "https://wynnlasvegas.com/casino/poker",
        "quote_status": "channel only — no published rate",
    },
]

# ---- flag re-check notes + one new flag ----
flags = {f["id"]: f for f in d["flags"]}
flags["F1"]["detail"] += (
    " Re-checked 2026-11-19 (arena/1257a37f-poker4): structure sheets 21 ($2,200 PokerAtlas "
    "Championship, Event 47) and 12 ($800, Event 26) re-read live from the official PDFs — fee "
    "splits ($225/$1,975 and $110/$690), chips, level length and the Day-2 bagging clause match "
    "the audit exactly; still no entry-count, re-entry or add-on clause on either sheet. Verdict "
    "unchanged: NOT CONFIRMED. The printed clause 'Any player who bags chips for Day 2 may not "
    "play a subsequent flight' is now surfaced in the re-entry field of the rows built from those "
    "sheets — a printed restriction on subsequent flights after bagging, not a single-entry grant."
)
flags["F4"]["detail"] += (
    " Re-attempted 2026-11-19 (arena/1257a37f-poker4): the Venetian official booking endpoint with "
    "fixed dates 2026-12-10 → 2026-12-15 (2 adults) returns only the booking shell — rates render "
    "in JavaScript and no checkout total is retrievable by static fetch. Wynn, Caesars, MGM "
    "(Bellagio/ARIA) and TI route to interactive booking engines the same way (TI hands off to "
    "all.accor.com). Dated quotes therefore stay blank by policy. What the same day's reads did "
    "produce is logged in the dated rate log instead: TI's '$69 night + no resort fee' offer "
    "(conditions printed) and the Venetian poker-rate endpoints re-read unchanged."
)
flags["F19"]["detail"] += (
    " Re-read 2026-11-19 (arena/1257a37f-poker4) on offer terms 850257: 'A daily resort fee of $55 "
    "plus tax will be added to your room account for each room night' for resort rooms and, in a "
    "separate Tower Suites section, the same $55 plus tax. The offer's own cancellation terms are "
    "stricter than DK26WLV2's (full deposit at booking; non-cancellable, non-refundable) — a "
    "reminder that Wynn prints deposit/cancellation terms only inside offer terms; no general Wynn "
    "cancellation policy has been captured on any official page. Verdict on the fee unchanged."
)
flags["F24"]["detail"] += (
    " Re-read 2026-11-19 (arena/1257a37f-poker4): the live page now prints an FAQ answer — "
    "'With the exception of during a published tournament series, such as the Wynn Classic, daily "
    "tournaments run each day and feature $95,000 per week in guaranteed prize pools' — which "
    "conflicts both with the same page's '$200,000 in guaranteed prize pools weekly' and with the "
    "structures PDF's 'Monday-Thursday … may be suspended'. See F39."
)
flags["F25"]["detail"] += (
    " Re-read 2026-11-19 (arena/1257a37f-poker4): both sentences unchanged — the explore article "
    "still prints 'Every event carries a $100 buy-in, starts you with 20,000 chips, and features a "
    "$1,000 guaranteed prize pool … a $50 add-on at the first break gives you an extra 15,000 "
    "chips', and the 2026 flyer still prints $160 at 2 p.m. and 9 p.m. The article also states "
    "'Most sessions finish in four to six hours' — cited on Q4 as the only official duration "
    "statement found for these slates. Verdict unchanged: rows follow the flyer, conflict stands."
)
flags["F38"]["detail"] += (
    " Re-read 2026-11-19 (arena/1257a37f-poker4): the live page links the same two daily PDFs at "
    "the same CDN asset versions (v1752011166 poster / v1752011191 structures); neither PDF prints "
    "a revision date. Verdict unchanged."
)
d["flags"].append({
    "id": "F39",
    "severity": "conflicting-official-values",
    "item": "Wynn's own poker page contradicts itself: weekly guarantee totals and which days the dailies run",
    "detail": (
        "Read live 2026-11-19 from https://wynnlasvegas.com/casino/poker. (1) Weekly guarantee: the "
        "daily section says the twice-daily slate offers 'a total of $200,000 in guaranteed prize "
        "pools weekly' — which matches the poster's arithmetic (Mon–Thu $10K + Fri $40K rebuy + "
        "Sat $25K + Sun $25K + nightly $10K × 7 = $200K) — while the FAQ on the same page says the "
        "dailies 'feature $95,000 per week in guaranteed prize pools'. (2) Days run: the FAQ says "
        "'daily tournaments run each day'; the official structures PDF says the noon event 'will be "
        "offered Monday-Thursday and may be suspended'; the daily section says the schedule 'will be "
        "suspended during each Wynn Signature, Wynn Millions, and Classic tournament series'. Three "
        "inconsistent statements on one official page. Policy: the rows follow the poster PDF (the "
        "schedule document of record) and show its arithmetic only; the FAQ figures are not used as "
        "values. Whether the dailies run at all during the WPT World Championship (2026-11-27 – "
        "2026-12-21) remains unestablished (F24)."
    ),
    "sources": [
        "https://wynnlasvegas.com/casino/poker",
        "https://cdn.wynnresorts.com/image/upload/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf",
        "https://cdn.wynnresorts.com/image/upload/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf",
    ],
})

# ---- Q4: the only official duration statement found, dated ----
q4 = next(q for q in d["questions"] if q["id"] == "Q4")
q4["we_have"] += (
    " Added 2026-11-19 (arena/1257a37f-poker4): the Caesars official explore article (caesars.com, "
    "article dated July 17, 2026) states 'Most sessions finish in four to six hours' — the only "
    "official generic duration statement found for the Caesars Palace / Horseshoe dailies. It is a "
    "marketing sentence about sessions in general, not a printed per-event finish time, so it "
    "supports the overlap check as a plausible-duration citation only."
)
q4["sources"].append(
    "https://www.caesars.com/las-vegas/explore/casino/poker-tournaments-las-vegas-strip")

# ---- S13: window-extension decision ----
d["suggestions"].append({
    "id": "S13",
    "title": "Decide whether to extend the data window to the Wynn Signature Series (Jan 11–24, 2027)",
    "problem": (
        "The dashboard covers 2026-11-16 → 2026-12-23 (Venetian DSE IV + WPT World Championship). "
        "Wynn's official poker page (read 2026-11-19) announces the Wynn Signature Series for "
        "January 11–24, 2027, and links official schedule and structure PDFs for it "
        "(Wynn_Signature_Series_Schedule.pdf, Wynn_Signature_Series_Structures.pdf). The Wynn daily "
        "slate is suspended during that series, so January planning needs its rows, not the dailies."
    ),
    "proposal": (
        "Extend the snapshot window to 2027-01-24, add the two Signature Series PDFs to the "
        "tracked-source registry so the scheduled re-check monitors them, ingest their rows with the "
        "same per-sheet verification, and widen the date filter. Alternative: keep the window fixed "
        "and publish the series as a pointer note on the Wynn venue page until the sheets settle."
    ),
    "impact": "A January trip becomes plannable in the same tool; the alternative keeps the current window's verification guarantees intact.",
    "effort": "medium — two new tracked sources, one parser run, window constants and the date-filter bounds",
    "decision_needed": "Extend the window through Jan 24, 2027, or keep Nov–Dec 2026 and link the series as a note?",
    "status": "awaiting your choice",
})

P.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("poker4.json updated:",
      "rate-log lines added: 4 (venetian 2, ti 1, wynn 1); flags: +F39; Q4 extended; +S13")
