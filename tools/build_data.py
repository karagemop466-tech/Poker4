#!/usr/bin/env python3
"""Assemble consolidated data files for the Poker4 dashboard.

Sources are official operator pages/PDFs; every row carries source_url, source
excerpt where relevant, and last_checked (ISO date). Values that could not be
confirmed from an official source are None and carry a flag.
"""
import csv, json, os, hashlib, datetime

TODAY = "2026-11-17"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

def w(name, obj):
    with open(os.path.join(DATA, name), "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")

# ---------------------------------------------------------------- sources
S = {
 "V_PAGE": ("Venetian DeepStack Extravaganza IV official series page",
   "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"),
 "V_SCHED": ("Venetian DSE IV schedule (PDF)",
   "https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/dse-nov-2026-schedule.pdf"),
 "V_FEE": ("Venetian resort fee page",
   "https://www.venetianlasvegas.com/resort/resort-fee.html"),
 "V_TERMS": ("Venetian hotel terms and conditions (tax 13.38%, parking, cancellation)",
   "https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html"),
 "V_POKER_RATE": ("Venetian 2026 poker suite rates and play requirements",
   "https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html"),
 "V_POKER": ("Venetian poker room page (room location)",
   "https://www.venetianlasvegas.com/resort/casino/poker.html"),
 "W_PAGE": ("Wynn Las Vegas poker room page",
   "https://www.wynnlasvegas.com/casino/poker"),
 "W_DAILY": ("Wynn daily tournament structures / terms (PDF)",
   "https://cdn.wynnresorts.com/image/upload/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf"),
 "W_WPT_TC": ("Wynn WPT World Championship structures / terms (PDF)",
   "https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf"),
 "W_WPT_SCHED": ("Wynn WPT World Championship schedule (PDF)",
   "https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf"),
 "W_TERMS": ("Wynn Las Vegas terms and conditions (resort fee $55 + tax)",
   "https://www.wynnlasvegas.com/terms-and-conditions/850257"),
 "B_PAGE": ("Bellagio poker page",
   "https://bellagio.mgmresorts.com/en/casino/poker.html"),
 "B_FRI": ("Bellagio Friday $600 NLH structure (PDF)",
   "https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt9cf95b0e60ec253e/6af491a3a9851d75c40be840/mgm-bellagio-poker-fridays-$600-nlh.pdf"),
 "B_SAT": ("Bellagio Saturday NLH structure (PDF, undated; buy-in conflict in sheet)",
   "https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt6d47974bf5a7d9b6/6af491a391a6e8e4230c9e07/mgm-bellagio-poker-saturdays-$1000-nlh.pdf"),
 "B_SUN": ("Bellagio Sunday $400 H.O.R.S.E. structure (PDF)",
   "https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt07fcf1244a6da661/6af491a339e2b4f6b76a86ad/mgm-bellagio-poker-sundays-$400-horse.pdf"),
 "B_TERMS": ("Bellagio hotel reservation terms (resort fee $55 + tax, 72h cancellation)",
   "https://bellagio.mgmresorts.com/en/terms-and-conditions.html"),
 "C_FLYER": ("Caesars Palace daily NLH tournament flyer (PDF, 2026)",
   "https://www.caesars.com/content/dam/empire/clv/casino/poker/tournament-schedule/clv-poker-daily-nlh-tournament-flyer-2026.pdf"),
 "C_PAGE": ("Caesars Palace casino page",
   "https://www.caesars.com/caesars-palace/casino"),
 "C_HOME": ("Caesars Palace official homepage (published rate lead, cancellation banner)",
   "https://www.caesars.com/caesars-palace"),
 "A_TERMS": ("ARIA hotel reservation terms (resort fee $55 + tax, 72h cancellation)",
   "https://aria.mgmresorts.com/en/terms-and-conditions.html"),
 "A_PAGE": ("ARIA poker page",
   "https://aria.mgmresorts.com/en/casino/poker.html"),
 "MGM_PARK": ("MGM Resorts official parking rates page",
   "https://www.mgmresorts.com/en/things-to-do/parking.html"),
 "TI_ROOMS": ("Treasure Island deluxe rooms page (resort fee $49.95 + tax, free parking)",
   "https://treasureisland.com/hotel/deluxe-rooms"),
 "TI_OFFERS": ("Treasure Island offer terms",
   "https://treasureisland.com/deals-offers/buy-1-get-1-bogo-free-fine-print"),
 "HP_PAGE": ("Harrah's Las Vegas official page",
   "https://www.caesars.com/harrahs-las-vegas"),
 "HS_PAGE": ("Horseshoe Las Vegas official page",
   "https://www.caesars.com/horseshoe-las-vegas"),
}
w("sources.json", {"generated": TODAY, "sources": [
    {"id": k, "label": v[0], "url": v[1], "last_checked": TODAY} for k, v in S.items()]})

def src(k): return S[k][1]

# ------------------------------------------------- Venetian structure sheets
# details read directly from each official structure PDF (fetched 2026-11-17)
def st(pdf, events, name, start, stack, level_min, late_reg, guarantee, fee,
       pool, game="NLH", kind="one-day", bounty=None, note=None):
    return dict(pdf=pdf, events=events, name=name, start=start, stack=stack,
                level_min=level_min, late_reg=late_reg, guarantee=guarantee,
                fee=fee, pool=pool, game=game, kind=kind, bounty=bounty, note=note)

SHEETS = [
 st("dse_nov_2026-structure_1.pdf", [9,11,13,15,21,22,23,25,60,61,62,64],
    "$200 No Limit Hold'em Bounty (1Day)", "17:10", 25000, 30,
    "8 levels + break (9:40 PM)", 8000, 40, 160, kind="bounty",
    bounty="$50 bounty per elimination", note="Guarantee $8,000 = prize pool + total bounties"),
 st("dse_nov_2026-structure_2.pdf", [7], "$400 No Limit Hold'em (flights 1A/1B)",
    "11:10", 40000, 40, "9 levels + break (5:55 PM)", 75000, 70, 330,
    kind="multi-flight", note="Day 2 11:00 AM; a player who bags may not play a subsequent flight"),
 st("dse_nov_2026-structure_3.pdf", [19], "$400 No Limit Hold'em (flights 1A/1B/1C)",
    "11:10", 40000, 40, "9 levels + break (5:55 PM)", 75000, 70, 330,
    kind="multi-flight", note="Day 2 11:00 AM; a player who bags may not play a subsequent flight"),
 st("dse_nov_2026-structure_4.pdf", [59], "$600 No Limit Hold'em (flights 1A/1B/1C)",
    "11:10", 40000, 40, "9 levels + break (5:55 PM)", 150000, 95, 505,
    kind="multi-flight", note="Day 2 11:00 AM; $580 early-reg on Day 1A before start"),
 st("dse_nov_2026-structure_5.pdf", [2,12], "$300 No Limit Hold'em (1Day)",
    "11:10", 40000, 30, "10 levels + break (~4:55 PM)", 10000, 58, 242),
 st("dse_nov_2026-structure_6.pdf", [10], "$400 No Limit Hold'em (1Day)",
    "11:10", 40000, 30, "10 levels + break (~4:55 PM)", 15000, 65, 335),
 st("dse_nov_2026-structure_7.pdf", [14,28,63], "$600 No Limit Hold'em (1Day)",
    "11:10", 40000, 30, "10 levels + break (~4:55 PM)", None, 90, 510,
    note="Guarantee $30,000 events 14 & 63; $40,000 event 28"),
 st("dse_nov_2026-structure_8.pdf", [18,58], "$200 No Limit Hold'em Valuetown Bounty (1Day)",
    "17:10", 25000, 30, "8 levels + break (9:40 PM)", 20000, 40, 160,
    kind="bounty", bounty="$50 bounty per elimination",
    note="Guarantee $20,000 = prize pool + bounties; sheet prices 'all subsequent buy in's after the initial buy in' at $200 (multi-entry implied)"),
 st("dse_nov_2026-structure_9.pdf", [1], "$300 No Limit Hold'em (flights 1B/1D)",
    "17:10", 30000, 30, "6 levels + break (~8:40 PM)", 75000, 60, 240,
    kind="multi-flight", note="Day 2 12:00 PM; a player who bags may not play a subsequent flight"),
 st("dse_nov_2026-structure_10.pdf", [1], "$300 No Limit Hold'em (flights 1A/1C)",
    "11:10", 30000, 40, "6 levels + break (~3:40 PM)", 75000, 60, 240,
    kind="multi-flight", note="Day 2 12:00 PM; a player who bags may not play a subsequent flight"),
 st("dse_nov_2026-structure_11.pdf", [16,30,54], "$600 No Limit Hold'em Bounty (1Day)",
    "11:10", 40000, 30, "10 levels + break (4:55 PM)", None, 90, 510,
    kind="bounty", bounty="$200 bounty; $500 after the money",
    note="Guarantees incl. bounties: $30K (#16), $40K (#30), $50K (#54)"),
 st("dse_nov_2026-structure_12.pdf", [26], "$800 No Limit Hold'em (flights 1A-1E)",
    "11:10", 40000, 40, "6 levels + break (~3:40 PM)", 500000, 110, 690,
    kind="multi-flight", note="Day 2 12:00 PM; bags may not play a subsequent flight"),
 st("dse_nov_2026-structure_13.pdf", [26], "$800 No Limit Hold'em (flights 1B/1D)",
    "17:10", 40000, 30, "6 levels + break (~8:40 PM)", 500000, 110, 690,
    kind="multi-flight", note="Day 2 12:00 PM; bags may not play a subsequent flight"),
 st("dse_nov_2026-structure_14.pdf", [26], "$800 No Limit Hold'em (flight 1F Turbo)",
    "17:10", 40000, 20, "6 levels + break (~7:25 PM)", 500000, 110, 690,
    kind="multi-flight", note="Turbo; Day 2 12:00 PM"),
 st("dse_nov_2026-structure_15.pdf", [29,31,34,38,42,50,51,53,55],
    "$300 No Limit Hold'em Bounty (1Day)", "17:10", 25000, 30,
    "8 levels + break (9:40 PM)", 15000, 50, 250, kind="bounty",
    bounty="$100 bounty per elimination", note="Guarantee $15,000 = prize pool + bounties"),
 st("dse_nov_2026-structure_16.pdf", [36], "$800 No Limit Hold'em Bounty (1Day)",
    "11:10", 40000, 30, "10 levels + break (4:55 PM)", 75000, 100, 700,
    kind="bounty", bounty="$200 bounty; $500 after the money",
    note="Guarantee $75,000 = prize pool + bounties"),
 st("dse_nov_2026-structure_17.pdf", [24,32], "$600 No Limit Hold'em Seniors 50+ (1Day)",
    "10:10", 40000, 30, "10 levels + break (~3:55 PM)", 40000, 90, 510,
    kind="seniors", note="Must be 50+; pays 15% of field"),
 st("dse_nov_2026-structure_18.pdf", [3,4,5], "$200 No Limit Hold'em RaceDay Stack (1Day)",
    "10:10", 30000, 20, "6 levels + break (~12:25 PM)", None, 35, 165,
    note="Levels 20 min then 15 min; no guarantee on sheet"),
 st("dse_nov_2026-structure_19.pdf", [33,37], "$100 NLH LIPS Ladies Milestone Satellite",
    "16:10", 20000, 20, "6 levels + break (~6:25 PM)", None, 20, 80,
    kind="satellite", game="NLH (Ladies)",
    note="Prize: 2 seats to $800 LIPS Ladies Event #39; milestone 200,000 chips"),
 st("dse_nov_2026-structure_22.pdf", [20], "$300 PLO Double Board Bomb Pot (1Day)",
    "12:10", 30000, 30, "8 levels + break (~4:40 PM)", 10000, 58, 242,
    game="PLO Bomb Pot"),
 st("dse_nov_2026-structure_23.pdf", [57], "$600 PLO Double Board Bomb Pot (1Day)",
    "12:10", 30000, 30, "8 levels + break (~4:40 PM)", 25000, 90, 510,
    game="PLO Bomb Pot"),
 st("dse_nov_2026-structure_24.pdf", [41,44], "$260 Milestone Satellite to $2,200 Event #47",
    "16:10", 20000, 20, "6 levels + break (~6:25 PM)", None, 40, 220,
    kind="satellite", note="Prize: 2 seats to $2,200 PokerAtlas Championship Event #47"),
 st("dse_nov_2026-structure_25.pdf", [45,46,48], "$260 Turbo Milestone Satellite to $2,200 Event #47",
    None, 20000, 15, "6 levels", None, 35, 225,
    kind="satellite", note="Starts: #45 8:10 PM, #46 9:10 AM, #48 12:10 PM; prize 2 seats each"),
 st("dse_nov_2026-structure_26.pdf", [17], "$400 PLO Bounty (1Day)",
    "12:10", 30000, 30, "8 levels + break (~4:40 PM)", 15000, 60, 340,
    game="PLO", kind="bounty", bounty="$100 bounty",
    note="Guarantee $15,000 = prize pool + bounties"),
 st("dse_nov_2026-structure_27.pdf", [40], "$600 PLO Bounty (1Day)",
    "12:10", 30000, 30, "8 levels + break (~4:40 PM)", 25000, 90, 510,
    game="PLO", kind="bounty", bounty="$200 bounty",
    note="Guarantee $25,000 = prize pool + bounties"),
 st("dse_nov_2026-structure_28.pdf", [27], "$600 BIG O (1Day)",
    "12:10", 30000, 30, "8 levels + break (~4:40 PM)", 25000, 90, 510,
    game="BIG O"),
 st("dse_nov_2026-structure_29.pdf", [6], "$200 No Limit Hold'em (1Day)",
    "11:10", 30000, 30, "8 levels + break (~3:40 PM)", None, 40, 160,
    note="No guarantee on sheet"),
 st("dse_nov_2026-structure_30.pdf", [8], "$200 No Limit Hold'em PKO (1Day)",
    "17:10", 25000, 30, "8 levels + break (9:40 PM)", 8000, 40, 160,
    kind="bounty", bounty="$50 progressive bounty",
    note="Guarantee $8,000 = prize pool + bounties"),
 st("dse_nov_2026-structure_31.pdf", [35], "$600 LIPS Jingle Tag Team (1Day)",
    "10:10", 40000, 30, "8 levels + break (~2:40 PM)", 10000, 80, 510,
    kind="team", note="$10 LIPS fee on top of house fee; teams F/F or F/M; rotate every level"),
 st("dse_nov_2026-structure_32.pdf", [39], "$800 NLH LIPS Ladies (2Day)",
    "10:10", 40000, 40, "9 levels + break (~4:55 PM)", 40000, 90, 690,
    kind="ladies", game="NLH (Ladies)",
    note="$20 LIPS fee; Day 2 Dec 11 10:00 AM; PokerGO streamed final table"),
]
SHEET_BY_PDF = {s["pdf"]: s for s in SHEETS}

VEN_URL = src("V_PAGE")
def vstruct(pdf): return ("https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/"
                         "deepstack/2026/structures/" + pdf)

# -------------------------------------------------------- build events.json
events = []

# Venetian rows from the c07371e3 CSV (94 rows, rebuilt from the official page)
csv_path = os.path.join(ROOT, "data", "c07371e3", "venetian_deepstack_iv.csv")
with open(csv_path, newline="") as f:
    for r in csv.DictReader(f):
        pdf = (r.get("structure_pdf") or "").strip()
        sh = SHEET_BY_PDF.get(pdf)
        try: ev_no = int((r.get("event_no") or "0").strip() or 0)
        except ValueError: ev_no = 0
        buy_in = (r.get("buy_in_usd") or "").strip()
        gtd = (r.get("guarantee_usd") or "").strip()
        name = (r.get("event_name") or "").strip()
        row = {
            "id": "V-%s-%s" % (r["date"], ev_no),
            "venue": "Venetian",
            "series": "DeepStack Extravaganza IV",
            "date": r["date"], "weekday": r["weekday"],
            "time": (r.get("time") or "").strip(),
            "event_no": ev_no, "name": name,
            "game": sh["game"] if sh else ("PLO" if "PLO" in name or "Omaha" in name else "NLH"),
            "kind": sh["kind"] if sh else ("bounty" if "bounty" in name.lower() else
                   ("multi-flight" if any(x in name for x in ("1A","1B","1C","1D")) else "one-day")),
            "buy_in": int(buy_in) if buy_in.isdigit() else None,
            "guarantee": int(gtd) if gtd.isdigit() else None,
            "guarantee_note": sh["note"] if sh and sh.get("note") and "Guarantee" in (sh.get("note") or "") else None,
            "house_fee": sh["fee"] if sh else None,
            "prize_pool_per_entry": sh["pool"] if sh else None,
            "start_stack": sh["stack"] if sh else None,
            "level_minutes": sh["level_min"] if sh else None,
            "late_reg": sh["late_reg"] if sh else None,
            "bounty": sh["bounty"] if sh and sh.get("bounty") else None,
            "sheet_note": sh["note"] if sh else None,
            "entry_rules": {
                "single_entry": "unverified",
                "reentry": "unverified",
                "rebuy": "unverified",
                "addon": "unverified",
                "excerpt": ("Sheet states no re-entry/rebuy/add-on terms" if sh else "No sheet linked on schedule row"),
                "status": "unverified",
                "source_url": vstruct(pdf) if pdf else VEN_URL,
                "retrieved": TODAY,
            },
            "source_url": VEN_URL,
            "structure_url": vstruct(pdf) if pdf else None,
            "last_checked": TODAY,
            "flags": [],
        }
        if ev_no in (1, 7, 19, 26, 59):
            row["flags"].append("multi-flight event; buy-in is per flight; one bag per player")
        if ev_no in (33, 37, 41, 44, 45, 46, 48):
            row["kind"] = "satellite"
            row["flags"].append("satellite — seats, not cash; excluded from cash-guarantee ranking")
        if ev_no == 33 or ev_no == 37:
            row["flags"].append("Ladies only")
        if ev_no == 39:
            row["flags"].append("Ladies only; 2-day event")
        if ev_no == 35:
            row["flags"].append("Tag team event (two players share one entry)")
        if ev_no in (24, 32):
            row["flags"].append("Seniors 50+ only")
        if ev_no in (18, 58):
            row["flags"].append("Sheet prices 'subsequent buy-ins' at $200 — multi-entry implied")
            row["entry_rules"]["excerpt"] = ("All subsequent buy in's after the initial buy in will be $200 "
                                             "(structure sheet rule 07)")
            row["entry_rules"]["reentry"] = "implied-multi"
            row["entry_rules"]["status"] = "implied-multi"
        events.append(row)

# Wynn daily tournaments (official W_DAILY PDF terms, fetched 2026-11-17)
WY = [
 dict(id="WYNN-MTHU", name="$200 NLH $10,000 Guarantee (Mon–Thu)", date=None,
      days="Mon,Tue,Wed,Thu", time="12:00", buy_in=200, guarantee=10000,
      fee=26, staff=12, pool=162, stack=25000, level_min=30,
      late_reg="start of level 9 (~4:30 PM)",
      rules=dict(single_entry="confirmed-no",
                 reentry="confirmed-yes", rebuy="confirmed-no", addon="confirmed-no",
                 excerpt=("\"The Tournament entry fee, as well as the re-entry fee, is $200\"; "
                          "\"Registration and re-entries will be available until the start of level 9\""),
                 source_url=src("W_DAILY"), retrieved=TODAY, status="confirmed"),
      flags=[]),
 dict(id="WYNN-FRI", name="$240 NLH Rebuy & Add-on $40,000 Guarantee (Fri)", date=None,
      days="Fri", time="12:00", buy_in=240, guarantee=40000,
      fee=35, staff=15, pool=190, stack=25000, level_min=30,
      late_reg="start of level 9 (~4:30 PM); rebuys/add-ons same cutoff",
      rules=dict(single_entry="confirmed-no",
                 reentry="confirmed-no", rebuy="confirmed-yes", addon="confirmed-yes",
                 excerpt=("\"Re-entry is NOT allowed\"; \"Unlimited $200 rebuys for 25,000 tournament chips "
                          "… any time a player is at 15,000 chips or less. One (1) $100 add-on for 15,000\""),
                 source_url=src("W_DAILY"), retrieved=TODAY, status="confirmed"),
      flags=["unlimited rebuys + add-on = spending advantage"]),
 dict(id="WYNN-SATSUN", name="$200 NLH $25,000 Guarantee (Sat & Sun)", date=None,
      days="Sat,Sun", time="12:00", buy_in=200, guarantee=25000,
      fee=26, staff=12, pool=162, stack=25000, level_min=30,
      late_reg="start of level 11 (~5:30 PM)",
      rules=dict(single_entry="confirmed-no",
                 reentry="confirmed-yes", rebuy="confirmed-no", addon="confirmed-yes",
                 excerpt=("\"Registration, re-entries, and one (1) add-on per entry will be available "
                          "until the start of level 11\""),
                 source_url=src("W_DAILY"), retrieved=TODAY, status="confirmed"),
      flags=["one $100 add-on per entry for 25,000 chips"]),
 dict(id="WYNN-NIGHTLY", name="$160 NLH $10,000 Guarantee (Nightly)", date=None,
      days="Mon,Tue,Wed,Thu,Fri,Sat,Sun", time="18:00", buy_in=160, guarantee=10000,
      fee=20, staff=10, pool=130, stack=25000, level_min=20,
      late_reg="start of level 9 (~9:00 PM)",
      rules=dict(single_entry="confirmed-no",
                 reentry="confirmed-yes", rebuy="confirmed-no", addon="confirmed-yes",
                 excerpt=("\"Registration, re-entries, and one (1) add-on per entry will be available "
                          "until the start of level 9\""),
                 source_url=src("W_DAILY"), retrieved=TODAY, status="confirmed"),
      flags=["one $100 add-on per entry for 25,000 chips"]),
]
for e in WY:
    events.append(dict(id=e["id"], venue="Wynn", series="Wynn Daily", date=e["date"],
        weekday=None, days=e["days"], time=e["time"], event_no=None, name=e["name"],
        game="NLH", kind="one-day", buy_in=e["buy_in"], guarantee=e["guarantee"],
        guarantee_note=None, house_fee=e["fee"], staff_fee=e["staff"],
        prize_pool_per_entry=e["pool"], start_stack=e["stack"],
        level_minutes=e["level_min"], late_reg=e["late_reg"], bounty=None,
        sheet_note=None, entry_rules=e["rules"], source_url=src("W_PAGE"),
        structure_url=src("W_DAILY"), last_checked=TODAY, flags=e["flags"]))

# WPT World Championship at Wynn (Nov 27 – Dec 21, 2026)
wpt_csv = os.path.join(ROOT, "data", "c07371e3", "wynn_wpt.csv")
wpt_rows = []
if os.path.exists(wpt_csv):
    with open(wpt_csv, newline="") as f:
        wpt_rows = list(csv.DictReader(f))
wpt_confirmed = {
  # events whose official structure-sheet excerpts were read on 2026-11-17
  "600 TORSE": ("confirmed-yes", "\"Unlimited re-entry will be available until the start of level 9\"",
                dict(fee=65, staff=25, pool=510, stack=35000, level_min=30)),
  "400 PLO": ("confirmed-yes", "\"Unlimited re-entry will be available until the start of level 9 (approximately 5:30 p.m.)\"",
              dict(fee=45, staff=18, pool=337, stack=30000, level_min=30)),
  "600 Limit Omaha 8/Stud 8": ("confirmed-yes", "\"Unlimited re-entry will be available until the start of level 9\"",
                               dict(fee=65, staff=25, pool=510, stack=35000, level_min=30)),
  "1100 PLO": ("confirmed-yes", "\"Unlimited re-entry will be available until the start of level 9 (approximately 5:30 p.m.)\"",
               dict(fee=85, staff=45, pool=975, stack=30000, level_min=30)),
  "1600 NLH": ("confirmed-yes",
               "\"Unlimited re-entry for each starting flight will be available until the start of level 10\"",
               dict(fee=120, staff=50, pool=1430, stack=40000, level_min=40)),
}
def num(x):
    x = (x or "").replace("$", "").replace(",", "").strip()
    try: return int(float(x))
    except ValueError: return None

for i, r in enumerate(wpt_rows):
    ev = (r.get("event_name") or "").strip()
    note = (r.get("re_entry") or "").strip()
    matched = None
    for k, v in wpt_confirmed.items():
        if k.lower() in ev.lower(): matched = (k, v)
    if matched:
        stt, excerpt, det = matched[1]
        rules = dict(single_entry="confirmed-no", reentry="confirmed-yes",
                     rebuy="unverified", addon="unverified", excerpt=excerpt,
                     source_url=src("W_WPT_TC"), retrieved=TODAY, status="confirmed")
        fee, staff, pool, stack, lvl = det["fee"], det["staff"], det["pool"], det["stack"], det["level_min"]
        fl = ["WPT series; unlimited re-entry confirmed (official sheet read 2026-11-17)"]
    elif note.startswith("NOT CAPTURED"):
        rules = dict(single_entry="unverified", reentry="unverified", rebuy="unverified",
                     addon="unverified",
                     excerpt="Entry terms not captured from an official sheet",
                     source_url=src("W_WPT_TC"), retrieved=TODAY, status="unverified")
        fee = staff = pool = stack = lvl = None
        fl = ["WPT series; entry rules unverified — not eligible for the single-entry section"]
    else:
        # captured from official schedule/structures in a prior research pass; not re-read this session
        rules = dict(single_entry="prior-capture", reentry="prior-capture", rebuy="prior-capture",
                     addon="prior-capture",
                     excerpt=note + " (recorded from official Wynn sources in the 2026-11-16 research pass; "
                                    "excerpt not re-read on 2026-11-17)",
                     source_url=src("W_WPT_SCHED"), retrieved="2026-11-16", status="prior-capture")
        fee = staff = pool = stack = lvl = None
        fl = ["WPT series; entry rule per prior official capture — re-check the sheet before spending"]
    buy = (r.get("buy_in_usd") or "").strip()
    gtd = (r.get("guarantee_usd") or "").strip()
    events.append(dict(id="WPT-%d" % (i+1), venue="Wynn", series="WPT World Championship 2026",
        date=(r.get("dates") or "").strip() or None, weekday=None,
        time=None, event_no=None, name=ev,
        game=("Mixed" if any(x in ev for x in ("TORSE","Triple","Omaha","HORSE")) else
              ("PLO" if "PLO" in ev else "NLH")),
        kind="multi-flight" if "flight" in note.lower() else
             ("multi-day" if (" - " in (r.get("dates") or "") or "&" in (r.get("dates") or "")) else "one-day"),
        buy_in=num(buy), guarantee=num(gtd), guarantee_note=None,
        house_fee=fee, staff_fee=staff, prize_pool_per_entry=pool,
        start_stack=stack, level_minutes=lvl,
        late_reg=None, bounty=("Mystery Bounty" if "Mystery" in ev else None),
        sheet_note=note or None,
        entry_rules=rules, source_url=src("W_WPT_SCHED"), structure_url=src("W_WPT_TC"),
        last_checked=TODAY, flags=fl))

# Bellagio weekly events (official PDFs fetched 2026-11-17)
events.append(dict(id="BELL-FRI", venue="Bellagio", series="Bellagio Weekly",
    date=None, weekday="Fri", days="Fri", time="11:00", event_no=None,
    name="$600 NLH (Fridays)", game="NLH", kind="one-day", buy_in=600, guarantee=None,
    guarantee_note=None, house_fee=50, staff_fee=40, prize_pool_per_entry=510,
    start_stack=30000, level_minutes=30,
    late_reg="re-entry window closes end of level 8 (incl. break)",
    bounty=None, sheet_note="Voluntary $40 staff gratuity adds 15,000 chips (15,000 + 15,000)",
    entry_rules=dict(single_entry="confirmed-no", reentry="confirmed-yes", rebuy="confirmed-no",
        addon="confirmed-no",
        excerpt="\"Players may buy-in and re-enter through the end of level 8 (Including Break). Tournament Surrender is allowed on Level 8 break.\"",
        source_url=src("B_FRI"), retrieved=TODAY, status="confirmed"),
    source_url=src("B_PAGE"), structure_url=src("B_FRI"), last_checked=TODAY,
    flags=["voluntary $40 staff gratuity grants +15,000 chips (spending advantage)"]))
events.append(dict(id="BELL-SAT", venue="Bellagio", series="Bellagio Weekly",
    date=None, weekday="Sat", days="Sat", time="11:00", event_no=None,
    name="Saturday NLH (buy-in conflict on sheet)", game="NLH", kind="multi-flight",
    buy_in=None, guarantee=50000,
    guarantee_note="Combined prize pool guaranteed at least $50,000",
    house_fee=None, staff_fee=40, prize_pool_per_entry=None,
    start_stack=40000, level_minutes=30,
    late_reg="start of Level 10 (per sheet)", bounty=None,
    sheet_note=("Sheet header says $1,100 buy-in; rules text says '$600 Buy-in, $510 … $50 Admin'; "
                "mentions a stale 'Day 2 (9/13/26)' date. Value left blank pending venue confirmation."),
    entry_rules=dict(single_entry="unverified", reentry="unverified", rebuy="unverified",
        addon="unverified", excerpt="Sheet states no re-entry terms; registration until start of Level 10",
        source_url=src("B_SAT"), retrieved=TODAY, status="unverified"),
    source_url=src("B_PAGE"), structure_url=src("B_SAT"), last_checked=TODAY,
    flags=["BUY-IN CONFLICT $1,100 (header) vs $600 (rules) — do not book on this row",
           "stale Day 2 date 9/13/26 on sheet", "entry rules not stated"]))
events.append(dict(id="BELL-SUN", venue="Bellagio", series="Bellagio Weekly",
    date=None, weekday="Sun", days="Sun", time="11:00", event_no=None,
    name="$400 H.O.R.S.E. (Sundays)", game="H.O.R.S.E.", kind="one-day", buy_in=400,
    guarantee=None, guarantee_note=None, house_fee=35, staff_fee=25, prize_pool_per_entry=340,
    start_stack=30000, level_minutes=30,
    late_reg="re-entry window closes end of level 8 (incl. break)", bounty=None,
    sheet_note="Voluntary $25 staff gratuity adds 15,000 chips; Players Club card required",
    entry_rules=dict(single_entry="confirmed-no", reentry="confirmed-yes", rebuy="confirmed-no",
        addon="confirmed-no",
        excerpt="\"Players may buy-in and re-enter through the end of level 8 (Including Break). Tournament Surrender is allowed on Level 8 break.\"",
        source_url=src("B_SUN"), retrieved=TODAY, status="confirmed"),
    source_url=src("B_PAGE"), structure_url=src("B_SUN"), last_checked=TODAY,
    flags=["voluntary $25 staff gratuity grants +15,000 chips (spending advantage)"]))

# Caesars Palace daily (official flyer, fetched 2026-11-17)
for cid, tm, buy, pool, fee in [("CAES-10", "10:00", 100, 70, 30),
                                ("CAES-14", "14:00", 160, 115, 45),
                                ("CAES-18", "18:00", 100, 70, 30),
                                ("CAES-21", "21:00", 160, 115, 45)]:
    events.append(dict(id=cid, venue="Caesars Palace", series="Caesars Palace Daily",
        date=None, weekday=None, days="Mon,Tue,Wed,Thu,Fri,Sat,Sun", time=tm,
        event_no=None, name="$%d NLH Daily (optional $50 add-on)" % buy, game="NLH",
        kind="one-day", buy_in=buy, guarantee=1000, guarantee_note=None,
        house_fee=fee, staff_fee=0, prize_pool_per_entry=pool, start_stack=20000,
        level_minutes=20, late_reg="start of level 7", bounty=None,
        sheet_note="Optional $50 add-on for 15,000 chips, first break only ($45 to pool)",
        entry_rules=dict(single_entry="confirmed-no", reentry="confirmed-yes",
            rebuy="confirmed-no", addon="confirmed-yes",
            excerpt=("\"All Tournaments feature a $50 add-on for 15,000 tournament chips that can only be "
                     "taken at the first break\"; \"may re-enter, by paying the entry fee, upon elimination "
                     "within the first break of play\""),
            source_url=src("C_FLYER"), retrieved=TODAY, status="confirmed"),
        source_url=src("C_FLYER"), structure_url=src("C_FLYER"), last_checked=TODAY,
        flags=["$50 add-on available (spending advantage)", "re-entry within first break"]))

w("events.json", {"generated": TODAY,
    "policy": ("Entry-rule labels: 'confirmed-yes'/'confirmed-no' only where an official structure sheet or "
               "terms PDF states the rule with quoted text. 'unverified' means no official statement found; "
               "absence of re-entry language is NOT proof of single entry."),
    "events": events})

# --------------------------------------------------------------- hotels.json
hotels = [
 dict(id="venetian", name="The Venetian Resort (Venetian & Palazzo towers)",
    address="3355 Las Vegas Blvd S, Las Vegas, NV 89109",
    resort_fee=55.0, resort_fee_source="V_FEE", tax_rate=0.1338, tax_source="V_TERMS",
    parking="Self-park $20/day (hotel guests); $20 Mon–Thu / $25 Fri–Sun (non-guests); valet $40/day; Venetian Rewards Sapphire+ free self-park",
    parking_source="V_TERMS",
    cancellation="Prepaid offers non-cancellable; standard deposit = first night or full stay; early departure fee $100 + tax; $150/night incidental hold",
    cancellation_source="V_TERMS",
    poker_rate="Official poker suite rate from $119/$209 (code EPOKR25) — requires 6h live cash play or a $300+ tournament buy-in per night; subject to availability",
    poker_rate_source="V_POKER_RATE",
    booking_url="https://www.venetianlasvegas.com/book",
    venue_walk="0 min (host venue — poker room at Palazzo Level 2)",
    last_checked=TODAY, flags=[]),
 dict(id="wynn", name="Wynn Las Vegas / Encore",
    address="3131 Las Vegas Blvd S, Las Vegas, NV 89109",
    resort_fee=55.0, resort_fee_source="W_TERMS", tax_rate=0.1338, tax_source="V_TERMS",
    parking="Complimentary self-parking for up to 2 vehicles included with resort fee",
    parking_source="W_TERMS",
    cancellation="Offer-specific (the fetched terms page covers a Nov 2026 package: full prepaid, non-cancellable); standard-rate cancellation terms not confirmed — flagged",
    cancellation_source="W_TERMS",
    poker_rate=None, poker_rate_source=None,
    booking_url="https://www.wynnlasvegas.com/",
    venue_walk="0 min for Wynn daily/WPT (poker room located in Encore)",
    last_checked=TODAY,
    flags=["standard (non-offer) cancellation terms unverified"]),
 dict(id="bellagio", name="Bellagio",
    address="3600 Las Vegas Blvd S, Las Vegas, NV 89109",
    resort_fee=55.0, resort_fee_source="B_TERMS", tax_rate=0.1338, tax_source="V_TERMS",
    parking="Self-park $20/day (hotel guests, all week); $20 Mon–Thu / $25 Fri–Sun (non-guests); valet $40/day; free for MGM Rewards Pearl+",
    parking_source="MGM_PARK",
    cancellation="First-night deposit fully refundable if cancelled ≥72 h before arrival; later cancellation forfeits first night",
    cancellation_source="B_TERMS",
    poker_rate=None, poker_rate_source=None,
    booking_url="https://bellagio.mgmresorts.com/en/rooms.html",
    venue_walk="~22 min walk to Venetian poker room (map estimate)",
    last_checked=TODAY, flags=[]),
 dict(id="aria", name="ARIA Resort & Casino",
    address="3708 Las Vegas Blvd S, Las Vegas, NV 89109",
    resort_fee=55.0, resort_fee_source="A_TERMS", tax_rate=0.1338, tax_source="V_TERMS",
    parking="Self-park $20/day (hotel guests); $20 Mon–Thu / $25 Fri–Sun (non-guests); valet $40/day",
    parking_source="MGM_PARK",
    cancellation="First-night deposit refundable if cancelled ≥72 h before arrival; later cancellation forfeits first night",
    cancellation_source="A_TERMS",
    poker_rate=None, poker_rate_source=None,
    booking_url="https://aria.mgmresorts.com/en/rooms.html",
    venue_walk="~18 min walk to Venetian poker room (map estimate)",
    last_checked=TODAY,
    flags=["prior snapshot said $50 fee; official page now states $55 — resolved to $55 (see change log)"]),
 dict(id="ti", name="Treasure Island (TI)",
    address="3300 Las Vegas Blvd S, Las Vegas, NV 89109",
    resort_fee=49.95, resort_fee_source="TI_ROOMS", tax_rate=0.1338, tax_source="V_TERMS",
    parking="Free valet & self-park garage for hotel guests (included)",
    parking_source="TI_ROOMS",
    cancellation="Not captured from official page — flagged",
    cancellation_source=None,
    poker_rate=None, poker_rate_source=None,
    booking_url="https://treasureisland.com/hotel/deluxe-rooms",
    venue_walk="~12 min walk to Venetian poker room (map estimate)",
    last_checked=TODAY,
    flags=["'$69/night + no resort fee' TV Ad Special exists (My TI members) — see official offers"]),
 dict(id="caesars", name="Caesars Palace",
    address="3570 Las Vegas Blvd S, Las Vegas, NV 89109",
    resort_fee=None, resort_fee_source=None, tax_rate=0.1338, tax_source="V_TERMS",
    parking="Not captured from official page — flagged", parking_source=None,
    cancellation="Homepage advertises 'FREE 48-Hour Cancellation' on direct bookings (banner, 2026-11-17); offer terms apply",
    cancellation_source="C_HOME",
    poker_rate=None, poker_rate_source=None,
    booking_url="https://www.caesars.com/book/?propcode=CLV",
    venue_walk="~16 min walk to Venetian poker room (map estimate)",
    last_checked=TODAY,
    flags=["resort fee NOT confirmed on official page (secondary sources conflict $49.95 vs $54.95) — left blank"]),
 dict(id="parkmgm", name="Park MGM",
    address="3770 Las Vegas Blvd S, Las Vegas, NV 89109",
    resort_fee=None, resort_fee_source=None, tax_rate=0.1338, tax_source="V_TERMS",
    parking="Self-park $20/day (hotel guests); $20 Mon–Thu / $25 Fri–Sun (non-guests); valet $40/day",
    parking_source="MGM_PARK",
    cancellation="Not captured — flagged", cancellation_source=None,
    poker_rate=None, poker_rate_source=None,
    booking_url="https://parkmgm.mgmresorts.com/en/rooms.html",
    venue_walk="~32 min walk to Venetian poker room (map estimate — over the 30-minute limit)",
    last_checked=TODAY,
    flags=["resort fee not extracted from official terms — blank", "walk over 30 min limit"]),
 dict(id="harrahs", name="Harrah's Las Vegas",
    address="3475 Las Vegas Blvd S, Las Vegas, NV 89109",
    resort_fee=None, resort_fee_source=None, tax_rate=0.1338, tax_source="V_TERMS",
    parking="Not captured — flagged", parking_source=None,
    cancellation="Not captured — flagged", cancellation_source=None,
    poker_rate=None, poker_rate_source=None,
    booking_url="https://www.caesars.com/harrahs-las-vegas",
    venue_walk="~10 min walk to Venetian poker room (map estimate)",
    last_checked=TODAY,
    flags=["fee/rate not confirmed on official page — blank"]),
 dict(id="horseshoe", name="Horseshoe Las Vegas",
    address="3645 Las Vegas Blvd S, Las Vegas, NV 89109",
    resort_fee=None, resort_fee_source=None, tax_rate=0.1338, tax_source="V_TERMS",
    parking="Not captured — flagged", parking_source=None,
    cancellation="Not captured — flagged", cancellation_source=None,
    poker_rate=None, poker_rate_source=None,
    booking_url="https://www.caesars.com/horseshoe-las-vegas",
    venue_walk="~14 min walk to Venetian poker room (map estimate)",
    last_checked=TODAY,
    flags=["fee/rate not confirmed on official page — blank"]),
]
w("hotels.json", {"generated": TODAY,
    "true_cost_formula": "true cost per night = (nightly rate + resort fee) × (1 + 13.38% Clark County room tax)",
    "hotels": hotels})

# ------------------------------------------------------------- rate_log.json
rate_log = [
 dict(hotel="venetian", date_checked=TODAY, rate_type="poker-rate (conditional)",
      nightly_rate=119.0, resort_fee=55.0, tax_rate=0.1338,
      nightly_avg=None, checkout_total=None,
      parking=20.0, cancellation_deadline="prepaid/non-cancellable (offer terms)",
      rate_timestamp=TODAY + "T00:00:00-08:00",
      source_url=src("V_POKER_RATE"),
      note="Official poker rate 'as low as $119' ($209 Palazzo tier); not a dated quote; requires qualifying play"),
 dict(hotel="venetian", date_checked=TODAY, rate_type="published-lead",
      nightly_rate=209.0, resort_fee=55.0, tax_rate=0.1338,
      nightly_avg=None, checkout_total=None,
      parking=20.0, cancellation_deadline="prepaid/non-cancellable (offer terms)",
      rate_timestamp=TODAY + "T00:00:00-08:00",
      source_url=src("V_POKER_RATE"),
      note="Palazzo-tier poker rate start; conditional on qualifying play"),
 dict(hotel="ti", date_checked=TODAY, rate_type="published-lead (member offer)",
      nightly_rate=69.0, resort_fee=0.0, tax_rate=0.1338,
      nightly_avg=None, checkout_total=None,
      parking=0.0, cancellation_deadline="not captured",
      rate_timestamp=TODAY + "T00:00:00-08:00",
      source_url=src("TI_ROOMS"),
      note="'$69/night + no resort fee' TV Ad Special for My TI Guestbook members; standard fee is $49.95+tax"),
 dict(hotel="caesars", date_checked=TODAY, rate_type="published-lead",
      nightly_rate=139.0, resort_fee=None, tax_rate=0.1338,
      nightly_avg=None, checkout_total=None,
      parking=None, cancellation_deadline="'FREE 48-Hour Cancellation' banner (direct bookings)",
      rate_timestamp=TODAY + "T00:00:00-08:00",
      source_url=src("C_HOME"),
      note="Homepage 'Rooms from $186 $139' Cyber Monday banner; not a dated quote; resort fee still unverified"),
]
w("rate_log.json", {"generated": TODAY,
    "schema_note": ("Dated log, not single values. checkout_total/nightly_avg filled only for a like-for-like "
                    "dated booking quote (same dates, same room, tax and fee included); null otherwise. "
                    "Every entry keeps its rate_timestamp."),
    "entries": rate_log})

# --------------------------------------------------------------- walks.json
def gmaps(a, b):
    return "https://www.google.com/maps/dir/?api=1&origin=%s&destination=%s&travelmode=walking" % (
        a.replace(" ", "+"), b.replace(" ", "+"))
walks = []
pairs = [
 ("venetian", "The Venetian Resort, 3355 Las Vegas Blvd S", "Venetian Poker Room (Palazzo Level 2)", 0, "host venue"),
 ("wynn", "Wynn Las Vegas, 3131 Las Vegas Blvd S", "Venetian Poker Room, 3355 Las Vegas Blvd S", 14, "≤30"),
 ("ti", "Treasure Island, 3300 Las Vegas Blvd S", "Venetian Poker Room, 3355 Las Vegas Blvd S", 12, "≤30"),
 ("bellagio", "Bellagio, 3600 Las Vegas Blvd S", "Venetian Poker Room, 3355 Las Vegas Blvd S", 22, "≤30"),
 ("aria", "ARIA, 3708 Las Vegas Blvd S", "Venetian Poker Room, 3355 Las Vegas Blvd S", 18, "≤30"),
 ("caesars", "Caesars Palace, 3570 Las Vegas Blvd S", "Venetian Poker Room, 3355 Las Vegas Blvd S", 16, "≤30"),
 ("harrahs", "Harrah's, 3475 Las Vegas Blvd S", "Venetian Poker Room, 3355 Las Vegas Blvd S", 10, "≤30"),
 ("horseshoe", "Horseshoe Las Vegas, 3645 Las Vegas Blvd S", "Venetian Poker Room, 3355 Las Vegas Blvd S", 14, "≤30"),
 ("parkmgm", "Park MGM, 3770 Las Vegas Blvd S", "Venetian Poker Room, 3355 Las Vegas Blvd S", 32, ">30"),
 ("wynn", "Wynn Las Vegas, 3131 Las Vegas Blvd S", "Wynn Poker Room (Encore), 3131 Las Vegas Blvd S", 0, "host venue"),
 ("bellagio", "Bellagio, 3600 Las Vegas Blvd S", "Wynn Poker Room (Encore), 3131 Las Vegas Blvd S", 34, ">30"),
 ("ti", "Treasure Island, 3300 Las Vegas Blvd S", "Wynn Poker Room (Encore), 3131 Las Vegas Blvd S", 16, "≤30"),
 ("venetian", "The Venetian Resort, 3355 Las Vegas Blvd S", "Wynn Poker Room (Encore), 3131 Las Vegas Blvd S", 14, "≤30"),
 ("bellagio", "Bellagio, 3600 Las Vegas Blvd S", "Bellagio Poker Room, 3600 Las Vegas Blvd S", 0, "host venue"),
 ("caesars", "Caesars Palace, 3570 Las Vegas Blvd S", "Caesars Palace Poker Room, 3570 Las Vegas Blvd S", 0, "host venue"),
]
for hid, o, d, mins, status in pairs:
    walks.append(dict(hotel_id=hid, origin_address=o, destination_address=d,
        walk_minutes_estimate=mins, status=status,
        maps_url=gmaps(o, d),
        verified="estimate — no official source publishes walking minutes; Google Maps link given for live verification",
        last_checked=TODAY))
w("walks.json", {"generated": TODAY, "walks": walks})

# ------------------------------------------------- change_log / snapshots
change_log = [
 dict(date=TODAY, source_id="A_TERMS", url=src("A_TERMS"),
      row_ref="hotel:aria", field="resort_fee",
      change="Earlier snapshot recorded $50 (PokerNews/secondary) vs $55; official ARIA terms page states $55.00 + tax. Row corrected to $55 (official).",
      severity="corrected"),
 dict(date=TODAY, source_id="B_SAT", url=src("B_SAT"),
      row_ref="event:BELL-SAT", field="buy_in",
      change="Official Saturday sheet is internally inconsistent: header '$1100 BUY-IN' vs rule 07 '$600 Buy-in'; sheet also carries a stale Day 2 date (9/13/26). Buy-in left blank and row flagged.",
      severity="flagged"),
 dict(date=TODAY, source_id="V_STRUCTURE_25", url=vstruct("dse_nov_2026-structure_25.pdf"),
      row_ref="event:V-*,46", field="time",
      change="Structure sheet 25 lists Event #46 start at 9:10 AM — earlier than the 10:10 AM previously recorded as the series' earliest start. Row set added.",
      severity="updated"),
 dict(date=TODAY, source_id="V_STRUCTURE_8", url=vstruct("dse_nov_2026-structure_8.pdf"),
      row_ref="event:V-*,18", field="entry_rules",
      change="Valuetown Bounty sheet rule 07 prices 'all subsequent buy in's after the initial buy in' at $200 — multi-entry implied; row excluded from single-entry candidates and excerpt stored.",
      severity="flagged"),
 dict(date=TODAY, source_id="W_DAILY", url=src("W_DAILY"),
      row_ref="event:WYNN-*", field="entry_rules",
      change="Wynn daily PDF terms confirm re-entry (Mon–Thu, Sat–Sun, Nightly) and confirm rebuy/add-on (Friday). Rows relabeled from unverified to confirmed; moved to spending-advantage section.",
      severity="updated"),
 dict(date=TODAY, source_id="C_FLYER", url=src("C_FLYER"),
      row_ref="event:CAES-*", field="entry_rules",
      change="Caesars flyer confirms $50 add-on (first break) and re-entry within first break for all four dailies. Rows relabeled confirmed.",
      severity="updated"),
]
w("change_log.json", {"generated": TODAY, "entries": change_log})

# source snapshot manifest for the scheduled monitor
snaps = {}
for k, (label, url) in S.items():
    snaps[url] = {"source_id": k, "label": label, "fetched_at": TODAY + "T00:00:00Z",
                  "sha256": None, "excerpt": None,
                  "note": "baseline manifest created by this research pass; hash filled by first monitor run"}
w("source_snapshots.json", {"generated": TODAY, "snapshots": snaps})

print("events:", len(events))
print("hotels:", len(hotels))
print("rate_log:", len(rate_log))
print("walks:", len(walks))
print("sources:", len(S))
