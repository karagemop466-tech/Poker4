#!/usr/bin/env python3
"""Daily schedule feed: pull each Strip poker room's official schedule each morning.

Fetches the official schedule pages listed in SOURCES, extracts the event table
rows (date, time, event #, name), and writes a dated snapshot to
planner/data/schedule-snapshots/<YYYY-MM-DD>.json so changes can be diffed over
time. Run manually or on a schedule via .github/workflows/monitor.yml.

Run:  python3 tools/scrape_schedule.py
Exit 0 if at least one source was fetched; non-zero if every source failed.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "planner", "data", "schedule-snapshots")
UA = "Poker4-ScheduleFeed/1.0 (+official daily schedule)"

# Official schedule pages. Add a room's official schedule URL here as it is verified.
SOURCES = {
    "venetian_dse_iv": "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html",
}

DATE_RE = re.compile(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\w+ \d{1,2}, \d{4}")
ROW_RE = re.compile(r"^\|.*\|$")


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_rows(html):
    """Extract (date, time, event_no, name) from markdown-ish table rows."""
    rows = []
    for line in html.splitlines():
        line = line.strip()
        if not ROW_RE.match(line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        dm = DATE_RE.search(cells[0])
        if not dm:
            continue
        date_str = dm.group(0)
        time = cells[1]
        event_no = cells[2]
        name = re.sub(r"<[^>]+>", "", cells[3]).strip()
        if time and event_no and name:
            rows.append({"date": date_str, "time": time, "event_no": event_no, "name": name})
    return rows


def main():
    today = date.today().isoformat()
    os.makedirs(OUT_DIR, exist_ok=True)
    snapshot = {"fetched": datetime.utcnow().isoformat() + "Z", "sources": {}, "rows": 0}
    ok = 0
    for key, url in SOURCES.items():
        try:
            html = fetch_text(url)
            rows = parse_rows(html)
            snapshot["sources"][key] = {"url": url, "status": "ok", "rows": len(rows)}
            snapshot["rows"] += len(rows)
            ok += 1
            print(f"[ok] {key}: {len(rows)} rows from {url}")
        except Exception as e:  # noqa: BLE001
            snapshot["sources"][key] = {"url": url, "status": "error", "error": repr(e)}
            print(f"[error] {key}: {e}")
    # store the parsed rows keyed by source for diffing
    for key, url in SOURCES.items():
        try:
            snapshot.setdefault("parsed", {})[key] = parse_rows(fetch_text(url))
        except Exception:
            pass
    out = os.path.join(OUT_DIR, f"{today}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    print(f"\nWrote {out} ({snapshot['rows']} rows from {ok}/{len(SOURCES)} sources).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
