#!/usr/bin/env python3
"""Verify every published row against the official capture it was read from.

The site publishes values only where an official page or PDF printed them.  This
checker proves that mechanically against the verbatim captures committed under
``data/raw/`` (fetched by ``tools/sync_official_sources.py`` and hashed in
``data/url-checks.json``):

  * every rule excerpt published on a row must appear **verbatim** in the
    capture of the URL that row cites for that rule;
  * every money value published on a row (buy-in, guarantee, pool per entry,
    house fee) must appear in the capture of one of the row's cited URLs;
  * every text field read off a structure sheet (starting chips, level length,
    late-registration text, printed title) must appear in the capture of the
    sheet the row cites;
  * a row that cites a URL with no committed capture is reported, because
    nothing can be proven about it offline.

Nothing here decides whether a value is *true* in the world — only that the
number or sentence on the page is present in the document it was taken from.  A
mismatch is a hard failure: it means the site prints something its own source
does not say.

Run:  python3 scripts/verify_against_captures.py
Exit: 0 = every published value is present in its cited official capture.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def norm(text: str) -> str:
    """Fold the capture and the value to one comparable shape.

    Captures come out of HTML/PDF text extraction, so they carry non-breaking
    spaces, soft hyphens, curly quotes and stray whitespace.  None of that
    changes what the document says, so all of it is folded away before the
    comparison.
    """
    t = text.replace(" ", " ").replace("‑", "-").replace("–", "-")
    t = t.replace("—", "-").replace("‘", "'").replace("’", "'")
    t = t.replace("“", '"').replace("”", '"').replace("×", "x")
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


def money_forms(amount) -> list[str]:
    """Every way a document might print this money value."""
    if amount in (None, ""):
        return []
    n = int(round(float(amount)))
    forms = {f"{n}", f"${n}", f"{n:,}", f"${n:,}", f"{n}.00", f"${n}.00"}
    return sorted(forms)


def main() -> int:
    tracked = json.loads((DATA / "tracked-sources.json").read_text(encoding="utf-8"))["sources"]
    captures: dict[str, str] = {}
    no_capture: list[str] = []
    for s in tracked:
        path = s.get("save_text_to")
        if not path:
            continue
        p = ROOT / path
        if p.exists():
            captures[s["url"]] = norm(p.read_text(encoding="utf-8", errors="replace"))
        else:
            no_capture.append(s["url"])

    events = json.loads((DATA / "site-events.json").read_text(encoding="utf-8"))["events"]

    errors: list[str] = []
    checked_excerpt = checked_money = checked_text = 0
    rows_with_capture = 0

    for ev in events:
        urls = ev.get("sources") or []
        pool = [captures[u] for u in urls if u in captures]
        if pool:
            rows_with_capture += 1
        else:
            errors.append(f"{ev['id']}: no committed capture for its cited source(s) "
                          f"{urls[:2]} — nothing can be proven about this row offline")

        # 1. rule excerpts must be verbatim in the capture the rule cites
        for rule_name, rule in (ev.get("rules") or {}).items():
            if not isinstance(rule, dict):
                continue          # e.g. the boolean spend_advantage marker
            excerpt = rule.get("excerpt")
            src = rule.get("source")
            if not excerpt:
                continue
            if not src or src not in captures:
                errors.append(f"{ev['id']}: rule '{rule_name}' quotes an excerpt but its source "
                              f"has no committed capture")
                continue
            if norm(excerpt) not in captures[src]:
                errors.append(f"{ev['id']}: rule '{rule_name}' excerpt is NOT in the cited capture "
                              f"{src.split('//')[-1][:70]}: {excerpt[:80]!r}")
            else:
                checked_excerpt += 1

        # 2. money values must appear in one of the row's cited captures
        for field in ("buy_in_usd", "guarantee_usd", "pool_per_entry_usd", "house_fee_usd"):
            amount = ev.get(field)
            if not amount or not pool:
                continue
            if any(any(form.lower() in cap for form in money_forms(amount)) for cap in pool):
                checked_money += 1
            else:
                errors.append(f"{ev['id']}: {field}={amount} does not appear in any cited capture "
                              f"({ev.get('name_printed') or ev.get('name')!r})")

        # 3. text read off a structure sheet must appear in that sheet's capture
        sheet_url = None
        for u in urls:
            if "/structures/" in u and u in captures:
                sheet_url = u
                break
        if sheet_url:
            sheet_cap = captures[sheet_url]
            for field in ("sheet_title", "sheet_note"):
                val = ev.get(field)
                if not val:
                    continue
                if norm(val) in sheet_cap:
                    checked_text += 1
                else:
                    errors.append(f"{ev['id']}: {field} {val[:70]!r} is not in the cited sheet "
                                  f"{sheet_url.split('/')[-1]}")
            for field, label in (("starting_chips", "starting chips"),
                                 ("level_duration", "level length"),
                                 ("sheet_late_registration", "late registration")):
                val = ev.get(field)
                if val in (None, ""):
                    continue
                if norm(str(val)) in sheet_cap:
                    checked_text += 1
                else:
                    errors.append(f"{ev['id']}: {label} {val!r} is not in the cited sheet "
                                  f"{sheet_url.split('/')[-1]}")

    print(f"captures: {len(captures)} · rows with a capture: {rows_with_capture}/{len(events)} · "
          f"excerpts verified: {checked_excerpt} · money values verified: {checked_money} · "
          f"sheet text values verified: {checked_text}")
    if no_capture:
        print(f"NOTE: {len(no_capture)} tracked source(s) have no committed text capture "
              f"(PDF/page not fetched): {no_capture[:3]}")
    if errors:
        print(f"FAIL: {len(errors)} published value(s) are not present in their own official source:")
        for e in errors[:60]:
            print(" -", e)
        if len(errors) > 60:
            print(f" ... and {len(errors) - 60} more")
        return 1
    print("OK: every published value is present in the official capture it was read from.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
