#!/usr/bin/env python3
"""Re-check every official source URL recorded in data/recheck_log.json.

Compares a SHA-256 of the live response against the previous run:
  - status 'changed'  -> content hash differs; rows citing this URL need re-verification
  - status 'unchanged'-> fetch succeeded, content identical to previous run
  - status 'error'     -> fetch failed (network/HTTP error)
Writes the updated log back to data/recheck_log.json and prints a summary.
Used by .github/workflows/recheck.yml (daily schedule). Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "recheck_log.json"
UA = "Poker4-recheck/1.0 (+https://github.com/karagemop466-tech/Poker4)"


def fetch_hash(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        body = resp.read()
    return hashlib.sha256(body).hexdigest()


def main() -> int:
    log = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    changed = errors = 0
    for entry in log["urls"]:
        url = entry["url"]
        try:
            digest = fetch_hash(url)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            entry["status"] = "error"
            entry["detail"] = f"fetch failed: {exc}"
            entry["checked_at"] = now
            errors += 1
            continue
        prev = entry.get("sha256")
        entry["sha256"] = digest
        entry["checked_at"] = now
        if prev is None:
            # First scheduled run: record the baseline hash.
            if entry.get("status") in ("pending", "unchanged", "changed"):
                entry["status"] = "unchanged" if entry.get("status") != "changed" else "changed"
            entry["detail"] = (entry.get("detail") or "") + " [baseline hash recorded]"
        elif prev != digest:
            entry["status"] = "changed"
            entry["detail"] = "CONTENT CHANGED vs previous run — re-verify every row citing this URL"
            changed += 1
        else:
            entry["status"] = "unchanged"
    log["checked_at"] = now
    log["run_by"] = "scheduled workflow .github/workflows/recheck.yml via scripts/recheck.py"
    LOG_PATH.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total = len(log["urls"])
    print(f"recheck: {total} URLs, {changed} changed, {errors} errors, checked {now}")
    if changed:
        print("::warning::Official source content changed — see data/recheck_log.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
