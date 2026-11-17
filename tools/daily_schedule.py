#!/usr/bin/env python3
"""Morning live-schedule capture per poker room (workflow step 4).

Each run stores the text of each room's official schedule page under
data/v2/monitor/snapshots/YYYY-MM-DD/<room>.txt and diffs it against the
previous snapshot, so same-day additions/cancellations (e.g. a daily
tournament suspended during a series) become visible in the monitor log.

Run: python3 tools/daily_schedule.py   (inside GitHub Actions, full network)
"""
import difflib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MON = ROOT / "data" / "0f6c627b" / "monitor"
SNAP = MON / "snapshots"
UA = {"User-Agent": "Mozilla/5.0 (Poker4 daily schedule capture; +github.com/karagemop466-tech/Poker4)"}

ROOMS = {
    "venetian_dse_iv": "https://www.venetianlasvegas.com/casino/poker/deepstack-tournament-series.html",
    "wynn_poker": "https://www.wynnlasvegas.com/casino/poker",
    "bellagio_poker": "https://bellagio.mgmresorts.com/en/amenities/poker-room.html",
    "caesars_poker": "https://www.caesars.com/caesars-palace/casino/poker",
}

def text_of(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read().decode("utf-8", "ignore")
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", "\n", raw)
    raw = re.sub(r"\n{2,}", "\n", re.sub(r"[ \t]+", " ", raw))
    return raw.strip()

def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_dir = SNAP / today
    day_dir.mkdir(parents=True, exist_ok=True)
    prev_day = sorted(p for p in SNAP.iterdir() if p.is_dir() and p.name != today)
    prev = prev_day[-1] if prev_day else None
    report = {"date": today, "rooms": {}, "diffs": {}}
    for room, url in ROOMS.items():
        try:
            txt = text_of(url)
            (day_dir / f"{room}.txt").write_text(txt, encoding="utf-8")
            report["rooms"][room] = {"url": url, "bytes": len(txt), "status": "captured"}
            if prev and (prev / f"{room}.txt").exists():
                old = (prev / f"{room}.txt").read_text(encoding="utf-8").splitlines()
                new = txt.splitlines()
                diff = list(difflib.unified_diff(old, new, lineterm="", n=1))
                if diff:
                    (day_dir / f"{room}.diff").write_text("\n".join(diff), encoding="utf-8")
                    report["diffs"][room] = f"{len(diff)} diff lines vs {prev.name} (see {room}.diff)"
        except Exception as exc:  # noqa: BLE001
            report["rooms"][room] = {"url": url, "status": "failed", "error": str(exc)[:200]}
    (day_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (MON / "runs.log").open("a", encoding="utf-8") as f:
        f.write(f"{today} daily-schedule: " + json.dumps({k: v.get('status') for k, v in report['rooms'].items()}) + "\n")
        for room, d in report["diffs"].items():
            f.write(f"  SCHEDULE-DIFF {room}: {d}\n")
    print(f"daily-schedule: captured {len(report['rooms'])} rooms, diffs: {list(report['diffs'])}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
