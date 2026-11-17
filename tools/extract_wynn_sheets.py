#!/usr/bin/env python3
"""Build data/wynn-official-<captured-date>.json from Wynn's own captured structure PDFs.

Why this exists
---------------
Wynn publishes its tournament terms as PDFs, not as a table the repo's calendar parser can
read.  The c07371e3 capture of those sheets recorded buy-in, guarantee and a short re-entry
note but left the fee split, the starting stack, the level length and the registration
deadline blank — which is why none of those rows could be ranked (ranking needs the total
entry fee *and* the guarantee confirmed from an official page).

This tool re-reads the venue's own text capture and lifts, for each event, only the sentences
the sheet actually prints:

    Entry Fee: $600 Buy-in = $510 (Tournament Prize Pool) + $65 (Tournament Fee)
               + $25 (Poker Staff Service Charge)
    Players will start with 40,000 in tournament chips
    Length of Play: Day 1A-E: 30 minutes per level until 12.5% or less of the field remains.
    Registration: Unlimited re-entry ... / One (1) Entry and One (1) re-entry ... /
                  Four (4) Entries maximum.

A field the sheet does not print stays null; nothing here is computed from another event or
inferred from a similar row.  Each value carries the sentence it came from, so the site can
show the excerpt and the retrieval date next to the number, and a human can re-open the PDF
at the recorded line and check it.

Run:
    python3 tools/extract_wynn_sheets.py            # writes data/wynn-official-<date>.json
    python3 tools/extract_wynn_sheets.py --check    # exits 1 if the committed file is stale

Inputs are the captures under data/raw/ that tools/sync_official_sources.py refreshes:

    data/raw/wynn-wpt-terms.txt          WPT World Championship Structures PDF
    data/raw/wynn-daily-structures.txt   All Daily Structures PDF

The capture banner (first line of each file) records the fetch timestamp and the sha256 of
the PDF, and that timestamp is what the output's `retrieved` field reports.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data"

DAILY_PDF = "https://cdn.wynnresorts.com/image/upload/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf"
WPT_PDF = "https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf"
ROOM_PAGE = "https://www.wynnlasvegas.com/casino/poker"

# WPT rows the site carries (dates + event name as captured in data/c07371e3/wynn_wpt.csv)
# mapped to the sheet that describes them.  Mapping is by hand, not by fuzzy title matching:
# the PDF prints 69 event sheets and several share a buy-in, so an ambiguous match would put
# one event's fee split on another event's row.
WPT_SHEETS: dict[str, str] = {
    "Nov 27|WPT NLH $600": "$600 No Limit Hold'em $400,000 GUARANTEE",
    "Nov 27|WPT TORSE $600": "$600 TORSE",
    "Nov 28 & Dec 20|WPT Mixed Triple Draw $600": "$600 Mixed Triple Draw (A-5, 2-7, Badugi)",
    "Nov 30 - Dec 4|WPT NLH $800": "$800 No Limit Hold'em $1,000,000 GUARANTEE",
    "Nov 30|WPT Limit Omaha 8 $600": "$600 Limit Omaha 8",
    "Dec 1|WPT Omaha 8 / Stud 8 $600": "$600 Limit Omaha 8/Stud 8",
    "Dec 1|WPT PLO $1,100": "$1,100 PLO",
    "Dec 3 - 5|WPT NLH $1,600": "$1,600 No Limit Hold'em $1,000,000 GUARANTEE",
    "Dec 4|WPT HORSE $600": "$600 HORSE",
    "Dec 5 - 12|WPT Prime Championship $1,100 ($5M GTD)": "$1,100 WPT Prime Championship $5,000,000 GUARANTEE",
    "Dec 5 - 21 (nightly)|WPT NLH Turbo $600 ($50K GTD nightly)": "$600 NLH Turbo $50,000 GUARANTEE",
    "Dec 6 - 7|WPT PLO Mystery Bounty $1,600 ($500K GTD)": "$1,600 PLO Mystery Bounty $500,000 GUARANTEE",
    "Dec 10 - 13|Super Gold Million $400 ($3M GTD)": "$400 Super Gold Million",
    "Dec 13 - 21|WPT World Championship $10,400 (+$1M added)": "$10,400 WPT World Championship",
}

DAILY_SHEETS: dict[str, str] = {
    "Mon-Thu daily|12:00 PM": "$200 NLH",
    "Fri|12:00 PM": "$240 NLH Rebuy & Add-on",
    "Sat & Sun daily|12:00 PM": "$200 NLH",
    "Nightly|6:00 PM": "$160 NLH",
}

MONEY = r"\$[\d,]+(?:\.\d+)?"
TIME = r"\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.)"
DAYWORD = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
MONTH = r"(?:November|December|January|February|March|April|May|June|July|August|September|October)"
SPLIT_RE = re.compile(
    rf"Entry Fee: ({MONEY}) Buy-in = ({MONEY}) \((?:Tournament|[^)]*Mystery Bounty) Prize Pool\) \+ "
    rf"(?:{MONEY} \(Mystery Bounty Prize Pool\) \+ )?({MONEY}) \(Tournament Fee\) \+ ({MONEY}) \(Poker Staff Service Charge\)", re.I)
BOUNTY_NOTE = re.compile(rf"{MONEY} from the Tournament Prize Pool will fund the Mystery Bounty Prize Pool\.", re.I)
GTD_RE = re.compile(rf"{MONEY}\s+(?:GUARANTEE|Guaranteed)", re.I)
ADDED_RE = re.compile(rf"({MONEY})\s+ADDED", re.I)
STACK_RE = re.compile(r"Players will start with ([\d,]+) in [Tt]ournament chips")
LEVEL_RE = re.compile(r"(\d+) minutes per level")
PER_TABLE_RE = re.compile(r"[Tt]ables? (?:will be )?play(?:ed)? (\d+)[- ](?:handed|hand)")
FLIGHT_RE = re.compile(rf"((?:Day 1[A-F]|Day [1-5]|Final Table):\s*)?({DAYWORD},? {MONTH} \d{{1,2}}, 2026,? at {TIME})", re.I)
REG_RE = re.compile(r"Registration:\s*(.{0,900}?)(?=Starting Stack:|Length of Play:|Payouts:|Players Per Table:|Breaks:|$)", re.S)
DAILY_FEE_RE = re.compile(
    rf"The (?P<buy>{MONEY}) Entry Fee will be distributed as follows: (?P<fee>{MONEY}) for the Tournament fee, "
    rf"(?P<staff>{MONEY}) for the poker staff service charge, and (?P<pool>{MONEY}) for the Tournament prize pool\.", re.I)
FRIDAY_FEE_RE = re.compile(
    rf"The Tournament entry fee is (?P<buy>{MONEY})(?:[^.]{{0,60}})?of which (?P<fee>{MONEY}) will be withheld for the "
    rf"Tournament fee and (?P<staff>{MONEY}) as a service charge for poker staff\. (?P<pool>{MONEY}) of each Entry Fee and "
    rf"rebuy will fund the Tournament prize pool\.", re.I)
SUSP_RE = re.compile(r"The Tournament will be offered ([^.]{0,120}?) and may be suspended[^.]{0,160}\.", re.I)
LEVEL_NUM = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
             "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12"}
OFFER_RE = re.compile(r"until the start of level (\d+|[a-z]+)(?:\s*\((\d+)\))?((?:\s*\(approximately [^)]+\))?)", re.I)


TERMS_AT = "TERMS AND CONDITIONS"


def norm(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]


def capture_meta(lines: list[str]) -> dict:
    m = re.search(r"captured\s+(\S+)\s+from\s+(\S+)\s+\(sha256\s+([0-9a-f]+)\)", lines[0])
    if not m:
        return {}
    return {"captured_at": m.group(1), "url": m.group(2), "sha256": m.group(3),
            "retrieved": m.group(1)[:10]}


def sections(lines: list[str]) -> list[tuple[int, str, str]]:
    """(line index, title text, body text) for every '... TERMS AND CONDITIONS' sheet."""
    hits = [i for i, l in enumerate(lines) if l.upper().endswith(TERMS_AT)]
    out = []
    for n, i in enumerate(hits):
        end = hits[n + 1] if n + 1 < len(hits) else len(lines)
        body_rows = [x for x in lines[i:end] if x and not x.startswith("|")]
        title_rows = [x for x in lines[max(0, i - 4):i] if x and not x.startswith("|")]
        out.append((i, " ".join(title_rows), " ".join(body_rows)))
    return out


def find_sheet(secs, needle: str, avoid: str | None = None):
    want = needle.replace("\u2019", "'").lower()
    for i, title, body in secs:
        t = title.replace("\u2019", "'").lower()
        if t.rstrip().endswith(want) or f" {want} " in f" {t} ":
            if avoid and avoid.lower() in body[:600].lower():
                continue
            return i, title, body
    return None


def _money(txt: str | None) -> int | None:
    if not txt:
        return None
    digits = re.sub(r"[^\d]", "", txt)
    return int(digits) if digits else None


def comma(n: int | None) -> str:
    return f"${n:,}" if n is not None else "—"


def _money(txt: str | None) -> int | None:
    if not txt:
        return None
    digits = re.sub(r"[^\d]", "", txt)
    return int(digits) if digits else None


def comma(n: int | None) -> str:
    return f"${n:,}" if n is not None else "—"


def numbered_clause(text: str, anchor: str, span: int = 560) -> str | None:
    """Return the whole numbered clause an anchor phrase sits in.

    Wynn's daily sheets number their terms ("4. Registration and re-entries will be available
    until the start of level 9 (approximately 4:30 p.m.).") and the abbreviations inside them
    contain periods, so the text cannot be split into sentences on "." — the clause boundary is
    the next "N. " marker instead.
    """
    m = re.search(anchor, text, re.I)
    if not m:
        return None
    begin = text.rfind(". ", max(0, m.start() - 60), m.start())
    begin = begin + 2 if begin >= 0 else max(0, m.start() - 40)
    tail = text[m.end():m.end() + span]
    e = re.search(r"\s\d{1,2}\.\s", tail)
    end = m.end() + e.start() if e else min(len(text), m.end() + span)
    clipped = end >= min(len(text), m.end() + span) - 1
    out = re.sub(r"\s+", " ", text[begin:end]).strip(" .")
    if not out:
        return None
    out = out.replace("add- on", "add-on").replace("two- day", "two-day").replace("re- entry", "re-entry")
    return out + (" […]" if clipped else "")


def parse_row(i: int, title: str, body: str, captured: dict) -> dict:
    """Lift from one sheet only the sentences the sheet itself prints."""
    row: dict = {"sheet_line": i, "retrieved": captured.get("retrieved"), "captured_at": captured.get("captured_at")}
    quotes: dict[str, str] = {}
    head = re.sub(r"\s+", " ", title).strip()

    # guarantee / added pool: the heading and the first sentence are the only two places a
    # guarantee is printed, so search there and never in the blind-level table that sits
    # between two sheets in the same PDF
    front = head + " " + body[:260]
    gtd = GTD_RE.search(head) or GTD_RE.search(body[:260])
    if gtd:
        row["guarantee_usd"] = _money(gtd.group(0))
        row["guarantee_printed"] = gtd.group(0).strip()
    added = ADDED_RE.search(front)
    if added:
        row["added_pool_printed"] = added.group(0).strip()
    if "guarantee_usd" in row:
        amt_txt = comma(row["guarantee_usd"])
        sent = re.search(rf"This [^.\n]{{0,150}}?{re.escape(amt_txt)} (?:GUARANTEE|Guaranteed?)[^.\n]{{0,150}}?(?:event|declared)\.", body, re.I)
        quotes["guarantee"] = re.sub(r"\s+", " ", sent.group(0)).strip() if sent else row["guarantee_printed"]
    elif added:
        sent = re.search(r"[^.]{0,80}\$1,000,000 in [^.]{0,240}\.", body, re.I)
        quotes["guarantee"] = re.sub(r"\s+", " ", (sent.group(0) if sent else added.group(0))).strip()

    # the fee split, printed the same way on every sheet
    split = SPLIT_RE.search(body) or DAILY_FEE_RE.search(body) or FRIDAY_FEE_RE.search(body)
    if split:
        if "pool" in (split.re.groupindex or {}):
            gd = split.groupdict()
            buy, pool, fee, staff = (_money(gd.get("buy")), _money(gd.get("pool")),
                                     _money(gd.get("fee")), _money(gd.get("staff")))
        else:
            buy, pool, fee, staff = (_money(g) for g in split.groups())
        row.update({"buy_in_usd": buy, "pool_per_entry_usd": pool, "fee_usd": fee, "staff_charge_usd": staff})
        bounty = BOUNTY_NOTE.search(body)
        extra = (" " + bounty.group(0).strip()) if bounty else ""
        if bounty:
            row["bounty_note"] = bounty.group(0).strip()
        row["fee_text"] = (f"{comma(fee)} tournament fee + {comma(staff)} poker-staff service charge; "
                          f"{comma(pool)} of the {comma(buy)} reaches the prize pool{extra}")
        m = re.search(r"Entry Fee:[^.]*\(Poker Staff Service Charge\)", body)
        quotes["fee"] = re.sub(r"\s+", " ", (m.group(0) if m else split.group(0))).strip()

    stack = STACK_RE.search(body)
    if stack:
        row["starting_chips"] = int(stack.group(1).replace(",", ""))
        quotes["chips"] = re.sub(r"\s+", " ", stack.group(0)).strip()
    lv = LEVEL_RE.findall(body)
    if lv:
        uniq = list(dict.fromkeys(lv))
        row["level_minutes"] = uniq[0] if len(uniq) == 1 else " / ".join(f"{v}-min" for v in uniq)
        lp = re.search(r"Length of Play:(.{0,300}?)(?=Breaks:|Players Per Table:|$)", body, re.S)
        if lp:
            quotes["levels"] = ("Length of Play: " + re.sub(r"\s+", " ", lp.group(1)).strip()).replace(": ", ": ")
    tbl = PER_TABLE_RE.search(body)
    if tbl:
        row["players_per_table"] = int(tbl.group(1))
    fl = [(re.sub(r"\s+", " ", (a or "")).strip(), re.sub(r"\s+", " ", b).strip())
          for a, b in FLIGHT_RE.findall(body[:4200])]
    if fl:
        row["dates_printed"] = [f"{a} {b}".replace(": ", ": ").strip() for a, b in dict.fromkeys(fl)][:10]

    # registration / re-entry / add-on, from the sheet's own clause
    reg = REG_RE.search(body)
    text = re.sub(r"\s+", " ", reg.group(1)).strip() if reg else numbered_clause(
        body, r"Registration(?:, rebuys and add-ons|, re-entries(?:, and one \(1\) add-on per entry)?| and re-entries)? will be available")
    chips_clause = numbered_clause(body, r"Players will start with [\d,]+ in Tournament chips") or ""
    if text:
        quotes["re_entry"] = text if text.lower().startswith("registration") else "Registration: " + text
        low = text.lower()
        cut = OFFER_RE.search(text)
        num = approx = None
        if cut:
            word = cut.group(1)
            num = cut.group(2) or (word if word.isdigit() else LEVEL_NUM.get(word.lower()))
            approx = (cut.group(3) or "").strip()
            if num:
                row["registration_end"] = f"start of level {num}" + (f" {approx}" if approx else "")
        cap = re.search(r"[A-Z][^.]{0,60}[Ee]ntries maximum", text)
        buys_more = bool(re.search(r"rebuy|add-on|addon|re-purchase", text + " " + chips_clause, re.I))
        if cap:
            row["re_entry"] = f"entries capped by the sheet: {cap.group(0)}"
            row["entry_limit_printed"] = cap.group(0).strip()
            row["single_entry_status"] = "no"
        elif "not allowed" in low:
            row["re_entry"] = ("re-entry not allowed; the sheet still prices further buy-ins (rebuy/add-on)"
                              if buys_more else "re-entry not allowed")
            row["single_entry_status"] = "no" if buys_more else "unverified"
        elif re.search(r"one \(1\) entry and one \(1\) re-entry", low):
            row["re_entry"] = "one entry plus one re-entry per starting flight, until the sheet's cutoff"
            row["single_entry_status"] = "no"
        elif "unlimited re-entry" in low or "re-entries" in low:
            row["re_entry"] = "unlimited re-entry" + (f" until the start of level {num}" if num else "") + \
                              " (the sheet's own cutoff)"
            row["single_entry_status"] = "no"
        elif "re-entry" in low:
            row["re_entry"] = text.split(". ")[0].rstrip(".")
            row["single_entry_status"] = "no"
        ao = numbered_clause(body, r"(?:One \(1\) \$[\d,]+ add-?on|Unlimited \$[\d,]+ rebuys)")
        if ao:
            row["add_on"] = ao
            quotes["add_on"] = ao
        elif re.search(r"add-on|addon|rebuy", low):
            row["add_on"] = text
    susp = SUSP_RE.search(body)
    if susp:
        row["suspension"] = re.sub(r"\s+", " ", susp.group(0)).strip()
        quotes["suspension"] = row["suspension"]
    if quotes:
        row["quotes"] = quotes
    return row


def daily_rows(text: str, captured: dict) -> dict:
    """Wynn's daily PDF holds one numbered-terms block per event in a single file.

    The blocks are split on the venue's own "DAILY TOURNAMENT" banner and matched to a site
    row by the sentence naming the days it runs on ("The Tournament will be offered
    Monday-Thursday ..."), so a row can never inherit another day's fee split.
    """
    rows: dict[str, dict] = {}
    flat_all = re.sub(r"\s+", " ", text)
    wanted = {
        "Mon-Thu daily|12:00 PM": "offered Monday-Thursday",
        "Fri|12:00 PM": "offered Friday",
        "Sat & Sun daily|12:00 PM": "offered Saturday & Sunday",
        "Nightly|6:00 PM": "offered Nightly Monday-Sunday",
    }
    for key, needle in wanted.items():
        m = re.search(re.escape(needle), flat_all)
        if not m:
            continue
        start = flat_all.rfind("DAILY TOURNAMENT", 0, m.start())
        start = 0 if start < 0 else start
        nxt = flat_all.find("DAILY TOURNAMENT", m.end())
        block = flat_all[start:nxt if nxt > 0 else len(flat_all)]
        if "TERMS AND CONDITIONS" in block:
            head, rest = block.split("TERMS AND CONDITIONS", 1)
            # the blind-level table between the banner and the sheet heading is noise: it is
            # dropped so a search cannot mistake "26 100,000 200,000" for a fee line
            head = re.sub(r"\d+ [\d,]+ [\d,]+(?: [\d,]+)*", " ", head).strip()
            block = head + " " + rest.strip()
        else:
            block = block[:160]
        head = block.split("TERMS AND CONDITIONS")[0].strip() if "TERMS AND CONDITIONS" in block else block[:140]
        line_no = flat_all[:flat_all.find(needle)].count(" ")
        r = parse_row(line_no, head, block, captured)
        r["sheet_title_printed"] = re.sub(r"\s+", " ", head)[-90:]
        rows[key] = r
    return rows


def build() -> dict:
    wpt_txt = (RAW / "wynn-wpt-terms.txt").read_text(encoding="utf-8", errors="replace")
    daily_txt = (RAW / "wynn-daily-structures.txt").read_text(encoding="utf-8", errors="replace")
    wpt_cap = capture_meta(norm(wpt_txt))
    daily_cap = capture_meta(norm(daily_txt))
    secs = sections(norm(wpt_txt))
    rows: dict[str, dict] = {}
    for key, needle in WPT_SHEETS.items():
        hit = find_sheet(secs, needle)
        if not hit:
            print(f"warn: no sheet matched for {key}", file=sys.stderr)
            continue
        i, title, body = hit
        r = parse_row(i, title, body, wpt_cap)
        r["sources"] = [WPT_PDF, ROOM_PAGE]
        r["sheet_title_printed"] = re.sub(r"\s+", " ", title).strip()[-90:]
        rows[key] = r
    for key, r in daily_rows(daily_txt, daily_cap).items():
        r["sources"] = [DAILY_PDF, ROOM_PAGE]
        rows[key] = r
    return {
        "meta": {
            "generated_by": "tools/extract_wynn_sheets.py",
            "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "retrieved": max(wpt_cap.get("retrieved", ""), daily_cap.get("retrieved", "")),
            "rule": "Only sentences the venue's own sheet prints. A value the sheet does not state stays absent here, and stays blank and flagged on the site.",
            "wpt_capture": wpt_cap,
            "daily_capture": daily_cap,
            "sheet_count_wpt_pdf": len(secs),
            "notes": [
                "The room page states the dailies run twice a day outside event windows and that the fields total $200,000 in weekly guarantees.",
                "Daily sheets carry their own suspension clause; the WPT World Championship runs Nov 27 - Dec 21, 2026 in the same room, so a daily row is not dependable inside that window.",
                "Clause 3 of the daily general terms places the room in Encore: \"Players will register in the Wynn Las Vegas Poker Room, located in Encore at Wynn Las Vegas.\"",
            ],
        },
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare with the committed file instead of writing")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    doc = build()
    stamp = doc["meta"]["retrieved"] or dt.date.today().isoformat()
    out = pathlib.Path(a.out) if a.out else OUT_DIR / f"wynn-official-{stamp}.json"
    payload = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if a.check:
        have = out.read_text(encoding="utf-8") if out.exists() else ""
        same = json.loads(have)["rows"] == doc["rows"] if have else False
        if not same:
            print(f"stale: {out.name} does not match the capture", file=sys.stderr)
            return 1
        print(f"current: {out.name} matches the capture ({len(doc['rows'])} rows)")
        return 0
    out.write_text(payload, encoding="utf-8")
    print(f"wrote {out} — {len(doc['rows'])} rows (WPT sheets in PDF: {doc['meta']['sheet_count_wpt_pdf']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
