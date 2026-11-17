# -*- coding: utf-8 -*-
"""Render the root site pages from data/integrated/*.json (run build_integrated.py first)."""
import json, os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(ROOT, "data", "integrated")

def load(n):
    with open(os.path.join(OUTD, n), encoding="utf-8") as f:
        return json.load(f)

DATA = load("events.json")
HOTELS = load("hotels.json")
SOURCES = load("sources.json")
PLAN = load("plan.json")
FLAGS = load("flags.json")
try:
    MONITORING = load("monitoring.json")
except FileNotFoundError:
    MONITORING = {"checks": []}
CHANGED_URLS = {c.get("url") for c in MONITORING.get("checks", [])
                if str(c.get("changed", "")).lower().startswith("yes") or
                   str(c.get("status", "")).lower().startswith("changed")}
EVENTS = DATA["events"]
TODAY = DATA["meta"]["built"]
VEN_SCHED = "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"
WPT_SCHED = "https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf"
WPT_STRUCTS = "https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf"
VEN_POKER_RATES = "https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html"
VEN_BOOK = HOTELS["hotels"][0]["booking_url"]

NAV = [("index.html","Overview"),("tournaments.html","Tournaments"),("schedule.html","Daily plan"),
       ("hotels.html","Hotels"),("calculator.html","Trip calculator"),("venues/venetian.html","Venetian"),
       ("venues/wynn.html","Wynn"),("venues/others.html","Other venues"),("monitoring.html","Change monitor"),
       ("questions.html","Questions"),("suggestions.html","Suggestions"),("flagged.html","Flagged"),
       ("sources.html","Sources"),("archive.html","Archive")]

def esc(s):
    return html.escape(str(s if s is not None else ""))

def link(url, label=None):
    if not url: return ""
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(label or "source"))

def page(filename, title, body, extra_head=""):
    pre = "../" if "/" in filename else ""
    nav = "".join('<a href="%s%s"%s>%s</a>' % (pre, u, ' class="active"' if u == filename else "", t) for u, t in NAV)
    doc = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s — Poker4</title><link rel="stylesheet" href="%sassets/dashboard.css">%s</head>
<body><header><div class="wrap"><h1>%s</h1><p class="sub">Poker4 — Las Vegas Strip tournament &amp; hotel research · data last checked %s · every row links an official source</p>
<nav>%s</nav></div></header>
<main class="wrap">%s</main>
<footer class="wrap"><p>Poker4 · built %s · verified values come from official property/organizer sources only. Unverified values are left blank and listed on the <a href="%sflagged.html">Flagged for Review</a> page. Guaranteed-pool ratios are descriptive arithmetic, not forecasts.</p></footer>
<script src="%sassets/dashboard.js"></script></body></html>""" % (esc(title), pre, extra_head, esc(title), TODAY, nav, body, TODAY, pre, pre)
    out = os.path.join(ROOT, filename)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)

def table(headers, rows, attrs=""):
    h = "".join("<th>%s</th>" % x for x in headers)
    b = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return '<table class="tbl" %s><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (attrs, h, b)

def money(v):
    return ("$%s" % format(v, ",d")) if isinstance(v, int) else ("$%s" % v if v else "")

def ratio_cell(e):
    if e["buy_in"] and e["guarantee"] and not e["gtd_note"] and e["section"] not in ("satellite", "bounty"):
        return "%.1f&times;" % (e["guarantee"] / e["buy_in"])
    if e["buy_in"] and e["guarantee"]:
        return "see note"
    return "—"

def rule_cell(e):
    st = e["entry_status"]
    lbl = {"not-stated": '<span class="badge unverified">unverified</span>',
           "re-entry-confirmed": '<span class="badge bad">re-entry confirmed</span>',
           "rebuy-add-on": '<span class="badge bad">rebuy + add-on</span>',
           "subsequent-buy-ins": '<span class="badge bad">multi-entry indicated</span>',
           "flights-bagging-rule": '<span class="badge warn">flights (bagging rule)</span>'}.get(st, esc(st))
    return lbl + ' <span class="det" title="%s">details</span>' % esc(e["entry_excerpt"][:300])

def src_cell(e):
    parts = [link(u, "src %d" % (i+1)) for i, u in enumerate(e["source_urls"][:2])]
    return " ".join(parts)

def event_row(e, with_date=True):
    r = []
    if with_date:
        date_cell = esc(e["date"])
        conflict = next((f for f in e.get("flags", []) if f.startswith("official schedule date/weekday conflict:")), None)
        if conflict:
            date_cell += ' <span class="badge warn" title="%s">date/weekday conflict</span>' % esc(conflict)
        r.append(date_cell)
    event_name = esc(e["name"])
    if CHANGED_URLS.intersection(e.get("source_urls", [])):
        event_name += ' <span class="badge warn" title="An official source changed since the previous scheduled check; review this row.">SOURCE CHANGED</span>'
    r += [esc(e["time"]), esc(e["venue"]), event_name,
          money(e["buy_in"]) or "—", money(e["guarantee"]) or "—",
          ratio_cell(e), rule_cell(e), esc(e["late_reg"]) or "—", esc(e["last_checked"]), src_cell(e)]
    return r

EV_HEAD = ["Date","Time","Venue","Event","Total entry","Guaranteed pool","Pool ÷ entry","Entry rules","Late reg. closes","Last checked","Sources"]

def section_rows(section, with_date=True):
    return [event_row(e, with_date) for e in EVENTS if e["section"] == section and e["kind"] != "restart"]

def filterbar(dates=True, freezeout=True, walk=False, placeholder="Search all columns…"):
    p = ['<div class="filters"><input type="search" class="searchbox" placeholder="%s" data-search>' % placeholder]
    if dates:
        opts = sorted({e["date"] for e in EVENTS if re.match(r"2026-", str(e["date"]))})
        p.append('<label>Date <select data-datefilter><option value="">All dates</option>%s</select></label>' %
                 "".join('<option value="%s">%s</option>' % (d, d) for d in opts))
    if freezeout:
        p.append('<label><input type="checkbox" data-freezeout> Single-entry / freezeout confirmed only</label>')
    if walk:
        p.append('<label><input type="checkbox" data-walkfilter> Verified ≤30 min walk only</label>')
    p.append('<span class="rowcount" data-rowcount></span></div>')
    return "".join(p)

# ---------------------------------------------------------------- overview
def build_index():
    nv = len([e for e in EVENTS if e["venue"]=="Venetian" and e["kind"]!="restart"])
    nw = len([e for e in EVENTS if e["venue"]=="Wynn" and e["kind"]!="restart"])
    body = []
    body.append('<section class="cards">'
        '<div class="card"><h3>%d</h3><p>Venetian DSE IV rows<br><span class="muted">Nov 16 – Dec 23, 2026 · all 37 structure sheets read</span></p></div>'
        '<div class="card"><h3>%d</h3><p>Wynn rows<br><span class="muted">WPT World Championship + dailies</span></p></div>'
        '<div class="card"><h3>0</h3><p>freezeout-confirmed events<br><span class="muted">no sheet confirms single-entry — see Flagged</span></p></div>'
        '<div class="card"><h3>%d</h3><p>flagged items<br><span class="muted">published, none block decisions silently</span></p></div>'
        '</section>' % (nv, nw, len(FLAGS["flags"])))
    body.append('<h2>Executive summary</h2>'
        '<p>The current window contains the <b>Venetian DeepStack Extravaganza IV</b> (Nov 16 – Dec 23, 2026; $3.6M+ in stated guarantees) and the <b>Wynn WPT World Championship</b> (Nov 27 – Dec 21, 2026). '
        'Every Venetian structure sheet (37) and every Wynn daily/WPT terms page was read from official PDFs on %s. '
        '<b>Not a single event is confirmed single-entry/freezeout</b>: Venetian sheets never state an entry-count rule (one sheet even references &ldquo;subsequent buy in&rsquo;s&rdquo;), and every Wynn daily explicitly allows re-entry (the Friday event adds unlimited rebuys and an add-on). '
        'Those spend-advantage events are kept in their own sections.</p>' % TODAY)
    body.append('<p><b>Single-entry recommendation status:</b> no event can yet be recommended or ranked as a confirmed single-entry tournament. The tournament tables retain confirmed entry/guarantee arithmetic as descriptive reference only, while entry-policy-unknown, re-entry, flight, bounty and satellite events remain separated and labeled. Obtain written maximum-entry / no-rebuy / no-add-on terms before ranking candidates.</p>')
    body.append('<p><b>Hotels</b>: The Venetian is the only property with a fully verified cost picture ($55 + tax resort fee, 13.38% Clark County tax, $20/day self-parking, cancellation terms, conditional poker rates from $119/$209 with a play requirement). '
        'Verified walks: Venetian-bound cross-property routes are ≤30 min except ARIA (31 min); Wynn-bound routes are ≤30 min except Bellagio (32 min) and ARIA (42 min). Wynn internal hotel-to-poker-room time remains unmeasured. '
        'The <a href="calculator.html">trip calculator</a> uses only user-provided rates and dates, plus verified fees; no stay quote or occupancy is assumed.</p>')
    body.append('<p><b>Daily plan</b>: the <a href="schedule.html">Daily plan</a> gives each day a primary event and a conditional fallback using verified start times, verified late-registration cutoffs and labeled duration estimates; overlapping pairs are flagged rather than sequenced impossibly. '
        'Note: no official schedule shows an 8:00 AM start in this window; the earliest verified starts are 9:10–10:10 AM.</p>')
    body.append('<h2>How to use this site</h2><ul>'
        '<li><a href="tournaments.html">Tournaments</a> — every event with filters: text search across all tables, date selector, and a &ldquo;single-entry / freezeout confirmed&rdquo; toggle (currently matches 0 rows — by verified data, not by omission).</li>'
        '<li><a href="hotels.html">Hotels</a> — dated rate log, resort fee + tax + parking + cancellation fields, walk-time matrix with a ≤30-min filter, official per-date booking links.</li>'
        '<li><a href="calculator.html">Trip calculator</a> — entries × buy-ins + nights × true hotel cost.</li>'
        '<li><a href="venues/venetian.html">Venue pages</a> — one per venue with its events and nearby hotels.</li>'
        '<li><a href="monitoring.html">Change monitor</a> — official URLs re-checked on a schedule; changed sources flagged.</li>'
        '<li><a href="questions.html">Questions</a> and <a href="suggestions.html">Suggestions</a> — what must be answered before nonrefundable decisions, and a reviewable suggestion queue.</li></ul>')
    page("index.html", "Executive summary", "".join(body))

# ------------------------------------------------------------- tournaments
def build_tournaments():
    body = [filterbar()]
    body.append('<p class="note">No event currently qualifies for a single-entry recommendation: not one audited structure sheet confirms a maximum of one entry / freezeout. Confirmed buy-in and guarantee values are shown as reference only; no event is ranked as a single-entry pick until its entry policy is verified. Pool ÷ entry is a descriptive ratio — arithmetic only, not a forecast. Bounty, flight, satellite and re-entry/rebuy events are labeled and listed separately.</p>')
    secs = [("main","Section A — Buy-in &amp; guarantee confirmed; entry policy unverified (not ranked as single-entry)"),
            ("flight","Section B — Flights &amp; multi-day events (shared guarantee, labeled separately)"),
            ("bounty","Section C — Bounty / PKO / mystery-bounty (guarantee often includes bounties)"),
            ("satellite","Section D — Satellites (prizes are seats/tickets)"),
            ("multi-entry","Section E — Re-entry confirmed (spend more money to stay alive)"),
            ("spend-advantage","Section F — Rebuys / add-ons confirmed (spend-advantage)")]
    for sec, title in secs:
        rows = section_rows(sec)
        body.append('<h2>%s <span class="muted">(%d rows)</span></h2>' % (title, len(rows)))
        if rows:
            body.append(table(EV_HEAD, rows))
        else:
            body.append('<p class="muted">No rows.</p>')
    body.append('<h2>Full rule excerpts</h2><p>Each row&rsquo;s structured rule fields (single-entry, re-entry, add-on, fees) with source excerpt and retrieval date live in <code>data/integrated/events.json</code>. '
        'The most recent retrieval date for every row is shown in the Last checked column.</p>')
    page("tournaments.html", "Tournaments", "".join(body))

# ---------------------------------------------------------------- schedule
def build_schedule():
    body = [filterbar(dates=True, freezeout=False, placeholder="Search the daily plan…")]
    body.append('<p class="note">Each day gets one <b>primary</b> event and a <b>conditional fallback</b> — never an impossible sequence. '
        'Overlap flags use verified start times and late-registration cutoffs plus <b>plausible-duration estimates</b> (labeled; no official source publishes finish times).</p>')
    for dt, p in PLAN["plan"].items():
        ov = "".join("<li>%s</li>" % esc(o) for o in p["overlaps"]) or "<li class='muted'>none detected</li>"
        body.append('<div class="daycard" data-day="%s"><h3>%s %s</h3>'
            '<p><b>Primary:</b> %s (%s) %s</p>'
            '<p><b>Fallback:</b> %s (%s)<br><span class="muted">%s</span></p>'
            '<details><summary>Overlap flags (%d)</summary><ul>%s</ul></details></div>'
            % (esc(p["date"]), esc(p["date"]), esc(p["weekday"]), esc(p["primary_name"]), esc(p["primary_time"]),
               link(DATA_SRC(p["primary"]), "source") if p["primary"] else "",
               esc(p["fallback_name"]), esc(p["fallback_time"]), esc(p["fallback_condition"] or "—"),
               len(p["overlaps"]), ov))
    page("schedule.html", "Daily plan", "".join(body))

EV_BY_ID = {e["id"]: e for e in EVENTS}
def DATA_SRC(eid):
    e = EV_BY_ID.get(eid)
    return e["source_urls"][0] if e and e["source_urls"] else ""

# ----------------------------------------------------------------- hotels
def build_hotels():
    body = [filterbar(dates=False, freezeout=False, walk=True, placeholder="Search hotels…")]
    body.append('<p class="note">Rates are kept as a <b>dated log</b>, not a single value. True cost/night = (rate + resort fee) × (1 + 13.38%% tax). '
        'Tax rate verified: %s (&ldquo;Daily rates do not include the applicable Clark County Room Tax of 13.38%%&rdquo;). Parking is listed separately because it is optional.</p>' % link(HOTELS["meta"]["tax_source"], "Venetian hotel terms"))
    rows = []
    for h in HOTELS["hotels"]:
        fee = money(h["resort_fee"]) + " + tax" if h["resort_fee"] else '<span class="badge unverified">unverified</span>'
        rl = h["rate_log"]
        latest = rl[0] if rl else None
        rate = money(latest["rate"]) if latest else '<span class="badge unverified">no dated quote</span>'
        ts = latest["retrieved"] if latest else "—"
        rows.append([esc(h["name"]), esc(h["quality"]), fee + " " + link(h["resort_fee_src"], "src"),
                     rate, "13.38%", esc(h["parking"])[:60] + ("…" if len(h["parking"])>60 else "") + (" " + link(h["parking_src"], "src") if h["parking_src"] else ""),
                     esc(ts), link(h["booking_url"].split("?")[0] if "{in}" in h["booking_url"] else h["booking_url"], "book (official)")])
    body.append('<h2>Hotel cost fields</h2>')
    body.append(table(["Property","Quality","Resort fee","Latest rate (dated log)","Room tax","Parking","Rate timestamp","Booking"], rows))
    body.append('<h2>Dated rate log (all entries)</h2>')
    rl_rows = []
    for h in HOTELS["hotels"]:
        for e in h["rate_log"]:
            tc = (e["rate"] + (h["resort_fee"] or 0)) * (1 + HOTELS["meta"]["tax"])
            rl_rows.append([esc(h["name"]), esc(e["label"]), money(e["rate"]),
                            money(h["resort_fee"]) if h["resort_fee"] else "unverified",
                            "$%.2f" % tc, esc(e["retrieved"]),
                            "yes" if e["dated_quote"] else "no — conditional starting rate",
                            link(e["rate_src"])])
    body.append(table(["Property","Entry","Nightly rate","Resort fee","True cost/night (rate+fee)×1.1338","Retrieved","Date-specific?","Source"], rl_rows))
    body.append('<h2>Itemized stay comparison (like-for-like)</h2>')
    body.append('<p class="note">No official dated quotes were captured this session, so checkout totals stay blank (flagged). '
        'The table below is the like-for-like capture template the scheduled re-check fills in: checkout total, nightly average, mandatory resort fee + tax, parking, cancellation deadline and rate timestamp for the same stay. '
        'Use the per-date official booking links to pull a quote for exact dates and occupancy, then the calculator applies the verified fee and tax.</p>')
    body.append(table(["Property","Stay dates","Occupancy","Checkout total","Nightly average","Mandatory fee + tax","Parking","Cancellation deadline","Rate timestamp","Official booking"],
        [[esc(h["name"]), '<span class="badge unverified">not captured</span>',
          '<span class="badge unverified">occupancy not provided</span>',
          '<span class="badge unverified">not captured</span>', '<span class="badge unverified">not captured</span>',
          (money(h["resort_fee"]) + " + 13.38% tax / night") if h["resort_fee"] else "unverified",
          esc(h["parking"] or "—")[:40], '<span class="badge unverified">not captured for a dated booking</span>', "—",
          link(h["booking_url"].split("?")[0] if "{in}" in h["booking_url"] else h["booking_url"], "official booking")] for h in HOTELS["hotels"]]))
    body.append('<h2>Walking routes (official addresses, Google Maps)</h2>')
    wrows = []
    for w in HOTELS["walks"]:
        mins = w["minutes"]
        ok = mins is not None and mins <= 30
        cell = ("%d min" % mins) if mins is not None else '<span class="badge unverified">not measured</span>'
        if mins is not None:
            cell += " · " + ("<b class='ok'>≤30 OK</b>" if ok else "<b class='bad'>over 30</b>")
        wrows.append([esc(w["hotel"]), esc(w["venue"]), cell, esc(w.get("distance") or "—"), esc(w["note"])[:70],
                      link(w["url"], "route"), esc(w["last_checked"] if "last_checked" in w else TODAY) if w["verified"] else "scheduled"])
    body.append(table(["Hotel","Venue","Walk time","Distance","Route note","Map / source","Checked"],
                      wrows, 'data-walktable'))
    body.append('<h2>Official booking links per date</h2><p class="note">Pick dates to generate the official booking URL (the booking engine accepts arrival/departure in the link). Rates displayed there are live quotes; record them in the dated log before comparing.</p>'
        '<div class="filters"><label>Check-in <input type="date" id="bk-in"></label>'
        '<label>Check-out <input type="date" id="bk-out"></label>'
        '<label>Adults <input type="number" id="bk-adults" min="1" step="1" placeholder="Enter occupancy"></label><div id="bk-links"></div></div>')
    bk = json.dumps([dict(name=h["name"], url=h["booking_url"]) for h in HOTELS["hotels"] if "{in}" in h["booking_url"]])
    body.append('<script>window.addEventListener("DOMContentLoaded",function(){poker4InitBooking(%s);});</script>' % bk)
    page("hotels.html", "Hotels &amp; true cost", "".join(body))

# -------------------------------------------------------------- calculator
def build_calculator():
    opts = []
    for h in HOTELS["hotels"]:
        fee = h["resort_fee"] or ""
        opts.append('<option value="%s" data-fee="%s">%s</option>' % (esc(h["name"]), fee, esc(h["name"])))
    body = ['<p class="note">Estimated trip cost = <b>entries × buy-ins + nights × true hotel cost</b>, where true hotel cost/night = (nightly rate + mandatory resort fee) × 1.1338 tax. '
        'Trip dates, exact occupancy and a date-specific booking quote have not been supplied or captured, so cost inputs start blank rather than using a conditional rate as a quote. '
        'Parking is shown as a separate optional line. Numbers you type are not saved or sent anywhere.</p>']
    body.append('<div class="calc"><div class="calcgrid">'
        '<label>Entries (total across tournaments) <input type="number" id="c-entries" min="0" placeholder="Enter count"></label>'
        '<label>Buy-in per entry ($) <input type="number" id="c-buyin" min="0" step="1" placeholder="Enter amount"></label>'
        '<label>Nights <input type="number" id="c-nights" min="0" placeholder="Enter nights"></label>'
        '<label>Hotel <select id="c-hotel"><option value="">Choose a hotel</option>%s</select></label>'
        '<label>Nightly rate ($, before fee &amp; tax) <input type="number" id="c-rate" min="0" step="1" placeholder="Use dated quote"></label>'
        '<label>Resort fee ($/night) <input type="number" id="c-fee" min="0" step="1" placeholder="Select verified hotel"></label>'
        '<label>Room tax (%%) <input type="number" id="c-tax" value="13.38" min="0" step="0.01"></label>'
        '<label>Parking ($/night, optional) <input type="number" id="c-park" min="0" step="1" placeholder="Optional"></label>'
        '</div><div class="calcout" id="c-out"></div></div>' % "".join(opts))
    body.append('<h2>What the output means</h2><ul>'
        '<li><b>Entries × buy-ins</b> — total tournament cost at one entry per event (rebuys/add-ons would change this; those events are in separate sections).</li>'
        '<li><b>True hotel cost/night</b> — (rate + resort fee) × (1 + tax). This is the mandatory nightly cost; parking is optional and listed separately.</li>'
        '<li><b>Checkout total</b> — nights × (rate + fee) plus tax on both, matching how the Venetian terms bill (&ldquo;Daily rates do not include the applicable Clark County Room Tax of 13.38%&rdquo;, resort fee &ldquo;$55 plus tax per night&rdquo;).</li>'
        '<li><b>Nightly average</b> — checkout total ÷ nights, for like-for-like comparisons.</li></ul>')
    page("calculator.html", "Trip cost calculator", "".join(body))

# ---------------------------------------------------------------- venues
def venue_page(fname, title, venue_names, blurb, hotel_filter=None):
    body = ['<p class="note">%s</p>' % blurb]
    rows = [event_row(e) for e in EVENTS if e["venue"] in venue_names and e["kind"] != "restart"]
    body.append('<h2>Events</h2>')
    body.append(filterbar(dates=False, freezeout=True, placeholder="Search this venue…"))
    body.append(table(EV_HEAD, rows))
    body.append('<h2>Nearby hotels &amp; walk times</h2>')
    wrows = []
    for w in HOTELS["walks"]:
        if w["venue"].lower() not in [v.lower() for v in venue_names]: continue
        mins = w["minutes"]
        cell = ("%d min" % mins) if mins is not None else '<span class="badge unverified">not measured — route link</span>'
        if mins is not None:
            cell += " · " + ("<b class='ok'>≤30 OK</b>" if mins <= 30 else "<b class='bad'>over 30</b>")
        wrows.append([esc(w["hotel"]), cell, esc(w["note"])[:60], link(w["url"], "route")])
    body.append(table(["Hotel","Walk to poker room","Note","Map / source"], wrows))
    page(fname, title, "".join(body))

# ---------------------------------------------------------------- monitoring
def build_monitoring():
    try:
        mon = load("monitoring.json")
    except FileNotFoundError:
        mon = dict(meta=dict(built=TODAY), checks=[])
    body = ['<p class="note">Each official URL is re-checked automatically on a schedule (GitHub Actions, daily) and every morning the scraper pulls each listed poker room&rsquo;s official daily schedule. '
        'Rows whose source content changed since the last check are marked <span class="badge warn">CHANGED</span> here and on the Flagged page.</p>']
    checks_by_url = {c.get("url"): c for c in MONITORING.get("checks", [])}
    rows = [[esc(s["label"]), link(s["url"]),
             esc(checks_by_url.get(s["url"], {}).get("status", s.get("status", "baseline captured — first scheduled run pending"))),
             esc(checks_by_url.get(s["url"], {}).get("last_checked", s.get("last_checked", TODAY))),
             esc(checks_by_url.get(s["url"], {}).get("changed", "—"))] for s in SOURCES["sources"]]
    body.append('<h2>Source re-check status (%d official URLs)</h2>' % len(SOURCES["sources"]))
    body.append(filterbar(dates=False, freezeout=False, placeholder="Search monitored sources…"))
    body.append(table(["Source","URL","Status","Last checked","Changed"], rows))
    body.append('<h2>Morning daily-schedule feed</h2><p>Target feeds: Venetian DSE IV schedule page, Wynn daily poster/structures, Bellagio poker page. '
        'Snapshots land in <code>data/integrated/monitoring/</code> with timestamps; the report above is regenerated from them. '
        'If a fetch fails, the row is marked with the error — never silently dropped.</p>')
    page("monitoring.html", "Change monitor", "".join(body))

# ---------------------------------------------------------------- questions
QUESTIONS = [
 ("Q1","Trip dates and budget","Are the trip dates fixed to any subset of Nov 16 – Dec 23, 2026, and is there a nightly budget ceiling?","Needed before any hotel is chosen. Blocks: booking.","open", VEN_SCHED),
 ("Q2","Single-entry policy hard requirement","Must every played event be confirmed single-entry/freezeout, or is 'entry rule unverified' acceptable for candidates?","No event is confirmed freezeout; a hard policy leaves no eligible event until rooms confirm rules in writing.","open — decisive", VEN_SCHED),
 ("Q3","Venetian entry rules in writing","Can the Venetian poker room provide written maximum-entry / no-rebuy / no-add-on rules for events of interest?","This is the missing fact that flips rows from unverified to confirmed or disqualified.","open", VEN_SCHED),
 ("Q4","Bounty tolerance","Are bounty/mystery-bounty events acceptable? Their guarantees may include bounty pools, so pool÷entry is not comparable.","Determines whether Super Gold Million and Venetian bounty events can be candidates.","open", WPT_SCHED),
 ("Q5","Occupancy","How many guests per room?","Required for a like-for-like hotel quote; occupancy is not assumed.","open", VEN_BOOK.split("?")[0]),
 ("Q6","Hotel dated quotes","What do the official booking engines show for the exact dates and occupancy?","No dated totals were captured; per-date official links are on Hotels. Required for checkout totals.","open", VEN_BOOK.split("?")[0]),
 ("Q7","On-site Wynn walk","Should the internal hotel-to-poker-room walk within Wynn be timed, or should it remain blank until an official route is available?","All cross-property hotel→venue routes have now been checked; Bellagio and ARIA exceed 30 minutes to Wynn. The Wynn property page identifies the poker room but gives no verified internal walking time.","open", "https://www.wynnlasvegas.com/casino/poker"),
 ("Q8","Poker-rate qualification","Will the player satisfy the play requirements for the Venetian $119/$209 poker rates?","The terms are conditional; failing them results in the prevailing rate.","open", VEN_POKER_RATES),
 ("Q9","Bust-out tolerance","If playing bounty/flight events, is re-entering (spending more) acceptable where allowed?","Sets whether re-entry-confirmed events are excluded or only separated.","open", WPT_STRUCTS),
 ("Q10","8 AM start","Is the 8 AM start a hard requirement?","No verified event in the window starts at 8 AM; the earliest Venetian start is 9:10 AM.","open — conflict", VEN_SCHED),
 ("Q11","Bellagio buy-in conflict","Which is correct for the Bellagio Saturday NLH: $1,000 or $1,100?","Official sources conflict; do not use this row for ranking until resolved.","open", "https://bellagio.mgmresorts.com/en/casino/poker.html"),
 ("Q12","WPT schedule date labels","How should Wynn resolve the official PDF rows labeled 'Dec. 18 Wednesday'?","The official PDF conflicts internally; rows are shown as printed and marked for review.","open", WPT_SCHED),
]

def build_questions():
    rows = [[esc(a), esc(b), esc(c), esc(d), '<span class="badge warn">%s</span>' % esc(e), link(source, "official source")]
            for a,b,c,d,e,source in QUESTIONS]
    body = ['<p class="note">A clear list of questions, information and answers that must be addressed before decisions can reasonably be made — based on what we have and what we do not have. '
        'Each row says what it blocks and links the official source used to identify the missing information.</p>']
    body.append(filterbar(dates=False, freezeout=False, placeholder="Search questions…"))
    body.append(table(["#","Topic","Question / needed information","Why it matters / how to discover it","Status","Official source"], rows))
    page("questions.html", "Questions before decisions", "".join(body))

# -------------------------------------------------------------- suggestions
SUGGESTIONS = [
 ("S1","Ask the Venetian poker room for written entry rules per event (Questions Q3)","Would convert the biggest unverified block into confirmed/disqualified rows","high","awaiting user choice — not implemented", VEN_SCHED),
 ("S2","Add a booking-engine snapshotter to capture dated hotel quotes nightly into the rate log","Fills the like-for-like checkout-total table automatically; cost: heavier CI","high","awaiting user choice — not implemented", VEN_BOOK.split("?")[0]),
 ("S3","Expand the morning daily-schedule feed to ARIA/Bellagio/Caesars/Harrah's/Horseshoe official pages","Wider daily coverage; some rooms publish only on PDFs or not at all","medium","awaiting user choice — not implemented", "https://bellagio.mgmresorts.com/en/casino/poker.html"),
 ("S4","Add an email/SMS alert when the change monitor marks a source CHANGED","Faster reaction to schedule changes; requires a secret/token in repo settings","medium","awaiting user choice — not implemented", WPT_SCHED),
 ("S5","Add a per-event bankroll simulator labeled clearly as toy math, not EV","Decision support; risks being mistaken for a forecast","low","awaiting user choice — not implemented", VEN_SCHED),
 ("S6","Measure cross-property walking routes","Completeness; route values can change over time","medium","completed for all cross-property rows on 2026-11-17; Wynn on-property walk remains unmeasured", "https://www.google.com/maps/dir/?api=1&origin=The+Venetian+Resort,+3355+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109&destination=Wynn+Las+Vegas,+3131+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109&travelmode=walking"),
 ("S7","Add a printable one-page day-plan PDF export","Convenience at the poker room","low","awaiting user choice — not implemented", VEN_SCHED),
 ("S8","Archive earlier session subsites from the root navigation while keeping URLs live","Less clutter; content remains accessible from the archive page","low","awaiting user choice — not implemented", VEN_SCHED),
]

def build_suggestions():
    rows = [[esc(a), esc(b), esc(c), esc(d), '<span class="badge warn">%s</span>' % esc(e), link(source, "official source")]
            for a,b,c,d,e,source in SUGGESTIONS]
    body = ['<p class="note">A dedicated section for suggestions so someone can review them and choose the best path <b>before</b> anything is implemented. '
        'Nothing on this page has been implemented — each row is decision-only and links the official source that motivates the suggestion.</p>']
    body.append(filterbar(dates=False, freezeout=False, placeholder="Search suggestions…"))
    body.append(table(["#","Suggestion","Impact if adopted","Priority","Status","Official source"], rows))
    page("suggestions.html", "Suggestions (decision-only)", "".join(body))

# ----------------------------------------------------------------- flagged
def build_flagged():
    body = ['<p class="note">Flagged irregularities and unverified items. None of these blocks the site; they are published here so they can be reviewed after launch with source links.</p>']
    rows = [[esc(f["id"]), esc(f["title"]), esc(f["detail"]), link(f["source"]) if f["source"] else "—"] for f in FLAGS["flags"]]
    body.append(filterbar(dates=False, freezeout=False, placeholder="Search flagged items…"))
    body.append(table(["#","Flag","Detail","Source"], rows))
    page("flagged.html", "Flagged for review", "".join(body))

# ---------------------------------------------------------------- sources
def build_sources_page():
    rows = [[esc(s["label"]), link(s["url"]), "official" if s["official"] else "—", esc(s["last_checked"])] for s in SOURCES["sources"]]
    body = ['<p class="note">Full source registry. Every table row on this site links at least one of these. %d sources, all official property/organizer pages or PDFs (Google Maps used for walk times).</p>' % len(rows)]
    body.append(filterbar(dates=False, freezeout=False, placeholder="Search official sources…"))
    body.append(table(["Label","URL","Type","Last checked"], rows))
    page("sources.html", "Sources", "".join(body))

# ---------------------------------------------------------------- archive
def build_archive():
    body = ['<p class="note">Earlier parallel sessions built independent snapshots that remain live and unmodified. They are kept for reference; the root pages are the integrated result.</p><ul>'
        '<li><a href="60fb62da/index.html">60fb62da — independent Venetian audit dashboard</a></li>'
        '<li><a href="c07371e3/index.html">c07371e3 — re-verification site (94-row Venetian CSV)</a></li>'
        '<li><a href="df41f5c6/index.html">df41f5c6 — decision dashboard</a></li>'
        '<li><a href="strip/index.html">strip — Strip schedule site</a></li>'
        '<li><a href="verified/index.html">verified — earlier verified build</a></li>'
        '<li><a href="pages/tournaments.html">pages/ — first root session site</a></li>'
        '<li><a href="decisions.html">decisions.html</a> · <a href="review.html">review.html</a> — earlier root pages</li>'
        '<li><b>08f07d1d session:</b> <a href="v2/index.html">v2/ verified poker4 dashboard</a> (live) · '
        '<a href="poker4/index.html">poker4/ subsite</a> (live) · '
        '<a href="archive/08f07d1d/index.html">archive/08f07d1d/ — PR #26 root page versions preserved verbatim</a> · '
        '<a href="archive/08f07d1d/pr30/index.html">archive/08f07d1d/pr30/ — PR #30 root/venue page versions preserved verbatim</a> · '
        'their other root pages remain live: '
        '<a href="change-monitor.html">change-monitor.html</a>, <a href="trip-calculator.html">trip-calculator.html</a>, '
        '<a href="venue-venetian.html">venue-venetian.html</a>, <a href="venue-wynn.html">venue-wynn.html</a>, '
        '<a href="venue-others.html">venue-others.html</a>, <a href="venues.html">venues.html</a>, '
        '<a href="ratelog.html">ratelog.html</a>, <a href="repo-review.html">repo-review.html</a>, '
        '<a href="workflow.html">workflow.html</a>, <a href="venues/aria.html">venues/aria</a> · '
        '<a href="venues/bellagio.html">bellagio</a> · <a href="venues/caesars.html">caesars</a> · '
        'their data: <code>data/08f07d1d/</code>, <code>data/v2/</code>, <code>data/rate_log.json</code></li></ul>']
    page("archive.html", "Archive of earlier session sites", "".join(body))

def build_others():
    body = ['<p class="note">Other Las Vegas Strip rooms in scope. Bellagio rows come from the official Bellagio poker page (via the c07371e3 audit); conflicts and gaps are labeled, never inferred. Circa has no poker room (verified official).</p>']
    rows = [
        ["Friday","Bellagio","$600 No Limit Hold'em","$600","—","re-entry through level 8 (prior audit of official page)","start time/date not captured",link("https://bellagio.mgmresorts.com/en/casino/poker.html")],
        ["Saturday","Bellagio","$1,000 or $1,100 No Limit Hold'em (conflict)","$1,000 or $1,100","$50,000","NOT CAPTURED — unverified","buy-in conflict on official sources: $1,100 header vs $1,000 rules text",link("https://bellagio.mgmresorts.com/en/casino/poker.html")],
    ]
    body.append(filterbar(dates=False, freezeout=False, placeholder="Search other venues…"))
    body.append(table(["Day","Venue","Event","Entry","Guarantee","Entry rules","Flags","Source"], rows))
    body.append('<h2>Rooms checked but not listed as candidates</h2><ul>'
        '<li>ARIA — poker room active; no official tournament schedule captured; walk to Venetian 31 min (over limit).</li>'
        '<li>Caesars Palace / Harrah&rsquo;s / Horseshoe — official pages carry no published daily tournament schedule in a capturable form; flagged.</li>'
        '<li>Circa (downtown) — official site confirms <b>no poker room</b>; excluded.</li></ul>')
    page("venues/others.html", "Other venues", "".join(body))

if __name__ == "__main__":
    build_index(); build_tournaments(); build_schedule(); build_hotels(); build_calculator()
    venue_page("venues/venetian.html", "Venetian", ["Venetian"],
        "The Venetian Resort, 3355 Las Vegas Blvd S — poker room at Palazzo Level 2 (official poker page). Host of DeepStack Extravaganza IV, Nov 16 – Dec 23, 2026, $3.6M+ stated guarantees. All 37 structure sheets were read on %s." % TODAY)
    venue_page("venues/wynn.html", "Wynn", ["Wynn"],
        "Wynn Las Vegas, 3131 Las Vegas Blvd S — poker room located in Encore at Wynn Las Vegas (official poker page). Host of the WPT World Championship, Nov 27 – Dec 21, 2026, plus verified daily tournaments.")
    build_others(); build_monitoring(); build_questions(); build_suggestions(); build_flagged(); build_sources_page(); build_archive()
    print("pages built")
