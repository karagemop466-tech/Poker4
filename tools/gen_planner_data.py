#!/usr/bin/env python3
"""Generate planner/assets/data.js from the verified Venetian DSE IV dataset.

All event facts below were read on 2026-11-17 from the official Venetian
DeepStack Extravaganza IV schedule page and its 37 official structure PDFs:
  https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html
Structure PDFs: https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_N.pdf

No value is inferred. Where a structure sheet does not state a value (e.g. a
guarantee for the RaceDay events, or re-entry/add-on terms anywhere except
structure_8), the field is null and flagged.
"""
import json, os

BASE = "https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures"
SCHED_URL = "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"
RETRIEVED = "2026-11-17"

# Per-structure-sheet facts, read directly from each official PDF.
# cat: single | bounty | pko | flight | satellite | seniors | ladies | tag_team | raceday
S = {
 1:  dict(cat="bounty",    buyin=200,  fee=40,  pool=160, chips=25000, lvl=30, latereg="8 levels (~9:40 PM)",  pays=12.5, guar=8000,  bounty="$50 per elimination"),
 2:  dict(cat="flight",    buyin=400,  fee=70,  pool=330, chips=40000, lvl=40, latereg="9 levels (5:55 PM)",     pays=12.5, guar=75000, flights="1A/1B + Day 2"),
 3:  dict(cat="flight",    buyin=400,  fee=70,  pool=330, chips=40000, lvl=40, latereg="9 levels (5:55 PM)",     pays=12.5, guar=75000, flights="1A/1B/1C + Day 2"),
 4:  dict(cat="flight",    buyin=600,  fee=95,  pool=505, chips=40000, lvl=40, latereg="9 levels (5:55 PM)",     pays=12.5, guar=150000, flights="1A/1B/1C + Day 2", discount="$20 early-register discount (Day 1A)"),
 5:  dict(cat="single",    buyin=300,  fee=58,  pool=242, chips=40000, lvl=30, latereg="10 levels (~4:55 PM)",   pays=12.5, guar=10000),
 6:  dict(cat="single",    buyin=400,  fee=65,  pool=335, chips=40000, lvl=30, latereg="10 levels (~4:55 PM)",   pays=12.5, guar=15000),
 7:  dict(cat="single",    buyin=600,  fee=90,  pool=510, chips=40000, lvl=30, latereg="10 levels (~4:55 PM)",   pays=12.5, guar=30000),
 8:  dict(cat="bounty",    buyin=200,  fee=40,  pool=160, chips=25000, lvl=30, latereg="8 levels (9:40 PM)",     pays=12.5, guar=20000, bounty="$50 per elimination", discount="PokerAtlas PRO $20 rake discount on initial buy-in"),
 9:  dict(cat="flight",    buyin=300,  fee=60,  pool=240, chips=30000, lvl=30, latereg="6 levels (~8:40 PM)",    pays=12.5, guar=75000, flights="1B/1D + Day 2"),
 10: dict(cat="flight",    buyin=300,  fee=60,  pool=240, chips=30000, lvl=40, latereg="6 levels (~3:40 PM)",    pays=12.5, guar=75000, flights="1A/1C + Day 2"),
 11: dict(cat="bounty",    buyin=600,  fee=90,  pool=510, chips=40000, lvl=30, latereg="10 levels (4:55 PM)",    pays=12.5, guar=30000, bounty="$200 to start / $500 in the money"),
 12: dict(cat="flight",    buyin=800,  fee=110, pool=690, chips=40000, lvl=40, latereg="6 levels (~3:40 PM)",    pays=12.5, guar=500000, flights="1A/1C/1E + Day 2"),
 13: dict(cat="flight",    buyin=800,  fee=110, pool=690, chips=40000, lvl=30, latereg="6 levels (~8:40 PM)",    pays=12.5, guar=500000, flights="1B/1D + Day 2"),
 14: dict(cat="flight",    buyin=800,  fee=110, pool=690, chips=40000, lvl=20, latereg="6 levels (~7:25 PM)",    pays=12.5, guar=500000, flights="1F Turbo + Day 2"),
 15: dict(cat="bounty",    buyin=300,  fee=50,  pool=250, chips=25000, lvl=30, latereg="8 levels (9:40 PM)",     pays=12.5, guar=15000, bounty="$100 per elimination"),
 16: dict(cat="bounty",    buyin=800,  fee=100, pool=700, chips=40000, lvl=30, latereg="10 levels (4:55 PM)",    pays=12.5, guar=75000, bounty="$200 to start / $500 in the money"),
 17: dict(cat="seniors",   buyin=600,  fee=90,  pool=510, chips=40000, lvl=30, latereg="10 levels (~3:55 PM)",   pays=15.0, guar=40000, eligibility="Must be 50+"),
 18: dict(cat="raceday",   buyin=200,  fee=35,  pool=165, chips=30000, lvl=20, latereg="6 levels (~12:25 PM)",   pays=12.5, guar=None),
 19: dict(cat="satellite", buyin=100,  fee=20,  pool=80,  chips=20000, lvl=20, latereg="6 levels (~6:25 PM)",    pays=None, guar="2 Seats", prize="Direct entry to Event #39"),
 20: dict(cat="seniors",   buyin=1100, fee=140, pool=960, chips=40000, lvl=40, latereg="9 levels (~4:55 PM)",   pays=15.0, guar=300000, eligibility="Must be 50+", flights="1A/1B + Day 2"),
 21: dict(cat="flight",    buyin=2200, fee=225, pool=1975,chips=40000, lvl=40, latereg="9 levels (~4:55 PM)",   pays=12.5, guar=1000000, flights="Day 1A + Day 2 + Day 3"),
 22: dict(cat="single",    buyin=300,  fee=58,  pool=242, chips=30000, lvl=30, latereg="8 levels (~4:40 PM)",   pays=12.5, guar=10000, variant="Double Board Bomb Pot"),
 23: dict(cat="single",    buyin=600,  fee=90,  pool=510, chips=30000, lvl=30, latereg="8 levels (~4:40 PM)",   pays=12.5, guar=25000, variant="Double Board Bomb Pot"),
 24: dict(cat="satellite", buyin=260,  fee=40,  pool=220, chips=20000, lvl=20, latereg="6 levels (~6:25 PM)",    pays=None, guar="2 Seats", prize="Direct entry to Event #47"),
 25: dict(cat="satellite", buyin=260,  fee=35,  pool=225, chips=20000, lvl=15, latereg="6 levels",              pays=None, guar="2 Seats", prize="Direct entry to Event #47 (Turbo)"),
 26: dict(cat="bounty",    buyin=400,  fee=60,  pool=340, chips=30000, lvl=30, latereg="8 levels (~4:40 PM)",   pays=12.5, guar=15000, bounty="$100 per elimination"),
 27: dict(cat="bounty",    buyin=600,  fee=90,  pool=510, chips=30000, lvl=30, latereg="8 levels (~4:40 PM)",   pays=12.5, guar=25000, bounty="$200 per elimination"),
 28: dict(cat="single",    buyin=600,  fee=90,  pool=510, chips=30000, lvl=30, latereg="8 levels (~4:40 PM)",   pays=12.5, guar=25000, variant="BIG O (5-card Omaha)"),
 29: dict(cat="single",    buyin=200,  fee=40,  pool=160, chips=30000, lvl=30, latereg="8 levels (~3:40 PM)",   pays=12.5, guar=None),
 30: dict(cat="pko",       buyin=200,  fee=40,  pool=160, chips=25000, lvl=30, latereg="8 levels (9:40 PM)",    pays=12.5, guar=8000),
 31: dict(cat="tag_team",  buyin=600,  fee=90,  pool=510, chips=40000, lvl=30, latereg="8 levels (~2:40 PM)",   pays=12.5, guar=10000, teams="Female/Female or Female/Male; $10 LIPS fee"),
 32: dict(cat="ladies",    buyin=800,  fee=110, pool=690, chips=40000, lvl=40, latereg="9 levels (~4:55 PM)",   pays=None, guar=40000, eligibility="Female 21+; $20 LIPS fee", flights="Day 1 + Day 2 + Final Table"),
 33: dict(cat="bounty",    buyin=600,  fee=90,  pool=510, chips=40000, lvl=30, latereg="10 levels (4:55 PM)",   pays=12.5, guar=30000, bounty="$200 per elimination", discount="$10 LIPS fee"),
 34: dict(cat="pko",       buyin=1100, fee=130, pool=970, chips=40000, lvl=30, latereg="10 levels (4:55 PM)",   pays=12.5, guar=75000),
 35: dict(cat="flight",    buyin=1100, fee=140, pool=960, chips=40000, lvl=40, latereg="9 levels (~4:55 PM)",   pays=12.5, guar=500000, flights="1A/1C/1E + Day 2", discount="$40 early-register discount (Day 1A)"),
 36: dict(cat="flight",    buyin=1100, fee=140, pool=960, chips=40000, lvl=30, latereg="9 levels (~11:10 PM)", pays=12.5, guar=500000, flights="1B/1D + Day 2", discount="$40 early-register discount (Day 1B)"),
 37: dict(cat="flight",    buyin=2200, fee=225, pool=1975,chips=40000, lvl=30, latereg="9 levels (~11:10 PM)", pays=12.5, guar=1000000, flights="Day 1B + Day 2 + Day 3"),
}

# (date, time, start24, event_no, name, sheet, guar_override)
ROWS = [
 ("2026-11-16","11:10 AM","11:10",1,"$300 No Limit Hold'em 1A $75K GTD",10,None),
 ("2026-11-16","5:10 PM","17:10",1,"$300 No Limit Hold'em 1B $75K GTD",9,None),
 ("2026-11-17","11:10 AM","11:10",1,"$300 No Limit Hold'em 1C $75K GTD",10,None),
 ("2026-11-17","5:10 PM","17:10",1,"$300 No Limit Hold'em 1D $75K GTD",9,None),
 ("2026-11-18","11:10 AM","11:10",2,"$300 No Limit Hold'em $10K GTD (1Day)",5,None),
 ("2026-11-18","12:00 PM","12:00",1,"$300 No Limit Hold'em Day 2 Restart",10,None),
 ("2026-11-19","10:10 AM","10:10",3,"$200 NLH RaceDay Stack (1Day)",18,None),
 ("2026-11-20","10:10 AM","10:10",4,"$200 NLH RaceDay Stack (1Day)",18,None),
 ("2026-11-21","10:10 AM","10:10",5,"$200 NLH RaceDay Stack (1Day)",18,None),
 ("2026-11-22","11:10 AM","11:10",6,"$200 No Limit Hold'em (1Day)",29,None),
 ("2026-11-23","11:10 AM","11:10",7,"$400 No Limit Hold'em 1A $75K GTD",2,None),
 ("2026-11-23","5:10 PM","17:10",8,"$200 No Limit Hold'em $8K GTD (1Day) PKO",30,None),
 ("2026-11-24","11:10 AM","11:10",7,"$400 No Limit Hold'em 1B $75K GTD",2,None),
 ("2026-11-24","5:10 PM","17:10",9,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-11-25","11:00 AM","11:00",7,"$400 No Limit Hold'em Day 2 Restart",2,None),
 ("2026-11-25","11:10 AM","11:10",10,"$400 No Limit Hold'em $15K GTD (1Day)",6,None),
 ("2026-11-25","5:10 PM","17:10",11,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-11-26","11:10 AM","11:10",12,"$300 No Limit Hold'em $10K GTD (1Day)",5,None),
 ("2026-11-26","5:10 PM","17:10",13,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-11-27","11:10 AM","11:10",14,"$600 No Limit Hold'em $30K GTD (1Day)",7,30000),
 ("2026-11-27","5:10 PM","17:10",15,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-11-28","11:10 AM","11:10",16,"$600 No Limit Hold'em Bounty $30K GTD (1Day)",11,30000),
 ("2026-11-28","12:10 PM","12:10",17,"$400 Pot Limit Omaha Bounty $15K GTD (1Day)",26,None),
 ("2026-11-29","11:10 AM","11:10",18,"$200 NLH PokerAtlas Valuetown Bounty $20K GTD (1Day)",8,None),
 ("2026-11-29","12:10 PM","12:10",20,"$300 Pot Limit Omaha $10K GTD (1Day) Double Board Bomb Pot",22,None),
 ("2026-11-29","5:10 PM","17:10",21,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-11-30","11:10 AM","11:10",19,"$400 No Limit Hold'em 1A $75K GTD",3,None),
 ("2026-11-30","5:10 PM","17:10",22,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-12-01","11:10 AM","11:10",19,"$400 No Limit Hold'em 1C $75K GTD",3,None),
 ("2026-12-01","5:10 PM","17:10",23,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-12-02","10:10 AM","10:10",24,"$600 No Limit Hold'em Seniors $40K GTD (1Day)",17,None),
 ("2026-12-02","11:00 AM","11:00",19,"$400 No Limit Hold'em Day 2 Restart",3,None),
 ("2026-12-02","5:10 PM","17:10",25,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-12-03","11:10 AM","11:10",26,"$800 No Limit Hold'em 1A $500K GTD",12,None),
 ("2026-12-03","12:10 PM","12:10",27,"$600 BIG O $25K GTD (1Day)",28,None),
 ("2026-12-03","5:10 PM","17:10",26,"$800 No Limit Hold'em 1B $500K GTD",13,None),
 ("2026-12-04","11:10 AM","11:10",26,"$800 No Limit Hold'em 1C $500K GTD",12,None),
 ("2026-12-04","5:10 PM","17:10",26,"$800 No Limit Hold'em 1D $500K GTD",13,None),
 ("2026-12-05","11:10 AM","11:10",26,"$800 No Limit Hold'em 1E $500K GTD",12,None),
 ("2026-12-05","5:10 PM","17:10",26,"$800 No Limit Hold'em 1F (Turbo) $500K GTD",14,None),
 ("2026-12-06","11:10 AM","11:10",28,"$600 No Limit Hold'em $40K GTD (1Day)",7,40000),
 ("2026-12-06","12:00 PM","12:00",26,"$800 No Limit Hold'em Day 2 Restart",12,None),
 ("2026-12-06","5:10 PM","17:10",29,"$300 No Limit Hold'em Bounty $15K GTD (1Day)",15,None),
 ("2026-12-07","11:10 AM","11:10",30,"$600 No Limit Hold'em Bounty $40K GTD (1Day)",11,40000),
 ("2026-12-07","5:10 PM","17:10",31,"$300 No Limit Hold'em Bounty $15K GTD (1Day)",15,None),
 ("2026-12-08","10:10 AM","10:10",32,"$600 No Limit Hold'em Seniors $40K GTD (1Day)",17,None),
 ("2026-12-08","4:10 PM","16:10",33,"$100 NLH LIPS Ladies Milestone Satellite (1Day)",19,None),
 ("2026-12-08","5:10 PM","17:10",34,"$300 No Limit Hold'em Bounty $15K GTD (1Day)",15,None),
 ("2026-12-09","10:10 AM","10:10",35,"$600 NLH LIPS Poker Jingle Tag Team $10K GTD (1Day)",31,None),
 ("2026-12-09","11:10 AM","11:10",36,"$800 No Limit Hold'em Bounty $75K GTD (1Day)",16,None),
 ("2026-12-09","4:10 PM","16:10",37,"$100 NLH LIPS Ladies Milestone Satellite (1Day)",19,None),
 ("2026-12-09","5:10 PM","17:10",38,"$300 No Limit Hold'em Bounty $15K GTD (1Day)",15,None),
 ("2026-12-10","10:10 AM","10:10",39,"$800 No Limit Hold'em LIPS Ladies $40K GTD (2Day)",32,None),
 ("2026-12-10","12:10 PM","12:10",40,"$600 Pot Limit Omaha Bounty $25K GTD (1Day)",27,None),
 ("2026-12-10","4:10 PM","16:10",41,"$260 NLH Milestone Satellite (1Day)",24,None),
 ("2026-12-10","5:10 PM","17:10",42,"$300 No Limit Hold'em Bounty $15K GTD (1Day)",15,None),
 ("2026-12-11","10:00 AM","10:00",39,"$800 No Limit Hold'em LIPS Ladies Day 2 Restart",32,None),
 ("2026-12-11","11:10 AM","11:10",43,"$600 No Limit Hold'em LIPS $30K GTD (1Day)",33,None),
 ("2026-12-11","4:10 PM","16:10",44,"$260 NLH Milestone Satellite (1Day)",24,None),
 ("2026-12-11","7:00 PM","19:00",39,"$800 No Limit Hold'em LIPS Ladies Final Table",32,None),
 ("2026-12-11","8:10 PM","20:10",45,"$260 NLH Turbo Milestone Satellite (1Day)",25,None),
 ("2026-12-12","9:10 AM","9:10",46,"$260 NLH Turbo Milestone Satellite (1Day)",25,None),
 ("2026-12-12","10:10 AM","10:10",47,"$2,200 No Limit Hold'em 1A $1 Mill GTD",21,None),
 ("2026-12-12","12:10 PM","12:10",48,"$260 NLH Turbo Milestone Satellite (1Day)",25,None),
 ("2026-12-12","6:10 PM","18:10",47,"$2,200 No Limit Hold'em 1B $1 Mill GTD",37,None),
 ("2026-12-13","10:10 AM","10:10",49,"$1,100 No Limit Hold'em Seniors 1A $300K GTD",20,None),
 ("2026-12-13","1:00 PM","13:00",47,"$2,200 NLH PokerAtlas Championship Day 2 Restart",21,None),
 ("2026-12-13","5:10 PM","17:10",50,"$300 No Limit Hold'em Bounty $15K GTD (1Day)",15,None),
 ("2026-12-14","10:10 AM","10:10",49,"$1,100 No Limit Hold'em Seniors 1B $300K GTD",20,None),
 ("2026-12-14","11:00 AM","11:00",47,"$2,200 NLH PokerAtlas Championship Day 3 Restart",21,None),
 ("2026-12-14","5:10 PM","17:10",51,"$300 No Limit Hold'em Bounty $15K GTD (1Day)",15,None),
 ("2026-12-15","10:00 AM","10:00",49,"$1,100 No Limit Hold'em Seniors Day 2 Restart",20,None),
 ("2026-12-15","11:10 AM","11:10",52,"$1,100 No Limit Hold'em $75K GTD (1Day) PKO",34,None),
 ("2026-12-15","5:10 PM","17:10",53,"$300 No Limit Hold'em Bounty $15K GTD (1Day)",15,None),
 ("2026-12-16","11:10 AM","11:10",54,"$600 No Limit Hold'em Bounty $50K GTD (1Day)",11,50000),
 ("2026-12-16","5:10 PM","17:10",55,"$300 No Limit Hold'em Bounty $15K GTD (1Day)",15,None),
 ("2026-12-17","10:10 AM","10:10",56,"$1,100 No Limit Hold'em 1A $500K GTD",35,None),
 ("2026-12-17","12:10 PM","12:10",57,"$600 Pot Limit Omaha $25K GTD (1Day) Double Board Bomb Pot",23,None),
 ("2026-12-17","6:10 PM","18:10",56,"$1,100 No Limit Hold'em 1B $500K GTD",36,None),
 ("2026-12-18","10:10 AM","10:10",56,"$1,100 No Limit Hold'em 1C $500K GTD",35,None),
 ("2026-12-18","6:10 PM","18:10",56,"$1,100 No Limit Hold'em 1D $500K GTD",36,None),
 ("2026-12-19","10:10 AM","10:10",56,"$1,100 No Limit Hold'em 1E $500K GTD",35,None),
 ("2026-12-19","5:10 PM","17:10",58,"$200 NLH PokerAtlas Valuetown Bounty $20K GTD (1Day)",8,None),
 ("2026-12-20","11:00 AM","11:00",56,"$1,100 No Limit Hold'em Day 2 Restart",35,None),
 ("2026-12-20","11:10 AM","11:10",59,"$600 No Limit Hold'em 1A $150K GTD",4,None),
 ("2026-12-20","5:10 PM","17:10",60,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-12-21","11:10 AM","11:10",59,"$600 No Limit Hold'em 1B $150K GTD",4,None),
 ("2026-12-21","5:10 PM","17:10",61,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-12-22","11:10 AM","11:10",59,"$600 No Limit Hold'em 1C $150K GTD",4,None),
 ("2026-12-22","5:10 PM","17:10",62,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
 ("2026-12-23","11:00 AM","11:00",59,"$600 No Limit Hold'em Day 2 Restart",4,None),
 ("2026-12-23","11:10 AM","11:10",63,"$600 No Limit Hold'em $30K GTD (1Day)",7,30000),
 ("2026-12-23","5:10 PM","17:10",64,"$200 No Limit Hold'em Bounty $8K GTD (1Day)",1,None),
]

def num(v):
    return v if isinstance(v, (int, float)) else None

events = []
for i, (date, time, s24, evno, name, sheet, gover) in enumerate(ROWS, 1):
    st = S[sheet]
    guar = gover if gover is not None else st["guar"]
    guar_num = num(guar)
    ratio = round(guar_num / st["buyin"], 2) if (guar_num and st["buyin"]) else None
    # single-entry status
    if sheet == 8:
        se = "confirmed NOT single-entry — structure_8 states 'All subsequent buy in's after the initial buy in will be $200' (re-buys permitted)"
        se_confirmed = False
        reentry = "Permitted (implied by 'subsequent buy in's' language)"
        addon = None
    else:
        se = "unverified — structure sheet does not state re-entry/rebuy/add-on terms (omission is not confirmation)"
        se_confirmed = False
        reentry = None
        addon = None
    events.append({
        "id": i,
        "venue": "The Venetian Resort (Venetian / Palazzo)",
        "date": date,
        "time": time,
        "start24": s24,
        "event_no": evno,
        "name": name,
        "buyin": st["buyin"],
        "house_fee": st["fee"],
        "pool_per_entry": st["pool"],
        "guarantee": guar,
        "guarantee_num": guar_num,
        "guarantee_ratio": ratio,
        "start_chips": st["chips"],
        "level_minutes": st["lvl"],
        "late_registration": st["latereg"],
        "pays_pct": st["pays"],
        "category": st["cat"],
        "format_detail": st.get("variant") or st.get("flights") or st.get("bounty") or st.get("eligibility") or st.get("teams") or st.get("prize") or "",
        "structure_sheet": f"{BASE}/dse_nov_2026-structure_{sheet}.pdf",
        "structure_no": sheet,
        "single_entry_confirmed": se_confirmed,
        "single_entry_status": se,
        "reentry": reentry,
        "addon": addon,
        "retrieved": RETRIEVED,
        "last_checked": RETRIEVED,
        "sources": [SCHED_URL, f"{BASE}/dse_nov_2026-structure_{sheet}.pdf"],
    })

# ---- hotels (resort fee / tax verified from official pages; rates unverified) ----
hotels = [
 {"property":"The Venetian / The Palazzo","venue":"The Venetian Resort","resort_fee":55,"tax_pct":13.38,
  "fee_source":"https://www.venetianlasvegas.com/resort/resort-fee.html",
  "rate_status":"unverified — no date-specific official room rate captured",
  "walk_to_venue_min":None,"walk_status":"unverified — no official walking-minute source",
  "booking_link":"https://www.venetianlasvegas.com/book",
  "notes":"Host property. Official poker suite rates start at $119/$209 (conditional, play-qualified); not a date quote."},
 {"property":"Wynn Las Vegas","venue":"Wynn Las Vegas","resort_fee":None,"tax_pct":13.38,
  "fee_source":"https://www.wynnlasvegas.com/",
  "rate_status":"unverified — official resort-fee page not reached; third-party figures conflict and are not used",
  "walk_to_venue_min":None,"walk_status":"unverified — no official walking-minute source",
  "booking_link":"https://www.wynnlasvegas.com/",
  "notes":"Wynn poker room verified on official poker page; resort fee amount unverified."},
 {"property":"Bellagio","venue":"Bellagio","resort_fee":None,"tax_pct":13.38,
  "fee_source":"https://www.bellagio.com/",
  "rate_status":"unverified — official resort-fee page returned 404; third-party figures conflict",
  "walk_to_venue_min":None,"walk_status":"unverified — no official walking-minute source",
  "booking_link":"https://www.bellagio.com/",
  "notes":"Bellagio poker room verified on official page; resort fee amount unverified."},
 {"property":"Caesars Palace","venue":"Caesars Palace","resort_fee":None,"tax_pct":13.38,
  "fee_source":"https://www.caesars.com/caesars-palace",
  "rate_status":"unverified — official resort-fee page is marketing copy with no amount",
  "walk_to_venue_min":None,"walk_status":"unverified — no official walking-minute source",
  "booking_link":"https://www.caesars.com/caesars-palace",
  "notes":"Caesars Palace poker room verified; resort fee amount unverified."},
]

# ---- dated rate log (empty until an official dated quote is captured) ----
rates_log = []

# ---- monitoring sources (re-checked on schedule by tools/check_sources.py) ----
monitoring_sources = [
 {"id":"V_SCHED","label":"Venetian DSE IV schedule page","url":SCHED_URL,"type":"schedule","last_checked":RETRIEVED,"status":"ok"},
 {"id":"V_RESORT","label":"Venetian resort fee page","url":"https://www.venetianlasvegas.com/resort/resort-fee.html","type":"fee","last_checked":RETRIEVED,"status":"ok"},
 {"id":"V_RATES","label":"Venetian poker suite rates","url":"https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html","type":"rate","last_checked":RETRIEVED,"status":"ok"},
 {"id":"W_PAGE","label":"Wynn Las Vegas poker room","url":"https://www.wynnlasvegas.com/casino/poker","type":"schedule","last_checked":RETRIEVED,"status":"unverified"},
 {"id":"B_PAGE","label":"Bellagio poker room","url":"https://www.bellagio.com/casino/poker","type":"schedule","last_checked":RETRIEVED,"status":"unverified"},
 {"id":"C_PAGE","label":"Caesars Palace poker","url":"https://www.caesars.com/caesars-palace/casino","type":"schedule","last_checked":RETRIEVED,"status":"unverified"},
]
change_log = []

data = {
  "meta": {"generated":"2026-11-17","snapshot":"Venetian DSE IV, Nov 16 – Dec 23 2026","retrieved":RETRIEVED,
           "policy":"Only values read on an official source are shown. Re-entry/add-on terms are blank where the structure sheet is silent. Omission is not confirmation."},
  "events": events,
  "hotels": hotels,
  "rates_log": rates_log,
  "monitoring_sources": monitoring_sources,
  "change_log": change_log,
}

out = "planner/assets/data.js"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    f.write("// Auto-generated by tools/gen_planner_data.py — verified Venetian DSE IV dataset, retrieved 2026-11-17.\n")
    f.write("// Do not edit by hand; regenerate after re-verification.\n")
    f.write("window.PLANNER_DATA = ")
    f.write(json.dumps(data, indent=2))
    f.write(";\n")
print(f"wrote {out}: {len(events)} events, {len(hotels)} hotels, {len(monitoring_sources)} sources")
