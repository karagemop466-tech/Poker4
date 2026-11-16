#!/usr/bin/env python3
"""Build the static GitHub Pages site in df41f5c6/ (served at /df41f5c6/) from data/df41f5c6/*.json.

Every table row links to an official source from data/sources.json.
Blank values stay blank and are flagged, never inferred.
"""
import datetime as dt
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "df41f5c6")
OUT = os.path.join(ROOT, "df41f5c6")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


SOURCES = load("sources.json")["sources"]
TOURN = load("tournaments.json")["rows"]
HOTELS = load("hotels.json")["rows"]
FLAGS = {f["id"]: f for f in load("flagged.json")["items"]}

E = html.escape


def src_link(sid):
    if not sid or sid not in SOURCES:
        return "<em>none</em>"
    s = SOURCES[sid]
    return f'<a href="{E(s["url"])}" rel="noopener">{E(sid)}</a>'


def flag_links(ids):
    if not ids:
        return ""
    return " ".join(f'<a class="flag" href="flagged.html#{E(i)}">{E(i)}</a>' for i in ids)


def money(v):
    return "" if v is None else f"${v:,.0f}"


def date_label(iso):
    if not iso:
        return ""
    d = dt.date.fromisoformat(iso)
    return d.strftime("%a %b %-d, %Y")


def start_minutes(text):
    """First clock time in a row's time string, in minutes after midnight."""
    m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", text or "")
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    h = h % 12 + (12 if ap == "PM" else 0)
    return h * 60 + mi


def page(title, body, active):
    nav = [
        ("index.html", "Dashboard"),
        ("tournaments.html", "Tournaments"),
        ("other-formats.html", "Spend-more &amp; re-entry"),
        ("hotels.html", "Hotels"),
        ("schedule.html", "Schedule"),
        ("questions.html", "Questions"),
        ("suggestions.html", "Suggestions"),
        ("flagged.html", "Flagged for Review"),
        ("repo-review.html", "Repo review"),
        ("sources.html", "Sources"),
    ]
    links = "".join(
        f'<a href="{h}"{" class=active" if h == active else ""}>{t}</a>' for h, t in nav
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · Las Vegas Strip poker</title>
<link rel="stylesheet" href="style.css"></head>
<body>
<header><h1><a href="index.html">Las Vegas Strip poker</a></h1>
<p class="sub">Data as of 2026-11-16 (UTC). Official sources only. Blank = not verified.</p>
<nav>{links}</nav></header>
<main>
<h2>{E(title)}</h2>
{body}
</main>
<footer>Built from <a href="https://github.com/karagemop466-tech/Poker4">karagemop466-tech/Poker4</a>. Flags do not block publication.</footer>
</body></html>
"""


def table(headers, rows):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def sort_key(r):
    gtd = r.get("gtd") or 0
    return (-(r.get("buy_in") or 0), -gtd)


main_rows = sorted([r for r in TOURN if r["section"] == "main"], key=sort_key)
other_rows = sorted([r for r in TOURN if r["section"] == "other"], key=sort_key)
venetian_main = [r for r in main_rows if r["venue"].startswith("Venetian")]
wynn_main = [r for r in main_rows if r["venue"].startswith("Wynn")]
dated_main = [r for r in main_rows if r["date"]]

# ---------- Dashboard ----------
top_buy = main_rows[:3]
top_gtd = sorted([r for r in main_rows if r.get("gtd")], key=lambda r: -r["gtd"])[:3]

def cardline(r):
    return f'{money(r["buy_in"])} · {E(r["name"])} ({E(r["venue"])}, {E(r["date"] or "date unconfirmed")})'

dash = f"""
<section class="cards">
<a class="card" href="tournaments.html"><b>{len(main_rows)}</b><span>single-entry rows (main list)</span></a>
<a class="card" href="other-formats.html"><b>{len(other_rows)}</b><span>re-entry, rebuy, satellite rows</span></a>
<a class="card" href="hotels.html"><b>{len(HOTELS)}</b><span>hotels checked (1 with official fee)</span></a>
<a class="card" href="schedule.html"><b>{len(dated_main)}</b><span>dated main-list rows in the schedule</span></a>
<a class="card" href="flagged.html"><b>{len(FLAGS)}</b><span>flagged items for review</span></a>
</section>
<h3>Executive summary</h3>
<ul>
<li><b>Live now:</b> The Venetian DeepStack IV runs Nov 16 – Dec 23, 2026 (official schedule). The Wynn WPT World Championship runs Nov 27 – Dec 21 (official PDF). Both are single-entry in their official listings.</li>
<li><b>Highest buy-ins (main list):</b> {"; ".join(cardline(r) for r in top_buy)}.</li>
<li><b>Largest guarantees (main list):</b> {"; ".join(cardline(r) for r in top_gtd)}.</li>
<li><b>Separate section:</b> Caesars Palace daily events use re-entry with an optional $50 add-on, so they are kept out of the main list. Wynn's Friday $240 event is a rebuy and is also separate. Venetian $260 satellites are separate.</li>
<li><b>Hotels:</b> Only the Venetian has an official resort fee ($55 plus tax per night). Its one dated booking snapshot (Dec 18–20, 2026, 2 adults) works out to $512.20 per night all-in. No hotel is confirmed within the 30-minute walking limit because no walking times were verified.</li>
<li><b>Schedule:</b> No verified main-list event starts before 10:00 AM. The only earlier verified start is a 9:10 AM satellite (Venetian event #46, Dec 11), which is a satellite and not a cash entry. So 8:00–10:00 AM has no verified main-list event. See the schedule page for the day-by-day list.</li>
<li><b>Gaps:</b> Caesars Palace, MGM Grand, Horseshoe, ARIA, Bellagio, Planet Hollywood, Resorts World, Golden Nugget, Orleans and South Point are not listed with verified buy-ins or fees. See the Flagged for Review page.</li>
</ul>
"""
open_page = page("Dashboard", dash, "index.html")

# ---------- Tournaments ----------
rows = []
for i, r in enumerate(main_rows, 1):
    rows.append([
        str(i), money(r["buy_in"]), money(r["gtd"]), E(r["name"]), E(r["venue"]),
        E(date_label(r["date"])) or "<em>unconfirmed</em>", E(r["time"] or ""), E(r["entry"]),
        flag_links(r["flags"]), src_link(r["source"]),
    ])
tour_body = (
    "<p>Single-entry only. Ranked by buy-in (highest first), then by guarantee. "
    "Daily rows have no dates. A blank cell means not verified.</p>"
    + table(["#", "Buy-in", "GTD", "Event", "Venue", "Date", "Time", "Entry", "Flags", "Source"], rows)
)
open_tour = page("Tournaments — single-entry, ranked by buy-in", tour_body, "tournaments.html")

# ---------- Other formats ----------
rows = []
for r in other_rows:
    rows.append([
        money(r["buy_in"]), money(r["gtd"]), E(r["name"]), E(r["venue"]),
        E(date_label(r["date"])) or "<em>unconfirmed</em>", E(r["time"] or ""), E(r["entry"]),
        flag_links(r["flags"]), src_link(r["source"]),
    ])
other_body = (
    "<p>These events are <b>not</b> single-entry: re-entry, rebuy, add-on, or satellite entries. "
    "Kept separate from the main list.</p>"
    + table(["Buy-in", "GTD", "Event", "Venue", "Date", "Time", "Entry rules", "Flags", "Source"], rows)
)
open_other = page("Spend-more, re-entry and satellite events", other_body, "other-formats.html")

# ---------- Hotels ----------
rows = []
for h in HOTELS:
    rows.append([
        E(h["hotel"]), E(h["near_venue"]),
        money(h["resort_fee_per_night_usd"]) if h["resort_fee_per_night_usd"] is not None else "",
        E(h["resort_fee_note"]),
        money(h["all_in_per_night_usd"]) if h["all_in_per_night_usd"] is not None else "",
        E(h["all_in_example"]),
        E(h["walk_note"]) if h["walk_minutes"] is None else f'{h["walk_minutes"]} min',
        flag_links(h["flags"]), src_link(h["source"]),
    ])
hotel_body = (
    "<p><b>Walking limit (30 min):</b> not confirmed for any hotel, because no walking-time source was read. "
    "Resort-fee values are shown only where an official page was read. Per-night all-in is computed from a dated booking snapshot.</p>"
    + table(["Hotel", "Near venue", "Resort fee / night", "Fee note", "All-in / night", "Example", "Walk to venue", "Flags", "Source"], rows)
)
open_hotels = page("Hotels near the tournament venues", hotel_body, "hotels.html")

# ---------- Schedule ----------
by_day = {}
for r in dated_main:
    by_day.setdefault(r["date"], []).append(r)
blocks = []
for d in sorted(by_day):
    evs = sorted(by_day[d], key=lambda r: (start_minutes(r["time"]) or 0))
    rows = []
    for r in evs:
        rows.append([E(r["time"] or ""), money(r["buy_in"]), money(r["gtd"]), E(r["name"]), E(r["venue"]),
                     flag_links(r["flags"]), src_link(r["source"])])
    blocks.append(f"<h3>{E(date_label(d))}</h3>" + table(["Start", "Buy-in", "GTD", "Event", "Venue", "Flags", "Source"], rows))
sched_body = """
<p><b>How to read this:</b> Only verified start times are shown. Event lengths and registration-close times are not verified,
so two events on the same day may overlap. Treat each day as a menu of options, not a fixed plan.</p>
<p><b>8:00–10:00 AM:</b> no verified main-list event starts in this window. The earliest verified main-list start is 10:00 AM. A 9:10 AM satellite (Venetian #46, Dec 11) is on the Spend-more &amp; satellite page only.</p>
<p>Rows with no date (daily Wynn and undated Venetian rows) are listed on the Tournaments page only.</p>
""" + "".join(blocks)
open_sched = page("Day-by-day schedule (verified start times)", sched_body, "schedule.html")

# ---------- Questions ----------
qs = [
    ("Caesars Palace daily NLH buy-ins", "Official flyer: $100 (10 AM, 6 PM) and $160 (2 PM, 9 PM); $1,000 GTD; re-entry; $50 add-on.", "Caesars Palace resort fee; event date range.", "Ask the Caesars Palace poker room, or check the official Caesars flyer for a date range."),
    ("Caesars Palace resort fee", "Not verified on an official page.", "The per-night fee.", "Open the Caesars Palace resort-fee or hotel-terms page and record the fee and tax line."),
    ("MGM Grand resort fee", "Third-party sources only: $50 plus tax per night.", "Official fee.", "Open MGM Grand hotel terms on the official site; confirm the fee."),
    ("MGM Grand daily tournament times and buy-ins", "Official page lists 11 AM, 7 PM, 11 PM. Third-party conflict.", "Buy-ins; whether tournaments currently run.", "Call the MGM Grand poker room or check the official page again."),
    ("Horseshoe tournament times and buy-ins", "Official page confirms six daily times.", "Times and buy-ins.", "Call the Horseshoe poker room; check the official page."),
    ("ARIA tournaments", "Official page: room only. Third-party mentions a $200 NL and an Aria Poker Open.", "Official schedule and buy-ins.", "Call ARIA poker room or follow the official poker social channel listed on its page."),
    ("Bellagio, Planet Hollywood, Resorts World, Golden Nugget, Orleans, South Point", "Official poker pages were not usable (not found, error, empty, or off-Strip).", "Current tournaments and buy-ins.", "Check each property's official site in a browser, then call its poker room."),
    ("Venetian rows with missing dates", "Events #47 1A, #49 1A and #58 lack dates in the extracted PDF text.", "Exact dates.", "Re-open the official DSE schedule PDF in a browser and read those rows."),
    ("Venetian Dec 8 LIPS Ladies and Dec 9 rows", "Partially captured.", "Buy-in, guarantee, time.", "Re-read the schedule PDF for those dates."),
    ("Venetian RaceDay Stack and #6 guarantees", "Not captured.", "Guarantees.", "Re-read the schedule PDF."),
    ("Wynn daily poster day mapping", "Poster shows day-specific guarantees, but the mapping is ambiguous.", "Which guarantee applies on which day.", "Check the current Wynn poker page or call the room."),
    ("Wynn WPT structures", "Structure PDF not read beyond general terms.", "Blinds, levels, re-entry rules.", "Open the official structure PDF from the Wynn WPT schedule."),
    ("Walking time to each venue", "No source read.", "Whether any hotel is within 30 minutes on foot.", "Use a map service to walk-route each hotel to its venue, then record the time with its source."),
    ("Hotel quality and ratings", "No source read for ratings.", "Quality comparison.", "Use official room pages and a rating source; add with a source link."),
    ("Your dates, budget and travel plan", "Not provided.", "Which days to plan around.", "Provide the dates; the schedule can then be narrowed."),
    ("DeepStack NYE and Showdown schedules", "Series announced; event schedule not read.", "Events after Dec 23.", "Open the official DeepStack pages in a browser."),
    ("Wynn Signature Series", "Jan 11–24, 2027; schedule PDF not read.", "Events in that window.", "Open the official Wynn Signature Series schedule."),
]
QSRC = ['S7', 'S7', 'S9', 'S9', 'S8', 'S10', 'S11', 'S1', 'S1', 'S1', 'S5', 'S6', 'S2', 'S2', 'S15', 'S1', 'S5']
rows = [[E(a), E(b), E(c), E(d), " ".join(src_link(s) for s in ([x] if isinstance(x, str) else x))] for (a, b, c, d), x in zip(qs, QSRC)]
q_body = ("<p>Known = verified from an official source. Missing = not verified. Each missing item has a way to find it.</p>"
          + table(["Topic", "Known (verified)", "Missing", "How to find it", "Source"], rows)
          + "<p>Sources: see the <a href=\"sources.html\">Sources</a> page.</p>")
open_q = page("Questions, known facts and gaps", q_body, "questions.html")

# ---------- Suggestions (decision-only) ----------
sugg = [
    ("S1", "Add a date filter to the tournaments and schedule pages", "Option A: yes, add filter. Option B: no. Option C: add date only, no filter."),
    ("S2", "Add a day-planner that shows conflicts for each day", "Option A: yes, using verified durations only (none yet). Option B: no. Option C: add after durations are verified."),
    ("S3", "Automate weekly checks of official pages", "Option A: yes, a scheduled job that re-reads each source and flags changes. Option B: manual only. Option C: check monthly."),
    ("S4", "Add a Caesars/MGM/Horseshoe/ARIA verification pass", "Option A: yes, add each as a table once verified. Option B: keep flagged only. Option C: add as soon as values exist."),
    ("S5", "Add a hotel comparison with verified walk times", "Option A: yes, once a walking source is chosen. Option B: no walking times. Option C: distance in miles only."),
]
rows = [[E(a), E(b), E(c), "<em>Awaiting your choice</em>", src_link("S15")] for a, b, c in sugg]
s_body = ("<p>Nothing on this page is implemented. Please choose an option per row; "
          "changes are made only after your choice. All suggestions are listed here and are not applied.</p>"
          + table(["ID", "Suggestion", "Choices", "Status", "Basis"], rows))
open_s = page("Site suggestions (review before any change)", s_body, "suggestions.html")

# ---------- Flagged ----------
rows = []
for f in FLAGS.values():
    srcs = " ".join(src_link(s) for s in (f["sources"] or []))
    rows.append([f'<span id="{E(f["id"])}"><b>{E(f["id"])}</b></span>', E(f["title"]), E(f["detail"]), srcs or "<em>none</em>"])
fl_body = ("<p>These items do not block the merge. Each is unverified or irregular and should be checked before relying on it.</p>"
           + table(["ID", "Item", "Detail", "Source"], rows))
open_f = page("Flagged for Review", fl_body, "flagged.html")

# ---------- Repo review ----------
rr = [
    ("README.md", "One-line README. Describes no project, scope or usage.", "Flagged (F24)", "S15"),
    ("Git history", "One commit (52654c1, Initial commit).", "Note", "S15"),
    ("LICENSE", "Not present.", "Flagged (F24)", "S15"),
    (".gitignore", "Not present.", "Flagged (F24)", "S15"),
    ("GitHub Pages", "Enabled; legacy build from main root, with no site files, so the published page was empty. Now served from /docs.", "Flagged (F24)", "S15"),
    ("COORDINATION.md", "Added this session as the shared task board.", "Note", "S15"),
    ("Branch rules", "Session rules name a single branch; the brief asked for per-task branches. Single-branch rule followed.", "Note", "S15"),
]
rows = [[E(a), E(b), E(c), src_link(d)] for a, b, c, d in rr]
rr_body = ("<p>Line-by-line review. The repo has one tracked file and one commit.</p>"
           + table(["Item", "Finding", "Status", "Source"], rows))
open_rr = page("Repo review", rr_body, "repo-review.html")

# ---------- Sources ----------
rows = [[E(k), E(v["title"]), E(v["type"]), f'<a href="{E(v["url"])}">{E(v["url"])}</a>'] for k, v in SOURCES.items()]
so_body = "<p>Every table row links to one of these sources. Accessed 2026-11-16.</p>" + table(["ID", "Title", "Type", "URL"], rows)
open_so = page("Sources", so_body, "sources.html")

pages = {
    "index.html": open_page,
    "tournaments.html": open_tour,
    "other-formats.html": open_other,
    "hotels.html": open_hotels,
    "schedule.html": open_sched,
    "questions.html": open_q,
    "suggestions.html": open_s,
    "flagged.html": open_f,
    "repo-review.html": open_rr,
    "sources.html": open_so,
}

os.makedirs(OUT, exist_ok=True)
for name, body in pages.items():
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(body)

with open(os.path.join(OUT, "style.css"), "w", encoding="utf-8") as fh:
    fh.write("""body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1d1d1f;background:#fafafa;line-height:1.45}
header{background:#14532d;color:#fff;padding:14px 24px}
header h1{margin:0;font-size:22px}header h1 a{color:#fff;text-decoration:none}
.sub{margin:4px 0 8px;font-size:13px;opacity:.9}
nav a{color:#d1fae5;margin-right:12px;text-decoration:none;font-size:14px}
nav a.active{color:#fff;font-weight:700;border-bottom:2px solid #fff}
main{padding:18px 24px;max-width:1280px}
h2{margin-top:4px}h3{margin-top:24px}
.cards{display:flex;flex-wrap:wrap;gap:12px;margin:10px 0 18px}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;min-width:180px;text-decoration:none;color:inherit}
.card b{display:block;font-size:26px;color:#14532d}
.card span{font-size:13px;color:#4b5563}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13.5px}
th,td{border-bottom:1px solid #e5e7eb;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#f3f4f6;position:sticky;top:0}
a.flag{background:#fef3c7;color:#92400e;border-radius:4px;padding:0 4px;font-size:12px;text-decoration:none}
footer{padding:12px 24px;font-size:12px;color:#6b7280}
""")

print("built", len(pages), "pages;", len(main_rows), "main,", len(other_rows), "other,", len(dated_main), "dated")
