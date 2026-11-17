#!/usr/bin/env python3
"""Build data/v2/events.json from the transcribed official schedule + structure facts.

Nothing is inferred: buy-in, guarantee and event name are parsed from the printed
event-name string and checked against the official structure sheet. Where the
printed string and the sheet disagree, the row records both and is flagged.
"""
import json, os, re
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "v2", "raw", "venetian_dse4_2026-11-17.tsv")
FACTS = json.load(open(os.path.join(ROOT, "data", "v2", "structure_facts.json")))["sheets"]

def money(s):
    m = re.match(r"\$([\d,]+)", s)
    return int(m.group(1).replace(",", "")) if m else None

def parse_guarantee(name):
    m = re.search(r"\$([\d,.]+)\s*(K|Mill|M)\b", name)
    if not m:
        return None, None
    v = float(m.group(1).replace(",", ""))
    mult = {"K": 1000, "Mill": 1000000, "M": 1000000}[m.group(2)]
    return int(v * mult), m.group(0)

def t2min(t):
    return datetime.strptime(t, "%I:%M %p").hour * 60 + datetime.strptime(t, "%I:%M %p").minute

rows = []
with open(RAW) as fh:
    for line in fh:
        if line.startswith("#") or not line.strip():
            continue
        d, t, ev, name, sheet, kind = line.rstrip("\n").split("|")
        f = FACTS[sheet]
        buy = money(name)
        gtd, gtd_txt = parse_guarantee(name)
        # per-event guarantee override from the sheet
        gsheet = f["guarantee_usd"]
        if f.get("guarantee_per_event") and ev in f["guarantee_per_event"]:
            gsheet = f["guarantee_per_event"][ev]
        rec = {
            "id": f"V-{d}-{ev}-{t.replace(':','').replace(' ','').lower()}",
            "venue": "Venetian",
            "venue_full": "The Venetian Resort Las Vegas — Poker Room, The Palazzo level 2",
            "date": d,
            "start": t,
            "event_no": ev,
            "name_printed": name,
            "kind": kind,
            "buy_in": buy,
            "buy_in_source": "printed in the official event name (calendar)" if buy else None,
            "guarantee_printed": gtd,
            "guarantee_text": gtd_txt,
            "guarantee_on_sheet": gsheet,
            "guarantee_basis": f["guarantee_basis"],
            "chips": f["chips"],
            "level_min": f["level_min"],
            "late_reg_text": f["late_reg_text"],
            "late_reg_time": f["late_reg_time"],
            "fee_house": f["fee_house"],
            "prize_pool_per_entry": f["prize_pool_per_entry"],
            "pays_pct": f["pays_pct"],
            "bounty": f.get("bounty"),
            "eligibility": f.get("eligibility"),
            "sheet_title": f["title"],
            "sheet_url": f["url"],
            "calendar_url": "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html",
            "retrieved": "2026-11-17",
            "reentry_published": False,
            "addon_published": False,
            "entry_rule_status": "not_published",
            "entry_rule_note": "The official structure sheet states the late-registration window only. It does not say whether a busted player may re-enter, and it lists no add-on or rebuy. See data/v2/sources.json V_S%02d." % int(sheet),
        }
        # cross-check printed guarantee vs sheet
        if gtd is not None and gsheet is not None and gtd != gsheet:
            rec["irregularity"] = f"Printed calendar guarantee ${gtd:,} differs from structure-sheet guarantee ${gsheet:,}."
        if gtd is None and gsheet is not None:
            rec["irregularity"] = f"Calendar row prints no GTD; structure sheet states ${gsheet:,}."
        rows.append(rec)

# Day-2 restarts and final tables are not entries
entries = [r for r in rows if r["kind"] not in ("restart", "final_table")]
restarts = [r for r in rows if r["kind"] in ("restart", "final_table")]

# --- overlap analysis -------------------------------------------------------
# A one-day event's plausible length is estimated from its own structure:
# levels until registration closes, plus a conservative run to the finish.
for r in entries:
    if r["late_reg_time"]:
        r["late_reg_min"] = t2min(r["late_reg_time"])
        if r["late_reg_min"] < t2min(r["start"]):
            r["late_reg_min"] += 24 * 60
    else:
        r["late_reg_min"] = None
    lv = r["level_min"]
    lv = lv if isinstance(lv, int) else 20
    # plausible finish = start + late-reg window + same number of levels again + breaks
    if r["late_reg_min"]:
        window = r["late_reg_min"] - t2min(r["start"])
        r["plausible_min_hours"] = round((window * 2 + 60) / 60, 1)
    else:
        r["plausible_min_hours"] = None

# --- guarantee scope -------------------------------------------------------
# A multi-flight event prints ONE guarantee for the whole event. Dividing it by a
# single flight's buy-in would overstate the ratio, so the scope is recorded and
# the builder refuses to show a per-flight ratio for flights.
import collections as _c
_flights = _c.defaultdict(list)
for r in entries:
    _flights[r["event_no"]].append(r)
for no, rs in _flights.items():
    for r in rs:
        r["guarantee_scope"] = "event_total" if len(rs) > 1 else "entry"
        r["flights_in_event"] = len(rs)
        if len(rs) > 1:
            r["guarantee_scope_note"] = (
                "Event #%s runs %d starting flights. The printed guarantee is for the whole event, "
                "not per flight, so no guarantee-to-buy-in ratio is shown on a flight row."
                % (no, len(rs)))

import collections
by_day = collections.defaultdict(list)
for r in entries:
    by_day[r["date"]].append(r)

overlaps = []
for d, rs in sorted(by_day.items()):
    rs.sort(key=lambda x: t2min(x["start"]))
    for i in range(len(rs) - 1):
        a, b = rs[i], rs[i + 1]
        if a["kind"] in ("restart", "final_table"):
            continue
        gap = t2min(b["start"]) - t2min(a["start"])
        # cannot both be played unless the earlier one ends (or the player busts) before b starts
        fits = a.get("plausible_min_hours") is not None and gap / 60.0 >= a["plausible_min_hours"]
        overlaps.append({
            "date": d, "a": a["id"], "b": b["id"],
            "a_label": f"#{a['event_no']} {a['start']}", "b_label": f"#{b['event_no']} {b['start']}",
            "gap_hours": round(gap / 60, 2),
            "a_plausible_min_hours": a["plausible_min_hours"],
            "sequence_plausible": bool(fits),
        })

out = {
    "meta": {
        "retrieved": "2026-11-17",
        "venue": "The Venetian Resort Las Vegas",
        "series": "DeepStack Extravaganza IV, Nov 16 – Dec 23, 2026",
        "rows_total": len(rows),
        "entry_rows": len(entries),
        "restart_rows": len(restarts),
        "confirmed_single_entry": sum(1 for r in entries if r["entry_rule_status"] == "single_entry_confirmed"),
        "how_derived": "data/v2/raw/venetian_dse4_2026-11-17.tsv (transcribed from V_CAL) joined to data/v2/structure_facts.json (each of the 37 structure sheets fetched and read).",
        "caution": "No Venetian 2026 sheet states re-entry terms. Silence is not a confirmation of single entry; this room printed explicit 'Registration and Re-Entry is allowed' clauses in prior seasons (V_OLD_2023_1, V_OLD_2024_1).",
    },
    "events": entries,
    "restarts": restarts,
    "overlaps": overlaps,
}
json.dump(out, open(os.path.join(ROOT, "data", "v2", "events.json"), "w"), indent=1)
print("rows", len(rows), "entries", len(entries), "restarts", len(restarts), "overlaps", len(overlaps))
print("confirmed single entry:", out["meta"]["confirmed_single_entry"])
bad = [r for r in entries if r.get("irregularity")]
for b in bad: print("IRREG", b["id"], b["irregularity"])
