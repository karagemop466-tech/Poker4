#!/usr/bin/env python3
"""Audit the generated v2/ site: broken anchors, missing source ids, empty tables,
leaked template braces, and rows with no official link."""
import glob, os, re, sys, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "v2")
problems = []
pages = sorted(glob.glob(os.path.join(OUT, "*.html")))
SRC = json.load(open(os.path.join(ROOT, "data", "v2", "sources.json")))["sources"]

for p in pages:
    name = os.path.basename(p)
    h = open(p).read()
    # leaked f-string braces
    for m in re.finditer(r"\{[a-z_]+\[|\{[a-z_]+\}", h):
        problems.append((name, "leaked template expression: " + m.group(0)[:60]))
    # missing source ids
    for m in re.finditer(r"missing source id (\w+)", h):
        problems.append((name, "missing source id in page: " + m.group(1)))
    # tables and their rows
    for tm in re.finditer(r'<table id="([^"]+)"[^>]*>(.*?)</table>', h, re.S):
        tid, body = tm.group(1), tm.group(2)
        rows = re.findall(r"<tr[ >].*?</tr>", body, re.S)
        data_rows = [r for r in rows if "<td" in r]
        if not data_rows:
            problems.append((name, "table %s has no data rows" % tid))
        # every data row must contain at least one anchor to an external official doc
        for r in data_rows:
            if 'class="mono">R' in r or "Repo review" in r:
                continue
            if "href=" not in r and "none read" not in r:
                problems.append((name, "table %s: row with no link -> %s" % (tid, re.sub(r"<[^>]+>", " ", r)[:70].strip())))
    # internal anchors
    for m in re.finditer(r'href="([^"#:][^"]*\.html)"', h):
        if "://" in m.group(1):
            continue
        tgt = os.path.join(OUT, m.group(1))
        if not os.path.exists(tgt):
            problems.append((name, "broken internal link: " + m.group(1)))
    # count of UNVERIFIED markers
    print("%-20s %6d bytes  %3d tables  %3d UNVERIFIED markers" % (name, len(h), h.count("<table"), h.count("UNVERIFIED")))

print()
if problems:
    print("PROBLEMS (%d):" % len(problems))
    for n, s in problems[:60]:
        print("  %-20s %s" % (n, s))
else:
    print("No structural problems found.")
sys.exit(1 if problems else 0)
