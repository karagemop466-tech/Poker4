#!/usr/bin/env python3
"""Verify the generated dashboard: internal links, row sources, JS syntax."""
import json, os, re, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
errors, notes = [], []

pages = [p for p in os.listdir(".") if p.endswith(".html")]
pages += ["venues/" + p for p in os.listdir("venues") if p.endswith(".html")]

# 1. internal link check
for p in pages:
    t = open(p).read()
    for href in re.findall(r'href="([^"]+)"', t) + re.findall(r'src="([^"]+)"', t):
        if href.startswith(("http://", "https://", "mailto:", "tel:", "#")): continue
        target = os.path.normpath(os.path.join(os.path.dirname(p), href.split("#")[0]))
        if not os.path.exists(target):
            errors.append("broken link in %s → %s" % (p, href))

# 2. data rows must carry official source links; unverified values must be blank
d = json.load(open("data/events.json"))
n_unv = 0
for ev in d["events"]:
    if not (ev.get("source_url") or "").startswith("https://"):
        errors.append("event %s has no official source_url" % ev.get("id"))
    if ev["entry_rules"].get("status") == "unverified":
        n_unv += 1
        if ev["entry_rules"].get("single_entry") == "confirmed-yes":
            errors.append("event %s claims single-entry while unverified" % ev.get("id"))
h = json.load(open("data/hotels.json"))
for hh in h["hotels"]:
    if hh.get("resort_fee") is not None and not (hh.get("resort_fee_source") or "").startswith(("V_", "W_", "B_", "A_", "TI_", "MGM_", "C_")):
        errors.append("hotel %s has fee without official source id" % hh.get("id"))
for r in json.load(open("data/rate_log.json"))["entries"]:
    if not (r.get("source_url") or "").startswith("https://"):
        errors.append("rate log row %s/%s has no official source" % (r.get("hotel"), r.get("date_checked")))

# 3. JS syntax (node --check when available)
if subprocess.call(["which", "node"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
    if subprocess.call(["node", "--check", "assets/site.js"]) != 0:
        errors.append("assets/site.js fails node --check")
    else:
        notes.append("site.js passes node --check")
else:
    notes.append("node unavailable; JS syntax not machine-checked")

# 4. every table row on the tournaments page has a source anchor
t = open("tournaments.html").read()
body = t.split("<tbody>", 1)[1] if "<tbody>" in t else ""
rows = body.count("<tr ")
srcs = body.count("schedule ↗")
if srcs < rows:
    errors.append("tournaments.html: %d rows but only %d source links" % (rows, srcs))

print("pages checked:", len(pages))
print("events:", len(d["events"]), "| unverified entry rules:", n_unv)
print("notes:", "; ".join(notes))
if errors:
    print("FAIL")
    for x in errors[:40]: print(" -", x)
    sys.exit(1)
print("PASS — all internal links resolve; every data row has an official source")
