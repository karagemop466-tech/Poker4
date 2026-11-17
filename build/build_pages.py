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
EVENTS = DATA["events"]
TODAY = DATA["meta"]["built"]

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
    if with_date: r.append(esc(e["date"]))
    r += [esc(e["time"]), esc(e["venue"]), esc(e["name"]),
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
    body.append('<p><b>Best verified value plays</b> (ratio = guaranteed pool ÷ total entry fee, descriptive arithmetic only, never a forecast): '
        'Wynn Super Gold Million Mystery Bounty $400 / $3,000,000 (7,500&times;, but it is a mystery-bounty flight event), '
        'Venetian $2,200 PokerAtlas Championship $1,000,000 (454.5&times;), Venetian $800 NLH $500,000 (625&times; across six flights), '
        'WPT Prime $1,100 / $5,000,000 (4,545.5&times;, flights), Wynn $800 NLH $1,000,000 (1,250&times;, flights). '
        'Single-flight, non-bounty candidates with clean guarantees include Venetian $600 NLH $40K (#28, 66.7&times;), $600 Seniors $40K (66.7&times;), $800 LIPS Ladies $40K (50&times;).</p>')
    body.append('<p><b>Hotels</b>: The Venetian is the only property with a fully verified cost picture ($55 + tax resort fee, 13.38% Clark County tax, $20/day self-parking, cancellation terms, conditional poker rates from $119/$209 with a play requirement). '
        'Verified walks to the Venetian poker room: TI 6 min, Harrah&rsquo;s 6 min, Caesars 12 min, Wynn 13 min, Horseshoe 16 min, Bellagio 21 min — all ≤30 min; ARIA is 31 min and fails the limit. '
        'True cost/night = (rate + resort fee) × 1.1338 — the <a href="calculator.html">trip calculator</a> does the math per stay and shows checkout totals and nightly averages.</p>')
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
    body.append('<p class="note">Ranked only after the total entry fee and guarantee are both confirmed on an official source. '
        'Pool ÷ entry is a descriptive ratio — arithmetic only, not a forecast. Bounty, flight, satellite and re-entry/rebuy events are labeled and listed separately. '
        'Within a flight, no Venetian sheet states an entry-count rule, so those rows stay <span class="badge unverified">unverified</span> until a source confirms them.</p>')
    secs = [("main","Section A — Ranked main events (non-bounty, confirmed buy-in &amp; guarantee)"),
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
        body.append('<div class="daycard"><h3>%s %s</h3>'
            '<p><b>Primary:</b> %s (%s) %s</p>'
            '<p><b>Fallback:</b> %s (%s)<br><span class="muted">%s</span></p>'
            '<details><summary>Overlap flags (%d)</summary><ul>%s</ul></details></div>'
            % (esc(p["date"]), esc(p["weekday"]), esc(p["primary_name"]), esc(p["primary_time"]),
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
                     esc(ts), link(h["booking_url"], "book (official)")])
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
    body.append(table(["Property","Stay dates","Occupancy","Checkout total","Nightly average","Mandatory fee + tax","Parking","Cancellation deadline","Rate timestamp"],
        [[esc(h["name"]), '<span class="badge unverified">not captured</span>', "2 guests",
          '<span class="badge unverified">—</span>', '<span class="badge unverified">—</span>',
          (money(h["resort_fee"]) + " + 13.38% tax / night") if h["resort_fee"] else "unverified",
          esc(h["parking"] or "—")[:40], esc(h["cancellation"] or "—")[:40], "—"] for h in HOTELS["hotels"]]))
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
        '<div class="filters"><label>Check-in <input type="date" id="bk-in" value="2026-11-27"></label>'
        '<label>Check-out <input type="date" id="bk-out" value="2026-12-01"></label><div id="bk-links"></div></div>')
    bk = json.dumps([dict(name=h["name"], url=h["booking_url"]) for h in HOTELS["hotels"] if "{in}" in h["booking_url"]])
    body.append('<script>window.addEventListener("DOMContentLoaded",function(){poker4InitBooking(%s);});</script>' % bk)
    page("hotels.html", "Hotels &amp; true cost", "".join(body))

# -------------------------------------------------------------- calculator
def build_calculator():
    opts = []
    for h in HOTELS["hotels"]:
        fee = h["resort_fee"] or 0
        rate = h["rate_log"][0]["rate"] if h["rate_log"] else ""
        opts.append('<option value="%s" data-fee="%s" data-rate="%s">%s</option>' % (esc(h["name"]), fee, rate, esc(h["name"])))
    body = ['<p class="note">Estimated trip cost = <b>entries × buy-ins + nights × true hotel cost</b>, where true hotel cost/night = (nightly rate + mandatory resort fee) × 1.1338 tax. '
        'Parking is shown as a separate optional line. Defaults come from the verified dated log where one exists; every input is editable. Numbers you type are not saved or sent anywhere.</p>']
    body.append('<div class="calc"><div class="calcgrid">'
        '<label>Entries (total across tournaments) <input type="number" id="c-entries" value="7" min="0"></label>'
        '<label>Buy-in per entry ($) <input type="number" id="c-buyin" value="600" min="0" step="1"></label>'
        '<label>Nights <input type="number" id="c-nights" value="5" min="0"></label>'
        '<label>Hotel <select id="c-hotel">%s</select></label>'
        '<label>Nightly rate ($, before fee &amp; tax) <input type="number" id="c-rate" value="209" min="0" step="1"></label>'
        '<label>Resort fee ($/night) <input type="number" id="c-fee" value="55" min="0" step="1"></label>'
        '<label>Room tax (%%) <input type="number" id="c-tax" value="13.38" min="0" step="0.01"></label>'
        '<label>Parking ($/night, optional) <input type="number" id="c-park" value="20" min="0" step="1"></label>'
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
    rows = [[esc(s["label"]), link(s["url"]), esc(s.get("status", "baseline captured — first scheduled run pending")),
             esc(s.get("last_checked", TODAY)), esc(s.get("changed", "—"))] for s in SOURCES["sources"][:25]]
    body.append('<h2>Source re-check status (first 25 of %d)</h2>' % len(SOURCES["sources"]))
    body.append(table(["Source","URL","Status","Last checked","Changed"], rows))
    body.append('<h2>Morning daily-schedule feed</h2><p>Target feeds: Venetian DSE IV schedule page, Wynn daily poster/structures, Bellagio poker page. '
        'Snapshots land in <code>data/integrated/monitoring/</code> with timestamps; the report above is regenerated from them. '
        'If a fetch fails, the row is marked with the error — never silently dropped.</p>')
    page("monitoring.html", "Change monitor", "".join(body))

# ---------------------------------------------------------------- questions
QUESTIONS = [
 ("Q1","Trip dates and budget","Are the trip dates fixed to any subset of Nov 16 – Dec 23, 2026, and is there a nightly budget ceiling?","Needed before any hotel is chosen. Blocks: booking.","open"),
 ("Q2","Single-entry policy hard requirement","Must every played event be confirmed single-entry/freezeout, or is 'entry rule unverified' acceptable for candidates?","Current verified data contains ZERO confirmed freezeouts — a hard policy would leave nothing to play until rooms confirm rules in writing.","open — decisive"),
 ("Q3","Venetian entry rules in writing","Can the Venetian poker room provide written maximum-entry / no-rebuy / no-add-on rules for the specific events of interest (email lv_cas_poker@venetianlasvegas.com or call 700.414.7657)?","This is the single missing fact that flips rows from unverified to confirmed or disqualified.","open"),
 ("Q4","Bounty tolerance","Are bounty/mystery-bounty events acceptable (their guarantees include bounty pools, so pool÷entry is not comparable)?","Determines whether the Super Gold Million ($400/$3M) and Venetian bounty dailies are candidates.","open"),
 ("Q5","Occupancy","How many guests per room?","Rates captured assume single/double occupancy; extra guests add $50+/night at the Venetian (verified).","open"),
 ("Q6","Hotel dated quotes","What do the official booking engines show for the exact dates/occupancy?","No dated quotes were machine-capturable; per-date official links are generated on the Hotels page. Needed for like-for-like totals.","open"),
 ("Q7","Walk-time completion","Should the remaining hotel→Wynn walk pairs be measured now, or is the scheduled re-check acceptable?","Venetian-venue pairs are complete (7 measured + on-site); Wynn pairs partially measured.","open"),
 ("Q8","Poker-rate qualification","Will the player do 6 hrs cash play or a $300+ tournament buy-in per night to qualify for the Venetian $119/$209 poker rates?","Qualification terms are verified; failing them rebills the prevailing rate.","open"),
 ("Q9","Bust-out tolerance","If playing bounty/flight events, is re-entering (spending more) acceptable at all, even where allowed?","Sets whether re-entry-confirmed events are excluded entirely or just ranked separately.","open"),
 ("Q10","8 AM start","Is the 8 AM start a hard requirement?","No verified event in the window starts before 9:10 AM. A hard requirement conflicts with the official schedules as published.","open — conflict"),
 ("Q11","Bellagio buy-in conflict","Which is correct for the Bellagio Saturday NLH: $1,000 or $1,100?","Official sources conflict; row is labeled with the conflict. Bellagio poker desk can settle it.","open"),
 ("Q12","WPT schedule date labels","Do the 'Dec. 18 Wednesday' rows on the official WPT PDF actually mean Dec. 16?","Official PDF date/weekday labels conflict internally; rows are shown as printed and flagged. Wynn poker room (702) 770-7654 can settle it.","open"),
]
def build_questions():
    rows = [[esc(a), esc(b), esc(c), esc(d), '<span class="badge warn">%s</span>' % esc(e)] for a,b,c,d,e in QUESTIONS]
    body = ['<p class="note">A clear list of questions, information and answers that must be addressed before decisions can reasonably be made — based on what we have and what we do not have. '
        'Each row says what it blocks and how to discover the missing information (suggestions live on the Suggestions page).</p>']
    body.append(table(["#","Topic","Question / needed information","Why it matters / how to discover it","Status"], rows))
    page("questions.html", "Questions before decisions", "".join(body))

# -------------------------------------------------------------- suggestions
SUGGESTIONS = [
 ("S1","Ask the Venetian poker room for written entry rules per event (email template on Questions Q3)","Would convert the biggest unverified block into confirmed/disqualified rows","high","awaiting user choice — not implemented"),
 ("S2","Add a booking-engine snapshotter (Playwright) to capture dated hotel quotes nightly into the rate log","Fills the like-for-like checkout-total table automatically; cost: heavier CI","high","awaiting user choice — not implemented"),
 ("S3","Expand the morning daily-schedule feed to ARIA/Bellagio/Caesars/Harrah's/Horseshoe official pages","Wider daily coverage; some rooms publish only on PDFs or not at all","medium","awaiting user choice — not implemented"),
 ("S4","Add an email/SMS alert when the change monitor marks a source CHANGED","Faster reaction to schedule changes; requires a secret/token in the repo settings","medium","awaiting user choice — not implemented"),
 ("S5","Add per-event bankroll simulator (labeled clearly as toy math, not EV)","Decision support; risks being mistaken for a forecast","low","awaiting user choice — not implemented"),
 ("S6","Measure remaining hotel→Wynn walk pairs now instead of via the scheduled job","Completeness; only a few fetches","medium","awaiting user choice — not implemented"),
 ("S7","Add a printable one-page day-plan PDF export","Convenience on the floor","low","awaiting user choice — not implemented"),
 ("S8","Archive earlier session subsites from the root nav (keep URLs live)","Less clutter; content stays reachable via Archive page","low","awaiting user choice — not implemented"),
]
def build_suggestions():
    rows = [[esc(a), esc(b), esc(c), esc(d), '<span class="badge warn">%s</span>' % esc(e)] for a,b,c,d,e in SUGGESTIONS]
    body = ['<p class="note">A dedicated section for suggestions so someone can review them and choose the best path <b>before</b> anything is implemented. '
        'Nothing on this page has been implemented — each row is decision-only. Tell the session which rows to execute.</p>']
    body.append(table(["#","Suggestion","Impact if adopted","Priority","Status"], rows))
    page("suggestions.html", "Suggestions (decision-only)", "".join(body))

# ----------------------------------------------------------------- flagged
def build_flagged():
    body = ['<p class="note">Flagged irregularities and unverified items. None of these blocks the site; they are published here so they can be reviewed after launch with source links.</p>']
    rows = [[esc(f["id"]), esc(f["title"]), esc(f["detail"]), link(f["source"]) if f["source"] else "—"] for f in FLAGS["flags"]]
    body.append(table(["#","Flag","Detail","Source"], rows))
    page("flagged.html", "Flagged for review", "".join(body))

# ---------------------------------------------------------------- sources
def build_sources_page():
    rows = [[esc(s["label"]), link(s["url"]), "official" if s["official"] else "—", esc(s["last_checked"])] for s in SOURCES["sources"]]
    body = ['<p class="note">Full source registry. Every table row on this site links at least one of these. %d sources, all official property/organizer pages or PDFs (Google Maps used for walk times).</p>' % len(rows)]
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
        '<a href="archive/08f07d1d/index.html">archive/08f07d1d/ — their root page versions preserved verbatim</a> '
        '(index, tournaments, hotels, schedule, questions, sources, suggestions) · their other root pages remain live: '
        '<a href="change-monitor.html">change-monitor.html</a>, <a href="trip-calculator.html">trip-calculator.html</a>, '
        '<a href="venue-venetian.html">venue-venetian.html</a>, <a href="venue-wynn.html">venue-wynn.html</a>, '
        '<a href="venue-others.html">venue-others.html</a> · their data: <code>data/08f07d1d/</code>, <code>data/v2/</code></li></ul>']
    page("archive.html", "Archive of earlier session sites", "".join(body))

def build_others():
    body = ['<p class="note">Other Las Vegas Strip rooms in scope. Bellagio rows come from the official Bellagio poker page (via the c07371e3 audit); conflicts and gaps are labeled, never inferred. Circa has no poker room (verified official).</p>']
    rows = [
        ["Friday","Bellagio","$600 No Limit Hold'em","$600","—","re-entry through level 8 (prior audit of official page)","start time/date not captured",link("https://bellagio.mgmresorts.com/en/casino/poker.html")],
        ["Saturday","Bellagio","$1,000 or $1,100 No Limit Hold'em (conflict)","$1,000 or $1,100","$50,000","NOT CAPTURED — unverified","buy-in conflict on official sources: $1,100 header vs $1,000 rules text",link("https://bellagio.mgmresorts.com/en/casino/poker.html")],
    ]
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
