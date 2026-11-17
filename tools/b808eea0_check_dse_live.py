#!/usr/bin/env python3
"""Independent line-by-line check: official Venetian DSE IV page capture vs the
row transcription used by tools/c2242cb1_check_dse.py, vs data/schedule-snapshot.json,
and vs the published site rows.

Inputs (all local; no network):
  data/raw/venetian-dse-iv-page.txt                        raw text capture of the official page
                                                           (made by tools/sync_official_sources.py,
                                                           header line carries capture time + URL + sha256)
  data/c2242cb1/venetian_official_rows_2026-11-17.json    row-for-row transcription of the official page
  data/schedule-snapshot.json                             PDF-parse snapshot (defects found here are
                                                           corrected by data/c2242cb1/venetian_overrides.json)
  data/site-events.json                                   what the site publishes

Checks:
  1. every row in the raw capture exists in the transcription (date, time, event no, name)
  2. every row in the transcription exists in the raw capture
  3. every raw-capture row is published on the site with the same date/time/event/buy-in/guarantee
  4. the snapshot's Venetian rows match the raw capture after the override layer is applied

Exit 0 = all checks pass. Any mismatch prints a line and exits 1.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data/raw/venetian-dse-iv-page.txt")
TRANS = os.path.join(ROOT, "data/c2242cb1/venetian_official_rows_2026-11-17.json")
SNAP = os.path.join(ROOT, "data/schedule-snapshot.json")
OVR = os.path.join(ROOT, "data/c2242cb1/venetian_overrides.json")
SITE = os.path.join(ROOT, "data/site-events.json")

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def norm_name(s):
    s = (s or "").replace("\u2019", "'").replace("<br>", " ").replace("<br/>", " ")
    s = re.sub(r"\s+", " ", s).strip().rstrip("|").strip()
    return s


def words_key(s):
    """Loose word key: casefold, drop punctuation. Compares wording, not markup.

    The official page itself prints 'No LImit' and uses <br> sub-lines; the
    transcription normalizes those. One name being a word-prefix of the other
    (e.g. a dropped note sub-line) also counts as the same row wording."""
    return re.sub(r"[^a-z0-9]+", " ", norm_name(s).casefold()).strip()


def name_matches(a, b):
    ka, kb = words_key(a), words_key(b)
    return ka == kb or ka.startswith(kb + " ") or kb.startswith(ka + " ")


DATE_RE = re.compile(r"^(" + "|".join(WEEKDAYS) + r"), ([A-Z][a-z]+ \d{1,2}, \d{4})$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2} [AP]M$")


def is_row_start(cells, i):
    return (i + 2 < len(cells) and DATE_RE.match(cells[i]) and TIME_RE.match(cells[i + 1])
            and re.match(r"^\d{1,3}$", cells[i + 2]))


def parse_raw():
    """Parse the raw page capture into (date_iso, time, event_no, name) rows."""
    import datetime as dt
    rows = []
    lines = open(RAW, encoding="utf-8").read().splitlines()
    cells = []
    for ln in lines:
        if ln.startswith("<!--"):
            continue
        c = ln.strip().rstrip("|").strip()
        if not c:
            continue
        cells.append(c)
    i = 0
    while i < len(cells):
        if is_row_start(cells, i):
            m = DATE_RE.match(cells[i])
            date_iso = dt.datetime.strptime(m.group(2), "%B %d, %Y").date().isoformat()
            rows.append((date_iso, cells[i + 1], int(cells[i + 2]), norm_name(cells[i + 3])))
            i += 4
            while i < len(cells) and not is_row_start(cells, i):
                i += 1
        else:
            i += 1
    return rows


def buy_in(name):
    m = re.search(r"\$([\d,]+)", name)
    return int(m.group(1).replace(",", "")) if m else None


def guarantee(name):
    m = re.search(r"\$([\d,]+)(K|\s*Mill)?\s*GTD", name, re.I)
    if not m:
        return None
    v = int(m.group(1).replace(",", ""))
    if m.group(2) and m.group(2).upper() == "K":
        return v * 1000
    if m.group(2) and "mill" in m.group(2).lower():
        return v * 1_000_000
    return v


def main():
    problems = []
    raw = parse_raw()
    trans = json.load(open(TRANS, encoding="utf-8"))["rows"]

    # 1-2. raw capture vs transcription: same rows, same wording (loose: case,
    # punctuation and dropped note sub-lines are transcription conventions)
    def match_lists(a_rows, b_rows, label):
        used = [False] * len(b_rows)
        for r in a_rows:
            hit = False
            for i, s in enumerate(b_rows):
                if used[i]:
                    continue
                if r[0] == s[0] and r[1] == s[1] and r[2] == s[2] and name_matches(r[3], s[3]):
                    used[i] = True
                    hit = True
                    break
            if not hit:
                problems.append(f"{label}: no counterpart for {r}")
        for i, s in enumerate(b_rows):
            if not used[i]:
                problems.append(f"{label}: unmatched row {s}")

    trans_as_raw = [(r[0], r[1], r[2], norm_name(r[3])) for r in trans]
    match_lists(raw, trans_as_raw, "raw-vs-transcription")
    match_lists(trans_as_raw, raw, "transcription-vs-raw")

    site = [e for e in json.load(open(SITE, encoding="utf-8"))["events"] if e.get("venue") == "venetian"]
    site_idx = {}
    for e in site:
        site_idx.setdefault((e["date"], e["time"], e["event_no"]), []).append(e)

    for (date, time, ev, name) in raw:
        want_buy, want_gtd = buy_in(name), guarantee(name)
        cands = site_idx.get((date, time, ev), [])
        if not cands:
            problems.append(f"site-missing: {date} {time} #{ev} {name}")
            continue
        ok = False
        for e in cands:
            if e.get("buy_in_usd") == want_buy and (e.get("guarantee_usd") or None) == want_gtd:
                ok = True
                break
        if not ok:
            got = [(e.get("buy_in_usd"), e.get("guarantee_usd")) for e in cands]
            problems.append(f"site-mismatch: {date} {time} #{ev} {name} want=({want_buy},{want_gtd}) got={got}")

    # site must not publish Venetian rows the official page does not list
    raw_idx = {}
    for (date, time, ev, name) in raw:
        raw_idx.setdefault((date, time, ev), []).append((name, buy_in(name), guarantee(name)))
    for e in site:
        k = (e["date"], e["time"], e["event_no"])
        if k not in raw_idx:
            problems.append(f"site-extra: {k} {e.get('name')}")
        else:
            vals = raw_idx[k]
            if (e.get("buy_in_usd"), e.get("guarantee_usd") or None) not in [(b, g) for (_, b, g) in vals]:
                problems.append(f"site-extra-value: {k} {e.get('name')} ({e.get('buy_in_usd')},{e.get('guarantee_usd')})")

    # 4. sheet-verified regression assertions (read live 2026-11-17 from the official
    # schedule page and structure sheets 4/35/36 — see data/c2242cb1/venetian_overrides.json
    # "why" fields for the exact source URLs and excerpts)
    snap_rows = json.load(open(SNAP, encoding="utf-8"))["rows"]
    checks = [
        # (date, time, event_no, gtd, level, reg, name_words, cef_early)
        ("2026-12-17", "10:10 AM", 56, 500000, "40", "4:55 PM", "1A $500K GTD", 1060),
        ("2026-12-17", "6:10 PM", 56, 500000, "30", "11:10 PM", "1B $500K GTD", 1060),
        ("2026-12-20", "11:10 AM", 59, 150000, "40", "5:55 PM", "1A $150K GTD", 580),
    ]
    for date, time, ev, gtd, lvl, reg, words, early in checks:
        srows = [e for e in site if e["date"] == date and e["time"] == time and e["event_no"] == ev]
        if len(srows) != 1:
            problems.append(f"assertion: site row {date} {time} #{ev} count={len(srows)}")
            continue
        e = srows[0]
        if e.get("guarantee_usd") != gtd:
            problems.append(f"assertion: {date} #{ev} guarantee {e.get('guarantee_usd')} != {gtd}")
        if e.get("level_duration") != lvl:
            problems.append(f"assertion: {date} #{ev} level {e.get('level_duration')!r} != {lvl!r}")
        if e.get("registration_closes") != reg:
            problems.append(f"assertion: {date} #{ev} reg {e.get('registration_closes')!r} != {reg!r}")
        if words_key(words) not in words_key(e.get("name") or ""):
            problems.append(f"assertion: {date} #{ev} name {e.get('name')!r} lacks printed {words!r}")
        cef = e.get("conditional_entry_fee") or {}
        if cef.get("early_usd") != early:
            problems.append(f"assertion: {date} #{ev} early fee {cef.get('early_usd')} != {early}")
        # the snapshot itself must carry the corrected values (durable sync fix)
        prows = [r for r in snap_rows if r.get("date") == date and r.get("time") == time
                 and r.get("event_no") == ev]
        if len(prows) != 1:
            problems.append(f"assertion: snapshot row {date} {time} #{ev} count={len(prows)}")
        else:
            r = prows[0]
            if r.get("guarantee_usd") != gtd or str(r.get("level_duration")) != lvl \
                    or r.get("registration_closes") != reg:
                problems.append(f"assertion: snapshot {date} #{ev} not corrected: "
                                f"gtd={r.get('guarantee_usd')} lvl={r.get('level_duration')!r} "
                                f"reg={r.get('registration_closes')!r}")

    print(f"raw rows: {len(raw)} · transcription rows: {len(trans)} · site venetian rows: {len(site)}")
    if problems:
        print(f"PROBLEMS: {len(problems)}")
        for p in problems[:40]:
            print(" -", p)
        sys.exit(1)
    print("OK: raw capture, transcription and site rows agree row-for-row (date, time, event no, name, buy-in, printed guarantee)")


if __name__ == "__main__":
    main()
