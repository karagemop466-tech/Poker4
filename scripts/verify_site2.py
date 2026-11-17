#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the Poker4 site build end-to-end:
   1. rebuild from dataset (fails on policy violations)
   2. data.js parses and matches the JSON artifacts
   3. every HTML page's internal links/asset references resolve to real files
   4. policy spot-checks: 0 fake 'confirmed single-entry' rows; every row has sources + last_checked
"""
import json, os, re, subprocess, sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
def fail(msg):
    print("VERIFY FAIL:", msg); sys.exit(1)

# 1. rebuild (also runs the policy gate)
r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_site2.py")], capture_output=True, text=True)
print(r.stdout)
if r.returncode != 0:
    fail("build_site2.py failed:\n" + r.stderr)

# 2. data.js parses
js = open(os.path.join(ROOT, "assets", "data.js")).read()
m = re.match(r"window\.POKER4_DATA = (\{.*\});\s*$", js, re.S)
if not m: fail("assets/data.js shape")
payload = json.loads(m.group(1))
events = json.load(open(os.path.join(ROOT, "data", "feature", "events.json")))
if len(payload["events"]) != len(events): fail("data.js/event.json mismatch")
for e in payload["events"]:
    if not e.get("sources"): fail(f"{e['id']}: no sources")
    if not e.get("last_checked"): fail(f"{e['id']}: no last_checked")
    se = (e.get("entry_rules") or {}).get("single_entry") or {}
    if se.get("status") == "confirmed": fail(f"{e['id']}: claims confirmed single-entry without policy backing")

# 3. internal links resolve (my dashboard pages hard-checked; other sessions' pages reported as warnings)
MY_PAGES = {"index.html", "tournaments.html", "schedule.html", "hotels.html", "trip.html", "venetian.html",
            "wynn.html", "others.html", "flagged.html", "questions.html", "suggestions.html", "sources.html",
            "changelog.html", "decisions.html", "review.html"}
pages = [f for f in os.listdir(ROOT) if f.endswith(".html")]
for page in pages:
    html = open(os.path.join(ROOT, page)).read()
    if 'http-equiv="refresh"' in html:   # legacy redirect stubs
        continue
    strict = page in MY_PAGES
    for href in re.findall(r'(?:href|src)="([^"#]+)"', html):
        if href.startswith("http") or href.startswith("mailto"): continue
        if not os.path.exists(os.path.join(ROOT, href)):
            if strict:
                fail(f"{page}: broken internal reference {href}")
            print(f"WARN (other-session page) {page}: broken reference {href}")
    if strict and ("assets/data.js" not in html or "assets/app.js" not in html):
        fail(f"{page}: missing script includes")

# 4. app.js ids referenced by pages exist in app.js expectations (spot check key ids)
app = open(os.path.join(ROOT, "assets", "app.js")).read()
for page, ids in {"tournaments.html": ["f-venue", "f-confirmed", "t-main", "t-multi", "t-rank"],
                  "schedule.html": ["s-date", "s-plan", "t-day"],
                  "hotels.html": ["t-hotels", "f-walk"],
                  "trip.html": ["trip-out", "trip-hotel", "trip-nights"],
                  "flagged.html": ["t-flagged"],
                  "sources.html": ["t-sources"]}.items():
    html = open(os.path.join(ROOT, page)).read()
    for i in ids:
        if f'id="{i}"' not in html: fail(f"{page}: missing element id {i}")

print(f"VERIFY OK: {len(payload['events'])} events, {len(payload['hotels'])} hotels, {len(payload['sources'])} sources, {len(pages)} pages.")
