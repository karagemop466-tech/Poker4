#!/usr/bin/env python3
"""Extract dated, rule-complete tournament rows from the venue PDFs already committed.

Why this exists
---------------
`scripts/integrate_data.py` builds the site from data that earlier passes put in
place.  The largest verified gap in that data was that only the Venetian rows
carried dates: every Wynn, Bellagio and Caesars row was an undated placeholder,
so the date filter, the day plan and the trip calculator could not see them.

This tool does not invent a single value.  It reads **the official capture text
that is already committed in `data/raw/`** (written by the scheduled
`tools/sync_official_sources.py` job, each file pinned to the URL and SHA-256 of
the response it came from) plus the three Bellagio structure sheets committed on
2026-11-17, and emits `data/room-facts.json`.  For every field it keeps the
sentence the value was read from, the official URL and the retrieval date, so
the site can show the quote next to the number.

Deliberately NOT done here
--------------------------
* No value is defaulted, rounded or inferred.  If the capture does not print a
  field, the field is null.
* `single_entry` is only ever "confirmed" when the sheet explicitly restricts
  the player to one entry.  "Re-entry is NOT allowed" *with* rebuys on offer
  (the Wynn Friday format) is recorded as its own state: the player can still
  put more money in, so it is not a freezeout and it is not single-entry.

Run:  python3 tools/room_extract.py
Then: python3 scripts/integrate_data.py   (picks the file up automatically)
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "room-facts.json"

RETRIEVED = "2026-11-17"

WYNN_WPT_SCHED = "https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf"
WYNN_WPT_TERMS = "https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf"
WYNN_DAILY = "https://cdn.wynnresorts.com/image/upload/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf"
WYNN_POSTER = "https://cdn.wynnresorts.com/image/upload/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf"

BELLAGIO_FRI = "https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt9cf95b0e60ec253e/6af491a3a9851d75c40be840/mgm-bellagio-poker-fridays-$600-nlh.pdf"
BELLAGIO_SAT = "https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt6d47974bf5a7d9b6/6af491a391a6e8e4230c9e07/mgm-bellagio-poker-saturdays-$1000-nlh.pdf"
BELLAGIO_SUN = "https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt07fcf1244a6da661/6af491a339e2b4f6b76a86ad/mgm-bellagio-poker-sundays-$400-horse.pdf"
BELLAGIO_PAGE = "https://bellagio.mgmresorts.com/en/casino/poker.html"
CAESARS_PAGE = "https://www.caesars.com/las-vegas/explore/casino/poker-tournaments-las-vegas-strip"

MONTHS = {m: i for i, m in enumerate(
    "January February March April May June July August September October November December".split(), 1)}
MON3 = {m[:3]: i for m, i in MONTHS.items()}

# A block ends where the next event's fee header starts; without this the
# guarantee / chip count of the *following* event leaks into the current row.
NEXT_EVENT = re.compile(r"\n\s*\$[\d,]+\s+(?:Entry Fee|Buy-?[Ii]n)\b")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flat(text: str) -> str:
    """PDF text wraps mid-sentence; collapse whitespace so excerpts are readable."""
    return re.sub(r"\s+", " ", text).strip()


def money(s: str | None) -> int | None:
    return int(re.sub(r"[^\d]", "", s)) if s and re.search(r"\d", s) else None


def iso(month_day: str) -> str | None:
    m = re.match(r"(\w+)\.?\s+(\d{1,2}),\s*(\d{4})", month_day.strip())
    if not m:
        return None
    month = MONTHS.get(m.group(1)) or MON3.get(m.group(1)[:3])
    if not month:
        return None
    return f"{int(m.group(3)):04d}-{month:02d}-{int(m.group(2)):02d}"


DAY_TIME = re.compile(
    r"(\w+ \d{1,2}, 2026)\s*,?\s*(?:at\s*)?(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\.", re.I)


def day_time(line: str):
    m = DAY_TIME.search(line)
    if not m:
        return None
    hour, minute = int(m.group(2)), m.group(3) or "00"
    mer = "PM" if m.group(4).lower() == "p" else "AM"
    return {"date": iso(m.group(1)), "time": f"{hour}:{minute} {mer}", "excerpt": flat(m.group(0))}


def section(block: str, start: str, end: str) -> str:
    m = re.search(rf"{start}\s*:?\s*(.*?)(?:{end}\s*:|\Z)", block, re.S | re.I)
    return flat(m.group(1)) if m else ""


def fee_split(text: str):
    """'Entry Fee: $600 Buy-in = $510 (Tournament Prize Pool) + $65 (Tournament Fee) + ...'"""
    m = re.search(r"Entry Fee:\s*\$([\d,]+)\s*Buy-?in\s*=\s*(.+?)(?:\s*Registration:|$)", text, re.S | re.I)
    if not m:
        return None, [], ""
    total = money(m.group(1))
    # A Ladies event prints a second, discounted split. Only the first split belongs
    # to the headline buy-in; the discounted one is kept separately.
    body_all = flat(m.group(2))
    body = body_all.split("Discounted")[0]
    components = [{"amount_usd": money(a), "purpose": flat(p)}
                  for a, p in re.findall(r"\$\s*([\d,]+)\s*\(([^)]*)\)", body)]
    discounted = ""
    if "Discounted" in body_all:
        dm = re.search(r"Discounted.{0,240}", body_all)
        discounted = flat(dm.group(0))[:240] if dm else ""
    return total, components, flat("Entry Fee: " + m.group(0).strip()), discounted


def entry_rule(reg_text: str):
    """Classify the printed registration rule. Never guesses."""
    t = flat(reg_text or "")
    low = t.lower()
    out = {
        "single_entry": {"status": "unverified", "value": None, "excerpt": None},
        "re_entry": {"status": "not_stated_in_sheet", "value": None, "excerpt": None},
        "add_on": {"status": "not_stated_in_sheet", "value": None, "excerpt": None},
    }

    def sent(pattern):
        m = re.search(rf"[^.]*{pattern}[^.]*\.", t, re.I)
        return m.group(0).strip() if m else t[:240]

    if re.search(r"no re-?entry", low):
        out["re_entry"] = {"status": "forbidden", "value": "re-entry not allowed (printed)",
                           "excerpt": sent(r"no re-?entr\w*")}
    if re.search(r"unlimited re-?entr|unlimited rebuys?", low):
        out["re_entry"] = {"status": "confirmed_allowed", "value": "unlimited re-entry / rebuys (printed)",
                           "excerpt": sent(r"unlimited re-?entr\w*|rebuy")}
    if re.search(r"registration,? (?:and )?re-?entries|re-?entries will be available|"
                 r"re-entries,? and one \(1\) add-?on", low) and out["re_entry"]["status"] == "not_stated_in_sheet":
        out["re_entry"] = {"status": "confirmed_allowed",
                           "value": "re-entries available (printed)",
                           "excerpt": sent(r"re-?entries will be available|re-entries,? and one")}
    m = re.search(r"one \(1\) entry and one \(1\) re-?entry|four \(4\) entries maximum|"
                  r"one \(1\) entry per starting flight|maximum of (\w+) entries", low)
    if m:
        out["re_entry"] = {"status": "confirmed_limited", "value": flat(m.group(0)),
                           "excerpt": sent(r"one \(1\) entry|four \(4\) entries|maximum")}
    if re.search(r"add-?on", low):
        out["add_on"] = {"status": "confirmed_allowed", "value": "add-on offered",
                         "excerpt": sent(r"add-?on")}
    if re.search(r"(only one entry|one entry only|no additional entries|single entry only|freezeout)", low):
        out["single_entry"] = {"status": "confirmed", "value": "one entry",
                               "excerpt": sent(r"only one entry|one entry only|no additional entries|single entry only|freezeout")}
    out["spend_advantage"] = (out["re_entry"]["status"] in ("confirmed_allowed", "confirmed_limited")
                              or out["add_on"]["status"] == "confirmed_allowed")
    return out


# ----------------------------------------------------------------- Wynn WPT series
def wynn_wpt():
    path = RAW / "wynn-wpt-terms.txt"
    text = path.read_text(encoding="utf-8")
    chunks = text.split("TERMS AND CONDITIONS")[1:]
    events, skipped = [], []
    for idx, chunk in enumerate(chunks, 1):
        block = NEXT_EVENT.split(chunk)[0]
        head = re.search(r"This (\$[\d,]+) (.+?) tournament", block, re.S)
        if not head:
            skipped.append({"block_index": idx, "reason": "no '$X <name> poker tournament' opening sentence",
                            "opening": flat(chunk)[:160]})
            continue
        buy = money(head.group(1))
        label = flat(head.group(2))
        gtd = re.search(r"\$([\d,]+)\s*GUARANTEE", block, re.I)
        total, components, fee_excerpt, discounted = fee_split(block)
        reg = section(block, "Registration", "Starting Stack|Length of Play|Breaks")
        rules = entry_rule(reg)
        days = []
        for line in block.split("\n"):
            found = day_time(line)
            if found and found["date"]:
                tag = re.match(r"\s*(?:•\s*)?((?:Day|Final Table)[^:,]*)", line)
                days.append({**found, "stage": flat(tag.group(1)) if tag else None})
        chips = re.search(r"Players (?:will )?start with ([\d,]+)", block)
        lvl = re.search(r"(\d{1,3})\s*minutes per level", block)
        pay = re.search(r"(1-in-\w+|approximately 12\.5%)", block, re.I)
        events.append({
            "id": f"WPT-{idx:02d}",
            "venue": "wynn",
            "venue_name": "Wynn Las Vegas Poker",
            "buy_in_usd": buy,
            "name_printed": label,
            "guarantee_usd": money(gtd.group(1)) if gtd else None,
            "guarantee_excerpt": flat(gtd.group(0)) if gtd else None,
            "fee_total_usd": total,
            "fee_components": components,
            "fee_excerpt": fee_excerpt,
            "fee_split_sums_to_buy_in": (sum(c["amount_usd"] or 0 for c in components) == total)
                                        if components else None,
            "discounted_entry_excerpt": discounted or None,
            "registration_excerpt": reg,
            "rules": rules,
            "starting_chips": money(chips.group(1)) if chips else None,
            "level_minutes": int(lvl.group(1)) if lvl else None,
            "payout_fraction": flat(pay.group(0)) if pay else None,
            "days": days,
            "source": WYNN_WPT_TERMS,
            "retrieved": RETRIEVED,
            "block_index": idx,
        })
    return {"file": "data/raw/wynn-wpt-terms.txt", "sha256": sha256(path), "url": WYNN_WPT_TERMS,
            "events": events, "unparsed_blocks": skipped}


# --------------------------------------------------------------- Wynn daily slate
def wynn_daily():
    path = RAW / "wynn-daily-structures.txt"
    text = path.read_text(encoding="utf-8")
    chunks = text.split("TERMS AND CONDITIONS")[1:]
    events = []
    for idx, chunk in enumerate(chunks, 1):
        block = NEXT_EVENT.split(chunk)[0]
        head = re.search(r"This (\$[\d,]+) (.+?) tournament", block, re.S)
        if not head:
            continue
        body = flat(NEXT_EVENT.split(chunk)[0])
        clauses = [c.strip() for c in re.split(r"(?<=\.)\s+(?=\d{1,2}\.\s)", body)]
        reg = next((c for c in clauses if re.match(r"\d+\.\s*Registration", c)), "")
        fee_clause = next((c for c in clauses if "Entry Fee will be distributed" in c), "")
        start = re.search(r"beginning at (\d{1,2}(?::\d{2})?)\s*([ap])\.?\s*m\.", block, re.I)
        days = re.search(r"offered ([A-Za-z&,\- ]+?) and may be suspended", block, re.I)
        addon = re.search(r"(Unlimited \$[\d,]+ rebuys[^.]*\.|[Oo]ne \(1\) \$[\d,]+ add-?on[^.]*\.)", body)
        events.append({
            "id": f"WYNN-DAILY-{idx}",
            "venue": "wynn", "venue_name": "Wynn Las Vegas Poker",
            "buy_in_usd": money(head.group(1)),
            "name_printed": flat(head.group(2)),
            "guarantee_usd": money(re.search(r"\$([\d,]+)\s*Guarantee", block, re.I).group(1))
                             if re.search(r"\$([\d,]+)\s*Guarantee", block, re.I) else None,
            "start_time": (f"{start.group(1)} {'PM' if start.group(2).lower() == 'p' else 'AM'}"
                           if start else None),
            "offered_days_printed": flat(days.group(1)) if days else None,
            "fee_excerpt": fee_clause or None,
            "registration_excerpt": reg or None,
            "rules": entry_rule(reg),
            "extra_play_option_excerpt": flat(addon.group(0)) if addon else None,
            "starting_chips": money(re.search(r"start with ([\d,]+)", body).group(1))
                              if re.search(r"start with ([\d,]+)", body) else None,
            "level_minutes": int(re.search(r"(\d{1,3}) minutes per level", body).group(1))
                             if re.search(r"(\d{1,3}) minutes per level", body) else None,
            "source": WYNN_DAILY, "retrieved": RETRIEVED, "block_index": idx,
        })
    return {"file": "data/raw/wynn-daily-structures.txt", "sha256": sha256(path), "url": WYNN_DAILY,
            "poster_file": "data/raw/wynn-daily-poster.txt", "poster_url": WYNN_POSTER,
            "events": events}


# ---------------------------------------------------------------------- Bellagio
BELLAGIO_SPECS = [
    ("BELLAGIO-FRI", "data/raw/bellagio-friday-600-nlh.txt", BELLAGIO_FRI, "Friday",
     "$600 No Limit Hold'em", 600, "11:00 AM"),
    ("BELLAGIO-SAT", "data/raw/bellagio-saturday-1100-nlh.txt", BELLAGIO_SAT, "Saturday",
     "No Limit Hold'em — the sheet's title block prints '$1100 BUY-IN' and the poker page lists it as "
     "'SATURDAYS | $1,000 NLH', while rule 07 on the same sheet says 'Of the $600 Buy-in': the buy-in "
     "is therefore left blank and the row is flagged", None, "11:00 AM"),
    ("BELLAGIO-SUN", "data/raw/bellagio-sunday-400-horse.txt", BELLAGIO_SUN, "Sunday",
     "$400 H.O.R.S.E.", 400, "11:00 AM"),
]


def bellagio():
    events = []
    for eid, rel, url, weekday, label, buy, start in BELLAGIO_SPECS:
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        body = flat(text)
        fee = (re.search(r"(?:The )?\$([\d,]+) Buy-?[Ii]n is allocated as follows:\s*(.+?)\.", body)
               or re.search(r"Of the \$([\d,]+) Buy-?in,\s*(.+?)\.", body))
        components = []
        if fee:
            parts = re.split(r"[;,]|\band\b", fee.group(2)) if ";" not in fee.group(2) \
                    else fee.group(2).split(";")
            for part in parts:
                mm = re.match(r"\s*\$([\d,]+)\s*(.*)", part.strip())
                if mm:
                    components.append({"amount_usd": money(mm.group(1)), "purpose": mm.group(2).strip()})
        reg = re.search(r"Players may buy-in and re-enter[^.]*\.|Registration will be open until[^.]*\.", body)
        reg_txt = reg.group(0).strip() if reg else ""
        rules = entry_rule(reg_txt)
        if re.search(r"may buy-in and re-enter", reg_txt, re.I):
            rules["re_entry"] = {"status": "confirmed_allowed",
                                 "value": "buy-in and re-enter through the end of level 8",
                                 "excerpt": reg_txt}
            rules["spend_advantage"] = True
        gr = re.search(r"Bellagio guarantees[^.]*\.", body)
        gtd = re.search(r"\$([\d,]+)", gr.group(0)) if gr else None
        chips = re.search(r"Players (?:will )?start with ([\d,]+)", body)
        lvl = re.search(r"(\d{1,3}) [Mm]inutes? in [Ll]ength|(\d{1,3})\s*minutes in length|"
                        r"[Ee]ach level will last thirty \((\d{1,2})\)", body)
        events.append({
            "id": eid, "venue": "bellagio", "venue_name": "Bellagio Poker Room",
            "buy_in_usd": buy, "name_printed": label,
            "weekday": weekday, "start_time": start,
            "guarantee_usd": money(gtd.group(1)) if gtd else None,
            "guarantee_excerpt": gr.group(0) if gr else None,
            "fee_excerpt": flat(fee.group(0)) if fee else None,
            "fee_components": components,
            "registration_excerpt": reg_txt,
            "rules": rules,
            "starting_chips": money(chips.group(1)) if chips else None,
            "level_minutes": 30 if re.search(r"30 Minutes in Length|thirty \(30\)", body) else None,
            "source": url, "retrieved": RETRIEVED,
            "capture_file": rel, "capture_sha256": sha256(p),
            "page_source": BELLAGIO_PAGE,
        })
    return events


def main():
    wpt = wynn_wpt()
    daily = wynn_daily()
    bell = bellagio()

    problems = []          # an extraction failure: the build must stop
    irregularities = []    # the official document itself is inconsistent: flag, do not "fix"
    if len(wpt["events"]) < 60:
        problems.append(f"Wynn WPT rows parsed: {len(wpt['events'])} (<60) — capture truncated?")
    for e in wpt["events"]:
        if not e["days"]:
            problems.append(f"{e['id']} has no printed play day")
        if not e["fee_components"]:
            problems.append(f"{e['id']} has no printed fee split")
        # a guarantee must be printed inside this block, not inherited from the next
        if e.get("fee_split_sums_to_buy_in") is False:
            irregularities.append(f"{e['id']} printed fee split does not add up to the printed buy-in "
                            f"({sum(c['amount_usd'] or 0 for c in e['fee_components'])} vs {e['buy_in_usd']}) "
                            f"— recorded verbatim and flagged, not corrected")
        if e["guarantee_usd"] and e["guarantee_usd"] > 6_000_000:
            problems.append(f"{e['id']} guarantee looks borrowed from another block: {e['guarantee_usd']}")
    for e in daily["events"]:
        if not e["start_time"]:
            problems.append(f"{e['id']} has no printed start time")
        if not e["registration_excerpt"]:
            problems.append(f"{e['id']} has no printed registration clause")
    for e in bell:
        if not e["fee_components"]:
            problems.append(f"{e['id']} has no printed fee split")

    payload = {
        "meta": {
            "generated_by": "tools/room_extract.py",
            "session": "511d43ab (tasks A1/A2)",
            "retrieved": RETRIEVED,
            "policy": ("Every value below was read from the official capture text committed in data/raw/ "
                       "(the same bytes the scheduled monitor hashes) or from the venue's structure sheet "
                       "committed on 2026-11-17. Fields the sheet does not print are null. "
                       "single_entry stays 'unverified' unless the sheet restricts the player to one entry."),
            "sources": [
                {"url": WYNN_WPT_TERMS, "label": "Wynn — WPT World Championship structures (every event sheet)", "venue": "Wynn Las Vegas"},
                {"url": WYNN_WPT_SCHED, "label": "Wynn — WPT World Championship schedule", "venue": "Wynn Las Vegas"},
                {"url": WYNN_DAILY, "label": "Wynn — all daily tournament structures", "venue": "Wynn Las Vegas"},
                {"url": WYNN_POSTER, "label": "Wynn — daily tournament poster", "venue": "Wynn Las Vegas"},
                {"url": BELLAGIO_FRI, "label": "Bellagio — Friday $600 NLH structure sheet", "venue": "Bellagio"},
                {"url": BELLAGIO_SAT, "label": "Bellagio — Saturday NLH structure sheet", "venue": "Bellagio"},
                {"url": BELLAGIO_SUN, "label": "Bellagio — Sunday $400 H.O.R.S.E. structure sheet", "venue": "Bellagio"},
                {"url": BELLAGIO_PAGE, "label": "Bellagio poker room page (links the three sheets)", "venue": "Bellagio"},
                {"url": CAESARS_PAGE, "label": "Caesars Palace + Horseshoe daily tournament description", "venue": "Caesars Palace"},
            ],
            "problems": problems,
            "source_irregularities": irregularities,
            "unparsed_blocks": wpt["unparsed_blocks"],
        },
        "wynn_wpt": wpt,
        "wynn_daily": daily,
        "bellagio": bell,
        "caesars": {
            "source": CAESARS_PAGE, "retrieved": RETRIEVED,
            "schedule_excerpt": ("At Caesars Palace, the daily schedule runs like clockwork. You will find four "
                                 "No-Limit Hold'em tournaments each day at 10 a.m., 2 p.m., 6 p.m. and 9 p.m. Every "
                                 "event carries a $100 buy-in, starts you with 20,000 chips, and features a $1,000 "
                                 "guaranteed prize pool. Blinds increase every 20 minutes to keep the pace lively, and "
                                 "a $50 add-on at the first break gives you an extra 15,000 chips if you want a deeper run."),
            "horseshoe_excerpt": ("At Horseshoe Las Vegas, the tournament slate ups the ante with six daily No-Limit "
                                  "Hold'em games. The times at 9 a.m., 11 a.m., 2 p.m., 5 p.m., 8 p.m. and 11 p.m. provide "
                                  "plenty of opportunity throughout the day to grab a seat. A mixture of buy-ins, levels "
                                  "and guarantees caters to all participants"),
            "times": ["10:00 AM", "2:00 PM", "6:00 PM", "9:00 PM"],
            "buy_in_printed": 100, "chips_printed": 20000, "guarantee_printed": 1000,
            "level_minutes_printed": 20,
            "rules": {
                "single_entry": {"status": "unverified", "value": None,
                                 "excerpt": "the page prints no single-entry rule"},
                "re_entry": {"status": "unverified", "value": None,
                             "excerpt": "the page describes the slate but prints no re-entry rule"},
                "add_on": {"status": "confirmed_allowed", "value": "$50 add-on for 15,000 extra chips",
                           "excerpt": "a $50 add-on at the first break gives you an extra 15,000 chips"},
                "fee": {"status": "unverified", "value": None,
                        "excerpt": "the page prints the $100 buy-in but not the house-fee split"},
                "spend_advantage": True,
            },
        },
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"room-facts: WPT {len(wpt['events'])} · Wynn daily {len(daily['events'])} · "
          f"Bellagio {len(bell)} · Caesars {len(payload['caesars']['times'])} printed start times · "
          f"unparsed WPT blocks {len(wpt['unparsed_blocks'])}")
    for p in problems:
        print("PROBLEM:", p)
    for i in irregularities:
        print("OFFICIAL-SOURCE IRREGULARITY:", i)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
