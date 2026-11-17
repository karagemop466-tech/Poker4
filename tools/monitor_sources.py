#!/usr/bin/env python3
"""Scheduled re-check of every official source URL.

Run daily by .github/workflows/monitor.yml. For each URL in
data/source_snapshots.json this script:
  * fetches the document (official pages and PDFs),
  * stores a sha256 content hash and a text excerpt,
  * compares against the previous snapshot,
  * appends a data/change_log.json entry when content changed (rows whose
    source changed are then marked on the dashboard),
  * saves a dated raw-text snapshot of each schedule page under
    data/feeds/YYYY-MM-DD/ (the daily-schedule feed).

Values are never rewritten here: a change entry says "the official page
moved", so a human can compare the excerpt and update rows deliberately.
"""
import json, os, re, sys, hashlib, datetime, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UA = {"User-Agent": "Mozilla/5.0 (Poker4 source monitor; +https://github.com/karagemop466-tech/Poker4)"}
TIMEOUT = 30

SCHEDULE_IDS = {"V_PAGE", "W_PAGE", "B_PAGE", "C_FLYER", "A_PAGE", "W_WPT_SCHED", "V_SCHED"}

def load(name, default):
    p = os.path.join(DATA, name)
    if os.path.exists(p):
        with open(p) as f: return json.load(f)
    return default

def save(name, obj):
    with open(os.path.join(DATA, name), "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False); f.write("\n")

def textify(raw: bytes) -> str:
    t = raw.decode("utf-8", errors="replace")
    t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(), r.headers.get("Content-Type", "")

def main():
    today = datetime.date.today().isoformat()
    snaps = load("source_snapshots.json", {"snapshots": {}})
    clog = load("change_log.json", {"entries": []})
    feed_dir = os.path.join(DATA, "feeds", today)
    os.makedirs(feed_dir, exist_ok=True)
    changed = failed = ok = 0
    for url, meta in snaps.get("snapshots", {}).items():
        sid = meta.get("source_id", "UNKNOWN")
        try:
            raw, ctype = fetch(url)
            sha = hashlib.sha256(raw).hexdigest()
            excerpt = textify(raw)[:400]
            prev = meta.get("sha256")
            if prev and prev != sha:
                clog["entries"].append({
                    "date": today, "source_id": sid, "url": url,
                    "row_ref": "rows sourced from %s" % sid, "field": "source-content",
                    "change": "Official document content changed since %s (hash %s → %s). Compare the excerpt in "
                              "data/source_snapshots.json and update affected rows deliberately; rows sourced here "
                              "are marked SOURCE CHANGED." % (meta.get("fetched_at", "?"), prev[:12], sha[:12]),
                    "severity": "changed"})
                changed += 1
            meta.update({"sha256": sha, "fetched_at": today + "T00:00:00Z", "excerpt": excerpt,
                         "content_type": ctype, "last_error": None})
            if sid in SCHEDULE_IDS or "schedule" in url.lower() or "poker" in url.lower():
                safe = re.sub(r"[^A-Za-z0-9]+", "-", sid).strip("-")
                with open(os.path.join(feed_dir, safe + ".txt"), "w") as f:
                    f.write("# %s\n# %s\n# fetched %s\n%s\n" % (sid, url, today, excerpt))
            ok += 1
            print("OK  %s %s" % (sid, sha[:12]))
        except Exception as ex:  # network or parse failure: record, keep old snapshot
            meta["last_error"] = "%s: %s" % (today, ex)
            failed += 1
            print("ERR %s %s" % (sid, ex), file=sys.stderr)
    save("source_snapshots.json", snaps)
    save("change_log.json", clog)
    print("monitor run %s: ok=%d changed=%d failed=%d" % (today, ok, changed, failed))
    return 0

if __name__ == "__main__":
    sys.exit(main())
