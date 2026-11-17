#!/usr/bin/env python3
"""Official-source sync + change monitor for the Poker4 dashboard.

Runs where the network is available (GitHub Actions). It does four jobs:

1. Re-check every tracked official URL (casino / hotel / structure-sheet pages).
   Records: checked_at (UTC), HTTP status, sha256 of the fetched body, ETag /
   Last-Modified, and whether the body changed since the previous run.
2. Parse each venue's official schedule listing into a machine-readable snapshot
   (`data/schedule-snapshot.json`) with one row per printed event line.
3. Audit every linked structure sheet: extract the header facts (event numbers,
   start time, starting chips, level duration, late-registration window, guarantee,
   house fee, per-entry prize-pool contribution) and the *verbatim* rule lines that
   mention entries / re-entries / rebuys / add-ons. Omission is recorded as
   "not_stated" — never as confirmation of single-entry play.
4. Write `data/url-checks.json` (per-URL status + changed flag),
   `data/change-log.json` (append-only, newest first) and
   `data/structure-audit.json` (per-sheet extracts). The site reads all three and
   stamps every row with "last checked" + "source changed" marks.

Values are only ever copied or matched from the fetched text. Nothing is inferred:
if a value is not present in the source, the field stays null and the row is flagged.

Exit code is 0 even when changes are found — the caller commits the diff and the
workflow job summary announces what changed.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html as htmllib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TRACKED = os.path.join(DATA, "tracked-sources.json")
UA = "Mozilla/5.0 (compatible; Poker4-source-monitor/1.0; research snapshot job)"
TIMEOUT = 30
RETRIES = 3


# --------------------------------------------------------------------------- io
def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


# ------------------------------------------------------------------------ fetch
def fetch(url: str) -> dict:
    """GET with retries. Returns a status dict; never raises."""
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
                body = res.read()
                head = {k.lower(): v for k, v in res.headers.items()}
                return {
                    "ok": True,
                    "status": res.status,
                    "final_url": res.geturl(),
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "etag": head.get("etag"),
                    "last_modified": head.get("last-modified"),
                    "content_type": head.get("content-type"),
                    "body": body,
                    "attempt": attempt,
                }
        except urllib.error.HTTPError as exc:  # 4xx/5xx still counts as a check
            last_err = f"HTTP {exc.code}"
            if exc.code in (404, 410):
                return {"ok": False, "status": exc.code, "error": last_err, "attempt": attempt}
        except Exception as exc:  # noqa: BLE001 - network layer, record and retry
            last_err = f"{type(exc).__name__}: {exc}"
    return {"ok": False, "status": None, "error": last_err, "attempt": RETRIES}


# --------------------------------------------------------------- text extraction
TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TR_RE = re.compile(r"</tr\s*>", re.I)
TD_RE = re.compile(r"</t[dh]\s*>", re.I)
ANY_TAG = re.compile(r"<[^>]+>")


def html_to_text(raw: bytes) -> str:
    txt = raw.decode("utf-8", "replace")
    txt = TAG_RE.sub(" ", txt)
    txt = TR_RE.sub("\n", txt)
    txt = TD_RE.sub(" | ", txt)
    txt = BR_RE.sub("\n", txt)
    txt = ANY_TAG.sub(" ", txt)
    txt = htmllib.unescape(txt)
    txt = re.sub(r"[ \t\xa0]+", " ", txt)
    txt = re.sub(r" ?\| ?", " | ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt)
    return txt.strip()


def pdf_to_text(raw: bytes, workdir: str) -> tuple[str | None, str]:
    """pdftotext -layout when available; otherwise pypdf; otherwise give up (recorded)."""
    notes = []
    exe = shutil.which("pdftotext")
    if exe:
        path = os.path.join(workdir, "sheet.pdf")
        with open(path, "wb") as fh:
            fh.write(raw)
        try:
            out = subprocess.run([exe, "-layout", "-enc", "UTF-8", path, "-"],
                                 capture_output=True, timeout=120, check=False)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.decode("utf-8", "replace"), "pdftotext"
            notes.append(f"pdftotext rc={out.returncode}")
        except Exception as exc:  # noqa: BLE001
            notes.append(f"pdftotext error: {exc}")
    else:
        notes.append("pdftotext not installed")
    try:
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        txt = "\n".join((page.extract_text() or "") for page in reader.pages)
        if txt.strip():
            return txt, "pypdf"
        notes.append("pypdf returned no text")
    except Exception as exc:  # noqa: BLE001
        notes.append(f"pypdf error: {exc}")
    return None, "; ".join(notes)


# --------------------------------------------------------------------- schedule
GTD_RE = re.compile(r"\$\s?([\d,.]+)\s*(K|Mill| Million|MM)?\s*(?:USD)?\s*GTD", re.I)
BUYIN_RE = re.compile(r"\$\s?([\d,]+)(?!\s*(?:K|Mill| Million|MM))", re.I)
DATE_RE = re.compile(
    r"(?:(?P<wd>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,\s]+)?\s*"
    r"(?P<mon>January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?(?:,\s*(?P<year>\d{4}))?", re.I)
TIME_RE = re.compile(r"^(?P<t>\d{1,2}:\d{2}\s*(?:AM|PM))$", re.I)
MONTH_ABBR = {m.lower(): i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}


def parse_schedule(text: str, source_url: str) -> list[dict]:
    """One row per printed schedule line. Values are copied only when printed.

    The official pages print a table: Date | Time | Event # | Event Name | Structures | Results.
    Rows that continue a multi-flight event leave the date cell blank, so the last
    seen date carries forward.
    """
    rows: list[dict] = []
    cur: dict[str, str | None] = {"date": None, "weekday": None}
    for line in text.split("\n"):
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c != ""]
        if not cells:
            continue
        joined = " ".join(cells)
        if "Event Name" in joined and "Structures" in joined:
            continue  # header row
        date_hit = None
        for c in cells:
            m = DATE_RE.search(c)
            if m and m.group("mon"):
                mon = MONTH_ABBR.get(m.group("mon").lower()[:3])
                day = int(m.group("day"))
                year = int(m.group("year")) if m.group("year") else None
                if mon and day and year:
                    try:
                        date_hit = {
                            "date": dt.date(year, mon, day).isoformat(),
                            "weekday": (m.group("wd") or
                                       dt.date(year, mon, day).strftime("%A")),
                        }
                    except ValueError:
                        date_hit = None
                    break
        if date_hit:
            cur = date_hit
        time_cell = next((TIME_RE.match(c).group("t").upper()
                          for c in cells if TIME_RE.match(c)), None)
        event_no = None
        for c in cells:
            m = re.fullmatch(r"(?:Event\s*)?#?(\d{1,3})", c, re.I)
            if m:
                event_no = int(m.group(1))
                break
        name = None
        for c in cells:
            if len(c) > 12 and "$" in c and not re.fullmatch(r"View|Results|\d.*", c):
                name = c
                break
        if not (time_cell and event_no is not None and name):
            continue
        gu = GTD_RE.search(name)
        buy = BUYIN_RE.search(name)
        row = {
            "date": cur["date"],
            "weekday": cur["weekday"],
            "time": re.sub(r"\s+", " ", time_cell),
            "event_no": event_no,
            "event_name": name,
            "buy_in_usd": int(buy.group(1).replace(",", "")) if buy else None,
            "guarantee_usd": None,
            "guarantee_text": gu.group(0).strip() if gu else None,
            "source": source_url,
            "retrieved": today_utc(),
        }
        if gu:
            val = float(gu.group(1).replace(",", ""))
            mult = (gu.group(2) or "").strip().lower()
            if mult.startswith("k"):
                val *= 1000
            elif mult:
                val *= 1_000_000
            row["guarantee_usd"] = int(val)
        rows.append(row)
    return rows


PDF_DATE_RE = re.compile(
    r"(?:(?P<wd>MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)[,\s]+)?"
    r"(?P<mon>JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)"
    r"\s+(?P<day>\d{1,2})(?:ST|ND|RD|TH)?\b", re.I)
PDF_ROW_RE = re.compile(
    # The printed title column wraps over several lines (e.g. "… STREAMED FINAL TABLE
    # (POKERGO) AT 7:00 PM" for the LIPS Ladies Day 2 restart). The title is allowed to
    # run long so a wrapped title is captured whole instead of being dropped.
    r"(?P<no>\d{1,3})\s+\$(?P<buy>[\d,]+)\s+(?P<name>.{3,190}?)\s+"
    r"(?P<time>\d{1,2}:\d{2}\s*(?:AM|PM))"
    r"(?:\s+(?P<close>\d{1,2}:\d{2}\s*(?:AM|PM)))?"
    r"(?:\s+\$(?P<gtd>[\d,]+)(?P<gtdmult>\s*(?:K|MILL|MILLION))?)?"
    r"(?:\s+(?P<chips>\d{1,3},\d{3}))?"
    r"(?:\s+(?P<level>\d{1,2}(?:/\d{1,2})?))?", re.I)
CLOCK_RE = re.compile(r"\b\d{1,2}:\d{2}\s*(?:AM|PM)\b", re.I)

# --- right-aligned row parser -------------------------------------------------
# The printed table is column-based, but a PDF text dump flattens it into one
# line, and several event names contain a clock time of their own
# ("…$40 RAKE DISCOUNT FOR ENTRIES BEFORE 10:10 AM", "…FINAL TABLE (POKERGO) AT
# 7:00 PM"). A left-to-right regex therefore reads the name's clock as the start
# time. The columns after the name are printed in a fixed order —
# TIME · REG CLOSES · GUARANTEE · CHIPS · LEVEL · COIN/TROPHY — so the cells are
# peeled off from the RIGHT instead. Whatever remains is the event name, clock
# times inside it included.
PDF_ROW_START_RE = re.compile(r"(?<![\w$])(\d{1,3})\s+\$([\d,]+)\s+")
PDF_COIN_RE = re.compile(r"\s*(?:TROPHY\s*\+\s*)?(?:GOLD|SILVER|BRONZE)\s+COINS?\s*$", re.I)
PDF_LEVEL_RE = re.compile(r"\s+(\d{1,2}(?:/\d{1,2})?)$")
PDF_CHIPS_RE = re.compile(r"\s+(\d{1,3},\d{3})$")
PDF_GTD_RE = re.compile(r"\s+\$([\d,]+)(?:\s*(K|MILL|MILLION))?$", re.I)
PDF_GTD_SEATS_RE = re.compile(r"\s+(\d+)\s+SEATS?$", re.I)
PDF_TIME_RE = re.compile(r"\s+(\d{1,2}:\d{2}\s*(?:AM|PM))$", re.I)
PDF_FOOTER_RE = re.compile(r"\s+The Venetian®.*$", re.I)
MONTHS = {m: i for i, m in enumerate(
    ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY",
     "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"], start=1)}


# --------------------------------------------------------------------- schedule (PDF, line-oriented)
# The printed calendar is a table whose cells wrap onto extra lines, and whose DATE cell is
# sometimes replaced by a series banner ("LIPS CHAMPIONSHIP", "@PokerAtlas* TOUR"). A single
# regex over the flattened text silently lost two rows (Dec 11 10:00 AM #39 and Dec 13
# 1:00 PM #47) and mis-dated one (it read the "AT 7:00 PM" inside a wrapped event name as the
# start time). This parser works line by line, the way the table is actually laid out:
#   * a row starts either with "<event #> $<buy-in>" on one line, or with a bare event number
#     whose name and columns continue on the following lines;
#   * the column values are read from the *last* physical line of the row, from its first
#     clock token onward — that is where the TIME column sits in `pdftotext -layout` output,
#     so a time that is part of a wrapped event name is never mistaken for the start time.
LINE_DATE_RE = re.compile(
    r"^\s*(?:(?P<wd>MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)[,\s]+)?"
    r"(?P<mon>JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)"
    r"\s+(?P<day>\d{1,2})(?:ST|ND|RD|TH)?\b", re.I)
LINE_ROW_RE = re.compile(r"^(?P<no>\d{1,3})\s+\$\s?(?P<buy>[\d,]+)\s*(?P<rest>.*)$")
LINE_BARE_RE = re.compile(r"^(?P<no>\d{1,3})$")
LINE_BUYIN_RE = re.compile(r"^\$\s?(?P<buy>[\d,]+)\s*(?P<rest>.*)$")
LINE_TIME_RE = re.compile(r"^(\d{1,2}:\d{2}\s*(?:AM|PM))", re.I)
LINE_TIME_ANY_RE = re.compile(r"(?<![\d:.])\d{1,2}:\d{2}\s*(?:AM|PM)", re.I)
LINE_GTD_RE = re.compile(r"^\$\s?(?P<v>[\d,.]+)(?P<mult>\s*(?:K|MILL|MILLION|MM))?\b", re.I)
LINE_SEATS_RE = re.compile(r"^(?P<n>\d{1,3})\s+(SEAT|SEATS|PRIZE|PRIZES)\b", re.I)
LINE_CHIPS_RE = re.compile(r"^(?P<v>\d{1,3},\d{3})\b")
LINE_LEVEL_RE = re.compile(r"^(?P<v>\d{1,2}(?:\s*/\s*\d{1,2})?)(?:\s|$)")
TAIL_TOKEN_RE = re.compile(
    r"(?P<time>\d{1,2}:\d{2}\s*(?:AM|PM))"
    r"|(?P<money>\$\s?[\d,.]+(?:\s*(?:K|MILL|MILLION|MM))?(?!\s*[A-Za-z]*GTD))"
    r"|(?P<seats>\d{1,3}\s+(?:SEAT|SEATS|PRIZE|PRIZES))"
    r"|(?P<chips>\d{1,3},\d{3})"
    r"|(?P<level>\d{1,2}(?:\s*/\s*\d{1,2})?)(?=\s|$)", re.I)
LINE_NOISE_RE = re.compile(r"^(DATE EVENT #|CHAMPIONSHIP\s*$|COIN OR TROPHY\s*$|VENETIAN POKER$|"
                           r"NOVEMBER 16- DECEMBER 23, 2026$|MORE$|THAN$|\$3\.6 MILLION$|"
                           r"IN GUARANTEED PRIZE POOLS\s*$)", re.I)


def _clock_minutes(value: str):
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", value.strip(), re.I)
    if not m:
        return None
    h, mm, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
    return ((h % 12) + (12 if ap == "PM" else 0)) * 60 + mm


def parse_schedule_pdf_lines(text: str, source_url: str, default_year: int | None = None) -> list[dict]:
    """One row per printed calendar row, recovered from the `pdftotext -layout` line structure."""
    lines = [re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in text.split("\n")]
    rows: list[dict] = []
    cur_date = cur_wd = None
    year = default_year
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line or LINE_NOISE_RE.match(line):
            continue
        rest = line
        dm = LINE_DATE_RE.match(line)
        if dm:
            ym = re.search(r"\b(20\d{2})\b", line)
            if ym:
                year = int(ym.group(1))
            mon = MONTHS.get(dm.group("mon").upper())
            day = int(dm.group("day"))
            try:
                d = dt.date(year or 0, mon, day)
                cur_date = d.isoformat()
                cur_wd = (dm.group("wd") or d.strftime("%A")).title()
            except (ValueError, TypeError):
                cur_date, cur_wd = None, (dm.group("wd").title() if dm.group("wd") else None)
            rest = line[dm.end():].strip()
            if not rest:
                continue
        bm = LINE_BARE_RE.match(rest)
        head = LINE_ROW_RE.match(rest)
        if bm:  # event number alone: the row's cells continue on the following lines
            no = int(bm.group("no"))
            buy = name = None
            body_lines: list[str] = []
            tail = None
            for _ in range(8):
                if i >= len(lines):
                    break
                nxt = lines[i]
                i += 1
                if not nxt:
                    continue
                if LINE_DATE_RE.match(nxt) or LINE_ROW_RE.match(nxt) or LINE_NOISE_RE.match(nxt):
                    break
                bmm = LINE_ROW_RE.match(nxt)
                buy_m = None if bmm else LINE_BUYIN_RE.match(nxt)
                if bmm and buy is None:
                    buy = int(bmm.group("buy").replace(",", ""))
                    nxt_tail = bmm.group("rest")
                elif buy_m and buy is None:
                    buy = int(buy_m.group("buy").replace(",", ""))
                    nxt_tail = buy_m.group("rest")
                else:
                    nxt_tail = nxt
                tm = LINE_TIME_RE.match(nxt_tail)
                if tm:
                    name_part = nxt_tail[:tm.start()].strip()
                    if name_part:
                        body_lines.append(name_part)
                    tail = nxt_tail[tm.start():].strip()
                    break
                body_lines.append(nxt_tail)
            if tail is None or buy is None:
                continue
            name = re.sub(r"\s+", " ", " ".join(body_lines)).strip(" -|")
            rows.append(_pdf_row(no, buy, name, tail, cur_date, cur_wd, source_url))
            continue
        if head:
            no = int(head.group("no"))
            buy = int(head.group("buy").replace(",", ""))
            body = head.group("rest")
            tm = LINE_TIME_ANY_RE.search(body)
            if not tm:  # the columns wrapped onto the next line
                for _ in range(6):
                    if i >= len(lines):
                        break
                    nxt = lines[i]
                    i += 1
                    if not nxt:
                        continue
                    if LINE_DATE_RE.match(nxt) or LINE_ROW_RE.match(nxt):
                        i -= 1
                        break
                    tm2 = LINE_TIME_ANY_RE.search(nxt)
                    if tm2:
                        name = re.sub(r"\s+", " ", (body + " " + nxt[:tm2.start()])).strip(" -|")
                        rows.append(_pdf_row(no, buy, name, nxt[tm2.start():].strip(),
                                             cur_date, cur_wd, source_url))
                        break
                    body = (body + " " + nxt).strip()
                else:
                    continue
                continue
            name = re.sub(r"\s+", " ", body[:tm.start()]).strip(" -|")
            rows.append(_pdf_row(no, buy, name, body[tm.start():].strip(), cur_date, cur_wd, source_url))
            continue
    return [r for r in rows if r]


def _pdf_row(no: int, buy: int, name: str, tail: str, date_iso, weekday, source_url) -> dict | None:
    """Split a row's tail (TIME [REG CLOSES] [GUARANTEE] [CHIPS] [LEVEL] [TROPHY]) into columns.

    A wrapped event name can end inside the tail (for example "$40 RAKE DISCOUNT FOR ENTRIES
    BEFORE 10:10 AM", where the printed start time is also 10:10 AM), so time tokens that are
    not later than the start are treated as part of the name and skipped rather than recorded as
    a registration deadline.
    """
    note: list[str] = []
    if not name:
        return None
    tokens = [(mo.lastgroup, mo.group(0).strip()) for mo in TAIL_TOKEN_RE.finditer(tail)]
    if not tokens or tokens[0][0] != "time":
        return None
    time_val = tokens[0][1]
    start_min = _clock_minutes(time_val)
    idx = 1
    close = None
    while idx < len(tokens):
        kind, val = tokens[idx][0], tokens[idx][1]
        if kind != "time":
            break
        mins = _clock_minutes(val)
        if mins is not None and start_min is not None and mins > start_min:
            close = val
            idx += 1
            break
        note.append(f"a printed time “{val}” inside the event name is not later than the start "
                    "time; left in the name, not recorded as a registration deadline")
        idx += 1
    gtd = gtd_text = None
    if idx < len(tokens) and tokens[idx][0] == "money":
        raw = tokens[idx][1]
        m = LINE_GTD_RE.match(raw)
        if m:
            val = float(m.group("v").replace(",", ""))
            mult = (m.group("mult") or "").strip().upper()
            if mult == "K":
                val *= 1000
            elif mult:
                val *= 1_000_000
            gtd = int(val)
            idx += 1
    elif idx < len(tokens) and tokens[idx][0] == "seats":
        gtd_text = re.sub(r"\s+", " ", tokens[idx][1]).strip()
        idx += 1
    chips = None
    if idx < len(tokens) and tokens[idx][0] == "chips":
        chips = int(tokens[idx][1].replace(",", ""))
        idx += 1
    level = None
    if idx < len(tokens) and tokens[idx][0] == "level":
        v = re.sub(r"\s+", "", tokens[idx][1])
        parts = [int(x) for x in v.split("/")]
        if all(5 <= x <= 120 for x in parts):
            level = v
        else:
            note.append(f"LEVEL cell “{v}” is not a plausible blind level; not recorded")
    return {
        "parse_notes": note or None,
        "registration_closes": re.sub(r"\s+", " ", close).upper() if close else None,
        "date": date_iso,
        "weekday": weekday,
        "time": re.sub(r"\s+", " ", time_val).upper(),
        "event_no": no,
        "event_name": name,
        "buy_in_usd": buy,
        "guarantee_usd": gtd,
        "guarantee_text": gtd_text,
        "starting_chips": chips,
        "level_duration": level,
        "source": source_url,
        "retrieved": today_utc(),
    }


def parse_schedule_pdf(text: str, source_url: str, default_year: int | None = None) -> list[dict]:
    """Rows of the printed schedule table: DATE | EVENT # | EVENT | TIME | REG CLOSES | GUARANTEE | CHIPS | LEVEL.

    Each row is attributed to the most recent printed date header. The trailing
    cells are peeled off the end of the flat PDF line (see the regexes above) so
    that a clock time printed *inside* an event name stays in the name instead of
    being read as the start time. Fields the page does not print stay null — they
    are never carried over from a neighbouring row.

    The line-oriented parser above is used first because it reads the wrapped cells and the
    banner-replaced DATE cells correctly. The older table-text pass is kept as a fallback and
    as a cross-check: any row it finds that the line parser did not is reported in
    `_parser_disagreement` (never published as a value) so a disagreement is reviewed instead
    of silently changing the calendar.
    """
    line_rows = parse_schedule_pdf_lines(text, source_url, default_year)
    if not line_rows:  # layout changed beyond recognition — fall back to the table-text pass
        return _parse_schedule_pdf_text(text, source_url, default_year)

    def key(r):
        return (r.get("date"), r.get("event_no"), (r.get("time") or "").upper())

    seen = {key(r) for r in line_rows}
    orphan = [r for r in _parse_schedule_pdf_text(text, source_url, default_year) if key(r) not in seen]
    for r in line_rows:
        if orphan and not r.get("parse_notes"):
            r["parse_notes"] = [f"{len(orphan)} row(s) the table-text pass read differently — "
                                "compare data/schedule-snapshot.json against the printed page"]
            break
    return line_rows


def _parse_schedule_pdf_text(text: str, source_url: str, default_year: int | None = None) -> list[dict]:
    """Table-text pass over the flattened PDF (kept as fallback / cross-check)."""
    flat = re.sub(r"\s+", " ", text).strip()
    heads = list(PDF_DATE_RE.finditer(flat))
    if not heads:
        return []
    bounds = [(m.start(), m) for m in heads] + [(len(flat), None)]
    rows: list[dict] = []
    for i, (start, head) in enumerate(bounds[:-1]):
        end = bounds[i + 1][0]
        seg = flat[start:end]
        mon = MONTHS.get(head.group("mon").upper())
        day = int(head.group("day"))
        year = default_year
        yr = re.search(r"\b(20\d{2})\b", seg)
        if yr:
            year = int(yr.group(1))
        date_iso = None
        if mon and day and year:
            try:
                date_iso = dt.date(year, mon, day).isoformat()
            except ValueError:
                date_iso = None

        def clock(value):
            if not value:
                return None
            h, rest = value.upper().split(":")
            mm = rest.strip()[:2]
            ap = "PM" if "PM" in rest.upper() else "AM"
            hr = int(h) % 12 + (12 if ap == "PM" else 0)
            return hr * 60 + int(mm)

        starts = list(PDF_ROW_START_RE.finditer(seg))
        for j, m in enumerate(starts):
            stop = starts[j + 1].start() if j + 1 < len(starts) else len(seg)
            chunk = re.sub(PDF_FOOTER_RE, "", seg[m.start():stop]).strip()
            note: list[str] = []
            event_no = int(m.group(1))
            buy = int(m.group(2).replace(",", ""))
            body = chunk[m.end() - m.start():].strip()

            # --- peel the trailing cells off the right, in printed column order
            for _ in range(3):
                new_body = re.sub(PDF_COIN_RE, "", body).strip()
                if new_body == body:
                    break
                body = new_body
            level = None
            m_lvl = PDF_LEVEL_RE.search(body)
            if m_lvl:
                cand = m_lvl.group(1)
                parts = [int(x) for x in cand.split("/")]
                if all(5 <= x <= 120 for x in parts):
                    level = cand
                    body = body[:m_lvl.start()].strip()
                else:
                    note.append(f"trailing value “{cand}” is not a plausible blind level; not recorded")
                    body = body[:m_lvl.start()].strip()
            chips = None
            m_ch = PDF_CHIPS_RE.search(body)
            if m_ch:
                chips = int(m_ch.group(1).replace(",", ""))
                body = body[:m_ch.start()].strip()
            gtd = None
            gtd_text = None
            m_gtd = PDF_GTD_RE.search(body)
            if m_gtd:
                gtd = int(m_gtd.group(1).replace(",", ""))
                mult = (m_gtd.group(2) or "").strip().upper()
                if mult == "K":
                    gtd *= 1000
                elif mult:
                    gtd *= 1_000_000
                body = body[:m_gtd.start()].strip()
            else:
                m_seats = PDF_GTD_SEATS_RE.search(body)
                if m_seats:
                    gtd_text = f"{m_seats.group(1)} seats"
                    body = body[:m_seats.start()].strip()
            # --- the TIME and REG CLOSES columns, right to left
            times: list[str] = []
            while len(times) < 2:
                m_t = PDF_TIME_RE.search(body)
                if not m_t:
                    break
                times.insert(0, re.sub(r"\s+", " ", m_t.group(1)).upper())
                body = body[:m_t.start()].strip()
            if len(times) == 2 and clock(times[1]) is not None and clock(times[1]) > clock(times[0]):
                time_s, close = times[0], times[1]
            elif len(times) == 2:
                # the later-looking clock is not later than the earlier one: it belongs
                # to the event name (“…FINAL TABLE (POKERGO) AT 7:00 PM 10:00 AM”), so
                # the start time is the last clock and no deadline is recorded.
                time_s, close = times[1], None
                body = (body + " " + times[0]).strip()
                note.append(f"“{times[0]}” appears inside the event name, not in the TIME column; "
                            f"start time taken as {times[1]}")
            elif len(times) == 1:
                time_s, close = times[0], None
            else:
                note.append("no TIME cell printed on this row; row kept without a start time")
                time_s, close = None, None
            name = re.sub(r"\s+", " ", body).strip(" -|")
            rows.append({
                "parse_notes": note or None,
                "registration_closes": close,
                "date": date_iso,
                "weekday": (head.group("wd").title() if head and head.group("wd") else None),
                "time": time_s,
                "event_no": event_no,
                "event_name": name,
                "buy_in_usd": buy,
                "guarantee_usd": gtd,
                "guarantee_text": gtd_text,
                "starting_chips": chips,
                "level_duration": level,
                "source": source_url,
                "retrieved": today_utc(),
            })
    return rows


SCHEDULE_COMPARE_FIELDS = ("event_no", "time", "registration_closes", "buy_in_usd", "guarantee_usd",
                           "starting_chips", "event_name", "date")


def diff_schedule(old_rows, new_rows) -> dict:
    """Row-level diff of the printed schedule, keyed by event number + time + name."""
    if not old_rows:
        return {}

    def key(r):
        return f"{r.get('event_no')}|{r.get('time')}|{(r.get('event_name') or '')[:28]}"

    old = {key(r): r for r in old_rows}
    new = {key(r): r for r in new_rows}
    out = {"added": [k for k in new if k not in old][:40],
           "removed": [k for k in old if k not in new][:40],
           "changed": {}}
    for k in set(old) & set(new):
        d = {f: {"was": old[k].get(f), "now": new[k].get(f)}
             for f in SCHEDULE_COMPARE_FIELDS if old[k].get(f) != new[k].get(f)}
        if d:
            out["changed"][k] = d
    return {kk: vv for kk, vv in out.items() if vv}


# ------------------------------------------------------------------- structures
FIELD_PATTERNS = {
    "title": r"^\s*\$?[\d,]*\s*.{0,70}?$",
    "event_numbers": r"Event\s*Numbers?\s*:?\s*(?P<v>[0-9,\s and]+)",
    "start_time": r"Start\s*Time\s*:?\s*(?P<v>\d{1,2}:\d{2}\s*[AP]M)",
    "starting_chips": r"Starting\s*Chips\s*:?\s*(?P<v>[\d,]+)",
    "level_duration": r"Level\s*Duration\s*:?\s*(?P<v>\d+\s*min\w*)",
    "late_registration": r"Late\s*Registration\s*:?\s*(?P<v>.{0,60})",
    "guarantee": r"Guarantee\s*:?\s*(?P<v>.{0,90})",
    "day2": r"Day\s*2[^.\n]{0,120}",
    "flight_start": r"Day\s*[A-Z](?:\s*\+\s*[A-Z])*\s*@\s*(\d{1,2}:\d{2}\s*[AP]M)",
    "bagging": r"Any\s*player\s*who\s*bags[^.\n]{0,120}",
}
FEE_RE = re.compile(
    r"\$\s?([\d,]+)\s+of\s+the\s+\$\s?([\d,]+)\s+Buy[-'\s]?In\s+is\s+withheld\s+for\s+house\s*fees?"
    r"[\s\S]{0,300}?prize\s+pool\s+consists\s+of\s+\$\s?([\d,]+)",
    re.I,
)
FEE_ONLY_RE = re.compile(r"\$\s?([\d,]+)\s+of\s+the\s+\$\s?([\d,]+)\s+Buy[-'\s]?In\s+is\s+withheld", re.I)
POOL_ONLY_RE = re.compile(r"prize\s+pool\s+consists\s+of\s+\$\s?([\d,]+)\s+of\s+every\s+\$\s?([\d,]+)", re.I)
PAYOUT_RE = re.compile(r"pays\s+(?P<v>[\d.]+%)\s+of\s+the\s+field", re.I)
# Clauses that would actually settle the single-entry question. Re-entry wording is
# matched on purpose in BOTH directions: an explicit allowance is as decisive as an
# explicit prohibition.
CLAUSE_RULES = [
    ("single_entry_confirmed", r"(one|1)\s+entry\s+per\s+player|single[\s-]entry\s+(only|event|tournament)?|no\s+(additional|further|second)\s+entr(y|ies)|freeze\s?out|freezeout|maximum\s+of\s+(one|1)\s+entr(y|ies)"),
    ("entry_forbidden", r"one\s+entry\s+only|only\s+one\s+entry|no\s+re-?(?:entries?|buys?)|re-?(?:entries|buys?)\s+(?:are\s+)?(?:not\s+allowed|prohibited|forbidden)|no\s+add-?\s?ons?"),
    ("reentry_allowed", r"(unlimited|multiple|infinite)\s+(re-?entries?|re-?buys?)|re-?entries?\s*[:=]?\s*(allowed|permitted|unlimited)|players?\s+may\s+re-?enter|each\s+player\s+may\s+(re-?buy|re-?enter)"),
    ("reentry_limited", r"re-?entr(?:y|ies)\s+(?:through|up\s+to|until|for|during)\s+(?:the\s+)?(?:first\s+)?level\s*\d+|max(?:imum)?\s+(?:of\s+)?\d+\s+re-?entr|late\s+re-?buy"),
    ("addon_allowed", r"add-?\s?on\s*[:=]?\s*(?:allowed|permitted|available|optional|\$)|may\s+(?:purchase\s+an?\s+)?add-?\s?on|re-?buy\s+and\s+add-?\s?on"),
    ("addon_forbidden", r"no\s+add-?\s?ons?|add-?\s?ons?\s+(?:are\s+)?(?:not\s+allowed|prohibited|will\s+not\s+be)"),
]
SUBSEQUENT_ENTRY_RE = re.compile(
    r"subsequent\s+buy\s*-?\s*in'?s?|subsequent\s+entr(?:y|ies)|additional\s+buy\s*-?\s*in'?s?", re.I)


def audit_structure(text: str, url: str) -> dict:
    flat = re.sub(r"[ \t]+", " ", text)
    out: dict = {"source": url, "retrieved": today_utc()}
    for key, pat in FIELD_PATTERNS.items():
        if key == "title":
            continue
        m = re.search(pat, flat, re.I)
        out[key] = re.sub(r"\s+", " ", m.group("v" if "v" in (m.groupdict() or {}) else 0)).strip(" |") if m else None
    # The title line is the first printed line that looks like an event heading.
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    title = None
    for ln in lines[:12]:
        if re.search(r"\$\s?\d[\d,]*\s+.{3,40}", ln) and "license" not in ln.lower():
            title = re.sub(r"\s+", " ", ln)
            break
    out["title"] = title or (lines[0] if lines else None)
    fee = FEE_RE.search(flat)
    if fee:
        out["house_fee_usd"] = int(fee.group(1).replace(",", ""))
        out["buy_in_usd"] = int(fee.group(2).replace(",", ""))
        out["pool_per_entry_usd"] = int(fee.group(3).replace(",", ""))
    else:  # the two sentences are sometimes separated by a page-break artefact
        f2, p2 = FEE_ONLY_RE.search(flat), POOL_ONLY_RE.search(flat)
        out["house_fee_usd"] = int(f2.group(1).replace(",", "")) if f2 else None
        out["buy_in_usd"] = int(f2.group(2).replace(",", "")) if f2 else None
        if p2:
            out["pool_per_entry_usd"] = int(p2.group(1).replace(",", ""))
            out["buy_in_usd"] = out["buy_in_usd"] or int(p2.group(2).replace(",", ""))
        else:
            out["pool_per_entry_usd"] = None
    if not out.get("start_time"):
        fl = re.search(FIELD_PATTERNS["flight_start"], flat, re.I)
        out["start_time"] = fl.group(1) if fl else out.get("start_time")
        if fl:
            out["start_time_basis"] = "printed as the Day-A flight start on the sheet"
    pay = PAYOUT_RE.search(flat)
    out["payout_pct_of_field"] = pay.group("v") if pay else None

    clauses = {name: [] for name, _ in CLAUSE_RULES}
    for name, pat in CLAUSE_RULES:
        for m in re.finditer(pat, flat, re.I):
            s = max(0, m.start() - 90)
            clauses[name].append(re.sub(r"\s+", " ", flat[s:m.end() + 90]).strip())
    sub = SUBSEQUENT_ENTRY_RE.search(flat)
    out["clauses"] = clauses
    out["subsequent_entry_excerpt"] = (
        re.sub(r"\s+", " ", flat[max(0, sub.start() - 120):sub.end() + 120]).strip() if sub else None
    )

    confirm = clauses["single_entry_confirmed"] + clauses["entry_forbidden"] + clauses["addon_forbidden"]
    allow = clauses["reentry_allowed"] + clauses["addon_allowed"]
    if allow and confirm:
        out["entry_policy"] = "contradictory_in_sheet"
    elif confirm:
        out["entry_policy"] = "confirmed_single_entry"
    elif allow:
        out["entry_policy"] = "not_single_entry"
    elif clauses["reentry_limited"]:
        out["entry_policy"] = "limited_reentry"
    else:
        out["entry_policy"] = "not_stated_in_sheet"
    # Level count gives the sheet's own worst-case play clock; used only to flag
    # same-day overlap risk, never presented as an announced finish time.
    levels = [int(n) for n in re.findall(r"^\s*(\d{1,3})\s+\|\s*\d{2}", text, re.M)]
    out["levels_listed"] = max(levels) if levels else None
    out["breaks_listed"] = len(re.findall(r"Minute Break", text, re.I))
    return out


FACT_PATTERNS = {
    "resort_fee": r"[^.\n]{0,90}resort\s*fee[^.\n]{0,240}",
    # "lodging tax" is the wording MGM's hotel terms use instead of "room tax"; it is the sentence
    # that proves the resort fee itself is taxed, which the true-cost calculation depends on.
    "room_tax": r"[^.\n]{0,90}(?:13\.38|room\s+tax|state\s+room|lodging\s+tax(?:es)?)[^.\n]{0,240}",
    # added 2026-11-17 (arena/60ade3e8): per-occupant charges above double occupancy change the
    # room cost once a third or fourth player joins the room, so the clause is captured verbatim.
    "occupancy_charge": r"[^.\n]{0,90}(?:additional\s+(?:occupant\s+)?charge|per\s+occupant[^.\n]{0,60}per\s+night)[^.\n]{0,240}",
    "parking": r"[^.\n]{0,90}(?:self[- ]?parking|valet\s+parking|parking\s+(?:fee|rate|is))[^.\n]{0,240}",
    "cancellation": r"[^.\n]{0,90}(?:cancel\w*|no[- ]?show)[^.\n]{0,240}",
    "check_in_out": r"[^.\n]{0,90}(?:check[- ]in|check[- ]out)\s+(?:time|is|at|after|by)[^.\n]{0,240}",
    "walk": r"[^.\n]{0,90}(?:minutes?\s+(?:walk|walking)|walking\s+distance|skybridge|monorail)[^.\n]{0,240}",
}


def extract_facts(text: str) -> dict:
    """Verbatim sentences containing the wording we need — copied, never rewritten."""
    flat = re.sub(r"\s+", " ", text)
    # Amounts like "$55.00" and abbreviations like "i.e." used to cut a sentence in half, because the
    # clause patterns stop at a period. Those periods are masked so the quoted sentence stays whole;
    # the mask is undone before the sentence is stored, so what reaches the page is the original wording.
    flat = re.sub(r"(?<=\d)\.(?=\d)", "\u0000", flat)
    for abbr in ("i.e", "e.g", "vs", "approx", "No", "St"):
        flat = flat.replace(abbr + ".", abbr + "\u0001")
    out: dict[str, list[str]] = {}
    for key, pat in FACT_PATTERNS.items():
        hits: list[str] = []
        for m in re.finditer(pat, flat, re.I):
            sent = (re.sub(r"\s+", " ", m.group(0)).strip(" -|")
                    .replace("\u0000", ".").replace("\u0001", "."))
            if len(sent) >= 240:  # the excerpt hit the cap: do not end mid-word
                sent = sent[:239].rsplit(" ", 1)[0].rstrip(",;:") + "…"
            # a hit that opens with a piece of a URL is the tail of a link, not a sentence
            if re.match(r"^(?:https?://|www\.|[^ ]*\)\.html\)|html\)|\.html\b)", sent, re.I):
                continue
            if len(sent) > 24 and sent not in hits:
                hits.append(sent)
            if len(hits) >= 6:
                break
        if hits:
            out[key] = hits
    return out


# --------------------------------------------------------------- venetian overrides
VENETIAN_OVERRIDES = os.path.join(DATA, "c2242cb1", "venetian_overrides.json")


def apply_venetian_overrides(rows: list[dict]) -> list[dict]:
    """Apply data/c2242cb1/venetian_overrides.json to parsed Venetian schedule rows.

    Row-level corrections where the PDF extraction disagrees with the official
    schedule page and its structure sheets (page-style event names, conditional
    entry fees, rows a broken parse dropped). Applied here at scrape time AND by
    scripts/integrate_data.py at build time, so neither a re-scrape nor a stale
    snapshot can silently undo them. Each "set" must match exactly one row — or
    find a row already carrying the corrected values — otherwise the run stops
    rather than publishing a row that disagrees with the official page.
    """
    if not os.path.exists(VENETIAN_OVERRIDES):
        return rows
    ovr = read_json(VENETIAN_OVERRIDES, {})
    rows = [dict(r) for r in rows]
    for op in ovr.get("operations", []):
        if op["op"] == "set":
            m = op["match"]
            hits = [r for r in rows if r.get("date") == m["date"] and r.get("time") == m["time"]
                    and r.get("event_no") == m["event_no"]
                    and (not m.get("name_contains") or m["name_contains"] in (r.get("event_name") or "").upper())]
            if len(hits) == 1:
                hits[0].update(op["set"])
            elif len(hits) == 0:
                done = [r for r in rows if r.get("date") == m["date"] and r.get("event_no") == m["event_no"]
                        and all(r.get(k) == v for k, v in op["set"].items())]
                if not done:
                    raise SystemExit(f"venetian override matched no row and no corrected row exists: {m}")
            else:
                raise SystemExit(f"venetian override matched {len(hits)} rows (need exactly 1): {m}")
        elif op["op"] == "add":
            r = op["row"]
            if any(x.get("date") == r.get("date") and x.get("time") == r.get("time")
                   and x.get("event_no") == r.get("event_no") for x in rows):
                continue
            rows.append(dict(r))
        else:
            raise SystemExit(f"unknown override op: {op['op']}")
    return rows


# --------------------------------------------------------------------------- main
def from_raw(cfg: dict) -> int:
    """Offline re-derivation: rebuild the audit + schedule snapshots from the text
    already captured under data/raw (same code paths, no network). Lets the site be
    rebuilt reproducibly without re-fetching, and lets a parser fix be verified
    against the exact bytes that were fetched."""
    prev = read_json(os.path.join(DATA, "url-checks.json"), {})
    prev_audit = read_json(os.path.join(DATA, "structure-audit.json"), {"sheets": {}})
    sheets: dict[str, dict] = dict(prev_audit.get("sheets") or {})  # keep sheets we cannot re-derive offline
    rederived: list[str] = []
    snapshot_rows: list[dict] = []
    for entry in cfg["sources"]:
        dest = entry.get("save_text_to")
        if not dest:
            continue
        path = os.path.join(ROOT, dest)
        if not os.path.exists(path):
            continue
        raw = open(path, encoding="utf-8").read()
        text = raw.split("-->\n", 1)[-1] if raw.startswith("<!--") else raw
        url = entry["url"]
        checked = (prev.get(url) or {}).get("checked_at") or now_utc()
        if entry.get("parse") == "venetian-schedule-pdf":
            snapshot_rows.extend(apply_venetian_overrides(
                parse_schedule_pdf(text, url, entry.get("default_year"))))
        if entry.get("kind") == "pdf" and re.search(r"structure", url, re.I):
            key = entry.get("key") or url.rsplit("/", 1)[-1]
            audit = audit_structure(text, url)
            # keep the hash of the bytes this text was extracted from, so an
            # offline re-derivation stays traceable to the fetch it came from
            fetched_sha = (prev.get(url) or {}).get("sha256")
            if fetched_sha:
                audit["pdf_sha256"] = fetched_sha
            audit["rederived_from"] = dest
            sheets[key] = audit
            rederived.append(key)
    write_json(os.path.join(DATA, "structure-audit.json"), {
        "meta": {"generated_at": now_utc(), "generator": "tools/sync_official_sources.py --from-raw",
                 "rederived": len(rederived),
                 "policy": prev_audit.get("meta", {}).get("policy", ""), "sheets": sheets},
        "sheets": sheets,
        "schedule_rows": {"V_SCHED_PDF": snapshot_rows},
        "audit_schedule_rows": {k: len(v) for k, v in ((prev_audit.get("schedule_rows") or {}).items())},
    })
    write_json(os.path.join(DATA, "schedule-snapshot.json"), {
        "meta": {"generated_at": now_utc(), "rows": len(snapshot_rows),
                 "note": "Rows read from the official schedule text captured in data/raw; blank fields were not printed."},
        "rows": snapshot_rows,
    })
    print(f"[from-raw] sheets={len(sheets)} schedule_rows={len(snapshot_rows)} "
          f"dated={sum(1 for r in snapshot_rows if r.get('date'))}")
    return 0


def main() -> int:
    cfg = read_json(TRACKED, None)
    if not cfg:
        print(f"missing {TRACKED}", file=sys.stderr)
        return 2
    if "--from-raw" in sys.argv:
        return from_raw(cfg)
    os.makedirs(DATA, exist_ok=True)
    workdir = os.path.join(DATA, ".sync-tmp")
    os.makedirs(workdir, exist_ok=True)

    prev = read_json(os.path.join(DATA, "url-checks.json"), {})
    prev_audit = read_json(os.path.join(DATA, "structure-audit.json"), {"sheets": {}})
    change_log = read_json(os.path.join(DATA, "change-log.json"), {"entries": []})
    checks: dict[str, dict] = {}
    sheets: dict[str, dict] = prev_audit.get("sheets", {})
    snapshot_rows: list[dict] = []
    changed_urls: list[str] = []
    facts: dict[str, dict] = {}

    for entry in cfg["sources"]:
        url = entry["url"]
        kind = entry.get("kind", "page")
        res = fetch(url)
        rec: dict = {
            "url": url,
            "label": entry.get("label", ""),
            "venue": entry.get("venue"),
            "kind": kind,
            "checked_at": now_utc(),
            "ok": res.get("ok", False),
            "status": res.get("status"),
        }
        if res.get("ok"):
            rec["bytes"] = res["bytes"]
            rec["sha256"] = res["sha256"]
            rec["etag"] = res.get("etag")
            rec["last_modified"] = res.get("last_modified")
            rec["content_type"] = res.get("content_type")
            before = prev.get(url) or {}
            rec["previous_sha256"] = before.get("sha256")
            rec["first_run"] = not bool(before)
            # Raw bytes on a marketing page move for cosmetic reasons; that is recorded
            # but is NOT treated as a data change. Rows are only flagged from value diffs.
            rec["bytes_changed"] = bool(before.get("sha256")) and before["sha256"] != res["sha256"]
            rec["values_changed"] = None  # set below once text has been parsed
            body = res.pop("body")
            text = None
            if kind == "pdf":
                text, note = pdf_to_text(body, workdir)
                rec["extractor"] = note
                rec["text_chars"] = len(text) if text else 0
                if text:
                    key = entry.get("key") or url.rsplit("/", 1)[-1]
                    audit = audit_structure(text, url)
                    audit["pdf_sha256"] = res["sha256"]
                    old = sheets.get(key)
                    if old:
                        diffs = {
                            f: {"was": old.get(f), "now": audit.get(f)}
                            for f in ("event_numbers", "start_time", "guarantee", "buy_in_usd",
                                      "house_fee_usd", "pool_per_entry_usd", "entry_policy")
                            if old.get(f) != audit.get(f)
                        }
                        if diffs:
                            audit["changed_fields"] = diffs
                            rec["values_changed"] = True
                            rec["changed_values"] = diffs
                            changed_urls.append(url)
                            change_log["entries"].insert(0, {
                                "at": rec["checked_at"], "url": url, "scope": "structure",
                                "key": key, "diff": diffs,
                            })
                    sheets[key] = audit
            else:
                text = html_to_text(body)
                if entry.get("parse") == "venetian-schedule":
                    rows = parse_schedule(text, url)
                    snapshot_rows.extend(rows)
                    rec["schedule_rows_parsed"] = len(rows)
            if entry.get("parse") == "venetian-schedule-pdf" and text:
                rows = apply_venetian_overrides(parse_schedule_pdf(text, url, entry.get("default_year")))
                key = entry.get("key") or url.rsplit("/", 1)[-1]
                diff = diff_schedule((prev_audit.get("schedule_rows") or {}).get(key), rows)
                if diff:
                    rec["values_changed"] = True
                    rec["schedule_diff"] = diff
                    changed_urls.append(url)
                    change_log["entries"].insert(0, {
                        "at": rec["checked_at"], "url": url, "scope": "schedule",
                        "key": key, "diff": diff,
                    })
                rows_by_time = sorted(rows, key=lambda r: (r.get("date") or "9999", r["time"]))
                snapshot_rows.extend(rows_by_time)
                rec["schedule_rows_parsed"] = len(rows)
            if entry.get("save_text_to") and text:
                dest = os.path.join(ROOT, entry["save_text_to"])
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "w", encoding="utf-8") as fh:
                    fh.write(f"<!-- captured {rec['checked_at']} from {url} (sha256 {rec['sha256']}) -->\n")
                    fh.write(text)
                rec["saved_text_to"] = entry["save_text_to"]
            if entry.get("extract_facts") and text:
                facts[url] = {"label": entry.get("label"), "venue": entry.get("venue"),
                              "url": url, "retrieved": rec["checked_at"], "sha256": rec["sha256"],
                              "facts": extract_facts(text)}
            if text is not None:
                rec["text_sha256"] = hashlib.sha256(
                    re.sub(r"\s+", " ", text).encode("utf-8")).hexdigest()
                if rec["bytes_changed"]:
                    prev_text = prev.get(url, {}).get("text_sha256")
                    rec["text_changed"] = (prev_text != rec["text_sha256"]) if prev_text else None
            if entry.get("keep_text_excerpt") and text:
                n = int(entry.get("excerpt_chars") or 600)
                rec["text_head"] = text[:n]
        else:
            rec["error"] = res.get("error")
            rec["content_changed"] = None
            if (prev.get(url) or {}).get("sha256"):
                rec["previously_ok"] = True
        checks[url] = rec

    change_log["entries"] = change_log["entries"][:400]
    write_json(os.path.join(DATA, "url-checks.json"), checks)
    write_json(os.path.join(DATA, "structure-audit.json"), {
        "schedule_rows": {k: v for k, v in [(e.get("key") or e["url"], snapshot_rows)
                                             for e in cfg["sources"]
                                             if e.get("parse") == "venetian-schedule-pdf"]},
        "meta": {
            "generated_at": now_utc(),
            "generator": "tools/sync_official_sources.py",
            "policy": "Field values are matched from the fetched sheet text only. "
                      "entry_policy='not_stated_in_sheet' means the sheet contains no clause about "
                      "entries/re-entries/add-ons — that is NOT confirmation of single-entry play.",
        },
        "sheets": sheets,
    })
    write_json(os.path.join(DATA, "schedule-snapshot.json"), {
        "meta": {"generated_at": now_utc(), "rows": len(snapshot_rows),
                 "note": "Rows read from the official schedule page at run time; blank fields were not printed on the page."},
        "rows": snapshot_rows,
    })
    write_json(os.path.join(DATA, "hotel-facts.json"), {
        "meta": {"generated_at": now_utc(),
                 "policy": "Sentences are copied verbatim from the fetched official page/PDF. "
                           "A fact is only recorded when the wording is actually present; "
                           "nothing is summarised, rounded or inferred."},
        "sources": facts,
    })
    write_json(os.path.join(DATA, "change-log.json"), {
        "meta": {"generated_at": now_utc(), "changed_urls_this_run": changed_urls},
        "entries": change_log["entries"],
    })
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            ok = sum(1 for v in checks.values() if v.get("ok"))
            fh.write(f"## Official source sync ({rec['checked_at']})\n\n")
            fh.write(f"- URLs checked: **{len(checks)}** (ok {ok}, failed {len(checks) - ok})\n")
            fh.write(f"- Content changed this run: **{len(changed_urls)}**\n")
            fh.write(f"- Structure sheets audited: **{len(sheets)}**\n")
            fh.write(f"- Schedule rows parsed: **{len(snapshot_rows)}**\n")
            for u in changed_urls[:20]:
                fh.write(f"  - value changed: {u}\n")
    dated = sum(1 for r in snapshot_rows if r.get("date"))
    sample_head = None
    for u2 in [e["url"] for e in cfg["sources"] if e.get("parse") == "venetian-schedule-pdf"]:
        body = (checks.get(u2) or {}).get("text_head") or ""
        flat = re.sub(r"\s+", " ", body)
        m = PDF_DATE_RE.search(flat)
        sample_head = flat[max(0, m.start() - 60):m.end() + 90] if m else "no date header matched"
    write_json(os.path.join(DATA, "sync-status.json"), {
        "generated_at": now_utc(),
        "urls_checked": len(checks),
        "urls_failed": [u for u, v in checks.items() if not v.get("ok")],
        "changed_this_run": changed_urls,
        "sheets_audited": len(sheets),
        "schedule_rows": len(snapshot_rows),
        "schedule_rows_with_date": dated,
        "date_head_sample": sample_head,
        "hotel_fact_sources": len(facts),
    })
    print(f"checked={len(checks)} changed={len(changed_urls)} sheets={len(sheets)} rows={len(snapshot_rows)} dated={dated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
