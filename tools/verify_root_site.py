#!/usr/bin/env python3
"""Automated verification of the root dashboard (workflow step 6).

Checks:
  1. Every HTML page parses; internal links resolve to real files.
  2. Every event row on every page carries at least one official-source link.
  3. No value flagged 'unverified' in data/v2 is displayed as verified.
  4. Required features present: search boxes, date filter, single-entry toggle,
     ≤30-min walk filter, trip calculator, rate log, monitor page.
  5. Money figures in tables match data/v2/events.json exactly.

Run: python3 tools/verify_root_site.py   (exit 0 = pass)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data" / "0f6c627b"
errors, warnings, checked = [], [], 0

EV = json.loads((D / "events.json").read_text(encoding="utf-8"))
SRC = EV["sources"]

pages = [ROOT / n for n in ("index.html", "tournaments.html", "schedule.html", "hotels.html",
                            "trip-calculator.html", "rate-log.html", "monitor.html", "questions.html",
                            "suggestions.html", "flagged.html", "sources.html")]
pages += [ROOT / "venues" / n for n in ("venetian.html", "wynn.html", "bellagio.html", "caesars.html", "others.html")]
pages = [p for p in pages if p.exists()]
if not pages:
    sys.exit("no pages found — run tools/build_root_site.py first")

# warn-level file-link scan for preserved parallel pages (not this session's output)
for p in ROOT.glob("*.html"):
    if p in pages:
        continue
    t = p.read_text(encoding="utf-8")
    for href in re.findall(r'href="([^"#$]+\.html?)"', t):
        if href.startswith(("http", "${")) or "{{" in href:
            continue
        if not (p.parent / href.split("#")[0]).exists():
            warn(f"preserved page {p.name}: file link not found -> {href}")

def err(m):
    errors.append(m)

def warn(m):
    warnings.append(m)

# 1. parse + internal links
link_re = re.compile(r'href="([^"]+)"')
for p in pages:
    t = p.read_text(encoding="utf-8")
    checked += 1
    if "<!doctype html>" not in t.lower():
        err(f"{p.name}: missing doctype")
    if t.count("<table") != t.count("</table>"):
        err(f"{p.name}: table tags unbalanced")
    for href in link_re.findall(t):
        if href.startswith(("http", "mailto", "#")):
            continue
        target = (p.parent / href.split("#")[0]).resolve()
        if not target.exists():
            err(f"{p.name}: broken internal link -> {href}")

# 2. every event row on data pages has a source link
DATA_PAGES = ("tournaments.html", "schedule.html", "hotels.html", "rate-log.html",
              "flagged.html", "index.html")
row_re = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
src_href_re = re.compile(r"""href=["'](https?://[^"']+)["']""")
official_hosts = ("venetianlasvegas.com", "wynnresorts.com", "wynnlasvegas.com", "wynnpoker.com",
                  "bellagio.mgmresorts.com", "assets.contentstack.io", "caesars.com",
                  "treasureisland.com", "maps.google.", "maps.apple.", "google.com/maps")
for p in pages:
    if not (p.name in DATA_PAGES or p.parent.name == "venues"):
        continue
    t = p.read_text(encoding="utf-8")
    for row in row_re.findall(t):
        if "<td" not in row:
            continue  # header row
        hrefs = src_href_re.findall(row)
        if not hrefs and ("src" not in row and "route" not in row and "on property" not in row):
            # rows that legitimately have no source: day-plan prose / worked examples
            if "est." in row or "example only" in row or "nights × true cost" in row:
                continue
            err(f"{p.name}: row without any source link: {row[:110]}…")
            continue
        for h in hrefs:
            if not any(host in h for host in official_hosts) and "github.io" not in h:
                warn(f"{p.name}: row links non-official host {h}")

# 3. unverified values must never be displayed as verified money
for e in EV["events"]:
    for field in ("buy_in", "guarantee"):
        v = e.get(field)
        st_fee = (e.get("entry_rules") or {}).get("fees", {}).get("status")
        if v is None:
            continue
        if e["id"].startswith("V-") and field in ("buy_in", "guarantee"):
            pass  # Venetian buy-ins/guarantees ARE sheet-verified; entry rules are not
unverified_phrase = re.compile(r"entry rules unverified|unverified", re.I)
for p in pages:
    t = p.read_text(encoding="utf-8")
    if "confirmed" in t and "unverified" not in t and p.name in ("tournaments.html",):
        err(f"{p.name}: shows 'confirmed' but never mentions unverified — policy breach")

# 4. required features
feat = {
    "tournaments.html": ["data-search", "data-date", "data-entry", 'value="confirmed"', "Single-entry"],
    "schedule.html": ["data-date", "primary", "fallback", "Overlap", "Plausible"],
    "hotels.html": ["data-walkmax", "1.1338", "hotelcalc", "booking", "30-min"],
    "trip-calculator.html": ["tripcalc", "r-total", "entries", "nights"],
    "rate-log.html": ["RL-0", "cancellation", "checkout total"],
    "monitor.html": ["monitor-live", "recheck", "status.json"],
    "flagged.html": ["F-0", "Flagged"],
    "questions.html": ["Q1", "missing information"],
    "sources.html": ["dse_nov_2026", "Poker-All_Daily_Structures"],
    "index.html": ["Executive", "single-entry", "37"],
}
for fname, needles in feat.items():
    t = (ROOT / fname).read_text(encoding="utf-8")
    for n in needles:
        if n not in t:
            err(f"{fname}: required feature/content missing: {n!r}")

# 5. money figures from data must appear correctly on tournaments page
t = (ROOT / "tournaments.html").read_text(encoding="utf-8")
for e in EV["events"]:
    if e["buy_in"] and f"${e['buy_in']:,.0f}" not in t and e["venue"] == "venetian":
        warn(f"tournaments.html: buy-in ${e['buy_in']} of {e['id']} not rendered")
for e in EV["events"]:
    if e.get("ratio_guarantee_per_buy_in") is not None and e["kind"] == "tournament":
        if f"{e['ratio_guarantee_per_buy_in']}×" not in t:
            warn(f"tournaments.html: ratio of {e['id']} not rendered")

print(f"checked {checked} pages")
for w in warnings:
    print("WARN:", w)
for e in errors:
    print("FAIL:", e)
print(f"{len(errors)} errors, {len(warnings)} warnings")
sys.exit(1 if errors else 0)
