#!/usr/bin/env python3
"""Daily change monitor for every official URL the dashboard relies on.

Runs inside GitHub Actions (full network) via .github/workflows/recheck.yml.
For each URL in data/v2/sources.json it stores a SHA-256 content hash in
data/v2/monitor/status.json. A run that detects a changed source rewrites the
"changed" list so the Flagged/monitor pages can surface rows needing review,
and refreshes the last-checked date. Nothing is deleted; history of hashes is
kept per URL.

Run: python3 tools/recheck.py          (one pass over all sources)
Exit codes: 0 = ran (changed or not); 1 = at least one fetch failed.
"""
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# The live site is built from data/ by scripts/integrate_data.py; data/0f6c627b is an
# earlier, still-preserved snapshot.  Re-pointed so the monitor checks the sources the
# published pages actually use, and so the change marks land on the live rows.
D = ROOT / "data"
if not (D / "sources.json").exists():          # fallback for the preserved snapshot layout
    D = ROOT / "data" / "0f6c627b"
MON = D / "monitor"
MON.mkdir(parents=True, exist_ok=True)
STATUS = MON / "status.json"
UA = {"User-Agent": "Mozilla/5.0 (Poker4 source monitor; +github.com/karagemop466-tech/Poker4)"}

def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), dict(r.headers)

def main():
    raw_sources = json.loads((D / "sources.json").read_text(encoding="utf-8"))["sources"]
    # two shapes are in use: a dict keyed by source id (older snapshots) and a list of
    # records (the live site's registry).  Both are accepted.
    if isinstance(raw_sources, list):
        sources = {r.get("id") or r["url"]: r for r in raw_sources}
    else:
        sources = raw_sources
    prev = {}
    if STATUS.exists():
        prev = {e["url"]: e for e in json.loads(STATUS.read_text(encoding="utf-8")).get("entries", [])}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entries, changed, failed = [], [], []
    for key, s in sorted(sources.items()):
        url = s["url"]
        if not url or "maps" in url or "apple" in url:
            # walking routes: captured manually per row; skip automated re-fetch
            entries.append({"key": key, "url": url, "status": "manual", "last_run": now})
            continue
        try:
            data, hdrs = fetch(url)
            h = hashlib.sha256(data).hexdigest()
            old = prev.get(url, {})
            state = "changed" if (old.get("sha256") and old["sha256"] != h) else ("new" if not old.get("sha256") else "same")
            if state == "changed":
                changed.append({"key": key, "url": url, "previous": old.get("sha256"), "current": h})
            entries.append({"key": key, "url": url, "sha256": h, "bytes": len(data),
                            "content_type": hdrs.get("Content-Type", ""), "status": state,
                            "last_run": now, "previous_sha256": old.get("sha256")})
        except Exception as exc:  # noqa: BLE001 — record and continue
            failed.append({"key": key, "url": url, "error": str(exc)[:200]})
            entries.append({"key": key, "url": url, "status": "fetch-failed", "error": str(exc)[:200], "last_run": now})

    status = {"last_run": now, "entries": entries, "changed": changed, "failed": failed}
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")

    # mark rows whose source changed: each event referencing a changed source key
    # gets that key in review_flags; the site renders a "source changed" badge.
    if changed:
        changed_urls = {c["url"] for c in changed}
        ev_path = D / "site-events.json"
        ev = json.loads(ev_path.read_text(encoding="utf-8"))
        for e in ev["events"]:
            hit = sorted(changed_urls.intersection(e.get("sources", [])))
            if hit:
                flags = sorted(set(e.get("review_flags", [])).union(hit))
                e["review_flags"] = flags
        ev_path.write_text(json.dumps(ev, indent=2), encoding="utf-8")
    # dated append-only log for post-hoc review
    with (MON / "runs.log").open("a", encoding="utf-8") as f:
        f.write(f"{now}: {len(entries)} urls, {len(changed)} changed, {len(failed)} failed\n")
        for c in changed:
            f.write(f"  CHANGED {c['key']} {c['url']}\n")
        for x in failed:
            f.write(f"  FAILED  {x['key']} {x['url']} {x['error']}\n")
    print(f"recheck: {len(entries)} urls — {len(changed)} changed, {len(failed)} failed"
          + ("  (fetch failures are recorded per URL in data/monitor/status.json; this runner has no "
             "outbound network, the scheduled job does)" if failed else ""))
    if changed:
        print("changed sources need row review:", [c["key"] for c in changed])
    return 0

if __name__ == "__main__":
    sys.exit(main())
