#!/usr/bin/env python3
"""Re-fetch every official URL in data/v2/sources.json and report which ones changed.

We hash a normalised text extract of the page rather than the raw bytes, because
these sites inject rotating timestamps, session IDs and ad slots. A changed hash
means "a human needs to look", not "a fact changed" — the tool never edits values.
"""
import argparse, hashlib, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "v2", "sources.json")
UA = "Poker4-v2-monitor/1.0 (+https://github.com/karagemop466-tech/Poker4)"
# Fragments that change on every page load and would otherwise cause false positives.
NOISE = re.compile(r"(csrf|session|nonce|timestamp|_ga|gtm|visitor)[=:][^\s\"'&<]+", re.I)


def normalise(text):
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = NOISE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()[:200000]


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/pdf,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        ctype = r.headers.get("content-type", "")
    if "pdf" in ctype or raw[:4] == b"%PDF":
        return "PDF-BYTES:" + hashlib.sha256(raw).hexdigest()
    return normalise(raw.decode("utf-8", "replace"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=os.path.join(ROOT, "data", "v2", "source_state.json"))
    ap.add_argument("--report", default="")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    sources = json.load(open(SRC))["sources"]
    state = json.load(open(a.state)) if os.path.exists(a.state) else {"urls": {}}
    changed, failed, checked = [], [], 0
    items = list(sources.items())
    if a.limit:
        items = items[: a.limit]

    for sid, s in items:
        url = s["url"]
        try:
            digest = hashlib.sha256(fetch(url).encode("utf-8", "replace")).hexdigest()
        except Exception as e:                                  # noqa: BLE001
            failed.append((sid, url, "%s: %s" % (type(e).__name__, e)))
            continue        # deliberately NOT recorded in state: a failed fetch must never become a baseline
        checked += 1
        prev = state["urls"].get(url, {}).get("sha256")
        state["urls"].setdefault(url, {})["sha256"] = digest
        state["urls"][url]["last_checked"] = __import__("datetime").date.today().isoformat()
        state["urls"][url]["source_ids"] = sorted(set(state["urls"][url].get("source_ids", []) + [sid]))
        if prev and prev != digest:
            changed.append((sid, url))

    if checked == 0:
        print("\nNOT writing %s: every source was unreachable, so there is no baseline to record." % a.state)
    else:
        json.dump(state, open(a.state, "w"), indent=1, sort_keys=True)

    lines = ["# v2 source monitor", "", "checked: %d  changed: %d  unreachable: %d" % (checked, len(changed), len(failed)), ""]
    if changed:
        lines.append("## Changed since last run (a human must re-read these)")
        for sid, url in changed:
            lines += ["- **%s** — %s" % (sid, url)]
    if failed:
        lines.append("## Unreachable")
        for sid, url, why in failed:
            lines += ["- %s — %s (%s)" % (sid, url, why)]
    if not changed and not failed:
        lines.append("Nothing moved.")
    report = "\n".join(lines) + "\n"
    print(report)
    if a.report:
        os.makedirs(os.path.dirname(a.report), exist_ok=True)
        open(a.report, "w").write(report)
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as fh:
            fh.write("changed=%d\n" % (len(changed) + len(failed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
