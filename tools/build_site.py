#!/usr/bin/env python3
"""Generate the Poker4 dashboard site (static HTML) from data/*.json."""
import json, os, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

def load(n):
    with open(os.path.join(DATA, n)) as f: return json.load(f)

EV = load("events.json")["events"]
HO = load("hotels.json")["hotels"]
RL = load("rate_log.json")["entries"]
WK = load("walks.json")["walks"]
CL = load("change_log.json")["entries"]
SN = load("source_snapshots.json")["snapshots"]
SRC = {s["id"]: s for s in load("sources.json")["sources"]}
TODAY = load("events.json")["generated"]

def e(x): return html.escape("" if x is None else str(x))
def money(x):
    if x is None: return "—"
    try: return "$" + format(float(x), ",.2f").replace(".00", "")
    except (TypeError, ValueError): return "—"

NAV = [("index.html","Executive brief"),("tournaments.html","Tournaments"),
       ("schedule.html","Day plan"),("hotels.html","Hotels & true cost"),
       ("ratelog.html","Rate log"),("calculator.html","Trip calculator"),
       ("venues.html","Venues"),("monitor.html","Change monitor"),
       ("workflow.html","Workflow"),("questions.html","Q&A"),
       ("suggestions.html","Suggestions"),("review.html","Flagged for review"),
       ("sources.html","Sources"),("repo-review.html","Repo review")]

def page(title, nav, body, head_extra="", depth=0):
    pre = "../" * depth
    nav = nav.replace(pre, "")
    links = "".join('<a href="%s%s"%s>%s</a>' % (pre, h, ' class="active"' if h == nav else '', e(t))
                    for h, t in NAV)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="description" content="Official-source Las Vegas Strip poker tournament and hotel decision dashboard">'
            '<title>%s — Strip Poker Planner</title><link rel="stylesheet" href="%sassets/site.css">%s</head>'
            '<body><header class="topbar"><a class="brand" href="%sindex.html">♠ STRIP POKER PLANNER</a>'
            '<span class="stamp">Research snapshot · %s · official sources only</span></header>'
            '<nav class="nav"><div class="nav-inner">%s</div></nav><main>%s</main>'
            '<footer class="footer">Every value shown links to an official operator source. Unverified values are blank and flagged. '
            'Snapshot dated %s; schedules and rates change — re-verify before payment. '
            '<a href="https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html">Official Venetian calendar ↗</a> · '
            '<a href="https://www.wynnlasvegas.com/casino/poker">Official Wynn poker ↗</a></footer>'
            '<script src="%sassets/site.js"></script></body></html>') % (
            e(title), pre, head_extra, pre, TODAY, links, body, TODAY, pre)

# ------------------------------------------------------------------ helpers
STATUS_PILL = {
    "confirmed": '<span class="pill ok">confirmed</span>',
    "prior-capture": '<span class="pill info">prior official capture</span>',
    "implied-multi": '<span class="pill warn">multi-entry implied</span>',
    "unverified": '<span class="pill grey">unverified</span>',
}

def ratio(ev):
    if not ev.get("buy_in") or not ev.get("guarantee"): return None
    return ev["guarantee"] / ev["buy_in"]

def entry_cell(ev):
    r = ev["entry_rules"]; st = r.get("status", "unverified")
    pill = STATUS_PILL.get(st, STATUS_PILL["unverified"])
    single = r.get("single_entry")
    if single == "confirmed-yes":
        pill = '<span class="pill ok">single-entry confirmed</span>'
    ex = e(r.get("excerpt") or "")
    return pill + ' <details style="margin-top:4px"><summary class="muted">rule excerpt</summary><p class="muted" style="margin:4px 0 2px">' + \
        ex + '<br>source: <a href="' + e(r.get("source_url")) + '">official document ↗</a> · retrieved ' + e(r.get("retrieved")) + '</p></details>'

def flags_cell(ev):
    fl = ev.get("flags") or []
    if not fl: return ""
    return "<br>".join('<span class="pill warn">%s</span>' % e(f) for f in fl)

EVENTS_HEAD = ("<tr><th>Date</th><th>Time</th><th>Venue</th><th>Event</th><th>Buy-in</th>"
               "<th>House/staff fee</th><th>Pool per entry</th><th>Guarantee</th>"
               "<th>Ratio*</th><th>Entry rules</th><th>Notes & flags</th><th>Sources</th><th>Last checked</th></tr>")

def event_row(ev):
    r = ev["entry_rules"]; st = r.get("status", "unverified")
    single = "single" if r.get("single_entry") == "confirmed-yes" else st
    date = ev.get("date") or (ev.get("days") or "—")
    rt = ratio(ev)
    guar = money(ev.get("guarantee"))
    if ev.get("guarantee") and (ev.get("bounty") or "bounty" in (ev.get("name","").lower())):
        guar += ' <span class="pill warn">incl. bounties</span>'
    if ev.get("kind") == "satellite": guar += ' <span class="pill info">seats</span>'
    fee = "—"
    if ev.get("house_fee") is not None:
        fee = money(ev["house_fee"]) + (" + " + money(ev["staff_fee"]) + " staff" if ev.get("staff_fee") else "")
    srcs = '<a href="%s">schedule ↗</a>' % e(ev["source_url"])
    if ev.get("structure_url"): srcs += ' · <a href="%s">structure ↗</a>' % e(ev["structure_url"])
    return ('<tr data-date="%s" data-entry="%s"><td>%s</td><td>%s</td><td>%s</td><td><b>%s</b>%s</td>'
            '<td>%s</td><td class="mono">%s</td><td class="mono">%s</td><td class="mono">%s</td>'
            '<td class="mono">%s</td><td>%s</td><td class="muted">%s<br>%s</td><td>%s</td><td>%s</td></tr>') % (
        e(ev.get("date") or ""), e(single), e(date), e(ev.get("time") or "—"), e(ev.get("venue")),
        e(ev.get("name")), ("<br><span class='muted'>#" + str(ev.get("event_no")) + " · " + e(ev.get("kind")) + "</span>") if ev.get("event_no") else "",
        money(ev.get("buy_in")), fee, money(ev.get("prize_pool_per_entry")), guar,
        ("%.1fx" % rt) if rt else "—",
        entry_cell(ev), e(ev.get("sheet_note") or ""), flags_cell(ev), srcs, e(ev.get("last_checked")))

def events_table(rows, table_id="events-table"):
    return ('<div class="tablewrap"><table id="%s"><thead>%s</thead><tbody>%s</tbody></table></div>'
            '<p class="muted">*Ratio = guaranteed pool ÷ buy-in. Descriptive arithmetic only — not a forecast of returns. '
            'Bounty guarantees include bounty money; satellite prizes are seats; multi-flight guarantees cover all flights '
            'while the buy-in shown is per flight.</p>') % (table_id, EVENTS_HEAD, "".join(event_row(x) for x in rows))

def sort_events(rows):
    def key(ev):
        d = ev.get("date") or "9999"
        t = (ev.get("time") or "").replace(" AM", " AM")
        return (d, t, ev.get("venue") or "")
    return sorted(rows, key=key)

DATED = sort_events([x for x in EV if x.get("date")])
SERIES = [x for x in EV if not x.get("date")]

# --------------------------------------------------------------- index page
def build_index():
    n_total = len(EV)
    n_single = sum(1 for x in EV if x["entry_rules"].get("single_entry") == "confirmed-yes")
    n_conf = sum(1 for x in EV if x["entry_rules"].get("status") == "confirmed")
    n_prior = sum(1 for x in EV if x["entry_rules"].get("status") == "prior-capture")
    n_unv = sum(1 for x in EV if x["entry_rules"].get("status") == "unverified")
    best = sorted([x for x in EV if ratio(x) and x.get("kind") not in ("satellite",)
                   and x["entry_rules"].get("status") in ("unverified", "implied-multi", "prior-capture")],
                  key=lambda x: -ratio(x))[:3]
    best_conf = sorted([x for x in EV if ratio(x) and x["entry_rules"].get("status") == "confirmed"
                        and x.get("kind") not in ("satellite",)], key=lambda x: -ratio(x))[:3]
    cards = "".join(
        '<article class="card"><span class="tag">%s</span><h3>%s</h3><p class="muted">%s · %s · %s gtd%s</p>'
        '<p>Ratio <b>%.1fx</b> (descriptive). Entry rules: %s.</p></article>' % (
            ("best ratio · " + x.get("venue", "")), e(x["name"]),
            e(x.get("date") or x.get("days") or ""), e(x.get("time") or ""),
            money(x.get("guarantee")), (" · " + e(x["guarantee_note"])) if x.get("guarantee_note") else "",
            ratio(x), STATUS_PILL.get(x["entry_rules"].get("status"), ""))
        for x in best)
    cards_conf = "".join(
        '<article class="card"><span class="tag">confirmed entry rules · %s</span><h3>%s</h3><p class="muted">%s · %s · %s gtd</p>'
        '<p>Ratio <b>%.1fx</b>. Official sheet confirms: %s.</p></article>' % (
            e(x.get("venue")), e(x["name"]), e(x.get("days") or x.get("date") or ""), e(x.get("time") or ""),
            money(x.get("guarantee")), ratio(x), e(x["entry_rules"].get("reentry")))
        for x in best_conf)
    body = """
<section class="hero"><p class="eyebrow">Decision dashboard · official-source snapshot</p>
<h1>Vegas poker, organized for a real decision.</h1>
<p>Upcoming tournament listings with <b>entry rules read from official structure sheets</b>, verified buy-ins and
guarantees, hotel true-cost math (rate + resort fee + 13.38%% tax), walking-time filters, a trip-cost calculator, and an
automatic daily source re-check that flags rows whose official page changed. Anything not stated by an official source is
left blank and flagged.</p>
<div class="hero-actions"><a class="button" href="tournaments.html">Review tournaments</a>
<a class="button ghost" href="calculator.html">Plan a trip (cost calculator)</a>
<a class="button ghost" href="review.html">See what is unverified</a></div></section>
<div class="stats">
<div class="stat"><span>Event rows tracked</span><b>%d</b><span>Venetian DSE IV (dated) + Wynn/WPT/Bellagio/Caesars series rows</span></div>
<div class="stat"><span>Confirmed single-entry / freezeout</span><b>%d</b><span>Official sheets never state one-entry-only in this set</span></div>
<div class="stat"><span>Entry rules confirmed (all multi-entry)</span><b>%d</b><span>Wynn, Bellagio, Caesars — quoted excerpts on each row</span></div>
<div class="stat"><span>Rows still unverified</span><b>%d</b><span>+%d prior official captures awaiting re-check</span></div>
<div class="stat"><span>Earliest listed start</span><b>9:10 AM</b><span>Venetian #46 turbo satellite (structure sheet 25)</span></div>
<div class="stat"><span>Room tax (Clark County)</span><b>13.38%%</b><span>Applied to rate + resort fee in every true-cost figure</span></div>
</div>
<div class="callout danger"><strong>Executive decision: no tournament in this snapshot is confirmed single-entry.</strong>
Every official structure sheet that states an entry rule describes <i>re-entry, rebuys, or add-ons</i>. The Venetian
DeepStack sheets state no entry rules at all — silence is not confirmation. The single-entry toggle on the Tournaments
page therefore returns zero rows; play the confirmed multi-entry events only with that in mind, or call the room to
request written maximum-entry terms (see <a href="questions.html">Q&amp;A</a>).</div>
<div class="callout warn"><strong>Best value screen (descriptive arithmetic):</strong> guarantee ÷ buy-in is shown only after the
total entry fee and guarantee were confirmed from official sheets. It is not expected value. Bounty and flight events are
ranked separately below and labeled.</div>
<section class="section"><h2>Top ratios among rows without confirmed multi-entry terms (candidates)</h2>
<div class="grid">%s</div>
<p class="muted">These rows remain unverified for entry rules — they are candidates, not confirmed single-entry events.</p>
<h2>Top ratios among rows with confirmed entry rules (all multi-entry — spending advantage exists)</h2>
<div class="grid">%s</div></section>
<section class="section"><h2>Lodging — true cost per night = (rate + resort fee) × 1.1338</h2>
<div class="grid">
<article class="card"><span class="tag">host venue</span><h3>Venetian / Palazzo — $55 fee</h3>
<p>Official poker rate from $119/$209 (qualifying play: 6h cash or a $300+ tournament buy-in per night).
True cost at $119: <b>$197.28</b>/night. <a href="hotels.html">Hotel math →</a></p></article>
<article class="card"><span class="tag">confirmed fee</span><h3>Wynn / Encore — $55 fee</h3>
<p>Self-parking included for 2 vehicles. True cost scenario and walking minutes on the hotel page.
<a href="hotels.html">Hotel math →</a></p></article>
<article class="card"><span class="tag">confirmed fee</span><h3>Bellagio &amp; ARIA — $55 fee</h3>
<p>Official T&amp;C pages state $55 + tax (the earlier $50 ARIA figure was corrected —
<a href="monitor.html">see change log</a>). 72-hour cancellation.</p></article>
</div></section>
<section class="section"><h2>What this dashboard adds</h2>
<div class="grid">
<article class="card"><h3>Trip cost calculator</h3><p>entries × buy-ins + nights × true hotel cost, with parking and the descriptive guarantee ratio. <a href="calculator.html">Open calculator →</a></p></article>
<article class="card"><h3>Day plan with overlap flags</h3><p>Primary event + conditional fallback per day; sequences that cannot be played are flagged using start time, late-reg cutoff and plausible duration. <a href="schedule.html">Day plan →</a></p></article>
<article class="card"><h3>Automatic source re-check</h3><p>A scheduled GitHub Actions job re-fetches every official URL daily, stores hashes, and marks rows whose source changed. <a href="monitor.html">Change monitor →</a></p></article>
<article class="card"><h3>One page per venue</h3><p>Venetian, Wynn, Bellagio, Caesars, ARIA — each with its events and walkable hotels. <a href="venues.html">Venues →</a></p></article>
</div></section>
<section class="section"><h2>Recommended next move</h2>
<ol class="tight">
<li>Fix trip dates and a nightly budget, then use the <a href="calculator.html">trip calculator</a> with real hotel quotes for those dates (rates here are published leads, not dated quotes).</li>
<li>For each candidate event, call the poker room and get <b>written</b> maximum-entry / no-rebuy / no-add-on terms — the single-entry filter cannot be satisfied from public sheets alone (<a href="workflow.html">workflow</a>).</li>
<li>Re-verify schedules, rates and policies before any nonrefundable payment — the <a href="monitor.html">change monitor</a> tracks official pages daily.</li>
</ol></section>""" % (n_total, n_single, n_conf, n_unv, n_prior, cards, cards_conf)
    return page("Executive brief", "index.html", body)

# ---------------------------------------------------------- tournaments page
def build_tournaments():
    dated = DATED
    series = SERIES
    conf_multi = [x for x in EV if x["entry_rules"].get("status") == "confirmed"]
    unv = [x for x in EV if x["entry_rules"].get("status") in ("unverified", "implied-multi")]
    # ranked screens
    def rank_rows(rows):
        out = []
        for x in sorted([r for r in rows if ratio(r)], key=lambda r: -ratio(r)):
            out.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class="mono">%.1fx</td><td>%s</td></tr>' % (
                e(x.get("venue")), e(x["name"]), money(x.get("buy_in")), money(x.get("guarantee")),
                ratio(x), STATUS_PILL.get(x["entry_rules"].get("status"), "")))
        return "".join(out)
    one_day_cash = [x for x in EV if ratio(x) and x.get("kind") in ("one-day", "multi-flight")
                    and not x.get("bounty") and x.get("kind") != "satellite"]
    bounty = [x for x in EV if ratio(x) and x.get("bounty")]
    sats = [x for x in EV if x.get("kind") == "satellite"]
    body = """
<h1>Tournaments</h1>
<p class="muted">Every row links its official schedule and structure sheet. Entry-rule badges:
<span class="pill ok">confirmed</span> = rule quoted from an official sheet read 2026-11-17;
<span class="pill info">prior official capture</span> = recorded from official documents in the 2026-11-16 research pass;
<span class="pill warn">multi-entry implied</span> = sheet prices subsequent buy-ins;
<span class="pill grey">unverified</span> = no official statement found (never treat as single-entry).</p>
<div class="toolbar">
<input type="text" class="search-box" data-target="events-table" placeholder="Search all events…">
<label>Date: <select id="date-filter"><option value="">All dates</option>%s</select></label>
<label class="chk"><input type="checkbox" class="entry-toggle" data-kind="single"> Single-entry / freezeout confirmed</label>
<label class="chk"><input type="checkbox" class="entry-toggle" data-kind="confirmed" checked> Confirmed multi-entry</label>
<label class="chk"><input type="checkbox" class="entry-toggle" data-kind="prior-capture" checked> Prior official capture</label>
<label class="chk"><input type="checkbox" class="entry-toggle" data-kind="implied-multi" checked> Multi-entry implied</label>
<label class="chk"><input type="checkbox" class="entry-toggle" data-kind="unverified" checked> Unverified</label>
</div>
<div class="callout"><strong>Ranking policy:</strong> rows are ranked below only where the total entry fee and guarantee are
both confirmed. The ratio (guaranteed pool ÷ entry fee) is descriptive arithmetic — not a forecast. Bounty events
(guarantee includes bounty money) and flight/multi-day events (guarantee covers all flights; buy-in shown per flight) are
ranked in separate tables.</div>
<section class="section"><h2>Rank A — one-day &amp; flight cash events (non-bounty)</h2>
<div class="tablewrap"><table><thead><tr><th>Venue</th><th>Event</th><th>Entry fee</th><th>Guarantee</th><th>Ratio</th><th>Entry rules</th></tr></thead>
<tbody>%s</tbody></table></div></section>
<section class="section"><h2>Rank B — bounty events (guarantee includes bounty money — labeled separately)</h2>
<div class="tablewrap"><table><thead><tr><th>Venue</th><th>Event</th><th>Entry fee</th><th>Guarantee</th><th>Ratio</th><th>Entry rules</th></tr></thead>
<tbody>%s</tbody></table></div></section>
<section class="section"><h2>Rank C — satellites (seats, not cash — excluded from cash ranking)</h2>
<div class="tablewrap"><table><thead><tr><th>Venue</th><th>Event</th><th>Entry fee</th><th>Prize</th><th>Ratio</th><th>Entry rules</th></tr></thead>
<tbody>%s</tbody></table></div></section>
<section class="section"><h2>Spending-advantage section — confirmed re-entry / rebuy / add-on</h2>
<p class="muted">Official sheets confirm that money can be added beyond one entry. Kept separate per policy.</p>
<div class="tablewrap"><table><thead><tr><th>Venue</th><th>Event</th><th>Entry fee</th><th>Guarantee</th><th>Extra-buy terms</th></tr></thead>
<tbody>%s</tbody></table></div></section>
<section class="section"><h2>All rows (%d)</h2>%s</section>""" % (
        "".join('<option value="%s">%s</option>' % (e(d), e(d)) for d in sorted({x["date"] for x in DATED})),
        rank_rows(one_day_cash), rank_rows(bounty), rank_rows(sats),
        "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class="muted">%s</td></tr>' % (
            e(x.get("venue")), e(x["name"]), money(x.get("buy_in")), money(x.get("guarantee")),
            e(x["entry_rules"].get("excerpt"))) for x in conf_multi),
        len(EV), events_table(sort_events(EV)))
    return page("Tournaments", "tournaments.html", body)

# ------------------------------------------------------------ schedule page
def plausible_end(ev):
    try:
        h, m = ev.get("time", "12:00").replace(" AM", "").replace(" PM", "").split(":")
        h = int(h)
        if "PM" in (ev.get("time") or "") and h != 12: h += 12
        if "AM" in (ev.get("time") or "") and h == 12: h = 0
        start = h * 60 + int(m)
    except Exception:
        return None, None
    lvl = ev.get("level_minutes") or 30
    dur = 4 * 60 if lvl <= 20 else (9 * 60 if lvl <= 30 else 10 * 60)
    return start, start + dur

def fmt_min(m):
    m = int(m) % (24 * 60)
    ap = "AM" if m < 720 else "PM"
    h = m // 60; h = h if 1 <= h <= 12 else (h - 12 if h > 12 else 12)
    return "%d:%02d %s" % (h, m % 60, ap)

def build_schedule():
    days = {}
    for ev in DATED:
        days.setdefault(ev["date"], []).append(ev)
    rows = []
    for d in sorted(days):
        evs = sorted(days[d], key=lambda x: plausible_end(x)[0] or 0)
        tmap = {x["id"] + "|" + (x.get("name") or ""): plausible_end(x) for x in evs}
        def se(x): return tmap[x["id"] + "|" + (x.get("name") or "")]
        primary = evs[0]
        fallbacks = []
        flags = []
        for ev in evs[1:]:
            if se(primary)[1] and se(ev)[0] and se(ev)[0] < se(primary)[1]:
                flags.append("%s (%s) cannot follow %s (%s): estimated end %s crosses its start — play it only as a "
                             "conditional fallback after exiting the primary." % (
                             ev["name"], ev.get("time"), primary["name"], primary.get("time"), fmt_min(se(primary)[1])))
                fallbacks.append(ev)
            else:
                fallbacks.append(ev)
        fb_txt = "".join('<li>%s — %s · %s · <span class="pill warn">conditional</span> only if you exit the primary first</li>' % (
            e(x["name"]), e(x.get("time")), money(x.get("buy_in"))) for x in fallbacks) or "<li class='muted'>none listed</li>"
        fl_txt = "".join('<li class="muted">%s</li>' % e(f) for f in flags) or "<li class='muted'>no hard overlaps detected with the duration model</li>"
        rows.append("""<tr><td><b>%s</b></td><td>%s<br><span class="muted">%s · %s gtd</span><br>
<span class="muted">est. end %s (estimate — durations unverified)</span></td><td><ul class="tight">%s</ul></td>
<td><ul class="tight">%s</ul></td></tr>""" % (
            e(d), e(primary["name"]), e(primary.get("time")), money(primary.get("guarantee")),
            fmt_min(se(primary)[1]) if se(primary)[1] else "?", fb_txt, fl_txt))
    body = """
<h1>Day plan — one primary per day, conditional fallbacks, impossible sequences flagged</h1>
<p class="muted">Plausible duration model (marked as an estimate everywhere): 20-minute-level events ≈ 4 h,
30-minute-level one-days ≈ 9 h, 40-minute multi-flight day-1s ≈ 10 h. Finish times are not published by the venues, so
overlap verdicts are planning heuristics, not verified facts. A later event is a <b>conditional fallback</b> only: you can
play it if you bust or exit the primary before its registration closes.</p>
<div class="callout"><strong>8 AM goal:</strong> no official schedule in this set starts at 8:00 AM. The earliest listed start is
9:10 AM (Venetian #46 turbo satellite, structure sheet 25). The earliest full tournament starts are 10:00 AM (Caesars
daily) and 10:10 AM (Venetian Seniors/RaceDay). An all-day plan is feasible from ~10 AM, with nightly events (Wynn 6 PM,
Caesars 6 PM/9 PM) as conditional evening fallbacks.</div>
<section class="section"><h2>Daily recurring rooms (every day of the week)</h2>
<div class="tablewrap"><table><thead><tr><th>Room</th><th>Event</th><th>Start</th><th>Entry fee</th><th>Guarantee</th><th>Entry rules</th></tr></thead><tbody>
%s
</tbody></table></div></section>
<section class="section"><h2>Venetian DeepStack IV — dated days (Nov 16 – Dec 23, 2026)</h2>
<div class="tablewrap"><table><thead><tr><th>Date</th><th>Primary event</th><th>Conditional fallbacks</th><th>Overlap flags</th></tr></thead>
<tbody>%s</tbody></table></div></section>""" % (
        "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            e(x.get("venue")), e(x["name"]), e(x.get("time")), money(x.get("buy_in")),
            money(x.get("guarantee")), entry_cell(x)) for x in SERIES),
        "".join(rows))
    return page("Day plan", "schedule.html", body)

# ------------------------------------------------------------- hotels page
def build_hotels():
    hrows = []
    for h in HO:
        fee = money(h.get("resort_fee")) if h.get("resort_fee") is not None else '<span class="pill grey">unverified</span>'
        tax = "%.2f%%" % (h["tax_rate"] * 100) if h.get("tax_rate") else "—"
        scen = ""
        lead = next((r for r in RL if r["hotel"] == h["id"] and r.get("nightly_rate")), None)
        if lead and h.get("resort_fee") is not None:
            true = (lead["nightly_rate"] + h["resort_fee"]) * 1.1338
            scen = ("at published lead %s/night: <b>%s</b>/night true cost" % (money(lead["nightly_rate"]), money(round(true, 2))))
        elif h.get("resort_fee") is not None:
            scen = "true cost = (rate + %s) x 1.1338 — rate varies by date" % money(h["resort_fee"])
        else:
            scen = '<span class="pill grey">fee unverified — cannot compute</span>'
        hrows.append('<tr><td><b>%s</b><br><span class="muted">%s</span></td><td>%s</td><td>%s</td><td>%s</td>'
                     '<td class="muted">%s</td><td class="muted">%s</td><td class="muted">%s</td><td>%s</td><td>%s</td></tr>' % (
            e(h["name"]), e(h["address"]), fee, tax, scen,
            e(h.get("parking")), e(h.get("cancellation")),
            e(h.get("poker_rate") or "—"),
            '<a href="%s">book ↗</a>' % e(h.get("booking_url")),
            ("<br>".join('<span class="pill warn">%s</span>' % e(f) for f in h.get("flags", [])) or "—") +
            '<br><span class="muted">checked ' + e(h["last_checked"]) + "</span>"))
    wrows = []
    for w in WK:
        w30 = "1" if w["status"] in ("≤30", "host venue") else "0"
        pill = {"host venue": '<span class="pill ok">host venue</span>',
                "≤30": '<span class="pill ok">≤ 30 min</span>',
                ">30": '<span class="pill bad">&gt; 30 min</span>'}.get(w["status"], "")
        wrows.append('<tr data-within30="%s"><td>%s</td><td>%s</td><td>%s</td><td class="mono">%s</td><td>%s</td>'
                     '<td class="muted">%s</td><td><a href="%s">live route ↗</a></td></tr>' % (
            w30, e(w["hotel_id"]), e(w["origin_address"]), e(w["destination_address"]),
            (str(w["walk_minutes_estimate"]) + " min") if w["walk_minutes_estimate"] else "0",
            pill, e(w["verified"]), e(w["maps_url"])))
    body = """
<h1>Hotels &amp; true cost</h1>
<div class="callout"><strong>True cost per night = (nightly rate + mandatory resort fee) × (1 + 13.38%% Clark County room tax).</strong>
Parking is added per night in the calculator. Rates shown are official <i>published leads</i> with timestamps — not dated
booking quotes. For a like-for-like comparison, price the same dates and room type on each official booking link and record
it in the <a href="ratelog.html">rate log</a> (checkout total, nightly average, cancellation deadline, timestamp).</div>
<section class="section"><h2>Hotel economics</h2>
<div class="tablewrap"><table id="hotels-table"><thead><tr><th>Hotel</th><th>Resort fee</th><th>Room tax</th>
<th>True cost scenario</th><th>Parking</th><th>Cancellation</th><th>Poker rate</th><th>Official booking</th>
<th>Flags &amp; last checked</th></tr></thead><tbody>%s</tbody></table></div></section>
<section class="section"><h2>Walking routes (official addresses)</h2>
<div class="toolbar"><label class="chk"><input type="checkbox" id="walk30"> Show only ≤ 30-minute walks</label>
<input type="text" class="search-box" data-target="walks-table" placeholder="Search routes…"></div>
<p class="muted">No official source publishes walking minutes; the estimates below are marked as such and each row links a
Google Maps walking route between the official addresses for live verification. The 30-minute limit is applied as a filter.</p>
<div class="tablewrap"><table id="walks-table"><thead><tr><th>Hotel</th><th>From (official address)</th><th>To (venue)</th>
<th>Est. walk</th><th>30-min limit</th><th>Basis</th><th>Verify live</th></tr></thead><tbody>%s</tbody></table></div>
</section>
<section class="section"><h2>Comparison rules (like-for-like)</h2>
<ul class="tight">
<li>Same dates, same occupancy, same room class (standard king/queen), tax and mandatory fee included.</li>
<li>Record checkout total and nightly average, the resort fee and tax rate used, parking, the cancellation deadline, and the exact timestamp of the quote.</li>
<li>Conditional poker rates (Venetian $119/$209) require qualifying play — count the buy-in/hours as part of the cost when comparing.</li>
<li>Parking: Venetian guests $20/day; MGM properties $20/day guests ($20–25 non-guests); Wynn and TI include parking.</li>
</ul></section>""" % ("".join(hrows), "".join(wrows))
    return page("Hotels & true cost", "hotels.html", body)

# ----------------------------------------------------------- rate log page
def build_ratelog():
    rows = []
    for r in RL:
        rows.append('<tr><td>%s</td><td>%s</td><td class="mono">%s</td><td class="mono">%s</td><td class="mono">%s</td>'
                    '<td class="mono">%s</td><td class="mono">%s</td><td class="mono">%s</td><td class="muted">%s</td>'
                    '<td><a href="%s">source ↗</a></td><td class="muted">%s</td></tr>' % (
            e(r["hotel"]), e(r["date_checked"]), e(r["rate_type"]), money(r.get("nightly_rate")),
            money(r.get("resort_fee")), "%.2f%%" % (r["tax_rate"] * 100) if r.get("tax_rate") else "—",
            money(r.get("checkout_total")), money(r.get("nightly_avg")), e(r.get("cancellation_deadline")),
            e(r.get("source_url")), e(r.get("note"))))
    body = """
<h1>Rate log — dated entries, not single values</h1>
<p class="muted">Each observation keeps its own timestamp. <b>checkout_total</b> and <b>nightly_avg</b> stay blank until a
like-for-like dated booking quote is captured (same dates and room class, all mandatory charges included). The scheduled
monitor appends new observations rather than overwriting these.</p>
<div class="tablewrap"><table><thead><tr><th>Hotel</th><th>Checked</th><th>Rate type</th><th>Nightly rate</th>
<th>Resort fee</th><th>Tax</th><th>Checkout total</th><th>Nightly avg</th><th>Cancellation deadline</th><th>Source</th><th>Note</th></tr></thead>
<tbody>%s</tbody></table></div>
<div class="callout warn">Blank cells are deliberate: no official source gave a dated quote for those fields. Never infer them.
Use each hotel's official booking link (on the <a href="hotels.html">Hotels page</a>) to price exact dates and add a log row.</div>""" % "".join(rows)
    return page("Rate log", "ratelog.html", body)

# --------------------------------------------------------- calculator page
def build_calculator():
    fees = {}
    for h in HO:
        lead = next((r for r in RL if r["hotel"] == h["id"] and r.get("nightly_rate")), None)
        fees[h["id"]] = {"fee": h.get("resort_fee"), "rate": lead["nightly_rate"] if lead else None, "name": h["name"]}
    opts = "".join('<option value="%s">%s</option>' % (k, e(v["name"])) for k, v in fees.items())
    body = """
<h1>Trip cost calculator</h1>
<p>Estimated cost of a trip = <b>entries × buy-ins</b> + <b>nights × true hotel cost</b>, where true hotel cost =
(nightly rate + resort fee) × 1.1338 + parking. Defaults come from official published leads; replace them with your dated
quote for a real booking.</p>
<section class="section" id="trip-calc">
<div class="calc-grid">
<div><label>Entries (tournaments × re-entries counted separately)</label><input type="number" id="calc-entries" value="5" min="0" step="1"></div>
<div><label>Buy-in per entry ($)</label><input type="number" id="calc-buyin" value="300" min="0" step="1"></div>
<div><label>Guarantee of the event ($, optional — for the ratio)</label><input type="number" id="calc-gtd" value="10000" min="0" step="1"></div>
<div><label>Nights</label><input type="number" id="calc-nights" value="4" min="0" step="1"></div>
<div><label>Hotel (sets default fee/rate)</label><select id="calc-hotel">%s</select></div>
<div><label>Nightly rate ($)</label><input type="number" id="calc-rate" value="119" min="0" step="0.01"></div>
<div><label>Resort fee ($/night)</label><input type="number" id="calc-fee" value="55" min="0" step="0.01"></div>
<div><label>Room tax rate</label><input type="number" id="calc-tax" value="0.1338" min="0" step="0.0001"></div>
<div><label>Parking ($/night)</label><input type="number" id="calc-parking" value="20" min="0" step="0.01"></div>
</div>
<div class="result">
<div>Entries total: <span class="big" id="out-entries">—</span> &nbsp;·&nbsp; Hotel total: <span class="big" id="out-hotel">—</span>
 &nbsp;·&nbsp; <b>Trip total: <span class="big" id="out-trip">—</span></b></div>
<p class="muted" id="out-detail"></p>
<p class="muted">Guaranteed pool ÷ entry fee: <b id="out-ratio">—</b></p>
</div></section>
<section class="section"><h2>What this calculator does not include</h2>
<ul class="tight">
<li>Flights, food, resort incidentals ($150/night hold at Venetian/MGM), tips.</li>
<li>Re-entry/rebuy/add-on costs — add them as extra entries if you plan to use them (see the spending-advantage section).</li>
<li>Qualifying-play cost of conditional poker rates (6 h cash play or a $300+ tournament buy-in per night at the Venetian).</li>
</ul></section>
<script>window.HOTEL_FEES = %s;</script>""" % (opts, json.dumps(fees))
    return page("Trip calculator", "calculator.html", body)

# -------------------------------------------------------------- venues
VENUE_MAP = {
 "Venetian": ("venues/venetian.html", "The Venetian Resort — poker room at Palazzo Level 2",
   "https://www.venetianlasvegas.com/resort/casino/poker.html"),
 "Wynn": ("venues/wynn.html", "Wynn Las Vegas — poker room located in Encore", "https://www.wynnlasvegas.com/casino/poker"),
 "Bellagio": ("venues/bellagio.html", "Bellagio — poker room", "https://bellagio.mgmresorts.com/en/casino/poker.html"),
 "Caesars Palace": ("venues/caesars.html", "Caesars Palace — poker room", "https://www.caesars.com/caesars-palace/casino"),
 "ARIA": ("venues/aria.html", "ARIA — poker room", "https://aria.mgmresorts.com/en/casino/poker.html"),
}

def venue_page(key):
    path, title, url = VENUE_MAP[key]
    evs = sort_events([x for x in EV if x.get("venue") == key])
    dest_key = {"Venetian": "Venetian Poker", "Wynn": "Wynn Poker", "Bellagio": "Bellagio Poker",
                "Caesars Palace": "Caesars Palace Poker", "ARIA": "ARIA"}[key]
    hotels = []
    for h in HO:
        w = next((x for x in WK if x["hotel_id"] == h["id"] and dest_key in x["destination_address"]), None)
        fee = money(h.get("resort_fee")) if h.get("resort_fee") is not None else '<span class="pill grey">unverified</span>'
        if w:
            mins = (str(w["walk_minutes_estimate"]) + " min") if w["walk_minutes_estimate"] else "0 (host)"
            pill = ('<span class="pill ok">%s</span>' % e(w["status"])) if w["status"] in ("≤30", "host venue") \
                   else '<span class="pill bad">%s</span>' % e(w["status"])
            route = ' · <a href="%s">route ↗</a>' % e(w["maps_url"])
        else:
            mins, pill, route = "—", '<span class="pill grey">not measured</span>', ""
        hotels.append('<tr><td>%s</td><td>%s</td><td class="mono">%s</td><td>%s%s</td></tr>' % (
            e(h["name"]), fee, mins, pill, route))
    body = """
<h1>%s</h1>
<p class="muted">Official page: <a href="%s">%s ↗</a> · rows below are the events this dashboard tracks for this venue;
each links its official schedule/structure source. Hotels listed are within the 30-minute walking limit (host venue first).</p>
<section class="section"><h2>Events (%d)</h2>%s</section>
<section class="section"><h2>Hotels within 30 minutes (walk estimates)</h2>
<div class="tablewrap"><table><thead><tr><th>Hotel</th><th>Resort fee</th><th>Walk to this room</th><th>30-min status</th></tr></thead>
<tbody>%s</tbody></table></div></section>""" % (
        e(title), e(url), e(key), len(evs), events_table(evs, table_id="vt-" + key.lower().replace(" ", "-")),
        "".join(hotels))
    return page(key, "venues.html", body, depth=1)

def build_venues_index():
    cards = []
    for key, (path, title, url) in VENUE_MAP.items():
        n = len([x for x in EV if x.get("venue") == key])
        cards.append('<article class="card"><span class="tag">%d events tracked</span><h3>%s</h3>'
                     '<p class="muted">%s</p><p><a class="button ghost" href="%s">Open venue page →</a></p></article>' % (
            n, e(key), e(title), path))
    body = """
<h1>Venues</h1>
<p>One page per poker venue: its events (with source links and entry-rule excerpts) and the hotels within the
30-minute walking limit.</p>
<div class="grid">%s</div>
<div class="callout warn"><strong>ARIA note:</strong> no official daily tournament schedule was captured from the ARIA
poker page; its venue page is included for lodging/walking reference and lists the gap as a
<a href="review.html">flagged item</a>.</div>""" % "".join(cards)
    return page("Venues", "venues.html", body)

# ------------------------------------------------------------- monitor page
def build_monitor():
    rows = "".join(
        '<tr><td>%s</td><td>%s</td><td class="mono">%s</td><td>%s</td><td class="pill warn">SOURCE CHANGED</span></td>'
        '<td class="muted">%s</td><td><a href="%s">source ↗</a></td></tr>' % (
            e(c["date"]), e(c.get("row_ref")), e(c.get("field")), e(c.get("change")), e(c.get("severity")),
            e(c.get("url")))
        for c in CL)
    snaps = "".join(
        '<tr><td class="mono">%s</td><td><a href="%s">%s</a></td><td class="muted">%s</td><td class="mono">%s</td></tr>' % (
            e(v["source_id"]), e(u), e(v["label"]), e(v.get("fetched_at")), e((v.get("sha256") or "—")[:16]))
        for u, v in SN.items())
    body = """
<h1>Change monitor — scheduled official-source re-check</h1>
<p>The repository ships a scheduled GitHub Actions workflow (<span class="mono">.github/workflows/monitor.yml</span>) that
runs every morning (14:00 UTC ≈ 6:00–7:00 AM PT). It re-fetches every official URL below with
<span class="mono">tools/monitor_sources.py</span>, stores a content hash and excerpt snapshot, appends any differences to
<span class="mono">data/change_log.json</span>, and commits the result. Rows whose source changed appear here with a
<b>SOURCE CHANGED</b> marker and carry a badge on the Tournaments/Hotels pages after the next site build.</p>
<div class="callout"><strong>How to read it:</strong> a change entry means the official page content moved — not that a value
necessarily changed. Open the source link, compare the excerpt, then update the row (and this log) deliberately.
Changed rows are marked, never silently rewritten.</div>
<section class="section"><h2>Change log (%d)</h2>
<div class="tablewrap"><table><thead><tr><th>Date</th><th>Row</th><th>Field</th><th>What changed</th><th>Marker</th><th>Severity</th><th>Source</th></tr></thead>
<tbody>%s</tbody></table></div></section>
<section class="section"><h2>Monitored official URLs (%d)</h2>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Official page</th><th>Last fetched</th><th>Hash prefix</th></tr></thead>
<tbody>%s</tbody></table></div></section>
<section class="section"><h2>Daily schedule feed</h2>
<p>The same workflow stores a text snapshot of each room's official daily-schedule page under
<span class="mono">data/feeds/YYYY-MM-DD/</span> each morning, so schedule drift between runs is diffable.
Snapshots are committed to the repository (small text files), keeping the large datasets out of Git.</p></section>""" % (
        len(CL), rows, len(SN), snaps)
    return page("Change monitor", "monitor.html", body)

# ------------------------------------------------------------ workflow page
def build_workflow():
    body = """
<h1>Decision workflow</h1>
<p class="muted">The staged process this dashboard is built to support — work top to bottom; do not skip the confirmations.</p>
<section class="section"><ol class="tight">
<li><b>Fix trip dates and a nightly budget/quality floor.</b> Without dates, hotel totals are not comparable. Use the
<a href="calculator.html">trip calculator</a> to set the envelope.</li>
<li><b>For candidate events, obtain the official structure sheet and written maximum-entry / no-rebuy / no-add-on rules.</b>
Remove any event that does not match the single-entry policy. In this snapshot, that filter removes everything — the
public sheets state re-entry/rebuy/add-on or say nothing (see <a href="tournaments.html">entry-rule excerpts</a>).</li>
<li><b>Compare only surviving events</b> on guaranteed pool, buy-in, starting stack / blind duration, payout structure, and
daily schedule fit. The <a href="tournaments.html">ranking tables</a> do the arithmetic; the columns carry the caveats.</li>
<li><b>Obtain itemized hotel totals for the same stay</b> (checkout total, nightly average, resort fee, tax, parking,
cancellation deadline, rate timestamp) and record them in the <a href="ratelog.html">rate log</a>. Check the walking route
under 30 minutes (<a href="hotels.html">walk filter</a>).</li>
<li><b>Build one event per day first.</b> Add evening events only where you can realistically exit the earlier event —
the <a href="schedule.html">day plan</a> marks these as conditional fallbacks and flags impossible sequences.</li>
<li><b>Reconfirm official schedules, rates and policies before any nonrefundable payment.</b> The
<a href="monitor.html">change monitor</a> shows what moved since the last check.</li>
</ol></section>
<section class="section"><h2>Standing rules used throughout</h2>
<ul class="tight">
<li>Ranking happens only after total entry fee and guarantee are confirmed; the ratio is descriptive, never a forecast.</li>
<li>Bounty, satellite/seat, and multi-flight events are labeled and ranked separately.</li>
<li>Rates are kept as a dated log, never a single overwritten value.</li>
<li>Blank + flagged beats inferred. Every row links an official source or is marked unverified.</li>
</ul></section>"""
    return page("Workflow", "workflow.html", body)

# --------------------------------------------------------- questions page
QA = [
 ("What is confirmed single-entry?", "Nothing in this snapshot. No official Venetian sheet states one-entry-only; Wynn, Bellagio and Caesars sheets state the opposite (re-entry/rebuy/add-on).",
  "Get written maximum-entry terms from each poker room; add the response to the rate/policy log with its date."),
 ("Why does the single-entry toggle return zero rows?", "Because zero events have an official sheet confirming a single entry or freezeout. This is the honest result of reading every sheet, not a data gap.",
  "Call the Venetian poker room (702-414-7657) and ask for the re-entry policy of specific DSE IV one-day events."),
 ("What is the earliest tournament start?", "9:10 AM — Venetian Event #46 $260 turbo milestone satellite (structure sheet 25). Full tournaments: 10:00 AM (Caesars daily) and 10:10 AM (Venetian Seniors/RaceDay). No 8:00 AM start exists in any reviewed official schedule.",
  "Nothing further — verified from sheets. If an 8 AM start is mandatory, expand the search to off-Strip rooms (flagged separately)."),
 ("Can I play all day, 8 AM to late?", "Not from 8 AM. A ~10 AM start with a mid-afternoon primary and a conditional 5:10/6 PM fallback is feasible; overlap flags on the day plan show which pairings cannot both be played in full.",
  "Real finish times only become verifiable during play; treat durations as estimates until then."),
 ("What is the true cost of a hotel night?", "(rate + resort fee) × 1.1338. At the Venetian poker rate $119 + $55 fee → $197.28; at $209 → $299.32. Parking extra ($20/day at Venetian and MGM; free at Wynn and TI).",
  "Price exact dates on the official booking links and log the quote (checkout total, cancellation deadline, timestamp)."),
 ("Are the Venetian poker rates guaranteed?", "No — 'as low as $119/$209', subject to availability, blackout dates, and 6 hours of live cash play (or a $300+ tournament buy-in) per night, verified before 2 a.m. Failure adjusts the night to prevailing rate.",
  "Ask the poker room for the rate calendar for your dates (code EPOKR25) and get it in writing."),
 ("What does the guarantee ÷ buy-in ratio mean?", "Pure arithmetic: how many buy-ins the advertised guarantee equals. Not expected value. Bounty guarantees include bounty money (ranked separately); multi-flight guarantees cover all flights (buy-in shown per flight).",
  "Compare payout structures (12.5% vs 15% paid) before preferring a bigger ratio."),
 ("Which hotels are within 30 minutes walking?", "Venetian/Palazzo (host), Wynn/Encore (~14 min), TI (~12), Harrah's (~10), Horseshoe (~14), Caesars (~16), ARIA (~18), Bellagio (~22). Park MGM (~32) fails the limit. Minutes are map estimates — each row links a live Google Maps route.",
  "Verify each route on foot or via the maps link before booking; no official source publishes walking minutes."),
 ("What changed recently on official pages?", "ARIA resort fee corrected to $55 (was $50 in a secondary snapshot); Bellagio Saturday sheet has a $1,100 vs $600 buy-in conflict and a stale date; Venetian sheet 25 revealed a 9:10 AM start.",
  "Watch the change monitor — it re-checks all official URLs every morning."),
 ("Is the Bellagio Saturday event playable?", "Unknown — the official sheet contradicts itself on the buy-in ($1,100 header vs $600 rules text) and references a September Day 2 date. The row is flagged; do not book travel around it.",
  "Call Bellagio poker (702-693-7290) for the current Saturday structure and buy-in in writing."),
 ("Are Wynn dailies single-entry?", "No. Official terms confirm re-entry (Mon–Thu, Sat–Sun, Nightly) and unlimited rebuys + one add-on (Friday). All are in the spending-advantage section with quoted excerpts.",
  "Nothing further — confirmed. Treat any 'single-entry' claim elsewhere as unverified."),
 ("What about WPT World Championship events?", "Series runs Nov 27 – Dec 21, 2026 at Wynn. Sheets read this session confirm unlimited re-entry on the sampled events; 11 rows carry prior official captures, 4 remain unverified (including the $10,400 World Championship).",
  "Read the remaining WPT sheets before entering; the $10,400's entry terms are the highest-value gap."),
 ("How are walking times verified?", "They are not — no official property publishes walking minutes. Estimates carry a Google Maps walking-route link built from the official addresses, and the ≤30-min filter is applied to them.",
  "Walk the route on arrival day; adjust the estimate in the data file with your measured time."),
 ("What hotel fees are still unverified?", "Caesars Palace resort fee (secondary sources conflict $49.95 vs $54.95), Park MGM/NYNY/Harrah's/Horseshoe fees, and several cancellation terms. All are blank and flagged on the review page.",
  "Fetch each property's booking terms page (the fee appears at checkout) or call reservations; log it in the rate log with a timestamp."),
]

def build_questions():
    rows = "".join('<tr><td><b>%s</b></td><td>%s</td><td class="muted">%s</td></tr>' % (e(q), e(a), e(n)) for q, a, n in QA)
    body = """
<h1>Questions, information, and answers</h1>
<p class="muted">What is known, what is missing, and how each gap would be closed — before any decision is made on it.</p>
<div class="tablewrap"><table><thead><tr><th>Question</th><th>Answer from verified data</th><th>Missing information / how to discover it</th></tr></thead>
<tbody>%s</tbody></table></div>""" % rows
    return page("Q&A", "questions.html", body)

# --------------------------------------------------------- suggestions page
SUG = [
 ("S1", "Get written entry-policy statements from the Venetian and Bellagio poker rooms for the specific candidate events",
  "Turns the zero-row single-entry filter into a real shortlist", "Low cost — one call/email per room",
  "Rooms may decline to put it in writing", "review — highest priority"),
 ("S2", "Capture dated booking quotes for Nov 17–Dec 23 stays on the official booking links and append them to the rate log",
  "Makes hotel totals like-for-like and enables true checkout totals", "Manual quotes or an authorized API",
  "Rates move; quotes expire", "review"),
 ("S3", "Extend the source monitor to parse schedule PDFs and diff extracted fields (buy-in/guarantee/start) instead of whole-page hashes",
  "Flags the exact row/value that changed, not just that a page moved", "Build-time only",
  "PDF layout changes break parsers", "review"),
 ("S4", "Add measured walking times (phone GPS) for each hotel–venue pair and store them beside the map estimates",
  "Replaces estimates with first-hand data", "One walk per pair",
  "Route closures/seasonal detours", "review"),
 ("S5", "Add off-Strip rooms (Orleans, South Point, Golden Nugget) in a separate section for 8 AM starts",
  "May satisfy the 'start at 8 AM' goal", "More research",
  "Dilutes the Strip-walking constraint", "review"),
 ("S6", "Record payout structures (percent paid, bubble format) per event and factor them into the comparison table",
  "The 12.5% vs 15% paid difference matters as much as the ratio", "Structure sheets already partly cover it",
  "Sheets omit some payout tables", "review"),
 ("S7", "Automate hotel quote capture via each chain's public booking API where terms permit",
  "Dated checkout totals without manual work", "Engineering; terms-of-service review required",
  "ToS risk — must be cleared first", "review — blocked on ToS check"),
 ("S8", "Add a 'policy change' subscription: email or issue opened when the monitor marks a row",
  "Turns the change log into action", "GitHub Actions + issues",
  "Noise if pages change daily", "review"),
]
def build_suggestions():
    rows = "".join(
        '<tr><td><b>%s</b></td><td>%s</td><td class="muted">%s</td><td class="muted">%s</td><td class="muted">%s</td><td><span class="pill info">%s</span></td></tr>' % s
        for s in SUG)
    body = """
<h1>Suggestions — review and choose before implementing</h1>
<p class="muted">Nothing here is implemented automatically. Each row states the expected decision value, cost and risk so
you can pick a path. Record a decision (approve / defer / reject) and only then should work start.</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Suggestion</th><th>Expected value</th><th>Cost</th><th>Risk</th><th>Status</th></tr></thead>
<tbody>%s</tbody></table></div>
<div class="callout"><strong>Recommended review order:</strong> S1 → S2 → S6 → S3. S1 and S2 directly unblock the two
filters that currently return nothing useful (single-entry rows and dated hotel totals). S7 must not start until its
terms-of-service check is cleared.</div>""" % rows
    return page("Suggestions", "suggestions.html", body)

# ------------------------------------------------------------- review page
def build_review():
    ev_flags = []
    for x in EV:
        for f in (x.get("flags") or []):
            ev_flags.append((x["id"], x["name"], f, x.get("structure_url") or x.get("source_url")))
        if x["entry_rules"].get("status") == "unverified":
            ev_flags.append((x["id"], x["name"], "Entry rules unverified — not eligible for the single-entry section",
                             x["entry_rules"].get("source_url")))
    h_flags = []
    for h in HO:
        for f in (h.get("flags") or []):
            h_flags.append((h["id"], h["name"], f, SRC.get(h.get("resort_fee_source"), {}).get("url", h.get("booking_url"))))
    rows = "".join('<tr><td class="mono">%s</td><td>%s</td><td><span class="pill warn">%s</span></td><td><a href="%s">source ↗</a></td></tr>' % (
        e(i), e(n), e(f), e(u)) for i, n, f, u in ev_flags)
    hrows = "".join('<tr><td class="mono">%s</td><td>%s</td><td><span class="pill warn">%s</span></td><td><a href="%s">source ↗</a></td></tr>' % (
        e(i), e(n), e(f), e(u)) for i, n, f, u in h_flags)
    body = """
<h1>Flagged for review</h1>
<div class="callout warn">These items do <b>not</b> block using the dashboard, but they must not be treated as verified.
Every flag keeps its official source link so you can check it yourself. Unverified values are left blank in the tables.</div>
<section class="section"><h2>Event flags (%d)</h2>
<div class="tablewrap"><table><thead><tr><th>Row</th><th>Event</th><th>Flag</th><th>Source</th></tr></thead><tbody>%s</tbody></table></div></section>
<section class="section"><h2>Hotel flags (%d)</h2>
<div class="tablewrap"><table><thead><tr><th>Row</th><th>Hotel</th><th>Flag</th><th>Source</th></tr></thead><tbody>%s</tbody></table></div></section>
<section class="section"><h2>Unverified summary</h2>
<ul class="tight">
<li>%d event rows have unverified entry rules (mostly Venetian — the sheets are silent).</li>
<li>0 rows are confirmed single-entry.</li>
<li>Caesars Palace, Park MGM, Harrah's, Horseshoe resort fees are blank (not stated on the pages fetched).</li>
<li>Walking minutes are map estimates (no official source publishes them).</li>
<li>Rate-log rows have no dated checkout totals yet — published leads only.</li>
</ul></section>""" % (
        len(ev_flags), rows, len(h_flags), hrows,
        sum(1 for x in EV if x["entry_rules"].get("status") == "unverified"))
    return page("Flagged for review", "review.html", body)

# ------------------------------------------------------------ sources page
def build_sources():
    rows = "".join(
        '<tr><td class="mono">%s</td><td>%s</td><td><a href="%s">%s</a></td><td>%s</td></tr>' % (
            e(s["id"]), e(s["label"]), e(s["url"]), e(s["url"]), e(s["last_checked"]))
        for s in SRC.values())
    body = """
<h1>Sources</h1>
<p class="muted">Every confirmed value on this site traces to one of these official operator documents. Last-checked dates
are per document; the scheduled monitor re-fetches them all.</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Document</th><th>Official URL</th><th>Last checked</th></tr></thead>
<tbody>%s</tbody></table></div>""" % rows
    return page("Sources", "sources.html", body)

# --------------------------------------------------------- repo review page
def build_repo_review():
    items = [
     ("RR-1", "COORDINATION.md contained unresolved git conflict markers (======= / >>>>>>> origin/main) on main",
      "fixed on this branch 2026-11-17 (kept the superset block; no text lost)", "fixed"),
     ("RR-2", "Bellagio Saturday official sheet is internally inconsistent ($1,100 header vs $600 rules) and carries a stale Day 2 date (9/13/26)",
      "row flagged, buy-in left blank", "flagged"),
     ("RR-3", "Earlier snapshots recorded the ARIA resort fee as $50 (secondary source); the official terms page states $55.00 + tax",
      "row corrected to the official value; recorded in the change log", "resolved"),
     ("RR-4", "No event in the repo's data sets is confirmed single-entry; some earlier pages implied candidate rows could qualify",
      "labels standardized: confirmed / prior-capture / implied-multi / unverified; zero rows pass the single-entry filter", "resolved"),
     ("RR-5", "Multiple parallel site fragments coexist in the repo (c07371e3/, 60fb62da/, df41f5c6/, strip/, verified/, pages/)",
      "preserved untouched as prior-session work; the root dashboard is the integration layer and links them", "informational"),
     ("RR-6", "Some CSVs use CRLF line endings (git diff --check warns)",
      "left as-is to avoid touching other sessions' files; new data files use LF", "informational"),
     ("RR-7", "Root README was originally 8 bytes; a fuller README landed in an earlier integration",
      "README updated again on this branch with the current page map", "resolved"),
     ("RR-8", "Wynn 'terms' page used for the $55 resort fee is an offer terms page that also states the standard resort fee",
      "fee cross-checks with the prior official capture; flagged as acceptable but re-checkable", "flagged"),
     ("RR-9", "Root decisions.html from the 2026-11-16 integration is superseded by questions.html + suggestions.html and is no longer in the navigation",
      "file preserved untouched for its historical snapshot; linked content replaced by the new pages", "informational"),
    ]
    rows = "".join('<tr><td class="mono">%s</td><td>%s</td><td class="muted">%s</td><td><span class="pill %s">%s</span></td></tr>' % (
        i, e(a), e(b), "ok" if s in ("fixed", "resolved") else ("warn" if s == "flagged" else "grey"), e(s))
        for i, a, b, s in items)
    body = """
<h1>Repo review — irregularities</h1>
<p class="muted">Found while verifying the repository line by line against official sources. Anything unresolved stays
listed here and on the Flagged for Review page.</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Irregularity</th><th>Action taken</th><th>Status</th></tr></thead>
<tbody>%s</tbody></table></div>""" % rows
    return page("Repo review", "repo-review.html", body)

# ------------------------------------------------------------------- main
def write(path, content):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f: f.write(content)

write("index.html", build_index())
write("tournaments.html", build_tournaments())
write("schedule.html", build_schedule())
write("hotels.html", build_hotels())
write("ratelog.html", build_ratelog())
write("calculator.html", build_calculator())
write("venues.html", build_venues_index())
for k in VENUE_MAP:
    write(VENUE_MAP[k][0], venue_page(k))
write("monitor.html", build_monitor())
write("workflow.html", build_workflow())
write("questions.html", build_questions())
write("suggestions.html", build_suggestions())
write("review.html", build_review())
write("sources.html", build_sources())
write("repo-review.html", build_repo_review())
print("site built: %d pages" % (7 + len(VENUE_MAP) + 7))
