#!/usr/bin/env python3
"""Checks: every data row has a valid source; every table row on the site links an official source;
internal links resolve; flag IDs used in data exist on the Flagged for Review page."""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
errors = []

sources = json.load(open(os.path.join(ROOT, "data/sources.json")))["sources"]
flags = {f["id"]: f for f in json.load(open(os.path.join(ROOT, "data/flagged.json")))["items"]}
data_files = {"tournaments.json": "rows", "hotels.json": "rows"}
for fname, key in data_files.items():
    for r in json.load(open(os.path.join(ROOT, "data", fname)))[key]:
        sid = r.get("source")
        if sid not in sources:
            errors.append(f"{fname} {r['id']}: unknown source {sid}")
        for fid in r.get("flags", []):
            if fid not in flags:
                errors.append(f"{fname} {r['id']}: unknown flag {fid}")
for f in flags.values():
    for s in f.get("sources") or []:
        if s not in sources:
            errors.append(f"flag {f['id']}: unknown source {s}")

ids_in_pages = {}
for path in glob.glob(os.path.join(DOCS, "*.html")):
    name = os.path.basename(path)
    html = open(path, encoding="utf-8").read()
    ids_in_pages[name] = set(re.findall(r'id="([^"]+)"', html))
    # table rows must link an official source (skip header rows)
    for tbody in re.findall(r"<tbody>(.*?)</tbody>", html, re.S):
        for tr in re.findall(r"<tr>(.*?)</tr>", tbody, re.S):
            links = re.findall(r'href="(https?://[^"]+)"', tr)
            if not any(l in [s["url"] for s in sources.values()] for l in links):
                errors.append(f"{name}: table row without a source link: {tr[:80]}")
    # internal links
    for href in re.findall(r'href="(?!https?:)([^"#]+\.html)(#[^"]*)?"', html):
        target = href[0]
        if not os.path.exists(os.path.join(DOCS, target)):
            errors.append(f"{name}: broken internal link {target}")
    if "undefined" in html or "None<" in html:
        errors.append(f"{name}: contains 'undefined' or 'None'")

print(f"pages: {len(ids_in_pages)}; sources: {len(sources)}; flags: {len(flags)}")
if errors:
    print("ERRORS:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("OK: all table rows link official sources; internal links resolve; data references valid")
