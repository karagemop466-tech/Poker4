#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live source verification for the canonical Poker4 dataset.

Compares, line by line, the canonical rows against independently re-fetched
official source tables:

  live official TSV   ->  data/c07371e3/venetian_deepstack_iv.csv   ->  data/integrated/events.json
  live official TSV   ->  build/data_venetian.py SHEETS (structure-sheet metadata)

Missing/extra rows, key dates/times/numbers, buy-in/guarantee values, and sheet
mappings are hard errors. Editorial display-title differences are reported as
line-item notes because the canonical builder normalizes some wording. A blank
official value is never filled in from elsewhere; continuation rows are not
misread as new buy-ins.

Run:  python3 scripts/verify_live_sources.py
Exit: 0 = checked schedule fields agree (title variants remain explicitly listed); 1 = errors found.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, "data", "verify", "venetian_dse_iv_live_2026-11-17.tsv")
CSV_IN = os.path.join(ROOT, "data", "c07371e3", "venetian_deepstack_iv.csv")
EVENTS = os.path.join(ROOT, "data", "integrated", "events.json")

errors: list[str] = []
notes: list[str] = []


def read_live() -> list[tuple[str, str, str, str, str]]:
    rows = []
    with open(LIVE, encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) != 5:
                errors.append(f"live TSV line {ln}: expected 5 fields, got {len(parts)}")
                continue
            rows.append(tuple(p.strip() for p in parts))
    return rows


def norm_name(s: str) -> str:
    """Normalise only whitespace/separator noise; never change words."""
    s = s.replace("—", "-").replace("–", "-")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main() -> int:
    live = read_live()
    if not live:
        errors.append("live TSV produced no rows")
        return 1

    # ---------------- 1. live official table vs the CSV that feeds the builder
    with open(CSV_IN, encoding="utf-8-sig") as fh:
        csv_rows = list(csv.DictReader(fh))

    if len(live) != len(csv_rows):
        errors.append(f"row count: live official table has {len(live)} rows, "
                      f"data/c07371e3/venetian_deepstack_iv.csv has {len(csv_rows)}")

    live_by_key = {(r[0], r[1], r[2]): r for r in live}
    csv_by_key = {(r["date"], r["time"].strip(), r["event_no"].strip()): r for r in csv_rows}

    for key in sorted(set(live_by_key) - set(csv_by_key)):
        errors.append(f"row present on the official page but MISSING from the CSV: {key}")
    for key in sorted(set(csv_by_key) - set(live_by_key)):
        errors.append(f"row present in the CSV but NOT on the official page: {key}")

    name_differences: list[str] = []
    for key in sorted(set(live_by_key) & set(csv_by_key)):
        lv, cs = live_by_key[key], csv_by_key[key]
        # The integrated display titles are editorially normalized, so preserve
        # (and report) the official display text rather than treating title style
        # as a schedule-data mismatch.
        if norm_name(lv[3]) != norm_name(cs["event_name"]):
            name_differences.append(f"{key}: official={lv[3]!r}; canonical={cs['event_name']!r}")
        lv_sheet = lv[4]
        cs_sheet = re.sub(r"^dse_nov_2026-structure_|\.pdf$", "", cs["structure_pdf"])
        if lv_sheet != cs_sheet:
            errors.append(f"structure sheet mismatch {key}: official={lv_sheet} csv={cs_sheet}")
        # A continuation row is not a new entry: its title may contain the
        # original event's buy-in, while the canonical entry price is blank.
        is_continuation = "continuation" in cs.get("kind", "").lower() or "restart" in lv[3].lower()
        if not is_continuation:
            m = re.match(r"\$([\d,]+)", lv[3])
            if m:
                off_buy = int(m.group(1).replace(",", ""))
                csv_buy = int(cs["buy_in_usd"]) if cs["buy_in_usd"] else None
                if csv_buy != off_buy:
                    errors.append(f"buy-in mismatch {key}: official name says {off_buy}, csv says {csv_buy}")
        g = re.search(r"\$([\d,.]+)\s*(K|M|Mill)\b", lv[3], re.IGNORECASE)
        if g:
            txt = g.group(1).replace(",", "")
            unit = g.group(2).lower()
            mult = 1000 if unit == "k" else 1000000
            off_gtd = int(float(txt) * mult)
            csv_gtd = int(cs["guarantee_usd"]) if cs["guarantee_usd"] else None
            if csv_gtd is not None and csv_gtd != off_gtd:
                errors.append(f"guarantee mismatch {key}: official name says {off_gtd}, csv says {csv_gtd}")

    # ---------------- 2. the CSV vs the canonical integrated dataset
    with open(EVENTS, encoding="utf-8") as fh:
        ev = json.load(fh)
    ven = [e for e in ev["events"] if e["venue"] == "Venetian"]
    if len(ven) != len(live):
        errors.append(f"row count: data/integrated/events.json has {len(ven)} Venetian rows, "
                      f"the official page has {len(live)}")

    ev_by_key = {(e["date"], e["time"], e["event_no"]): e for e in ven}
    for key in sorted(set(live_by_key) - set(ev_by_key)):
        errors.append(f"official row MISSING from data/integrated/events.json: {key}")
    for key in sorted(set(ev_by_key) - set(live_by_key)):
        errors.append(f"row in data/integrated/events.json is NOT on the official page: {key}")
    event_name_differences: list[str] = []
    for key in sorted(set(live_by_key) & set(ev_by_key)):
        lv, e = live_by_key[key], ev_by_key[key]
        if norm_name(lv[3]) != norm_name(e["name"].replace(" — ", " - ")):
            event_name_differences.append(f"{key}: official={lv[3]!r}; integrated={e['name']!r}")
        cs = csv_by_key.get(key)
        if cs:
            csv_buy = int(cs["buy_in_usd"]) if cs.get("buy_in_usd") else None
            csv_gtd = int(cs["guarantee_usd"]) if cs.get("guarantee_usd") else None
            if e.get("buy_in") != csv_buy:
                errors.append(f"buy-in mismatch in events.json {key}: csv={csv_buy}, integrated={e.get('buy_in')}")
            if e.get("guarantee") != csv_gtd:
                errors.append(f"guarantee mismatch in events.json {key}: csv={csv_gtd}, integrated={e.get('guarantee')}")
        if not e.get("structure_url"):
            errors.append(f"events.json row has no structure_url: {key}")
        elif not e["structure_url"].endswith(f"structure_{lv[4]}.pdf"):
            errors.append(f"structure_url mismatch {key}: official sheet {lv[4]}, json {e['structure_url']}")
        if not e.get("source_urls"):
            errors.append(f"events.json row has no source_urls: {key}")
        if not e.get("last_checked"):
            errors.append(f"events.json row has no last_checked date: {key}")
        for field in ("single_entry", "re_entry", "add_on", "fees"):
            rule = (e.get("rule_fields") or {}).get(field)
            if not rule:
                errors.append(f"events.json row lacks structured {field} field: {key}")
                continue
            if not rule.get("retrieved_on") or rule.get("retrieved_on") != e.get("last_checked"):
                errors.append(f"events.json {field} retrieval date missing/mismatched: {key}")
            if not rule.get("source_url") or rule.get("source_url") not in e.get("source_urls", []):
                errors.append(f"events.json {field} source missing/not attached to row: {key}")
            if not rule.get("excerpt"):
                errors.append(f"events.json {field} excerpt missing: {key}")

    # ---------------- 3. every official structure sheet referenced must be one of the 37
    sys.path.insert(0, os.path.join(ROOT, "build"))
    import data_venetian as V  # noqa: E402
    referenced = {r[4] for r in live}
    known = set(V.SHEETS)
    for s in sorted(referenced - known):
        errors.append(f"official page references structure sheet {s}, which has no metadata in build/data_venetian.py")
    for s in sorted(known - referenced):
        notes.append(f"structure sheet {s} has metadata but the official page does not reference it")

    # ---------------- 4. every event on the page must map to a structure sheet with rules
    by_sheet_events = {}
    for r in live:
        by_sheet_events.setdefault(r[4], []).append(r)
    for s, rows in sorted(by_sheet_events.items()):
        sh = V.SHEETS.get(s)
        if not sh:
            continue
        missing = [x[2] for x in rows if x[2] not in [str(e) for e in sh["events"]]]
        if missing:
            errors.append(f"structure sheet {s} does not list event(s) {missing} that the official page "
                          f"maps to it ({[x[0] for x in rows]})")

    # ---------------- report
    print(f"live official rows checked : {len(live)}")
    print(f"CSV rows checked            : {len(csv_rows)}")
    print(f"integrated Venetian rows    : {len(ven)}")
    print(f"structure sheets referenced  : {len(referenced)} of {len(known)} known")
    if name_differences:
        print(f"EDITORIAL TITLE VARIANTS (CSV; {len(name_differences)} rows; official wording retained in live TSV):")
        for item in name_differences:
            print(" -", item)
    if event_name_differences:
        print(f"EDITORIAL TITLE VARIANTS (integrated JSON; {len(event_name_differences)} rows):")
        for item in event_name_differences:
            print(" -", item)
    for n in notes:
        print("NOTE:", n)
    if errors:
        print("\nDIFFERENCES (%d):" % len(errors))
        for e in errors:
            print(" -", e)
        return 1
    print("\nOK: all keyed Venetian schedule values match; editorial title variants are listed above, not silently normalized away.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
