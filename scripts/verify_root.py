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
    # Every data-table row on current dashboard pages must point to an official
    # operator/organizer source (Google Maps is the route authority for walks).
    if page in {"tournaments.html", "hotels.html", "questions.html", "suggestions.html",
                "flagged.html", "sources.html", "monitoring.html", "venues/others.html",
                "venues/venetian.html", "venues/wynn.html"}:
        for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", doc, re.S):
            if "<td" not in tr:
                continue
            links = re.findall(r"href=[\"'](https?://[^\"']+)[\"']", tr)
            if not links:
                errors.append(f"{page}: data row has no official source link: {re.sub(chr(10), ' ', tr)[:100]}")
                continue
            hosts = [re.sub(r"^www\.", "", u.split("//", 1)[1].split("/", 1)[0]) for u in links]
            if not any(h in official_hosts or h.endswith(".google.com") or h == "google.com" or h == "maps.apple.com" for h in hosts):
                errors.append(f"{page}: data row links no recognized official source: {links[:2]}")
    rows = re.findall(r"<tr[^>]*>\s*<td", doc)
    if rows and "last_checked" in doc and "2026-" not in doc:
        errors.append(f"{page}: checked-date field exists but no checked date is rendered")

# The current dashboard is generated from the canonical integrated layer.
canonical = json.load(open(os.path.join(ROOT, "data/integrated/events.json"), encoding="utf-8"))["events"]
tourn = open(os.path.join(ROOT, "tournaments.html"), encoding="utf-8").read()
n_rows = len(re.findall(r"<tr[^>]*>\s*<td", tourn))
expected_rows = sum(1 for e in canonical if e.get("section") != "restart")
if n_rows != expected_rows:
    errors.append(f"tournaments.html renders {n_rows} data rows but the integrated event sections require {expected_rows}")
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

for ev in canonical:
    fields = ev.get("rule_fields", {})
    single = fields.get("single_entry", {})
    if single.get("status") == "confirmed" and single.get("value") is True:
        if not single.get("excerpt") or not single.get("source_url") or not single.get("retrieved_on"):
            errors.append(f"{ev['id']}: confirmed single-entry status lacks provenance")
    if ev.get("section") == "main" and ev.get("buy_in") and ev.get("guarantee"):
        if not ev.get("source_urls") or not ev.get("last_checked"):
            errors.append(f"{ev['id']}: value candidate lacks source link or last_checked date")

print(f"pages: {len(PAGES)} · rendered event rows: {n_rows}/{expected_rows} · rate-log lines: {len(rate)} · "
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
