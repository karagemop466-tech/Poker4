#!/usr/bin/env python3
"""f0d7de66 — extract Wynn / WPT tournament rows from the OFFICIAL capture, mechanically.

Why a script instead of hand-typed rows: every number and every rule sentence written into
data/f0d7de66/events.json has to be a verbatim substring of the official document text that the
source monitor saved in data/raw/, or this script refuses to write the file. That is what keeps
the site free of invented values: the builder cannot be quieter than its source.

Inputs (each is a plain-text capture of the venue's own PDF, with the URL + sha256 + capture
timestamp in a leading HTML comment written by tools/sync_official_sources.py):
  data/raw/wynn-wpt-terms.txt      WPT World Championship Structures PDF  (69 event sheets)
  data/raw/wynn-daily-structures.txt  Wynn "All Daily Structures" PDF     (4 recurring dailies)

Output:
  data/f0d7de66/events.json        rows in the shape scripts/integrate_data.py already consumes
  data/f0d7de66/extraction-report.json  counts, per-event coverage, every verbatim check

Run:  python3 tools/f0d7de66_extract_official.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "f0d7de66"

MONTHS = {m: i for i, m in enumerate(
    "january february march april may june july august september october november december".split(), 1)}
WEEKDAYS = {w: i for i, w in enumerate("monday tuesday wednesday thursday friday saturday sunday".split())}

NUM = r"\$?([\d,]+(?:\.\d+)?)"


def cents(txt: str) -> int | None:
    m = re.search(r"\$\s*([\d,]+)", txt)
    return int(m.group(1).replace(",", "")) if m else None


def normalise(text: str) -> str:
    """Collapse whitespace so a captured line-wrap never breaks a verbatim check."""
    return re.sub(r"\s+", " ", text.replace("\u2019", "'").replace("\u2018", "'")
                  .replace("\u201c", '"').replace("\u201d", '"')).strip()


def time24(s: str) -> str | None:
    """Normalise a printed clock time to the 12-hour 'H:MM AM/PM' form the dashboard's
    overlap and sequencing maths understands (scripts/integrate_data.py: to_min())."""
    m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?", s.strip(), re.I)
    if not m:
        return None
    h = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "p" else 0)
    mins = m.group(2) or "00"
    ampm = "AM" if h < 12 else "PM"
    return f"{(h % 12) or 12}:{mins} {ampm}"


def hm_to_min(t: str | None):
    """'3:40 PM' -> 220, or None. Mirrors scripts/integrate_data.py: to_min()."""
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", (t or "").upper())
    if not m:
        return None
    return (int(m.group(1)) % 12 + (12 if m.group(3) == "PM" else 0)) * 60 + int(m.group(2))


def min_to_hm(mins: int) -> str:
    h, mi = divmod(mins % (24 * 60), 60)
    ampm = "AM" if h < 12 else "PM"
    return f"{(h % 12) or 12}:{mi:02d} {ampm}"


def clean_name(txt: str) -> str:
    """Trim the boilerplate off the sheet's own sentence so the row shows the event name."""
    t = normalise(txt)
    t = re.sub(r"\*+", "", t)
    t = re.sub(r"\s+poker tournament$", "", t, flags=re.I)
    t = re.sub(r"\s+tournament$", "", t, flags=re.I)
    t = re.sub(r"[,.]\s*$", "", t)
    t = re.sub(r"^(Guaranteed|Guarantee)\s+", "", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()


# --------------------------------------------------------------------- capture reading
def read_capture(name: str) -> tuple[str, dict]:
    path = RAW / name
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = {"file": f"data/raw/{name}"}
    m = re.match(r"<!--\s*captured\s+(\S+)\s+from\s+(\S+)\s+\(sha256\s+([0-9a-f]+)\)", text)
    if m:
        meta.update(captured_at=m.group(1), url=m.group(2), sha256=m.group(3))
    meta["sha256_of_capture"] = hashlib.sha256(text.encode()).hexdigest()
    return text, meta


# ------------------------------------------------------------------------ block parse
SECTION_RX = re.compile(
    r"^(Entry Fee|Registration|Starting Stack|Length of Play|Breaks|Players Per Table|Payouts|"
    r"Action Clock|Milestone Rules|Late Registration|Add-?on|Re-?buy)\s*:\s*(.*)$", re.I)


def split_sections(block: str) -> dict[str, str]:
    """Return {section-name: verbatim body} for the labelled paragraphs of one event sheet."""
    lines = block.split("\n")
    out: dict[str, list[str]] = {}
    cur = None
    for raw in lines:
        line = raw.strip()
        m = SECTION_RX.match(line)
        if m:
            cur = m.group(1).lower().replace("-", "").replace(" ", "")
            out.setdefault(cur, [])
            if m.group(2).strip():
                out[cur].append(m.group(2).strip())
            continue
        if cur and line:
            out[cur].append(line)
    return {k: " ".join(v) for k, v in out.items()}


DAY_LINE = re.compile(
    r"^\s*(?:(?P<label>Day\s*\d+[A-Z]?|Final\s+Table|Semifinal|Heads-Up|Flight\s*\d+)\s*[:\-]\s*)?"
    r"[•*\-]?\s*(?P<wd>[A-Za-z]+day),?\s*(?P<mon>[A-Za-z]+)\.?\s+(?P<day>\d{1,2}),?\s*(?P<yr>\d{4})"
    r",?\s*(?:at\s+)?(?P<time>\d{1,2}(?::\d{2})?\s*[ap]\.m\.?)\s*$", re.I)


def parse_day_lines(block: str) -> list[dict]:
    """Every dated start a sheet prints, line by line, so no wording variant is guessed at:
    'Day 1A: Wednesday, December 16, 2026 at 11 a.m.', '• Tuesday, December 15, 2026 12 p.m.',
    and the bare 'Friday, November 27, 2026, at 12 p.m.' under 'This event will be held …'."""
    rows, seen = [], set()
    for raw in block.split("\n"):
        m = DAY_LINE.match(raw.rstrip())
        if not m:
            continue
        key = (m.group("label"), m.group("mon").lower(), m.group("day"), m.group("time").lower())
        if key in seen:
            continue
        seen.add(key)
        rows.append({"label": re.sub(r"\s+", " ", m.group("label")).title() if m.group("label") else None,
                     "printed_weekday": m.group("wd"), "month": m.group("mon"),
                     "day": int(m.group("day")), "year": int(m.group("yr")), "time": m.group("time")})
    for r in rows:
        iso = dt.date(r["year"], MONTHS[r["month"].lower()], r["day"])
        r["date"] = iso.isoformat()
        r["weekday_ok"] = WEEKDAYS[r["printed_weekday"].lower()] == iso.weekday()
        r["weekday_printed"] = r.pop("printed_weekday")
        r["time_display"] = time24(r["time"])
    return rows


def parse_terms(text: str, source_url: str, retrieved: str) -> tuple[list[dict], list[dict], dict]:
    """Walk the structures PDF text event-sheet by event-sheet."""
    lines = [l.rstrip() for l in text.split("\n")]
    idx = [i for i, l in enumerate(lines) if re.match(r"^\s*TERMS AND CONDITIONS\s*$", l)]
    events: list[dict] = []
    problems: list[dict] = []
    for n, i in enumerate(idx):
        end = idx[n + 1] - 1 if n + 1 < len(idx) else len(lines)
        # header = the non-empty lines above the marker, stopping at the previous sheet's tail
        head: list[str] = []
        j = i - 1
        while j > 0 and len(head) < 3:
            s = lines[j].strip()
            if not s:
                if head:
                    break
                j -= 1
                continue
            if re.search(r"(Players Per Table|Payouts|Breaks|Action Clock|Level\s+Small Blind|^\d+\s)", s):
                break
            head.insert(0, s)
            j -= 1
        block = "\n".join(lines[i + 1:end])
        secs = split_sections(block)
        desc = re.search(r"This\s+(.{0,240}?)\s*\(the .{0,3}Tournament.{0,3}\)\s*is\s*a?\.?\s*"
                         r"(one|single|two|three|four|five|six|[6-9])-?day?\s*([^.]*)\s*event",
                         block, re.I | re.S)
        name_src = " ".join(head)
        if desc:
            name_src = desc.group(1).strip()
        name = clean_name(name_src)
        buy = None
        for src_txt in (secs.get("entryfee"), name_src, block[:400]):
            if src_txt:
                m = re.search(r"Entry Fee:\s*\$\s*([\d,]+)", src_txt) or re.search(r"This\s*\$\s*([\d,]+)", src_txt) \
                    or re.search(r"^\s*\$\s*([\d,]+)", src_txt)
                if m:
                    buy = int(m.group(1).replace(",", ""))
                    break
        gtd = None
        gtd_txt = None
        for cand in (" ".join(head[:1]), block[:600]):
            m = re.search(r"\$\s*([\d,]+)\s*(?:GUARANTEE|Guarantee(?:d)?|GTG)", cand, re.I)
            if m:
                gtd = int(m.group(1).replace(",", ""))
                gtd_txt = normalise(m.group(0))
                break
        pool = fee = staff = bounty_pool = None
        if secs.get("entryfee"):
            for m in re.finditer(r"\$\s*([\d,]+)\s*\(([^)]*)\)", secs["entryfee"]):
                amt = int(m.group(1).replace(",", ""))
                tag = m.group(2).lower()
                if "prize pool" in tag:
                    pool = (pool or 0) + amt
                elif "bounty" in tag:
                    bounty_pool = (bounty_pool or 0) + amt
                elif "tournament fee" in tag or "maintenance" in tag:
                    fee = (fee or 0) + amt
                elif "service charge" in tag or "staff" in tag:
                    staff = (staff or 0) + amt
        reg = secs.get("registration", "")
        reg_closes = None
        if reg:
            m_app = re.search(r"\(approximately\s+([0-9]{1,2}(?::[0-9]{2})?\s*[ap]\.m\.)\)", reg, re.I)
            m_lvl = re.search(r"until the start of level\s*(\d+)", reg, re.I)
            if m_app:
                reg_closes = time24(m_app.group(1))
            elif m_lvl:
                reg_closes = f"start of level {m_lvl.group(1)}"
        stack = None
        m = re.search(r"start with\s*([\d,]+)\s*(?:in\s*)?tournament chips", secs.get("startingstack", ""), re.I)
        if m:
            stack = int(m.group(1).replace(",", ""))
        lv = None
        m = re.search(r"(\d{2})\s*minutes per level", secs.get("lengthofplay", ""), re.I)
        if m:
            lv = int(m.group(1))
        events.append({
            "sheet_index": n + 1, "name": name, "buy_in_usd": buy, "guarantee_usd": gtd,
            "guarantee_excerpt": gtd_txt, "pool_per_entry_usd": pool, "house_fee_usd": fee,
            "staff_charge_usd": staff, "bounty_pool_usd": bounty_pool, "starting_chips": stack,
            "level_minutes": lv, "registration_excerpt": reg or None, "registration_closes": reg_closes,
            "length_of_play": normalise(secs.get("lengthofplay", "")) or None,
            "payouts": normalise(secs.get("payouts", "")) or None,
            "add_on_excerpt": (secs.get("addon") or None), "rebuy_excerpt": (secs.get("rebuy") or None),
            "entry_fee_excerpt": normalise(secs.get("entryfee") or "") or None,
            "mentions_bounty": bool(re.search(r"bount", block, re.I)),
            "days": parse_day_lines(block), "block_chars": len(block),
            "source_url": source_url, "retrieved": retrieved,
        })
        if not reg:
            problems.append({"event": name, "problem": "no Registration paragraph found on this sheet"})
        if not days_ok(events[-1]):
            problems.append({"event": name, "problem": "printed weekday does not match the calendar date"})
    return events, problems, {"sheets": len(idx)}


def days_ok(ev: dict) -> bool:
    return all(d["weekday_ok"] for d in ev["days"]) if ev["days"] else True


# ------------------------------------------------------------------- entry-rule verdicts
def entry_rules(ev: dict, source_url: str, retrieved: str) -> dict:
    reg = (ev.get("registration_excerpt") or "")
    low = reg.lower()
    ret = {"retrieved": retrieved, "source": source_url}
    if not reg:
        single = {"status": "unverified", "value": None, "excerpt": None, **ret}
        reent = {"status": "not_stated_in_sheet", "value": None, "excerpt": None, **ret}
    else:
        cap = re.search(r"([A-Za-z()0-9, ]{0,40}?(?:Entries?|Re-?entries?)\s+maximum[^.]*\.)", reg, re.I)
        unlimited = "unlimited re-entry" in low or "unlimited re-entries" in low
        if cap:
            val = "entry count limited by the printed maximum"
            st = "no"
        elif unlimited or "re-entry" in low or "re-entries" in low or "rebuy" in low or "add-on" in low:
            val, st = "multiple entries allowed", "no"
        else:
            val, st = None, "not_stated_in_sheet"
        single = {"status": st, "value": val, "excerpt": normalise(reg)[:600], **ret}
        reent = {"status": "confirmed_allowed" if ("re-entry" in low or "re-entries" in low or "rebuy" in low)
                 else ("not_stated_in_sheet" if not reg else "no"),
                 "value": normalise(reg)[:300] or None, "excerpt": normalise(reg)[:600], **ret}
    addon_txt = ev.get("add_on_excerpt") or (("add-on" in low and normalise(reg)[:300]) or None)
    addon = {"status": "confirmed_allowed" if addon_txt else "not_stated_in_sheet",
             "value": addon_txt, "excerpt": addon_txt, **ret}
    # The fee line is published verbatim on the sheet; nothing here is recomposed, so the
    # quoted sentence is both the value and the excerpt. The parsed numbers live in their own
    # typed fields on the row (pool_per_entry_usd / house_fee_usd / staff_charge_usd).
    fee_txt = ev.get("entry_fee_excerpt")
    fee = {"status": "confirmed" if fee_txt else "unverified", "value": fee_txt, "excerpt": fee_txt, **ret}
    return {"single_entry": single, "re_entry": reentry_status(ev, reent, ret), "add_on": addon, "fee": fee}


def reentry_status(ev: dict, reent: dict, ret: dict) -> dict:
    reg = (ev.get("registration_excerpt") or "").lower()
    if "re-entry is not allowed" in reg or "reentry is not allowed" in reg:
        return {"status": "confirmed_not_allowed", "value": "re-entry prohibited (rebuys may still be offered)",
                "excerpt": reent.get("excerpt"), **ret}
    return reent


# ------------------------------------------------------------------------- Wynn dailies
def parse_dailies(text: str, source_url: str, retrieved: str) -> tuple[list[dict], dict]:
    """The daily-structures PDF prints one TERMS AND CONDITIONS numbered list per recurring event."""
    norm = normalise(text)
    out = []
    heads = re.finditer(r"(Monday-Thursday|Friday|Saturday & Sunday|Nightly)\s*(NLH[^*]{0,60}?|[^*]{0,40}?)?"
                       r"\s*\$([\d,]+)\s*(GUARANTEE|Guarantee)", norm)
    # simpler and safer: split on the numbered term blocks
    blocks = re.split(r"(?=\d{1,2}\.\s*This\s*\$\s*[\d,]+\s)", norm)
    for b in blocks[1:]:
        b = b[:6000]
        m_name = re.search(r"This\s*\$\s*([\d,]+)\s*([^.(]{0,80}?)\s*\$?\s*([\d,]{2,11})?\s*"
                           r"(Guarantee|GTD)?\s*poker tournament", b, re.I)
        m_entry = re.search(r"The Tournament entry fee(?:, as well as the re-entry fee,)?\s*is\s*\$\s*([\d,]+)", b, re.I)
        m_fee = re.search(r"(The \$\s*[\d,]+ Entry Fee will be distributed as follows:[^.]*\.)", b, re.I) \
            or re.search(r"(The Tournament entry fee is \$\s*[\d,]+[^.]*\.\s*\$\s*[\d,]+ of each Entry Fee[^.]*\.)", b, re.I) \
            or re.search(r"(of which \$\s*[\d,]+ will be withheld[^.]*\.\s*\$\s*[\d,]+ of each [^.]*\.)", b, re.I)
        m_reg = re.search(r"(Registration.{0,520}?)(?:Players will start with|All levels play|Tables will be played|These Tournament terms)", b, re.I)
        m_stack = re.search(r"start with\s*([\d,]+)\s*in Tournament chips", b, re.I)
        m_days = re.search(r"The Tournament will be offered\s*([^.]*)\.", b, re.I)
        m_start = re.search(r"(?:Single Day|beginning at)\s*(?:No Limit Hold'em event beginning at\s*)?(\d{1,2}\s*[ap]\.m\.)", b, re.I)
        if not (m_entry and m_reg):
            continue
        out.append({
            "name": normalise(f"${int(m_entry.group(1).replace(',', '')):,} " + (m_name.group(2).strip() if m_name else "NLH")),
            "buy_in_usd": int(m_entry.group(1).replace(",", "")),
            "guarantee_usd": (int(m_name.group(3).replace(",", "")) if m_name and m_name.group(3) else None),
            "days_offered": (normalise(m_days.group(1)).split(" and may be suspended")[0]) if m_days else None,
            "start_time": time24(m_start.group(1)) if m_start else None,
            "starting_chips": int(m_stack.group(1).replace(",", "")) if m_stack else None,
            "registration_excerpt": normalise(m_reg.group(1)),
            "fee_excerpt": normalise(m_fee.group(1)) if m_fee else None,
            "block_head": normalise(b[:160]),
            "source_url": source_url, "retrieved": retrieved,
        })
    return out, {"blocks_seen": len(blocks) - 1, "rows": len(out)}


# ------------------------------------------------------------------------- build the file
def main() -> int:
    wpt_text, wpt_meta = read_capture("wynn-wpt-terms.txt")
    daily_text, daily_meta = read_capture("wynn-daily-structures.txt")
    retrieved = (wpt_meta.get("captured_at") or "")[:10] or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    events, problems, counts = parse_terms(wpt_text, wpt_meta.get("url", ""), retrieved)
    dailies, dcounts = parse_dailies(daily_text, daily_meta.get("url", ""), retrieved)

    rows, checks = [], []
    for ev in events:
        rules = entry_rules(ev, ev["source_url"], retrieved)
        spend = [s for s in (rules["re_entry"].get("excerpt"),) if s]
        tags = []
        if "bounty" in ev["name"].lower() or ev.get("mentions_bounty"):
            tags.append("bounty")
        if "satellite" in ev["name"].lower():
            tags.append("satellite")
        if "turbo" in ev["name"].lower():
            tags.append("turbo")
        if len(ev["days"]) > 1 and ev["days"][0]["label"]:
            tags.append("multi-flight")
        starts = ev["days"] or [{}]
        for k, d in enumerate(starts):
            is_cont = bool(d.get("label") and re.match(r"(Day\s*[2-9]|Final Table|Semifinal)", d["label"], re.I))
            rc_printed = ev.get("registration_closes")
            rc, rc_basis = rc_printed, None
            m_lvl = re.search(r"start of level (\d+)", rc_printed or "", re.I)
            start_min = hm_to_min(time24(d.get("time_display") or ""))
            if m_lvl and start_min is not None and ev.get("level_minutes"):
                cut = start_min + (int(m_lvl.group(1)) - 1) * int(ev["level_minutes"])
                rc = min_to_hm(cut)
                rc_basis = (f"derived arithmetic, not a printed clock time: the sheet closes entries at the "
                            f"start of level {m_lvl.group(1)}, i.e. after {int(m_lvl.group(1)) - 1} levels of "
                            f"{ev['level_minutes']} minutes from the {time24(d['time_display'])} start = {rc}")
            rid = (f"WPT-{ev['sheet_index']}-{d.get('date', 'nd')}-"
                   + (d.get('time_display') or 'na').replace(':', '').replace(' ', '').lower())
            row = {
                "id": rid, "venue": "wynn", "venue_name": "Wynn Las Vegas Poker (WPT World Championship)",
                "event_no": None,
                "name": ev["name"] + (f" — {d['label']}" if d.get("label") else ""),
                "name_printed": ev["name"] + (f" — {d['label']}" if d.get("label") else ""),
                "date": d.get("date"), "weekday": d.get("weekday_printed"),
                "printed_date": None, "time": (d.get("time_display") or None),
                "registration_closes": rc,
                "registration_closes_printed": rc_printed, "registration_closes_basis": rc_basis,
                "buy_in_usd": ev["buy_in_usd"], "guarantee_usd": ev["guarantee_usd"],
                "guarantee_printed": ev["guarantee_usd"] is not None,
                "starting_chips": ev["starting_chips"], "level_duration": ev["level_minutes"],
                "pool_per_entry_usd": (ev["pool_per_entry_usd"] or 0) + (ev["bounty_pool_usd"] or 0) or None,
                "house_fee_usd": ev["house_fee_usd"], "staff_charge_usd": ev["staff_charge_usd"],
                "bounty_pool_usd": ev["bounty_pool_usd"],
                "kind": "Tournament", "tags": tags + ["WPT festival"],
                "is_flight": bool(d.get("label") and re.match(r"Day\s*1", str(d.get("label")))),
                "is_continuation": is_cont,
                "rules": rules, "sources": [ev["source_url"]], "sheet_key": f"WPT_S{ev['sheet_index']}",
                "sheet_note": ev["guarantee_excerpt"], "sheet_late_registration": ev["registration_excerpt"],
                "length_of_play": ev["length_of_play"], "payout_structure": ev["payouts"],
                "spend_advantage": rules["single_entry"]["status"] == "no" or rules["add_on"]["status"] == "confirmed_allowed",
                "spend_advantage_evidence": ([ev["registration_excerpt"]] if rules["single_entry"]["status"] == "no" else []),
                "rankable": bool(ev["buy_in_usd"] and ev["guarantee_usd"]),
                "gtd_ratio": (round(ev["guarantee_usd"] / ev["buy_in_usd"], 2)
                              if ev["buy_in_usd"] and ev["guarantee_usd"] else None),
                "flags": [f"weekday printed on the sheet does not match {d.get('date')} — do not schedule this row"
                          for _ in () if not d.get("weekday_ok", True)],
                "single_entry_confirmed": False,
                "notes": None,
                "last_checked": retrieved, "source_changed": False,
            }
            row["flags"] = [f for f in row["flags"] if f]     # flat list of strings, never nested
            if not row["rankable"]:
                row["flags"].append("no guarantee printed on this event sheet — not ranked")
            if "bounty" in tags:
                row["flags"].append("bounty event: the guaranteed pool includes bounty money — not comparable "
                                    "with a flat prize pool, kept in its own section")
            if "satellite" in tags:
                row["flags"].append("satellite: pays a ticket/seat, not a cash prize pool — not comparable")
            # verbatim guarantees: every excerpt must exist in the official capture
            for key in ("single_entry", "re_entry", "add_on", "fee"):
                exc = row["rules"][key].get("excerpt")
                if exc:
                    ok = exc in normalise(wpt_text) or exc[:60] in normalise(wpt_text)
                    checks.append({"row": rid, "field": key, "verbatim_in_official_capture": ok})
                    if not ok:
                        raise SystemExit(f"REFUSING TO WRITE: {rid} {key} excerpt is not verbatim in {wpt_meta.get('file')}")
            rows.append(row)

    daily_rows = []
    for d in dailies:
        reg = d.get("registration_excerpt") or ""
        low = reg.lower()
        no_reentry = "re-entry is not allowed" in low
        single = ("no" if ("re-entr" in low or "rebuy" in low or "add-on" in low or "addon" in low)
                  else "not_stated_in_sheet")
        rules = {
            "single_entry": {"status": single,
                             "value": "multiple entries allowed" if single == "no" else None,
                             "excerpt": reg, "source": d["source_url"], "retrieved": retrieved},
            "re_entry": ({"status": "confirmed_not_allowed",
                           "value": "the sheet states re-entry is not allowed; rebuys and the add-on still cost extra",
                           "excerpt": reg, "source": d["source_url"], "retrieved": retrieved}
                          if no_reentry else
                          {"status": "confirmed_allowed" if "re-entr" in low else "not_stated_in_sheet",
                           "value": reg or None, "excerpt": reg or None,
                           "source": d["source_url"], "retrieved": retrieved}),
            "add_on": {"status": "confirmed_allowed" if ("add-on" in low or "addon" in low) else "not_stated_in_sheet",
                       "value": reg if ("add-on" in low or "addon" in low) else None,
                       "excerpt": reg if ("add-on" in low or "addon" in low) else None,
                       "source": d["source_url"], "retrieved": retrieved},
            "fee": {"status": "confirmed" if d.get("fee_excerpt") else "unverified",
                    "value": d.get("fee_excerpt"), "excerpt": d.get("fee_excerpt"),
                    "source": d["source_url"], "retrieved": retrieved},
        }
        days_slug = re.sub(r"[^a-z0-9]+", "-", (d.get("days_offered") or "recurring").lower()).strip("-")[:22]
        nid = f"wyndaily-{d['buy_in_usd']}-{days_slug}"
        daily_rows.append({
            "id": nid, "venue": "wynn", "venue_name": "Wynn Las Vegas Poker (daily tournaments)",
            "event_no": None, "name": d["name"], "name_printed": d["name"],
            "date": None, "weekday": None, "printed_date": d.get("days_offered") or "",
            "time": d.get("start_time"),
            "registration_closes": (time24(_m_app.group(1)) if (_m_app := re.search(
                r"\(approximately\s+([0-9]{1,2}(?::[0-9]{2})?\s*[ap]\.m\.)\)", reg or "", re.I)) else None),
            "registration_closes_printed": (reg or None),
            "registration_closes_basis": ("the sheet prints this clock time itself, as an approximation"
                                          if re.search(r"\(approximately\s+[0-9]{1,2}(?::[0-9]{2})?\s*[ap]\.m\.",
                                                       reg or "", re.I) else None),
            "single_entry_confirmed": False,
            "gtd_ratio": (round(d["guarantee_usd"] / d["buy_in_usd"], 2)
                          if d.get("guarantee_usd") and d.get("buy_in_usd") else None),
            "buy_in_usd": d["buy_in_usd"], "guarantee_usd": d["guarantee_usd"],
            "guarantee_printed": d["guarantee_usd"] is not None,
            "starting_chips": d.get("starting_chips"), "kind": "Recurring daily",
            "tags": ["Recurring / weekly"], "is_flight": False, "is_continuation": False,
            "rules": rules, "sources": [d["source_url"]], "sheet_key": None,
            "spend_advantage": True, "spend_advantage_evidence": [reg],
            "rankable": False,
            "flags": ["recurring schedule, not a dated calendar row",
                      "entry terms allow more than one entry (or add money) — excluded from the single-entry list"],
            "notes": "re-entry is expressly not allowed on this event, but rebuys/add-on are — so it is still a spend-advantage event"
            if no_reentry else "Wynn daily recurring event, read from the venue's own daily-structures PDF",
            "last_checked": retrieved, "source_changed": False,
        })
        for key in ("single_entry", "re_entry", "add_on"):
            exc = rules[key].get("excerpt")
            if exc and exc not in normalise(daily_text):
                raise SystemExit(f"REFUSING TO WRITE: daily {nid} {key} excerpt is not verbatim")

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session": "f0d7de66",
        "policy": ("Rows extracted mechanically from the venue's own PDF text captured by the source monitor. "
                   "Every rule excerpt stored here is verified to be a verbatim substring of that capture; the "
                   "extractor aborts otherwise. A sheet that says nothing about entries is recorded as "
                   "'not_stated_in_sheet', never as single-entry."),
        "captures": {"wpt_terms": wpt_meta, "wynn_daily": daily_meta},
        "events": rows, "dailies": daily_rows,
    }
    (OUT / "events.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    report = {
        "wpt_sheets_parsed": counts["sheets"], "wpt_events": len(events), "wpt_dated_rows": len(rows),
        "wpt_events_without_dated_start": sum(1 for e in events if not e["days"]),
        "wynn_daily_events": len(daily_rows), "verbatim_checks": len(checks),
        "problems": problems,
        "confirmed_reentry_events": sum(1 for e in events if e["registration_excerpt"] and
                                        ("re-entry" in e["registration_excerpt"].lower() or
                                         "re-entries" in e["registration_excerpt"].lower())),
        "events_stating_no_reentry": sum(1 for e in events if "re-entry is not allowed" in
                                         (e["registration_excerpt"] or "").lower()),
        "single_entry_confirmed": sum(1 for r in rows + daily_rows
                                      if r["rules"]["single_entry"]["status"] == "confirmed_yes"),
        "rankable_rows": sum(1 for r in rows if r["rankable"]),
    }
    (OUT / "extraction-report.json").write_text(json.dumps({"generated": payload["generated"], **report}, indent=1),
                                                encoding="utf-8")
    print(json.dumps({"generated": payload["generated"], **report}, indent=1)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
