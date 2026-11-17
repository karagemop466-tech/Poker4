#!/usr/bin/env python3
"""Canonical root-site integrity gate for the published dashboard.

The older version of this tool asserted markers from a pre-integration root-page
generation (schedule.html / trip-calculator.html instead of plan.html /
calculator.html, and the data layer under data/0f6c627b/ instead of data/).  Against
the current pages it reported false errors and the scheduled morning job stayed
permanently red.

It now does two things:

  1. delegates link / data / source-link validation to the canonical checkers
     (``scripts/verify_root.py`` and ``scripts/verify.py``);
  2. adds *structural* feature checks against the pages the canonical generator
     (``scripts/integrate_data.py``) actually emits, so a page that loses its
     search box, its filter hooks or its behaviour script fails the build instead
     of silently shipping.

The checks are deliberately structural (does the control exist, is the script
loaded, does the row carry the hook the JS binds to) rather than editorial
("does the page contain this exact sentence"), so copy-editing a page cannot
break the gate.

Run:  python3 tools/verify_root_site.py        (exit 0 = pass)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []

# ---------------------------------------------------------------- canonical pages
CANONICAL_PAGES = [
    "index.html", "tournaments.html", "hotels.html", "plan.html", "calculator.html",
    "questions.html", "suggestions.html", "flagged.html", "review.html",
    "venues/venetian.html", "venues/wynn.html", "venues/others.html",
]

# Pages that must exist because a canonical page or the README links to them.
LINKED_PAGES = ["sources.html", "monitoring.html", "archive.html"]


def run(script: str) -> int:
    path = ROOT / "scripts" / script
    proc = subprocess.run([sys.executable, str(path)], cwd=ROOT, text=True,
                          capture_output=True)
    print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    return proc.returncode


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ------------------------------------------------------- 1. delegate to the gates
for script in ("verify_root.py", "verify.py"):
    rc = run(script)
    if rc:
        errors.append(f"scripts/{script} failed")

# ------------------------------------------------------- 2. structural page checks
for rel in CANONICAL_PAGES:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"{rel}: missing canonical page")
        continue
    doc = path.read_text(encoding="utf-8")
    # the universal search box and the behaviour script
    if 'id="global-search"' not in doc:
        errors.append(f"{rel}: no global search box (id=\"global-search\")")
    if not re.search(r'src="(?:\.\./)?app\.js"', doc):
        errors.append(f"{rel}: does not load app.js")
    # every page that carries a table must let the reader act on it
    if "<table" in doc and "id=\"search-results\"" not in doc:
        errors.append(f"{rel}: table page has no search results container")

for rel in LINKED_PAGES:
    if not (ROOT / rel).exists():
        errors.append(f"{rel}: linked from the canonical pages but missing")

# ---------------------------------------------------------- 3. filter behaviours
# The tournaments table must expose the date filter, the venue filter and the
# "single-entry confirmed only" toggle, and its rows must carry the hooks app.js
# binds to.  A filter that is present in the markup but not wired to the rows
# silently filters nothing, which is worse than not offering it at all.
tourn = read("tournaments.html")
for hook, label in (
    ('id="f-from"', "from-date filter"),
    ('id="f-to"', "to-date filter"),
    ('id="f-venue"', "venue filter"),
    ('id="f-single"', "single-entry toggle"),
):
    if hook not in tourn:
        errors.append(f"tournaments.html: missing {label} ({hook})")
rows = len(re.findall(r'data-date="', tourn))
if rows == 0:
    errors.append("tournaments.html: no event row carries a data-date hook")
site_events = json.loads(read("data/site-events.json"))
if rows != len(site_events["events"]):
    errors.append(f"tournaments.html: {rows} dated rows but data/site-events.json has "
                  f"{len(site_events['events'])} events")

# The hotel page must carry the <=30-minute walk filter and the dated rate log.
hotels = read("hotels.html")
if 'id="walk-filter"' not in hotels:
    errors.append("hotels.html: missing the <=30-minute walk filter")
if "dated log" not in hotels.lower():
    errors.append("hotels.html: missing the dated rate log")
if hotels.count("data-walk-min") == 0:
    errors.append("hotels.html: no hotel card carries a data-walk-min hook")
if hotels.count("data-walk-min=\"\"") == hotels.count("data-walk-min"):
    errors.append("hotels.html: every walk time is blank — the measured walking routes are not reaching the page")

# The day plan must give each day a primary event and a conditional fallback.
plan = read("plan.html")
for needle, label in (("<th>Primary</th>", "primary-event column"),
                       ("<th>Conditional fallback</th>", "conditional-fallback column")):
    if needle not in plan:
        errors.append(f"plan.html: missing the {label}")
if len(re.findall(r"data-date=", plan)) == 0:
    errors.append("plan.html: no day row carries a data-date hook")

# The trip calculator must expose both terms of the brief's formula.
calc = read("calculator.html")
if not re.search(r'buy-?in', calc, re.I):
    errors.append("calculator.html: no buy-in input")
if not re.search(r'night', calc, re.I):
    errors.append("calculator.html: no nights input")

# The flagged page must actually publish the open items.
flagged = read("flagged.html")
if len(re.findall(r'class="flag', flagged)) == 0 and len(re.findall(r"F\d+", flagged)) == 0:
    errors.append("flagged.html: no flagged items published")

# The venue pages must carry events, hotels and their sources in one place.
for rel in ("venues/venetian.html", "venues/wynn.html", "venues/others.html"):
    doc = read(rel)
    if "<table" not in doc:
        errors.append(f"{rel}: no event/hotel table")

# ------------------------------------------------------------- 4. cross-page nav
for rel in CANONICAL_PAGES:
    doc = read(rel)
    for target in re.findall(r'href="([^"#][^"]*)"', doc):
        if target.startswith(("http://", "https://", "//", "mailto:", "data:", "javascript:")):
            continue
        if "${" in target:
            continue
        resolved = (ROOT / rel).parent / target.split("?")[0].split("#")[0]
        if not resolved.exists():
            errors.append(f"{rel}: broken internal link -> {target}")

# ------------------------------------------------------------------------ report
if errors:
    print("ERRORS:")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print(f"OK: canonical dashboard integrity and feature checks passed "
      f"({len(CANONICAL_PAGES)} canonical pages, {rows} dated event rows)")
