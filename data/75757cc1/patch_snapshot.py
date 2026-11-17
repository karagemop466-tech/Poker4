#!/usr/bin/env python3
"""Apply the six corrections proven by check_calendar.py to data/schedule-snapshot.json.

Each change is traced to the official page (dse-nov-2026.html) or the structure sheet it names.
Idempotent: running it twice changes nothing the second time.
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
path = os.path.join(ROOT, "data", "schedule-snapshot.json")
doc = json.load(open(path, encoding="utf-8"))
rows = doc["rows"]
SRC = "https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/dse-nov-2026-schedule.pdf"
NOTE = "corrected 2026-11-17 (session 75757cc1) against the official DSE page and structure sheet"

def find(date, time, ev, name_part=None):
    hits = [r for r in rows if r["date"] == date and r["time"] == time and r["event_no"] == ev
            and (name_part is None or name_part in (r.get("event_name") or "").upper())]
    return hits

# 1. Event 39 Day 2 restart is printed 10:00 AM on the official page; snapshot had it at 7:00 PM
for r in find("2026-12-11", "7:00 PM", 39, "DAY 2 RESTART"):
    r["time"] = "10:00 AM"; r["parse_notes"] = NOTE
# 2. Event 47 Day 2 restart at 1:00 PM was missing
if not find("2026-12-13", "1:00 PM", 47):
    idx = max(i for i, r in enumerate(rows) if r["date"] == "2026-12-13" and r["time"] == "10:10 AM") + 1
    rows.insert(idx, {"parse_notes": NOTE, "registration_closes": None, "date": "2026-12-13", "weekday": "Sunday",
                 "time": "1:00 PM", "event_no": 47,
                 "event_name": "$2,200 NLH POKERATLAS CHAMPIONSHIP TITLE EVENT DAY 2 RESTART",
                 "buy_in_usd": 2200, "guarantee_usd": None, "starting_chips": None, "level_duration": None,
                 "source": SRC, "retrieved": "2026-11-17"})
# 3-4. Event 56 1A/1B ($500K GTD) and 59 1A ($150K GTD): guarantee was dropped by the parser
for date, time, ev, gtd in [("2026-12-17", "10:10 AM", 56, 500000), ("2026-12-17", "6:10 PM", 56, 500000),
                            ("2026-12-20", "11:10 AM", 59, 150000)]:
    for r in find(date, time, ev):
        r["guarantee_usd"] = gtd; r["parse_notes"] = NOTE
# 5-6. level durations printed on the sheets: #36 = 30 min (Event 56 1B), #4 = 40 min (Event 59 1A)
for r in find("2026-12-17", "6:10 PM", 56):
    r["level_duration"] = "30"
for r in find("2026-12-20", "11:10 AM", 59):
    r["level_duration"] = "40"
doc["meta"]["rows"] = len(rows)
doc["meta"]["note"] = (doc["meta"].get("note") or "") + " | 2026-11-17 session 75757cc1: 6 corrections (see parse_notes)."
json.dump(doc, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(path, "a", encoding="utf-8").write("\n")
print("rows now", len(rows))
