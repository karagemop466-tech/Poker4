# -*- coding: utf-8 -*-
"""Integrated data assembly for the Poker4 site (final integration session b040f8dd).

Run:  python3 build/build_integrated.py
Writes data/integrated/*.json and then renders the root pages via build_pages.py.

Verification rules enforced here:
  * every event row carries official source URL(s) and a last_checked date;
  * entry-rule fields are 'unverified' unless an official sheet excerpt confirms them;
  * guaranteed-pool ratio is computed only when buy-in and guarantee are both
    confirmed; bounty/seat guarantees are labeled, never silently divided.
"""
import csv, json, os, re, sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data_venetian as V
import data_wynn as W
import data_hotels as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "integrated")
os.makedirs(OUT, exist_ok=True)
TODAY = "2026-11-17"

WEEKDAY = {d: w for d, w in [
    ("2026-11-16","Monday"),("2026-11-17","Tuesday"),("2026-11-18","Wednesday"),
    ("2026-11-19","Thursday"),("2026-11-20","Friday"),("2026-11-21","Saturday"),
    ("2026-11-22","Sunday"),("2026-11-23","Monday"),("2026-11-24","Tuesday"),
    ("2026-11-25","Wednesday"),("2026-11-26","Thursday"),("2026-11-27","Friday"),
    ("2026-11-28","Saturday"),("2026-11-29","Sunday"),("2026-11-30","Monday"),
    ("2026-12-01","Tuesday"),("2026-12-02","Wednesday"),("2026-12-03","Thursday"),
    ("2026-12-04","Friday"),("2026-12-05","Saturday"),("2026-12-06","Sunday"),
    ("2026-12-07","Monday"),("2026-12-08","Tuesday"),("2026-12-09","Wednesday"),
    ("2026-12-10","Thursday"),("2026-12-11","Friday"),("2026-12-12","Saturday"),
    ("2026-12-13","Sunday"),("2026-12-14","Monday"),("2026-12-15","Tuesday"),
    ("2026-12-16","Wednesday"),("2026-12-17","Thursday"),("2026-12-18","Friday"),
    ("2026-12-19","Saturday"),("2026-12-20","Sunday"),("2026-12-21","Monday"),
    ("2026-12-22","Tuesday"),("2026-12-23","Wednesday")]}

def hm_to_min(s):
    s = (s or "").strip()
    m = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM)$", s, re.I)
    if not m:
        m2 = re.match(r"^(\d{1,2})\s*(a\.m\.|p\.m\.)$", s, re.I)
        if not m2:
            return None
        h = int(m2.group(1)) % 12
        if m2.group(2).lower().startswith("p"): h += 12
        return h * 60
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
    h = h % 12
    if ap == "PM": h += 12
    return h * 60 + mi

def min_to_hm(v):
    if v is None: return ""
    return "%d:%02d %s" % (v // 60 % 12 or 12, v % 60, "AM" if v < 720 else "PM")

# ----------------------------------------------------------------- Venetian rows
def load_venetian():
    rows = []
    path = os.path.join(ROOT, "data", "c07371e3", "venetian_deepstack_iv.csv")
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            no = r["event_no"].strip()
            name = r["event_name"].replace("<br>- ", " — ").strip()
            sheet_no = V.sheet_from_pdf(r["structure_pdf"])
            sh = V.SHEETS.get(sheet_no)
            buy = int(r["buy_in_usd"]) if r["buy_in_usd"] else None
            gtd = int(r["guarantee_usd"]) if r["guarantee_usd"] else None
            flags = []
            kind = "1day"
            if "Day 2" in name or "Final Table" in name:
                kind = "restart"
            elif re.search(r"\b1[A-F]\b", name):
                kind = "flight"
            elif "(2Day)" in name or "(3Day)" in name:
                kind = "multiday"
            if "Satellite" in name: kind = "satellite"
            section = "main"
            if kind == "satellite": section = "satellite"
            elif kind == "restart": section = "restart"
            elif "Bounty" in name or "PKO" in name: section = "bounty"
            elif kind == "flight" or kind == "multiday": section = "flight"
            if "Tag Team" in name or "Seniors" in name or "LIPS" in name:
                flags.append("restricted/specialty event")
            gtd_note = ""
            if sh and "bounties" in (sh.get("guarantee") or ""):
                gtd_note = "guarantee includes total bounties (sheet)"
                if section == "bounty": flags.append("guarantee includes bounties — ratio not comparable")
            entry_status = sh["entry"] if sh else "not-stated"
            entry_excerpt = (sh.get("extra") or "Sheet states no re-entry/freezeout rule; entry count UNVERIFIED.") if sh else "structure sheet not mapped — UNVERIFIED"
            if entry_status == "flights-bagging-rule":
                entry_excerpt = V.BAGGING + " Within-flight entry count not stated on the sheet."
            reentry = {"flights-bagging-rule": "Not stated within a flight; bagged players barred from later flights (sheet rule)",
                       "subsequent-buy-ins": "Multiple buy-ins indicated by sheet language ('subsequent buy in's')",
                       "not-stated": "UNVERIFIED — no statement on sheet"}.get(entry_status, "UNVERIFIED")
            start_min = hm_to_min(r["time"])
            # plausible-duration estimate (documented heuristic, NOT an official value)
            est_h = {"1day": 10, "flight": 9, "multiday": 9, "satellite": 4, "restart": 8}.get(kind, 10)
            if "RaceDay" in name: est_h = 6
            est_end = (start_min + int(est_h * 60)) if start_min is not None else None
            rows.append(dict(
                id="V%s-%s-%s" % (no, r["date"], r["time"].replace(" ", "")),
                venue="Venetian", date=r["date"], weekday=r["weekday"], time=r["time"],
                event_no=no, name=name, kind=kind, buy_in=buy, guarantee=gtd,
                gtd_note=gtd_note,
                fee_text=(sh["fee"] if sh else ""), fee_verified=bool(sh),
                entry_status=entry_status, entry_excerpt=entry_excerpt, reentry=reentry,
                addon="UNVERIFIED — no statement on sheet", rebuy="UNVERIFIED — no statement on sheet",
                late_reg=(sh["late_reg"] if sh else ""), stack=(sh["stack"] if sh else None),
                level_min=(sh["level_min"] if sh else None), payout=(sh["payout"] if sh else ""),
                est_duration_h=est_h, est_end_hm=min_to_hm(est_end) if kind != "restart" else "",
                section=section, flags=flags,
                source_urls=[V.SCHED_URL] + ([V.sheet_url(sheet_no)] if sheet_no else []),
                structure_url=(V.sheet_url(sheet_no) if sheet_no else ""),
                last_checked=TODAY))
    return rows

# --------------------------------------------------------------- Wynn daily rows
def load_wynn_daily():
    rows = []
    for i, d in enumerate(W.WYNN_DAILY):
        est_h = 9 if d["level_min"] == 30 else 5
        rows.append(dict(
            id="WD%d" % (i+1), venue="Wynn", date="daily", weekday=d["days"], time=d["time"],
            event_no="", name=d["name"], kind="daily", buy_in=d["buy_in"], guarantee=d["guarantee"],
            gtd_note="", fee_text=d["fees"], fee_verified=True,
            entry_status=d["entry"], entry_excerpt=d["entry_excerpt"],
            reentry=d["reentry"], addon=d["addon"], rebuy=d["rebuy"],
            late_reg=d["late_reg"], stack=d["chips"], level_min=d["level_min"],
            payout="", est_duration_h=est_h, est_end_hm="",
            section="spend-advantage" if d["section"] == "spend-advantage" else "multi-entry",
            flags=["Daily event — offered on a repeating weekly schedule"] +
                  (["rebuys/add-ons: spending more money adds chips"] if d["section"] == "spend-advantage" else ["re-entry allowed — not single-entry"]),
            source_urls=[d["source"]], structure_url=d["source"], last_checked=TODAY))
    return rows

# ------------------------------------------------------------------ WPT rows
def load_wpt():
    rows = []
    for i, (dl, wd, tm, name, buy, gtd, chips, levels, kind, rk) in enumerate(W.WPT_ROWS):
        rules = W.RULES[rk]
        iso = None
        m = re.match(r"(Nov|Dec)\.\s+(\d+)", dl)
        if m:
            mo = 11 if m.group(1) == "Nov" else 12
            iso = "2026-%02d-%02d" % (mo, int(m.group(2)))
        section = "main"
        if kind == "satellite": section = "satellite"
        elif kind == "restart" or kind == "finaltable": section = "restart"
        elif kind in ("mysterybounty",) or "Bounty" in name or "Mystery" in name: section = "bounty"
        elif kind == "flight": section = "flight"
        elif rules["entry"] == "re-entry-confirmed": section = "multi-entry"
        if kind == "mysterybounty": section = "bounty"
        gtd_note = ""
        if "Mystery" in name: gtd_note = "mystery-bounty event — guarantee includes bounty pool"
        if "added" in name: gtd_note = "$1,000,000 added by ClubWPT Gold (not available in Nevada) — not a house guarantee"
        flags = []
        if kind == "satellite": flags.append("satellite — prizes are seats/tickets, not cash")
        if "Ladies" in name: flags.append("Ladies event (discounted entry $1,100 vs $11,100 full)")
        if "Seniors" in name: flags.append("Seniors event")
        if kind in ("turbo",): flags.append("turbo structure")
        if "High Roller" in name or "6-Max" in name or "8-Max" in name: flags.append("specialty format")
        if rules["entry"] == "not-stated" and kind not in ("restart","finaltable"):
            flags.append("entry rule UNVERIFIED (per-event terms not captured in audit)")
        start_min = hm_to_min(tm)
        est_h = {"flight": 10, "satellite": 4, "turbo": 4, "mysterybounty": 10}.get(kind, 10)
        rows.append(dict(
            id="W%d" % (i+1), venue="Wynn", date=iso or dl, weekday=wd, time=tm,
            event_no="", name=name, kind=kind, buy_in=buy, guarantee=gtd,
            gtd_note=gtd_note, fee_text=rules["fee"], fee_verified=(rules["fee"] != ""),
            entry_status=rules["entry"], entry_excerpt=rules["excerpt"],
            reentry=rules["reentry"],
            addon="UNVERIFIED — not captured" if rules["entry"] == "not-stated" else "Not stated in per-event terms",
            rebuy="UNVERIFIED — not captured" if rules["entry"] == "not-stated" else "Not stated in per-event terms",
            late_reg=rules["reentry"].split("(")[-1].rstrip(")") if "level" in rules["reentry"] else "",
            stack=chips or None,
            level_min=(int(levels.split("/")[0]) if levels and levels.split("/")[0].isdigit() else None),
            payout="", est_duration_h=est_h,
            est_end_hm=min_to_hm(start_min + est_h * 60) if start_min is not None else "",
            section=section, flags=flags,
            source_urls=[W.WPT_SCHED] + ([W.WPT_STRUCTS] if rk != "unknown" else [W.WPT_STRUCTS]),
            structure_url=W.WPT_STRUCTS, last_checked=TODAY))
    return rows

# --------------------------------------------------------------- daily plan
def build_plan(events):
    plan = {}
    by_date = {}
    for e in events:
        if e["section"] == "restart" or e["date"] in ("daily", None): continue
        if not re.match(r"2026-\d\d-\d\d", str(e["date"])): continue
        by_date.setdefault(e["date"], []).append(e)
    for dt in sorted(by_date):
        evs = [e for e in by_date[dt] if e["kind"] not in ("restart",)]
        def startmin(e): return hm_to_min(e["time"]) or 0
        evs.sort(key=startmin)
        # overlap flags
        overlaps = []
        for i in range(len(evs)):
            for j in range(i+1, len(evs)):
                a, b = evs[i], evs[j]
                sa, sb = startmin(a), startmin(b)
                ea = sa + (a["est_duration_h"] or 0) * 60
                if ea > sb and not (a["event_no"] and a["event_no"] == b["event_no"]):
                    if a["kind"] != "satellite" and b["kind"] != "satellite":
                        overlaps.append("%s (%s) plausibly ends %s — overlaps %s (%s)" % (
                            a["name"][:40], a["time"], min_to_hm(ea), b["name"][:40], b["time"]))
        # primary: earliest non-satellite, non-multi-entry-preferred main event
        cands = [e for e in evs if e["section"] in ("main", "flight", "bounty", "multi-entry", "spend-advantage")]
        primary = None
        for e in cands:
            if e["section"] in ("main", "flight") and e["guarantee"]:
                primary = e; break
        if not primary:
            for e in cands:
                if e["section"] != "satellite":
                    primary = e; break
        fallback, cond = None, ""
        if primary:
            pend = startmin(primary) + (primary["est_duration_h"] or 0) * 60
            late = [e for e in evs if e is not primary and e["kind"] not in ("restart",) and startmin(e) > startmin(primary)]
            late.sort(key=startmin, reverse=True)
            for e in late:
                if startmin(e) >= pend:
                    fallback, cond = e, "Feasible in sequence: %s starts %s, after the primary's plausible end (%s, estimate)." % (e["name"][:40], e["time"], min_to_hm(pend))
                    break
            if not fallback and late:
                e = late[0]
                fallback = e
                cond = "CONDITIONAL: %s starts %s with registration closing %s. The primary plausibly ends %s (estimate) — only playable if you exit the primary early." % (
                    e["name"][:40], e["time"], e["late_reg"] or "(not stated)", min_to_hm(pend))
        plan[dt] = dict(date=dt, weekday=WEEKDAY.get(dt, ""),
            primary=(primary["id"] if primary else None),
            primary_name=(primary["name"] if primary else "No startable event found"),
            primary_time=(primary["time"] if primary else ""),
            fallback=(fallback["id"] if fallback else None),
            fallback_name=(fallback["name"] if fallback else "None"),
            fallback_time=(fallback["time"] if fallback else ""),
            fallback_condition=cond, overlaps=overlaps)
    return plan

# ------------------------------------------------------------------ sources
def build_sources(all_events):
    srcs = {}
    def add(url, label, official=True):
        if url and url not in srcs:
            srcs[url] = dict(url=url, label=label, official=official, last_checked=TODAY)
    add(V.SCHED_URL, "Venetian DeepStack Extravaganza IV — official schedule page")
    for no in V.SHEETS:
        add(V.sheet_url(no), "Venetian DSE IV structure sheet %s — %s" % (no, V.SHEETS[no]["title"]))
    add(W.DAILY_STRUCTS, "Wynn daily tournament structures + terms (PDF)")
    add(W.DAILY_POSTER, "Wynn daily tournament poster (PDF)")
    add(W.WPT_SCHED, "Wynn WPT World Championship schedule (PDF)")
    add(W.WPT_STRUCTS, "Wynn WPT World Championship structures / general terms (PDF)")
    add(W.WYNN_POKER, "Wynn Las Vegas poker room — official page")
    add(H.VEN_RESORT_FEE, "Venetian resort fee page")
    add(H.VEN_TERMS, "Venetian hotel terms & conditions (tax, parking, cancellation)")
    add(H.VEN_POKER_RATES, "Venetian 2026 poker suite rates & play requirements")
    add("https://www.venetianlasvegas.com/resort/casino/poker.html", "Venetian poker room — official page")
    add("https://www.wynnlasvegas.com/terms-and-conditions/850257", "Wynn terms & conditions (resort fee)")
    add("https://treasureisland.com/hotel/deluxe-rooms", "Treasure Island deluxe rooms (resort fee)")
    add("https://www.caesars.com/caesars-palace", "Caesars Palace — official page")
    add("https://www.caesars.com/harrahs-las-vegas", "Harrah's Las Vegas — official page")
    add("https://www.caesars.com/horseshoe-las-vegas", "Horseshoe Las Vegas — official page")
    add("https://bellagio.mgmresorts.com/en/casino/poker.html", "Bellagio poker room — official page")
    add("https://aria.mgmresorts.com/en.html", "ARIA — official page")
    add("https://www.pokertda.com/poker-tda-rules/", "Tournament Directors Association rules (cited by Venetian/Wynn sheets)")
    for hotel, venue, mi, mi2, note, url, done in H.WALKS:
        if "google.com/maps" in url:
            add(url, "Google Maps walking directions: %s → %s poker room" % (hotel, venue), official=True)
    for e in all_events:
        for u in e["source_urls"]:
            add(u, "Official source (event rows)")
    return list(srcs.values())

# ------------------------------------------------------------------- flags
def build_flags(events, hotels):
    flags = []
    def F(title, detail, source=""):
        flags.append(dict(id="F%02d" % (len(flags)+1), title=title, detail=detail, source=source))
    F("No Venetian event is confirmed single-entry / freezeout",
      "All 37 DSE IV structure sheets were read on 2026-11-17. None states a re-entry or freezeout rule for single-flight events; omission is not confirmation. Rows remain 'entry rule unverified'. Events #18/#58 (Valuetown) reference 'subsequent buy in's' and are treated as multi-entry. Multi-flight events carry the bagging rule only.",
      V.SCHED_URL)
    F("Wynn daily events all allow re-entry (Friday adds rebuys + add-on)",
      "Official daily terms confirm re-entry on Mon–Thu $200, Sat/Sun $200 and Nightly $160; the Friday $240 confirms 'Re-entry is NOT allowed' but has unlimited $200 rebuys and one $100 add-on. No Wynn daily qualifies as single-entry.",
      W.DAILY_STRUCTS)
    F("WPT World Championship schedule has internal date/label conflicts",
      "; ".join(W.WPT_IRREGULARITIES), W.WPT_SCHED)
    F("Super Gold Million & WPT World Championship entry rules unverified",
      "Per-event Registration lines for the $400/$3M Super Gold Million and the $10,400 World Championship were not captured in the structures-PDF audit (text-extraction gap). Flagged, not inferred.",
      W.WPT_STRUCTS)
    F("No date-specific hotel room quotes captured",
      "Official booking engines did not yield dated totals in this session. Venetian $119/$209 are conditional starting rates with a play requirement, not quotes. All date-specific totals remain blank; per-date official booking links are provided and the scheduled re-check will log quotes when available.",
      H.VEN_POKER_RATES)
    F("Resort fees unverified for Bellagio, Caesars Palace, Harrah's, Horseshoe, ARIA",
      "No official page states an amount (or the page is marketing copy). Third-party figures conflict and are not used. Venetian $55+tax, Wynn $55+tax (bookings on/after Jan 15 2025) and Treasure Island $49.95+tax are verified from official pages.",
      "https://www.caesars.com/caesars-palace")
    F("Walk-time matrix incomplete for Wynn venue",
      "Hotel→Venetian walking times verified for 7 hotels + on-site (Google Maps, 2026-11-17). ARIA at 31 min exceeds the 30-minute limit. Hotel→Wynn pairs for Bellagio/ARIA/Caesars/TI/Harrah's/Horseshoe are unmeasured — links provided, scheduled for automated re-check.",
      "https://www.google.com/maps/dir/?api=1&origin=Wynn+Las+Vegas,+3131+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109&destination=The+Venetian+Resort,+3355+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109&travelmode=walking")
    F("Bellagio Saturday buy-in conflict",
      "Bellagio official sources conflict on the Saturday NLH buy-in ($1,000 vs $1,100) and prior audit could not capture start time/date. Row carried with conflict label; not resolved by inference.",
      "https://bellagio.mgmresorts.com/en/casino/poker.html")
    F("8 AM start target not met by any verified event",
      "The earliest verified starts are 9:10 AM (Venetian Event #46 satellite, Dec 12) and 10:00 AM/10:10 AM for most mains. No official schedule shows an 8:00 AM tournament in the window; the daily plan starts at the earliest verified start.",
      V.SCHED_URL)
    F("Event durations are labeled estimates",
      "No official source publishes finish times. Plausible-duration estimates (1-day ≈ 10 h, flights ≈ 9 h, turbo/satellite ≈ 4–6 h) drive overlap flags and the daily plan; every such value is labeled as an estimate on the page.",
      "")
    return flags

def main():
    ven = load_venetian()
    wd = load_wynn_daily()
    wpt = load_wpt()
    events = ven + wd + wpt
    plan = build_plan(ven + wpt)
    sources = build_sources(events)
    flags = build_flags(events, H.HOTELS)

    # cross-check: every Venetian row's event number must belong to its mapped sheet
    checks = []
    for e in ven:
        m = re.search(r"structure_(\d+)", e["structure_url"] or "")
        if not m: 
            checks.append("UNMAPPED %s %s" % (e["date"], e["name"][:30])); continue
        sh = V.SHEETS[m.group(1)]
        if e["event_no"] and int(e["event_no"]) not in sh["events"]:
            checks.append("EVENT-NO MISMATCH sheet %s row %s %s" % (m.group(1), e["event_no"], e["name"][:30]))
    for e in events:
        if e["section"] != "restart" and not e["source_urls"]:
            checks.append("NO SOURCE %s" % e["id"])
    results = dict(cross_checks=checks, checked=TODAY)

    with open(os.path.join(OUT, "events.json"), "w") as f:
        json.dump(dict(meta=dict(built=TODAY, note="Integrated event table — every row carries official source URL(s) and last_checked. Entry rules unverified unless an excerpt confirms them."),
                       events=events), f, indent=1)
    with open(os.path.join(OUT, "hotels.json"), "w") as f:
        json.dump(dict(meta=dict(built=TODAY, tax=H.TAX, tax_source=H.TAX_SOURCE,
                                 note="Rates are kept as a dated log. True cost/night = (rate + resort fee) x (1 + tax)."),
                       hotels=H.HOTELS, walks=[dict(hotel=a, venue=b, minutes=c, distance=d, note=n, url=u, verified=v) for a,b,c,d,n,u,v in H.WALKS]), f, indent=1)
    with open(os.path.join(OUT, "sources.json"), "w") as f:
        json.dump(dict(meta=dict(built=TODAY), sources=sources), f, indent=1)
    with open(os.path.join(OUT, "plan.json"), "w") as f:
        json.dump(dict(meta=dict(built=TODAY, note="Durations are estimates; overlap flags use start time, late-registration cutoff and plausible duration."), plan=plan), f, indent=1)
    with open(os.path.join(OUT, "flags.json"), "w") as f:
        json.dump(dict(meta=dict(built=TODAY), flags=flags), f, indent=1)
    with open(os.path.join(OUT, "crosscheck.json"), "w") as f:
        json.dump(results, f, indent=1)
    print("events:", len(events), "| venetian:", len(ven), "| wynn daily:", len(wd), "| wpt:", len(wpt))
    print("sources:", len(sources), "| flags:", len(flags), "| plan days:", len(plan))
    print("cross-check issues:", len(checks))
    for c in checks: print("  -", c)

if __name__ == "__main__":
    main()
