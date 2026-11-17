#!/usr/bin/env python3
"""Line-by-line check: every official Venetian calendar row transcribed on a given date
   must agree with the stored schedule table (date, time, event #, structure sheet,
   buy-in, guarantee). Run: python3 tools/check_rows.py [fixture.tsv]
"""
import csv, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data/08f07d1d/official_rows_2026-11-17.tsv")
CSVF = os.path.join(ROOT, "data/c07371e3/venetian_deepstack_iv.csv")

def num(s):
    return int(float(str(s).replace(",", "").replace("$", ""))) if s not in (None, "", "None") else None

def main():
    rows = list(csv.DictReader(open(CSVF, encoding="utf-8")))
    idx = {}
    for r in rows:
        idx.setdefault((r["date"], r["time"], r["event_no"]), []).append(r)
    problems, checked = [], 0
    for line in open(FIX, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        d, t, ev, name, sheet = line.split("\t")
        checked += 1
        got = idx.get((d, t, ev))
        if not got:
            problems.append(f"MISSING from table: {d} {t} #{ev}")
            continue
        g = got[0]
        gs = re.search(r"structure_(\d+)\.pdf", g["structure_pdf"])
        gs = gs.group(1) if gs else None
        if gs != sheet:
            problems.append(f"SHEET mismatch {d} {t} #{ev}: table={gs} official={sheet}")
        lb = re.search(r"\$([\d,]+)", name)
        if lb and num(lb.group(1)) != num(g["buy_in_usd"]) and "Day 2" not in name and "Day 3" not in name:
            problems.append(f"BUY-IN mismatch {d} #{ev}: table={g['buy_in_usd']} official={lb.group(1)}")
        lg = re.search(r"\$([\d,.]+)\s*(K|Mill)", name)
        if lg:
            val = int(float(lg.group(1).replace(",", "")) * (1000 if lg.group(2) == "K" else 1_000_000))
            if num(g["guarantee_usd"]) != val:
                problems.append(f"GUARANTEE mismatch {d} #{ev}: table={g['guarantee_usd']} official={val}")
        elif num(g["guarantee_usd"]):
            problems.append(f"GUARANTEE present in table but not in official listing {d} #{ev}")
    report = {"fixture": os.path.basename(FIX), "official_rows_checked": checked,
              "table_rows": len(rows), "problems": problems,
              "verdict": "OK - every checked official row agrees" if not problems else "PROBLEMS FOUND"}
    print(json.dumps(report, indent=1))
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main())
