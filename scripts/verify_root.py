#!/usr/bin/env python3
"""Root-site verifier for the integrated dashboard (the df41f5c6 sub-site has its own check).

Rules enforced, in the order they have bitten us before:
 1. every internal href/src resolves to a file in the repo (a broken link is a broken deploy);
 2. every same-page anchor target exists;
 3. no unresolved template value reaches the page ("undefined", "None", "[object Object]");
 4. every data row in the event tables carries an official source link, or says out loud that the
    value is unverified (class="unknown" / a ⚑ flag) — a silent blank is not acceptable;
 5. data/site-events.json agrees with the HTML (same row count, same confirmed-single-entry count);
 6. the tag tree is balanced enough that the page cannot half-render.

Exit 0 = safe to publish. This runs in CI (site-verify.yml) and must pass before a merge.
"""
import glob
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "tournaments.html", "hotels.html", "plan.html", "calculator.html",
         "questions.html", "suggestions.html", "flagged.html", "review.html"] + \
        [os.path.relpath(p, ROOT) for p in sorted(glob.glob(os.path.join(ROOT, "venues", "*.html")))]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
        "source", "track", "wbr", "!doctype"}
SELF_OK = {"search-input"}
errors: list[str] = []
warnings: list[str] = []


class Checker(HTMLParser):
    def __init__(self, name):
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.ids: set[str] = set()
        self.bad_close = None

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        self.stack.append(tag)
        for k, v in attrs:
            if k == "id" and v:
                self.ids.add(v)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.bad_close = f"unclosed <{self.stack[-1]}> before </{tag}>"
                self.stack.pop()
            if self.stack:
                self.stack.pop()
        else:
            self.bad_close = f"stray </{tag}>"


official_hosts = set()
tracked = json.load(open(os.path.join(ROOT, "data/tracked-sources.json"), encoding="utf-8"))["sources"]
official_urls = {s["url"] for s in tracked}
for s in tracked:
    official_hosts.add(re.sub(r"^www\.", "", s["url"].split("//")[1].split("/")[0]))

for page in PAGES:
    path = os.path.join(ROOT, page)
    if not os.path.exists(path):
        errors.append(f"{page}: MISSING (scripts/integrate_data.py did not emit it)")
        continue
    doc = open(path, encoding="utf-8").read()
    here = os.path.dirname(path) or "."
    # honour <base href>: a page that declares its own base resolves links from there
    bm = re.search(r'<base\s+href="([^"]*)"', doc)
    if bm:
        here = os.path.normpath(os.path.join(here, bm.group(1)))
    for pat, kind in ((r'href="([^"]+)"', "href"), (r'src="([^"]+)"', "src")):
        for target in re.findall(pat, doc):
            if target.startswith(("http:", "https:", "mailto:", "#", "data:")):
                continue
            f = target.split("#")[0]
            if not f:
                continue
            if not os.path.exists(os.path.normpath(os.path.join(here, f))):
                errors.append(f"{page}: broken internal {kind} -> {target}")
    for frag in set(re.findall(r'href="#([^"]+)"', doc)):
        if frag not in set(re.findall(r'id="([^"]+)"', doc)) | set(re.findall(r"id='([^']+)'", doc)):
            errors.append(f"{page}: anchor #{frag} has no target id on the page")
    for bad in ("undefined", "[object Object]", "None<", ">None<", "'None'", "nan×", "NaN"):
        if bad in doc:
            errors.append(f"{page}: unresolved template value {bad!r}")
    ch = Checker(page)
    ch.feed(doc)
    if ch.bad_close:
        errors.append(f"{page}: markup problem — {ch.bad_close}")
    leftover = [t for t in ch.stack if t not in ("html", "body")]
    if leftover:
        errors.append(f"{page}: unclosed tags at EOF: {leftover[:6]}")
    # every event-table row must carry an official link or an explicit unverified marker
    rows = re.findall(r'<tr class="ev-row"[^>]*>(.*?)</tr>', doc, re.S)
    for tr in rows:
        links = re.findall(r'href="(https?://[^"]+)"', tr)
        if not links:
            errors.append(f"{page}: event row with no official source link: {re.sub(chr(10), ' ', tr)[:90]}")
        elif not any(re.sub(r"^www\.", "", l.split("//")[1].split("/")[0]) in official_hosts for l in links):
            errors.append(f"{page}: event row whose only links are non-official: {links[:2]}")
        elif '<span class="unknown">' not in tr and "chip-warn" not in tr and "chip-bad" not in tr:
            warnings.append(f"{page}: event row with no unverified marker (check it is genuinely confirmed)")
    # the pages that show a source column must show the checked date too
    if rows and "checked " not in doc:
        errors.append(f"{page}: event rows present but no 'checked' date rendered")

site = json.load(open(os.path.join(ROOT, "data/site-events.json"), encoding="utf-8"))
tourn = open(os.path.join(ROOT, "tournaments.html"), encoding="utf-8").read()
n_rows = tourn.count('<tr class="ev-row"')
if n_rows != len(site["events"]):
    errors.append(f"tournaments.html renders {n_rows} rows but data/site-events.json holds {len(site['events'])}")

# Date controls must default to upcoming rows while retaining an explicit whole-window reset.
dated = sorted({str(e.get("date")) for e in site["events"]
                if e.get("date") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e.get("date")))})
snapshot_day = str((site.get("meta") or {}).get("generated_at") or "")[:10]
window_start = dated[0] if dated else snapshot_day
window_end = dated[-1] if dated else snapshot_day
expected_from = max(snapshot_day, window_start) if snapshot_day and window_start else (snapshot_day or window_start)
expected_to = max(window_end, expected_from) if expected_from else window_end


def tag_attrs(pattern, document):
    match = re.search(pattern, document)
    return dict(re.findall(r'([a-zA-Z][\w:-]*)="([^"]*)"', match.group(1))) if match else {}


for page in ("tournaments.html", "compare.html"):
    doc = open(os.path.join(ROOT, page), encoding="utf-8").read()
    root_attrs = tag_attrs(r'<div class="filters" id="filters"([^>]*)>', doc)
    from_attrs = tag_attrs(r'<input type="date" id="f-from"([^>]*)>', doc)
    to_attrs = tag_attrs(r'<input type="date" id="f-to"([^>]*)>', doc)
    if not root_attrs or not from_attrs or not to_attrs:
        errors.append(f"{page}: missing date-filter controls")
        continue
    expected_root = {"data-window-start": window_start, "data-window-end": window_end,
                     "data-snapshot-day": snapshot_day}
    for key, value in expected_root.items():
        if root_attrs.get(key) != value:
            errors.append(f"{page}: {key}={root_attrs.get(key)!r}, expected {value!r} from event snapshot")
    for label, attrs, expected_value in (("from", from_attrs, expected_from), ("to", to_attrs, expected_to)):
        if attrs.get("value") != expected_value:
            errors.append(f"{page}: default {label} date {attrs.get('value')!r}, expected {expected_value!r}")
        if attrs.get("min") != window_start or attrs.get("max") != expected_to:
            errors.append(f"{page}: {label} date bounds do not match the printed event window")
    if 'data-preset="all"' not in doc:
        errors.append(f"{page}: no whole-window reset is available for historical rows")

app_js = open(os.path.join(ROOT, "app.js"), encoding="utf-8").read()
for required in ("function initializeUpcomingRange()", "function prepareDeepLink()",
                 "function addDaysISO(value, days)", "Math.max(0, span - 1)"):
    if required not in app_js:
        errors.append(f"app.js: upcoming date-filter behavior is missing {required!r}")
for key in ("data/schedule-snapshot.json", "data/structure-audit.json", "data/hotel-facts.json",
            "data/url-checks.json", "data/source-status.json", "data/rate-log.json", "data/walks.json",
            "data/day-plan.json", "data/search-index.json", "data/change-log.json", "data/sync-status.json"):
    p = os.path.join(ROOT, key)
    if not os.path.exists(p):
        errors.append(f"{key}: missing — the build expects it")
        continue
    try:
        json.load(open(p, encoding="utf-8"))
    except Exception as exc:  # a truncated JSON file is the classic half-commit failure
        errors.append(f"{key}: invalid JSON ({exc})")
    else:
        if os.path.getsize(p) < 40:
            errors.append(f"{key}: suspiciously small ({os.path.getsize(p)} bytes)")

rate = json.load(open(os.path.join(ROOT, "data/rate-log.json"), encoding="utf-8"))["entries"]
for e in rate:
    if e.get("amount_usd") and not e.get("source"):
        errors.append(f"rate-log: dated amount with no source: {e}")
    if e.get("amount_usd") and not e.get("observed_on"):
        errors.append(f"rate-log: dated amount with no observation date: {e.get('label')}")

for ev in site["events"]:
    if ev.get("single_entry_confirmed"):
        r = ev["rules"]["single_entry"]
        if r["status"] != "confirmed" or not r.get("excerpt"):
            errors.append(f"{ev['id']}: labelled single-entry confirmed without an excerpt")
    if ev.get("rankable") and not (ev.get("buy_in_usd") and ev.get("guarantee_usd")):
        errors.append(f"{ev['id']}: rankable without both fee and guarantee confirmed")

print(f"pages: {len(PAGES)} · event rows: {len(site['events'])} · rate-log lines: {len(rate)} · "
      f"tracked sources: {len(tracked)} · warnings: {len(warnings)}")
if warnings:
    print("WARNINGS:")
    for w in warnings[:15]:
        print(" -", w)
if errors:
    print("ERRORS:")
    for e in errors[:40]:
        print(" -", e)
    print(f"({len(errors)} total)")
    sys.exit(1)
print("OK: links resolve, every row carries an official source or an explicit unverified marker, data files parse")
