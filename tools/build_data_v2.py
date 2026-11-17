#!/usr/bin/env python3
"""Assemble the canonical data/v2/* JSON set for the root dashboard.

Run:  python3 tools/build_data_v2.py

Inputs
  - data/c07371e3/venetian_deepstack_iv.csv  (94 official-schedule rows, verified against the
    official Venetian DSE IV page by session c07371e3 on 2026-11-16)
  - the verified facts recorded in notes/structure_rules.md — every Venetian structure sheet
    (dse_nov_2026-structure_1..37.pdf), the Wynn daily-structures PDF, the WPT schedule and
    terms PDFs, the Bellagio Fri/Sat/Sun sheets and the Caesars Palace daily flyer were read
    in full on 2026-11-17 by session 0f6c627b (excerpts kept verbatim below).

Outputs  data/v2/{sources,events,hotels,walking,rate_log,monitor_status}.json

Policy: never infer. A field is filled only from an official source we read; otherwise it is
null and the row is flagged.  Every value carries source keys + a retrieval date.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "0f6c627b"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "monitor").mkdir(exist_ok=True)

TODAY = "2026-11-17"           # retrieval date for this pass
PRIOR = "2026-11-16"           # values carried from the previous verified pass
STRUCT_BASE = "https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/"

# ---------------------------------------------------------------- sources
SOURCES = {
    "V_PAGE": {"label": "Venetian DeepStack Extravaganza IV official series page (schedule)",
               "url": "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"},
    "V_SCHED": {"label": "Venetian DSE IV schedule PDF (official)",
                "url": "https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/dse-nov-2026-schedule.pdf"},
    "V_POKER": {"label": "Venetian Poker Room official page (room at The Palazzo, Level 2)",
                "url": "https://www.venetianlasvegas.com/resort/casino/poker.html"},
    "V_RATES": {"label": "Venetian 2026 Poker Suite Rates official page",
                "url": "https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html"},
    "V_RESORT": {"label": "Venetian Resort Fee official page",
                 "url": "https://www.venetianlasvegas.com/resort/resort-fee.html"},
    "V_TERMS": {"label": "Venetian Hotel Terms & Conditions (tax, parking, cancellation)",
                "url": "https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html"},
    "W_PAGE": {"label": "Wynn Las Vegas Poker Room official page",
               "url": "https://www.wynnlasvegas.com/casino/poker"},
    "W_DAILY": {"label": "Wynn Daily Tournament Structures + General Terms PDF (official)",
                "url": "https://cdn.wynnresorts.com/image/upload/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf"},
    "W_WPT": {"label": "Wynn WPT World Championship 2026 schedule PDF (official)",
              "url": "https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf"},
    "W_WPT_TC": {"label": "WPT World Championship General Terms + event structures PDF (official)",
                 "url": "https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf"},
    "W_TERMS": {"label": "Wynn Las Vegas Terms & Conditions (resort fee, parking, deposit)",
                "url": "https://www.wynnlasvegas.com/terms-and-conditions/850257"},
    "B_PAGE": {"label": "Bellagio Poker Room official page",
               "url": "https://bellagio.mgmresorts.com/en/casino/poker.html"},
    "B_FRI": {"label": "Bellagio Friday $600 NLH structure PDF (official)",
              "url": "https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt9cf95b0e60ec253e/6af491a3a9851d75c40be840/mgm-bellagio-poker-fridays-$600-nlh.pdf"},
    "B_SAT": {"label": "Bellagio Saturday NLH structure PDF (official; buy-in conflict inside)",
              "url": "https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt6d47974bf5a7d9b6/6af491a391a6e8e4230c9e07/mgm-bellagio-poker-saturdays-$1000-nlh.pdf"},
    "B_SUN": {"label": "Bellagio Sunday $400 H.O.R.S.E. structure PDF (official)",
              "url": "https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt07fcf1244a6da661/6af491a339e2b4f6b76a86ad/mgm-bellagio-poker-sundays-$400-horse.pdf"},
    "C_FLYER": {"label": "Caesars Palace Daily NLH tournament flyer PDF (official)",
                "url": "https://www.caesars.com/content/dam/empire/clv/casino/poker/tournament-schedule/clv-poker-daily-nlh-tournament-flyer-2026.pdf"},
    "C_PAGE": {"label": "Caesars Palace casino page (links the flyer)",
               "url": "https://www.caesars.com/caesars-palace/casino"},
    "TI_FEE": {"label": "Treasure Island resort-fee section (Tower Suite page, official)",
               "url": "https://treasureisland.com/hotel/tower-suite"},
    "GM": {"label": "Google Maps walking directions (mode=walking, retrieved per row)",
           "url": "https://www.google.com/maps"},
}
for n in range(1, 38):
    SOURCES[f"V_S{n}"] = {"label": f"Venetian DSE IV structure sheet #{n} (official PDF)",
                          "url": f"{STRUCT_BASE}dse_nov_2026-structure_{n}.pdf"}

# ------------------------------------------------- Venetian structure facts
# key = structure sheet number.  Every line below is copied from the sheet read on 2026-11-17.
# entry-rule lines: NONE of the 37 sheets states a re-entry / rebuy / add-on / single-entry policy.
VEN_STRUCT = {
    1: dict(buy=200, fee=40, pool=160, chips=25000, lvl=30, reg="8 levels + break (9:40 PM)", pays=12.5,
            bounty=50, start="5:10 PM",
            fee_ex="$40 of the $200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $160 of every $200 Buy In.",
            extra="Guarantee $8,000 = prize pool + total bounties. $50 bounty per elimination."),
    2: dict(buy=400, fee=70, pool=330, chips=40000, lvl=40, reg="9 levels + break (5:55 PM)", pays=None,
            start="11:10 AM", flights=True,
            fee_ex="$70 of the $400 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $330 of every $400 Buy In.",
            extra="Multi-flight (1A,1B) + Day 2 11:00 AM. Rule 08: 'Any player who bags chips for Day 2 may not play a subsequent flight.'"),
    3: dict(buy=400, fee=70, pool=330, chips=40000, lvl=40, reg="9 levels + break (5:55 PM)", pays=None,
            start="11:10 AM", flights=True,
            fee_ex="$70 of the $400 Buy-In ... $330 of every $400 Buy In.",
            extra="Multi-flight (1A,1B,1C) + Day 2. Bag rule 08 same as sheet 2."),
    4: dict(buy=600, fee=95, pool=505, chips=40000, lvl=40, reg="9 levels + break (5:55 PM)", pays=None,
            start="11:10 AM", flights=True,
            fee_ex="$95 of the $600 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $505 of every $600 Buy In. On Day 1A only, players who register before the start of the event (11:10 a.m.), will receive a $20 discount on house fees for a total buy in of $580 instead of $600.",
            extra="Multi-flight (1A,1B,1C) + Day 2. $150,000 guarantee. Bag rule 08."),
    5: dict(buy=300, fee=58, pool=242, chips=40000, lvl=30, reg="10 levels + break (~4:55 PM)", pays=12.5,
            start="11:10 AM",
            fee_ex="$58 of the $300 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $242 of every $300 Buy In.",
            extra="$10,000 guarantee."),
    6: dict(buy=400, fee=65, pool=335, chips=40000, lvl=30, reg="10 levels + break (~4:55 PM)", pays=12.5,
            start="11:10 AM",
            fee_ex="$65 of the $400 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $335 of every $400 Buy In.",
            extra="$15,000 guarantee."),
    7: dict(buy=600, fee=90, pool=510, chips=40000, lvl=30, reg="10 levels + break (~4:55 PM)", pays=12.5,
            start="11:10 AM",
            fee_ex="$90 of the $600 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $510 of every $600 Buy In.",
            extra="$30,000 guarantee (#14, #63); $40,000 guarantee (#28)."),
    8: dict(buy=200, fee=40, pool=160, chips=25000, lvl=30, reg="8 levels + break (9:40 PM)", pays=12.5,
            bounty=50, start="5:10 PM",
            fee_ex="$40 of the $200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $160 of every $200 Buy In.",
            extra="Valuetown Bounty: PokerAtlas PRO $20 rake discount on initial buy-in only; rule 07 says 'All subsequent buy in's after the initial buy in will be $200.' Guarantee $20,000 = prize pool + total bounties."),
    9: dict(buy=300, fee=60, pool=240, chips=30000, lvl=30, reg="6 levels + break (~8:40 PM)", pays=None,
            start="5:10 PM", flights=True,
            fee_ex="$60 of the $300 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $240 of every $300 Buy In.",
            extra="Event 1 flights B+D; Day 2 12:00 PM. Bag rule 08."),
    10: dict(buy=300, fee=60, pool=240, chips=30000, lvl=40, reg="6 levels + break (~3:40 PM)", pays=None,
             start="11:10 AM", flights=True,
             fee_ex="$60 of the $300 Buy-In ... $240 of every $300 Buy In.",
             extra="Event 1 flights A+C; Day 2 12:00 PM. Bag rule 08."),
    11: dict(buy=600, fee=90, pool=510, chips=40000, lvl=30, reg="10 levels + break (4:55 PM)", pays=12.5,
             start="11:10 AM", bounty=200,
             fee_ex="$90 of the $600 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $510 of every $600 Buy In.",
             extra="$200 bounty per elimination, $500 after the money; winner keeps own bounty. Guarantees include bounties: #16 $30,000; #30 $40,000; #54 $50,000."),
    12: dict(buy=800, fee=110, pool=690, chips=40000, lvl=40, reg="6 levels + break (~3:40 PM)", pays=None,
             start="11:10 AM", flights=True,
             fee_ex="$110 of the $800 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $690 of every $800 Buy In.",
             extra="Event 26 flights A,C,E; Day 2 12:00 PM; $500,000 guarantee. Bag rule 08."),
    13: dict(buy=800, fee=110, pool=690, chips=40000, lvl=30, reg="6 levels + break (~8:40 PM)", pays=None,
             start="5:10 PM", flights=True,
             fee_ex="$110 of the $800 Buy-In ... $690 of every $800 Buy In.",
             extra="Event 26 flights B,D; Day 2 12:00 PM. Bag rule 08."),
    14: dict(buy=800, fee=110, pool=690, chips=40000, lvl=20, reg="6 levels + break (~7:25 PM)", pays=None,
             start="5:10 PM", flights=True,
             fee_ex="$110 of the $800 Buy-In ... $690 of every $800 Buy In.",
             extra="Event 26 flight F (Turbo); Day 2 12:00 PM. Bag rule 08."),
    15: dict(buy=300, fee=50, pool=250, chips=25000, lvl=30, reg="8 levels + break (9:40 PM)", pays=12.5,
             bounty=100, start="5:10 PM",
             fee_ex="$50 of the $300 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $250 of every $300 Buy In.",
             extra="$100 bounty per elimination. Guarantee $15,000 = prize pool + total bounties."),
    16: dict(buy=800, fee=100, pool=700, chips=40000, lvl=30, reg="10 levels + break (4:55 PM)", pays=12.5,
             bounty=200, start="11:10 AM",
             fee_ex="$100 of the $800 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $700 of every $800 Buy In.",
             extra="$200 bounty, $500 after the money. Guarantee $75,000 = prize pool + total bounties."),
    17: dict(buy=600, fee=90, pool=510, chips=40000, lvl=30, reg="10 levels + break (~3:55 PM)", pays=15.0,
             start="10:10 AM",
             fee_ex="$90 of the $600 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $510 of every $600 Buy In.",
             extra="Seniors 50+; pays 15% of field; $40,000 guarantee."),
    18: dict(buy=200, fee=35, pool=165, chips=30000, lvl="20/15", reg="6 levels + break (~12:25 PM)", pays=12.5,
             start="10:10 AM",
             fee_ex="$35 of the $200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $165 of every $200 Buy In.",
             extra="RaceDay Stack (20/15-minute levels) — 'Race to finish before the Race'; no guarantee listed."),
    19: dict(buy=100, fee=20, pool=80, chips=20000, lvl=20, reg="6 levels + break (~6:25 PM)", pays=None,
             start="4:10 PM", satellite=True,
             fee_ex="$20 of the $100 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $80 of every $100 Buy In.",
             extra="LIPS Ladies Milestone Satellite — awards 2 seats into $800 LIPS Event #39; milestone 200,000 chips; female players only."),
    20: dict(buy=1100, fee=140, pool=960, chips=40000, lvl=40, reg="9 levels + break (~4:55 PM)", pays=None,
             start="10:10 AM", flights=True,
             fee_ex="$140 of the $1,100 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $960 of every $1,100 Buy In.",
             extra="Seniors 50+ multi-flight (1A,1B), Day 2 10:00 AM; flights play to ~15%; $300,000 guarantee. Bag rule 08."),
    21: dict(buy=2200, fee=225, pool=1975, chips=40000, lvl=40, reg="9 levels + break (~4:55 PM)", pays=None,
             start="10:10 AM", flights=True,
             fee_ex="$225 of the $2,200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $1,975 of every $2,200 Buy In.",
             extra="PokerAtlas Championship #47 Day 1A; Day 2 1:00 PM; Day 3 11:00 AM (PokerGO final table); $1,000,000 guarantee. Bag rule 08."),
    22: dict(buy=300, fee=58, pool=242, chips=30000, lvl=30, reg="8 levels + break (~4:40 PM)", pays=12.5,
             start="12:10 PM",
             fee_ex="$58 of the $300 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $242 of every $300 Buy In.",
             extra="PLO Double Board Bomb Pot; 8-handed; $10,000 guarantee."),
    23: dict(buy=600, fee=90, pool=510, chips=30000, lvl=30, reg="8 levels + break (~4:40 PM)", pays=12.5,
             start="12:10 PM",
             fee_ex="$90 of the $600 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $510 of every $600 Buy In.",
             extra="PLO Double Board Bomb Pot; 8-handed; $25,000 guarantee."),
    24: dict(buy=260, fee=40, pool=220, chips=20000, lvl=20, reg="6 levels + break (~6:25 PM)", pays=None,
             start="4:10 PM", satellite=True,
             fee_ex="$40 of the $260 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $220 of every $260 Buy In.",
             extra="Milestone Satellite to $2,200 Event #47 — awards 2 seats; milestone 200,000 chips."),
    25: dict(buy=260, fee=35, pool=225, chips=20000, lvl=15, reg="6 levels", pays=None,
             start="varies", satellite=True,
             fee_ex="$35 of the $260 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $225 of every $260 Buy In.",
             extra="Milestone Turbo Satellite to Event #47 — awards 2 seats. Starts: #45 8:10 PM, #46 9:10 AM, #48 12:10 PM."),
    26: dict(buy=400, fee=60, pool=340, chips=30000, lvl=30, reg="8 levels + break (~4:40 PM)", pays=12.5,
             bounty=100, start="12:10 PM",
             fee_ex="$60 of the $400 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $340 of every $400 Buy In.",
             extra="PLO Bounty; 8-handed; $100 bounty; guarantee $15,000 = pool + total bounties."),
    27: dict(buy=600, fee=90, pool=510, chips=30000, lvl=30, reg="8 levels + break (~4:40 PM)", pays=12.5,
             bounty=200, start="12:10 PM",
             fee_ex="$90 of the $600 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $510 of every $600 Buy In.",
             extra="PLO Bounty; 8-handed; $200 bounty; guarantee $25,000 = pool + total bounties."),
    28: dict(buy=600, fee=90, pool=510, chips=30000, lvl=30, reg="8 levels + break (~4:40 PM)", pays=12.5,
             start="12:10 PM",
             fee_ex="$90 of the $600 Buy-In is withheld for house fees (Rake + Staff). Prize pool consists of $510 of every $600 Buy In.",
             extra="BIG O; 8-handed; $25,000 guarantee."),
    29: dict(buy=200, fee=40, pool=160, chips=30000, lvl=30, reg="8 levels + break (~3:40 PM)", pays=12.5,
             start="11:10 AM",
             fee_ex="$40 of the $200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $160 of every $200 Buy In.",
             extra="No guarantee listed."),
    30: dict(buy=200, fee=40, pool=160, chips=25000, lvl=30, reg="8 levels + break (9:40 PM)", pays=12.5,
             bounty=50, start="5:10 PM",
             fee_ex="$40 of the $200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $160 of every $200 Buy In.",
             extra="Progressive Knock-Out (PKO): start as $50 bounty, half of each knockout added to own bounty. Guarantee $8,000 = pool + bounty prize money."),
    31: dict(buy=600, fee=80, pool=510, chips=40000, lvl=30, reg="8 levels + break (~2:40 PM)", pays=12.5,
             start="10:10 AM",
             fee_ex="$80 of the $600 Buy-In is withheld for house fees (Rake + Staff). $10 of the $600 Buy In will be withheld as a flat fee for Vegas Connected, INC, DBA Ladies International Poker Series (LIPS). Prize pool consists of $510 of every $600 Buy In.",
             extra="LIPS Jingle Tag Team #35; teams Female/Female OR Female/Male; members alternate every level; $10,000 guarantee."),
    32: dict(buy=800, fee=90, pool=690, chips=40000, lvl=40, reg="9 levels + break (~4:55 PM)", pays=None,
             start="10:10 AM",
             fee_ex="$90 of the $800 Buy-In is withheld for house fees (Rake + Staff). $20 of the $800 Buy In will be withheld as a flat fee for Vegas Connected, INC, DBA LIPS. Prize pool consists of $690 of every $800 Buy In.",
             extra="LIPS Ladies #39 (2-Day, female only): Day 1 Dec 10 10:10 AM, Day 2 Dec 11 10:00 AM, PokerGO final table ~7:00 PM; $40,000 guarantee."),
    33: dict(buy=600, fee=80, pool=510, chips=40000, lvl=30, reg="10 levels + break (4:55 PM)", pays=12.5,
             bounty=200, start="11:10 AM",
             fee_ex="$80 of the $600 Buy-In is withheld for house fees (Rake + Staff). $10 of the $600 Buy In will be withheld as a flat fee for Vegas Connected, INC, DBA LIPS. Prize pool consists of $510 of every $600 Buy In.",
             extra="Kings & Queens Bounty #43 (open to all); $200 bounties; trophy to last King and last Queen; guarantee $30,000 = pool + bounties."),
    34: dict(buy=1100, fee=130, pool=970, chips=40000, lvl=30, reg="10 levels + break (4:55 PM)", pays=12.5,
             bounty=200, start="11:10 AM",
             fee_ex="$130 of the $1,100 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $970 of every $1,100 Buy In.",
             extra="PKO #52: start as $200 bounty, half of each knockout added to own bounty; guarantee $75,000 = pool + bounty prize money."),
    35: dict(buy=1100, fee=140, pool=960, chips=40000, lvl=40, reg="9 levels + break (~4:55 PM)", pays=None,
             start="10:10 AM", flights=True,
             fee_ex="$140 of the $1,100 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $960 of every $1,100 Buy In. On Day 1A, players who register before the start of the event (10:10 a.m.) will receive a forty ($40) discount on house fees for a total buy in of $1,060 instead of $1,100.",
             extra="Event 56 flights A,C,E; Day 2 11:00 AM; $500,000 guarantee. Bag rule 08."),
    36: dict(buy=1100, fee=140, pool=960, chips=40000, lvl=30, reg="9 levels + break (~11:10 PM)", pays=None,
             start="6:10 PM", flights=True,
             fee_ex="$140 of the $1,100 Buy-In ... $960 of every $1,100 Buy In. On Day 1B, players who register before the start of the event (6:10 PM.) will receive a forty ($40) discount ... $1,060 instead of $1,100.",
             extra="Event 56 flights B,D; Day 2 11:00 AM; $500,000 guarantee. Bag rule 08."),
    37: dict(buy=2200, fee=225, pool=1975, chips=40000, lvl=30, reg="9 levels + break (~11:10 PM)", pays=None,
             start="6:10 PM", flights=True,
             fee_ex="$225 of the $2,200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $1,975 of every $2,200 Buy In.",
             extra="Event #47 Day 1B; Day 2 1:00 PM; Day 3 11:00 AM; $1,000,000 guarantee. Bag rule 08."),
}
# Start-time overrides keyed by event number where the CSV flight label differs from sheet default
FLIGHT_START = {  # (event_no, csv time) -> sheet that matches
    ("1", "11:10 AM"): 10, ("1", "5:10 PM"): 9,
    ("7", "11:10 AM"): 2, ("7", "5:10 PM"): 2, ("7", "11:00 AM"): 2,
    ("19", "11:10 AM"): 3, ("19", "5:10 PM"): 3,
    ("26", "11:10 AM"): 12, ("26", "5:10 PM"): 13,
    ("47", "10:10 AM"): 21, ("47", "6:10 PM"): 37,
    ("49", "10:10 AM"): 20, ("49", "5:10 PM"): 20,
    ("56", "10:10 AM"): 35, ("56", "6:10 PM"): 36,
    ("59", "11:10 AM"): 4, ("59", "5:10 PM"): 4,
}

def vn_rules(sheet_no, extra_note=""):
    """Entry-rule field set for a Venetian event.  All 37 sheets are silent on entry policy."""
    return {
        "status": "unverified",
        "single_entry": {"value": "unverified", "excerpt": "Structure sheet states no entry limit; silence is not confirmation.",
                         "source": f"V_S{sheet_no}", "retrieved": TODAY},
        "reentry": {"value": "unverified", "excerpt": "No re-entry line in the sheet's numbered rules.",
                    "source": f"V_S{sheet_no}", "retrieved": TODAY},
        "addon": {"value": "unverified", "excerpt": "No add-on line in the sheet's numbered rules.",
                  "source": f"V_S{sheet_no}", "retrieved": TODAY},
        "fees": {"value": VEN_STRUCT[sheet_no]["fee_ex"], "excerpt": VEN_STRUCT[sheet_no]["fee_ex"],
                 "source": f"V_S{sheet_no}", "retrieved": TODAY},
        "note": extra_note,
    }

# --------------------------------------------------------------- events
events = []

# -- Venetian DSE IV: 94 official rows, enriched from the structure sheets
with open(ROOT / "data/c07371e3/venetian_deepstack_iv.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ev_no = row["event_no"]
        pdf = row["structure_pdf"]
        sheet_no = int(pdf.split("_")[-1].split(".")[0])
        st = VEN_STRUCT[sheet_no]
        # match flight-specific sheet when two sheets cover one event
        key = (ev_no, row["time"])
        if key in FLIGHT_START:
            sheet_no = FLIGHT_START[key]
            st = VEN_STRUCT[sheet_no]
            pdf = f"dse_nov_2026-structure_{sheet_no}.pdf"
        buy = int(row["buy_in_usd"]) if row["buy_in_usd"] else None
        gtd = int(row["guarantee_usd"]) if row["guarantee_usd"] else None
        kind = {"Tournament": "tournament", "Satellite": "satellite",
                "Continuation (not an entry)": "continuation"}[row["kind"]]
        if st.get("flights") and kind == "tournament":
            kind = "flight"
        if st.get("bounty") and kind == "tournament":
            kind = "bounty"
        if "PKO" in row["event_name"] or "Progressive" in row["event_name"]:
            kind = "bounty"
        ev = {
            "id": f"V-{ev_no}-{row['date']}-{row['time'].replace(' ', '')}",
            "venue": "venetian", "venue_name": "The Venetian (Poker Room — The Palazzo, Level 2)",
            "date": row["date"], "weekday": row["weekday"], "start_time": row["time"],
            "event_no": ev_no, "name": row["event_name"],
            "game": "PLO" if "Omaha" in row["event_name"] or "BIG O" in row["event_name"] else "NLH",
            "kind": kind,
            "buy_in": buy if kind != "continuation" else None,
            "guarantee": gtd,
            "bounty_amount": st.get("bounty"),
            "structure": {"sheet": pdf, "url": SOURCES[f"V_S{sheet_no}"]["url"],
                          "chips": st["chips"], "level_minutes": st["lvl"],
                          "reg_close": st["reg"], "pays_pct": st["pays"]},
            "fees": {"house_fee": st["fee"] if buy else None, "to_prize_pool": st["pool"] if buy else None,
                     "excerpt": st["fee_ex"], "source": f"V_S{sheet_no}", "retrieved": TODAY},
            "entry_rules": vn_rules(sheet_no, st.get("extra", "")),
            "last_checked": TODAY,
            "sources": ["V_PAGE", "V_SCHED", f"V_S{sheet_no}"],
            "notes": st.get("extra", ""),
        }
        if gtd and buy and kind not in ("satellite", "continuation"):
            ev["ratio_guarantee_per_buy_in"] = round(gtd / buy, 1)
        else:
            ev["ratio_guarantee_per_buy_in"] = None
        events.append(ev)

# -- Wynn daily tournaments (rules CONFIRMED in the official structures PDF, read 2026-11-17)
wynn_daily = [
    dict(id="W-D-200", name="Wynn Daily NLH $200 — $10,000 GTD", days="Monday–Thursday", time="12:00 PM",
         buy=200, gtd=10000, chips=25000, lvl="30 min", reg="start of level 9 (~4:30 PM)",
         reentry="allowed", addon="none",
         fee_split="$26 Tournament fee + $12 poker staff service charge + $162 prize pool",
         excerpt="The Tournament entry fee, as well as the re-entry fee, is $200 … Registration and re-entries will be available until the start of level 9 (approximately 4:30 p.m.)."),
    dict(id="W-D-240F", name="Wynn Friday NLH Rebuy & Add-on $240 — $40,000 GTD", days="Friday", time="12:00 PM",
         buy=240, gtd=40000, chips=25000, lvl="30 min", reg="start of level 9 (~4:30 PM)",
         reentry="not_allowed", addon="allowed",
         fee_split="$35 Tournament fee + $15 staff; $190 of each entry/rebuy to prize pool; rebuys $200 (=$190 pool+$5 fee+$5 staff); add-on $100 (=$90 pool+$5 fee+$5 staff)",
         excerpt="Re-entry is NOT allowed. … Unlimited $200 rebuys for 25,000 tournament chips are available any time a player is at 15,000 chips or less. One (1) $100 add-on for 15,000 tournament chips is available any time until the end of registration."),
    dict(id="W-D-200SS", name="Wynn Sat/Sun NLH $200 — $25,000 GTD", days="Saturday & Sunday", time="12:00 PM",
         buy=200, gtd=25000, chips=25000, lvl="30 min", reg="start of level 11 (~5:30 PM)",
         reentry="allowed", addon="allowed",
         fee_split="$26 Tournament fee + $12 staff + $162 prize pool; one $100 add-on for 25,000 chips",
         excerpt="Registration, re-entries, and one (1) add-on per entry will be available until the start of level 11 (approximately 5:30 p.m.)."),
    dict(id="W-D-160N", name="Wynn Nightly NLH $160 — $10,000 GTD", days="Monday–Sunday", time="6:00 PM",
         buy=160, gtd=10000, chips=25000, lvl="20 min", reg="start of level 9 (~9:00 PM)",
         reentry="allowed", addon="allowed",
         fee_split="$20 Tournament fee + $10 staff + $130 prize pool; one $100 add-on for 25,000 chips",
         excerpt="Registration, re-entries, and one (1) add-on per entry will be available until the start of level 9 (approximately 9:00 p.m.)."),
]
for d in wynn_daily:
    re_ex = d["excerpt"]
    events.append({
        "id": d["id"], "venue": "wynn", "venue_name": "Wynn Las Vegas (Poker Room in Encore)",
        "date": "weekly:" + d["days"], "weekday": d["days"], "start_time": d["time"],
        "event_no": None, "name": d["name"], "game": "NLH", "kind": "tournament",
        "buy_in": d["buy"], "guarantee": d["gtd"], "bounty_amount": None,
        "structure": {"sheet": "W_DAILY", "url": SOURCES["W_DAILY"]["url"], "chips": d["chips"],
                      "level_minutes": d["lvl"], "reg_close": d["reg"], "pays_pct": None},
        "fees": {"house_fee": None, "to_prize_pool": None, "excerpt": d["fee_split"],
                 "source": "W_DAILY", "retrieved": TODAY},
        "entry_rules": {
            "status": "confirmed",
            "single_entry": {"value": "no", "excerpt": re_ex, "source": "W_DAILY", "retrieved": TODAY},
            "reentry": {"value": d["reentry"], "excerpt": re_ex, "source": "W_DAILY", "retrieved": TODAY},
            "addon": {"value": d["addon"], "excerpt": re_ex, "source": "W_DAILY", "retrieved": TODAY},
            "fees": {"value": d["fee_split"], "excerpt": d["fee_split"], "source": "W_DAILY", "retrieved": TODAY},
            "note": "",
        },
        "ratio_guarantee_per_buy_in": round(d["gtd"] / d["buy"], 1),
        "last_checked": TODAY, "sources": ["W_PAGE", "W_DAILY"], "notes": d["excerpt"],
    })

# -- Wynn WPT World Championship (schedule PDF read in full 2026-11-17).  Event-level rows.
WPT_EXCERPT = ("Unlimited re-entry for each starting flight will be available until the start of level 9. "
               "A player who advances to Day 2 is prohibited from entering a subsequent starting flight.")
wpt = [
    dict(id="WPT-600", name="WPT NLH $600 — $400,000 GTD (6 flights)", dates="Nov 27–Nov 30", time="11 AM / 5 PM / 6 PM",
         buy=600, gtd=400000, chips=40000, lvl="30/40 min", fee="$510 prize pool + $65 Tournament fee + $25 staff"),
    dict(id="WPT-800", name="WPT NLH $800 — $1,000,000 GTD (6 flights)", dates="Nov 30–Dec 3", time="11 AM / 5 PM / 6 PM",
         buy=800, gtd=1000000, chips=40000, lvl="30/40 min", fee="house/staff fees listed on wynnpoker.com / structure sheets"),
    dict(id="WPT-1600", name="WPT NLH $1,600 — $1,000,000 GTD", dates="Dec 3–Dec 5", time="11 AM",
         buy=1600, gtd=1000000, chips=40000, lvl="40 min", fee="house/staff fees listed on wynnpoker.com / structure sheets"),
    dict(id="WPT-PRIME", name="WPT Prime Championship $1,100 — $5,000,000 GTD", dates="Dec 5–Dec 12", time="11 AM",
         buy=1100, gtd=5000000, chips=40000, lvl="40/60 min", fee="house/staff fees listed on wynnpoker.com / structure sheets"),
    dict(id="WPT-SGM", name="Super Gold Million Mystery Bounty $400 — $3,000,000 GTD", dates="Dec 10–Dec 14", time="10 AM / 6 PM",
         buy=400, gtd=3000000, chips=30000, lvl="20/30/40 min", fee="house/staff fees listed on wynnpoker.com / structure sheets"),
    dict(id="WPT-500K", name="WPT NLH $800 — $500,000 GTD", dates="Dec 13–Dec 15", time="11 AM",
         buy=800, gtd=500000, chips=40000, lvl="40 min", fee="house/staff fees listed on wynnpoker.com / structure sheets"),
    dict(id="WPT-PLO1M", name="WPT PLO $1,600 — $1,000,000 GTD", dates="Dec 13–Dec 15", time="12 PM",
         buy=1600, gtd=1000000, chips=40000, lvl="40 min", fee="house/staff fees listed on wynnpoker.com / structure sheets"),
    dict(id="WPT-WC", name="WPT World Championship $10,400 — $1,000,000 added by ClubWPT Gold (no cash guarantee printed)",
         dates="Dec 13–Dec 20", time="11 AM", buy=10400, gtd=None, chips=100000, lvl="60/90 min",
         fee="see structure sheet; $1,000,000 added in cash prizes by ClubWPT Gold (not available in Nevada)"),
    dict(id="WPT-LADIES", name="WPT Ladies NLH Championship $1,100 (discounted; entry $11,100) — $250,000 GTD",
         dates="Dec 13", time="11 AM", buy=1100, gtd=250000, chips=40000, lvl="40 min",
         fee="see structure sheet"),
    dict(id="WPT-1100-1M", name="WPT NLH $1,100 — $1,000,000 GTD", dates="Dec 18 (as printed) – Dec 21", time="11 AM / 7 PM",
         buy=1100, gtd=1000000, chips=40000, lvl="20/40 min", fee="see structure sheet",
         flag="Official schedule prints two rows as 'Dec. 18 Wednesday' although Dec 18, 2026 is a Friday — date unverified (see Flagged)."),
    dict(id="WPT-3000", name="WPT NLH $3,000 — $2,000,000 GTD", dates="Dec 17 (as printed) – Dec 20", time="12 PM",
         buy=3000, gtd=2000000, chips=40000, lvl="40 min", fee="see structure sheet",
         flag="Date rows around this event also carry the Dec 18/Dec 17 weekday mismatch — dates as printed, flagged."),
    dict(id="WPT-MB1600", name="WPT NLH Mystery Bounty $1,600 — $1,000,000 GTD", dates="Dec 19–Dec 21", time="11 AM / 7 PM",
         buy=1600, gtd=1000000, chips=40000, lvl="20/40 min", fee="see structure sheet"),
    dict(id="WPT-TURBO50", name="Wynn WPT NLH Turbo $600 — $50,000 GTD (recurring evenings)", dates="Dec 5–Dec 21", time="9 PM (8 PM Dec 21)",
         buy=600, gtd=50000, chips=30000, lvl="20 min", fee="see structure sheet"),
]
for w in wpt:
    events.append({
        "id": w["id"], "venue": "wynn", "venue_name": "Wynn Las Vegas (Poker Room in Encore)",
        "date": "wpt:" + w["dates"], "weekday": w["dates"], "start_time": w["time"],
        "event_no": None, "name": w["name"], "game": "NLH", "kind": "flight",
        "buy_in": w["buy"], "guarantee": w["gtd"], "bounty_amount": None,
        "structure": {"sheet": "W_WPT_TC", "url": SOURCES["W_WPT_TC"]["url"], "chips": w["chips"],
                      "level_minutes": w["lvl"], "reg_close": "per structure sheet", "pays_pct": None},
        "fees": {"house_fee": None, "to_prize_pool": None, "excerpt": w["fee"], "source": "W_WPT", "retrieved": TODAY},
        "entry_rules": {
            "status": "confirmed",
            "single_entry": {"value": "no", "excerpt": WPT_EXCERPT, "source": "W_WPT_TC", "retrieved": TODAY},
            "reentry": {"value": "unlimited per flight to level 9", "excerpt": WPT_EXCERPT,
                        "source": "W_WPT_TC", "retrieved": TODAY},
            "addon": {"value": "none stated", "excerpt": "No add-on language in the event terms read.",
                      "source": "W_WPT_TC", "retrieved": TODAY},
            "fees": {"value": w["fee"], "excerpt": w["fee"], "source": "W_WPT", "retrieved": TODAY},
            "note": w.get("flag", ""),
        },
        "ratio_guarantee_per_buy_in": round(w["gtd"] / w["buy"], 1) if w["gtd"] and w["buy"] else None,
        "last_checked": TODAY, "sources": ["W_WPT", "W_WPT_TC"],
        "notes": w.get("flag", "") or WPT_EXCERPT,
    })

# -- Bellagio weekly (structure sheets read 2026-11-17; rules CONFIRMED on Fri & Sun)
bellagio = [
    dict(id="B-FRI", name="Bellagio Friday NLH $600", days="Friday", time="11:00 AM", buy=600, gtd=None,
         chips="30,000 incl. optional gratuity (15,000 + 15,000)", lvl="30 min", reg="end of level 8 (incl. break)",
         reentry="allowed", addon="none", src="B_FRI",
         fee="$510 to Prize Pool; $50 House Fee; $40 Voluntary Staff Gratuity (extra 15,000 chips)",
         excerpt="Players may buy-in and re-enter through the end of level 8 (Including Break). Tournament Surrender is allowed on Level 8 break."),
    dict(id="B-SAT", name="Bellagio Saturday NLH — buy-in UNVERIFIED ($1,000 file / $1,100 header / $600 rule 07)",
         days="Saturday", time="11:00 AM", buy=None, gtd=50000,
         chips="40,000 (20,000 + 20,000 optional)", lvl="30 min (Day 1D: 25 min)", reg="start of Level 10",
         reentry="unverified", addon="none", src="B_SAT",
         fee="rule 07 says $510 pool / $50 admin / $40 optional gratuity 'of the $600 Buy-in' — conflicts with the $1,100 header",
         excerpt="Registration will be open until the start of Level 10. … Each Flight would play until the money (12.5%). … Bellagio guarantees that the total Combined Prize Pool will be at least $50,000.",
         flag="Official PDF conflicts with itself on buy-in ($1,100 header vs $600 rule 07 vs $1,000 filename) and mixes flighted dates — flagged, buy-in left blank."),
    dict(id="B-SUN", name="Bellagio Sunday H.O.R.S.E. $400", days="Sunday", time="11:00 AM", buy=400, gtd=None,
         chips="30,000 incl. optional gratuity (15,000 + 15,000)", lvl="30 min", reg="end of level 8 (incl. break)",
         reentry="allowed", addon="none", src="B_SUN",
         fee="$340 to Prize Pool; $35 House Fee; $25 Voluntary Staff Gratuity (extra 15,000 chips)",
         excerpt="Players may buy-in and re-enter through the end of level 8 (Including Break). Tournament Surrender is allowed on Level 8 break."),
]
for b in bellagio:
    status = "unverified" if b["reentry"] == "unverified" else "confirmed"
    events.append({
        "id": b["id"], "venue": "bellagio", "venue_name": "Bellagio (Poker Room)",
        "date": "weekly:" + b["days"], "weekday": b["days"], "start_time": b["time"],
        "event_no": None, "name": b["name"], "game": "HORSE" if "HORSE" in b["name"] else "NLH",
        "kind": "tournament", "buy_in": b["buy"], "guarantee": b["gtd"], "bounty_amount": None,
        "structure": {"sheet": b["src"], "url": SOURCES[b["src"]]["url"], "chips": b["chips"],
                      "level_minutes": b["lvl"], "reg_close": b["reg"], "pays_pct": None},
        "fees": {"house_fee": None, "to_prize_pool": None, "excerpt": b["fee"], "source": b["src"], "retrieved": TODAY},
        "entry_rules": {
            "status": status,
            "single_entry": {"value": "no" if status == "confirmed" else "unverified", "excerpt": b["excerpt"],
                             "source": b["src"], "retrieved": TODAY},
            "reentry": {"value": b["reentry"], "excerpt": b["excerpt"], "source": b["src"], "retrieved": TODAY},
            "addon": {"value": b["addon"], "excerpt": b["excerpt"], "source": b["src"], "retrieved": TODAY},
            "fees": {"value": b["fee"], "excerpt": b["fee"], "source": b["src"], "retrieved": TODAY},
            "note": b.get("flag", ""),
        },
        "ratio_guarantee_per_buy_in": round(b["gtd"] / b["buy"], 1) if b["gtd"] and b["buy"] else None,
        "last_checked": TODAY, "sources": ["B_PAGE", b["src"]], "notes": b.get("flag", "") or b["excerpt"],
    })

# -- Caesars Palace dailies (flyer read 2026-11-17; rules CONFIRMED)
C_EXCERPT = ("Sign-ups start one hour before the scheduled start of the event. … may re-enter, by paying the entry "
             "fee, upon elimination within the first break of play. All Tournaments feature a $50 add-on for 15,000 "
             "tournament chips that can only be taken at the first break.")
for cid, ctime, cbuy, cfee in [("C-10AM", "10:00 AM", 100, "$70 to prize pool; $30 maintenance fee"),
                               ("C-2PM", "2:00 PM", 160, "$115 to prize pool; $45 maintenance fee"),
                               ("C-6PM", "6:00 PM", 100, "$70 to prize pool; $30 maintenance fee"),
                               ("C-9PM", "9:00 PM", 160, "$115 to prize pool; $45 maintenance fee")]:
    events.append({
        "id": cid, "venue": "caesars", "venue_name": "Caesars Palace (Poker Room)",
        "date": "daily", "weekday": "Daily", "start_time": ctime,
        "event_no": None, "name": f"Caesars Palace Daily NLH ${cbuy}", "game": "NLH", "kind": "tournament",
        "buy_in": cbuy, "guarantee": 1000, "bounty_amount": None,
        "structure": {"sheet": "C_FLYER", "url": SOURCES["C_FLYER"]["url"], "chips": 20000,
                      "level_minutes": "20 min", "reg_close": "start of level 7", "pays_pct": None},
        "fees": {"house_fee": None, "to_prize_pool": None, "excerpt": cfee, "source": "C_FLYER", "retrieved": TODAY},
        "entry_rules": {
            "status": "confirmed",
            "single_entry": {"value": "no", "excerpt": C_EXCERPT, "source": "C_FLYER", "retrieved": TODAY},
            "reentry": {"value": "allowed (once, within first break)", "excerpt": C_EXCERPT,
                        "source": "C_FLYER", "retrieved": TODAY},
            "addon": {"value": "allowed ($50 for 15,000 chips at first break)", "excerpt": C_EXCERPT,
                      "source": "C_FLYER", "retrieved": TODAY},
            "fees": {"value": cfee, "excerpt": cfee, "source": "C_FLYER", "retrieved": TODAY},
            "note": "",
        },
        "ratio_guarantee_per_buy_in": 10.0,
        "last_checked": TODAY, "sources": ["C_FLYER", "C_PAGE"], "notes": C_EXCERPT,
    })

# ---------------------------------------------------------------- hotels
hotels = [
    {
        "id": "venetian", "name": "The Venetian / The Palazzo", "address": "3355 Las Vegas Blvd S, Las Vegas, NV 89109",
        "poker_on_site": "Venetian Poker Room — The Palazzo, Level 2 (official poker page)",
        "resort_fee_usd": 55.0, "resort_fee_note": "$55 plus tax per night, payable at check-in (mandatory)",
        "resort_fee_source": "V_RESORT", "resort_fee_checked": TODAY,
        "tax_rate_pct": 13.38, "tax_note": "Daily rates do not include the applicable Clark County Room Tax of 13.38%.",
        "tax_source": "V_TERMS", "tax_checked": TODAY,
        "parking": "$20/day registered hotel guests; $20 Mon–Thu / $25 Fri–Sun non-hotel; valet $40/day; Sapphire+ self-park free",
        "parking_source": "V_TERMS", "parking_checked": TODAY,
        "cancellation": "Deposit (first night or full stay) billed at booking. Prepaid offers non-cancellable/non-refundable. Check-out prior to scheduled departure: $100 + tax. Incidental deposit $150/night.",
        "cancellation_source": "V_TERMS", "cancellation_checked": TODAY,
        "poker_rate": "$119 / $209 starting rates (Luxury King Suite, single/double), code EPOKR25 by phone 866.255.8936; conditional on 6 hrs live cash play OR a $300+ tournament buy-in per night; blackout dates may apply",
        "poker_rate_source": "V_RATES", "poker_rate_checked": TODAY,
        "booking_url_template": "https://www.venetianlasvegas.com/booking?adults[]=2&arrival_date={in}&children[]=0&departure_date={out}&view=calendar",
        "last_checked": TODAY,
    },
    {
        "id": "wynn", "name": "Wynn Las Vegas / Encore", "address": "3131 Las Vegas Blvd S, Las Vegas, NV 89109",
        "poker_on_site": "Wynn Poker Room — located in Encore (official poker page / WPT terms)",
        "resort_fee_usd": 55.0, "resort_fee_note": "A daily resort fee of $55 plus tax for each room night (Resort rooms and Tower Suites)",
        "resort_fee_source": "W_TERMS", "resort_fee_checked": TODAY,
        "tax_rate_pct": 13.38, "tax_note": "Clark County Room Tax of 13.38% applies county-wide (stated on official Venetian hotel terms; Wynn page states '$55 plus tax' without a rate)",
        "tax_source": "V_TERMS", "tax_checked": TODAY,
        "parking": "Complimentary self-parking for up to 2 vehicles included with resort fee (Tower Suites: valet or self-park)",
        "parking_source": "W_TERMS", "parking_checked": TODAY,
        "cancellation": "For the read offer: full deposit of all room nights and tax at booking; reservations non-cancellable/non-refundable/non-changeable; $150/night incidentals at check-in. Cancellation terms are rate-specific — confirm at booking.",
        "cancellation_source": "W_TERMS", "cancellation_checked": TODAY,
        "poker_rate": None, "poker_rate_source": None, "poker_rate_checked": None,
        "booking_url_template": "https://www.wynnlasvegas.com/rooms/suites?checkInDate={in}&checkOutDate={out}",
        "last_checked": TODAY,
    },
    {
        "id": "ti", "name": "Treasure Island (TI)", "address": "3300 Las Vegas Blvd S, Las Vegas, NV 89109",
        "poker_on_site": None,
        "resort_fee_usd": 49.95, "resort_fee_note": "The $49.95 + tax daily resort fee; optional only for My TI Guestbook TV Ad Special / qualified Treasury Players Club / qualified meeting groups",
        "resort_fee_source": "TI_FEE", "resort_fee_checked": TODAY,
        "tax_rate_pct": 13.38, "tax_note": "Clark County Room Tax of 13.38% applies county-wide (stated on official Venetian hotel terms; TI page states '+ tax' without a rate)",
        "tax_source": "V_TERMS", "tax_checked": TODAY,
        "parking": "Always free valet parking & self-park garage (official fee page)",
        "parking_source": "TI_FEE", "parking_checked": TODAY,
        "cancellation": None, "cancellation_source": None, "cancellation_checked": None,
        "poker_rate": "$69* night + no resort fee TV Ad Special (conditional, as advertised on official page)",
        "poker_rate_source": "TI_FEE", "poker_rate_checked": TODAY,
        "booking_url_template": "https://all.accor.com/lien_externe.svlt?goto=rech_resa&destination=C598&origin=treasureisland",
        "last_checked": TODAY,
    },
    {
        "id": "bellagio", "name": "Bellagio", "address": "3600 Las Vegas Blvd S, Las Vegas, NV 89109",
        "poker_on_site": "Bellagio Poker Room (official poker page)",
        "resort_fee_usd": None, "resort_fee_note": "UNVERIFIED — official resort-fee page returned 404 on prior check; third-party figures conflict and are not used",
        "resort_fee_source": None, "resort_fee_checked": PRIOR,
        "tax_rate_pct": 13.38, "tax_note": "Clark County Room Tax of 13.38% applies county-wide (stated on official Venetian hotel terms)",
        "tax_source": "V_TERMS", "tax_checked": TODAY,
        "parking": None, "parking_source": None, "parking_checked": None,
        "cancellation": None, "cancellation_source": None, "cancellation_checked": None,
        "poker_rate": None, "poker_rate_source": None, "poker_rate_checked": None,
        "booking_url_template": "https://www.bellagio.mgmresorts.com/en/booking/hotel.html?checkIn={in}&checkOut={out}",
        "last_checked": PRIOR,
    },
    {
        "id": "caesars", "name": "Caesars Palace", "address": "3570 Las Vegas Blvd S, Las Vegas, NV 89109",
        "poker_on_site": "Caesars Palace Poker Room (official casino page)",
        "resort_fee_usd": None, "resort_fee_note": "UNVERIFIED — official resort-fee page is marketing copy with no fee amount; third-party figures conflict and are not used",
        "resort_fee_source": None, "resort_fee_checked": PRIOR,
        "tax_rate_pct": 13.38, "tax_note": "Clark County Room Tax of 13.38% applies county-wide (stated on official Venetian hotel terms)",
        "tax_source": "V_TERMS", "tax_checked": TODAY,
        "parking": None, "parking_source": None, "parking_checked": None,
        "cancellation": None, "cancellation_source": None, "cancellation_checked": None,
        "poker_rate": None, "poker_rate_source": None, "poker_rate_checked": None,
        "booking_url_template": "https://www.caesars.com/book/rooms?checkInDate={in}&checkOutDate={out}",
        "last_checked": PRIOR,
    },
]

# ---------------------------------------------------------------- walking
def gm(origin, dest):
    o = origin.replace(" ", "+").replace(",", "%2C")
    d = dest.replace(" ", "+").replace(",", "%2C")
    return f"https://www.google.com/maps/dir/{o}/{d}/data=!4m2!4m1!3e2"

walking = [
    # hotel, venue, minutes, distance, maps origin/destination labels (verified 2026-11-16/17, Google Maps walking mode)
    ("venetian", "venetian", 0, "on property (Palazzo Level 2)", None, None),
    ("wynn", "wynn", 0, "on property (Encore)", None, None),
    ("bellagio", "bellagio", 0, "on property", None, None),
    ("caesars", "caesars", 0, "on property", None, None),
    ("venetian", "wynn", 13, "0.6 mi", "The Venetian Resort Las Vegas, 3355 Las Vegas Blvd S, Las Vegas, NV 89109",
     "Wynn Las Vegas, 3131 Las Vegas Blvd S, Las Vegas, NV 89109"),
    ("venetian", "bellagio", 18, "0.8 mi", "The Venetian Resort Las Vegas, 3355 Las Vegas Blvd S, Las Vegas, NV 89109",
     "Bellagio Poker Room, 3600 Las Vegas Blvd S, Las Vegas, NV 89109"),
    ("venetian", "caesars", 12, "0.5 mi", "The Venetian Resort Las Vegas, 3355 Las Vegas Blvd S, Las Vegas, NV 89109",
     "Caesars Palace Poker Room, 3570 Las Vegas Blvd S, Las Vegas, NV 89109"),
    ("ti", "venetian", 6, "0.2 mi", "Treasure Island Las Vegas, 3300 Las Vegas Blvd S, Las Vegas, NV 89109",
     "The Venetian Resort Las Vegas, 3355 Las Vegas Blvd S, Las Vegas, NV 89109"),
    ("ti", "wynn", 11, "0.5 mi", "Treasure Island Las Vegas, 3300 Las Vegas Blvd S, Las Vegas, NV 89109",
     "Wynn Las Vegas, 3131 Las Vegas Blvd S, Las Vegas, NV 89109"),
    ("ti", "bellagio", 21, "0.9 mi", "Treasure Island Las Vegas, 3300 Las Vegas Blvd S, Las Vegas, NV 89109",
     "Bellagio Poker Room, 3600 Las Vegas Blvd S, Las Vegas, NV 89109"),
    ("ti", "caesars", 14, "0.6 mi", "Treasure Island Las Vegas, 3300 Las Vegas Blvd S, Las Vegas, NV 89109",
     "Caesars Palace Poker Room, 3570 Las Vegas Blvd S, Las Vegas, NV 89109"),
    ("wynn", "bellagio", 29, "1.3 mi", "Wynn Las Vegas, 3131 Las Vegas Blvd S, Las Vegas, NV 89109",
     "Bellagio Poker Room, 3600 Las Vegas Blvd S, Las Vegas, NV 89109"),
    ("wynn", "caesars", 22, "1.0 mi", "Wynn Las Vegas, 3131 Las Vegas Blvd S, Las Vegas, NV 89109",
     "Caesars Palace Poker Room, 3570 Las Vegas Blvd S, Las Vegas, NV 89109"),
    ("bellagio", "caesars", 13, "0.6 mi", "Bellagio, 3600 Las Vegas Blvd S, Las Vegas, NV 89109",
     "Caesars Palace Poker Room, 3570 Las Vegas Blvd S, Las Vegas, NV 89109"),
]
walk_rows = []
for hotel_id, venue_id, mins, dist, o, d in walking:
    url = gm(o, d) if o else None
    walk_rows.append({
        "hotel": hotel_id, "venue": venue_id,
        "walk_minutes": mins if o else 0, "walk_distance": dist,
        "within_30_min": True,
        "source": "GM" if o else "V_POKER", "maps_url": url,
        "apple_url": f"https://maps.apple.com/?saddr={o.replace(' ', '+')}&daddr={d.replace(' ', '+')}&dirflg=w" if o else None,
        "retrieved": TODAY if o else TODAY, "last_checked": TODAY,
    })

# ---------------------------------------------------------------- rate log
rate_log = [
    {"id": "RL-001", "property": "venetian", "retrieved": TODAY, "rate_timestamp": f"{TODAY} (page read, UTC)",
     "stay_start": None, "stay_end": None, "occupancy": "single/double (Luxury King Suite)",
     "nightly_avg": None, "checkout_total": None,
     "published_rate": "$119 / $209 starting poker-suite rates ('as low as'; can be higher)",
     "resort_fee": "$55 + tax", "tax": "13.38% Clark County room tax",
     "parking": "$20/day hotel guests", "cancellation_deadline": "prepaid offers non-cancellable; deposit at booking",
     "source": "V_RATES",
     "notes": "Conditional poker rate: 6 hrs live cash play or a $300+ tournament buy-in per night, code EPOKR25 by phone. Not a dated quote; date-specific totals require the official booking engine (deep link per date on the Hotels page)."},
    {"id": "RL-002", "property": "wynn", "retrieved": TODAY, "rate_timestamp": f"{TODAY} (terms page read, UTC)",
     "stay_start": None, "stay_end": None, "occupancy": None,
     "nightly_avg": None, "checkout_total": None,
     "published_rate": None,
     "resort_fee": "$55 + tax", "tax": "13.38% county rate (see note)",
     "parking": "free self-park, 2 vehicles (with resort fee)",
     "cancellation_deadline": "read offer: non-cancellable, full deposit at booking (rate-specific)",
     "source": "W_TERMS",
     "notes": "No nightly rate published on the official terms page. Date-specific quotes via official booking deep link."},
    {"id": "RL-003", "property": "ti", "retrieved": TODAY, "rate_timestamp": f"{TODAY} (official page read, UTC)",
     "stay_start": None, "stay_end": None, "occupancy": None,
     "nightly_avg": None, "checkout_total": None,
     "published_rate": "$69/night + no resort fee (TV Ad Special, conditional)",
     "resort_fee": "$49.95 + tax (mandatory unless qualifying booking)", "tax": "13.38% county rate (see note)",
     "parking": "free valet & self-park", "cancellation_deadline": None,
     "source": "TI_FEE",
     "notes": "TV Ad Special is conditional; standard bookings pay the resort fee."},
    {"id": "RL-004", "property": "bellagio", "retrieved": PRIOR, "rate_timestamp": f"{PRIOR} (official pages checked)",
     "stay_start": None, "stay_end": None, "occupancy": None,
     "nightly_avg": None, "checkout_total": None,
     "published_rate": None, "resort_fee": None, "tax": "13.38% county rate (see note)",
     "parking": None, "cancellation_deadline": None,
     "source": "B_PAGE",
     "notes": "No official resort-fee amount found (404 on fee page); values left blank + flagged."},
    {"id": "RL-005", "property": "caesars", "retrieved": PRIOR, "rate_timestamp": f"{PRIOR} (official pages checked)",
     "stay_start": None, "stay_end": None, "occupancy": None,
     "nightly_avg": None, "checkout_total": None,
     "published_rate": None, "resort_fee": None, "tax": "13.38% county rate (see note)",
     "parking": None, "cancellation_deadline": None,
     "source": "C_PAGE",
     "notes": "Official resort-fee page contains no fee amount; values left blank + flagged."},
]

# ---------------------------------------------------------------- flagged
flagged = [
    {"id": "F-01", "severity": "decision-blocking",
     "topic": "Entry rules",
     "detail": "After reading all 37 Venetian DSE IV structure sheets in full (2026-11-17), none states a re-entry, rebuy, add-on, freezeout or single-entry policy. Silence is not confirmation: NO Venetian event can be labeled 'single-entry confirmed'. The 'Single-entry / freezeout confirmed' toggle therefore shows 0 matching rows until the poker room confirms in writing.",
     "sources": ["V_PAGE", "V_S1", "V_S5", "V_S29"]},
    {"id": "F-02", "severity": "irregularity",
     "topic": "Bellagio Saturday buy-in conflict",
     "detail": "The official Bellagio Saturday PDF is internally inconsistent: filename says $1000, header says '$1100 BUY-IN', rule 07 allocates 'the $600 Buy-in' ($510/$50/$40). It also describes flights (1A–1D) with a combined Day 2 '9/13/26'. Buy-in left blank; verify with the Bellagio poker room before planning.",
     "sources": ["B_SAT"]},
    {"id": "F-03", "severity": "irregularity",
     "topic": "Wynn WPT schedule date labels",
     "detail": "The official WPT schedule PDF prints two rows as 'Dec. 18 Wednesday' and one as 'Dec. 18 Friday'; in 2026 Dec 18 is a Friday and Dec 16 is the Wednesday. The Wednesday rows may belong to Dec 16. Dates left as printed and flagged; verify with the Wynn poker room.",
     "sources": ["W_WPT"]},
    {"id": "F-04", "severity": "decision-blocking",
     "topic": "No 8:00 AM start exists",
     "detail": "The earliest verified start anywhere in the official schedules read is 9:10 AM (Venetian satellite #46) and 10:10 AM for open tournaments (Seniors/RaceDay). A strict 8 AM–onward tournament day is not achievable in this snapshot; the day plan starts at 9:10/10:10 AM and says so.",
     "sources": ["V_PAGE", "V_SCHED"]},
    {"id": "F-05", "severity": "needs-info",
     "topic": "Date-specific hotel totals",
     "detail": "Official sites publish no scraped date-specific totals (checkout total / nightly average) outside their booking engines. The rate log keeps dated, timestamped published rates and fees; the Hotels page links the official booking engine per date and provides a true-cost calculator. Occupancy + exact dates are required before any like-for-like comparison.",
     "sources": ["V_RATES", "W_TERMS", "TI_FEE"]},
    {"id": "F-06", "severity": "needs-info",
     "topic": "Bellagio & Caesars resort fees",
     "detail": "Bellagio's official fee page returned 404 and Caesars Palace's fee page carries no amount (both checked 2026-11-16). Third-party figures conflict and are not used. Fee fields left blank and flagged.",
     "sources": ["B_PAGE", "C_PAGE"]},
    {"id": "F-07", "severity": "irregularity",
     "topic": "Venetian schedule labels vs structure sheets",
     "detail": "The official schedule page marks some events '$20 rake disc' / '$40 rake disc' (e.g. #16/#36/#59/#56); the discount wording actually appears on structure sheets 4, 8, 35, 36 only. Sheet 11/16 contain no discount clause. Discounts verified only where the sheet states them.",
     "sources": ["V_PAGE", "V_S4", "V_S8", "V_S11", "V_S16"]},
    {"id": "F-08", "severity": "needs-info",
     "topic": "Event finish times",
     "detail": "No official source publishes event end times. Overlap flags use start time + late-registration cutoff + a documented plausible-duration heuristic (see Schedule page). Once real finish times are observed, replace the heuristic and re-check overlaps.",
     "sources": ["V_SCHED", "W_DAILY"]},
    {"id": "F-09", "severity": "irregularity",
     "topic": "Multi-flight 're-entry' semantics",
     "detail": "Venetian multi-flight events (sheets 2/3/4/9/10/12/13/14/20/21/35/36/37) only state 'Any player who bags chips for Day 2 may not play a subsequent flight' — implying repeat buy-ins via new flights are possible unless bagged. Within-flight re-entry remains unverified. WPT events explicitly allow unlimited re-entry per flight (confirmed).",
     "sources": ["V_S2", "V_S12", "W_WPT_TC"]},
    {"id": "F-10", "severity": "irregularity",
     "topic": "Venetian Valuetown bounty 'subsequent buy ins'",
     "detail": "Structure sheet 8 rule 07 says 'All subsequent buy in's after the initial buy in will be $200', implying multiple buy-ins are possible, but no re-entry policy clause exists. Not single-entry-confirmed.",
     "sources": ["V_S8"]},
]

# ---------------------------------------------------------------- write
def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")

dump("sources.json", {"meta": {"generated": TODAY, "policy": "Official operator sources only; each row's values link these keys."},
                      "sources": SOURCES})
dump("events.json", {"meta": {
        "generated": TODAY,
        "window": "Nov 17 – Dec 23, 2026 (DSE IV) and Nov 27 – Dec 21, 2026 (Wynn WPT), plus daily/weekly rooms",
        "ranking_rule": "Rank only where the total entry fee and the guarantee are both confirmed. Ratio = guarantee ÷ total entry fee, descriptive arithmetic only — not a forecast. Bounty and flight events are labeled separately because their guarantees pool different things.",
        "entry_rule_policy": "single-entry/freezeout is 'confirmed' only when an official sheet states the entry limit. Venetian sheets are silent → unverified. Wynn / Bellagio / Caesars rules are stated → confirmed."},
    "sources": SOURCES, "events": events})
dump("hotels.json", {"meta": {"generated": TODAY,
                             "true_cost_formula": "true cost/night = (nightly rate + mandatory resort fee) × (1 + 13.38% tax). Tax applies to room and fee in Clark County.",
                             "policy": "Only official-page values. Blank = unverified."},
                     "tax_rate_pct": 13.38, "tax_source": "V_TERMS",
                     "hotels": hotels, "sources": SOURCES})
dump("walking.json", {"meta": {"generated": TODAY,
                              "rule": "≤ 30-minute walking limit applied. Minutes/distance read from Google Maps walking directions on the retrieval date (each row links its route). Same-property pairs are 0 (on site)."},
                      "pairs": walk_rows, "sources": SOURCES})
dump("rate_log.json", {"meta": {"generated": TODAY,
                               "policy": "Dated log, never a single value. Each entry records what the official page published and when we read it."},
                       "entries": rate_log, "sources": SOURCES})
dump("flagged.json", {"meta": {"generated": TODAY, "policy": "Flagged items do not block publication; they are review work."},
                      "items": flagged, "sources": SOURCES})
dump("monitor/status.json", {"meta": {"generated": TODAY,
                                     "explanation": "Refreshed by tools/recheck.py on a daily GitHub Actions schedule. Each monitored URL keeps a content hash; rows whose source changed since the previous run are marked changed=true."},
                             "last_run": TODAY, "entries": []})

n_unv = sum(1 for e in events if e["entry_rules"]["status"] == "unverified")
n_conf = sum(1 for e in events if e["entry_rules"]["status"] == "confirmed")
print(f"events: {len(events)} total — {n_unv} entry-rule-unverified, {n_conf} confirmed")
print(f"hotels: {len(hotels)}, walking pairs: {len(walk_rows)}, rate log: {len(rate_log)}, flagged: {len(flagged)}")
print(f"wrote data/v2/*.json (sources: {len(SOURCES)})")
