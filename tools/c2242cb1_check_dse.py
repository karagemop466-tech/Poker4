#!/usr/bin/env python3
"""Re-check the site's Venetian DeepStack IV rows against the official schedule transcription.

Inputs : data/c2242cb1/venetian_official_rows_2026-11-17.json  (official page, row for row)
         data/site-events.json                                  (what the site publishes)
Exit 0 = every official row is published with the same date, time, event number, buy-in
and printed guarantee, and the site publishes no Venetian row the official page does not list.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
official = json.load(open(os.path.join(ROOT, "data/c2242cb1/venetian_official_rows_2026-11-17.json"), encoding="utf-8"))
site = [e for e in json.load(open(os.path.join(ROOT, "data/site-events.json"), encoding="utf-8"))["events"]
        if e["venue"] == "venetian"]


def buy_in(name):
    m = re.search(r"\$([\d,]+)", name)
    return int(m.group(1).replace(",", "")) if m else None


def guarantee(name):
    m = re.search(r"\$([\d,]+)(K|\s*Mill)?\s*GTD", name)
    if not m:
        return None
    v = int(m.group(1).replace(",", ""))
    if m.group(2) == "K":
        return v * 1000
    if m.group(2) and "Mill" in m.group(2):
        return v * 1_000_000
    return v


def key(date, time, event_no):
    return (date, time, event_no)


site_keys = {}
for e in site:
    site_keys.setdefault(key(e["date"], e["time"], e["event_no"]), []).append(e)
off = {}
for date, time, no, name, sheet in official["rows"]:
    off.setdefault(key(date, time, no), []).append((name, sheet))

problems = []
for k, offs in off.items():
    got = site_keys.get(k, [])
    if len(got) != len(offs):
        problems.append(f"{k}: official lists {len(offs)} row(s), site publishes {len(got)}")
        continue
    for (name, _), e in zip(offs, got):
        if buy_in(name) != e.get("buy_in_usd"):
            problems.append(f"{k}: buy-in official {buy_in(name)} vs site {e.get('buy_in_usd')}")
        if guarantee(name) != e.get("guarantee_usd"):
            problems.append(f"{k}: guarantee printed {guarantee(name)} vs site {e.get('guarantee_usd')}")
extra = [k for k in site_keys if k not in off]
for k in extra:
    problems.append(f"{k}: site publishes a Venetian row the official page does not list")

print(f"official rows: {official['row_count']} · site Venetian rows: {len(site)} · "
      f"matched keys: {len(off) - len([p for p in problems if 'official lists' in p])}")
for p in problems:
    print("  PROBLEM:", p)
if problems:
    print("FAIL")
    sys.exit(1)
print("OK: every official Venetian row is published with matching date, time, event number, buy-in and printed guarantee")
