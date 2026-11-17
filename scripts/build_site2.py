#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Poker4 v2 data artifacts from data/feature/dataset.py and validate policy:
   - every event row must cite official source ids whose URLs are https on official domains
   - every row carries a last_checked date
   - nothing is marked 'confirmed' without a verbatim excerpt
Outputs: data/feature/events.json, hotels.json, sources.json, flagged.json, assets/data.js"""
import json, os, sys, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data", "feature"))
import dataset as D

ROOT = os.path.join(os.path.dirname(__file__), "..")
OFFICIAL_HOSTS = ("venetianlasvegas.com", "cdn.wynnresorts.com", "wynnlasvegas.com", "wptmedia-mig.s3.amazonaws.com",
                  "bellagio.mgmresorts.com", "assets.contentstack.io", "caesars.com", "aria.mgmresorts.com",
                  "mgmgrand.mgmresorts.com", "treasureisland.com", "goldennugget.com")

def official(url):
    return url.startswith("https://") and any(h in url for h in OFFICIAL_HOSTS)

events = []

def base_row(**kw):
    kw.setdefault("last_checked", D.RETRIEVED)
    kw.setdefault("changed", False)
    return kw

# ---- Venetian
for (date, time, evno, flight, sheet_id, name) in D.VEN_ROWS:
    sh = D.VEN_SHEETS[sheet_id]
    gtd = D.EVENT_GUARANTEE.get(evno, sh["guarantee"])
    is_restart = "Day 2" in flight or "Day 3" in flight
    ratio = round(gtd / sh["buy_in"], 1) if (gtd and sh["buy_in"]) else None
    multi = sh["rules"]["single_entry"]["status"] == "confirmed-no"
    section = "multi-entry" if multi else (
        "satellite" if "satellite" in sh["kind"] else (
        "bounty" if ("bounty" in sh["kind"] or "pko" in sh["kind"]) else (
        "flighted" if "flight" in sh["kind"] else "standard")))
    events.append(base_row(
        id=f"ven-{evno}-{date}-{time}", venue="Venetian", series="DSE IV (Nov 16 – Dec 23, 2026)",
        date=date, time=time, event_no=evno, flight=flight, name=name,
        buy_in=sh["buy_in"], prize_pool_per_entry=sh["pool"], house_fee=sh["house"], staff_fee=sh["staff"],
        guarantee=gtd, guarantee_includes_bounties=sh["gtd_bounty"], ratio=ratio,
        chips=sh["chips"], level_min=sh["lvl"], late_reg=sh["late_reg"], late_reg_time=sh["late_time"],
        kind=sh["kind"], section=section, multi_day=bool(flight), restart=is_restart,
        entry_rules=sh["rules"], note=sh["note"],
        sources=["V-DSE", "V-S"], structure_url=(D.S % sheet_id) if sheet_id else None,
        status="past" if date < D.TODAY else "upcoming"))

# ---- Wynn daily
for w in D.WYNN_DAILY:
    multi = w["rules"]["single_entry"]["status"] == "confirmed-no"
    section = "multi-entry" if multi else "standard"
    if "rebuy" in w["kind"]:
        section = "multi-entry"
    ratio = round(w["guarantee"] / w["buy_in"], 1) if w.get("guarantee") else None
    events.append(base_row(
        id=w["id"], venue="Wynn", series="Wynn daily tournaments (recurring)",
        date=None, date_note=w["date_note"], days=w["days"], time=w["time"], event_no=None, flight="",
        name=w["name"], buy_in=w["buy_in"], prize_pool_per_entry=w["pool"], house_fee=None, staff_fee=None,
        fees_total=w.get("fees"), guarantee=w["guarantee"], guarantee_includes_bounties=w["gtd_bounty"],
        ratio=ratio, chips=w["chips"], level_min=w["lvl"], late_reg=w["late_reg"], late_reg_time=None,
        kind=w["kind"], section=section, multi_day=False, restart=False,
        entry_rules=w["rules"], note=w["note"], sources=[w["src"]], structure_url=None,
        status="upcoming"))

# ---- Wynn WPT festival
for (date, time, name, buy_in, gtd, chips, lvl, kind, note) in D.WYNN_WPT:
    lvlmin = int(lvl.split("/")[0])
    ratio = round(gtd / buy_in, 1) if (gtd and buy_in) else None
    section = "satellite" if "satellite" in kind else ("bounty" if ("bounty" in kind or "pko" in kind) else
               ("flighted" if "flight" in kind else "standard"))
    events.append(base_row(
        id=f"wynn-wpt-{date}-{time}", venue="Wynn", series="WPT World Championship festival (Nov 27 – Dec 21, 2026)",
        date=date, time=time, event_no=None, flight="", name=name,
        buy_in=buy_in, prize_pool_per_entry=None, house_fee=None, staff_fee=None,
        guarantee=gtd, guarantee_includes_bounties=None if ("bounty" in kind) else False,
        ratio=ratio, chips=chips, level_min=lvlmin, late_reg="per-event structure sheet (not verified this pass)",
        late_reg_time=None, kind=kind, section=section, multi_day=("2 Day" in name or "3 Day" in name or "flight" in kind),
        restart=False, entry_rules=D.WPT_RULES, note=note,
        sources=["W-WPT", "WPT-TC"], structure_url=None,
        status="past" if date < D.TODAY else "upcoming"))

# ---- Bellagio
for b in D.BELLAGIO:
    ratio = round(b["guarantee"] / b["buy_in"], 1) if (b.get("guarantee") and b.get("buy_in")) else None
    multi = b["rules"]["single_entry"]["status"] == "confirmed-no"
    section = "multi-entry" if multi else ("flighted" if "flight" in b["kind"] else "standard")
    events.append(base_row(
        id=b["id"], venue="Bellagio", series="Bellagio weekly tournaments",
        date=None, date_note=b["date_note"], days=b["days"], time=b["time"], event_no=None, flight="",
        name=b["name"], buy_in=b["buy_in"], prize_pool_per_entry=b["pool"], house_fee=b["house"], staff_fee=b["staff"],
        guarantee=b["guarantee"], guarantee_includes_bounties=b["gtd_bounty"], ratio=ratio,
        chips=b["chips"], level_min=b["lvl"], late_reg=b["late_reg"], late_reg_time=None,
        kind=b["kind"], section=section, multi_day="flight" in b["kind"], restart=False,
        entry_rules=b["rules"], note=b["note"], sources=[b["src"], "B-POKER"], structure_url=None,
        status="upcoming"))

# ---- Caesars
for c in D.CAESARS:
    ratio = round(c["guarantee"] / c["buy_in"], 1) if c.get("guarantee") else None
    events.append(base_row(
        id=c["id"], venue="Caesars Palace", series="Caesars Palace daily tournaments",
        date=None, date_note=c["date_note"], days=c["days"], time=c["time"], event_no=None, flight="",
        name=c["name"], buy_in=c["buy_in"], prize_pool_per_entry=c["pool"], house_fee=c["house"], staff_fee=c["staff"],
        guarantee=c["guarantee"], guarantee_includes_bounties=c["gtd_bounty"], ratio=ratio,
        chips=c["chips"], level_min=c["lvl"], late_reg=c["late_reg"], late_reg_time=None,
        kind=c["kind"], section="multi-entry", multi_day=False, restart=False,
        entry_rules=c["rules"], note=c["note"], sources=[c["src"]], structure_url=None,
        status="upcoming"))

# ---------------- validation (policy gate)
errors = []
for e in events:
    if not e.get("last_checked"):
        errors.append(f"{e['id']}: missing last_checked")
    for sid in e["sources"]:
        if sid not in D.SOURCES:
            errors.append(f"{e['id']}: unknown source id {sid}")
        elif not official(D.SOURCES[sid][1]):
            errors.append(f"{e['id']}: source {sid} not an approved official host: {D.SOURCES[sid][1]}")
    if e.get("structure_url") and not official(e["structure_url"]):
        errors.append(f"{e['id']}: structure_url not official")
    for rk, rv in e["entry_rules"].items():
        if rv["status"].startswith("confirmed") and not rv.get("excerpt") and rv["status"] != "confirmed-no":
            errors.append(f"{e['id']}: rule {rk} marked {rv['status']} without excerpt")
        if rv["status"] == "confirmed" and not rv.get("excerpt"):
            errors.append(f"{e['id']}: rule {rk} confirmed without excerpt")

for h in D.HOTELS:
    if not h.get("last_checked"):
        errors.append(f"hotel {h['id']}: missing last_checked")
    for sid in [h.get("resort_fee_src"), h.get("tax_src"), h.get("parking_src"), h.get("cancellation_src"), h.get("walk_src")]:
        if sid and (sid not in D.SOURCES or not official(D.SOURCES[sid][1])):
            errors.append(f"hotel {h['id']}: bad source {sid}")
    for r in h.get("rate_log", []):
        if r.get("src") and (r["src"] not in D.SOURCES or not official(D.SOURCES[r["src"]][1])):
            errors.append(f"hotel {h['id']}: rate_log bad source {r.get('src')}")
        # verify checkout total arithmetic when all parts present
        if r.get("nightly") and r.get("resort_fee_per_night") is not None and r.get("taxes") is not None:
            room = sum(r["nightly"])
            base = room + r["resort_fee_per_night"] * r["nights"]
            tax = round(base * D.TAX_RATE, 2)
            if abs(tax - r["taxes"]) > 0.05:
                errors.append(f"hotel {h['id']}: tax arithmetic mismatch {tax} vs {r['taxes']}")
            total = round(base + r["taxes"], 2)
            if abs(total - r["checkout_total"]) > 0.05:
                errors.append(f"hotel {h['id']}: total arithmetic mismatch {total} vs {r['checkout_total']}")

if errors:
    print("VALIDATION ERRORS:")
    for e in errors:
        print(" -", e)
    sys.exit(1)

# ---------------- write artifacts
os.makedirs(os.path.join(ROOT, "data", "feature"), exist_ok=True)
os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)

# sources with last-checked
sources_out = [{"id": k, "title": v[0], "url": v[1], "last_checked": D.RETRIEVED} for k, v in D.SOURCES.items()]

with open(os.path.join(ROOT, "data", "feature", "events.json"), "w") as f:
    json.dump(events, f, indent=1)
with open(os.path.join(ROOT, "data", "feature", "hotels.json"), "w") as f:
    json.dump(D.HOTELS, f, indent=1)
with open(os.path.join(ROOT, "data", "feature", "sources.json"), "w") as f:
    json.dump(sources_out, f, indent=1)

payload = {"generated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
           "retrieved": D.RETRIEVED, "events": events, "hotels": D.HOTELS, "sources": sources_out,
           "tax_rate": D.TAX_RATE}
try:
    with open(os.path.join(ROOT, "data", "feature", "flagged.json")) as f:
        payload["flagged"] = json.load(f)
except FileNotFoundError:
    payload["flagged"] = []
try:
    with open(os.path.join(ROOT, "data", "feature", "changes.json")) as f:
        payload["changes"] = json.load(f)
except FileNotFoundError:
    payload["changes"] = []
try:
    with open(os.path.join(ROOT, "data", "feature", "questions.json")) as f:
        payload["questions"] = json.load(f)
except FileNotFoundError:
    payload["questions"] = []
try:
    with open(os.path.join(ROOT, "data", "feature", "suggestions.json")) as f:
        payload["suggestions"] = json.load(f)
except FileNotFoundError:
    payload["suggestions"] = []

with open(os.path.join(ROOT, "assets", "data.js"), "w") as f:
    f.write("window.POKER4_DATA = ")
    json.dump(payload, f, indent=1)
    f.write(";\n")

counts = {}
for e in events:
    counts[e["section"]] = counts.get(e["section"], 0) + 1
print(f"OK: {len(events)} event rows, {len(D.HOTELS)} hotels, {len(sources_out)} sources.")
print("sections:", counts)
print("confirmed single-entry rows:", sum(1 for e in events if e["entry_rules"]["single_entry"]["status"] == "confirmed"))
