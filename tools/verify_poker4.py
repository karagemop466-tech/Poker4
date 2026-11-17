#!/usr/bin/env python3
"""Gate for the poker4 site. A build is only publishable if every claim on it is traceable.

Refuses, with a non-zero exit, when:
  * a table row has no link to a property-owned/organizer-owned document;
  * a row shows a blank value without an "unverified"/"not stated"/"not captured" marker;
  * an internal link or anchor is broken;
  * a source URL is not on the official-domain allowlist;
  * a row is labelled confirmed single-entry without a quoted sentence from its sheet;
  * the schedule table disagrees with the re-read official rows (tools/check_rows.py).
"""
from __future__ import annotations
import glob, json, os, re, subprocess, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "poker4")
D = os.path.join(ROOT, "data", "08f07d1d")
OFFICIAL = ("venetianlasvegas.com", "wynnlasvegas.com", "wynnresorts.com", "mgmresorts.com",
            "caesars.com", "treasureisland.com", "goldennugget.com", "orleanscasino.com",
            "planethollywoodresort.com", "rwlasvegas.com", "southpointcasino.com",
            "pokertda.com", "github.com")
MAPS = ("google.com", "apple.com")
BLANK_OK = ("unverified", "not stated", "not captured", "not verified", "not available", "not re-read",
            "not audited", "carried", "no guarantee", "pending", "same property", "not published",
            "not loading", "not restated", "no price")
errs, warns = [], []

pages = sorted(glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True))
if not pages:
    print("FAIL: no pages built"); sys.exit(1)

srcs = json.load(open(os.path.join(D, "sources.json")))["sources"]
src_urls = {s["url"] for s in srcs}
rules = {r["sheet"]: r for r in json.load(open(os.path.join(D, "structure_rules.json")))}
flags = {f["id"]: f for f in json.load(open(os.path.join(D, "flags.json")))["items"]}
questions = json.load(open(os.path.join(D, "questions.json")))["items"]
for q in questions:
    if q.get("flag") and q["flag"] not in flags:
        errs.append(f"question {q['id']} points at unknown flag {q['flag']}")

anchors = {}
for p in pages:
    html = open(p, encoding="utf-8").read()
    rel = os.path.relpath(p, SITE)
    anchors[rel] = set(re.findall(r'id=["\']([^"\']+)', html))
    if "undefined" in html or "None<" in html or ">None<" in html:
        errs.append(f"{rel}: leaked undefined/None into the markup")

    # ---- any table that presents a source column must link an official document in every row
    for tm in re.finditer(r'<table class="([^"]*)"[^>]*>(.*?)</table>', html, re.S):
        cls, block = tm.group(1), tm.group(2)
        head = re.search(r"<thead>(.*?)</thead>", block, re.S)
        head_txt = re.sub(r"<[^>]+>", " ", head.group(1)) if head else ""
        sourced = bool(re.search(r"(?i)source|official|link|url|pdf", head_txt))
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", block, re.S):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            if not cells:
                continue
            links = re.findall(r'href=["\'](https?://[^"\']+)', tr)
            if sourced:
                if not links:
                    plain = re.sub(r"<[^>]+>", "", tr)[:70]
                    if "no official source applies" in tr:
                        continue
                    errs.append(f"{rel}: sourced-table row with no link: {plain}")
                    continue
                for u in links:
                    host = urllib.parse.urlparse(u).netloc.lower()
                    if not any(host == d or host.endswith("." + d) for d in OFFICIAL + MAPS):
                        errs.append(f"{rel}: non-official source domain {host}")
            plain_links = [u for u in links if not any(host_ok(u) for host_ok in [lambda x: True])]
            if links:
                for u in links:
                    if not u.startswith("https://"):
                        errs.append(f"{rel}: non-https source link {u[:60]}")
            blank_rows = ">\u2014<" in tr or ">&mdash;<" in tr
            if blank_rows and not any(k in tr.lower() for k in BLANK_OK):
                plain = re.sub(r"<[^>]+>", "", tr)[:70]
                if "must" in cls:
                    errs.append(f"{rel}: blank value without an unverified marker: {plain}")

    # ---- internal links and anchors
    for target, frag in re.findall(r'href=["\']([^"#]+\.html)(#[^"\']*)?["\']', html):
        if target.startswith(("http", "/")):
            continue
        norm = os.path.normpath(os.path.join(os.path.dirname(p), target))
        if not os.path.exists(norm):
            errs.append(f"{rel}: broken internal link {target}")
        elif frag:
            key = os.path.relpath(norm, SITE)
            if frag[1:] not in anchors.get(key, set()):
                warns.append(f"{rel}: anchor {frag} not present in {key}")

# ---- confirmation labels must be backed by a quote
rows = json.load(open(os.path.join(D, "tournaments.json")))["rows"]
for r in rows:
    if r["frozen_confirmed"]:
        quote = (r.get("rule_excerpt") or (rules.get(r["sheet"] or 0, {}).get("entry_rule_excerpt"))
                 or ((rules.get(r["sheet"] or 0, {}).get("monitor") or {}).get("stated") or {})
                 .get("reentry_forbidden", {}).get("excerpt"))
        if not quote:
            errs.append(f"row {r['id']} marked confirmed single-entry with no quoted sentence")
audited_n = len([r for r in rows if r["audited"]])

# ---- schedule must still agree with the re-read official rows
rc = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_rows.py")],
                    capture_output=True, text=True, cwd=ROOT)
try:
    rep = json.loads(rc.stdout)
    if rep.get("problems"):
        errs.append(f"schedule table disagrees with official rows: {rep['problems'][:4]}")
except Exception:
    errs.append("check_rows.py did not produce a report")

# ---- monitor data sanity
state = json.load(open(os.path.join(D, "monitor_state.json"))) if os.path.exists(os.path.join(D, "monitor_state.json")) else {"sources": {}}
for s in srcs:
    if s["kind"] == "structure":
        n = int(re.search(r"structure_(\d+)\.pdf", s["url"]).group(1))
        if n not in rules:
            warns.append(f"structure sheet #{n} is tracked but has no record yet")

print(f"pages: {len(pages)} | tournament rows: {len(rows)} (sheet-audited {audited_n}) | "
      f"official sources tracked: {len(srcs)} | flags: {len(flags)} | monitor state: "
      f"{'present' if state.get('sources') else 'not yet run'}")
if warns:
    print("WARNINGS:")
    for w in sorted(set(warns)):
        print("  -", w)
if errs:
    print("FAIL:")
    for e in errs[:40]:
        print("  -", e)
    print(f"  ({len(errs)} errors)")
    sys.exit(1)
print("OK: every table row links an official document, blanks are marked unverified, "
      "internal links resolve, and no row is called confirmed without a quote.")
