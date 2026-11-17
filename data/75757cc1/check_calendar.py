#!/usr/bin/env python3
"""Compare data/schedule-snapshot.json (the feed that feeds the root tournaments table) with the
94-row official calendar transcription and with the level duration printed on each structure sheet.

Exit 0 only when every snapshot row matches the page on date, time, event number, buy-in and
guarantee, and every printed level duration matches its sheet. Transcription source:
https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html
Level durations: each structure PDF named in the TSV's structure_no column (read 2026-11-17).
"""
import csv, json, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
page = list(csv.DictReader(open(os.path.join(HERE, "official_calendar_2026-11-17.tsv"), encoding="utf-8"), delimiter="\t"))
snap = json.load(open(os.path.join(ROOT, "data", "schedule-snapshot.json"), encoding="utf-8"))["rows"]

# level duration (minutes) printed on each structure sheet, as read on 2026-11-17 (None = mixed/not single)
SHEET_LEVEL = {1: 30, 2: 40, 3: 40, 4: 40, 5: 30, 6: 30, 7: 30, 8: 30, 9: 30, 10: 40, 11: 30, 12: 40,
               13: 30, 14: 20, 15: 30, 16: 30, 17: 30, 18: None, 19: 20, 20: 40, 21: 40, 22: 30, 23: 30,
               24: 20, 25: 15, 26: 30, 27: 30, 28: 30, 29: 30, 30: 30, 31: 30, 32: 40, 33: 30, 34: 30,
               35: 40, 36: 30, 37: 30}

def key(d, t, n):
    return (d, t.strip().upper(), int(n))

pk = {key(r["date"], r["time"], r["event_no"]): r for r in page}
problems = []
sk = collections.Counter()
for s in snap:
    k = key(s["date"], s["time"], s["event_no"])
    sk[k] += 1
    if k not in pk:
        problems.append(f"snapshot row not on official page: {k} '{s.get('event_name')}'")
        continue
    p = pk[k]
    if s.get("buy_in_usd") is not None and int(s["buy_in_usd"]) != int(p["buy_in_usd"]):
        problems.append(f"buy-in differs {k}: snapshot {s['buy_in_usd']} page {p['buy_in_usd']}")
    if int(p["guarantee_usd"]) and (s.get("guarantee_usd") or 0) != int(p["guarantee_usd"]):
        problems.append(f"guarantee differs {k}: snapshot {s.get('guarantee_usd')} page {p['guarantee_usd']}")
    lvl = SHEET_LEVEL.get(int(p["structure_no"]))
    if lvl and s.get("level_duration") not in (None, str(lvl)):
        problems.append(f"level duration differs {k}: snapshot {s.get('level_duration')} sheet #{p['structure_no']} {lvl}")
for k, n in sk.items():
    if n > 1:
        problems.append(f"duplicate snapshot key {k} x{n} (two different printed rows share one date/time/event)")
for k in pk:
    if sk.get(k, 0) == 0:
        problems.append(f"official row missing from snapshot: {k}")
print(f"official rows {len(pk)} · snapshot rows {len(snap)} · problems {len(problems)}")
for line in problems:
    print(" -", line)
sys.exit(1 if problems else 0)
