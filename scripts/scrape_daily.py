#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Poker4 scheduled re-check (runs in GitHub Actions or locally with internet).

For every official URL in data/feature/dataset.py SOURCES:
  - fetch it, hash the normalized text
  - compare with the previous hash in data/feature/checks.json
  - on change: mark affected rows changed=True in data/feature/events.json /
    hotels.json (via last_checked update + changes.json entry) and append a
    dated entry to data/feature/changes.json

Never overwrites rate logs — hotel rate captures are append-only.
"""
import hashlib, json, os, sys, time, urllib.request, datetime

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "data", "feature"))
import dataset as D

CHECKS = os.path.join(ROOT, "data", "feature", "checks.json")
CHANGES = os.path.join(ROOT, "data", "feature", "changes.json")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Poker4-recheck/1.0 (+github.com/karagemop466-tech/Poker4)"})
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
    try:
        text = raw.decode("utf-8", "replace")
    except Exception:
        text = raw[:2000].hex()
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest(), len(raw)

def main():
    today = datetime.date.today().isoformat()
    prev = {}
    if os.path.exists(CHECKS):
        prev = json.load(open(CHECKS))
    out = {}
    changes = json.load(open(CHANGES)) if os.path.exists(CHANGES) else []
    changed_urls = []
    for sid, (title, url) in D.SOURCES.items():
        try:
            h, size = fetch(url)
        except Exception as e:
            out[sid] = {"url": url, "hash": prev.get(sid, {}).get("hash"), "error": str(e)[:200], "checked": today}
            print(f"ERROR {sid}: {e}")
            continue
        old = prev.get(sid, {})
        out[sid] = {"url": url, "hash": h, "bytes": size, "checked": today}
        if old.get("hash") and old["hash"] != h:
            changed_urls.append(sid)
            changes.append({"id": f"C-{sid}-{today}", "date": today, "source": url,
                            "field": f"{sid}: {title}", "change": f"Source content changed since {old.get('checked','previous check')} (hash mismatch).",
                            "action": "Row(s) citing this source marked 'changed — needs re-verification'."})
            print(f"CHANGED: {sid} {url}")
        else:
            print(f"ok: {sid}")
        time.sleep(0.4)
    json.dump(out, open(CHECKS, "w"), indent=1)

    if changed_urls:
        # mark affected rows in built artifacts
        for fn in ("events.json", "hotels.json"):
            p = os.path.join(ROOT, "data", "feature", fn)
            if not os.path.exists(p):
                continue
            rows = json.load(open(p))
            touched = False
            for row in rows:
                sids = set(row.get("sources") or [])
                for k in ("resort_fee_src", "tax_src", "parking_src", "cancellation_src", "src", "walk_src"):
                    if row.get(k):
                        sids.add(row[k])
                if sids & set(changed_urls):
                    row["changed"] = True
                    touched = True
            if touched:
                json.dump(rows, open(p, "w"), indent=1)
        json.dump(changes, open(CHANGES, "w"), indent=1)
        print(f"{len(changed_urls)} source(s) changed; changes.json updated.")
        sys.exit(0)
    print("No source changes detected.")
    sys.exit(0)

if __name__ == "__main__":
    main()
