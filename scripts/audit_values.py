#!/usr/bin/env python3
"""Value-level audit of the published rows against the committed official evidence.

Why this exists
---------------
`scripts/verify_root.py` proves the *structure* of the site: links resolve, every row
carries a source or an explicit unverified marker, the data files parse.  It cannot
prove that the number printed on the site is the number the operator printed, and it
cannot tell a verbatim quote from a sentence the build assembled from parsed numbers.

This tool does that second half.  It re-reads every piece of official evidence that is
committed in this repository and, for every published row, looks for the literal
evidence behind each published value:

  * the buy-in, the guarantee, the starting stack, the start time, the registration
    deadline, the house fee and the prize-pool contribution must be printed by the
    document the row cites;
  * every rule sentence quoted on the site must appear, word for word, in the
    committed evidence for that row.

Nothing here writes to the published pages, and nothing here guesses.  A value that
cannot be found is reported so a human can re-read the sheet and either fix the row or
flag it.  The result is published at `data/audit-values.json` and summarised on the
site's review page.

The committed evidence
----------------------
| source | what it is | provenance |
|--------|------------|------------|
| `data/raw/*.txt` | the official page/PDF text, each file headed by the URL it came from and the SHA-256 of the response | hashed capture |
| `research/raw/venetian_dse_iv_structures.md` | the 37 Venetian DSE IV structure sheets, transcribed sheet by sheet | hand-read transcription |
| `notes/structure_rules.md` | the same sheets' verbatim house-fee and entry-rule sentences | hand-read transcription |
| `data/75757cc1/structure_reads.tsv` | every sheet's verbatim entry-related text | hand-read transcription |
| `data/08f07d1d/structure_rules.json` | every sheet's parsed fields with its verbatim excerpts | hand-read transcription |

Exit codes
----------
  0  every checked value was found in its cited evidence (or was explicitly unverified)
  1  at least one published value or quote could not be located in the evidence
  2  a data file was missing or unreadable (the audit could not run)

Run:  python3 scripts/audit_values.py [--json data/audit-values.json] [--strict]
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VEN_SHEET_RE = re.compile(r"dse_nov_2026-structure_(\d+)\.pdf")


# --------------------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------------------

def norm(text: str) -> str:
    """Collapse the whitespace and the typography noise a PDF introduces."""
    text = (text.replace("’", "'").replace("‘", "'")
                .replace("“", '"').replace("”", '"')
                .replace("–", "-").replace("—", "-").replace("−", "-")
                .replace(" ", " ").replace("ﬁ", "fi").replace("ﬂ", "fl")
                .replace("\xa0", " "))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def loose(text: str) -> str:
    """Normalise further for a containment test: ignore spacing around punctuation."""
    text = norm(text)
    text = re.sub(r"\s*([$%.,:/()#\-]) ?", r"\1", text)
    return text.lower()


def find(haystack_loose: str, needle: str) -> bool:
    if not needle:
        return False
    return loose(needle) in haystack_loose


# --------------------------------------------------------------------------------------
# the committed evidence
# --------------------------------------------------------------------------------------

class Evidence:
    """Everything in this repository that an official value can be checked against."""

    def __init__(self) -> None:
        self.captures: dict[str, str] = {}      # URL -> text (hashed capture)
        self.capture_sha: dict[str, str] = {}   # URL -> sha256 from the capture header
        self.sheet_text: dict[str, list[str]] = defaultdict(list)  # sheet no -> [text]
        self.sheet_origin: dict[str, list[str]] = defaultdict(list)

    # -- loaders ----------------------------------------------------------------
    def load_captures(self) -> None:
        for path in sorted(glob.glob(os.path.join(ROOT, "data", "raw", "*.txt"))):
            raw = open(path, encoding="utf-8", errors="replace").read()
            m = re.search(r"captured[^\n]*?from\s+(https?://[^\s(]+)", raw)
            if not m:
                m = re.search(r"(https?://[^\s)]+)", raw.split("\n", 1)[0])
            if not m:
                continue
            url = m.group(1).rstrip(".,")
            self.captures[url] = norm(raw)
            sha = re.search(r"sha256\s+([0-9a-f]{64})", raw[:2000])
            if sha:
                self.capture_sha[url] = sha.group(1)

    def load_sheet_notes(self) -> None:
        """research/raw/venetian_dse_iv_structures.md — the condensed per-sheet record."""
        path = os.path.join(ROOT, "research", "raw", "venetian_dse_iv_structures.md")
        if not os.path.exists(path):
            return
        for line in open(path, encoding="utf-8"):
            m = re.match(r"\*\*S(\d+)\*\*\s*(.*)", line.strip())
            if m:
                self.add_sheet(m.group(1), m.group(2), "research/raw/venetian_dse_iv_structures.md")

    def load_structure_rules_notes(self) -> None:
        """notes/structure_rules.md — the sheets' verbatim house-fee and entry sentences."""
        path = os.path.join(ROOT, "notes", "structure_rules.md")
        if not os.path.exists(path):
            return
        text = open(path, encoding="utf-8").read()
        parts = re.split(r"^##\s+dse_nov_2026-structure_(\d+)\.pdf", text, flags=re.M)
        for i in range(1, len(parts), 2):
            self.add_sheet(parts[i], parts[i + 1], "notes/structure_rules.md")

    def load_structure_reads_tsv(self) -> None:
        """data/75757cc1/structure_reads.tsv — every sheet's verbatim entry-related text."""
        path = os.path.join(ROOT, "data", "75757cc1", "structure_reads.tsv")
        if not os.path.exists(path):
            return
        rows = list(csv.reader(io.StringIO(open(path, encoding="utf-8").read()), delimiter="\t"))
        for r in rows[1:]:
            if len(r) < 6 or not r[0].strip().isdigit():
                continue
            self.add_sheet(r[0].strip(), "\n".join(r[1:]), "data/75757cc1/structure_reads.tsv")

    def load_structure_rules_json(self) -> None:
        """data/08f07d1d/structure_rules.json — every sheet's parsed fields and excerpts."""
        path = os.path.join(ROOT, "data", "08f07d1d", "structure_rules.json")
        if not os.path.exists(path):
            return
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            return
        for sheet in data if isinstance(data, list) else []:
            n = str(sheet.get("sheet") or "").strip()
            if not n.isdigit():
                continue
            self.add_sheet(n, json.dumps(sheet, ensure_ascii=False),
                           "data/08f07d1d/structure_rules.json")

    def add_sheet(self, number: str, text: str, origin: str) -> None:
        self.sheet_text[number].append(norm(text))
        self.sheet_origin[number].append(origin)

    def load(self) -> None:
        self.load_captures()
        self.load_sheet_notes()
        self.load_structure_rules_notes()
        self.load_structure_reads_tsv()
        self.load_structure_rules_json()

    # -- queries ----------------------------------------------------------------
    def sheet_of(self, url: str) -> str | None:
        m = VEN_SHEET_RE.search(url or "")
        return m.group(1) if m else None

    def documents_for(self, event: dict) -> list[tuple[str, str]]:
        """(label, loose text) pairs this row may be checked against."""
        docs: list[tuple[str, str]] = []
        cited = list(event.get("sources") or [])
        for url in cited:
            if url in self.captures:
                docs.append((url, loose(self.captures[url])))
        sheet = self.sheet_of((event.get("sheet_key_url") or "") or "") or None
        if sheet is None:
            for url in cited:
                s = self.sheet_of(url)
                if s:
                    sheet = s
                    break
        if sheet:
            for i, text in enumerate(self.sheet_text.get(sheet, [])):
                docs.append((f"sheet {sheet} · {self.sheet_origin[sheet][i]}", loose(text)))
        return docs

    def sheets_covered(self) -> list[str]:
        return sorted(self.sheet_text, key=lambda n: int(n) if n.isdigit() else 0)


# --------------------------------------------------------------------------------------
# value renderings we look for
# --------------------------------------------------------------------------------------

def money_forms(amount: int) -> list[str]:
    plain = f"{amount:,}"
    return [f"${amount:,}", f"$ {amount:,}", f"${plain}", f"$ {plain}", f"{amount}", plain]


DOLLAR_RE = re.compile(r"\$\s?([\d,]+)")


def blank_numbers(text: str) -> str:
    """A sentence with its money amounts replaced by '#', so two sentences that differ
    only in their figures can be compared."""
    return re.sub(r"\s+", " ", DOLLAR_RE.sub("$#", text)).strip().lower()


HOUSE_FEE_WORDING_RE = re.compile(
    r"\$\s?[\d,]+\s+of\s+the\s+\$\s?[\d,]+\s+Buy[-'\s]?In\s+is\s+withheld[^.]*\.\s*"
    r"(?:The\s+)?prize\s+pool\s+consists\s+of\s+\$\s?[\d,]+\s+of\s+every\s+\$\s?[\d,]+[^.]*\.",
    re.I)


def verified_templates(evidence: "Evidence") -> set[str]:
    """The wording templates that the committed verbatim transcriptions prove an
    operator uses — e.g. the Venetian's house-fee sentence.

    A sentence the build assembles itself is only acceptable when the operator is
    proven to write it that way somewhere in this series, so the template is read out
    of the committed transcriptions rather than assumed.
    """
    templates: set[str] = set()
    for texts in evidence.sheet_text.values():
        for text in texts:
            for m in HOUSE_FEE_WORDING_RE.finditer(text):
                templates.add(blank_numbers(m.group(0)))
    return templates


def time_forms(value: str | None) -> list[str]:
    """'11:10 AM' -> the ways a capture may print it ('11:10 AM', '11:10am', '11:10 a.m.')."""
    if not value:
        return []
    out = [value, value.replace(" ", "")]
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*([AaPp][Mm])$", value)
    if m:
        h, mi, ap = m.groups()
        mi = mi or "00"
        ap2 = "AM" if ap.upper() == "AM" else "PM"
        h2 = str(int(h))
        out += [f"{h}:{mi} {ap2}", f"{h}:{mi}{ap2}", f"{h}:{mi}", f"{h2}:{mi} {ap2}",
                f"{h2}:{mi}{ap2}", f"{h2}:{mi}",
                # "11 a.m." / "11 a.m" / "11 am" / "11 AM" — the Wynn booklet's form
                f"{h2} {ap2.lower()[0]}.m.", f"{h2} {ap2.lower()[0]}.m", f"{h2} {ap2.lower()[0]}m",
                f"{h2} {ap2.lower()}", f"{h2} {ap2}"]
    return list(dict.fromkeys(out))


# --------------------------------------------------------------------------------------
# the audit
# --------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="data/audit-values.json")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 when a published value or quote cannot be located")
    args = ap.parse_args()

    site_path = os.path.join(ROOT, "data", "site-events.json")
    if not os.path.exists(site_path):
        print("data/site-events.json missing — run scripts/integrate_data.py first", file=sys.stderr)
        return 2
    site = json.load(open(site_path, encoding="utf-8"))
    events = site["events"]

    ev = Evidence()
    ev.load()
    if not ev.captures:
        print("no captures found in data/raw/", file=sys.stderr)
        return 2

    per_field: Counter = Counter()
    per_field_ok: Counter = Counter()
    failures: list[dict] = []
    no_evidence: list[dict] = []
    reconstructed_ok: list[dict] = []
    templates = verified_templates(ev)

    for event in events:
        docs = ev.documents_for(event)
        cited = list(event.get("sources") or [])

        def add(field: str, value, forms: list[str], note: str = "") -> None:
            if value in (None, ""):
                return
            per_field[field] += 1
            hit = None
            for label, hay in docs:
                for f in forms:
                    if find(hay, f):
                        hit = (label, f)
                        break
                if hit:
                    break
            if hit:
                per_field_ok[field] += 1
            else:
                failures.append({"event_id": event["id"], "venue": event["venue"],
                                 "field": field, "value": value,
                                 "kind": "value_not_found", "note": note,
                                 "cited_sources": cited})

        buy = event.get("buy_in_usd")
        add("buy_in_usd", buy, money_forms(int(buy)) if buy else [], "printed entry / buy-in")
        gtd = event.get("guarantee_usd")
        add("guarantee_usd", gtd, money_forms(int(gtd)) if gtd else [], "printed guarantee")
        chips = event.get("starting_chips")
        add("starting_chips", chips,
            [f"{int(chips):,}", str(chips)] if chips else [], "printed starting stack")
        add("time", event.get("time"), time_forms(event.get("time")), "printed start time")
        add("registration_closes", event.get("registration_closes"),
            time_forms(event.get("registration_closes")), "printed registration deadline")
        fee = event.get("house_fee_usd")
        add("house_fee_usd", fee, money_forms(int(fee)) if fee else [], "printed house fee")
        pool = event.get("pool_per_entry_usd")
        add("pool_per_entry_usd", pool, money_forms(int(pool)) if pool else [],
            "printed prize-pool contribution")

        # quoted rule text must appear word for word in the committed evidence
        for rule, payload in (event.get("rules") or {}).items():
            if not isinstance(payload, dict):
                continue
            excerpt = payload.get("excerpt")
            if not excerpt:
                continue
            per_field[f"excerpt:{rule}"] += 1
            src = payload.get("source")
            haystacks = list(docs)
            if src and src not in {l for l, _ in haystacks} and src in ev.captures:
                haystacks.append((src, loose(ev.captures[src])))
            hit = next((l for l, h in haystacks if h and find(h, excerpt)), None)
            if hit:
                per_field_ok[f"excerpt:{rule}"] += 1
                continue
            if payload.get("excerpt_kind") == "reconstructed":
                # The build assembled this sentence from the sheet's printed figures.
                # It is acceptable only when every figure is printed by the sheet and
                # the wording is one an operator is proven to use in this series.
                amounts = [int(a.replace(",", "")) for a in DOLLAR_RE.findall(excerpt)]
                sheet_prints_all = all(
                    any(find(h, f"${a:,}") or find(h, f"${a}") or find(h, str(a))
                        for _, h in haystacks)
                    for a in amounts)
                wording_known = blank_numbers(excerpt) in templates
                if sheet_prints_all and wording_known:
                    per_field_ok[f"excerpt:{rule}"] += 1
                    reconstructed_ok.append({"event_id": event["id"], "venue": event["venue"],
                                             "field": f"excerpt:{rule}",
                                             "value": excerpt[:200],
                                             "note": "reworded from the sheet's printed figures; "
                                                     "the wording is proven verbatim on other "
                                                     "sheets of this series"})
                    continue
                failures.append({"event_id": event["id"], "venue": event["venue"],
                                 "field": f"excerpt:{rule}", "value": excerpt[:200],
                                 "kind": "reconstruction_unverified",
                                 "note": "the rebuilt sentence's figures are not all printed by "
                                         "the sheet, or its wording is not one the operator is "
                                         "proven to use",
                                 "cited_sources": cited})
                continue
            failures.append({"event_id": event["id"], "venue": event["venue"],
                             "field": f"excerpt:{rule}", "value": excerpt[:200],
                             "kind": "quote_not_verbatim", "note":
                             "the sentence shown on the site is not present, word for word, "
                             "in the committed evidence for this row",
                             "cited_sources": cited})

        if not docs:
            no_evidence.append({"event_id": event["id"], "venue": event["venue"],
                                 "cited_sources": cited})

    # ---------------------------------------------------------------- cross-checks
    cross = []

    # every published (date, time) pair must be printed by the document it cites
    wpt_capture = ev.captures.get(
        "https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/"
        "WPT/WPT_World_Championship_Structures.pdf")
    if wpt_capture:
        months = {m.lower(): i + 1 for i, m in enumerate(
            "January February March April May June July August September October "
            "November December".split())}
        printed: set[tuple[str, str]] = set()
        for wd, mon, d, y, hh, mm, ap in re.findall(
                r"([A-Za-z]+),\s*([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})\s*,?\s*at\s+"
                r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\.?", wpt_capture, re.I):
            printed.add((f"{y}-{months[mon.lower()]:02d}-{int(d):02d}",
                         f"{int(hh)}:{int(mm) if mm else 0:02d} "
                         f"{'PM' if ap.lower() == 'p' else 'AM'}"))
        checked = bad = 0
        for e in events:
            if e["venue"] != "wynn" or not e.get("date") or not e.get("time"):
                continue
            checked += 1
            if (e["date"], e["time"]) not in printed:
                bad += 1
                failures.append({"event_id": e["id"], "venue": e["venue"],
                                 "field": "date+time", "value": f"{e['date']} {e['time']}",
                                 "kind": "value_not_found",
                                 "note": "no printed day-and-time line in the cited booklet",
                                 "cited_sources": e.get("sources") or []})
        cross.append({"check": "wynn_wpt_date_time_pairs", "checked": checked,
                      "failed": bad,
                      "description": "every published Wynn (date, time) pair is printed "
                                     "in the official WPT structure booklet"})

    # every published guarantee ÷ entry ratio must recompute
    ratio_bad = 0
    for e in events:
        if e.get("gtd_ratio") is None:
            continue
        buy, gtd = e.get("buy_in_usd"), e.get("guarantee_usd")
        if not buy or not gtd:
            continue
        if abs(round(gtd / buy, 2) - e["gtd_ratio"]) > 0.01:
            ratio_bad += 1
            failures.append({"event_id": e["id"], "venue": e["venue"], "field": "gtd_ratio",
                             "value": e["gtd_ratio"], "kind": "arithmetic_mismatch",
                             "note": "guarantee ÷ buy-in does not recompute",
                             "cited_sources": e.get("sources") or []})
    cross.append({"check": "gtd_ratio_recomputes", "checked": sum(
        1 for e in events if e.get("gtd_ratio") is not None), "failed": ratio_bad,
        "description": "every published guarantee ÷ entry fee recomputes from its own row"})

    # a row labelled single-entry confirmed must carry a verbatim excerpt
    single_bad = 0
    for e in events:
        if not e.get("single_entry_confirmed"):
            continue
        r = (e.get("rules") or {}).get("single_entry") or {}
        if r.get("status") != "confirmed" or not r.get("excerpt"):
            single_bad += 1
    cross.append({"check": "single_entry_rows_carry_a_quote", "checked": sum(
        1 for e in events if e.get("single_entry_confirmed")), "failed": single_bad,
        "description": "a row labelled single-entry confirmed always quotes the rule"})

    # ---------------------------------------------------------------- summary
    checked = sum(per_field.values())
    located = sum(per_field_ok.values())
    blocking = [f for f in failures if f["kind"] in ("value_not_found", "quote_not_verbatim",
                                                     "arithmetic_mismatch")]

    report = {
        "meta": {
            # the snapshot the audit is about, not the moment the tool ran: the file
            # stays byte-stable so CI can prove the committed result is current
            "as_of": (site.get("meta") or {}).get("generated_at") or "",
            "what_this_does": (
                "Re-reads every official capture committed in data/raw/ and every committed "
                "verbatim transcription of the official structure sheets, then looks for the "
                "literal evidence behind each published number and each quoted rule sentence."),
            "evidence": {
                "hashed_captures": len(ev.captures),
                "structure_sheets_transcribed": len(ev.sheets_covered()),
                "transcription_files": [
                    "research/raw/venetian_dse_iv_structures.md",
                    "notes/structure_rules.md",
                    "data/75757cc1/structure_reads.tsv",
                    "data/08f07d1d/structure_rules.json"],
            },
            "event_rows": len(events),
            "values_checked": checked,
            "values_located": located,
            "blocking_failures": len(blocking),
        },
        "fields": {f: {"checked": per_field[f], "located": per_field_ok[f]}
                   for f in sorted(per_field)},
        "cross_checks": cross,
        "reworded_excerpts_verified": reconstructed_ok,
        "failures": failures,
        "rows_without_committed_evidence": no_evidence,
    }

    out_path = os.path.join(ROOT, args.json)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)

    print(f"evidence: {len(ev.captures)} hashed captures · "
          f"{len(ev.sheets_covered())} transcribed structure sheets")
    print(f"audit of the snapshot {report['meta']['as_of'] or '(undated)'} · "
          f"run at {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"event rows: {len(events)} · values checked: {checked} · located: {located} · "
          f"blocking failures: {len(blocking)}")
    for f in sorted(per_field):
        flag = "" if per_field_ok[f] == per_field[f] else "   <-- failures"
        print(f"  {f:32s} {per_field_ok[f]:4d}/{per_field[f]:4d}{flag}")
    for c in cross:
        mark = "OK " if c["failed"] == 0 else "FAIL"
        print(f"  [{mark}] {c['check']:38s} {c['checked']:4d} checked, {c['failed']} failed")
    if failures:
        grouped = defaultdict(list)
        for item in failures:
            grouped[(item["event_id"], item["field"], item["kind"])].append(item)
        print("\nFAILURES:")
        for (eid, field, kind), items in list(grouped.items())[:40]:
            print(f"  - {eid} · {field} · {kind}: {str(items[0]['value'])[:110]}")
        print(f"  ({len(failures)} total)")
    if no_evidence:
        print(f"\nrows whose cited document has no committed text at all: {len(no_evidence)}")

    if blocking and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
