#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Morning live-data feed: pull each listed poker room's official daily schedule
and store a dated snapshot + a comparison report.

Runs daily via GitHub Actions. Failures are recorded with an error message —
never silently dropped. Snapshots live in data/integrated/monitoring/fetches/.
"""
import difflib, json, os, re, sys, urllib.request, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "integrated")
FEEDS = os.path.join(D, "monitoring", "fetches")
os.makedirs(FEEDS, exist_ok=True)
TODAY = datetime.date.today().isoformat()
UA = {"User-Agent": "Mozilla/5.0 (compatible; Poker4-daily-feed/1.0)"}

# Official daily-schedule feeds for each listed poker room (Strip rooms + Circa check).
FEED_URLS = [
    ("Venetian DSE IV schedule", "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"),
    ("Wynn daily tournament poster", "https://cdn.wynnresorts.com/image/upload/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf"),
    ("Wynn poker room", "https://www.wynnlasvegas.com/casino/poker"),
    ("Bellagio poker", "https://bellagio.mgmresorts.com/en/casino/poker.html"),
    ("Caesars Palace", "https://www.caesars.com/caesars-palace"),
    ("Harrah's Las Vegas", "https://www.caesars.com/harrahs-las-vegas"),
    ("Horseshoe Las Vegas", "https://www.caesars.com/horseshoe-las-vegas"),
    ("Treasure Island", "https://treasureisland.com/hotel"),
    ("ARIA poker", "https://aria.mgmresorts.com/en.html"),
]

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()

def normalize(body):
    if body[:4] == b"%PDF":
        return "(pdf, %d bytes, sha %s)" % (len(body), __import__("hashlib").sha256(body).hexdigest()[:16])
    text = body.decode("utf-8", "ignore")
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def main():
    report = []
    for name, url in FEED_URLS:
        slug = re.sub(r"\W+", "-", name).lower()
        snap = os.path.join(FEEDS, "%s.txt" % slug)
        row = dict(room=name, url=url, checked=TODAY)
        try:
            current = normalize(fetch(url))
            with open(os.path.join(FEEDS, "%s-latest.txt" % slug), "w") as f:
                f.write(current)
            if os.path.exists(snap):
                with open(snap) as f:
                    prev = f.read()
                if prev.strip() != current.strip():
                    diff = list(difflib.unified_diff(prev.split(". "), current.split(". "), lineterm=""))[:40]
                    row["status"] = "CHANGED since last snapshot"
                    row["diff_sample"] = " | ".join(d.strip() for d in diff if d[:1] in "+-" and d[:3] not in ("+++","---"))
                    with open(os.path.join(FEEDS, "%s-diff-%s.txt" % (slug, TODAY)), "w") as f:
                        f.write("\n".join(diff))
                else:
                    row["status"] = "unchanged"
            else:
                row["status"] = "first snapshot stored"
            with open(snap, "w") as f:
                f.write(current)
        except Exception as ex:
            row["status"] = "FETCH ERROR (recorded, not dropped): %s" % ex
        report.append(row)
    with open(os.path.join(D, "monitoring", "daily-schedule-report.json"), "w") as f:
        json.dump(dict(meta=dict(built=TODAY), rooms=report), f, indent=1)
    print("fetch_daily_schedules: %d rooms" % len(report))
    for r in report:
        print("  %-32s %s" % (r["room"], r["status"]))

if __name__ == "__main__":
    main()
