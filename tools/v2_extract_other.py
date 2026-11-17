#!/usr/bin/env python3
"""Build data/v2/events_other.json.
Sources: W_DAILY/W_POSTER (Wynn dailies), W_WPT (Wynn WPT poster T58), B_FRI/B_SAT/B_POKER,
C_FLYER (Caesars). Entry-rule statuses only ever come from text quoted in data/v2/sources.json.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "v2", "raw", "wynn_wpt_2026-11-17.tsv")

def num(s):
    s = (s or "").strip()
    if not s or s == "-":
        return None
    if s.startswith("$"):
        return int(float(s[1:].replace(",", "")))
    return None

def kind_of(name):
    n = name.lower()
    if "satellite" in n:
        return "satellite"
    if "final table" in n:
        return "final_table"
    if re.search(r"day [2-9]\b", n):
        return "restart"
    if re.search(r"day 1[a-f0-9]?\b", n):
        return "flight"
    return "one_day"

wpt = []
for i, line in enumerate(open(RAW)):
    line = line.rstrip("\n")
    if line.startswith("#") or not line.strip():
        continue
    d, t, name, buy, gtd, chips, lv = line.split("|")
    k = kind_of(name)
    g = num(gtd)
    gtext = gtd if gtd != "-" else None
    if g is None and gtext and ("Seats" in gtext or "Prizes" in gtext):
        pass
    rec = {
        "id": "W-WPT-%s-%03d" % (d.replace("-", ""), i),
        "venue": "Wynn", "venue_full": "Wynn Las Vegas — Poker Room, Encore",
        "date": d, "start": t.replace("a.m.", "AM").replace("p.m.", "PM"),
        "name": name, "kind": k,
        "buy_in": num(buy), "guarantee": g, "guarantee_text": gtext,
        "chips": num(chips), "level_min": (lv if lv != "-" else None),
        "fee": None, "late_reg": None, "reentry": None, "addon": None,
        "entry_rule_status": "not_published",
        "sources": ["W_WPT", "W_WPT_TC"], "retrieved": "2026-11-17",
        "note": "Poster prints buy-in, guarantee, chips and level minutes; it prints no house/staff fee and no per-event re-entry clause (it defers fees to the structure sheets).",
    }
    wpt.append(rec)

# Published entry rules from W_WPT_PR (worldpokertour.com, the organiser)
champ = [r for r in wpt if r["buy_in"] == 10400]
for r in champ:
    r["entry_rule_status"] = "single_entry_per_flight_confirmed"
    r["reentry"] = "NO re-entry within a starting flight — WPT: 'players allowed a single entry per starting flight with the final opportunity to enter being prior to the start of Day 2'"
    r["reentry_caveat"] = "Three starting flights exist (Dec 13, 14, 15), so the same player can legitimately enter up to three times in total. This is NOT a pure freezeout."
    r["sources"] = ["W_WPT", "W_WPT_PR", "W_WPT_TC"]
sgm = [r for r in wpt if "Super Gold Million" in r["name"] and r["kind"] == "flight"]
for r in sgm:
    r["entry_rule_status"] = "reentry_allowed_published"
    r["reentry"] = "YES, unlimited — WPT: the Super Gold Million 'will offer four starting flights and unlimited re-entry'"
    r["sources"] = ["W_WPT", "W_WPT_PR"]

hand = [
  {
    "id": "W-DAILY-MONTHU", "venue": "Wynn", "venue_full": "Wynn Las Vegas — Poker Room, Encore",
    "date": "Monday–Thursday (recurring)", "start": "12:00 PM",
    "name": "Daily NLH $200 — $10,000 guarantee", "kind": "recurring",
    "buy_in": 200, "guarantee": 10000, "chips": 25000, "level_min": 30,
    "fee": {"total_fee": 38, "fee_breakdown": "$26 tournament fee + $12 poker staff service charge", "prize_pool_per_entry": 162},
    "late_reg": "Until the start of level 9 (approximately 4:30 p.m.)",
    "reentry": "YES — the terms call out the re-entry fee and say registration and re-entries run to level 9",
    "addon": "None published",
    "entry_rule_status": "reentry_allowed_published",
    "sources": ["W_DAILY", "W_POSTER"], "retrieved": "2026-11-17",
    "note": "Suspended during Signature/Millions/Classic series. The WPT World Championship runs Nov 27 – Dec 21, 2026, so confirm the daily is running before relying on it."
  },
  {
    "id": "W-DAILY-FRI", "venue": "Wynn", "venue_full": "Wynn Las Vegas — Poker Room, Encore",
    "date": "Friday (recurring)", "start": "12:00 PM",
    "name": "Friday NLH Rebuy & Add-on $240 — $40,000 guarantee", "kind": "recurring",
    "buy_in": 240, "guarantee": 40000, "chips": 25000, "level_min": 30,
    "fee": {"total_fee": 50, "fee_breakdown": "$35 tournament fee + $15 service charge", "prize_pool_per_entry": 190},
    "late_reg": "Until the start of level 9 (approximately 4:30 p.m.)",
    "reentry": "NO — 'Re-entry is NOT allowed'",
    "addon": "YES — unlimited $200 rebuys for 25,000 chips while at 15,000 chips or fewer, plus one $100 add-on for 15,000 chips until the end of registration",
    "entry_rule_status": "addon_or_rebuy_published",
    "sources": ["W_DAILY", "W_POSTER"], "retrieved": "2026-11-17",
    "note": "No re-entry, but rebuys and an add-on are allowed — this belongs in the separate section even though re-entry is barred."
  },
  {
    "id": "W-DAILY-WEEKEND", "venue": "Wynn", "venue_full": "Wynn Las Vegas — Poker Room, Encore",
    "date": "Saturday & Sunday (recurring)", "start": "12:00 PM",
    "name": "Weekend NLH $200 — $25,000 guarantee", "kind": "recurring",
    "buy_in": 200, "guarantee": 25000, "chips": 25000, "level_min": 30,
    "fee": {"total_fee": 38, "fee_breakdown": "$26 tournament fee + $12 poker staff service charge", "prize_pool_per_entry": 162},
    "late_reg": "Until the start of level 9 (approximately 4:30 p.m.)",
    "reentry": "YES — the terms call out the re-entry fee and state that re-entries run to level 9",
    "addon": "None published",
    "entry_rule_status": "reentry_allowed_published",
    "sources": ["W_DAILY", "W_POSTER"], "retrieved": "2026-11-17"
  },
  {
    "id": "W-NIGHTLY", "venue": "Wynn", "venue_full": "Wynn Las Vegas — Poker Room, Encore",
    "date": "Nightly (recurring)", "start": "6:00 PM",
    "name": "Nightly NLH $160 — $10,000 guarantee", "kind": "recurring",
    "buy_in": 160, "guarantee": 10000, "chips": None, "level_min": None,
    "fee": None, "late_reg": None, "reentry": None, "addon": None,
    "entry_rule_status": "not_published",
    "sources": ["W_POSTER", "W_POKER"], "retrieved": "2026-11-17",
    "note": "Named on the official poster and poker page, but the structures PDF read here prints terms only for the Mon–Thu, Friday and weekend events. Fee, chips, level minutes and entry rules were not published there, so they are blank."
  },
  {
    "id": "B-FRI-600", "venue": "Bellagio", "venue_full": "Bellagio — Poker Room, north side of casino next to the sportsbook",
    "date": "Friday (recurring)", "start": "11:00 AM", "name": "NLH $600", "kind": "recurring",
    "buy_in": 600, "guarantee": None, "chips": 30000, "level_min": 30,
    "fee": {"total_fee": 50, "fee_breakdown": "$50 house fee, plus a $40 voluntary staff gratuity that adds 15,000 chips", "prize_pool_per_entry": 510},
    "late_reg": "Through the end of level 8 (including the break)",
    "reentry": "YES — 'Players may buy-in and re-enter through the end of level 8 (Including Break)'",
    "addon": "YES in effect — $40 voluntary staff gratuity at registration buys 15,000 extra chips (15,000 + 15,000)",
    "entry_rule_status": "addon_or_rebuy_published",
    "sources": ["B_POKER", "B_FRI"], "retrieved": "2026-11-17",
    "note": "No guarantee printed on the Friday sheet."
  },
  {
    "id": "B-SAT-1100", "venue": "Bellagio", "venue_full": "Bellagio — Poker Room",
    "date": "Saturday (recurring)", "start": "11:00 AM",
    "name": "NLH $1,100 (sheet heading; linked file name says $1,000)", "kind": "recurring",
    "buy_in": 1100, "guarantee": 50000, "chips": 40000, "level_min": 30,
    "fee": None,
    "guarantee_note": "Rule 08 guarantees the 'total Combined Prize Pool' of at least $50,000 — a combined multi-flight figure, not a per-flight guarantee.",
    "late_reg": "Until the start of level 10 (approx. 5:15 p.m. for flights 1A/1B, 4:15 p.m. 1C, 9:30 p.m. 1D)",
    "reentry": None,
    "addon": "YES in effect — $40 voluntary staff gratuity adds 20,000 chips",
    "entry_rule_status": "addon_or_rebuy_published",
    "sources": ["B_POKER", "B_SAT"], "retrieved": "2026-11-17",
    "irregularity": "The linked PDF contradicts itself: filename '$1000 NLH', heading 'NLH $1100 BUY-IN', and rule 07 splits 'the $600 Buy-in'. The buy-in cannot be confirmed from this document."
  },
]

advantage = [
  {"id":"ADV-C-100","venue":"Caesars Palace","date":"Daily (recurring)","times":["10:00 AM","6:00 PM"],
   "name":"Daily NLH $100","buy_in":100,"guarantee":1000,"chips":20000,"level_min":20,
   "fee":{"total_fee":30,"fee_breakdown":"$30 maintenance fee","prize_pool_per_entry":70},
   "late_reg":"Registration closes at the start of level 7; sign-ups open one hour before the event",
   "reentry":"YES — 'may re-enter, by paying the entry fee, upon elimination within the first break of play'",
   "addon":"YES — $50 add-on for 15,000 chips, first break only",
   "why":"Re-entry and an add-on both let a player pay more for more chips.",
   "sources":["C_FLYER"],"retrieved":"2026-11-17"},
  {"id":"ADV-C-160","venue":"Caesars Palace","date":"Daily (recurring)","times":["2:00 PM","9:00 PM"],
   "name":"Daily NLH $160","buy_in":160,"guarantee":1000,"chips":20000,"level_min":20,
   "fee":{"total_fee":45,"fee_breakdown":"$45 maintenance fee","prize_pool_per_entry":115},
   "late_reg":"Registration closes at the start of level 7",
   "reentry":"YES — same flyer rule","addon":"YES — $50 add-on, first break only",
   "why":"Re-entry and an add-on both let a player pay more for more chips.",
   "sources":["C_FLYER"],"retrieved":"2026-11-17"},
  {"id":"ADV-W-FRI","venue":"Wynn","date":"Friday (recurring)","times":["12:00 PM"],
   "name":"Friday NLH Rebuy & Add-on $240","buy_in":240,"guarantee":40000,"chips":25000,
   "reentry":"NO — explicitly barred","addon":"YES — unlimited $200 rebuys + one $100 add-on",
   "why":"Rebuys and an add-on are the spend-for-chips pattern the user asked to separate. This is the one case where 'no re-entry' and 'no spending advantage' disagree.",
   "sources":["W_DAILY","W_POSTER"],"retrieved":"2026-11-17"},
  {"id":"ADV-B-FRI","venue":"Bellagio","date":"Friday (recurring)","times":["11:00 AM"],
   "name":"Bellagio Friday $600 — optional staff-gratuity chip bonus","buy_in":600,"chips":30000,
   "reentry":"YES","addon":"Optional $40 gratuity = +15,000 chips",
   "why":"A registration payment that increases the starting stack functions as an add-on.",
   "sources":["B_FRI"],"retrieved":"2026-11-17"},
  {"id":"ADV-W-SGM","venue":"Wynn","date":"2026-12-10 to 2026-12-13","times":["10:00 AM & 6:00 PM flights"],
   "name":"Super Gold Million Mystery Bounty $400 — $3,000,000 guarantee","buy_in":400,"guarantee":3000000,"chips":30000,
   "reentry":"YES — 'unlimited re-entry' per the WPT release","addon":None,
   "why":"Unlimited re-entry across four flights.",
   "sources":["W_WPT","W_WPT_PR"],"retrieved":"2026-11-17"},
]

out = {
  "meta": {
    "retrieved": "2026-11-17",
    "rule": "Every row links an official page or PDF. Unprinted fields stay null and are listed on the Flagged for Review page.",
    "status_vocabulary": ["single_entry_per_flight_confirmed", "reentry_allowed_published", "addon_or_rebuy_published", "not_published"],
    "separate_section": "Anything with re-entry, rebuy or an add-on is catalogued in 'advantage_by_spending'. Those rows are described, not disqualified."
  },
  "events": hand,
  "wpt_events": wpt,
  "wpt_meta": {
    "source": "W_WPT (official Wynn poster, Nov 27 – Dec 21, 2026), both poster pages transcribed in full",
    "rows": len(wpt),
    "entry_rows": sum(1 for r in wpt if r["kind"] in ("one_day", "flight")),
    "restart_or_final_rows": sum(1 for r in wpt if r["kind"] in ("restart", "final_table")),
    "fee_note": "The poster defers fees to the per-event structure sheets; those were not read in this session, so every WPT fee is blank and flagged.",
    "championship_rule": "W_WPT_PR: the $10,400 WPT World Championship allows 'a single entry per starting flight' — with three flights that still permits up to three entries in the event overall.",
  },
  "advantage_by_spending": advantage,
}
json.dump(out, open(os.path.join(ROOT, "data", "v2", "events_other.json"), "w"), indent=1)
print("hand rows", len(hand), "wpt rows", len(wpt), "advantage rows", len(advantage))
print("wpt kinds", {k: sum(1 for r in wpt if r["kind"] == k) for k in sorted(set(r["kind"] for r in wpt))})
print("single-entry-per-flight rows:", len(champ), "| unlimited re-entry rows:", len(sgm))
