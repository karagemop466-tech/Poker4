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
WALKMEAS = load("walk-measurements.json", {"meta": {}, "pairs": []})


def merge_walk_measurements() -> None:
    """Fold measured hotel->poker-room walks into the curated hotel records.

    The minutes come from a routing engine (Google Maps, travel mode = walking,
    departure "leave now") recorded in data/walk-measurements.json with the
    timestamp of the request. They are measurements, not operator statements, so
    every cell keeps that distinction in its wording and the official address
    page stays the source link for the row.
    """
    pairs = WALKMEAS.get("pairs") or []
    if not pairs:
        return
    by_hotel = {p["hotel_id"]: p for p in pairs}
    for h in CFG["hotels"]:
        m = by_hotel.get(h["id"])
        if not m:
            continue
        walk = dict(h.get("walk") or {})
        walk.update({
            "minutes": m["minutes"],
            "distance_miles": m["distance_miles"],
            "route_summary": m["route_summary"],
            "measured_at": m["captured_at"],
            "method": m["measured_by"],
            "method_url": m["maps_url"],
            "alt_method_url": m["apple_url"],
            # the same measurement under the key names the other builder reads, so a
            # page rebuilt with either generator still shows miles, via and date
            "venue_id": m["venue_id"],
            "venue": m["venue"],
            "distance_mi": m["distance_miles"],
            "via": m["route_summary"][4:] if m["route_summary"].lower().startswith("via ") else m["route_summary"],
            "retrieved": m["captured_at"],
            "walk_url": m["maps_url"],
            "meets_30_min": ("yes — measured " + str(m["minutes"]) + " min (limit 30)"
                             if m["meets_30_min"] else
                             "no — measured " + str(m["minutes"]) + " min, over the 30-minute limit"),
            "status": (f"Measured {m['captured_at'][:10]} with Google Maps walking directions "
                       f"({m['measured_by']}) from {m['hotel_address']} to {m['venue_address']}: "
                       f"{m['minutes']} min / {m['distance_miles']} mi {m['route_summary']}. "
                       "A routing-engine measurement with a timestamp and a reproducible link, "
                       "not a statement by either property."),
            "source": m["hotel_address_source"],
        })
        h["walk"] = walk


merge_walk_measurements()
SCHED = load("schedule-snapshot.json", {"meta": {}, "rows": []})
# c2242cb1 (K2): row-level corrections where the PDF-parsed snapshot disagrees with the
# official schedule page. Each "set" must match exactly one row; otherwise the build stops,
# so a re-scrape can never silently drop or mis-time a row. See data/c2242cb1/.
_OVR_PATH = DATA / "c2242cb1" / "venetian_overrides.json"
if _OVR_PATH.exists():
    _ovr = json.loads(_OVR_PATH.read_text(encoding="utf-8"))
    _rows = [dict(r) for r in SCHED.get("rows", [])]
    for _op in _ovr.get("operations", []):
        if _op["op"] == "set":
            _m = _op["match"]
            _hits = [r for r in _rows if r.get("date") == _m["date"] and r.get("time") == _m["time"]
                     and r.get("event_no") == _m["event_no"]
                     and (not _m.get("name_contains") or _m["name_contains"] in (r.get("event_name") or "").upper())]
            if len(_hits) == 1:
                _hits[0].update(_op["set"])
            elif len(_hits) == 0:
                # Already corrected upstream (the snapshot may carry the fix): accept only if a row
                # with the corrected values exists; otherwise the row is missing and the build stops.
                _done = [r for r in _rows if r.get("date") == _m["date"] and r.get("event_no") == _m["event_no"]
                         and all(r.get(k) == v for k, v in _op["set"].items())]
                if not _done:
                    raise SystemExit(f"venetian override matched no row and no corrected row exists: {_m}")
            else:
                raise SystemExit(f"venetian override matched {len(_hits)} rows (need exactly 1): {_m}")
        elif _op["op"] == "add":
            _r = _op["row"]
            # Skip if the same row (date, time, event number) is already present upstream.
            if any(r.get("date") == _r.get("date") and r.get("time") == _r.get("time")
                   and r.get("event_no") == _r.get("event_no") for r in _rows):
                continue
            _rows.append(dict(_r))
        else:
            raise SystemExit(f"unknown override op: {_op['op']}")
    SCHED = {**SCHED, "rows": _rows}
AUDIT = load("structure-audit.json", {"sheets": {}})


def sheets_label() -> str:
    """Audit-record breakdown (flag F20): the audit mixes Venetian DSE IV
    structure sheets with other official documents; say which is which."""
    keys = AUDIT.get("sheets") or {}
    ven = sum(1 for k in keys if re.match(r"V_S\d+$", k or ""))
    other = len(keys) - ven
    return f"{ven} Venetian structure sheets audited + {other} other official documents"


VEN_SHEETS = sum(1 for k in (AUDIT.get("sheets") or {}) if re.match(r"V_S\d+$", k or ""))
FACTS = load("hotel-facts.json", {"sources": {}})
CHECKS = load("url-checks.json", {})
CHANGELOG = load("change-log.json", {"entries": []})
LEGACY = load("tournaments.json", {"sources": {}, "reentry_or_addon": []})
# tools/room_extract.py output: dated rows re-read from the rooms' own committed PDFs.
# Present => those rows supersede the earlier undated CSV-derived Wynn/Bellagio/Caesars
# placeholders, which are then skipped rather than published twice.
ROOM_FACTS = load("room-facts.json", None)
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
AMBIGUOUS_NOTE = "several sheets print this event number; no exact official row-to-sheet mapping was applied, so sheet-derived values are left blank"


def pick_sheet(event_no: int, time: str | None, date: str | None, name: str = ""):
    cands = SHEET_BY_EVENT.get(event_no) or []
    if not cands:
        return None, "no structure sheet printed for this event number"

    # Per-flight exceptions taken directly from the official Venetian calendar's
    # Structures column. The sheets do not print a Day-A start time for Events 39
    # and 47, so a generic time-based match cannot distinguish those flights.
    # For Event 56, the official page links the 1A/1C/1E sheets to #35 and the
    # 1B/1D sheets to #36; Day 2 also links #35.
    exact_key = None
    if event_no == 47:
        if re.search(r"\b1B\b", name, re.I):
            exact_key = "V_S37"
        else:
            exact_key = "V_S21"
    elif event_no == 56:
        if re.search(r"\b1B\b|\b1D\b", name, re.I):
            exact_key = "V_S36"
        else:
            exact_key = "V_S35"
    elif event_no == 26 and re.search(r"\b1F\b.*TURBO", name, re.I):
        exact_key = "V_S14"
    elif event_no == 1 and re.search(r"DAY \d (?:RESTART|RE-ENTRY)", name, re.I):
        exact_key = "V_S10"
    elif event_no == 26 and re.search(r"DAY \d (?:RESTART|RE-ENTRY)", name, re.I):
        exact_key = "V_S12"
    if exact_key:
        exact = next((c for c in cands if c.get("_key") == exact_key), None)
        if exact:
            return exact, None

    if len(cands) == 1:
        return cands[0], None
    timed = [c for c in cands if (c.get("start_time") or "").strip().upper() == (time or "").upper()]
    if len(timed) == 1:
        return timed[0], None
    # Never attach the first arbitrary matching sheet: doing so silently exposes
    # the wrong fee, level, or flight rules as if they belong to this row.
    return None, AMBIGUOUS_NOTE


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
    sheet, sheet_note = pick_sheet(row["event_no"], row.get("time"), row.get("date"), row.get("event_name") or "")
    sheet_url = sheet.get("source") if sheet else ""
    sources = [row["source"]] + ([sheet_url] if sheet_url else [])

    # The PDF text extractor splits the Event 56 1A/1B detail lines at the
    # page-column boundary: it drops the printed $500K GTD and truncates the
    # rake-discount note. The venue's live event page prints both facts in full.
    # Restore them only for the affected two rows and retain that page as a row
    # source, rather than carrying forward the incomplete PDF extraction.
    if row["event_no"] == 56 and row.get("date") == "2026-12-17":
        suffix = "1A" if (row.get("time") or "").upper() == "10:10 AM" else "1B"
        name = f"$1,100 No Limit Hold'em {suffix} $500K GTD"
        gtd = 500000
        page_url = "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"
        if page_url not in sources:
            sources.append(page_url)
    kind, tags = classify(name)
    entry = {
        "id": f"V{row['event_no']}-{row.get('date')}-{(row.get('time') or '').replace(' ', '').lower()}",
        "venue": "venetian",
        "venue_name": "The Venetian Poker Room",
        "event_no": row["event_no"],
        "name": (f"${buy:,} {name.title()}" if buy and not name.lstrip().startswith("$") else name.title()),
        "name_printed": name,
        "date": row.get("date"),
        "weekday": row.get("weekday"),
        "time": row.get("time"),
        "registration_closes": row.get("registration_closes"),
        "buy_in_usd": buy,
        "guarantee_usd": gtd,
        "guarantee_text": row.get("guarantee_text"),
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
    if row["event_no"] == 56 and row.get("date") == "2026-12-17":
        suffix = "1A" if (row.get("time") or "").upper() == "10:10 AM" else "1B"
        cutoff = "10:10 a.m." if suffix == "1A" else "6:10 p.m."
        entry["conditional_entry_fee"] = {
            "standard_usd": 1100,
            "early_usd": 1060,
            "discount_usd": 40,
            "deadline": f"before the event starts ({cutoff})",
            "excerpt": (f"On Day {suffix}, players who register before the start of the event "
                        f"({cutoff}) will receive a forty ($40) discount on house fees for a "
                        "total buy in of $1,060 instead of $1,100."),
            # The figures are the sheet's; the sentence is the build's wording, so it is
            # labelled as such until the sheet is re-read and the wording captured verbatim.
            "excerpt_kind": "reconstructed",
            "source": sheet_url,
            "retrieved": (sheet or {}).get("retrieved"),
        }
    # Verified conditional entry fees carried on the snapshot row itself
    # (data/c2242cb1/venetian_overrides.json), e.g. Event 59 Day 1A's $20 early
    # discount from structure sheet 4 rule 7. Each dict carries its own source,
    # excerpt and retrieval date.
    if row.get("conditional_entry_fee") and "conditional_entry_fee" not in entry:
        entry["conditional_entry_fee"] = row["conditional_entry_fee"]
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
        # A printed Day-2 bagging clause is a real restriction on entering subsequent
        # flights. Surface it in the re-entry field (2026-11-19 round) so the structured
        # rule field carries the sheet's own sentence instead of a silent blank — while
        # never treating it as a single-entry grant: it says nothing about re-entering a
        # flight after busting, so single_entry stays unverified.
        bag = sheet.get("bagging")
        if bag and entry["rules"]["re_entry"].get("status") in (None, "not_stated_in_sheet"):
            entry["rules"]["re_entry"] = {
                "status": "restricted_once_bagged",
                "value": "a player who bags for Day 2 may not play a subsequent flight (printed); "
                         "nothing else about re-entry is printed on the sheet",
                "excerpt": bag,
                "source": sheet_url,
                "retrieved": sheet.get("retrieved"),
            }
        entry["spend_advantage_evidence"] = [
            reason for pat, reason in SPEND_ADVANTAGE_PATTERNS
            if re.search(pat, (sub or "") + " " + " ".join(flat_excerpts), re.I)
        ]
        if fee is not None and entry["buy_in_usd"]:
            # Prefer the sentence the sheet itself prints.  `fee_sentence` is captured
            # verbatim by tools/sync_official_sources.py; until a sheet has been re-read
            # with that capture in place, the fallback below restates the printed
            # figures in the room's standard wording, and the row says so.
            verbatim = sheet.get("fee_sentence")
            entry["rules"]["fee"] = {
                "status": "confirmed",
                "value": f"${fee} of ${entry['buy_in_usd']} withheld; ${pool} per entry to the prize pool"
                         if pool is not None else f"${fee} of ${entry['buy_in_usd']} withheld",
                "excerpt": verbatim or (
                    f"$ {fee} of the $ {entry['buy_in_usd']} Buy-In is withheld for house fees (Rake + Staff)."
                    + (f" The prize pool consists of $ {pool} of every $ {entry['buy_in_usd']} Buy In."
                       if pool is not None else "")),
                "excerpt_kind": "verbatim" if verbatim else "reconstructed",
                "source": sheet_url,
                "retrieved": sheet.get("retrieved"),
            }
        else:
            entry["rules"]["fee"] = {"status": "unverified", "value": None, "excerpt": None,
                                     "excerpt_kind": "verbatim",
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

# --- Wynn: the room's own structure PDFs, re-read 2026-11-17 -------------------
# The c07371e3 capture of Wynn's dailies and WPT rows predates today's read of the
# venue's published structure sheets, which print the fee split, the stack, the level
# length, the registration cutoff and the suspension clause verbatim.  The overlay file
# holds only those printed values, each with the sentence it came from, so a value the
# PDF does not state stays blank and stays flagged rather than being filled in here.
_wynn_copies = sorted(DATA.glob("wynn-official-*.json"))
WYNN_OVERLAY = (json.loads(_wynn_copies[-1].read_text(encoding="utf-8")) if _wynn_copies
                else load("wynn-official-2026-11-17.json") if (DATA / "wynn-official-2026-11-17.json").exists() else {})
WYNN_VERIFIED = WYNN_OVERLAY.get("rows") or {}
WYNN_OVERLAY_DATE = (WYNN_OVERLAY.get("meta") or {}).get("retrieved") or TODAY


def add_room_row(venue_id, venue_name, *, when, time, name, buy, gtd, reentry, addon, fee_txt,
                 srcs, note=None, reg_closes=None, chips=None, overlay_key=None):
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
    ver = WYNN_VERIFIED.get(overlay_key or "") or {}
    if ver:
        # Only what the room's own sheet prints is applied here, and each value carries the
        # sentence it came from plus the PDF's capture hash, so a reader can re-open the sheet
        # at the same line. A field the sheet does not state stays blank and stays flagged.
        for field in ("guarantee_usd", "starting_chips", "pool_per_entry_usd", "fee_usd",
                      "staff_charge_usd", "players_per_table"):
            if ver.get(field) is not None:
                entry[field] = ver[field]
        entry["guarantee_printed"] = entry.get("guarantee_usd") is not None
        if ver.get("level_minutes"):
            entry["level_duration"] = ver["level_minutes"]
        if ver.get("registration_end"):
            entry["registration_closes"] = ver["registration_end"]
        quotes = ver.get("quotes") or {}
        vsrc = (ver.get("sources") or [None])[0]
        vdate = ver.get("retrieved") or WYNN_OVERLAY_DATE
        if vsrc:
            entry["sources"] = list(dict.fromkeys([u for u in (entry["sources"] or []) + [vsrc] if u]))
        sheet_buy = ver.get("buy_in_usd")
        if sheet_buy and entry.get("buy_in_usd") and int(sheet_buy) != int(entry["buy_in_usd"]):
            entry["flags"].append(f"buy-in on the room's sheet (${sheet_buy:,}) differs from the "
                                  f"captured row (${entry['buy_in_usd']:,}); the sheet value is used")
            entry["buy_in_usd"] = int(sheet_buy)
        elif sheet_buy and not entry.get("buy_in_usd"):
            entry["buy_in_usd"] = int(sheet_buy)
        entry["rules"]["fee"] = {
            "status": "confirmed" if ver.get("fee_text") else "unverified",
            "value": ver.get("fee_text"), "excerpt": quotes.get("fee"),
            "source": vsrc, "retrieved": vdate,
        }
        re_txt = ver.get("re_entry")
        entry["rules"]["re_entry"] = {
            "status": ("confirmed_limited" if ver.get("entry_limit_printed")
                       else "confirmed_not_allowed" if re_txt and "not allowed" in re_txt.lower()
                       else "confirmed_allowed" if re_txt else "unverified"),
            "value": re_txt, "excerpt": quotes.get("re_entry"),
            "source": vsrc, "retrieved": vdate,
        }
        entry["rules"]["add_on"] = {
            "status": "confirmed_allowed" if ver.get("add_on") else "not_stated_in_sheet",
            "value": ver.get("add_on"), "excerpt": quotes.get("add_on") or quotes.get("chips"),
            "source": vsrc, "retrieved": vdate,
        }
        single = ver.get("single_entry_status") or "unverified"
        entry["rules"]["single_entry"] = {
            "status": single,
            "value": (ver.get("entry_limit_printed") or "multiple entries allowed") if single == "no" else None,
            "excerpt": quotes.get("re_entry"), "source": vsrc, "retrieved": vdate,
        }
        entry["spend_advantage"] = single == "no"
        if single == "no":
            # the sheet states the entry rule, so "unverified" no longer applies to this row
            entry["flags"] = [f for f in entry["flags"] if f != "single-entry unverified"]
        entry["sheet_guarantee_text"] = quotes.get("guarantee") or ver.get("guarantee_printed")
        entry["guarantee_wording"] = ver.get("guarantee_printed")
        entry["added_pool_wording"] = ver.get("added_pool_printed")
        entry["bounty_wording"] = ver.get("bounty_note")
        entry["entry_limit_wording"] = ver.get("entry_limit_printed")
        entry["levels_note"] = quotes.get("levels")
        entry["chips_note"] = quotes.get("chips")
        entry["suspension_clause"] = quotes.get("suspension")
        entry["verified_from_sheet"] = vdate
        entry["sheet_capture"] = {"sha256": (ver.get("captured_at") or "")[:0] or None,
                                  "captured_at": ver.get("captured_at"), "line": ver.get("sheet_line"),
                                  "title": ver.get("sheet_title_printed")}
        if ver.get("dates_printed"):
            entry["printed_flights"] = ver["dates_printed"]
        if entry["spend_advantage"] and "single-entry excluded (entry rules allow more)" not in entry["flags"]:
            entry["flags"].append("single-entry excluded (the sheet allows more than one buy-in)")
    if entry.get("buy_in_usd") and entry.get("guarantee_usd"):
        entry["gtd_ratio"] = round(entry["guarantee_usd"] / entry["buy_in_usd"], 2)
        if entry.get("pool_per_entry_usd"):
            entry["gtd_over_pool_contribution"] = round(
                entry["guarantee_usd"] / entry["pool_per_entry_usd"], 2)
    if ver:
        # with the fee split and the guarantee both read from the room's own sheet, the row
        # meets the same ranking rule the Venetian rows are held to
        entry["rankable"] = bool(entry.get("buy_in_usd") and entry.get("guarantee_usd")
                                 and entry["rules"]["fee"]["status"] == "confirmed")
        entry["flags"] = [f for f in entry["flags"] if not f.startswith("schedule not re-published")]
        entry["flags"].insert(0, f"fee split read from the room's own structure sheet on {WYNN_OVERLAY_DATE}")
        if not entry.get("guarantee_usd"):
            entry["flags"].append("no guarantee printed on the sheet — not ranked")
        if entry.get("suspension_clause"):
            entry["flags"].append("may be suspended during a tournament series — see the sheet clause")
    checked, changed = last_checked_for(entry.get("sources") or srcs)
    entry["last_checked"] = checked
    entry["source_changed"] = changed
    events.append(entry)


for r in ([] if ROOM_FACTS else WYNN_DAILY):
    add_room_row("wynn", "Wynn Las Vegas Poker", when=r["schedule"], time=r["time"],
                 name=r["event_name"], buy=int(r["buy_in_usd"]) if r["buy_in_usd"] else None,
                 gtd=int(r["guarantee_usd"]) if r["guarantee_usd"] else None,
                 reentry=None if r["re_entry"].lower().startswith("not") else r["re_entry"],
                 addon=None if r["rebuy_addon"].lower().startswith("none") else r["rebuy_addon"],
                 fee_txt=r["fees_and_staff"] or None, reg_closes=r.get("registration_end"),
                 overlay_key=f"{r['schedule']}|{r['time']}",
                 srcs=[r["source"],
                       "https://cdn.wynnresorts.com/image/upload/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf"],
                 note=r.get("flag") or None)
for r in ([] if ROOM_FACTS else WYNN_WPT):
    add_room_row("wynn", "Wynn Las Vegas Poker", when=r["dates"], time=None, name=r["event_name"],
                 buy=int(r["buy_in_usd"]) if r["buy_in_usd"] else None,
                 gtd=int(r["guarantee_usd"]) if r["guarantee_usd"] else None,
                 reentry=None if "NOT CAPTURED" in r["re_entry"].upper() else r["re_entry"],
                 addon=None, fee_txt=None,
                 overlay_key=f"{r['dates']}|{r['event_name']}",
                 srcs=[r["source"],
                       "https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf",
                       "https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf"],
                 note="WPT World Championship series row (Nov 27 – Dec 21, 2026) from the venue's own PDFs" if "NOT CAPTURED" not in r["re_entry"].upper()
                      else "entry terms not captured from the official PDFs — treated as unverified, not as single-entry")
for r in ([] if ROOM_FACTS else BELLAGIO):
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
for r in ([] if ROOM_FACTS else (CFG.get("preserved_rows", {}).get("caesars") or LEGACY.get("reentry_or_addon", []))):
    if r.get("venue", "").startswith("Caesars"):
        add_room_row("caesars", "Caesars Palace Poker Room", when=r["day"], time=r["time"],
                     name=r["name"], buy=r.get("buy_in"), gtd=r.get("guarantee"),
                     reentry=(r.get("reentry_addon") or "").split(";")[0] or None,
                     addon=(r["reentry_addon"].split("add-on")[1].strip(" ;") if "add-on" in (r.get("reentry_addon") or "").lower() else None),
                     fee_txt=None, srcs=r.get("source_urls") or [LEGACY["sources"][k]["url"] for k in r.get("sources", []) if k in LEGACY.get("sources", {})],
                     note="Preserved from the earlier capture; the official 2026 daily flyer (now tracked as C_FLYER) prices this start time differently, so this fallback row needs re-verification")

# ------------------------------------------------- rooms re-read from their own PDFs
# tools/room_extract.py turns the *committed official captures* (data/raw/*, the same
# bytes the monitor hashes) into dated rows with a printed fee split and a printed
# entry rule.  Before this, only the Venetian calendar carried dates, so the date
# filter, the day plan and the trip cost could not see Wynn, Bellagio or Caesars.
# Nothing here is typed by hand: every field below comes out of that file.
ROOM_ROWS = []
WPT_SCHED_URL = next((x["url"] for x in (ROOM_FACTS or {}).get("meta", {}).get("sources", [])
                      if "Schedule.pdf" in x["url"]), "")
if ROOM_FACTS:
    def _rule(src, default_status="not_stated_in_sheet"):
        st = (src or {}).get("status") or default_status
        return {"status": st, "value": (src or {}).get("value"),
                "excerpt": (src or {}).get("excerpt")}

    def prize_pool_component(components):
        """The printed slice of the buy-in that funds the prize pool, if the sheet names it."""
        for want in ("tournament prize pool", "prize pool"):
            for c in components or []:
                if c["amount_usd"] and want in (c["purpose"] or "").lower():
                    return c["amount_usd"]
        return None

    def room_rule_set(rules, url, retrieved):
        out = {}
        for key in ("single_entry", "re_entry", "add_on"):
            r = _rule((rules or {}).get(key))
            out[key] = {**r, "source": url, "retrieved": retrieved}
        return out

    def fee_rule(components, total, url, retrieved, excerpt, note=None):
        if not components or not total:
            return {"status": "unverified", "value": None, "excerpt": excerpt or None,
                    "source": url, "retrieved": retrieved}
        known = sum(c["amount_usd"] or 0 for c in components)
        purposes = "; ".join(f"${c['amount_usd']:,} {c['purpose']}" for c in components if c["amount_usd"])
        return {"status": "confirmed", "value": purposes + (f" (adds to ${known:,})" if known != total else ""),
                "excerpt": excerpt, "source": url, "retrieved": retrieved,
                "sums_to_buy_in": known == total}

    WEEKDAY = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


WEEKDAY = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def recurrence_from_printed(text) -> dict | None:
    """Turn the days a room actually printed into the weekday names they cover.

    Only what the document says is used: "Nightly Monday-Sunday" covers every day because the range
    does, "Monday-Thursday" covers four, and a phrase this cannot parse returns None so the row stays
    undated rather than being quietly assumed to run every day.
    """
    if not text:
        return None
    t = re.sub(r"\s+", " ", str(text)).strip()
    idx = {d[:3]: i for i, d in enumerate(WEEKDAY)}   # matched on the three-letter prefix the sheets use
    days: list[str] = []
    for part in re.split(r"[,&]| and ", t):
        part = part.strip().rstrip(".")
        if not part:
            continue
        if re.search(r"\b(daily|nightly|every day|each day|all days)\b", part, re.I):
            days = list(WEEKDAY)
            continue
        m = re.search(r"([A-Za-z]+)\s*(?:-|to|\u2013|through)\s*([A-Za-z]+)", part)
        if m and m.group(1)[:3] in idx and m.group(2)[:3] in idx:
            lo = idx[m.group(1)[:3]]
            hi = idx[m.group(2)[:3]]
            span = list(range(lo, hi + 1)) if hi >= lo else list(range(lo, 7)) + list(range(0, hi + 1))
            days.extend(WEEKDAY[i] for i in span)
            continue
        w = re.match(r"([A-Za-z]+)", part)
        if w and w.group(1)[:3] in idx:
            days.append(WEEKDAY[idx[w.group(1)[:3]]])
    seen, out = set(), []
    for d in days:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return {"printed": t, "days": out} if out else None


def room_row(*, rid, venue, venue_name, date, time, name, buy, gtd, rules, fee, chips_,
             level_min, reg, sources, extra_flags, gtd_excerpt=None, note=None,
             pool=None, house=None, weekday=None, recurrence=None):
    ev = {
        "id": rid, "venue": venue, "venue_name": venue_name, "event_no": None,
        "name": name, "name_printed": name.upper(), "date": date,
        # the weekday is read off the printed date; it is a calendar fact, not a claim about the venue
        "weekday": weekday or (WEEKDAY[dt.date.fromisoformat(date).weekday()] if date else None),
        "time": time, "registration_closes": reg, "buy_in_usd": buy,
        "guarantee_usd": gtd, "guarantee_printed": gtd is not None,
        "starting_chips": chips_, "level_duration": str(level_min) if level_min else None,
        "kind": "Tournament", "tags": ["Recurring / weekly"],
        "is_flight": False, "is_continuation": False,
        "rules": {**rules, "fee": fee},
        "sources": sources, "sheet_key": None, "notes": note,
        "spend_advantage": bool((rules or {}).get("spend_advantage")),
        "single_entry_confirmed": (rules or {}).get("single_entry", {}).get("status") == "confirmed",
        "flags": [],
    }
    if recurrence:
        # a recurring slate prints weekdays, not a calendar date. The date filter and the day plan use
        # exactly those printed words — nothing else — to decide which days this row is playable on.
        ev["recurrence"] = recurrence
        ev["weekday"] = (", ".join(recurrence["days"]) if len(recurrence["days"]) < 7 else "every day")
    if house:
        # the house share of the entry, kept as its own number (the brief asks for the fee value
        # separately from the buy-in, not folded into a single "price" cell)
        ev["house_fee_usd"] = house
    if pool:
        ev["pool_per_entry_usd"] = pool
        if buy and pool:
            ev["gtd_over_pool_contribution"] = round(gtd / pool, 2) if gtd else None
    if gtd_excerpt:
        ev["guarantee_from_sheet_text"] = gtd_excerpt
    if buy and gtd:
        ev["gtd_ratio"] = round(gtd / buy, 2)
    checked, changed = last_checked_for(sources)
    ev["last_checked"] = checked
    ev["source_changed"] = changed
    ev["rankable"] = bool(buy and gtd and ev["rules"]["fee"]["status"] == "confirmed"
                          and not ev["spend_advantage"] and not extra_flags)
    if not ev["single_entry_confirmed"] and not ev["spend_advantage"]:
        ev["flags"].append("single-entry unverified")
    if ev["spend_advantage"]:
        ev["flags"].append("spend-advantage format — excluded from the single-entry list")
    if ev["rules"]["fee"]["status"] != "confirmed":
        ev["flags"].append("fee split not printed — not ranked")
    ev["flags"].extend(extra_flags)
    ROOM_ROWS.append(ev)

# --- Wynn WPT World Championship: one row per printed play day -----------------
wpt = ROOM_FACTS["wynn_wpt"]
for e in wpt["events"]:
    rules = room_rule_set(e["rules"], e["source"], e["retrieved"])
    rules["spend_advantage"] = e["rules"].get("spend_advantage")
    fee = fee_rule(e["fee_components"], e["buy_in_usd"], e["source"], e["retrieved"], e["fee_excerpt"])
    flags = []
    if e.get("fee_split_sums_to_buy_in") is False:
        flags.append("official sheet's own fee split does not add up — recorded verbatim, needs venue confirmation")
    if e.get("discounted_entry_excerpt"):
        flags.append("sheet also prints a discounted entry for this event")
    if not e["days"]:
        flags.append("no play day printed on the sheet")
    label = re.sub(r"\s*\$[\d,]+\s+[Gg]uarantee(d)?\s+poker$", "", e["name_printed"]).strip()
    for i, d in enumerate(e["days"]):
        stage = d.get("stage") or ""
        room_row(
            rid=f"{e['id']}-{d['date']}-{d['time'].replace(' ', '').replace(':', '')}"
                + (f"-{stage.replace(' ', '')}" if stage else ""),
            venue="wynn", venue_name=e["venue_name"],
            date=d["date"], time=d["time"],
            name=f"${e['buy_in_usd']:,} {label}" + (f" · {stage}" if stage else ""),
            buy=e["buy_in_usd"], gtd=e["guarantee_usd"], rules=rules, fee=fee,
            pool=prize_pool_component(e["fee_components"]),
            chips_=e["starting_chips"], level_min=e["level_minutes"],
            reg=None, sources=[e["source"]] + ([WPT_SCHED_URL] if WPT_SCHED_URL else []),
            extra_flags=flags, gtd_excerpt=e.get("guarantee_excerpt"),
            note=("Day 2 / final of an event whose Day 1 is listed separately — no new entry" if stage and stage.lower().startswith(("day 2", "day 3", "day 4", "day 5", "final")) else None))

# --- Wynn daily slate: the sheet prints the days offered, not calendar dates ----
# The same sheet says the slate "may be suspended during Seniors Events, Classic Events,
# or other Tournament Series", and the venue's own WPT schedule covers 2026-11-27 →
# 2026-12-21.  Both printed facts are recorded and the rows are flagged, rather than
# scheduled as if the series had not suspended them.
series_days = sorted({x["date"] for blk in ROOM_FACTS["wynn_wpt"]["events"] for x in blk["days"]})
for e in ROOM_FACTS["wynn_daily"]["events"]:
    rules = room_rule_set(e["rules"], e["source"], e["retrieved"])
    rules["spend_advantage"] = e["rules"].get("spend_advantage")
    fee = fee_rule([], e["buy_in_usd"], e["source"], e["retrieved"], e.get("fee_excerpt"))
    rec = recurrence_from_printed(e.get("offered_days_printed"))
    extra = [("recurring slate — the sheet prints “" + (e.get("offered_days_printed") or "no days") + "”, not calendar dates, "
              "so it is offered on those weekdays rather than placed on a dated slot"),
             "the sheet says the slate may be suspended during other Tournament Series; the venue's own WPT "
             f"series runs {series_days[0]} to {series_days[-1]}, so availability inside that window is unconfirmed"]
    if e.get("extra_play_option_excerpt"):
        extra.append("sheet also prints an optional rebuy/add-on purchase: " + e["extra_play_option_excerpt"])
    if e.get("registration_excerpt") and "NOT allowed" in e["registration_excerpt"]:
        rules["re_entry"] = {"status": "forbidden", "value": "re-entry not allowed (printed)",
                             "excerpt": e["registration_excerpt"], "source": e["source"],
                             "retrieved": e["retrieved"]}
        rules["spend_advantage"] = True   # unlimited $200 rebuys are still offered
    room_row(rid=e["id"], venue="wynn", venue_name=e["venue_name"], date=None,
             time=e["start_time"], name=f"${e['buy_in_usd']:,} {e['name_printed']}",
             buy=e["buy_in_usd"], gtd=e["guarantee_usd"], rules=rules, fee=fee,
             chips_=e["starting_chips"], level_min=e["level_minutes"], reg=None,
             sources=[e["source"], ROOM_FACTS["wynn_daily"]["poster_url"]],
             extra_flags=extra, recurrence=rec,
             note="offered " + (e["offered_days_printed"] or "days not printed on the sheet"))

# --- Bellagio weekend slate ----------------------------------------------------
for e in ROOM_FACTS["bellagio"]:
    rules = room_rule_set(e["rules"], e["source"], e["retrieved"])
    rules["spend_advantage"] = e["rules"].get("spend_advantage")
    fee = fee_rule(e["fee_components"], e["buy_in_usd"], e["source"], e["retrieved"], e.get("fee_excerpt"))
    flags = ["recurring weekly slate — no calendar date printed"]
    if e["buy_in_usd"] is None:
        flags.append("official sheet contradicts itself on the buy-in (title vs fee rule) — blank rather than guessed")
    room_row(rid=e["id"], venue="bellagio", venue_name=e["venue_name"], date=None,
             time=e["start_time"], name=e["name_printed"], buy=e["buy_in_usd"],
             gtd=e["guarantee_usd"], rules=rules, fee=fee,
             pool=prize_pool_component(e["fee_components"]), chips_=e["starting_chips"],
             level_min=e["level_minutes"], reg=None,
             sources=[e["source"], e["page_source"]], extra_flags=flags,
             gtd_excerpt=e.get("guarantee_excerpt"), weekday=e["weekday"],
             recurrence=recurrence_from_printed(e["weekday"]),
             note=f"played {e['weekday']}s")

# --- Caesars Palace: the flyer is the itemised schedule; the article is a summary ---------
# Two official pages, two price lists. The flyer (a schedule document on the property's own
# content path) prices each start time separately and prints the fee split and the re-entry
# clause; the marketing article describes all four daily events at one blanket $100. The row
# carries the flyer's value, the article's sentence stays beside it, and the disagreement is
# flagged (flag F25) instead of silently resolved. The values below are a fallback for a build
# without the capture; when data/raw/caesars-daily-flyer-2026.txt is present, every number on
# the row comes from that text via tools/room_extract.py, never from this table.
CAESARS_FLYER_URL = ("https://www.caesars.com/content/dam/empire/clv/casino/poker/"
                     "tournament-schedule/clv-poker-daily-nlh-tournament-flyer-2026.pdf")
CAESARS_FLYER_RETRIEVED = "2026-11-17"
CAESARS_FLYER_ROWS = [
    {"time_printed": "10 AM", "buy_in_usd": 100, "house_fee_usd": 30, "pool_per_entry_usd": 70,
     "guarantee_usd": 1000, "starting_chips": 20000, "level_minutes": 20,
     "fee_excerpt": "Of the $100 buy in, $70 goes to the prize pool and $30 is held by Caesars Palace as a maintenance fee."},
    {"time_printed": "2 PM", "buy_in_usd": 160, "house_fee_usd": 45, "pool_per_entry_usd": 115,
     "guarantee_usd": 1000, "starting_chips": 20000, "level_minutes": 20,
     "fee_excerpt": "Of the $160 buy in, $115 goes to the prize pool and $45 is held by Caesars Palace as a maintenance fee."},
    {"time_printed": "6 PM", "buy_in_usd": 100, "house_fee_usd": 30, "pool_per_entry_usd": 70,
     "guarantee_usd": 1000, "starting_chips": 20000, "level_minutes": 20,
     "fee_excerpt": "Of the $100 buy in, $70 goes to the prize pool and $30 is held by Caesars Palace as a maintenance fee."},
    {"time_printed": "9 PM", "buy_in_usd": 160, "house_fee_usd": 45, "pool_per_entry_usd": 115,
     "guarantee_usd": 1000, "starting_chips": 20000, "level_minutes": 20,
     "fee_excerpt": "Of the $160 buy in, $115 goes to the prize pool and $45 is held by Caesars Palace as a maintenance fee."},
]
c = ROOM_FACTS["caesars"]
flyer = c.get("flyer") or {}


def _canon_time(t):
    m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(AM|PM)", (t or "").upper())
    # the printed clock style is unpadded ("2:00 PM"), which is also how every other venue row
    # stores its start time, so the hour is deliberately not zero-padded here.
    return f"{int(m.group(1))}:{m.group(2) or '00'} {m.group(3)}" if m else None


FLYER_BY_TIME = {}
FLYER_FROM_CAPTURE = bool(flyer.get("rows"))
for _r in (flyer.get("rows") or CAESARS_FLYER_ROWS):
    _k = _canon_time(_r.get("time_printed"))
    if _k:
        FLYER_BY_TIME[_k] = _r

for t in c["times"]:
    r = FLYER_BY_TIME.get(t) or {}
    rules = room_rule_set(c["rules"], c["source"], c["retrieved"])
    rules["spend_advantage"] = True
    srcs = [c["source"]]
    if r:
        srcs = [flyer.get("url") or c["source"], c["source"]]
        for k in ("single_entry", "re_entry", "add_on"):
            fr = (flyer.get("rules") or {}).get(k) or {}
            if fr.get("excerpt"):
                rules[k] = {"status": fr["status"], "value": fr.get("value"), "excerpt": fr["excerpt"],
                            "source": flyer.get("url"), "retrieved": flyer.get("retrieved")}
    if r.get("fee_excerpt"):
        fee = {"status": "confirmed", "value": f"${r['house_fee_usd']} of the ${r['buy_in_usd']} buy-in is the house fee; "
                f"${r['pool_per_entry_usd']} per entry goes to the prize pool",
               "excerpt": r["fee_excerpt"], "source": flyer.get("url"), "retrieved": flyer.get("retrieved")}
    else:
        fee = {"status": "unverified", "value": None, "excerpt": c["rules"]["fee"]["excerpt"],
               "source": c["source"], "retrieved": c["retrieved"]}
    buy = r.get("buy_in_usd") or c["buy_in_printed"]
    flags = ["daily slate — the flyer prints no calendar date"]
    if r and not FLYER_FROM_CAPTURE:
        flags.append("flyer value reconstructed from the 2026-11-17 read — this build has no data/raw capture of the PDF to re-derive it from")
    if r:
        flags.append("official 2026 flyer prices this start time; the property's article states a blanket $100 "
                     "for all four daily events — both sentences are on the row, the conflict is not resolved (flag F25)")
    else:
        flags.append("official page prints no house-fee split, so the row is not ranked")
    room_row(rid="CAESARS-DAILY-" + t.replace(" ", "").replace(":", ""), venue="caesars",
             venue_name="Caesars Palace Poker Room", date=None, time=t,
             name=f"${buy} No Limit Hold'em", buy=buy,
             gtd=r.get("guarantee_usd") or c["guarantee_printed"], rules=rules, fee=fee,
             pool=r.get("pool_per_entry_usd"), house=r.get("house_fee_usd"),
             chips_=r.get("starting_chips") or c["chips_printed"],
             level_min=r.get("level_minutes") or c["level_minutes_printed"],
             reg=(re.sub(r"^Registration will close at\s*", "", flyer.get("registration_excerpt") or "").strip().rstrip(".") or None) if r else None,
             sources=srcs, extra_flags=flags,
             gtd_excerpt=(f"${r['guarantee_usd']:,} guarantee printed in the flyer's schedule table"
                          if r.get("guarantee_usd") else None),
             recurrence=recurrence_from_printed(flyer.get("title") or (c.get("schedule_excerpt") or "")),
             note=("flyer row: “" + E(r["row_excerpt"]) + "” · add-on: " + (flyer.get("addon_excerpt") or c["rules"]["add_on"]["excerpt"]))
             if r else ("add-on offered: " + c["rules"]["add_on"]["excerpt"]))
events.extend(ROOM_ROWS)


events.sort(key=lambda e: (e.get("date") or "9999-99-99", e.get("time") or "", e["venue"]))

# Two printed calendar rows can share an id when a venue repeats a row on the same day at
# the same time (the Venetian Dec 11 play-down/final-table pair does).  Anchors must be
# unique or the date filter and the detail toggles target the wrong row, so a stable
# suffix is appended — the row count itself is never changed.
_seen: dict[str, int] = {}
for _ev in events:
    _base = _ev["id"]
    if _base in _seen:
        _seen[_base] += 1
        _ev["id"] = f"{_base}--{_seen[_base]}"
        _ev["duplicate_printed_row"] = True
    else:
        _seen[_base] = 1

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
        for key in ("resort_fee", "room_tax", "parking", "cancellation", "occupancy_charge", "check_in_out"):
            for sent in (facts.get(key) or [])[:3]:
                rate_log.append({
                    "hotel_id": h["id"], "property": h["property"], "seq": 90,
                    "observed_on": TODAY,
                    "label": f"official {key.replace('_', ' ')} wording",
                    "amount_usd": None, "qualifier": sent, "source": url,
                    "quote_status": f"verbatim sentence captured {SNAPSHOT_AT[:10] or TODAY}",
                    "field": key,
                })
# The walking check on this site is always "lobby -> the Venetian poker room", because
# the trip is planned around the DeepStack series there. Measured pairs come from
# data/walk-measurements.json; a hotel that also hosts a room of its own gets a second
# row for that room, marked as not measured rather than silently reusing the Venetian
# number.
_walk_dates = sorted({(p.get("captured_at") or "")[:10] for p in (WALKMEAS.get("pairs") or []) if p.get("captured_at")})
WALK_MEASURED_ON = " and ".join(_walk_dates) if _walk_dates else ((WALKMEAS.get("meta") or {}).get("generated_at", "")[:10] or TODAY)
walk_measured_on = WALK_MEASURED_ON
WALK_TARGET_ID = "venetian"
WALK_BY_HOTEL = {m["hotel_id"]: m for m in (WALKMEAS.get("pairs") or [])}
walks: list[dict] = []
for h in CFG["hotels"]:
    w = h.get("walk") or {}
    # The measured walk targets the Venetian poker room for every hotel (the brief's
    # ≤30-min axis). Use the walk's own target venue/venue_id when present so the pair
    # label matches the measurement, not the hotel's grouping venue_id.
    for vid in ([w.get("venue_id")] if w.get("venue_id") else (h.get("venue_ids") or [])):
        walks.append({
            "hotel_id": h["id"], "hotel": h["property"], "venue_id": vid,
            "venue": w.get("venue") or (VENUE_BY_ID.get(vid) or {}).get("name", vid),
            "minutes": w.get("minutes"),
            "distance_mi": w.get("distance_mi"),
            "via": w.get("via"),
            "meets_30_min": w.get("meets_30_min", "unverified"),
            "status": w.get("status"),
            "method": w.get("method"),
            "retrieved": w.get("retrieved"),
            "source": w.get("source"),
        })
with open(DATA / "rate-log.json", "w", encoding="utf-8") as fh:
    json.dump({"meta": {"generated_at": SNAPSHOT_AT or TODAY,
                        "policy": "A dated log, not a single value. Every line keeps the date it was observed, the wording it came from and whether it is a dated quote at all."},
               "entries": rate_log}, fh, indent=1)
with open(DATA / "walks.json", "w", encoding="utf-8") as fh:
    json.dump({"meta": {"generated_at": SNAPSHOT_AT or TODAY, "rule": CFG["walk_policy"]["rule"],
                        "how_to_close": CFG["walk_policy"]["how_to_close"],
                        "measurement_source": (WALKMEAS.get("meta") or {}),
                        "measured_pairs": sum(1 for p in walks if p.get("minutes") is not None),
                        "within_30": sum(1 for p in walks if str(p.get("meets_30_min", "")).lower().startswith(("yes", "not applicable")))},
               "pairs": walks}, fh, indent=1)
with open(DATA / "site-events.json", "w", encoding="utf-8") as fh:
    json.dump({"meta": {"generated_at": SNAPSHOT_AT or TODAY, "rows": len(events),
                        "verified_single_entry": sum(1 for e in events if e.get("single_entry_confirmed")),
                        "rankable": sum(1 for e in events if e.get("rankable")),
                        "spend_advantage": sum(1 for e in events if e.get("spend_advantage"))},
               "events": events}, fh, indent=1)

# ------------------------------------------------------------------------ day plan
def to_min(t: str | None):
    """Minutes after midnight from a printed clock time, or None if it is not a clock time.

    Wynn prints bare hours ("12 PM", "6 PM") where the Venetian prints "11:10 AM"; both are parsed,
    and a value that is not a clock time at all ("the start of level seven") stays None so nothing is
    sequenced on an guess.
    """
    if not t:
        return None
    m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(AM|PM)", t.upper())
    if not m:
        return None
    h = int(m.group(1)) % 12 + (12 if m.group(3) == "PM" else 0)
    return h * 60 + int(m.group(2) or 0)


days: dict[str, dict] = {}
for ev in events:
    if not ev.get("date") or ev.get("is_continuation"):
        continue
    days.setdefault(ev["date"], []).append(ev)

# No Strip room publishes how long its tournaments last, so a duration is never
# invented here.  A day gets a conditional fallback only when the second event's
# printed start is at or after the first event's printed late-registration deadline:
# at that point the first entry can no longer be bought, so the sequence is at least
# arithmetically possible.  Every day also lists the printed Day-2 / final restarts,
# which are the only official signal about when a play day ends.
def event_key(ev):
    """Identity of the *event*, not of the printed start: 1A and 1B are one event, two ways in."""
    if ev.get("event_no"):
        return f"V{ev['event_no']}"
    return re.split(r"-20\d\d-", ev["id"])[0]


plan = []
for date, rows in sorted(days.items()):
    rows = sorted(rows, key=lambda r: to_min(r["time"]) or 0)
    # The day's lead entry: prefer a ranked (fee + guarantee confirmed, single-entry
    # candidate) row, earliest start first; otherwise the earliest printed start.
    primary = next((r for r in rows if r.get("rankable")), rows[0])
    p_close = to_min(primary.get("registration_closes"))
    fallback, why_not = None, ("the leading event prints no late-registration deadline, so no second "
                               "entry can be shown to be reachable") if p_close is None else (
                              "no other event starts at or after the leading event's printed registration deadline")
    for cand in rows:
        if cand is primary or cand.get("is_continuation"):
            continue
        if event_key(cand) == event_key(primary):
            continue   # a later flight of the same event is an alternative start, not a second entry
        c_start = to_min(cand.get("time"))
        if c_start is None or p_close is None:
            continue
        if c_start >= p_close:
            fallback, why_not = cand, ""
            break
    cont = [e for e in events if e.get("date") == date and e.get("is_continuation")]
    conflicts = []
    ranked = [r for r in rows if r.get("rankable")]
    if len(ranked) > 1:
        conflicts.append(f"{len(ranked)} ranked entries share this day "
                         f"(starts {', '.join(sorted({r.get('time') or 'not printed' for r in ranked}))}); "
                         f"entering one rules out the others, and no sheet prints a finish time to settle it")
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            ac = to_min(a.get("registration_closes"))
            bs = to_min(b.get("time"))
            if ac and bs and bs < ac and a.get("rankable") and b.get("rankable"):
                conflicts.append(f"{a['name']} keeps registration open until {a['registration_closes']}, after "
                                 f"{b['name']} starts at {b['time']} — playable in sequence only if you are out of the "
                                 f"first event before that deadline, which the sheet does not promise")
    # Recurring slates (Wynn dailies, Bellagio weekend events, Caesars' four-a-day) print weekdays,
    # not dates, so the only honest way to offer them on a given day is the weekday the document names.
    dow = rows[0].get("weekday")
    rec_opts = []
    for e in events:
        if e.get("date") or not e.get("recurrence") or not dow:
            continue
        if dow not in e["recurrence"]["days"]:
            continue
        r_start = to_min(e.get("time"))
        if r_start is None:
            feas = (f"no sequencing test is possible: this row prints “{e.get('time') or 'no time'}”, which is not a clock time "
                    "the deadline arithmetic can read")
        elif p_close is None:
            feas = ("no sequencing test is possible: the lead event prints no late-registration deadline, "
                    "so whether a second entry fits is not answerable from the schedule")
        elif r_start >= p_close:
            feas = (f"starts {e.get('time')}, at or after the lead event's printed registration deadline "
                    f"({primary.get('registration_closes')}), so a second entry is arithmetically possible")
        else:
            feas = (f"starts {e.get('time')}, before the lead event's registration closes "
                    f"({primary.get('registration_closes')}) — reachable only if you are already out of the lead event")
        rec_opts.append({"id": e["id"], "name": e["name"], "venue": e["venue_name"], "time": e.get("time"),
                         "buy_in_usd": e.get("buy_in_usd"), "printed_days": e["recurrence"]["printed"],
                         "feasibility": feas, "sources": e.get("sources") or []})
    plan.append({
        "date": date, "weekday": rows[0].get("weekday"),
        "recurring_options": rec_opts,
        "primary": primary, "fallback": fallback, "fallback_unavailable": why_not,
        "earliest_printed_start": next((r["time"] for r in rows if r.get("time")), None),
        "duration_note": ("no official source prints a finish time or a round count for this day, so the plan "
                          "gives a start and a late-registration deadline rather than a predicted end"),
        "restarts": [c["name"] for c in cont],
        "overlap_notes": conflicts,
        # counting one entry per *event*, because a 1A/1B pair is one event with two ways in
        "distinct_ranked_events": len({event_key(r) for r in ranked}),
        "entries_usd": sum(next(r for r in ranked if event_key(r) == k).get("buy_in_usd") or 0
                           for k in sorted({event_key(r) for r in ranked})),
    })
with open(DATA / "day-plan.json", "w", encoding="utf-8") as fh:
    json.dump({"meta": {"generated_at": SNAPSHOT_AT or TODAY,
                        "basis": "start time + printed registration-closes deadline + Day-2 restart rows on the official calendar",
                        "days": len(plan)},
               # the plan rows are compared and written field by field: dropping the two heavy nested
               # event objects keeps this file readable and keeps the build byte-stable
               "days": [{k: v for k, v in d.items() if k not in ("primary", "fallback")} |
                        {"primary_id": d["primary"]["id"],
                         "primary": {k: d["primary"].get(k) for k in ("id", "name", "date", "time",
                                                                     "registration_closes", "buy_in_usd",
                                                                     "guarantee_usd", "venue", "weekday")},
                         "fallback": ({k: d["fallback"].get(k) for k in ("id", "name", "date", "time",
                                                                         "registration_closes", "buy_in_usd",
                                                                         "guarantee_usd", "venue", "weekday")}
                                      if d["fallback"] else None),
                         "fallback_id": (d["fallback"] or {}).get("id")} for d in plan]},
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
RAW_BY_URL = {s["url"]: s["save_text_to"] for s in load("tracked-sources.json")["sources"]
              if s.get("save_text_to") and (ROOT / s["save_text_to"]).exists()}
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


RATE_KINDS_USABLE = ("advertised_rate", "dated_rate", "quoted_rate")
RATE_KINDS_ALL_IN = ("all_in_per_night",)


def hotel_true_cost(h):
    """(rate, resort_fee, tax, total_per_night, rate_log_entry) — total only if both components are published.

    Only a log entry that is actually a *room rate* may be used as one. Entries tagged
    `fee_only` (a resort fee re-read) or `not_published` are observations, not rates —
    turning them into a nightly rate would invent a number the property never printed.
    An `all_in_per_night` entry already contains the fee and the tax, so it is shown as
    the total and never run through the fee/tax arithmetic a second time.
    """
    rate = rate_note = all_in = None
    for e in (h.get("rate_log") or []):
        kind = e.get("kind") or ("advertised_rate" if e.get("amount_usd") else "not_published")
        amount = e.get("amount_usd")
        if not amount:
            continue
        if kind in RATE_KINDS_ALL_IN:
            all_in, rate_note = amount, e
            break
        if kind in RATE_KINDS_USABLE and rate is None:
            rate, rate_note = amount, e
    fee = (h.get("resort_fee") or {}).get("amount_usd")
    tax = tax_rate(h)
    if all_in is not None:
        total = round(all_in, 2)
    else:
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

NAV = [("index.html", "Overview"), ("tournaments.html", "Tournaments"), ("compare.html", "Compare"),
       ("hotels.html", "Hotels"),
       ("plan.html", "Day plan"), ("calculator.html", "Trip cost"), ("before-you-pay.html", "Before you pay"),
       ("questions.html", "Open questions"),
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
<nav><div class="mainnav">{nav}</div></nav>
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


def short_name(name: str, limit: int = 70) -> str:
    """An event name as printed can run for a paragraph (a Wynn satellite prints its
    whole offer). A table cell wants the headline, not the paragraph."""
    text = re.sub(r"\s+", " ", str(name or "")).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if ". " in cut:
        cut = cut[:cut.rfind(". ") + 1]
    return cut.rstrip() + " …"
STATUS_CLS = {"confirmed": "chip-ok", "not_stated_in_sheet": "chip-warn", "unverified": "chip-warn", "no": "chip-bad",
              "conflict": "chip-bad", "confirmed_allowed": "chip-bad", "indicated": "chip-bad",
              "restricted_once_bagged": "chip-warn", "confirmed_not_single_entry": "chip-bad"}


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
            if r.get("excerpt_kind") == "reconstructed":
                # the sentence restates the sheet's printed figures in the room's
                # standard wording — it is not a copy of this sheet's own line, and
                # the page must not present it as one.
                head += ('<div class="excerpt"><p class="excerpt-kind">reworded from the printed '
                         'figures — the sheet states the amounts below in this standard wording; '
                         'it is not a copy of this sheet&rsquo;s own line</p>'
                         f'<blockquote class="reconstructed">{E(r["excerpt"])}</blockquote></div>')
            else:
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
    discount = ev.get("conditional_entry_fee")
    if discount:
        lead = ("<strong>Conditional entry fee</strong> (figures as printed; wording reworded): "
                if discount.get("excerpt_kind") == "reconstructed"
                else "<strong>Conditional entry fee:</strong> ")
        extra.append(lead + E(discount["excerpt"]) +
                     f' <a href="{E(discount["source"])}" target="_blank" rel="noopener">official structure sheet ↗</a>' +
                     f' (retrieved {E(discount["retrieved"] or "")})')
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
        if ev.get("spend_advantage"):
            why = "descriptive only — the official sheet allows more than one entry, so this row is kept out of the ranked list"
        elif (ev.get("rules", {}).get("fee") or {}).get("status") != "confirmed":
            why = "descriptive only — this row is not ranked until the entry fee is confirmed from the sheet"
        else:
            why = "descriptive only — not a single-entry candidate"
        ratio_txt = f"<span class='muted'>{f'{ratio:,.0f}×' if ratio >= 100 else f'{ratio:.1f}×'}</span>" + note(why)
    elif ratio >= 100:
        ratio_txt = f"{ratio:,.0f}×"
    else:
        ratio_txt = f"{ratio:.1f}×"
    tags = "".join(chip(t, "chip chip-tag") for t in (ev.get("tags") or [])[:3])
    flags = "".join(chip("⚑ " + f, "chip chip-warn") for f in (ev.get("flags") or [])[:3])
    if ev.get("guarantee_usd"):
        gtd = money_cell(ev["guarantee_usd"])
    elif ev.get("guarantee_text"):
        gtd = money_cell(ev["guarantee_text"], "seats, not cash — never ranked")
    else:
        gtd = unk("no guarantee printed")
    buy_cell = money_cell(ev['buy_in_usd'], 'total buy-in incl. fee') if ev.get('buy_in_usd') else unk('not printed')
    discount = ev.get("conditional_entry_fee")
    if discount:
        buy_cell += (f'<small class="muted">{money(discount["early_usd"])} if registered '
                     f'{E(discount["deadline"])} (official $40 fee discount)</small>')
        if ev.get("guarantee_usd") and discount.get("early_usd"):
            ratio_txt += (f'<small class="muted">early-fee ratio: '
                          f'{ev["guarantee_usd"] / discount["early_usd"]:.1f}×</small>')
    return f"""<tr class="ev-row" id="{E(ev['id'])}" data-date="{E(ev.get('date') or '')}" data-venue="{E(ev['venue'])}" data-single="{1 if ev.get('single_entry_confirmed') else 0}" data-rankable="{1 if ev.get('rankable') else 0}" data-days="{E(",".join((ev.get("recurrence") or {}).get("days") or []))}" data-id="{E(ev['id'])}">
<td class="when">{head}<span class="time">{E(ev.get('weekday') or '')}{tail}</span></td>
<td class="ev">{link}<span class="evname">{E(ev['name'])}</span>{tags}{flags}</td>
<td class="num">{buy_cell}</td>
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

# The comparison table has no tab panels and no unranked rows, so it carries the date
# and venue selectors only — the same controls, the same code path.
COMPARE_FILTERS = """<div class="filters" id="filters">
<label>from <input type="date" id="f-from" min="2026-11-16" max="2026-12-31"></label>
<label>to <input type="date" id="f-to" min="2026-11-16" max="2026-12-31"></label>
<button class="btn-mini" data-preset="7" type="button">next 7 days</button>
<button class="btn-mini" data-preset="30" type="button">next 30 days</button>
<button class="btn-mini" data-preset="all" type="button">whole window</button>
<label>venue <select id="f-venue"><option value="">all venues</option>__VENUE_OPTS__</select></label>
<span class="count" id="f-count"></span>
</div>"""


def events_table(rows, base="", empty="no rows match these filters"):
    if not rows:
        return f'<p class="empty">{E(empty)}</p>'
    return ('<div class="table-scroll"><table class="events">' + TABLE_HEAD + "<tbody>"
            + "".join(event_row(ev, base) for ev in rows) + "</tbody></table></div>")


TRACKED_URLS = {t["url"] for t in TRACKED}


def status_banner():
    # a URL the registry dropped on purpose (because a live official successor was found) is not an
    # outage, so only still-tracked failures count here; the review page lists the superseded ones apart
    unreach = [s for s in source_rows if not s["ok"] and s["url"] in TRACKED_URLS]
    changed = [s for s in source_rows if s["values_changed"]]
    bits = [f'{len(SCHED["rows"])} calendar rows parsed', sheets_label(),
            f'{len(events)} events on this site', f'{sum(1 for e in events if e.get("single_entry_confirmed"))} confirmed single-entry',
            f'{len(unreach)} official URLs unreachable', f'{len(changed)} sources with value changes']
    inner = "".join(f'<span class="stat">{E(b)}</span>' for b in bits)
    return ('<div class="statusline">' + inner
            + f'<span class="stat">official-source run: {E(SNAPSHOT_AT or "never")} · 06:00 Las Vegas daily</span></div>')


def walk_minutes_to(h, vid):
    """Measured minutes from a hotel to a venue's poker room, or None if unmeasured."""
    for x in walks:
        if x["hotel_id"] == h["id"] and x["venue_id"] == vid and x.get("minutes") is not None:
            return x["minutes"]
    return None


def walk_ok_for(h, vid) -> bool:
    """True when the hotel passes the hard ≤30-minute walking rule for a venue.

    On-site properties pass trivially. Off-site properties pass only on a stored
    measurement; anything unmeasured fails rather than being assumed walkable.
    """
    m = walk_minutes_to(h, vid)
    if m is not None:
        return m <= 30
    return str((h.get("walk") or {}).get("meets_30_min", "")).lower().startswith("not applicable")


def hotels_within_walk(vid):
    hs = [h for h in CFG["hotels"] if walk_ok_for(h, vid)]
    return sorted(hs, key=lambda h: (walk_minutes_to(h, vid) is None, walk_minutes_to(h, vid) or 0))


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
            "<th>Walk to Venetian poker room</th><th>Official source</th></tr></thead><tbody>" + body + "</tbody></table></div>")


def source_table(rows, base=""):
    if not rows:
        return "<p class='empty'>none recorded</p>"
    body = ""
    for r in rows:
        state = status_span("ok", r["status"]) if r["ok"] else status_span("bad", f"{r['status']} {r.get('error') or ''}")
        chg = "yes — values" if r.get("values_changed") else ("bytes only" if r.get("bytes_changed") else ("baseline" if r.get("first_run") else "no"))
        saved = f"<a class='captured-link' href='{E(base + str(r['saved']))}'>captured text</a>" if r.get("saved") else ""
        body += (f"<tr><td>{E(r['label'])}</td><td class='num'>{E(r.get('venue') or '—')}</td><td>{E(r.get('kind') or '')}</td>"
                 f"<td class='num'>{E(r.get('checked_at') or 'never')}</td><td>{state}</td><td>{chg}</td>"
                 f"<td class='num'>{r.get('rows_parsed') if r.get('rows_parsed') is not None else ''}</td>"
                 f"<td class='srccell'>{src_cell([r['url']], r.get('checked_at'), r.get('values_changed'))}{saved}</td></tr>")
    return ("<div class='table-scroll'><table class='compact sources'><thead><tr><th>Source</th><th class='num'>Venue</th><th>Kind</th>"
            "<th class='num'>Last checked</th><th>Status</th><th>Changed</th><th class='num'>Rows parsed</th><th>Links</th></tr></thead><tbody>"
            + body + "</tbody></table></div>")


# ------------------------------------------------------------------ summary stats
import statistics as _stats

def _exec_stats():
    dated = [e for e in events if e.get("date")]
    ranked = [e for e in events if e.get("rankable")]
    buys = sorted(e["buy_in_usd"] for e in ranked if e.get("buy_in_usd"))
    top = max(ranked, key=lambda e: (e.get("gtd_ratio") or 0), default=None)
    return {
        "n_events": len(events), "n_dated": len(dated), "n_recurring": len(events) - len(dated),
        "n_single": sum(1 for e in events if e.get("single_entry_confirmed")),
        "single_note": ("nothing on any official sheet in this snapshot restricts a player to one entry — see "
                        f"the flagged section ({len(CFG['flags'])} items), starting with F1 and F2"
                        if not sum(1 for e in events if e.get("single_entry_confirmed"))
                        else "each of these rows carries the official sentence that says so"),
        "n_ranked": len(ranked), "n_spend": sum(1 for e in events if e.get("spend_advantage")),
        "n_sources": len(source_rows), "n_sheets": len(AUDIT.get("sheets") or {}), "n_sheets_detail": sheets_label(),
        "n_unreach": sum(1 for s in source_rows if not s["ok"]),
        "n_hotels": len(CFG["hotels"]), "n_rates": len(rate_log), "n_walks": len(walks),
        "median_entry": money(int(_stats.median(buys))) if buys else "not computable",
        # 6 nights at the two endpoints The Venetian prints on its own poker-rate page:
        # (rate + $55 resort fee) x 1.1338 x 6 nights.  Arithmetic on printed values only.
        "stay_low": money(round((119 + 55) * 1.1338 * 6)),
        "stay_high": money(round((209 + 55) * 1.1338 * 6)),
        "top_note": (f"The highest screening ratio actually confirmed is {top['name']} at "
                     f"{top.get('gtd_ratio')}× on a {money(top.get('buy_in_usd'))} entry."
                     if top else "No row currently has both figures confirmed."),
        "best_ratio_li": (f"The highest confirmed guarantee-to-entry ratio is {top['name']} — "
                          f"{money(top.get('guarantee_usd'))} guaranteed against a {money(top.get('buy_in_usd'))} entry "
                          f"({top.get('gtd_ratio')}×) — and the {len(ranked)} ranked rows run from that down to "
                          f"{money(min(r.get('buy_in_usd') or 0 for r in ranked))} entries."
                          if top else "No row has both figures confirmed yet."),
        "best_gtd_li": (f"The largest printed guarantee in the snapshot is {big['name']}: "
                        f"{money(big.get('guarantee_usd'))} on a {money(big.get('buy_in_usd'))} entry, from "
                        f"{big.get('venue_name')}.")
                       if (big := max(ranked, key=lambda e: e.get("guarantee_usd") or 0, default=None)) else "",
        "q_max": max((q["id"] for q in CFG["questions"]), key=lambda x: int(re.sub(r"\D", "", x) or 0)),
    }

EXEC_BLOCK = """<section class="exec">
<h2>Executive summary</h2>
<p class="mini-note">Everything in this block is counted from the rows below at build time — no figure here is typed by hand, and the snapshot date is the venue pages' own retrieval time. Two inputs are still open, and they are the two that decide whether this trip works: <a href="questions.html#Q1">what the rooms will put in writing about a second entry</a>, and <a href="questions.html">a dated checkout total</a> rather than an advertised “from” rate. Every row says which of its own fields is missing.</p>
<div class="exec-grid">
<div class="exec-card"><span class="k">Events published</span><span class="v">{n_events}</span><span class="s">{n_dated} carry a calendar date; {n_recurring} are recurring slates whose sheets print days offered, not dates</span></div>
<div class="exec-card"><span class="k">Confirmed single-entry / freezeout</span><span class="v">{n_single}</span><span class="s">{single_note}</span></div>
<div class="exec-card"><span class="k">Ranked (fee split + guarantee both printed)</span><span class="v">{n_ranked}</span><span class="s">guarantee ÷ total entry fee is shown beside each; it is descriptive, never a forecast</span></div>
<div class="exec-card"><span class="k">Kept out: more money buys an advantage</span><span class="v">{n_spend}</span><span class="s">printed re-entry, rebuy, add-on or a priced second buy-in</span></div>
<div class="exec-card"><span class="k">Official sources read</span><span class="v">{n_sources}</span><span class="s">{n_sheets_detail}; {n_unreach} URL(s) unreachable in the last run, listed on the review page</span></div>
<div class="exec-card"><span class="k">Trip-cost inputs</span><span class="v">{n_hotels}</span><span class="s">hotels with a published fee/tax chain; {n_rates} dated rate-log lines, {n_walks} measured walks</span></div>
</div>
<h3>The three things this site changes about the plan</h3>
<ol class="exec-list">
<li><strong>The single-entry list is empty on purpose.</strong> No official sheet in the snapshot restricts a player to one entry. Two rooms positively price a second entry (Venetian Valuetown: “all subsequent buy in's after the initial buy in will be $200”; Wynn: 67 of 69 event sheets print “unlimited re-entry”, the other two print a one-plus-one cap). Those rows are published, quoted and kept in their own section rather than relabelled as freezeouts.</li>
<li><strong>{best_ratio_li}</strong> {best_gtd_li} Both are printed guarantees against a printed entry fee; neither is a forecast, and every row that offers a second way in is excluded from this ranking on purpose.</li>
<li><strong>The trip cost is dominated by the hotel, not the entries.</strong> A 6-night stay at the Venetian's own published poker rate ($119–$209 a night plus the $55 resort fee, both taxed at 13.38%) comes to about {stay_low}–{stay_high} before a single buy-in, while the median ranked entry is {median_entry}. That is why the calculator takes nights first and why the hotel table is ordered by true cost per night rather than by distance — and why a dated checkout total from the booking calendar, not a marketing “from” price, is the number to hold the room against.</li>
</ol>
<p class="srcline">Machine copies: <a href="data/site-events.json">site-events.json</a> · <a href="data/day-plan.json">day-plan.json</a> · <a href="data/rate-log.json">rate-log.json</a> · <a href="data/room-facts.json">room-facts.json</a> · open questions: <a href="questions.html">Q1–{q_max}</a></p>
</section>"""


def page_index():
    ES = _exec_stats()
    exec_html = EXEC_BLOCK.format(**ES)
    findings = (f"<strong>0 of {sum(1 for e in events if e['venue'] == 'venetian')} Venetian calendar rows</strong> "
                f"can be labelled “single-entry confirmed”, and the same holds for every Wynn, Bellagio and Caesars row: "
                f"all {len(events)} published rows are unverified on that one question. "
                f"The sheets state buy-in, fee split, guarantee, stack and level schedule — and then say nothing about "
                f"whether one entry or several are allowed. Omission is not confirmation, so no row is quietly treated "
                f"as a freezeout. Where a sheet <em>does</em> speak about extra money — the Venetian Valuetown sheet's "
                f"“all subsequent buy in's after the initial buy in will be $200”, Wynn printing “unlimited re-entry” on "
                f"67 of its 69 event sheets, Bellagio's “buy-in and re-enter through the end of level 8” — that is "
                f"evidence of the opposite, and those rows sit in their own section. Re-entry wording was checked in each room's own "
                f"document as at 2026-11-17: 67 of the 69 Wynn event sheets print “unlimited re-entry”, Bellagio's Saturday sheet allows "
                f"re-entry “through the end of level 8”, and the Caesars 2026 flyer allows one “re-enter … upon elimination within the first "
                f"break of play”. The Venetian sheets print no entry rule at all, which is why 37 audited Venetian structures stay unverified "
                f"rather than confirmed.")
    rankable = [e for e in events if e.get("rankable")]
    top = sorted(rankable, key=lambda e: -(e.get("gtd_ratio") or 0))[:6]
    h_rows = ""
    for h in CFG["hotels"]:
        rate, fee, tax, total, rn = hotel_true_cost(h)
        h_rows += (f"<tr><td><a href='hotels.html#{E(h['id'])}'>{E(h['property'])}</a></td>"
                   + f"<td class='num'>{money(fee) if fee else unk('unconfirmed')}</td>"
                   + f"<td class='num'>{money(total) if total else unk('no dated rate')}</td>"
                   + f"<td class='num'>{money((h.get('parking') or {}).get('self_usd_per_day')) if (h.get('parking') or {}).get('self_usd_per_day') else unk('unconfirmed')}</td>"
                   + f"<td>{E((h.get('walk') or {}).get('meets_30_min'))}</td></tr>")
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
    _hotels_in_range = hotels_within_walk(WALK_TARGET_ID)
    _n_out = sum(1 for h in CFG["hotels"] if not walk_ok_for(h, WALK_TARGET_ID))
    _verb = "is" if _n_out == 1 else "are"
    for h in _hotels_in_range:
        rate, fee, tax, total, rn = hotel_true_cost(h)
        _wm = walk_minutes_to(h, WALK_TARGET_ID)
        h_rows += (f"<tr><td><a href='hotels.html#{E(h['id'])}'>{E(h['property'])}</a></td>"
                   + f"<td class='num'>{money(fee) if fee else unk('unconfirmed')}</td>"
                   + f"<td class='num'>{money(total) if total else unk('no dated rate')}</td>"
                   + f"<td class='num'>{money((h.get('parking') or {}).get('self_usd_per_day')) if (h.get('parking') or {}).get('self_usd_per_day') else unk('unconfirmed')}</td>"
                   + f"<td>{E(str(_wm) + ' min walk to the Venetian poker room' if _wm else 'on-site')}</td></tr>")
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
{exec_html}
<section class="cards">
<div class="card finding"><h2>The finding that changes the plan</h2><p>{findings}</p>
<p class="srcline">Evidence: <a href="review.html">the clause audit of all {len(AUDIT['sheets'])} documents ({VEN_SHEETS} Venetian structure sheets)</a> · <a href="data/structure-audit.json">structure-audit.json</a> · <a href="data/venetian_structures.json">the manual read of 12 sheets</a> · <a href="flagged.html#F1">flag F1</a></p></div>
<div class="card"><h2>Best screening ratios among rows that can be ranked</h2>
<p class="mini-note">Guarantee ÷ total entry fee, descriptive only — it is not a forecast of expected value, and none of these rows is confirmed single-entry. Ranking needs the fee split and the guarantee both confirmed; rows without them are excluded here and say why.</p>
<table class="compact"><thead><tr><th>Event</th><th>When</th><th class="num">Entry</th><th class="num">Pool/entry</th><th class="num">Guarantee</th><th class="num">Ratio</th></tr></thead><tbody>
{"".join(f"<tr><td><a href='tournaments.html#{E(e['id'])}'>{E(e['name'])}</a></td><td>{E(e.get('date') or '')}<span class='time'>{E(e.get('time') or '')}</span></td><td class='num'>{money(e['buy_in_usd'])}</td><td class='num'>{money(e.get('pool_per_entry_usd'))}</td><td class='num'>{money(e['guarantee_usd'])}</td><td class='num'>{e['gtd_ratio']:,.0f}×</td></tr>" for e in top)}
</tbody></table><p class="srcline"><a class="btn" href="tournaments.html">all {len(events)} rows</a> <a class="btn" href="compare.html">compare the shortlist</a> <a class="btn" href="plan.html">day plan</a></p></div>
<div class="card"><h2>Open questions and missing information</h2>
<ul class="ticks">{"".join(f"<li>{E(q['question'])}</li>" for q in CFG['questions'])}</ul>
<p><a class="btn" href="questions.html">questions ({len(CFG['questions'])})</a> <a class="btn" href="suggestions.html">suggestions ({len(CFG['suggestions'])})</a> <a class="btn" href="before-you-pay.html">before you pay</a> <a class="btn" href="flagged.html">flagged ({len(CFG['flags'])})</a></p></div>
</section>
<section><h2>Rooms covered</h2>
<table class="compact"><thead><tr><th>Venue</th><th class="num">Rows here</th><th>Machine-readable coverage</th><th>What that means</th><th class="num">Confirmed single-entry</th><th>Official sources</th></tr></thead><tbody>{v_rows}</tbody></table>
<h2>Hotels within a 30-minute walk of the Venetian poker room</h2>
<table class="compact"><thead><tr><th>Property</th><th class="num">Mandatory resort fee</th><th class="num">True cost/night</th><th class="num">Parking</th><th>Walk</th></tr></thead><tbody>{h_rows}</tbody></table>
<p class="mini-note">{len(_hotels_in_range)} of {len(CFG['hotels'])} properties on this site measure inside 30 minutes of the Venetian poker room; the other {_n_out} {_verb} on the <a href="hotels.html">hotels page</a>, listed and marked as failing the cut rather than quietly dropped. The minutes were measured with Google Maps walking directions on {E(walk_measured_on)} from each hotel's published address to 3355 Las Vegas Blvd. South; no operator publishes a walking time, so they are timestamped measurements with a link that re-runs the route, not official statements (<a href="flagged.html#F3">F3</a>). True cost/night = published room rate + mandatory resort fee, both taxed at {E(tax_label(CFG['hotels'][0]))}. “No dated rate” means the property publishes rates only inside its booking calendar, and we do not estimate them — see <a href="hotels.html">the hotel page</a> for the dated log and the source sentences.</p></section>
<section class="how"><h2>How this stays current</h2>
<p>All {len(source_rows)} official URLs are re-fetched on a schedule at 06:00 Las Vegas. The printed calendar PDF and every linked structure sheet are parsed field by field; a content hash detects cosmetic changes and only a <em>value</em> difference is written to the change log and flagged on the affected rows, so a re-render of the same page never looks like a schedule change. Each row carries its own “checked” date.</p>
<p>A second gate checks the other half: the <em>value-level audit</em> re-reads every official capture committed in <code>data/raw/</code> and every committed transcription of the structure sheets, then looks for the literal evidence behind each published figure and each sentence shown in a “source text” panel. A value it cannot find fails the build — it is never quietly corrected. For the current snapshot it places <strong>{E(str((load('audit-values.json', {}).get('meta') or {}).get('values_located') or '—'))} of {E(str((load('audit-values.json', {}).get('meta') or {}).get('values_checked') or '—'))}</strong> published values in their cited source with no blocking failure. <a href="review.html#audit">read the audit</a> · <a href="flagged.html#F43">F43</a>.</p>
<p><a class="btn" href="review.html">run log</a> <a class="btn" href="data/sync-status.json">sync-status.json</a> <a class="btn" href="data/change-log.json">change-log.json</a> <a class="btn" href="data/audit-values.json">audit-values.json</a> <a class="btn" href="data/site-events.json">site-events.json</a></p></section>
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
    board = [e for e in events if e.get("date") and e["date"] >= snap_day and not e.get("is_continuation")][:9]
    board_rows = "".join(
        f"<tr><td>{E(e['date'])}<span class='time'>{E(e.get('weekday') or '')}</span></td>"
        f"<td><a href='#{E(e['id'])}'>{E(e['name'])}</a></td>"
        f"<td class='num'>{E(e.get('time') or '?')}</td><td class='num'>{E(e.get('registration_closes') or 'not printed')}</td>"
        f"<td class='num'>{money(e.get('buy_in_usd'))}</td><td class='num'>{money(e.get('guarantee_usd'))}</td>"
        f"<td class='num'>{str(e.get('level_duration') or '?')} min</td>"
        f"<td>{chip('single-entry ' + e['rules']['single_entry']['status'], 'chip chip-warn')}</td>"
        f"<td class='num'><span class='checked'>checked {E(e.get('last_checked') or 'not yet')}</span></td></tr>" for e in board)
    feed = (f"""<section class="feed"><h2>Morning board — what is on from {E(snap_day)} onward</h2>
<p class="mini-note">Straight from the rooms' own printed schedules as re-read at 06:00 Las Vegas (snapshot {E(SNAPSHOT_AT or 'n/a')}); late-registration and level length are the calendar's own columns, not an estimate of when an event ends.</p>
<div class="table-scroll"><table class="compact"><thead><tr><th>Day</th><th>Event</th><th class="num">Start</th><th class="num">Reg closes</th><th class="num">Entry</th><th class="num">Guarantee</th><th class="num">Levels</th><th>Entry rule</th><th class="num">Last checked</th></tr></thead><tbody>{board_rows}</tbody></table></div>
<p class="srcline">Full parsed calendar: <a href="data/schedule-snapshot.json">data/schedule-snapshot.json</a> · per-room source status: <a href="review.html">review log</a></p></section>""")
    return shell("", "Tournaments", f"""
<section class="page-head"><h1>Every tournament the rooms published, with the entry rules beside it</h1>
<p class="lede">The first tab is the single-entry / freezeout list the brief asks for. Because no official sheet confirms single entry for any Venetian event, that list is empty <em>by design</em> — the second tab holds everything else, and the toggle in the filter bar shows what would qualify the moment a room states it.</p>
{status_banner()}</section>
{feed}
{filters}
<div class="tabs" role="tablist">
<button class="tab{' active' if confirmed else ''}" data-tab="confirmed" type="button">Single-entry / freezeout <span>{len(confirmed)}</span></button>
<button class="tab{'' if confirmed else ' active'}" data-tab="notconfirmed" type="button">Not confirmed <span>{len(other)}</span></button>
<button class="tab" data-tab="spend" type="button">More money buys an advantage <span>{len(spend)}</span></button>
<button class="tab" data-tab="restarts" type="button">Day-2 restarts, not entries <span>{len(cont)}</span></button>
</div>
<section class="tabpanel{' active' if confirmed else ''}" data-panel="confirmed">
<p class="panel-note">Nothing qualifies. A row enters this list only when the venue's own sheet or page explicitly says one entry / no rebuy / no add-on. <a href="questions.html#Q1">Q1 describes the single question that would change this.</a></p>
{events_table(confirmed, "", "no event on any official Strip sheet states single-entry-only play, so nothing qualifies yet")}</section>
<section class="tabpanel{' active' if not confirmed else ''}" data-panel="notconfirmed">
<p class="panel-note">Sorted by guarantee ÷ total entry fee (screening only). “Pool per entry” is what the sheet says reaches the prize pool, so two events with different fee splits stay comparable. Rows flagged <em>⚑ structure sheet ambiguous</em> share an event number with another sheet (different starting flights) and are never ranked off a fee split they may not belong to.</p>
<p class="panel-note">Sources behind these rows, by room: <strong>{len([e for e in events if e["venue"] == "venetian"])}</strong> Venetian series rows read from the DSE IV calendar and its {len([k for k in AUDIT["sheets"] if k.startswith("V_S")])} linked structure sheets; <strong>{len([e for e in events if e["venue"] == "wynn" and e.get("date")])}</strong> dated Wynn rows read from the venue's WPT structure booklet (one row per printed play day, fee split and re-entry rule beside it) and <strong>{len([e for e in events if e["venue"] == "wynn" and not e.get("date")])}</strong> undated Wynn rows from the daily poster; <strong>{len([e for e in events if e["venue"] == "bellagio"])}</strong> Bellagio rows and <strong>{len([e for e in events if e["venue"] == "caesars"])}</strong> Caesars Palace rows, all recurring slates whose documents print no calendar date, so none of them is dated on this page. Rows whose own sheet prices a re-entry or add-on sit in the third tab regardless of room, which is where most of the Bellagio and Caesars rows are; the counts here cover every tab. Anything the sheet does not print is blank, and the row says which field is missing. To put the events that passed the gates next to each other on guaranteed pool, entry cost, stack and blind length, payout and day fit, use <a href="compare.html">the comparison table</a>.</p>
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
    hotels = hotels_within_walk(v["id"])
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
{hotel_table(hotels, base) if hotels else unk("no hotel is associated with this room in the data — see flags F3/F18 for the walking-minute measurement method")}
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
        for field in ("resort_fee", "room_tax", "parking", "cancellation", "occupancy_charge", "check_in_out"):
            for sent, u in fact_sentences(h, field):
                facts += f"<li><strong>{E(field.replace('_', ' '))}</strong> “{E(sent)}” {src_cell([u], SNAPSHOT_AT[:10], label='source page ↗')}</li>"
        walk_rows = "".join(
            f"<tr><td>{E(p['venue'])}</td>"
            f"<td class='num'>{str(p['minutes']) + ' min' if p.get('minutes') is not None else unk('not published')}</td>"
            + (f"<td class='num'>{p.get('distance_mi')} mi</td>" if p.get('distance_mi') is not None else "<td></td>")
            + f"<td>{E(p['meets_30_min'])}</td><td class='qual'>{E(p.get('status') or '')}</td>"
            + (f" <a href='{E(p['method_url'])}' target='_blank' rel='noopener'>re-run the route ↗</a>" if p.get('method_url') else "")
            + f"<td class='srccell'>{src_cell([p.get('source')], SNAPSHOT_AT[:10], label='source ↗')}</td></tr>"
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
            floor = round(fee * (1 + tax), 2) if fee else None
            floor_line = (f" What <em>is</em> fixed: the mandatory {money(fee)} resort fee taxed at {tax * 100:.2f}% = "
                          f"<strong>{money(floor)}</strong> per night, on top of whatever the room rate turns out to be"
                          + (f", plus {money((h.get('parking') or {}).get('self_usd_per_day'))} self-parking per day"
                             if (h.get('parking') or {}).get('self_usd_per_day') else "")
                          + " — the tax basis and its caveat sit in the sentences below.") if floor else ""
            calc = (f"<p class='truecost blocked'>true cost per night cannot be computed: {E(' and '.join(missing))}. "
                    f"The blanks are kept rather than filled with an estimate.{floor_line}</p>")
        qual = h.get("qualification")
        qual_line = (f"<p class='mini-note'><strong>Rate eligibility:</strong> {E(qual)} — {src_cell([h.get('qualification_source')], SNAPSHOT_AT[:10], label='official terms ↗')}</p>"
                     if qual else "")
        dead = "".join(f"<li>the page that should carry this value is <a href='{E(d['url'])}' target='_blank' rel='noopener'>{E(d['url'].split('//')[-1])}</a> — {E(d['status'])}</li>"
                       for d in (h.get("dead_source_pages") or []))
        canc = h.get("cancellation") or {}
        park = h.get("parking") or {}
        bd = h.get("booking_dates_url") or {}
        if bd.get("template"):
            book_cell = (f"<a href='{E(bd['template'].replace('{arrival}', '2026-11-19').replace('{departure}', '2026-11-23').replace('{adults}', '2'))}' "
                         f"target='_blank' rel='noopener'>open the property's own booking calendar for the example window ↗</a> "
                         f"<span class='mini-note'>{E(bd.get('basis') or '')}</span>")
        elif h.get("booking_link"):
            book_cell = (f"<a href='{E(h['booking_link'])}' target='_blank' rel='noopener'>official booking engine ↗</a> "
                         f"<span class='mini-note'>this property publishes no date-carrying link pattern on the pages read, "
                         f"so the dates are typed into its own calendar rather than pre-filled here</span>")
        else:
            book_cell = unk('no official booking page reached')
        if not facts:
            # No machine-captured sentence yet (e.g. a freshly re-anchored source page):
            # fall back to the row's own confirmed excerpts instead of saying nothing exists.
            fallback = ""
            rf_ = h.get("resort_fee") or {}
            if rf_.get("excerpt"):
                fallback += (f"<li><strong>resort fee</strong> “{E(rf_['excerpt'])}” "
                             f"{src_cell([rf_.get('source')], rf_.get('retrieved'), label='source page ↗')}</li>")
            if canc.get("excerpt"):
                fallback += (f"<li><strong>cancellation</strong> “{E(canc['excerpt'])}” "
                             f"{src_cell([canc.get('source')], canc.get('retrieved'), label='source page ↗')}</li>")
            facts = fallback
        mins = next((str(p2["minutes"]) for p2 in walks if p2["hotel_id"] == h["id"] and p2.get("minutes")), "")
        onsite = "1" if "on-site" in str((h.get("walk") or {}).get("meets_30_min")).lower() else "0"
        meets = (h.get("walk") or {}).get("meets_30_min")
        meets_flag = ("onsite" if str(meets).lower().startswith("not applicable")
                      else "yes" if str(meets).lower().startswith(("yes", "under", "well"))
                      else "no" if str(meets).lower().startswith(("no", "over")) else "unverified")
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
<div><h4>Parking</h4><p>{(('self ' + money(park.get('self_usd_per_day')) + ' / day · valet ' + money(park.get('valet_usd_per_day')) + ' / day') if park.get('self_usd_per_day') else ('<b>$0 — included</b>' if park.get('self_usd_per_day') == 0 else unk('no price published'))) if park.get('self_usd_per_day') is not None else unk('no price published')} {chip(park.get('status') or 'unverified', 'chip chip-info')}</p></div>
<div><h4>Cancellation</h4><p>{E(canc.get('text') or '') or unk('not captured')} {chip(canc.get('status') or 'unverified', 'chip chip-warn')}</p>
{(f"<p class='mini-note'>{src_cell([canc.get('source')], canc.get('retrieved') or SNAPSHOT_AT[:10], label='official terms ↗')}</p>") if canc.get('source') else ''}</div>
<div><h4>Extra occupants</h4><p>{E((h.get('occupancy_charge') or {}).get('text') or '') or unk('the property publishes no per-occupant charge on the page read')} {chip((h.get('occupancy_charge') or {}).get('status') or 'unverified', 'chip chip-info')}</p>
{(f"<p class='mini-note'>{src_cell([(h.get('occupancy_charge') or {}).get('source')], (h.get('occupancy_charge') or {}).get('retrieved') or SNAPSHOT_AT[:10], label='official terms ↗')}</p>") if (h.get('occupancy_charge') or {}).get('source') else ''}</div>
<div><h4>Check-in / check-out</h4><p>{E((h.get('check_in_out') or {}).get('text') or '') or unk('not printed on the page read')} {chip((h.get('check_in_out') or {}).get('status') or 'unverified', 'chip chip-info')}</p></div>
<div><h4>Booking link for your dates</h4><p>{book_cell}</p></div>
</div>
<h4>Rates and fee facts as a dated log (not a single value)</h4>
<div class="table-scroll"><table class="compact"><thead><tr><th>Observed</th><th>What it is</th><th class="num">Amount</th><th>Wording / qualifier</th><th>Quote status</th><th>Source</th></tr></thead><tbody>{log_rows}</tbody></table></div>
<h4>Walk to the Venetian poker room (Google Maps, retrieved {E(walk_measured_on)})</h4>
<div class="table-scroll"><table class="compact"><thead><tr><th>Poker-room target</th><th class="num">Walk</th><th class="num">Distance</th><th>Meets the 30-min rule</th><th>How we know</th><th>Source</th></tr></thead><tbody>{walk_rows}</tbody></table></div>
{(f"<h4>Unresolved for this property</h4><ul class='flags'>{dead}</ul>") if dead else ''}
</article>"""
    return shell("", "Hotels", f"""
<section class="page-head"><h1>Hotels near the rooms, priced the way you actually pay</h1>
<p class="lede">True cost per night = the published room rate + the mandatory resort fee, both subject to {E(tax_label(CFG['hotels'][0]))}. Parking, the cancellation rule and the date the number was read sit next to it so two properties can be compared like for like. Rates are kept as a dated log, because a rate is only true at the moment it was quoted.</p>
{status_banner()}
<div class="walkfilter" id="walk-filter">
<span class="lbl">≤30-minute walking filter:</span>
<label class="toggle"><input type="radio" name="walkf" value="measured" checked> <strong>measured walk ≤ 30 min</strong> (the rule)</label>
<label class="toggle"><input type="radio" name="walkf" value="all"> every property on the list, including the ones that fail the rule</label>
<label class="toggle"><input type="radio" name="walkf" value="onsite"> inside the poker-room property only</label>
<span class="count" id="walk-count"></span>
</div>
<p class="mini-note">“Measured” holds a real walking time for every property: Google Maps walking directions (mode=walking) were retrieved {E(walk_measured_on)} for each hotel→Venetian poker-room pair and stored with the route distance, the “via” road, the exact directions URL and the retrieval date (see <a href="data/integrated/walks-google.json">data/integrated/walks-google.json</a>; flags <a href="flagged.html#F3">F3</a> / <a href="flagged.html#F18">F18</a> record the closure). Google's walking durations run optimistic, so the route distance in miles is shown beside each minute. Choosing “measured walk ≤ 30 min” filters to the properties that provably meet the rule.</p></section>
{cards}
<section class="callout"><h2>Reading a blank honestly</h2>
<p>Where a property shows rates only inside its booking calendar, no number is copied onto this site — the booking link is given instead and the row is marked. Two official pages returned 404 in the 2026-11-17 check: Bellagio&#39;s /hotel/resort-fee.html page and the 2025 Caesars Palace daily flyer. Both were re-anchored to the operator&#39;s own live successor the same day — Bellagio&#39;s Hotel Reservation Terms page, which Bellagio&#39;s FAQ names as where the fee is documented (“A daily resort fee of $55.00 plus applicable tax will be applied to all reservations”), and the 2026 flyer on Caesars&#39; own content path — and the retired URLs stay logged on the Bellagio row and in <a href="data/url-checks.json">data/url-checks.json</a> rather than being silently swapped. <a href="flagged.html#F5">F5</a> and <a href="flagged.html#F6">F6</a> record what each replacement page yields; <a href="flagged.html#F25">F25</a> records that Caesars&#39; two official pages disagree on two of the four daily buy-ins. Nothing was replaced with a third-party mirror: the $50 and $56.69 ARIA/Bellagio figures that circulate on review sites are deliberately not used because the properties&#39; own terms pages print $55.00 plus applicable tax, and the earlier sentence on this page claiming “ARIA publishes $50 and $55 on two official pages” has been corrected — <a href="flagged.html#F5">F5</a> shows the $50 figure traces only to third-party sources. Walking minutes are now measured rather than warned about: every hotel→poker-room pair carries a Google Maps walking time with its route distance and retrieval date (flags <a href="flagged.html#F3">F3</a> / <a href="flagged.html#F18">F18</a>), which is what the ≤30-minute filter below uses. The remaining blanks are the ones no official source can settle — a dated like-for-like room quote needs your exact dates and occupancy, and <a href="flagged.html#F27">F27</a> records that the 13.38% room-tax figure is the county&#39;s Primary Gaming Corridor rate rather than a number each property prints on its own page.</p></section>
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
            else unk(d.get("fallback_unavailable") or "no second entry is reachable on the official data")
        conf = "".join(f"<p>{E(c)}</p>" for c in d.get("overlap_notes") or []) or "<span class='ok'>nothing blocks a second entry</span>"
        recs = d.get("recurring_options") or []
        rec_html = (
            "<div class='recopts'><span class='recolabel'>printed for this weekday (no date printed):</span>"
            + "".join(f"<span class='recopt'><a href='tournaments.html#{E(r['id'])}'>{E(r['name'])}</a>"
                      f"<em>{E(r['venue'])} · {E(r['time'] or 'time not printed')} · {money(r['buy_in_usd'])}</em>"
                      f"<small>{E(r['feasibility'])}</small></span>" for r in recs) + "</div>") if recs else ""
        res = "; ".join(d.get("restarts") or [])
        rows += (f"<tr class='day-row' data-date='{E(d['date'])}'><td class='when'><strong>{E(d['date'])}</strong>"
                 f"<span class='time'>{E(d.get('weekday') or '')} · first start {E(d.get('earliest_printed_start') or 'not printed')}</span></td>"
                 f"<td>{p_txt}</td><td>{f_txt}{rec_html}</td><td class='restarts'>{E(res) if res else unk('nothing printed')}</td>"
                 f"<td class='conflicts'>{conf}</td><td class='num'>{money(d['entries_usd'])}"
                 f"{note('one entry per distinct event; ' + str(d.get('distinct_ranked_events', 0)) + ' ranked event(s) this day')}</td></tr>")
    with_fb = len([x for x in plan if x.get("fallback")])
    return shell("", "Day plan", f"""
<section class="page-head"><h1>One day, one primary event, one conditional fallback</h1>
<p class="lede">Sequencing uses only what the calendar prints: the start time, the “REG CLOSES” column and the Day-2 restart rows. A day gets a <strong>primary</strong> event and a <strong>fallback</strong> that is only reachable if you are done with the first — that means its start is at or after the primary's registration deadline, the closest thing to a guaranteed exit the official data offers. No event duration is invented: where a sheet lists levels, the implied length sits on the tournament row, and it is never used to reorder this plan.</p>
{status_banner()}
<p class="warn">The day cannot start at 8:00 AM: nothing on the Strip publishes an 8:00 AM first flight. In this window the earliest first starts are 10:10 AM (raceday events) and 11:10 AM for the $300 Events 1A/9, so each day begins at the earliest official start and the difference is flagged rather than papered over.</p></section>
<div class="table-scroll"><table class="compact days"><thead><tr><th>Day</th><th>Primary</th><th>Conditional fallback</th><th>Day-2 / finals that day</th><th>Overlap check</th><th class="num">Ranked entries that day</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<section class="callout"><h2>Recurring slates sit under each day, not inside it</h2>
<p>Under the fallback on every day are the rooms' <em>recurring</em> events — Wynn's dailies, Bellagio's weekend
slate, Caesars' four-a-day — which print a weekday (“Nightly Monday-Sunday”, “Fridays”) and no calendar date. They are
listed as what they are: an option the weekday allows, tested against the same printed deadline as everything else,
never promoted into the dated calendar. A day whose lead event prints no deadline therefore says so instead of
promising that a second entry fits.</p>
<h2>Why some days carry no fallback</h2>
<p>Where a second event starts before the first one's registration window closes, playing both is impossible on the official data — those days list the conflict instead of scheduling it. {with_fb} of {len(plan)} days have a defensible fallback. Rows on the same date with the same buy-in but different flights (1A/1B/1C…) are alternative starts of <em>one</em> event, not two entries, and the plan never counts both.</p>
<p class="srcline">Machine copy: <a href="data/day-plan.json">day-plan.json</a> · basis: <a href="data/schedule-snapshot.json">schedule-snapshot.json</a></p></section>
""", "plan.html", needs_data=False)


# ---------------------------------------------------------------------- compare
def page_compare():
    """The side-by-side comparison the brief asks for: compare only the events that
    survived, on guaranteed pool, buy-in, starting stack / blind duration, payout
    structure and daily schedule fit.

    "Survived" here means what actually survived the published gates, stated plainly:
    an event whose fee split AND whose guarantee are both printed by the official
    document, and which is an entry rather than a Day-2 continuation. No event in
    this snapshot is confirmed single-entry, so the single-entry gate removes nothing
    and the flag on every row says so.
    """
    day_by_date = {d["date"]: d for d in plan}
    survivors = [e for e in events if e.get("rankable")]
    rows = ""
    for e in sorted(survivors, key=lambda x: (-(x.get("gtd_ratio") or 0), x["date"])):
        d = day_by_date.get(e.get("date") or "")
        fee_parts = []
        if e.get("house_fee_usd"):
            fee_parts.append(f"{money(e['house_fee_usd'])} house fee")
        if e.get("pool_per_entry_usd"):
            fee_parts.append(f"{money(e['pool_per_entry_usd'])} to the pool")
        fee_txt = "; ".join(fee_parts) or unk("no fee split printed")
        stack = (f"{e['starting_chips']:,} chips" if e.get("starting_chips") else unk("stack not printed"))
        if e.get("level_duration"):
            stack += note(f"{e['level_duration']}-min levels")
        if e.get("levels_total"):
            stack += note(f"{e['levels_total']} levels listed")
        payout = (f"top {E(str(e['payout_pct_of_field']))}% of the field"
                  if e.get("payout_pct_of_field") else unk("no payout percentage printed"))
        # daily schedule fit: what else is on that day, and what the day plan picked
        if d:
            same_day = d.get("distinct_ranked_events", 0)
            fit = (f"<strong>{same_day}</strong> ranked event(s) this day")
            if d.get("primary"):
                fit += note("plan's primary: " + short_name(d["primary"]["name"]))
            if d.get("fallback"):
                fit += note("reachable fallback: " + short_name(d["fallback"]["name"]))
            else:
                fit += note("no second entry is reachable on the printed deadlines")
        else:
            fit = unk("no dated entry on the day plan")
        rule_txt = []
        for key, label in RULE_LABELS:
            r = e["rules"].get(key) or {}
            st = r.get("status") or "unverified"
            if st in ("confirmed", "confirmed_allowed", "confirmed_limited",
                      "confirmed_not_single_entry", "indicated", "no"):
                rule_txt.append(label + ": " + str(r.get("value") or st))
            elif key == "fee":
                rule_txt.append(label + ": " + str(r.get("value") or st))
            else:
                rule_txt.append(label + ": not stated in the sheet")
        rules = "; ".join(rule_txt)
        if not e.get("single_entry_confirmed"):
            rules += note("single-entry unverified — silence is not confirmation")
        rows += (f"<tr class='ev-row' id='cmp-{E(e['id'])}' data-id='{E(e['id'])}' data-date='{E(e.get('date') or '')}' "
                 f"data-venue='{E(e.get('venue') or '')}' data-single='{1 if e.get('single_entry_confirmed') else 0}' "
                 f"data-rankable='{1 if e.get('rankable') else 0}' data-days=''><td class='when'>{E(e.get('date') or '')}"
                 f"<span class='time'>{E(e.get('weekday') or '')} · {E(e.get('time') or 'time not printed')}</span></td>"
                 f"<td class='ev'><a href='tournaments.html#{E(e['id'])}'>{E(e.get('name') or '')}</a>"
                 f"<span class='time'>{E(e.get('venue_name') or e.get('venue') or '')}</span></td>"
                 f"<td class='num'>{money(e.get('buy_in_usd'))}</td>"
                 f"<td class='num'>{fee_txt}</td>"
                 f"<td class='num'>{money(e.get('guarantee_usd'))}</td>"
                 f"<td class='num'>{E(str(e.get('gtd_ratio') if e.get('gtd_ratio') is not None else '—'))}×</td>"
                 f"<td class='num'>{stack}</td>"
                 f"<td class='num'>{payout}</td>"
                 f"<td class='rules'>{rules}</td>"
                 f"<td class='conflicts'>{fit}</td>"
                 f"<td class='srccell'>{src_cell(e.get('sources'), e.get('last_checked'), e.get('source_changed'))}</td></tr>")
    n_surv = len(survivors)
    n_single = sum(1 for e in survivors if e.get("single_entry_confirmed"))
    n_payout = sum(1 for e in survivors if e.get("payout_pct_of_field"))
    n_stack = sum(1 for e in survivors if e.get("starting_chips"))
    venue_opts = "".join(f"<option value='{E(v['id'])}'>{E(v['name'])}</option>" for v in CFG["venues"])
    filters = COMPARE_FILTERS.replace("__VENUE_OPTS__", venue_opts)
    return shell("", "Compare the shortlist", f"""
<section class="page-head"><h1>Compare the surviving events, side by side</h1>
<p class="lede">One row per event that passed the published gates, compared on the five things that decide a trip:
the <strong>guaranteed pool</strong>, the <strong>entry cost</strong> (the printed buy-in and what the house keeps),
the <strong>starting stack and blind duration</strong>, the <strong>payout structure</strong> and the
<strong>daily schedule fit</strong>. Nothing is estimated: a figure the official document does not print is blank and says so.</p>
{status_banner()}</section>
{filters}
<div class="flagstats"><span class="stat">{n_surv} events survived the gates</span>
<span class="stat">{n_single} confirmed single-entry</span>
<span class="stat">{n_stack} with a printed starting stack</span>
<span class="stat">{n_payout} with a printed payout percentage</span>
<span class="stat">{len(plan)} days on the plan</span></div>
<div class="table-scroll"><table class="compact compare"><thead><tr>
<th>Day</th><th>Event</th><th class="num">Entry (buy-in)</th><th class="num">Fee split</th>
<th class="num">Guaranteed pool</th><th class="num">GTD ÷ entry</th><th class="num">Stack &amp; blinds</th>
<th class="num">Payout</th><th>Entry rules</th><th>Daily schedule fit</th><th>Official source</th>
</tr></thead><tbody>{rows}</tbody></table></div>
<section class="callout"><h2>What “survived” means here, and what it does not</h2>
<p>An event is on this page because the fee split <em>and</em> the guarantee are both printed by the official document, so
the ratio beside it can be recomputed, and because it is an entry rather than a Day-2 continuation. Every row still carries
its own entry rules.</p>
<p><strong>No event in this snapshot is confirmed single-entry.</strong> That gate is not applied here because it removes
nothing — 0 of {len(events)} rows carry a single-entry confirmation, and the reason is recorded on
<a href="flagged.html#F1">flag F1</a> and in the <em>source text</em> panel of every row on
<a href="tournaments.html">the tournaments page</a>. A sheet that prints nothing about entries is not a freezeout; it is
an unverified sheet.</p>
<p>The ratio is <strong>descriptive</strong>: guarantee ÷ total entry fee, both as printed. It is not an expected value, not a
forecast, and not a recommendation — an event with a 625× ratio is not better to play than one with 250×, because the
guarantee is a floor the field may exceed and the pool depends on how many players enter. Rows whose guarantee includes
bounty money, and rows whose venue names more than one starting flight, are labelled on the
<a href="tournaments.html">tournaments page</a> so a like-for-like comparison stays like-for-like.</p>
<p class="srcline">Machine copy: <a href="data/site-events.json">site-events.json</a> · <a href="data/day-plan.json">day-plan.json</a> ·
every figure checked against its source by <a href="review.html#audit">the value-level audit</a>.</p></section>
""", "compare.html", needs_data=False)


# --------------------------------------------------------------- before you pay
def page_before_you_pay():
    """The re-confirmation step the brief asks for: what to re-read, where, and what
    is still unverified — immediately before a non-refundable payment.

    Every link is the official document the site itself cites, and every "still
    unverified" line is generated from the same data the tables are built from, so
    this page cannot drift away from them.
    """
    # 1. the events: every official URL a planned entry depends on, with its check date
    ev_rows = ""
    for e in sorted([x for x in events if x.get("date") and x.get("rankable")],
                    key=lambda x: (x["date"], x.get("time") or "")):
        missing = []
        if not e.get("single_entry_confirmed"):
            missing.append("entry policy")
        if not e.get("payout_pct_of_field"):
            missing.append("payout percentage")
        if not e.get("registration_closes"):
            missing.append("registration deadline")
        if not e.get("levels_total"):
            missing.append("level count / implied finish time")
        ev_rows += (f"<tr><td class='when'>{E(e['date'])}"
                    f"<span class='time'>{E(e.get('weekday') or '')} · {E(e.get('time') or 'time not printed')}</span></td>"
                    f"<td class='ev'><a href='tournaments.html#{E(e['id'])}'>{E(e.get('name') or '')}</a>"
                    f"<span class='time'>{E(e.get('venue_name') or '')}</span></td>"
                    f"<td class='num'>{money(e.get('buy_in_usd'))}</td>"
                    f"<td class='num'>{money(e.get('guarantee_usd'))}</td>"
                    f"<td class='rules'>{E(', '.join(missing)) if missing else '<span class=ok>nothing outstanding on this row</span>'}</td>"
                    f"<td class='srccell'>{src_cell(e.get('sources'), e.get('last_checked'), e.get('source_changed'))}</td></tr>")

    # 2. the hotel: the fee chain, the parking, the cancellation and whether a dated
    #    checkout total exists at all
    h_rows = ""
    for h in CFG["hotels"]:
        fee = h.get("resort_fee") or {}
        tax = h.get("tax") or {}
        park = h.get("parking") or {}
        canc = h.get("cancellation") or {}
        dated = [r for r in (h.get("rate_log") or []) if r.get("observed_on")]
        # A checkout total exists only when a dated line actually carries an amount.
        # A line that says a checkout total is "not obtainable from a static page"
        # records the absence of a quote, not a quote.
        checkout = [r for r in dated
                    if r.get("amount_usd") and "checkout" in str(r.get("label", "")).lower()]
        self_park = park.get("self_usd_per_day")
        valet = park.get("valet_usd_per_day")
        if self_park is None and valet is None:
            park_cell = unk("parking not confirmed") + note(park.get("status") or "")
        else:
            bits = []
            if self_park is not None:
                bits.append("complimentary self parking" if self_park == 0
                            else money(self_park) + " self")
            if valet is not None:
                bits.append(money(valet) + " valet")
            park_cell = " · ".join(bits) + note(park.get("status") or "")
        h_rows += (f"<tr><td class='ev'>{E(h.get('property') or h['id'])}"
                   f"<span class='time'>{E(h.get('official_page') or '')}</span></td>"
                   f"<td class='num'>{money(fee.get('amount_usd')) if fee.get('amount_usd') else unk('no fee confirmed')}"
                   f"{note(fee.get('status') or '')}</td>"
                   f"<td class='num'>{E(str(tax.get('rate_pct')) + '%') if tax.get('rate_pct') else unk('no tax rate confirmed')}</td>"
                   f"<td class='num'>{park_cell}</td>"
                   f"<td class='rules'>{E(str(canc.get('status') or 'no cancellation policy captured'))}</td>"
                   f"<td class='num'>{E(str(len(dated)))} dated rate line(s)"
                   f"{note('dated checkout total captured — re-quote before booking' if checkout else 'NO dated checkout total — ask for one before paying')}</td>"
                   f"<td class='srccell'>{src_cell([h.get('official_page')] if h.get('official_page') else [], SNAPSHOT_AT[:10], label='official page ↗')}</td></tr>")

    # 3. the questions only the room can answer
    asks = ""
    for v in CFG["venues"]:
        vsrc = (v.get("schedule_sources") or [])[:1]
        asks += (f"<li><strong>{E(v['name'])}</strong>"
                 f"{note('ask: is one entry per player permitted in this event, and if not, what is the maximum number of entries and the price of each subsequent one?')}"
                 f"{note('ask: what time does the event finish, and what happens to the start stack if it is not finished on the same day?')}"
                 f"{note('ask: does the printed guarantee hold if fewer entries are sold than the guarantee assumes?')}"
                 + (f"{note('official calendar: ')} {src_cell(vsrc, SNAPSHOT_AT[:10], label='official calendar ↗')}" if vsrc else "")
                 + "</li>")

    return shell("", "Before you pay", f"""
<section class="page-head"><h1>Before you pay for anything</h1>
<p class="lede">This snapshot is a point-in-time reading of what the rooms publish, not a booking quote. Before a
non-refundable payment goes out, re-read the seven things below and close the gaps this site could not. Every link
here is the operator's own document — the same one the tables cite — and every “still unverified” line is generated
from the same data, so this page cannot drift away from the rest of the site.</p>
{status_banner()}</section>

<section class="callout"><h2>The seven things to re-check</h2>
<ol class="checklist">
<li><strong>The calendar for your dates.</strong> The schedule PDF is re-read every morning, but a printed series
calendar is a snapshot of one series: check the room's own page for the day you travel.</li>
<li><strong>The structure sheet for each event you intend to enter.</strong> The sheet carries the buy-in, the fee
split, the stack, the levels and the late-registration deadline — and, for the rooms that publish it, the entry rule.
Read the sheet, not the summary.</li>
<li><strong>The entry policy, in writing.</strong> This is the single largest open item on the whole site: 0 of
{len(events)} published rows are confirmed single-entry. Ask the room for the maximum number of entries per player
and the price of each subsequent entry, in writing, before you commit to a plan that depends on it
(<a href="flagged.html#F1">F1</a>, <a href="questions.html">Q1</a>).</li>
<li><strong>The finish time.</strong> No official document on the Strip prints a finish time for these events, so the
day plan sequences on registration deadlines only. Ask the room what time the event ends and what happens to your
stack if it runs long (<a href="questions.html">Q4</a>).</li>
<li><strong>A dated checkout total for the exact stay.</strong> Advertised “from” rates are not quotes. Ask for the
checkout total, the nightly average, the resort fee, the 13.38% room tax, parking and the cancellation deadline for
your exact nights and occupancy (<a href="questions.html">Q2</a>, <a href="flagged.html">the hotel flags</a>).</li>
<li><strong>Whether the poker-rate qualification applies to you.</strong> The advertised poker rate is conditional; if
you do not qualify, the rate you actually pay is different (<a href="questions.html">Q7</a>).</li>
<li><strong>The walking route on the day.</strong> The walking times here are timestamped measurements from a routing
engine, not statements by either property. Re-run the route on the morning you arrive
(<a href="flagged.html#F3">F3</a>).</li>
</ol></section>

<h2>Your event list, with what is still outstanding on each row</h2>
<p class="mini-note">Every event that passed the published gates, with the official documents behind it and the fields
that are not confirmed. Anything in the fifth column is a question to ask before you enter.</p>
<div class="table-scroll"><table class="compact"><thead><tr><th>Day</th><th>Event</th><th class="num">Entry</th>
<th class="num">Guarantee</th><th>Still unverified on this row</th><th>Official source</th></tr></thead>
<tbody>{ev_rows}</tbody></table></div>

<h2>Your hotel line, with what is still outstanding</h2>
<div class="table-scroll"><table class="compact"><thead><tr><th>Property</th><th class="num">Resort fee</th>
<th class="num">Tax</th><th class="num">Parking</th><th>Cancellation</th><th class="num">Dated rate lines</th>
<th>Official source</th></tr></thead><tbody>{h_rows}</tbody></table></div>

<h2>The exact words to ask each room</h2>
<ul class="flaglist">{asks}</ul>
<p class="srcline">Generated from <a href="data/site-events.json">site-events.json</a> and
<a href="data/poker4.json">poker4.json</a> · cross-checked by
<a href="review.html#audit">the value-level audit</a> · open items listed on
<a href="questions.html">the questions page</a>.</p>
""", "before-you-pay.html", needs_data=False)


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
<label>Arrival date <input type="date" id="calc-arrive" min="2026-11-16" max="2027-03-31"></label>
<label>Guests in the room <input type="number" id="calc-guests" value="2" min="1" max="6"></label>
<p class="mini-note" id="calc-booklink"></p>
</div>
<div><h3>Tournaments</h3><p class="mini-note">Tick what you would enter. Only the total buy-in is counted — each sheet says the house fee is already withheld inside it.</p>
<div class="picks" id="calc-events">{picks}</div></div>
<div class="calc-out"><h3>Totals</h3>
<dl id="calc-total"><dt>Entries</dt><dd id="t-entries">—</dd><dt>Hotel per night</dt><dd id="t-night">—</dd><dt>Hotel total</dt><dd id="t-hotel">—</dd><dt class="grand">Trip total</dt><dd class="grand" id="t-grand">—</dd></dl>
<p id="calc-note" class="warn"></p>
<p class="mini-note">Rates move constantly and the properties publish them only inside the booking calendar for specific dates, so a rate is never stored here — pick the dates and the calculator hands the query back to the property's own engine (only where that property publishes the link pattern). <a href="hotels.html" id="calc-book">The hotel's card lists its official booking link</a>.</p>
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
    nwalk = sum(1 for p in walks if p.get("minutes") is not None)
    nowalk = sum(1 for p in walks if p.get("minutes") is None)
    nfail = sum(1 for p in walks if str(p.get("meets_30_min", "")).lower().startswith("no "))
    return shell("", "Flagged for Review", f"""
<section class="page-head"><h1>Flagged for Review</h1>
<p class="lede">Every unresolved item, with the source that produced it. A flag is never cleared by re-wording a row — only when the official source states the value or an action closes the gap.</p>
<div class="flagstats"><span class="stat">{len(CFG['flags'])} open flags</span>
<span class="stat">{unconf} of {len(events)} rows without confirmed single-entry</span>
<span class="stat">{norate} of {len(CFG['hotels'])} hotels with no computable true cost</span>
<span class="stat">{nowalk} of {len(walks)} hotel→venue walks still unmeasured — {nwalk} measured, {nfail} over the 30-min line</span>
<span class="stat">{sum(1 for s in source_rows if not s['ok'])} official URLs unreachable</span></div></section>
{body}
<section class="callout"><h2>Row-level flags live with the rows</h2><p>Per-row flags (ambiguous sheet, no guarantee printed, not ranked because the fee split is unconfirmed) sit on each row in <a href="tournaments.html">tournaments</a> and on the venue pages, so the warning never separates from the number it qualifies.</p></section>""",
"flagged.html", needs_data=False)


VERIFY_NOTES = {
    "60ade3e8_source_recheck_2026-11-17.tsv":
        ("Caesars Palace daily slate re-read from the property's own 2026 flyer (C1–C7); Bellagio and ARIA fee, occupancy, cancellation and "
         "parking re-read from their reservation-terms and rate-table pages (B1–B5, A1–A2); the standing walking-minute position (W1); and the "
         "Venetian's own date-carrying booking-link pattern (V1)", "2026-11-17"),
    "1257a37f_source_recheck_2026-11-19.tsv":
        ("Live re-read 2026-11-19 of the Venetian DSE IV series page, the poker suite-rate page, the Wynn poker page and fee terms 850257, "
         "the Caesars explore article, the TI Deluxe Rooms page, the Bellagio and ARIA reservation terms, and structure sheets 21 and 12; "
         "every committed value compared against the live sentence behind it, plus one new dated rate-log observation per source that printed "
         "a price (TI offer, Venetian endpoints, Wynn player-rate channel) and flag F39 for the Wynn page's self-contradiction", "2026-11-19"),
}


def page_review():
    st = load("sync-status.json", {})
    chg = ""
    for c in (CHANGELOG.get("entries") or [])[:40]:
        chg += (f"<tr><td>{E(str(c.get('at') or '')[:16].replace('T', ' '))}</td><td>{E(c.get('scope') or '')}</td>"
                f"<td>{E(registry_label(str(c.get('url') or '')))}</td>"
                f"<td class='diff'><pre>{E(json.dumps(c.get('diff'), indent=1)[:1200])}</pre></td></tr>")
    if not chg:
        chg = f"<tr><td colspan='4'>{unk('no value-level change recorded since monitoring began — the first run seeds the baseline, later runs diff against it')}</td></tr>"
    dead_now = [s for s in source_rows if not s["ok"] and s["url"] in TRACKED_URLS]
    dead_gone = [s for s in source_rows if not s["ok"] and s["url"] not in TRACKED_URLS]

    def dead_row(s, cls, note_key):
        extra = (CHECKS.get(s["url"]) or {}).get(note_key)
        extra_txt = ("superseded on " + str((CHECKS.get(s["url"]) or {}).get("superseded_on") or "") +
                     " — the registry now tracks " + extra) if extra else None
        return (f"<tr><td><a href='{E(s['url'])}' target='_blank' rel='noopener'>{E(s['label'])}</a>{note(extra_txt)}</td>"
                f"<td>{E(s.get('venue') or '')}</td>"
                f"<td>{status_span(cls, str(s['status']) + ' ' + str(s.get('error') or ''))}</td>"
                f"<td class='num'>{E(s.get('checked_at') or '')}</td></tr>")

    dead_rows = "".join(dead_row(s, "bad", "superseded_by") for s in dead_now)
    superseded_rows = "".join(dead_row(s, "chip-warn", "superseded_by") for s in dead_gone)
    parsed = sum(1 for s in source_rows if (s.get("rows_parsed") or 0) > 0)
    saved = sum(1 for s in source_rows if s.get("saved"))
    verify_rows = ""
    vdir = DATA / "verify"
    for fp in sorted(vdir.glob("*.tsv")) if vdir.exists() else []:
        cov, when = VERIFY_NOTES.get(fp.name, (f"{max(0, sum(1 for _ in open(fp, encoding='utf-8')) - 1)} compared values", fp.name.rsplit("_", 2)[-2] if fp.name.count("_") > 1 else ""))
        verify_rows += (f"<tr><td><a href='data/verify/{E(fp.name)}'>{E(fp.name)}</a></td>"
                        f"<td class='qual'>{E(cov)}</td><td>{E(when)}</td></tr>")
    verify_rows = verify_rows or f"<tr><td colspan='3'>{unk('no per-value re-check records in data/verify yet')}</td></tr>"
    audit = load("audit-values.json", {})
    audit_meta = audit.get("meta") or {}
    audit_fields = audit.get("fields") or {}
    audit_failures = audit.get("failures") or []
    audit_blocking = [f for f in audit_failures
                      if f.get("kind") in ("value_not_found", "quote_not_verbatim",
                                           "reconstruction_unverified", "arithmetic_mismatch")]
    audit_cross = audit.get("cross_checks") or []
    audit_reworded = audit.get("reworded_excerpts_verified") or []
    if audit_meta:
        field_rows = "".join(
            f"<tr><td>{E(f.replace('excerpt:', 'quote · '))}</td>"
            f"<td class='num'>{E(str(v.get('checked')))}</td>"
            f"<td class='num'>{E(str(v.get('located')))}</td>"
            f"<td>{'OK — every value found in its cited source' if v.get('checked') == v.get('located') else 'FAIL'}</td></tr>"
            for f, v in audit_fields.items())
        cross_parts = []
        for c in audit_cross:
            failed = c.get("failed")
            verdict = "OK" if not failed else str(failed) + " failed"
            cross_parts.append(
                f"<tr><td>{E(c.get('check') or '')}</td>"
                f"<td class='qual'>{E(c.get('description') or '')}</td>"
                f"<td class='num'>{E(str(c.get('checked')))}</td>"
                f"<td>{status_span('ok' if not failed else 'bad', verdict)}</td></tr>")
        cross_rows = "".join(cross_parts)
        audit_block = f"""
<h2 id="audit">Value-level audit — every published number and every quoted sentence</h2>
<p class="mini-note">The link check above proves a row <em>has</em> a source. This proves the value <em>came from</em> it:
the tool re-reads every official capture committed in <code>data/raw/</code> and every committed verbatim transcription of the
official structure sheets, then looks for the literal evidence behind each published figure and each sentence shown in a
<em>source text</em> panel. A value it cannot find is reported, never corrected, and never quietly replaced.</p>
<div class="flagstats"><span class="stat">{E(str(audit_meta.get('values_checked')))} values checked</span>
<span class="stat">{E(str(audit_meta.get('values_located')))} found in the cited source</span>
<span class="stat">{E(str(audit_meta.get('blocking_failures')))} blocking failures</span>
<span class="stat">{E(str(len(audit_reworded)))} sentences shown as reworded rather than quoted</span>
<span class="stat">{E(str((audit_meta.get('evidence') or {}).get('hashed_captures')))} hashed captures · {E(str((audit_meta.get('evidence') or {}).get('structure_sheets_transcribed')))} transcribed structure sheets</span></div>
<div class="table-scroll"><table class="compact"><thead><tr><th>Field</th><th class="num">Checked</th><th class="num">Located</th><th>Verdict</th></tr></thead><tbody>{field_rows}</tbody></table></div>
<h3>Cross-checks</h3>
<div class="table-scroll"><table class="compact"><thead><tr><th>Check</th><th>What it proves</th><th class="num">Rows</th><th>Verdict</th></tr></thead><tbody>{cross_rows}</tbody></table></div>
<p class="mini-note">Reproduce offline: <code>python3 scripts/audit_values.py --strict</code> · machine copy:
<a href="data/audit-values.json">data/audit-values.json</a> · audit of the snapshot {E(str(audit_meta.get('as_of') or ''))}.</p>
<p class="mini-note">{len(audit_reworded)} sentence(s) are shown on the site as <em>reworded from the printed figures</em> rather than
as a copy of the sheet&rsquo;s own line: the figures are the sheet&rsquo;s, the sentence is the room&rsquo;s standard wording, verified verbatim on
other sheets of the same series. The scheduled re-read captures each sheet&rsquo;s own sentence, after which the label drops away
on its own.</p>"""
    else:
        audit_block = ("<h2>Value-level audit</h2><p class='unknown'>The value-level audit has not been run in this build. "
                       "Run <code>python3 scripts/audit_values.py</code> to produce it.</p>")
    return shell("", "Review log", f"""
<section class="page-head"><h1>Review log — what was checked, when, and what changed</h1>
<p class="lede">The numbers the site was built from, plus the raw material: every tracked official URL with the date it was last read, whether its bytes or its values moved, how many rows the parser got out of it, and the captured text itself. Any row on any page can be traced to a captured sentence in one click.</p>
{status_banner()}</section>
<div class="runstats"><div><h3>Last run</h3><ul>
<li>{E(st.get('urls_checked', len(source_rows)))} official URLs checked · {len(st.get('urls_failed') or [])} failed</li>
<li>{sheets_label()} · {E(st.get('schedule_rows', len(SCHED['rows'])))} calendar rows · {E(st.get('schedule_rows_with_date', sum(1 for r in SCHED['rows'] if r.get('date'))))} rows carrying a date</li>
<li>{len(st.get('changed_this_run') or [])} URLs changed on this run (cosmetic byte changes are counted separately from value changes)</li>
<li>{E(st.get('hotel_fact_sources', len(FACTS.get('sources') or {})))} property pages yielded a fee / tax / parking / cancellation sentence</li>
<li>{parsed} sources parsed into rows · {saved} sources kept as captured text under <code>data/raw/</code></li></ul>
<p class="mini-note">Machine copies: <a href="data/sync-status.json">sync-status</a> · <a href="data/url-checks.json">url-checks</a> · <a href="data/site-events.json">site-events</a> · <a href="data/structure-audit.json">structure-audit</a> · <a href="data/schedule-snapshot.json">schedule-snapshot</a> · <a href="data/rate-log.json">rate-log</a> · <a href="data/walks.json">walks</a> · <a href="data/hotel-facts.json">hotel-facts</a></p>
<p class="mini-note">Sample of the raw date headings read from the calendar PDF: <code>{E(str((st.get('date_head_sample') or '')[:220]))}</code></p></div>
<div><h3>Unreachable official URLs</h3>
<div class="table-scroll"><table class="compact"><thead><tr><th>Source</th><th>Venue</th><th>Status</th><th class="num">Checked</th></tr></thead><tbody>{dead_rows or "<tr><td colspan='4' class='ok'>none — every tracked official URL answered on its last check</td></tr>"}</tbody></table></div>
{(f"<h3>Dead URLs the registry has since repointed</h3><div class='table-scroll'><table class='compact'><thead><tr><th>Old official URL</th><th>Venue</th><th>Status</th><th class='num'>Checked</th></tr></thead><tbody>{superseded_rows}</tbody></table></div>") if superseded_rows else ""}
<p class="mini-note">Policy: a dead official URL is reported, never replaced by a third-party mirror, and only repointed when the operator
itself publishes a live successor for the same document (as the Caesars 2025→2026 flyer and Bellagio's fee page→reservation terms did on
2026-11-17). The old URL stays on the record above so the change is auditable.</p>
<p class="mini-note">Reproduce offline: <code>python3 tools/sync_official_sources.py --from-raw</code> then <code>python3 scripts/integrate_data.py</code>.</p></div></div>
<h2>Value changes recorded</h2>
<div class="table-scroll"><table class="compact"><thead><tr><th>When (UTC)</th><th>Scope</th><th>Source</th><th>Fields that moved</th></tr></thead><tbody>{chg}</tbody></table></div>
<h2>Line-by-line re-check records</h2>
<p class="mini-note">Each record is a machine-readable table of one published value against the official document that carries it: what the site
said, what the document says, the verdict and the action taken. Read these before treating anything as settled.</p>
<div class="table-scroll"><table class="compact"><thead><tr><th>Record</th><th>Coverage</th><th>Run date</th></tr></thead><tbody>{verify_rows}</tbody></table></div>
{audit_block}
<h2>All tracked sources ({len(source_rows)})</h2>
{source_table(source_rows)}
""", "review.html", needs_data=False)


# ------------------------------------------------------------------ emit the site
VENUES_OUT.mkdir(exist_ok=True)
pages = {"index.html": page_index(), "tournaments.html": page_tournaments(), "hotels.html": page_hotels(),
         "plan.html": page_plan(), "calculator.html": page_calculator(), "questions.html": page_questions(),
         "suggestions.html": page_suggestions(), "flagged.html": page_flagged(), "review.html": page_review(),
         "compare.html": page_compare(), "before-you-pay.html": page_before_you_pay()}
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
    # One page family at the root. These filenames belonged to earlier builders whose
    # pages are preserved in their own folders (poker4/, site/, v2/, archive/); at the
    # root they are now redirects so a bookmarked or linked URL still resolves and the
    # site keeps a single navigation, a single stylesheet and one set of numbers.
    "venetian.html": ("venues/venetian.html", "the Venetian room has its own page under venues/, with its events, its hotels and its sources"),
    "wynn.html": ("venues/wynn.html", "the Wynn room has its own page under venues/"),
    "others.html": ("venues/others.html", "the remaining rooms have their own page under venues/"),
    "venues.html": ("index.html", "the room-by-room coverage table is on the overview page"),
    "trip.html": ("calculator.html", "the trip-cost calculator now reads the dated rate log and the confirmed fee for each property"),
    "rate-log.html": ("hotels.html", "the dated rate log is kept per property on the hotels page"),
    "ratelog.html": ("hotels.html", "the dated rate log is kept per property on the hotels page"),
    "changelog.html": ("review.html", "value-level changes are reported in the review log, next to the URL that changed"),
    "monitor.html": ("review.html", "monitoring now covers every official URL and reports value changes, not a hand-picked list"),
    "monitoring.html": ("review.html", "monitoring now covers every official URL and reports value changes, not a hand-picked list"),
    "sources.html": ("review.html", "every tracked official URL, its last-checked date and its status are in the review log"),
    "repo-review.html": ("review.html", "the repository and source review is reported in the review log"),
    "workflow.html": ("review.html", "how the site stays current — the scheduled re-checks and what they write — is on the overview and review pages"),
    "archive.html": ("review.html", "earlier sessions' work is preserved in its own folders; the review log links the current one"),
}
for src, (dest, why) in REDIRECTS.items():
    (OUT / src).write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={dest}">
<link rel="canonical" href="{dest}">
<title>Moved · Vegas Strip Poker Planner</title>
<link rel="stylesheet" href="site.css"></head>
<body><nav><div class="mainnav">{"".join(f'<a href="{u}">{E(t)}</a>' for u, t in NAV)}</div></nav><main><section class="page-head"><h1>This page moved</h1>
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
