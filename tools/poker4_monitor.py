#!/usr/bin/env python3
"""Poker4 official-source monitor.

Runs the scheduled re-check of every official URL on the board:

 1. fetch each source (browser User-Agent, retries, per-source error capture);
 2. hash the bytes and compare with the previous run -> "source changed";
 3. for structure-sheet PDFs: extract text and audit the entry / re-entry / add-on
    language, so a row can only be called single-entry when the sheet says so;
 4. for the Venetian calendar page: parse every dated row into a machine feed
    (the "each morning" schedule scrape);
 5. write `last_checked` + change marks into the data files the site is built from;
 6. optionally commit the result (used by .github/workflows/tournament-monitor.yml).

Nothing is ever inferred: a value that a document does not state stays null, and the
row keeps its "unverified" label. A fetch failure is recorded as `unreachable` and
never silently treated as "no change".

Usage:
    python3 tools/poker4_monitor.py --once            # fetch, update data, no commit
    python3 tools/poker4_monitor.py --once --commit   # ... and commit the result
    python3 tools/poker4_monitor.py --selftest        # offline parser tests
    python3 tools/poker4_monitor.py --only V-SCH      # one source only
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "08f07d1d")
SOURCES_F = os.path.join(DATA, "sources.json")
STATE_F = os.path.join(DATA, "monitor_state.json")
LOG_F = os.path.join(DATA, "monitor_log.json")
RULES_F = os.path.join(DATA, "structure_rules.json")
FEED_DIR = os.path.join(DATA, "feed")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# --- what a sheet must say before a row may lose its "unverified" label -------------
RULE_PATTERNS = [
    ("reentry_allowed", r"(re-?entr\w*\s+(?:and|or)\s+re-?buy\w*\s*(?:are|is)?\s*(?:allowed|permitted|unlimited|available)|"
                        r"(?:unlimited|multiple|one)\s+re-?entr\w*|subsequent\s+buy-?\s?in)", "yes"),
    ("reentry_forbidden", r"(no\s+(?:re-?entr\w*|re-?buy\w*|add-?on)|re-?entr\w*\s*(?:is|are)\s*not\s*(?:allowed|permitted)|"
                          r"(?:only|1|one)\s+entry\s+per\s+player|single[- ]entry|freeze-?out|no\s+rebuys)", "no"),
    ("addon_allowed", r"(add-?on\s*(?:is|are)?\s*(?:available|allowed|permitted|offered)|may\s+(?:also\s+)?purchase\s+an?\s+add-?on)", "yes"),
    ("addon_forbidden", r"(no\s+add-?on|add-?ons?\s*(?:is|are)\s*not\s*(?:allowed|permitted|offered))", "no"),
    ("one_entry_only", r"(one\s+entry\s+per\s+player|only\s+one\s+entry|a\s+player\s+may\s+enter\s+only\s+once|"
                        r"may\s+not\s+(?:enter|play)\s+a\s+subsequent\s+flight)", "yes"),
]
FACT_PATTERNS = {
    "start_time": r"(?i)\*{0,2}start time\*{0,2}:\s*([^\n]+)",
    "reg_close": r"(?i)late registration:\s*([^\n|]+)",
    "guarantee": r"(?i)guarantee:\s*\$([\d,]+)",
    "fee_withheld": r"(?i)\$([\d,]+)\s+of\s+the\s+\$[\d,]+\s*(?:buy-?\s?in\s+)?is withheld",
    "to_pool": r"(?i)prize pool consists of \$([\d,]+)",
    "payout_pct": r"(?i)pays\s+([\d.]+)%\s+of the field",
    "chips": r"(?i)starting chips:\s*\$?([\d,]+)",
    "level": r"(?i)level duration\*{0,2}:\s*([^\n]+)",
}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def fetch(url: str, timeout: int = 45, tries: int = 3):
    """Return dict(status, bytes, final_url, error). Never raises."""
    try:
        import requests
    except Exception as exc:  # pragma: no cover
        return {"status": None, "bytes": b"", "final_url": None, "error": f"requests unavailable: {exc}"}
    err = None
    for n in range(tries):
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
                             allow_redirects=True)
            if r.status_code >= 400:
                err = f"HTTP {r.status_code}"
            else:
                return {"status": r.status_code, "bytes": r.content, "final_url": str(r.url), "error": None}
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
        time.sleep(2 * (n + 1))
    return {"status": None, "bytes": b"", "final_url": None, "error": err}


def pdf_text(blob: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""
    import io
    try:
        rd = PdfReader(io.BytesIO(blob))
        return "\n".join((pg.extract_text() or "") for pg in rd.pages)
    except Exception:
        return ""


def html_text(blob: bytes) -> str:
    txt = blob.decode("utf-8", "replace")
    txt = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", txt)
    txt = re.sub(r"(?s)<[^>]+>", " ", txt)
    return re.sub(r"[ \t]{2,}", " ", txt)


def audit_sheet(text: str) -> dict:
    """Pull rule lines + stated facts out of one structure sheet. Silent != confirmed."""
    out = {"audited_text": True, "rule_lines": [], "stated": {}}
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.splitlines()]
    for key, pat, verdict in RULE_PATTERNS:
        hits = [l for l in lines if re.search(pat, l, re.I) and len(l) > 12]
        if hits:
            out["stated"][key] = {"value": verdict, "excerpt": hits[0][:400]}
    for key, pat in FACT_PATTERNS.items():
        m = re.search(pat, text, re.I)
        if m:
            out["stated"][key] = m.group(1).strip()[:120]
    for l in lines:
        if re.search(r"(?i)re-?entr|re-?buy|add-?on|entry per|freeze|subsequent (?:flight|buy)|bags chips|late registration", l):
            if len(l) > 12 and l not in out["rule_lines"]:
                out["rule_lines"].append(l[:400])
        if len(out["rule_lines"]) >= 8:
            break
    stated = out["stated"]
    forbids = stated.get("reentry_forbidden") or stated.get("one_entry_only")
    allows = stated.get("reentry_allowed") or stated.get("addon_allowed")
    if forbids and not allows:
        out["entry_rule"] = "single-entry confirmed by sheet"
        out["single_entry_confirmed"] = True
    elif allows:
        out["entry_rule"] = "sheet states extra entries/add-ons are offered"
        out["single_entry_confirmed"] = False
    else:
        out["entry_rule"] = "not stated on the sheet"
        out["single_entry_confirmed"] = False
        out["stated"].pop("reentry_forbidden", None)
    return out


EXCERPT_KEYS = {
    "resort_fee": r"(?i)resort fee[^.]{0,200}",
    "room_tax": r"(?i)(13\.38|room tax|Transient Accommodations Tax)[^.]{0,200}",
    "parking": r"(?i)(self-?park|valet)[^.]{0,160}",
    "cancellation": r"(?i)(cancel|no-?show|modif)[^.]{0,240}",
    "reentry": r"(?i)(re-?entr|re-?buy|add-?on|freeze-?out|single-?entr|one entry|multiple entr)[^.]{0,240}",
    "guarantee": r"(?i)(guaranteed|GTD)[^.]{0,160}",
    "rate": r"(?i)(rates? (start|from|begin)|as low as|per night|nightly rate)[^.]{0,200}",
    "poker_rate_terms": r"(?i)(play|buy-?in|qualif)[^.]{0,200}(rate|nightly)[^.]{0,80}",
    "walk": r"(?i)(walking|walk from|minutes from|distance from)[^.]{0,200}",
    "address": r"(?i)\d{3,5} S\.? Las Vegas Blvd[^.]{0,60}",
}


def extract_excerpts(text: str, limit_each: int = 3) -> dict:
    """Pull the sentences that matter out of a page/sheet so a claim can carry a quote."""
    text = re.sub(r"\s+", " ", text or "")
    out = {}
    for key, pat in EXCERPT_KEYS.items():
        hits = []
        for m in re.finditer(pat, text):
            s = m.group(0).strip()
            if len(s) > 24 and s not in hits:
                hits.append(s[:320])
            if len(hits) >= limit_each:
                break
        if hits:
            out[key] = hits
    return out


def parse_venetian_schedule(html: str) -> list:
    """Parse the official DeepStack calendar table into dated rows."""
    rows = []
    for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", html):
        tds = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)
        if len(tds) < 5:
            continue
        clean = lambda s: re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", s)).strip()
        cells = [clean(c) for c in tds]
        if not re.search(r"(?i)\b(20\d\d)\b", cells[0]) and "20" not in cells[0]:
            continue
        pdfs = re.findall(r"(?i)href=\"([^\"]*structure[^\"*]*\.pdf)\"", tds[4] if len(tds) > 4 else "")
        buy = re.search(r"\$([\d,]+)", cells[3])
        gtd = re.search(r"\$([\d,.]+)\s*(K|Mill|million)?", cells[3], re.I)
        guarantee = None
        gm = re.search(r"\$([\d,.]+)\s*(K|Mill|million)", cells[3], re.I)
        if gm:
            num = float(gm.group(1).replace(",", ""))
            unit = gm.group(2).upper()
            guarantee = int(num * (1000 if unit == "K" else 1_000_000))
        rows.append({
            "date_text": cells[0], "time": cells[1], "event_no": cells[2], "listing": cells[3],
            "buy_in_usd": int(buy.group(1).replace(",", "")) if buy else None,
            "guarantee_usd": guarantee,
            "structure_pdf": (pdfs[0] if pdfs else None),
        })
    return rows


def iso_from_text(t: str):
    for fmt in ("%A, %B %d, %Y", "%a, %d %b %Y"):
        try:
            return dt.datetime.strptime(t, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def run(only: str | None = None, commit: bool = False, quiet: bool = False) -> dict:
    reg = load(SOURCES_F, {"sources": []})
    state = load(STATE_F, {"generated": None, "sources": {}})
    rules = {r["sheet"]: r for r in load(RULES_F, [])}
    stamp = now_utc()
    results, changed, unreachable, confirmed_new = [], [], [], []

    for src in reg["sources"]:
        if only and src["id"] != only:
            continue
        url = src["url"]
        res = fetch(url)
        prev = state["sources"].get(url, {})
        entry = {
            "id": src["id"], "url": url, "venue": src.get("venue"), "kind": src.get("kind"),
            "label": src.get("label"), "status": res["status"], "final_url": res["final_url"],
            "error": res["error"], "checked_at": stamp, "bytes": len(res["bytes"]),
            "sha256": hashlib.sha256(res["bytes"]).hexdigest() if res["bytes"] else None,
        }
        if res["bytes"]:
            entry["redirected"] = bool(res["final_url"] and res["final_url"].rstrip("/") != url.rstrip("/"))
        else:
            unreachable.append(src["id"])
        changed_flag = bool(prev.get("sha256") and entry["sha256"] and prev["sha256"] != entry["sha256"])
        entry["changed"] = changed_flag
        if changed_flag:
            changed.append(src["id"])
        entry["first_seen"] = prev.get("first_seen", stamp)
        entry["last_change"] = stamp if changed_flag else prev.get("last_change")
        entry["checks"] = int(prev.get("checks", 0)) + 1
        # pages that serve the homepage to fetchers are not usable sources
        if src.get("kind") in ("schedule", "fee", "terms") and entry.get("redirected") and not changed_flag:
            entry["note"] = "official URL redirected to another page; content not captured (see flagged)"

        if src.get("kind") == "structure" and res["bytes"]:
            txt = pdf_text(res["bytes"])
            aud = audit_sheet(txt)
            m = re.search(r"structure_(\d+)\.pdf", url)
            sheet = int(m.group(1)) if m else None
            if sheet is not None:
                base = rules.get(sheet, {"sheet": sheet, "source_url": url})
                base.update({"source_url": url, "last_checked": today(), "monitor": aud,
                             "sha256": entry["sha256"], "changed": changed_flag})
                rules[sheet] = base
                if aud.get("single_entry_confirmed") and not base.get("single_entry_confirmed"):
                    confirmed_new.append(sheet)
        if src.get("parser") == "venetian_dse_schedule" and res["bytes"]:
            rows = parse_venetian_schedule(html_text(res["bytes"]) if url.endswith(".html") else res["bytes"].decode("utf-8", "replace"))
            feed = {"generated": stamp, "source_url": url, "source_sha256": entry["sha256"],
                    "row_count": len(rows), "rows": rows}
            dump(os.path.join(FEED_DIR, "venetian_dse.json"), feed)
            entry["feed_rows"] = len(rows)
        state["sources"][url] = {k: v for k, v in entry.items() if k not in ("label", "kind", "venue")}
        results.append(entry)

    state["generated"] = stamp
    state["last_checked"] = stamp
    state["sources_changed_this_run"] = changed
    state["unreachable_this_run"] = unreachable
    dump(STATE_F, state)
    dump(RULES_F, [rules[k] for k in sorted(rules)])

    log = load(LOG_F, {"runs": []})
    log["runs"].append({"at": stamp, "checked": len(results), "changed": changed,
                        "unreachable": unreachable, "newly_confirmed_sheets": confirmed_new,
                        "sources": [{"id": r["id"], "status": r["status"], "changed": r["changed"],
                                     "bytes": r["bytes"], "error": r["error"], "checked_at": r["checked_at"]}
                                    for r in results]})
    log["runs"] = log["runs"][-90:]
    log["generated"] = stamp
    dump(LOG_F, log)

    if commit:
        _commit(changed, unreachable)
    if not quiet:
        print(json.dumps({"checked": len(results), "changed": changed, "unreachable": unreachable,
                          "newly_confirmed_sheets": confirmed_new}, indent=1))
    return {"changed": changed, "unreachable": unreachable, "results": results}


def _commit(changed, unreachable):
    paths = ["data/08f07d1d/", "poker4/"]
    subprocess.run(["git", "add", "-A"] + paths, cwd=ROOT, check=False)
    dirty = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode != 0
    if not dirty:
        print("monitor: no data changes to commit")
        return
    msg = ("chore(monitor): scheduled official-source re-check %s [skip ci]\n\n"
           "checked: %d sources; changed: %s; unreachable: %s" % (today(), len(changed) + len(unreachable) + 1,
                                                                  ", ".join(changed) or "none",
                                                                  ", ".join(unreachable) or "none"))
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, check=True)
    subprocess.run(["git", "pull", "--rebase", "origin", os.environ.get("GIT_BRANCH", "main")],
                   cwd=ROOT, check=False)
    subprocess.run(["git", "push"], cwd=ROOT, check=False)


def selftest():
    fake = """Event Number: 06. Start Time: 11:10 AM. Late Registration: 8 levels + Break (~ 3:40 PM)
    $40 of the $200 Buy-In is withheld for house fees (Rake + Staff). The prize pool consists of $160 of every $200 Buy In.
    This event pays 12.5% of the field. Starting Chips: 30,000. Level Duration: 30 minutes.
    """
    a = audit_sheet(fake)
    assert a["single_entry_confirmed"] is False and a["entry_rule"] == "not stated on the sheet", a
    assert "not stated" in a["entry_rule"]
    html = ('<table><tr><td>Tuesday, November 17, 2026</td><td>11:10 AM</td><td>1</td>'
            '<td>$300 No Limit Hold\'em 1C $75K GTD</td>'
            '<td><a href="https://x/dse_nov_2026-structure_10.pdf">View</a></td><td>-</td></tr></table>')
    rows = parse_venetian_schedule(html)
    assert len(rows) == 1 and rows[0]["buy_in_usd"] == 300 and rows[0]["guarantee_usd"] == 75000, rows
    assert rows[0]["structure_pdf"].endswith("structure_10.pdf"), rows
    b = audit_sheet("No re-entry, no rebuys, no add-on. One entry per player. Late Registration: 6 levels")
    assert b["single_entry_confirmed"] is True, b
    print("selftest OK: silence keeps the unverified label; explicit wording flips it")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="run one check cycle")
    ap.add_argument("--only", help="check a single source id")
    ap.add_argument("--commit", action="store_true", help="git-commit the refreshed data")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.once or a.only:
        run(only=a.only, commit=a.commit)
    else:
        ap.print_help()
        sys.exit(1)
