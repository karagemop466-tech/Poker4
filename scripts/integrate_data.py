#!/usr/bin/env python3
"""Generate the integrated Poker4 dashboard (GitHub Pages root site).

Inputs (all already source-linked, all produced by tools/sync_official_sources.py
or curated in data/poker4.json):
  data/poker4.json            venues, hotels, questions, suggestions, flags, policy
  data/schedule-snapshot.json every printed row of the official Venetian calendar
  data/structure-audit.json   field-matched values from every linked structure sheet
  data/hotel-facts.json       verbatim fee / tax / parking / cancellation sentences
  data/url-checks.json        per-URL last-checked date, status, hash, change flags
  data/change-log.json        value-level changes recorded across runs
  data/tournaments.json       Wynn / Caesars / Bellagio rows kept from earlier passes
  data/c07371e3/*.csv         Wynn daily + WPT + Bellagio detail captured earlier

Outputs: the root HTML pages, venues/*.html, data/site-events.json,
data/rate-log.json, data/walks.json, data/search-index.json, app.js, style.css.

Nothing is invented here: a blank cell means the official source did not print the
value, and the row carries a flag saying so.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT
VENUES_OUT = ROOT / "venues"

E = html.escape


def load(name, default=None):
    path = DATA / name
    if not path.exists():
        if default is not None:
            return default
        raise SystemExit(f"missing required data file: data/{name} — run python3 tools/sync_official_sources.py (or wait for the scheduled job)")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


CFG = load("poker4.json")
SCHED = load("schedule-snapshot.json", {"meta": {}, "rows": []})
AUDIT = load("structure-audit.json", {"sheets": {}})
FACTS = load("hotel-facts.json", {"sources": {}})
CHECKS = load("url-checks.json", {})
CHANGELOG = load("change-log.json", {"entries": []})
LEGACY = load("tournaments.json", {"sources": {}, "reentry_or_addon": []})
SNAPSHOT_AT = (CHECKS.get(list(CHECKS)[0]) or {}).get("checked_at", "") if CHECKS else ""
# Prefer the snapshot date so a rebuild is byte-for-byte reproducible; fall back to today.
TODAY = (SNAPSHOT_AT or "")[:10] or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def rel(url: str) -> str:
    """Map a tracked URL to its captured raw text, when one exists."""
    for src in load("tracked-sources.json")["sources"]:
        if src["url"] == url and src.get("save_text_to"):
            return "../" + src["save_text_to"] if False else src["save_text_to"]
    return ""


def src_link(url: str, label: str | None = None, cls: str = "source-link") -> str:
    if not url:
        return '<span class="unknown">no official source</span>'
    text = E(label or url.split("//")[-1].split("/", 1)[0])
    return f'<a class="{cls}" href="{E(url)}" target="_blank" rel="noopener">{text} ↗</a>'


def money(v, blank='<span class="unknown">—</span>'):
    if v in (None, "", 0):
        return blank if v != 0 else "$0"
    if isinstance(v, (int, float)):
        v = int(round(v)) if float(v).is_integer() else round(v, 2)
        return "$" + (f"{v:,}" if isinstance(v, int) else f"{v:,.2f}")
    return E(str(v))


def last_checked_for(urls) -> tuple[str, bool]:
    """(most recent checked date, any source value changed) for a row's sources."""
    dates, changed = [], False
    for u in urls:
        rec = CHECKS.get(u)
        if not rec:
            continue
        if rec.get("checked_at"):
            dates.append(rec["checked_at"][:10])
        if rec.get("values_changed"):
            changed = True
    return (max(dates) if dates else "", changed)


# ---------------------------------------------------------------- source registry
def registry_label(url: str) -> str:
    for src in load("tracked-sources.json")["sources"]:
        if src["url"] == url:
            return src.get("label", url)
    return url


# ------------------------------------------------------------------ event building
SHEET_BY_EVENT: dict[int, list[dict]] = {}
for key, sheet in (AUDIT.get("sheets") or {}).items():
    if not re.fullmatch(r"V_S\d+", key):
        continue
    nums = [int(n) for n in re.findall(r"\d{1,3}", sheet.get("event_numbers") or "")]
    for n in nums:
        SHEET_BY_EVENT.setdefault(n, []).append({**sheet, "_key": key})

VENUE_BY_ID = {v["id"]: v for v in CFG["venues"]}
AMBIGUOUS_NOTE = "several sheets print this event number (different starting flights) — the row lists both"


def pick_sheet(event_no: int, time: str | None, date: str | None):
    cands = SHEET_BY_EVENT.get(event_no) or []
    if not cands:
        return None, "no structure sheet printed for this event number"
    if len(cands) == 1:
        return cands[0], None
    timed = [c for c in cands if (c.get("start_time") or "").strip().upper() == (time or "").upper()]
    if len(timed) == 1:
        return timed[0], None
    return cands[0], AMBIGUOUS_NOTE


KIND_PATTERNS = [
    ("Continuation (not an entry)", r"DAY \d (RESTART|RE-ENTRY)|FINAL TABLE|PLAY DOWN"),
    ("Satellite", r"SATELLITE"),
    ("Bounty / PKO", r"BOUNTY|KNOCK-OUT|PKO"),
    ("Seniors (50+)", r"SENIORS"),
    ("Ladies", r"LADIES"),
    ("Mixed game", r"POT LIMIT OMAHA|PLO |BIG O|H\.O\.R\.S\.E|HORSE|TRIPLE DRAW|OMAHA"),
    ("Multi-flight", r"\b1[A-F]\b|DAY A|STARTING FLIGHT"),
]


def classify(name: str) -> tuple[str, list[str]]:
    tags = []
    for label, pat in KIND_PATTERNS:
        if re.search(pat, name or "", re.I):
            if label == "Multi-flight":
                tags.append(label)
            else:
                tags.append(label)
    kind = "Tournament"
    for label, pat in KIND_PATTERNS:
        if label == "Continuation (not an entry)" and re.search(pat, name or "", re.I):
            kind = label
    if re.search(r"SATELLITE", name or "", re.I):
        kind = "Satellite"
    if not tags:
        tags = ["Plain NLH one-day" if re.search(r"1DAY", name or "", re.I) else "Other format"]
    return kind, tags


SPEND_ADVANTAGE_PATTERNS = [
    (r"subsequent buy", "sheet states later buy-ins cost the same, i.e. more than one entry can be bought"),
    (r"re-?buy", "rebuy format"),
    (r"re-?entr", "re-entry allowed"),
    (r"add-?\s?on", "add-on offered"),
]

events: list[dict] = []
for row in SCHED["rows"]:
    name = (row.get("event_name") or "").upper()
    buy = row.get("buy_in_usd")
    gtd = row.get("guarantee_usd")
    sheet, sheet_note = pick_sheet(row["event_no"], row.get("time"), row.get("date"))
    sheet_url = sheet.get("source") if sheet else ""
    sources = [row["source"]] + ([sheet_url] if sheet_url else [])
    kind, tags = classify(name)
    entry = {
        "id": f"V{row['event_no']}-{row.get('date')}-{(row.get('time') or '').replace(' ', '').lower()}",
        "venue": "venetian",
        "venue_name": "The Venetian Poker Room",
        "event_no": row["event_no"],
        "name": f"${buy:,} {name.title()}" if buy else name.title(),
        "name_printed": name,
        "date": row.get("date"),
        "weekday": row.get("weekday"),
        "time": row.get("time"),
        "registration_closes": row.get("registration_closes"),
        "buy_in_usd": buy,
        "guarantee_usd": gtd,
        "guarantee_printed": row.get("guarantee_usd") is not None,
        "starting_chips": row.get("starting_chips"),
        "level_duration": row.get("level_duration"),
        "kind": kind,
        "tags": tags,
        "is_flight": "Multi-flight" in tags or bool(re.search(r"\b1[A-F]\b", name)),
        "is_continuation": kind == "Continuation (not an entry)",
        "rules": {
            "single_entry": {"status": "unverified", "value": None, "excerpt": None,
                             "source": sheet_url, "retrieved": (sheet or {}).get("retrieved")},
            "re_entry": {"status": "not_stated_in_sheet", "value": None, "excerpt": None,
                         "source": sheet_url, "retrieved": (sheet or {}).get("retrieved")},
            "add_on": {"status": "not_stated_in_sheet", "value": None, "excerpt": None,
                       "source": sheet_url, "retrieved": (sheet or {}).get("retrieved")},
            "fee": {"status": "unverified", "value": None, "excerpt": None,
                    "source": sheet_url, "retrieved": (sheet or {}).get("retrieved")},
        },
        "sources": sources,
        "sheet_key": (sheet or {}).get("_key"),
        "sheet_note": sheet_note,
    }
    if sheet:
        fee = sheet.get("house_fee_usd")
        pool = sheet.get("pool_per_entry_usd")
        entry["house_fee_usd"] = fee
        entry["pool_per_entry_usd"] = pool
        entry["sheet_start_time"] = sheet.get("start_time")
        entry["sheet_late_registration"] = sheet.get("late_registration")
        entry["sheet_guarantee_text"] = sheet.get("guarantee")
        entry["sheet_title"] = sheet.get("title")
        entry["payout_pct_of_field"] = sheet.get("payout_pct_of_field")
        entry["levels_total"] = sheet.get("levels_listed")
        entry["breaks_listed"] = sheet.get("breaks_listed")
        policy = sheet.get("entry_policy")
        ex = (sheet.get("clauses") or {})
        flat_excerpts = [s for arr in ex.values() for s in (arr or [])]
        sub = sheet.get("subsequent_entry_excerpt")
        if policy == "confirmed_single_entry":
            entry["rules"]["single_entry"] = {"status": "confirmed", "value": "one entry",
                                              "excerpt": (ex.get("single_entry_confirmed") or ex.get("entry_forbidden") or [""])[0],
                                              "source": sheet_url, "retrieved": sheet.get("retrieved")}
            entry["single_entry_confirmed"] = True
        elif policy in ("not_single_entry", "limited_reentry"):
            entry["rules"]["single_entry"] = {"status": "no", "value": "multiple entries possible",
                                              "excerpt": (ex.get("reentry_allowed") or ex.get("reentry_limited") or [sub or ""])[0],
                                              "source": sheet_url, "retrieved": sheet.get("retrieved")}
            entry["rules"]["re_entry"] = {"status": "confirmed_allowed", "value": "yes",
                                          "excerpt": (ex.get("reentry_allowed") or ex.get("reentry_limited") or [sub or ""])[0],
                                          "source": sheet_url, "retrieved": sheet.get("retrieved")}
            entry["spend_advantage"] = True
        elif policy == "contradictory_in_sheet":
            entry["rules"]["single_entry"] = {"status": "conflict", "value": None,
                                              "excerpt": "; ".join(flat_excerpts[:2]) or None,
                                              "source": sheet_url, "retrieved": sheet.get("retrieved")}
        if sub:
            entry["rules"]["re_entry"] = {"status": "indicated", "value": "sheet mentions subsequent buy-ins",
                                          "excerpt": sub, "source": sheet_url, "retrieved": sheet.get("retrieved")}
            entry["spend_advantage"] = True
        entry["spend_advantage_evidence"] = [
            reason for pat, reason in SPEND_ADVANTAGE_PATTERNS
            if re.search(pat, (sub or "") + " " + " ".join(flat_excerpts), re.I)
        ]
        if fee is not None and entry["buy_in_usd"]:
            entry["rules"]["fee"] = {
                "status": "confirmed",
                "value": f"${fee} of ${entry['buy_in_usd']} withheld; ${pool} per entry to the prize pool"
                         if pool is not None else f"${fee} of ${entry['buy_in_usd']} withheld",
                "excerpt": f"$ {fee} of the $ {entry['buy_in_usd']} Buy-In is withheld for house fees (Rake + Staff)."
                           + (f" The prize pool consists of $ {pool} of every $ {entry['buy_in_usd']} Buy In." if pool is not None else ""),
                "source": sheet_url,
                "retrieved": sheet.get("retrieved"),
            }
        else:
            entry["rules"]["fee"] = {"status": "unverified", "value": None, "excerpt": None,
                                     "source": sheet_url, "retrieved": sheet.get("retrieved")}
        if sheet.get("guarantee") and gtd is None:
            entry["guarantee_from_sheet_text"] = sheet["guarantee"]
    entry["single_entry_confirmed"] = bool(entry.get("single_entry_confirmed"))
    entry["rankable"] = bool(
        entry.get("buy_in_usd") and entry.get("guarantee_usd")
        and entry["rules"]["fee"]["status"] == "confirmed"
        and not entry.get("is_continuation")
    )
    if entry.get("buy_in_usd") and entry.get("guarantee_usd"):
        entry["gtd_ratio"] = round(entry["guarantee_usd"] / entry["buy_in_usd"], 2)
        if entry["rules"]["fee"]["status"] == "confirmed" and entry.get("pool_per_entry_usd"):
            entry["gtd_over_pool_contribution"] = round(entry["guarantee_usd"] / entry["pool_per_entry_usd"], 2)
    checked, changed = last_checked_for(entry["sources"])
    entry["last_checked"] = checked
    entry["source_changed"] = changed
    if not entry.get("single_entry_confirmed") and not entry.get("spend_advantage"):
        entry["flags"] = ["single-entry unverified"]
    else:
        entry["flags"] = []
    if entry.get("spend_advantage"):
        entry["flags"].append("spend-advantage format — excluded from the single-entry list")
    if entry.get("sheet_note"):
        entry["flags"].append("structure sheet ambiguous")
    if entry.get("rankable") is False and not entry.get("is_continuation"):
        entry["flags"].append("not ranked — entry fee or guarantee unconfirmed")
    events.append(entry)

# --- non-Venetian rooms: rows preserved from the earlier verified captures ------
WYNN_DAILY = list(csv.DictReader(open(DATA / "c07371e3" / "wynn_daily.csv", newline="", encoding="utf-8-sig")))
WYNN_WPT = list(csv.DictReader(open(DATA / "c07371e3" / "wynn_wpt.csv", newline="", encoding="utf-8-sig")))
BELLAGIO = list(csv.DictReader(open(DATA / "c07371e3" / "bellagio.csv", newline="", encoding="utf-8-sig")))


def add_room_row(venue_id, venue_name, *, when, time, name, buy, gtd, reentry, addon, fee_txt,
                 srcs, note=None, reg_closes=None, chips=None):
    entry = {
        # stable id: a per-process hash() would move every anchor on every rebuild
        "id": f"{venue_id}-{when}-{(time or '').replace(' ', '').lower()}-{hashlib.sha1(name.encode()).hexdigest()[:5]}",
        "venue": venue_id, "venue_name": venue_name,
        "event_no": None, "name": name, "name_printed": name.upper(),
        "date": None, "printed_date": when, "weekday": None, "time": time,
        "registration_closes": reg_closes, "buy_in_usd": buy, "guarantee_usd": gtd,
        "guarantee_printed": gtd is not None, "starting_chips": chips,
        "kind": "Tournament", "tags": ["Recurring / weekly"],
        "is_flight": False, "is_continuation": False,
        "rules": {
            "single_entry": {"status": "no" if (reentry or addon) else "unverified",
                             "value": "multiple entries allowed" if (reentry or addon) else None,
                             "excerpt": reentry or addon, "source": (srcs or [None])[0], "retrieved": "2026-11-16"},
            "re_entry": {"status": "confirmed_allowed" if reentry else "unverified",
                         "value": reentry or None, "excerpt": reentry, "source": (srcs or [None])[0], "retrieved": "2026-11-16"},
            "add_on": {"status": "confirmed_allowed" if addon else "unverified",
                       "value": addon or None, "excerpt": addon, "source": (srcs or [None])[0], "retrieved": "2026-11-16"},
            "fee": {"status": "confirmed" if fee_txt else "unverified", "value": fee_txt,
                    "excerpt": fee_txt, "source": (srcs or [None])[0], "retrieved": "2026-11-16"},
        },
        "sources": srcs, "sheet_key": None, "notes": note,
        "spend_advantage": bool(reentry or addon),
        "rankable": False,
        "flags": ["schedule not re-published in this snapshot's dated calendar", "single-entry excluded (entry rules allow more)"] if (reentry or addon)
                 else ["single-entry unverified"],
    }
    if buy and gtd:
        entry["gtd_ratio"] = round(gtd / buy, 2)
    checked, changed = last_checked_for(srcs)
    entry["last_checked"] = checked
    entry["source_changed"] = changed
    events.append(entry)


for r in WYNN_DAILY:
    add_room_row("wynn", "Wynn Las Vegas Poker", when=r["schedule"], time=r["time"],
                 name=r["event_name"], buy=int(r["buy_in_usd"]) if r["buy_in_usd"] else None,
                 gtd=int(r["guarantee_usd"]) if r["guarantee_usd"] else None,
                 reentry=None if r["re_entry"].lower().startswith("not") else r["re_entry"],
                 addon=None if r["rebuy_addon"].lower().startswith("none") else r["rebuy_addon"],
                 fee_txt=r["fees_and_staff"] or None, reg_closes=r.get("registration_end"),
                 srcs=[r["source"],
                       "https://cdn.wynnresorts.com/image/upload/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf"],
                 note=r.get("flag") or None)
for r in WYNN_WPT:
    add_room_row("wynn", "Wynn Las Vegas Poker", when=r["dates"], time=None, name=r["event_name"],
                 buy=int(r["buy_in_usd"]) if r["buy_in_usd"] else None,
                 gtd=int(r["guarantee_usd"]) if r["guarantee_usd"] else None,
                 reentry=None if "NOT CAPTURED" in r["re_entry"].upper() else r["re_entry"],
                 addon=None, fee_txt=None,
                 srcs=[r["source"],
                       "https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf",
                       "https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf"],
                 note="WPT World Championship series row (Nov 27 – Dec 21, 2026) from the venue's own PDFs" if "NOT CAPTURED" not in r["re_entry"].upper()
                      else "entry terms not captured from the official PDFs — treated as unverified, not as single-entry")
for r in BELLAGIO:
    srcs = [r["source"]]
    add_room_row("bellagio", "Bellagio Poker Room", when=r["day"], time="11:00 AM",
                 name=r["event_name"],
                 buy=int(re.sub(r"[^\d]", "", r["buy_in_usd"])) if r["buy_in_usd"].isdigit() else None,
                 gtd=int(r["guarantee_usd"]) if r["guarantee_usd"] else None,
                 reentry=None if "NOT CAPTURED" in r["re_entry"].upper() else r["re_entry"],
                 addon=None,
                 fee_txt=(r["house_fee_usd"] + (" + optional gratuity " + r["optional_gratuity_usd"] if r["optional_gratuity_usd"] else "")) if r["house_fee_usd"] else None,
                 srcs=srcs, note=r["flag"] or None,
                 chips=int(r["starting_chips"]) if r["starting_chips"].isdigit() else None)
for r in (CFG.get("preserved_rows", {}).get("caesars") or LEGACY.get("reentry_or_addon", [])):
    if r.get("venue", "").startswith("Caesars"):
        add_room_row("caesars", "Caesars Palace Poker Room", when=r["day"], time=r["time"],
                     name=r["name"], buy=r.get("buy_in"), gtd=r.get("guarantee"),
                     reentry=(r.get("reentry_addon") or "").split(";")[0] or None,
                     addon=(r["reentry_addon"].split("add-on")[1].strip(" ;") if "add-on" in (r.get("reentry_addon") or "").lower() else None),
                     fee_txt=None, srcs=r.get("source_urls") or [LEGACY["sources"][k]["url"] for k in r.get("sources", []) if k in LEGACY.get("sources", {})],
                     note="Preserved from the earlier capture; the official daily flyer URL now returns 404, so this row needs re-verification")

events.sort(key=lambda e: (e.get("date") or "9999-99-99", e.get("time") or "", e["venue"]))

# ------------------------------------------------------------------ hotel sources
# Which tracked official pages carry the fee / tax / parking / cancellation wording that
# applies to each property.  The sync job writes facts keyed by URL, so the join lives here
# rather than being duplicated into data/poker4.json.  Sister towers share the complex's
# published fee pages (their room rates stay separate).
FACT_VENUE = {"venetian": "The Venetian", "palazzo": "The Venetian", "penn-tellers": "The Venetian",
             "wynn": "Wynn Las Vegas", "encore": "Wynn Las Vegas", "bellagio": "Bellagio",
             "caesars": "Caesars Palace", "casino": "Caesars Palace", "aria": "ARIA",
             "ti": "Treasure Island", "horseshoe": "Horseshoe", "harrahs": "Harrah's"}
TRACKED = load("tracked-sources.json")["sources"]


def hotel_fact_urls(h):
    venue = FACT_VENUE.get(h["id"])
    out = []
    for key in (h.get("source_keys") or []):
        u = KEY_URL_ALL.get(key)
        if u and (u in FACTS_SOURCES) and u not in out:
            out.append(u)
    if venue:
        for src in TRACKED:
            if src.get("extract_facts") and src.get("venue") == venue:
                u = src["url"]
                if u in FACTS_SOURCES and u not in out:
                    out.append(u)
    for extra in (h.get("official_page"), (h.get("resort_fee") or {}).get("source"),
                  (h.get("tax") or {}).get("source"), (h.get("parking") or {}).get("source"),
                  (h.get("cancellation") or {}).get("source")):
        if extra and extra in FACTS_SOURCES and extra not in out:
            out.append(extra)
    return out


FACTS_SOURCES = FACTS.get("sources") or {}
KEY_URL_ALL = {k: v for k, v in json.load(open(DATA / "source-keys.json", encoding="utf-8")).items()}

# ------------------------------------------------------------------ rate log + walks
rate_log: list[dict] = []
for h in CFG["hotels"]:
    for i, entry in enumerate(h.get("rate_log") or []):
        rate_log.append({"hotel_id": h["id"], "property": h["property"], "seq": i + 1, **entry})
for h in CFG["hotels"]:
    for url in hotel_fact_urls(h):
        facts = (FACTS_SOURCES.get(url) or {}).get("facts") or {}
        for key in ("resort_fee", "room_tax", "parking", "cancellation"):
            for sent in (facts.get(key) or [])[:3]:
                rate_log.append({
                    "hotel_id": h["id"], "property": h["property"], "seq": 90,
                    "observed_on": TODAY,
                    "label": f"official {key.replace('_', ' ')} wording",
                    "amount_usd": None, "qualifier": sent, "source": url,
                    "quote_status": f"verbatim sentence captured {SNAPSHOT_AT[:10] or TODAY}",
                    "field": key,
                })
walks: list[dict] = []
for h in CFG["hotels"]:
    for vid in h.get("venue_ids") or []:
        walks.append({
            "hotel_id": h["id"], "hotel": h["property"], "venue_id": vid,
            "venue": (VENUE_BY_ID.get(vid) or {}).get("name", vid),
            "minutes": (h.get("walk") or {}).get("minutes"),
            "meets_30_min": (h.get("walk") or {}).get("meets_30_min", "unverified"),
            "status": (h.get("walk") or {}).get("status"),
            "source": (h.get("walk") or {}).get("source"),
        })
with open(DATA / "rate-log.json", "w", encoding="utf-8") as fh:
    json.dump({"meta": {"generated_at": SNAPSHOT_AT or TODAY,
                        "policy": "A dated log, not a single value. Every line keeps the date it was observed, the wording it came from and whether it is a dated quote at all."},
               "entries": rate_log}, fh, indent=1)
with open(DATA / "walks.json", "w", encoding="utf-8") as fh:
    json.dump({"meta": {"generated_at": SNAPSHOT_AT or TODAY, "rule": CFG["walk_policy"]["rule"],
                        "how_to_close": CFG["walk_policy"]["how_to_close"]},
               "pairs": walks}, fh, indent=1)
with open(DATA / "site-events.json", "w", encoding="utf-8") as fh:
    json.dump({"meta": {"generated_at": SNAPSHOT_AT or TODAY, "rows": len(events),
                        "verified_single_entry": sum(1 for e in events if e.get("single_entry_confirmed")),
                        "rankable": sum(1 for e in events if e.get("rankable")),
                        "spend_advantage": sum(1 for e in events if e.get("spend_advantage"))},
               "events": events}, fh, indent=1)

# ------------------------------------------------------------------------ day plan
def to_min(t: str | None):
    if not t:
        return None
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", t.upper())
    if not m:
        return None
    h = int(m.group(1)) % 12 + (12 if m.group(3) == "PM" else 0)
    return h * 60 + int(m.group(2))


days: dict[str, dict] = {}
for ev in events:
    if not ev.get("date") or ev.get("is_continuation"):
        continue
    days.setdefault(ev["date"], []).append(ev)

plan = []
for date, rows in sorted(days.items()):
    rows = sorted(rows, key=lambda r: to_min(r["time"]) or 0)
    primary = rows[0]
    fallback = None
    for cand in rows[1:]:
        if (to_min(cand["time"]) or 0) >= (to_min(primary.get("registration_closes")) or 0):
            fallback = cand
            break
    cont = [e for e in events if e.get("date") == date and e.get("is_continuation")]
    conflicts = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            ac = to_min(a.get("registration_closes"))
            bs = to_min(b.get("time"))
            if ac and bs and bs < ac:
                conflicts.append(f"{a['name']} registration stays open until {a['registration_closes']}, which is after {b['name']} starts at {b['time']} — the two cannot be played in sequence unless you are out of the first event before it closes")
            elif not ac:
                conflicts.append(f"{a['name']} prints no registration deadline, so overlap with {b['name']} cannot be settled from official data")
    plan.append({
        "date": date, "weekday": rows[0].get("weekday"),
        "primary": primary, "fallback": fallback,
        "restarts": [c["name"] for c in cont],
        "overlap_notes": conflicts,
        "entries_usd": sum(c.get("buy_in_usd") or 0 for c in rows),
    })
with open(DATA / "day-plan.json", "w", encoding="utf-8") as fh:
    json.dump({"meta": {"generated_at": SNAPSHOT_AT or TODAY,
                        "basis": "start time + printed registration-closes deadline + Day-2 restart rows on the official calendar",
                        "days": len(plan)},
               "days": [{**d, "primary_id": d["primary"]["id"], "fallback_id": (d["fallback"] or {}).get("id")} for d in plan]},
              fh, indent=1)

# ------------------------------------------------------------------------- sources
source_rows: list[dict] = []
for url, rec in sorted(CHECKS.items()):
    source_rows.append({
        "url": url, "label": rec.get("label") or registry_label(url), "venue": rec.get("venue"),
        "kind": rec.get("kind"), "checked_at": rec.get("checked_at"), "status": rec.get("status"),
        "ok": rec.get("ok"), "sha256": (rec.get("sha256") or "")[:16],
        "bytes": rec.get("bytes"), "last_modified": rec.get("last_modified"),
        "first_run": rec.get("first_run"), "bytes_changed": rec.get("bytes_changed"),
        "values_changed": rec.get("values_changed"), "error": rec.get("error"),
        "extractor": rec.get("extractor"), "rows_parsed": rec.get("schedule_rows_parsed"),
        "saved": rec.get("saved_text_to"),
    })
with open(DATA / "source-status.json", "w", encoding="utf-8") as fh:
    json.dump({"meta": {"generated_at": SNAPSHOT_AT or TODAY, "tracked": len(source_rows),
                        "reachable": sum(1 for s in source_rows if s["ok"]),
                        "unreachable": sum(1 for s in source_rows if not s["ok"]),
                        "value_changes_recorded": len(CHANGELOG.get("entries") or [])},
               "sources": source_rows, "change_log": (CHANGELOG.get("entries") or [])[:120]}, fh, indent=1)

print(f"events={len(events)} days={len(plan)} rate-log={len(rate_log)} walks={len(walks)} sources={len(source_rows)}")




def unk(t="not printed"):
    return "<span class='unknown'>" + E(t) + "</span>"


def note(t):
    return "<span class='cellnote'>" + E(t) + "</span>"


def status_span(cls, t):
    return "<span class='" + cls + "'>" + E(str(t)) + "</span>"

# ============================================================== HTML =============
SIBLINGS = {"palazzo": "venetian", "encore": "wynn", "caesars": "casino", "harrahs": "horseshoe"}
KEY_URL = json.load(open(DATA / "source-keys.json", encoding="utf-8"))
RAW_BY_URL = {s["url"]: s["save_text_to"] for s in load("tracked-sources.json")["sources"] if s.get("save_text_to")}
REL = {"venue": "../"}


_escape_once = E


def E(x):  # noqa: F811 - tolerate ints/None/floats coming straight out of the JSON
    return _escape_once("" if x is None else str(x))


def unk(t="not printed"):
    return "<span class='unknown'>" + E(str(t)) + "</span>"


def note(t):
    return "<span class='cellnote'>" + E(str(t)) + "</span>"


def status_span(cls, t):
    return "<span class='" + cls + "'>" + E(str(t)) + "</span>"


def tax_rate(h):
    t = (h.get("tax") or {}).get("rate_pct")
    return (t if isinstance(t, (int, float)) else 13.38) / 100.0


def tax_label(h):
    tx = h.get("tax") or {}
    t = tx.get("rate_pct")
    t = t if isinstance(t, (int, float)) else 13.38
    label = f"{t}% room tax"
    basis = (tx.get("basis") or "").strip()
    if basis:
        label = f"{t}% room tax — {basis}"
    if tx.get("source"):
        label += " (source: " + tx["source"].split("//")[-1].split("/")[0] + ")"
    return label


def hotel_true_cost(h):
    """(rate, resort_fee, tax, total_per_night, rate_log_entry) — total only if both components are published."""
    rate = rate_note = None
    for e in (h.get("rate_log") or []):
        if e.get("amount_usd"):
            rate, rate_note = e["amount_usd"], e
            break
    fee = (h.get("resort_fee") or {}).get("amount_usd")
    tax = tax_rate(h)
    total = round((rate + fee) * (1 + tax), 2) if (rate and fee) else None
    return rate, fee, tax, total, rate_note


def fact_sentences(hotel, field):
    out = []
    for u in hotel_fact_urls(hotel):
        rec = FACTS_SOURCES.get(u) or {}
        for sent in ((rec.get("facts") or {}).get(field) or [])[:3]:
            out.append((sent, u))
    seen, uniq = set(), []
    for s, u in out:
        if s not in seen:
            seen.add(s)
            uniq.append((s, u))
    return uniq


for h in CFG["hotels"]:
    sib = SIBLINGS.get(h["id"])
    if sib:
        other = next((x for x in CFG["hotels"] if x["id"] == sib), None)
        if other and not h.get("source_keys"):
            h["source_keys"] = list(other.get("source_keys") or [])
            h["fee_source_note"] = (f"sister property of {other['property']}: the mandatory fee and the room tax are published once for "
                                    f"the complex, so the same source links appear here. Published room rates are per hotel and stay separate.")

NAV = [("index.html", "Overview"), ("tournaments.html", "Tournaments"), ("hotels.html", "Hotels"),
       ("plan.html", "Day plan"), ("calculator.html", "Trip cost"), ("questions.html", "Open questions"),
       ("suggestions.html", "Suggestions"), ("flagged.html", "Flagged"), ("review.html", "Review log")]


def shell(rel, title, body, active, extra_head="", needs_data=True):
    """needs_data: "full" (everything), "rows" (only what the filters need),
    "calc" (hotels only) or False. Keeps every page's HTML small enough to load fast."""
    nav = "".join(f'<a class="{"active" if rel + href == active else ""}" href="{rel}{href}">{E(label)}</a>' for href, label in NAV)
    data = ""
    payload = None
    if needs_data == "full":
        payload = {"generated_at": SNAPSHOT_AT or TODAY, "events": events, "plan": plan, "venues": CFG["venues"],
                   "hotels": CFG["hotels"], "walk_policy": CFG["walk_policy"], "flags": CFG["flags"],
                   "questions": CFG["questions"], "suggestions": CFG["suggestions"],
                   "verification_policy": CFG["meta"]["verification_policy"], "ranking_policy": CFG["meta"]["ranking_policy"]}
    elif needs_data == "rows":
        payload = {"generated_at": SNAPSHOT_AT or TODAY, "rowmeta": {
            e["id"]: {"rankable": bool(e.get("rankable")), "fee": e["rules"]["fee"].get("status"),
                      "single": bool(e.get("single_entry_confirmed"))} for e in events}}
    elif needs_data == "calc":
        payload = {"generated_at": SNAPSHOT_AT or TODAY, "hotels": CFG["hotels"]}
    if payload is not None:
        data = "<script>window.POKER4=" + json.dumps(payload, separators=(",", ":")) + ";</script>"
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · Vegas Strip Poker Planner</title>
<meta name="description" content="Upcoming Strip poker tournaments ranked by guarantee against the confirmed entry cost, plus true hotel cost per night. Every value linked to the official page it came from.">
<link rel="stylesheet" href="{rel}site.css">{extra_head}{data}</head>
<body>
<header class="topbar">
<a class="brand" href="{rel}index.html">Poker<span>4</span></a>
<nav class="mainnav">{nav}</nav>
<div class="searchbox"><input id="global-search" type="search" placeholder="Search events, hotels, rules, sources…" autocomplete="off" aria-label="Search the site"><div id="search-results" hidden></div></div>
</header>
<main>
{body}
</main>
<footer class="page-foot">
<p><strong>No value on this site is estimated.</strong> A number appears only because the venue or hotel printed it on its own page or PDF; the link and the date it was read sit next to it. A blank cell means the official source did not publish that value, and a flag says what would close the gap.</p>
<p>Snapshot {E(SNAPSHOT_AT or TODAY)} · rebuilt by <code>scripts/integrate_data.py</code> from <code>data/</code> · <a href="{rel}review.html">source status, run log and change log</a></p>
</footer>
<script src="{rel}app.js"></script>
</body></html>"""


def chip(text, cls="chip"):
    return f'<span class="{cls}">{E(str(text))}</span>'


RULE_LABELS = [("single_entry", "Single entry"), ("re_entry", "Re-entry"), ("add_on", "Add-on"), ("fee", "Fee withheld")]
STATUS_CLS = {"confirmed": "chip-ok", "not_stated_in_sheet": "chip-warn", "unverified": "chip-warn", "no": "chip-bad",
              "conflict": "chip-bad", "confirmed_allowed": "chip-bad", "indicated": "chip-bad"}


def rule_chips(ev):
    out = []
    for key, label in RULE_LABELS:
        r = ev["rules"].get(key) or {}
        st = r.get("status", "unverified")
        out.append(chip(f"{label}: {st}", "chip " + STATUS_CLS.get(st, "chip-warn")))
    return "".join(out)


SRC_BASE = ""
VENUE_ALIAS = {"venetian": {"The Venetian"}, "wynn": {"Wynn Las Vegas"}, "bellagio": {"Bellagio"},
               "caesars": {"Caesars Palace"}, "aria": {"ARIA"},
               "others": {"Horseshoe", "Harrahs", "Treasure Island", "WSOP"}}


def src_cell(urls, checked="", changed=False, label="official source ↗"):
    parts = []
    for u in (urls or [])[:3]:
        if not u:
            continue
        parts.append(f'<a class="source-link" href="{E(u)}" target="_blank" rel="noopener">{E(label)}</a>')
        if u in RAW_BY_URL:
            parts.append(f'<a class="captured-link" href="{E(SRC_BASE + RAW_BY_URL[u])}">captured text</a>')
    tail = f'<span class="checked">checked {E(checked or "not yet re-checked")}</span>'
    warn = chip("official values changed since last run", "chip chip-bad") if changed else ""
    return '<span class="src">' + ("".join(parts) or unk("no official source recorded")) + tail + warn + "</span>"


def money_cell(v, note_txt=""):
    return f'<span class="amt">{money(v)}</span>' + (note(note_txt) if note_txt else "")


def event_detail(ev, base=""):
    blocks = []
    for key, label in RULE_LABELS:
        r = ev["rules"].get(key) or {}
        st = r.get("status", "unverified")
        src = r.get("source")
        head = f'<p class="status">{chip(st, "chip " + STATUS_CLS.get(st, "chip-warn"))}'
        if r.get("value"):
            head += f'<span class="val">{E(str(r["value"]))}</span>'
        if r.get("retrieved"):
            head += f'<span class="retr">retrieved {E(r.get("retrieved"))}</span>'
        head += "</p>"
        if r.get("excerpt"):
            head += f'<div class="excerpt"><blockquote>{E(r["excerpt"])}</blockquote></div>'
        else:
            head += ("<p class='unknown'>The official sheet contains no sentence about this. Silence is not "
                     "confirmation, so the field stays blank and flagged.</p>")
        head += (f'<p class="srcline"><a href="{E(src)}" target="_blank" rel="noopener">the sheet this was read from ↗</a></p>'
                 if src else "<p class='srcline'>no structure sheet was linked for this calendar row</p>")
        blocks.append(f'<div class="ruleblock"><h5>{E(label)}</h5>{head}</div>')
    extra = []
    if ev.get("sheet_title"):
        extra.append("captured sheet heading: " + E(ev["sheet_title"]))
    if ev.get("sheet_note"):
        extra.append(E(ev["sheet_note"]))
    if ev.get("sheet_late_registration"):
        extra.append("late registration on the sheet: " + E(ev["sheet_late_registration"]))
    if ev.get("starting_chips"):
        extra.append(f"starting stack {ev['starting_chips']:,} chips" + (f", {E(str(ev['level_duration']))}-min levels" if ev.get("level_duration") else ""))
    if ev.get("levels_total"):
        extra.append(f"{ev['levels_total']} levels listed on the sheet" + (f", {ev['breaks_listed']} break(s)" if ev.get("breaks_listed") else ""))
    if ev.get("payout_pct_of_field"):
        extra.append(f"pays the top {ev['payout_pct_of_field']}% of the field")
    if ev.get("guarantee_from_sheet_text"):
        extra.append("guarantee wording on the sheet: " + E(ev["guarantee_from_sheet_text"]))
    for s in (ev.get("spend_advantage_evidence") or []):
        extra.append("<strong>excluded from the single-entry list:</strong> " + E(s))
    if ev.get("notes"):
        extra.append(E(ev["notes"]))
    if ev.get("printed_date"):
        extra.append("date range as printed: " + E(ev["printed_date"]))
    lis = "".join(f"<li>{x}</li>" for x in extra if x)
    return '<div class="ruleset">' + "".join(blocks) + "</div>" + (f'<ul class="extras">{lis}</ul>' if lis else "")


def event_row(ev, base=""):
    when = ev.get("date") or ""
    head = E(when) if when else unk(ev.get("printed_date") or "no date on this row")
    tail = " · " + E(ev["time"]) if ev.get("time") else ""
    tail += " · reg closes " + E(ev["registration_closes"]) if ev.get("registration_closes") else ""
    link = f"<a href='{base}tournaments.html#{E(ev['id'])}'>event {ev['event_no']}</a> " if ev.get("event_no") else ""
    ratio = ev.get("gtd_ratio")
    if ratio is None:
        ratio_txt = unk("not ranked")
    elif not ev.get("rankable"):
        ratio_txt = f"<span class='muted'>{f'{ratio:,.0f}×' if ratio >= 100 else f'{ratio:.1f}×'}</span>" + note(
            "screening figure only — this row is not ranked until the entry fee and guarantee are both confirmed")
    elif ratio >= 100:
        ratio_txt = f"{ratio:,.0f}×"
    else:
        ratio_txt = f"{ratio:.1f}×"
    tags = "".join(chip(t, "chip chip-tag") for t in (ev.get("tags") or [])[:3])
    flags = "".join(chip("⚑ " + f, "chip chip-warn") for f in (ev.get("flags") or [])[:3])
    gtd = money_cell(ev["guarantee_usd"]) if ev.get("guarantee_usd") else unk("no guarantee printed")
    return f"""<tr class="ev-row" id="{E(ev['id'])}" data-date="{E(ev.get('date') or '')}" data-venue="{E(ev['venue'])}" data-single="{1 if ev.get('single_entry_confirmed') else 0}" data-rankable="{1 if ev.get('rankable') else 0}" data-id="{E(ev['id'])}">
<td class="when">{head}<span class="time">{E(ev.get('weekday') or '')}{tail}</span></td>
<td class="ev">{link}<span class="evname">{E(ev['name'])}</span>{tags}{flags}</td>
<td class="num">{money_cell(ev['buy_in_usd'], 'total buy-in incl. fee') if ev.get('buy_in_usd') else unk('not printed')}</td>
<td class="num">{money_cell(ev['pool_per_entry_usd'], 'into the prize pool') if ev.get('pool_per_entry_usd') else unk('not printed')}</td>
<td class="num">{gtd}</td>
<td class="num">{ratio_txt}</td>
<td class="rules">{rule_chips(ev)}</td>
<td class="srccell">{src_cell(ev.get('sources'), ev.get('last_checked'), ev.get('source_changed'))}</td>
<td class="detail-btn"><button class="disclose" aria-expanded="false">source text</button></td></tr>
<tr class="ev-detail" hidden><td colspan="9">{event_detail(ev, base)}</td></tr>"""


TABLE_HEAD = ("<thead><tr><th>When</th><th>Event</th><th class='num'>Total entry fee</th><th class='num'>Pool per entry</th>"
              "<th class='num'>Guarantee</th><th class='num'>GTD ÷ entry</th><th>Entry rules (each read from the official sheet)</th>"
              "<th>Official source</th><th></th></tr></thead>")

FILTERS = """<div class="filters" id="filters">
<label>from <input type="date" id="f-from" min="2026-11-16" max="2026-12-31"></label>
<label>to <input type="date" id="f-to" min="2026-11-16" max="2026-12-31"></label>
<button class="btn-mini" data-preset="7" type="button">next 7 days</button>
<button class="btn-mini" data-preset="30" type="button">next 30 days</button>
<button class="btn-mini" data-preset="all" type="button">whole window</button>
<label>venue <select id="f-venue"><option value="">all venues</option>__VENUE_OPTS__</select></label>
<label class="toggle"><input type="checkbox" id="f-single"> single-entry confirmed only</label>
<label class="toggle"><input type="checkbox" id="f-hide-unconfirmed"> hide rows with neither a confirmed fee nor a printed guarantee</label>
<span class="count" id="f-count"></span>
</div>"""


def events_table(rows, base="", empty="no rows match these filters"):
    if not rows:
        return f'<p class="empty">{E(empty)}</p>'
    return ('<div class="table-scroll"><table class="events">' + TABLE_HEAD + "<tbody>"
            + "".join(event_row(ev, base) for ev in rows) + "</tbody></table></div>")


def status_banner():
    unreach = [s for s in source_rows if not s["ok"]]
    changed = [s for s in source_rows if s["values_changed"]]
    bits = [f'{len(SCHED["rows"])} calendar rows parsed', f'{len(AUDIT["sheets"])} structure sheets audited',
            f'{len(events)} events on this site', f'{sum(1 for e in events if e.get("single_entry_confirmed"))} confirmed single-entry',
            f'{len(unreach)} official URLs unreachable', f'{len(changed)} sources with value changes']
    inner = "".join(f'<span class="stat">{E(b)}</span>' for b in bits)
    return ('<div class="statusline">' + inner
            + f'<span class="stat">official-source run: {E(SNAPSHOT_AT or "never")} · 06:00 Las Vegas daily</span></div>')


def hotel_table(hotels, base=""):
    if not hotels:
        return ""
    body = ""
    for h in hotels:
        rate, fee, tax, total, rn = hotel_true_cost(h)
        walk = h.get("walk") or {}
        pk = h.get("parking") or {}
        body += ("<tr id='" + E(h["id"]) + "'><td><a href='" + base + "hotels.html#" + E(h["id"]) + "'>" + E(h["property"]) + "</a>"
                 + (note(h.get("fee_source_note")) if h.get("fee_source_note") else "") + "</td>"
                 + "<td class='num'>" + (money(rate) + note("advertised starting point, " + str((rn or {}).get("quote_status") or "")) if rate else unk("no dated official rate")) + "</td>"
                 + "<td class='num'>" + (money(fee) if fee else unk("unconfirmed")) + "</td>"
                 + "<td class='num'>" + (money(total) + note(tax_label(h) + " applied to both") if total else unk("cannot compute")) + "</td>"
                 + "<td class='num'>" + (money(pk.get("self_usd_per_day")) + note("per day") if pk.get("self_usd_per_day") else chip("parking unconfirmed", "chip chip-warn")) + "</td>"
                 + "<td>" + E(walk.get("meets_30_min")) + (note(walk.get("status")) if walk.get("status") else "") + "</td>"
                 + "<td class='srccell'>" + src_cell([h.get("official_page"), h.get("booking_link")], SNAPSHOT_AT[:10]) + "</td></tr>")
    return ("<div class='table-scroll'><table class='compact hotels'><thead><tr><th>Property</th><th class='num'>Room rate</th>"
            "<th class='num'>Resort fee</th><th class='num'>True cost/night</th><th class='num'>Parking</th>"
            "<th>Walk to this room</th><th>Official source</th></tr></thead><tbody>" + body + "</tbody></table></div>")


def source_table(rows, base=""):
    if not rows:
        return "<p class='empty'>none recorded</p>"
    body = ""
    for r in rows:
        state = status_span("ok", r["status"]) if r["ok"] else status_span("bad", f"{r['status']} {r.get('error') or ''}")
        chg = "yes — values" if r.get("values_changed") else ("bytes only" if r.get("bytes_changed") else ("baseline" if r.get("first_run") else "no"))
        saved = f"<a class='captured-link' href='{E(r['saved'])}'>captured text</a>" if r.get("saved") else ""
        body += (f"<tr><td>{E(r['label'])}</td><td class='num'>{E(r.get('venue') or '—')}</td><td>{E(r.get('kind') or '')}</td>"
                 f"<td class='num'>{E(r.get('checked_at') or 'never')}</td><td>{state}</td><td>{chg}</td>"
                 f"<td class='num'>{r.get('rows_parsed') if r.get('rows_parsed') is not None else ''}</td>"
                 f"<td class='srccell'>{src_cell([r['url']], r.get('checked_at'), r.get('values_changed'))}{saved}</td></tr>")
    return ("<div class='table-scroll'><table class='compact sources'><thead><tr><th>Source</th><th class='num'>Venue</th><th>Kind</th>"
            "<th class='num'>Last checked</th><th>Status</th><th>Changed</th><th class='num'>Rows parsed</th><th>Links</th></tr></thead><tbody>"
            + body + "</tbody></table></div>")


# ------------------------------------------------------------------------- index
def page_index():
    rankable = [e for e in events if e.get("rankable")]
    top = sorted(rankable, key=lambda e: -(e.get("gtd_ratio") or 0))[:6]
    v_rows = ""
    for v in CFG["venues"]:
        rows = [e for e in events if e["venue"] == v["id"]]
        v_rows += (f"<tr><td><a href='venues/{E(v['id'])}.html'>{E(v['name'])}</a></td>"
                   + f"<td class='num'>{len(rows)}</td>"
                   + "<td>" + chip((v.get("coverage") or "").split("—")[0].strip(), "chip chip-info") + "</td>"
                   + "<td class='qual'>" + E((v.get("coverage") or "").split("—", 1)[-1].strip()) + "</td>"
                   + f"<td class='num'>{sum(1 for e in rows if e.get('single_entry_confirmed'))}</td>"
                   + "<td class='srccell'>" + src_cell(v.get("schedule_sources"), SNAPSHOT_AT[:10], label="venue's own pages ↗") + "</td></tr>")
    h_rows = ""
    for h in CFG["hotels"]:
        rate, fee, tax, total, rn = hotel_true_cost(h)
        h_rows += (f"<tr><td><a href='hotels.html#{E(h['id'])}'>{E(h['property'])}</a></td>"
                   + f"<td class='num'>{money(fee) if fee else unk('unconfirmed')}</td>"
                   + f"<td class='num'>{money(total) if total else unk('no dated rate')}</td>"
                   + f"<td class='num'>{money((h.get('parking') or {}).get('self_usd_per_day')) if (h.get('parking') or {}).get('self_usd_per_day') else unk('unconfirmed')}</td>"
                   + f"<td>{E((h.get('walk') or {}).get('meets_30_min'))}</td></tr>")
    findings = (f"<strong>0 of {sum(1 for e in events if e['venue'] == 'venetian')} Venetian calendar rows</strong> can be labelled "
                f"“single-entry confirmed”. The room's {len([k for k in AUDIT['sheets'] if k.startswith('V_S')])} published structure sheets state the buy-in, "
                "the fee split, the guarantee, the stack and the level schedule — and say nothing about whether one entry or several are allowed. "
                "Omission is not confirmation, so every row stays <em>unverified</em> rather than being quietly treated as a freezeout. "
                "Where a sheet <em>does</em> speak about extra money — the Valuetown sheet's “all subsequent buy in's after the initial buy in will be $200”, "
                "the $580 pre-registration rate against a $600 list price on Event 59 — that is evidence of the opposite, and those events sit in their own section.")
    return shell("", "Overview", f"""
<section class="hero">
<h1>Vegas Strip poker, filtered by what the rooms actually publish</h1>
<p class="lede">Upcoming tournaments near the Strip ranked by guarantee against the <em>confirmed</em> entry cost, next to the true cost per night of the hotels within a 30-minute walk, a day-by-day plan of as many entries as the printed schedule allows, and a trip-cost calculator. Nothing is estimated: a value shows only where the venue or hotel printed it, and the sentence behind it is one click away.</p>
{status_banner()}
</section>
<section class="cards">
<div class="card finding"><h2>The finding that changes the plan</h2><p>{findings}</p>
<p class="srcline">Evidence: <a href="review.html">the clause audit of all {len(AUDIT['sheets'])} sheets</a> · <a href="data/structure-audit.json">structure-audit.json</a> · <a href="data/venetian_structures.json">the manual read of 12 sheets</a> · <a href="flagged.html#F1">flag F1</a></p></div>
<div class="card"><h2>Best screening ratios among rows that can be ranked</h2>
<p class="mini-note">Guarantee ÷ total entry fee, descriptive only — it is not a forecast of expected value, and none of these rows is confirmed single-entry. Ranking needs the fee split and the guarantee both confirmed; rows without them are excluded here and say why.</p>
<table class="compact"><thead><tr><th>Event</th><th>When</th><th class="num">Entry</th><th class="num">Pool/entry</th><th class="num">Guarantee</th><th class="num">Ratio</th></tr></thead><tbody>
{"".join(f"<tr><td><a href='tournaments.html#{E(e['id'])}'>{E(e['name'])}</a></td><td>{E(e.get('date') or '')}<span class='time'>{E(e.get('time') or '')}</span></td><td class='num'>{money(e['buy_in_usd'])}</td><td class='num'>{money(e.get('pool_per_entry_usd'))}</td><td class='num'>{money(e['guarantee_usd'])}</td><td class='num'>{e['gtd_ratio']:,.0f}×</td></tr>" for e in top)}
</tbody></table><p class="srcline"><a class="btn" href="tournaments.html">all {len(events)} rows</a> <a class="btn" href="plan.html">day plan</a></p></div>
<div class="card"><h2>Open questions and missing information</h2>
<ul class="ticks">{"".join(f"<li>{E(q['question'])}</li>" for q in CFG['questions'])}</ul>
<p><a class="btn" href="questions.html">questions ({len(CFG['questions'])})</a> <a class="btn" href="suggestions.html">suggestions ({len(CFG['suggestions'])})</a> <a class="btn" href="flagged.html">flagged ({len(CFG['flags'])})</a></p></div>
</section>
<section><h2>Rooms covered</h2>
<table class="compact"><thead><tr><th>Venue</th><th class="num">Rows here</th><th>Machine-readable coverage</th><th>What that means</th><th class="num">Confirmed single-entry</th><th>Official sources</th></tr></thead><tbody>{v_rows}</tbody></table>
<h2>Hotels within a 30-minute walk</h2>
<table class="compact"><thead><tr><th>Property</th><th class="num">Mandatory resort fee</th><th class="num">True cost/night</th><th class="num">Parking</th><th>Walk</th></tr></thead><tbody>{h_rows}</tbody></table>
<p class="mini-note">True cost/night = published room rate + mandatory resort fee, both taxed at {E(tax_label(CFG['hotels'][0]))}. “No dated rate” means the property publishes rates only inside its booking calendar, and we do not estimate them — see <a href="hotels.html">the hotel page</a> for the dated log and the source sentences.</p></section>
<section class="how"><h2>How this stays current</h2>
<p>All {len(source_rows)} official URLs are re-fetched on a schedule at 06:00 Las Vegas. The printed calendar PDF and every linked structure sheet are parsed field by field; a content hash detects cosmetic changes and only a <em>value</em> difference is written to the change log and flagged on the affected rows, so a re-render of the same page never looks like a schedule change. Each row carries its own “checked” date.</p>
<p><a class="btn" href="review.html">run log</a> <a class="btn" href="data/sync-status.json">sync-status.json</a> <a class="btn" href="data/change-log.json">change-log.json</a> <a class="btn" href="data/site-events.json">site-events.json</a></p></section>
""", "index.html", needs_data=False)


# ------------------------------------------------------------------- tournaments
def page_tournaments():
    ven = [e for e in events if e["venue"] == "venetian" and not e.get("is_continuation")]
    confirmed = [e for e in events if e.get("single_entry_confirmed")]
    spend = [e for e in events if e.get("spend_advantage")]
    other = [e for e in events if not e.get("single_entry_confirmed") and not e.get("spend_advantage")
             and not e.get("is_continuation")]
    cont = [e for e in events if e.get("is_continuation")]
    opts = "".join(f"<option value='{E(v['id'])}'>{E(v['name'])}</option>" for v in CFG["venues"])
    filters = FILTERS.replace("__VENUE_OPTS__", opts)
    snap_day = (SNAPSHOT_AT or TODAY)[:10]
    board = [e for e in events if e.get("date") and e["date"] >= snap_day][:9]
    board_rows = "".join(
        f"<tr><td>{E(e['date'])}<span class='time'>{E(e.get('weekday') or '')}</span></td>"
        f"<td><a href='#{E(e['id'])}'>{E(e['name'])}</a></td>"
        f"<td class='num'>{E(e.get('time') or '?')}</td><td class='num'>{E(e.get('registration_closes') or 'not printed')}</td>"
        f"<td class='num'>{money(e.get('buy_in_usd'))}</td><td class='num'>{money(e.get('guarantee_usd'))}</td>"
        f"<td class='num'>{str(e.get('level_duration') or '?')} min</td>"
        f"<td>{chip('single-entry ' + e['rules']['single_entry']['status'], 'chip chip-warn')}</td></tr>" for e in board)
    feed = (f"""<section class="feed"><h2>Morning board — what is on from {E(snap_day)} onward</h2>
<p class="mini-note">Straight from the rooms' own printed schedules as re-read at 06:00 Las Vegas (snapshot {E(SNAPSHOT_AT or 'n/a')}); late-registration and level length are the calendar's own columns, not an estimate of when an event ends.</p>
<div class="table-scroll"><table class="compact"><thead><tr><th>Day</th><th>Event</th><th class="num">Start</th><th class="num">Reg closes</th><th class="num">Entry</th><th class="num">Guarantee</th><th class="num">Levels</th><th>Entry rule</th></tr></thead><tbody>{board_rows}</tbody></table></div>
<p class="srcline">Full parsed calendar: <a href="data/schedule-snapshot.json">data/schedule-snapshot.json</a> · per-room source status: <a href="review.html">review log</a></p></section>""")
    return shell("", "Tournaments", f"""
<section class="page-head"><h1>Every tournament the rooms published, with the entry rules beside it</h1>
<p class="lede">The first tab is the single-entry / freezeout list the brief asks for. Because no official sheet confirms single entry for any Venetian event, that list is empty <em>by design</em> — the second tab holds everything else, and the toggle in the filter bar shows what would qualify the moment a room states it.</p>
{status_banner()}</section>
{feed}
{filters}
<div class="tabs" role="tablist">
<button class="tab active" data-tab="confirmed" type="button">Single-entry / freezeout <span>{len(confirmed)}</span></button>
<button class="tab" data-tab="notconfirmed" type="button">Not confirmed <span>{len(other)}</span></button>
<button class="tab" data-tab="spend" type="button">More money buys an advantage <span>{len(spend)}</span></button>
<button class="tab" data-tab="restarts" type="button">Day-2 restarts, not entries <span>{len(cont)}</span></button>
</div>
<section class="tabpanel active" data-panel="confirmed">
<p class="panel-note">Nothing qualifies. A row enters this list only when the venue's own sheet or page explicitly says one entry / no rebuy / no add-on. <a href="questions.html#Q1">Q1 describes the single question that would change this.</a></p>
{events_table(confirmed, "", "no event on any official Strip sheet states single-entry-only play, so nothing qualifies yet")}</section>
<section class="tabpanel" data-panel="notconfirmed">
<p class="panel-note">Sorted by guarantee ÷ total entry fee (screening only). “Pool per entry” is what the sheet says reaches the prize pool, so two events with different fee splits stay comparable. Rows flagged <em>⚑ structure sheet ambiguous</em> share an event number with another sheet (different starting flights) and are never ranked off a fee split they may not belong to. {len(ven)} of these rows are the Venetian series calendar.</p>
{events_table(sorted(other, key=lambda e: -(e.get('gtd_ratio') or 0)))}</section>
<section class="tabpanel" data-panel="spend">
<p class="panel-note">Re-entry, add-on, or a second buy-in priced on the sheet: out of the main list because spending more buys an advantage, whatever the guarantee says.</p>
{events_table(spend)}</section>
<section class="tabpanel" data-panel="restarts">
<p class="panel-note">Day-2 restarts, final tables and play-downs already listed as an entry elsewhere. They cost no new buy-in, so they are never counted as an extra tournament in the day plan.</p>
{events_table(cont)}</section>
""", "tournaments.html", needs_data="rows")


# ----------------------------------------------------------------------- venues
NO_ROWS_NOTE = ("no machine-readable schedule rows for this room in this snapshot: the room publishes its schedule"
                "as an image or a notice rather than a parseable list, so the row count stays zero; the tracked official"
                "sources below are the only evidence available.")

def page_venue(v):
    global SRC_BASE
    base, prev = "../", SRC_BASE
    SRC_BASE = base
    try:
        return _page_venue(v, base)
    finally:
        SRC_BASE = prev


def _page_venue(v, base):
    rows = [e for e in events if e["venue"] == v["id"] and not e.get("is_continuation")]
    cont = [e for e in events if e["venue"] == v["id"] and e.get("is_continuation")]
    hotels = [h for h in CFG["hotels"] if v["id"] in (h.get("venue_ids") or [])]
    flags = [f for f in CFG["flags"] if v["id"] in json.dumps(f).lower() or v["name"].split()[0].lower() in json.dumps(f).lower()]
    addr = f"<a href='{E(v['address_source'])}' target='_blank' rel='noopener'>{E(v.get('official_address') or 'address not published')}</a>"
    return shell(base, v["name"], f"""
<section class="page-head"><p class="crumb"><a href="{base}index.html">Overview</a> / venue</p>
<h1>{E(v['name'])}</h1>
<p class="lede">{addr} · {E(v.get('property') or '')}</p>
<div class="metarow">{chip('coverage: ' + (v.get('coverage') or '').split('—')[0].strip(), 'chip chip-info')}
{chip('events listed: ' + str(len(rows)), 'chip chip-info')}
{chip('confirmed single-entry: ' + str(sum(1 for e in rows if e.get('single_entry_confirmed'))), 'chip chip-warn')}
{chip('hotels in range: ' + str(len(hotels)), 'chip chip-info')}</div>
<p class="cover-note">{E((v.get('coverage') or '').split('—', 1)[-1].strip())}</p>
{note(v.get('notes'))}</section>
<h2>Events here</h2>
{events_table(rows, base, empty=(NO_ROWS_NOTE if not rows else ""))}
{('<h3>Day-2 restarts and finals on the calendar (no new entry)</h3>' + events_table(cont, base)) if cont else ''}
<h2>Hotels within a 30-minute walk</h2>
{hotel_table(hotels, base) if hotels else unk("no hotel can be placed within 30 minutes of this room from an official measurement — see flag F6")}
{("<h2>Flagged for this venue</h2><ul class='flags'>" + "".join(f"<li><strong>{E(f['id'])}</strong> {E(f['item'])} — {E(f['detail'])}</li>" for f in flags) + "</ul>") if flags else ''}
<h2>Sources checked for this venue</h2>
{source_table([s for s in source_rows if str(s.get("venue")).replace(chr(39), "") in VENUE_ALIAS.get(v["id"], set())], base)}
<p class="srcline"><a href="{base}review.html">all {len(source_rows)} tracked sources</a></p>
""", f"{base}venues/{v['id']}.html", needs_data=False)


# ----------------------------------------------------------------------- hotels
def page_hotels():
    cards = ""
    for h in CFG["hotels"]:
        rate, fee, tax, total, rn = hotel_true_cost(h)
        vnames = ", ".join(VENUE_BY_ID.get(x, {}).get("name", x) for x in (h.get("venue_ids") or []))
        log_rows = "".join(
            f"<tr><td>{E(e.get('observed_on') or '—')}</td><td>{E(e.get('label') or '')}</td>"
            f"<td class='num'>{money(e['amount_usd']) if e.get('amount_usd') else unk('no amount published')}</td>"
            f"<td class='qual'>{E(e.get('qualifier') or '')}</td>"
            f"<td>{E(e.get('quote_status') or '')}</td>"
            f"<td class='srccell'>{src_cell([e.get('source')], e.get('observed_on'))}</td></tr>"
            for e in (h.get("rate_log") or [])) or f"<tr><td colspan='6'>{unk('no rate line captured yet')}</td></tr>"
        facts = ""
        for field in ("resort_fee", "room_tax", "parking", "cancellation"):
            for sent, u in fact_sentences(h, field):
                facts += f"<li><strong>{E(field.replace('_', ' '))}</strong> “{E(sent)}” {src_cell([u], SNAPSHOT_AT[:10], label='source page ↗')}</li>"
        walk_rows = "".join(
            f"<tr><td>{E(p['venue'])}</td><td class='num'>{str(p['minutes']) + ' min' if p.get('minutes') else unk('not published')}</td>"
            f"<td>{E(p['meets_30_min'])}</td><td class='qual'>{E(p.get('status') or '')}</td>"
            f"<td class='srccell'>{src_cell([p.get('source')], SNAPSHOT_AT[:10], label='source ↗')}</td></tr>"
            for p in walks if p["hotel_id"] == h["id"])
        if total:
            calc = (f"<p class='truecost'>true cost per night = {money(rate)} room rate + {money(fee)} mandatory resort fee "
                    f"= {money(rate + fee)} × 1.{str(int(round(tax * 10000))):0>4} ({E(tax_label(h))}) = <strong>{money(total)}</strong> per night, before parking."
                    + (f" {E(rn.get('quote_status'))}." if rn and rn.get("quote_status") else "") + "</p>")
        else:
            missing = []
            if not rate:
                missing.append("no room rate that this property publishes as a dated quotable number")
            if not fee:
                missing.append("the mandatory resort fee is not stated on a page that could be reached")
            calc = f"<p class='truecost blocked'>true cost per night cannot be computed: {E(' and '.join(missing))}. The blanks are kept rather than filled with an estimate.</p>"
        qual = h.get("qualification")
        qual_line = (f"<p class='mini-note'><strong>Rate eligibility:</strong> {E(qual)} — {src_cell([h.get('qualification_source')], SNAPSHOT_AT[:10], label='official terms ↗')}</p>"
                     if qual else "")
        dead = "".join(f"<li>the page that should carry this value is <a href='{E(d['url'])}' target='_blank' rel='noopener'>{E(d['url'].split('//')[-1])}</a> — {E(d['status'])}</li>"
                       for d in (h.get("dead_source_pages") or []))
        canc = h.get("cancellation") or {}
        park = h.get("parking") or {}
        mins = next((str(p2["minutes"]) for p2 in walks if p2["hotel_id"] == h["id"] and p2.get("minutes")), "")
        onsite = "1" if "on-site" in str((h.get("walk") or {}).get("meets_30_min")).lower() else "0"
        meets = (h.get("walk") or {}).get("meets_30_min")
        meets_flag = "yes" if str(meets).lower().startswith(("yes", "under", "well")) else ("no" if str(meets).lower().startswith(("no", "over")) else "unverified")
        cards += f"""<article class="hotel" id="{E(h['id'])}" data-walk-min="{E(mins)}" data-onsite="{onsite}" data-meets="{E(meets_flag)}">
<h3>{E(h['property'])} <span class="mini-note">near {E(vnames or 'the rooms listed below')}</span></h3>
<p class="addr">{E(h.get('address') or '')} · <a href="{E(h.get('official_page') or '#')}" target="_blank" rel="noopener">official page ↗</a>{(" · <a href='" + E(h['booking_link']) + "' target='_blank' rel='noopener'>official booking engine — live rates for your dates ↗</a>") if h.get('booking_link') else ''}</p>
{calc}{qual_line}
{note(h.get('fee_source_note')) if h.get('fee_source_note') else ''}
<h4>Fee, tax, parking, cancellation — the sentences behind the numbers</h4>
<ul class="facts">{facts or "<li>" + unk('no fee or tax sentence captured for this property') + "</li>"}</ul>
<div class="two">
<div><h4>Resort fee</h4><p>{money(fee) if fee else unk('unconfirmed')} <span class="mini-note">{E((h.get('resort_fee') or {}).get('basis') or '')}</span> {chip((h.get('resort_fee') or {}).get('status') or 'unverified', 'chip chip-info')}</p>
{(f"<p class='warn'>{E((h.get('resort_fee') or {}).get('conflict'))}</p>") if (h.get('resort_fee') or {}).get('conflict') else ''}</div>
<div><h4>Parking</h4><p>{('self ' + money(park.get('self_usd_per_day')) + ' / day · valet ' + money(park.get('valet_usd_per_day')) + ' / day') if park.get('self_usd_per_day') else unk('not published')} {chip(park.get('status') or 'unverified', 'chip chip-info')}</p></div>
<div><h4>Cancellation</h4><p>{E(canc.get('text') or '') or unk('not captured')} {chip(canc.get('status') or 'unverified', 'chip chip-warn')}</p></div>
</div>
<h4>Rates and fee facts as a dated log (not a single value)</h4>
<div class="table-scroll"><table class="compact"><thead><tr><th>Observed</th><th>What it is</th><th class="num">Amount</th><th>Wording / qualifier</th><th>Quote status</th><th>Source</th></tr></thead><tbody>{log_rows}</tbody></table></div>
<h4>Walk to the poker rooms</h4>
<div class="table-scroll"><table class="compact"><thead><tr><th>Poker room</th><th class="num">Walk</th><th>Meets the 30-min rule</th><th>How we know</th><th>Source</th></tr></thead><tbody>{walk_rows}</tbody></table></div>
{(f"<h4>Unresolved for this property</h4><ul class='flags'>{dead}</ul>") if dead else ''}
</article>"""
    return shell("", "Hotels", f"""
<section class="page-head"><h1>Hotels near the rooms, priced the way you actually pay</h1>
<p class="lede">True cost per night = the published room rate + the mandatory resort fee, both subject to {E(tax_label(CFG['hotels'][0]))}. Parking, the cancellation rule and the date the number was read sit next to it so two properties can be compared like for like. Rates are kept as a dated log, because a rate is only true at the moment it was quoted.</p>
{status_banner()}
<div class="walkfilter" id="walk-filter">
<span class="lbl">≤30-minute walking filter:</span>
<label class="toggle"><input type="radio" name="walkf" value="all" checked> every property on the list</label>
<label class="toggle"><input type="radio" name="walkf" value="onsite"> inside the poker-room property only</label>
<label class="toggle"><input type="radio" name="walkf" value="measured"> measured walk ≤ 30 min</label>
<span class="count" id="walk-count"></span>
</div>
<p class="mini-note">“Measured” is empty on purpose: no Strip property publishes a door-to-door walking time to another property's poker room, and the minutes cells are left blank rather than estimated — <a href="flagged.html#F6">F6</a> records the one API call that would fill them. Choosing it filters the list to what is actually provable today.</p></section>
{cards}
<section class="callout"><h2>Reading a blank honestly</h2>
<p>Where a property shows rates only inside its booking calendar, no number is copied onto this site — the booking link is given instead and the row is marked. Two official pages currently return 404 (Bellagio's resort-fee page and the Caesars Palace daily flyer); they are reported as unreachable, never replaced by a third-party mirror. ARIA publishes two different resort fees on two official pages ($50 and $55): both sentences are shown and neither is chosen for you. No official walking-minute figure exists for any hotel→poker-room pair on the Strip, so the ≤30-minute rule is carried as a warning, not a green tick — <a href="flagged.html#F6">F6</a> explains how to close it.</p></section>
""", "hotels.html", needs_data=False)


# -------------------------------------------------------------------------- plan
def page_plan():
    rows = ""
    for d in plan:
        p, f = d["primary"], d["fallback"]
        p_txt = (f"<a href='tournaments.html#{E(p['id'])}'>{E(p['name'])}</a><span class='time'>starts {E(p.get('time') or 'time not printed')}"
                 f" · reg closes {E(p.get('registration_closes') or 'not printed')} · entry {money(p.get('buy_in_usd'))}</span>")
        f_txt = (f"<a href='tournaments.html#{E(f['id'])}'>{E(f['name'])}</a><span class='time'>starts {E(f.get('time') or 'time not printed')}"
                 f" · reg closes {E(f.get('registration_closes') or 'not printed')} · entry {money(f.get('buy_in_usd'))}</span>") if f \
            else unk("no second event printed for this date")
        conf = "".join(f"<p>{E(c)}</p>" for c in d.get("overlap_notes") or []) or "<span class='ok'>nothing blocks a second entry</span>"
        res = "; ".join(d.get("restarts") or [])
        rows += (f"<tr class='day-row' data-date='{E(d['date'])}'><td class='when'><strong>{E(d['date'])}</strong><span class='time'>{E(d.get('weekday') or '')}</span></td>"
                 f"<td>{p_txt}</td><td>{f_txt}</td><td class='restarts'>{E(res) if res else unk('nothing to defend')}</td>"
                 f"<td class='conflicts'>{conf}</td><td class='num'>{money(d['entries_usd'])}</td></tr>")
    with_fb = len([x for x in plan if x.get("fallback")])
    return shell("", "Day plan", f"""
<section class="page-head"><h1>One day, one primary event, one conditional fallback</h1>
<p class="lede">Sequencing uses only what the calendar prints: the start time, the “REG CLOSES” column and the Day-2 restart rows. A day gets a <strong>primary</strong> event and a <strong>fallback</strong> that is only reachable if you are done with the first — that means its start is at or after the primary's registration deadline, the closest thing to a guaranteed exit the official data offers. No event duration is invented: where a sheet lists levels, the implied length sits on the tournament row, and it is never used to reorder this plan.</p>
{status_banner()}
<p class="warn">The day cannot start at 8:00 AM: nothing on the Strip publishes an 8:00 AM first flight. In this window the earliest first starts are 10:10 AM (raceday events) and 11:10 AM for the $300 Events 1A/9, so each day begins at the earliest official start and the difference is flagged rather than papered over.</p></section>
<div class="table-scroll"><table class="compact days"><thead><tr><th>Day</th><th>Primary</th><th>Conditional fallback</th><th>Day-2 / finals that day</th><th>Overlap check</th><th class="num">Entries if both</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<section class="callout"><h2>Why some days carry no fallback</h2>
<p>Where a second event starts before the first one's registration window closes, playing both is impossible on the official data — those days list the conflict instead of scheduling it. {with_fb} of {len(plan)} days have a defensible fallback. Rows on the same date with the same buy-in but different flights (1A/1B/1C…) are alternative starts of <em>one</em> event, not two entries, and the plan never counts both.</p>
<p class="srcline">Machine copy: <a href="data/day-plan.json">day-plan.json</a> · basis: <a href="data/schedule-snapshot.json">schedule-snapshot.json</a></p></section>
""", "plan.html", needs_data=False)


# ------------------------------------------------------------------- calculator
def page_calculator():
    hotel_opts = "".join(f"<option value='{E(h['id'])}'>{E(h['property'])}{'' if (h.get('resort_fee') or {}).get('amount_usd') else ' — fee unconfirmed'}</option>" for h in CFG["hotels"])
    fee_opts = "<option value=''>not confirmed — do not include</option>" + "".join(
        f"<option value='{E(h['id'])}' data-fee='{(h.get('resort_fee') or {}).get('amount_usd') or ''}'>{E(h['property'])}: {money((h.get('resort_fee') or {}).get('amount_usd'))}</option>"
        for h in CFG["hotels"] if (h.get("resort_fee") or {}).get("amount_usd"))
    picks = "".join(
        f"<label class='pick'><input type='checkbox' class='ev-pick' data-cost='{e.get('buy_in_usd') or 0}' data-id='{E(e['id'])}'>"
        f"<span>{E(e['name'])}</span><em>{E(e.get('date') or e.get('printed_date') or 'date not printed')} · {money(e.get('buy_in_usd'))}</em></label>"
        for e in events if e.get("buy_in_usd") and not e.get("is_continuation"))
    return shell("", "Trip cost", f"""
<section class="page-head"><h1>Estimated trip cost</h1>
<p class="lede">Entries × total buy-in, plus nights × the true hotel cost. Every input carries a source link and a date, and the calculator will not add a number the property did not publish: leave a field on “not confirmed” and the hotel total reads <em>cannot compute</em> instead of guessing.</p></section>
<section class="calc" id="calc"><div class="calc-grid">
<div><h3>Hotel</h3>
<label>Property <select id="calc-hotel">{hotel_opts}</select></label>
<label>Dated room rate <select id="calc-rate"><option value="">no official dated rate for this property</option></select></label>
<label>Mandatory resort fee <select id="calc-fee">{fee_opts}</select></label>
<label>Parking per night <select id="calc-park"><option value="">not confirmed</option></select></label>
<label>Nights <input type="number" id="calc-nights" value="4" min="1" max="21"></label>
<label>Rooms <input type="number" id="calc-rooms" value="1" min="1" max="6"></label>
</div>
<div><h3>Tournaments</h3><p class="mini-note">Tick what you would enter. Only the total buy-in is counted — each sheet says the house fee is already withheld inside it.</p>
<div class="picks" id="calc-events">{picks}</div></div>
<div class="calc-out"><h3>Totals</h3>
<dl id="calc-total"><dt>Entries</dt><dd id="t-entries">—</dd><dt>Hotel per night</dt><dd id="t-night">—</dd><dt>Hotel total</dt><dd id="t-hotel">—</dd><dt class="grand">Trip total</dt><dd class="grand" id="t-grand">—</dd></dl>
<p id="calc-note" class="warn"></p>
<p class="mini-note">Rates move constantly and the properties publish them only inside the booking calendar for specific dates. Re-read the official page before booking: <a href="hotels.html" id="calc-book">the hotel's own booking link is on its card</a>.</p>
<p class="mini-note">Worked example kept from the snapshot: {E(CFG['trip_example']['label'])} — {E(CFG['trip_example']['basis'])}</p>
</div></div></section>
""", "calculator.html", needs_data="calc")


# --------------------------------------------- questions / suggestions / flagged / review
def page_questions():
    body = ""
    for q in CFG["questions"]:
        srcs = "".join(f"<li>{src_cell([u], SNAPSHOT_AT[:10], label='official source ↗')}</li>" for u in (q.get("sources") or []))
        body += f"""<article class="q" id="{E(q['id'])}"><h3>{E(q['id'])} · {E(q['question'])}</h3>
<p class="why">{E(q.get('why_it_matters') or '')}</p>
<dl><dt>What we already have</dt><dd>{E(q['we_have'])}</dd>
<dt>What is missing</dt><dd>{E(q['missing'])}</dd>
<dt>How to close it</dt><dd>{E(q['how_to_close'])}</dd>
<dt>Owner</dt><dd>{E(q['owner'])}</dd></dl>
{f"<ul class='facts'>{srcs}</ul>" if srcs else ''}</article>"""
    return shell("", "Open questions", f"""
<section class="page-head"><h1>Questions and missing information</h1>
<p class="lede">What the official record does not answer, what we have instead, and the exact route to close each one. Nothing here blocks the site from running; until an item is closed, the affected rows on the tournament, hotel and plan pages stay blank and flagged instead of being filled in.</p></section>
{body}""", "questions.html", needs_data=False)


def page_suggestions():
    rows = ""
    for s in CFG["suggestions"]:
        rows += (f"<tr><td>{E(s['id'])}</td><td><strong>{E(s['title'])}</strong>"
                 f"<p class='cellnote'><em>problem:</em> {E(s.get('problem') or '')}</p>"
                 f"<p class='cellnote'><em>proposal:</em> {E(s.get('proposal') or '')}</p></td>"
                 + f"<td>{chip('impact: ' + s['impact'], 'chip chip-info')}</td><td>{chip('effort: ' + s['effort'], 'chip chip-info')}</td>"
                 + f"<td>{E(s['status'])}</td><td>{E(s.get('decision_needed') or '')}</td></tr>")
    steps = "".join(
        f"<tr><td class='num'>{d['step']}</td><td>{E(d['title'])}</td><td>{chip(d['status'], 'chip ' + ('chip-ok' if d['status'] == 'done' else ('chip-bad' if d['status'] == 'blocked' else 'chip-warn')))}</td>"
        f"<td>{E(d.get('detail') or '')}</td><td>{E(d.get('next_action') or '')}</td></tr>" for d in CFG["decision_workflow"])
    return shell("", "Suggestions", f"""
<section class="page-head"><h1>Suggestions, ranked by impact over effort</h1>
<p class="lede">Each entry says what it would buy, what is already automated, and whether a decision is actually needed. <em>automated</em> means it is live in the sync pipeline; <em>blocked</em> means it is waiting on an official source, not on anyone here.</p></section>
<div class="table-scroll"><table class="compact"><thead><tr><th>#</th><th>Suggestion</th><th>Impact</th><th>Effort</th><th>Status</th><th>Decision needed</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>The plan of record, step by step</h2>
<div class="table-scroll"><table class="compact"><thead><tr><th class="num">#</th><th>Step</th><th>Status</th><th>Where it stands</th><th>Next action</th></tr></thead><tbody>{steps}</tbody></table></div>""",
"suggestions.html", needs_data=False)


def page_flagged():
    groups: dict[str, list] = {}
    for f in CFG["flags"]:
        groups.setdefault(f["severity"], []).append(f)
    body = ""
    for kind in sorted(groups):
        items = groups[kind]
        body += f"<h3>{E(kind.replace('-', ' '))} ({len(items)})</h3><ul class='flaglist'>" + "".join(
            f"<li id='{E(i['id'])}'><strong>{E(i['id'])}</strong> {E(i['item'])}"
            f"<p>{E(i['detail'])}</p>"
            + (f"<p class='cellnote'>{E(i['description'])}</p>" if i.get("description") else "")
            + f"<p class='cellnote'>{src_cell(i.get('sources'), SNAPSHOT_AT[:10], label='official source ↗')}</p></li>" for i in items) + "</ul>"
    unconf = sum(1 for e in events if e["rules"]["single_entry"]["status"] != "confirmed")
    norate = sum(1 for h in CFG["hotels"] if not hotel_true_cost(h)[3])
    nowalk = sum(1 for p in walks if not p.get("minutes"))
    return shell("", "Flagged for review", f"""
<section class="page-head"><h1>Flagged for review</h1>
<p class="lede">Every unresolved item, with the source that produced it. A flag is never cleared by re-wording a row — only when the official source states the value or an action closes the gap.</p>
<div class="flagstats"><span class="stat">{len(CFG['flags'])} open flags</span>
<span class="stat">{unconf} of {len(events)} rows without confirmed single-entry</span>
<span class="stat">{norate} of {len(CFG['hotels'])} hotels with no computable true cost</span>
<span class="stat">{nowalk} of {len(walks)} hotel→venue walks unmeasured</span>
<span class="stat">{sum(1 for s in source_rows if not s['ok'])} official URLs unreachable</span></div></section>
{body}
<section class="callout"><h2>Row-level flags live with the rows</h2><p>Per-row flags (ambiguous sheet, no guarantee printed, not ranked because the fee split is unconfirmed) sit on each row in <a href="tournaments.html">tournaments</a> and on the venue pages, so the warning never separates from the number it qualifies.</p></section>""",
"flagged.html", needs_data=False)


def page_review():
    st = load("sync-status.json", {})
    chg = ""
    for c in (CHANGELOG.get("entries") or [])[:40]:
        chg += (f"<tr><td>{E(str(c.get('at') or '')[:16].replace('T', ' '))}</td><td>{E(c.get('scope') or '')}</td>"
                f"<td>{E(registry_label(str(c.get('url') or '')))}</td>"
                f"<td class='diff'><pre>{E(json.dumps(c.get('diff'), indent=1)[:1200])}</pre></td></tr>")
    if not chg:
        chg = f"<tr><td colspan='4'>{unk('no value-level change recorded since monitoring began — the first run seeds the baseline, later runs diff against it')}</td></tr>"
    dead_rows = "".join(f"<tr><td><a href='{E(s['url'])}' target='_blank' rel='noopener'>{E(s['label'])}</a></td><td>{E(s.get('venue') or '')}</td>"
                        f"<td>{status_span('bad', str(s['status']) + ' ' + str(s.get('error') or ''))}</td><td class='num'>{E(s.get('checked_at') or '')}</td></tr>"
                        for s in source_rows if not s["ok"])
    parsed = sum(1 for s in source_rows if (s.get("rows_parsed") or 0) > 0)
    saved = sum(1 for s in source_rows if s.get("saved"))
    return shell("", "Review log", f"""
<section class="page-head"><h1>Review log — what was checked, when, and what changed</h1>
<p class="lede">The numbers the site was built from, plus the raw material: every tracked official URL with the date it was last read, whether its bytes or its values moved, how many rows the parser got out of it, and the captured text itself. Any row on any page can be traced to a captured sentence in one click.</p>
{status_banner()}</section>
<div class="runstats"><div><h3>Last run</h3><ul>
<li>{E(st.get('urls_checked', len(source_rows)))} official URLs checked · {len(st.get('urls_failed') or [])} failed</li>
<li>{E(st.get('sheets_audited', len(AUDIT['sheets'])))} structure sheets audited · {E(st.get('schedule_rows', len(SCHED['rows'])))} calendar rows · {E(st.get('schedule_rows_with_date', sum(1 for r in SCHED['rows'] if r.get('date'))))} rows carrying a date</li>
<li>{len(st.get('changed_this_run') or [])} URLs changed on this run (cosmetic byte changes are counted separately from value changes)</li>
<li>{E(st.get('hotel_fact_sources', len(FACTS.get('sources') or {})))} property pages yielded a fee / tax / parking / cancellation sentence</li>
<li>{parsed} sources parsed into rows · {saved} sources kept as captured text under <code>data/raw/</code></li></ul>
<p class="mini-note">Machine copies: <a href="data/sync-status.json">sync-status</a> · <a href="data/url-checks.json">url-checks</a> · <a href="data/site-events.json">site-events</a> · <a href="data/structure-audit.json">structure-audit</a> · <a href="data/schedule-snapshot.json">schedule-snapshot</a> · <a href="data/rate-log.json">rate-log</a> · <a href="data/walks.json">walks</a> · <a href="data/hotel-facts.json">hotel-facts</a></p>
<p class="mini-note">Sample of the raw date headings read from the calendar PDF: <code>{E(str((st.get('date_head_sample') or '')[:220]))}</code></p></div>
<div><h3>Unreachable official URLs</h3>
<div class="table-scroll"><table class="compact"><thead><tr><th>Source</th><th>Venue</th><th>Status</th><th class="num">Checked</th></tr></thead><tbody>{dead_rows or "<tr><td colspan='4' class='ok'>none</td></tr>"}</tbody></table></div>
<p class="mini-note">Policy: a dead official URL is reported and kept in the tracked list; it is never replaced by a third-party mirror.</p>
<p class="mini-note">Reproduce offline: <code>python3 tools/sync_official_sources.py --from-raw</code> then <code>python3 scripts/integrate_data.py</code>.</p></div></div>
<h2>Value changes recorded</h2>
<div class="table-scroll"><table class="compact"><thead><tr><th>When (UTC)</th><th>Scope</th><th>Source</th><th>Fields that moved</th></tr></thead><tbody>{chg}</tbody></table></div>
<h2>All tracked sources ({len(source_rows)})</h2>
{source_table(source_rows)}
""", "review.html", needs_data=False)


# ------------------------------------------------------------------ emit the site
VENUES_OUT.mkdir(exist_ok=True)
pages = {"index.html": page_index(), "tournaments.html": page_tournaments(), "hotels.html": page_hotels(),
         "plan.html": page_plan(), "calculator.html": page_calculator(), "questions.html": page_questions(),
         "suggestions.html": page_suggestions(), "flagged.html": page_flagged(), "review.html": page_review()}
for v in CFG["venues"]:
    pages[f"venues/{v['id']}.html"] = page_venue(v)
# Superseded pages are kept as explicit redirects rather than deleted, so a bookmarked
# or linked old URL still lands on the page that replaced it and says why.
REDIRECTS = {
    "decisions.html": ("suggestions.html", "the decision workflow and the ranked suggestions now live on the suggestions page"),
    "schedule.html": ("plan.html", "the day-by-day plan now lives on the day-plan page, built from the printed registration deadlines"),
    "change-monitor.html": ("review.html", "monitoring now covers every official URL and reports value changes, not a hand-picked list"),
    "trip-calculator.html": ("calculator.html", "the cost calculator now reads the dated rate log and the confirmed fee for each property"),
    "venue-venetian.html": ("venues/venetian.html", "venue pages now carry the events, the hotels and the sources for that room in one place"),
    "venue-wynn.html": ("venues/wynn.html", "venue pages now carry the events, the hotels and the sources for that room in one place"),
    "venue-others.html": ("venues/others.html", "venue pages now carry the events, the hotels and the sources for that room in one place"),
}
for src, (dest, why) in REDIRECTS.items():
    (OUT / src).write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={dest}">
<link rel="canonical" href="{dest}">
<title>Moved · Vegas Strip Poker Planner</title>
<link rel="stylesheet" href="site.css"></head>
<body><main><section class="page-head"><h1>This page moved</h1>
<p><code>{E(src)}</code> was replaced during the integration: {E(why)}.</p>
<p>You are being redirected to <a href="{dest}">{E(dest)}</a>. If nothing happens, follow the link.</p>
</section></main></body></html>
""", encoding="utf-8")
    pages[src] = "<redirect>"
for path, html_out in pages.items():
    if html_out == "<redirect>":
        continue
    (OUT / path).write_text(html_out, encoding="utf-8")

search_index = []
for e in events:
    search_index.append({"t": f"{e['name']} — {e.get('date') or e.get('printed_date') or ''}".strip(" —"),
                         "u": f"tournaments.html#{e['id']}", "k": "event",
                         "s": f"{e['venue_name']} · {money(e.get('buy_in_usd'))} · {e.get('kind')} · {e['rules']['single_entry']['status']}"})
for h in CFG["hotels"]:
    search_index.append({"t": h["property"], "u": f"hotels.html#{h['id']}", "k": "hotel",
                         "s": f"resort fee {money((h.get('resort_fee') or {}).get('amount_usd'))} · walk {E((h.get('walk') or {}).get('meets_30_min'))}"})
for q in CFG["questions"]:
    search_index.append({"t": f"{q['id']} {q['question']}", "u": f"questions.html#{q['id']}", "k": "question", "s": q["missing"][:130]})
for f in CFG["flags"]:
    search_index.append({"t": f"{f['id']} {f['item']}", "u": f"flagged.html#{f['id']}", "k": "flag", "s": f["detail"][:130]})
for s_ in source_rows:
    search_index.append({"t": s_["label"], "u": s_["url"], "k": "official source", "s": f"{s_.get('venue')} · checked {s_.get('checked_at')}"})
(DATA / "search-index.json").write_text(json.dumps({"generated_at": SNAPSHOT_AT or TODAY, "items": search_index}, separators=(",", ":")), encoding="utf-8")
print(f"pages={len(pages)} search={len(search_index)} size-index={os.path.getsize(OUT / 'index.html')}")
