#!/usr/bin/env python3
"""Build the v2 dashboard into v2/ from data/v2/*.json.

Design rules enforced here:
  * every table row carries at least one official source link;
  * a missing value renders as an explicit UNVERIFIED marker, never as a guess;
  * nothing is labelled "single entry" unless an official page says so.
"""
import html, json, os, re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "v2")
OUT = os.path.join(ROOT, "v2")
E = html.escape

SRC = json.load(open(os.path.join(D, "sources.json")))["sources"]
EV = json.load(open(os.path.join(D, "events.json")))
OTHER = json.load(open(os.path.join(D, "events_other.json")))
HOT = json.load(open(os.path.join(D, "hotels.json")))
FLAG = json.load(open(os.path.join(D, "flagged.json")))
QUEST = json.load(open(os.path.join(D, "questions.json")))
SUGG = json.load(open(os.path.join(D, "suggestions.json")))

NAV = [
    ("index.html", "Dashboard"),
    ("tournaments.html", "Tournaments"),
    ("schedule.html", "Day plans"),
    ("hotels.html", "Hotels & rates"),
    ("calculator.html", "Trip calculator"),
    ("venues.html", "Venues"),
    ("separate.html", "Re-entry / add-on"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for review"),
    ("about.html", "Method & sources"),
]

RET = "2026-11-17"
NOFEE = '<span class="blank">—</span>'
UNV = '<span class="blank">UNVERIFIED</span>'
NA_ = "—"
DAGGER = "\u2020"


def src_link(sid, label=None):
    if isinstance(sid, str) and sid.startswith("http"):
        return '<a href="%s">%s</a>' % (E(sid), E(label or "source"))
    s = SRC.get(sid)
    if not s:
        return '<span class="blank">missing source id %s</span>' % E(sid)
    return '<a href="%s" title="%s">%s</a>' % (E(s["url"]), E(s["title"]), E(label or "source"))


def src_links(ids, label="source"):
    return " · ".join(src_link(i, "src%d" % (n + 1)) for n, i in enumerate(ids))


def v(x):
    """Render a value or an explicit unverified marker."""
    if x is None or x == "":
        return '<span class="blank">UNVERIFIED</span>'
    return E(str(x))


def money(x):
    if x is None:
        return '<span class="blank">UNVERIFIED</span>'
    return "$" + f"{int(x):,}"


def page(fname, title, body, active, extra_head=""):
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (h, ' class="active"' if h == active else "", E(t))
        for h, t in NAV
    )
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · Strip Poker Planner</title>
<meta name="description" content="Official-source Las Vegas Strip poker tournament and hotel-cost dashboard. Verified values only; everything else is flagged.">
<link rel="stylesheet" href="assets/app.css">{extra_head}</head><body>
<header class="top"><div class="top-in"><a class="brand" href="../index.html">♠ STRIP POKER <span>PLANNER</span></a>
<span class="stamp">verified {RET} · v2</span></div>
<nav class="main">{nav}</nav></header>
<main>{body}
<footer><p><strong>How to read this site.</strong> A value is shown only if a session runner read it on the official page linked in that row, on {RET}. Everything else says <span class="blank">UNVERIFIED</span> and appears on the <a href="flagged.html">Flagged for review</a> page with its source links. Walking minutes are OpenStreetMap/OSRM foot-routing estimates between property centroids — not a casino publication and not Google or Apple Maps. Guarantee ÷ buy-in is arithmetic, not a forecast.</p>
<p><a href="about.html">Method, source table and repo findings →</a> · <a href="../index.html">Older research snapshots</a></p></footer></main>
<script src="assets/app.js"></script></body></html>"""
    open(os.path.join(OUT, fname), "w").write(doc)


def table(headers, rows, caption="", searchable=True, table_id="t", extra_attrs=""):
    th = "".join('<th%s>%s</th>' % (' class="num"' if h.startswith("#") else "", E(h.lstrip("#"))) for h in headers)
    body = "\n".join(rows)
    attrs = ' data-searchable="1"' if searchable else ""
    return f'''<div class="tablewrap"><table id="{table_id}"{attrs} {extra_attrs}>
<caption>{caption}<span data-count style="float:right"></span></caption>
<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table><p data-empty style="display:none;padding:10px 12px" class="muted">No rows match the current filters.</p></div>'''


def controls(show_date=True, show_se=True, show_walk=False, show_kind=False):
    bits = ['<label>Search all tables<input type="text" id="q" placeholder="venue, event, date, fee…"></label>']
    if show_date:
        bits.append('<label>From date<input type="date" id="dfrom" value="2026-11-17"></label>')
        bits.append('<label>To date<input type="date" id="dto" value="2026-12-23"></label>')
    if show_se:
        bits.append('<label class="check"><input type="checkbox" id="seOnly"> official single-entry rule only</label>')
    if show_walk:
        bits.append('<label class="check"><input type="checkbox" id="walk30"> ≤30 min walk only</label>')
    if show_kind:
        bits.append('<label class="check"><input type="checkbox" id="noSat"> hide satellites</label>')
    bits.append('<button class="btn ghost" id="resetFilters" type="button">Reset</button>')
    bits.append('<span class="small muted" id="filterCount"></span>')
    return '<div class="controls">' + "".join(bits) + "</div>"



def ratio(e):
    g = e["guarantee_printed"] if e["guarantee_printed"] is not None else e["guarantee_on_sheet"]
    return (g / e["buy_in"]) if (g and e["buy_in"]) else None


def dashboard_cards():
    rated = [e for e in EV["events"] if ratio(e) and e.get("guarantee_scope") == "entry"]
    top = max(rated, key=ratio)
    cheapest = min((e for e in EV["events"] if e["buy_in"] and e["guarantee_printed"]),
                   key=lambda e: (e["buy_in"], e["date"]))
    cards = []
    cards.append(
        '<article class="card"><span class="tag ok">cheapest verified entry on the Venetian list</span>'
        '<h3>$%s · %s</h3>'
        '<p>%s, #%s. $%s of the $%s is the house fee and $%s reaches the pool; the guarantee is $%s. '
        'The Caesars Palace $100 daily has the same buy-in but allows re-entry and a $50 add-on, so it sits in the '
        '<a href="separate.html">separate section</a>.</p></article>'
        % (format(cheapest["buy_in"], ","), E(cheapest["venue"]),
           E(cheapest["date"] + " " + cheapest["start"]), E(cheapest["event_no"]),
           cheapest["fee_house"], format(cheapest["buy_in"], ","),
           format(cheapest["prize_pool_per_entry"], ","),
           format(cheapest["guarantee_printed"], ",")))
    bounty_note = ""
    if top["guarantee_basis"] == "pool_plus_bounties":
        bounty_note = (" Its guarantee is printed as <em>prize pool + total bounties</em>, so part of that $%s is "
                       "bounty money rather than prize pool." % format(top["guarantee_printed"], ","))
    cards.append(
        '<article class="card"><span class="tag info">largest guarantee ÷ buy-in, single-entry-scope rows only</span>'
        '<h3>$%s → $%s (%.0f×)</h3><p>%s. That ratio is arithmetic only — guarantee ÷ '
        'buy-in says nothing about expected value, field size or skill. The house fee is $%s of the $%s (%.1f%%), '
        'confirmed on its own sheet.%s</p></article>'
        % (format(top["buy_in"], ","), format(top["guarantee_printed"] or top["guarantee_on_sheet"], ","),
           ratio(top), E(top["name_printed"].split(" - ")[0] + " · " + top["date"]),
           top["fee_house"], format(top["buy_in"], ","), top["fee_house"] / top["buy_in"] * 100, bounty_note))
    cards.append(
        '<article class="card"><span class="tag warn">same buy-in, different rake</span>'
        '<h3>$300 — but the house fee is $50, $58 or $60</h3>'
        '<p>Three $300 events carry three different house fees depending on their sheet: $58 (events #2 and #12, '
        '19.3%), $60 (event #1 flights, 20.0%) and $50 (the $300 bounty rows, 16.7%). Rake is not uniform across '
        'the series, which is exactly why every row links its own sheet.</p></article>')
    return "".join(cards)



def buyin_rows():
    """Every distinct (buy-in, house fee) split found on an official structure sheet."""
    groups = {}
    for e in EV["events"]:
        if e["buy_in"] is None or e["fee_house"] is None:
            continue
        key = (e["buy_in"], e["fee_house"], e["prize_pool_per_entry"])
        g = groups.setdefault(key, {"events": set(), "sheets": set(), "names": set()})
        g["events"].add(e["event_no"])
        g["sheets"].add(int(e["sheet_url"].split("_")[-1].replace(".pdf", "")))
        g["names"].add(e["name_printed"].split(" - ")[0][:46])
    rows = []
    for (buy, fee, pool), g in sorted(groups.items()):
        pct = fee / buy * 100
        link = " · ".join(src_link("V_S%02d" % n, "s%d" % n) for n in sorted(g["sheets"])[:3])
        rows.append(
            '<tr data-search="venetian %d"><td>Venetian</td>'
            '<td class="small">%s</td><td class="num">$%s</td><td class="num">$%s</td>'
            '<td class="num">%.1f%%</td><td class="num">$%s</td>'
            '<td class="num">%d</td><td>%s</td></tr>'
            % (buy, E(sorted(g["names"])[0]), format(buy, ","), fee, pct,
               format(pool, ","), len(g["events"]), link))
    return rows


# ---------------------------------------------------------------- tournaments
def tournament_rows():
    rows = []
    for e in EV["events"]:
        date = e["date"]
        gtd = e["guarantee_printed"] if e["guarantee_printed"] is not None else e["guarantee_on_sheet"]
        basis = e["guarantee_basis"]
        if gtd is None or not e["buy_in"]:
            ratio = '<span class="blank">no GTD printed</span>'
        elif e.get("guarantee_scope") == "event_total":
            ratio = ('<span class="blank">event-total GTD</span><br><span class="small muted">'
                     + str(e.get("flights_in_event", 0)) + ' flights, not comparable per flight</span>')
        else:
            ratio = "%.1f×" % (gtd / e["buy_in"])
            if basis == "pool_plus_bounties":
                ratio += " <span class='tag warn'>incl. bounties</span>"
        se = "1" if e["entry_rule_status"] == "single_entry_confirmed" else "0"
        cells = [
            f'<td class="mono">{date}</td>',
            f'<td class="mono">{E(e["start"])}</td>',
            f'<td>#{E(e["event_no"])}</td>',
            f'<td>{E(e["name_printed"].split(" - ")[0])}<br><span class="small muted">{E(e["kind"].replace("_", " "))}</span></td>',
            f'<td class="num">{money(e["buy_in"])}</td>',
            f'<td class="num">{money(gtd)}</td>',
            f'<td class="num">{ratio}</td>',
            f'<td class="num">{e["chips"] or "—"}</td>',
            f'<td class="num">{e["level_min"]}</td>',
            f'<td class="mono">{v(e["late_reg_time"])}</td>',
            f'<td><span class="tag bad">not published</span></td>',
            f'<td>{src_links(e["sources"] if "sources" in e else ["V_CAL"])} · {src_link("V_CAL","calendar")}</td>',
        ]
        search = " ".join(str(x) for x in [date, e["start"], e["event_no"], e["name_printed"], e["buy_in"], gtd, e["sheet_title"]])
        rows.append(f'<tr data-date="{date}" data-single-entry="{se}" data-kind="{E(e["kind"])}" data-search="{E(search.lower())}">' + "".join(cells) + "</tr>")
    return rows


def page_tournaments():
    rows = tournament_rows()
    body = f"""
<div class="breadcrumb"><a href="index.html">Dashboard</a> / Tournaments</div>
<h1>Venetian tournament table — every dated row, every source</h1>
<p class="lede">All {len(EV['events'])} entry rows from the official DeepStack Extravaganza IV calendar (Nov 16 – Dec 23, 2026), with the buy-in and guarantee as printed, plus the fee, stack and late-registration facts read from that row's own structure sheet. The last column links the official calendar and the official structure sheet.</p>
<div class="callout bad"><strong>Read this before using the table.</strong> Not one of the 37 official 2026 structure sheets states whether a busted player may re-enter, and none lists an add-on. That silence is <em>not</em> a single-entry confirmation — this same room printed “Registration and Re-Entry is allowed” in its 2023 and 2024 sheets ({src_link('V_OLD_2023_1','2023 example')}, {src_link('V_OLD_2024_1','2024 example')}). Every Venetian row is therefore marked <span class="tag bad">not published</span> and <strong>zero rows pass the official single-entry filter</strong>.</div>
<div class="kpis">
<div class="kpi"><span>Dated entry rows</span><b>{EV['meta']['entry_rows']}</b><span>excludes Day-2 restarts and final tables</span></div>
<div class="kpi"><span>With a printed guarantee</span><b>{sum(1 for e in EV['events'] if (e['guarantee_printed'] or e['guarantee_on_sheet']))}</b><span>rest print none</span></div>
<div class="kpi"><span>Confirmed single-entry</span><b>0</b><span>of {EV['meta']['entry_rows']}</span></div>
<div class="kpi"><span>Earliest start</span><b>9:10 AM</b><span>#46, Dec 12 — a satellite, not a main event</span></div>
</div>
{controls(show_date=True, show_se=True)}
{table(["Date","#Start","#Ev","Event","#Buy-in","#GTD","#GTD÷buy-in","#Chips","#Level min","Late reg closes","Official entry rule","Sources"], rows,
       caption="Venetian DeepStack Extravaganza IV — official calendar + structure sheets. A multi-flight event prints ONE guarantee for the whole event, so its flights show ‘event-total GTD’ instead of a per-flight ratio.",
       table_id="tourn")}
<h2>Events the official pages do not give a guarantee for</h2>
<p>Three rows print no guaranteed prize pool anywhere on the official calendar or their structure sheet: {', '.join('#' + e['event_no'] + ' (' + e['date'] + ')' for e in EV['events'] if not (e['guarantee_printed'] or e['guarantee_on_sheet']))}. They are left blank rather than estimated.</p>
<h2>Day-2 restarts and final tables</h2>
<p>These are not new entries and cannot be bought into, so they are excluded from the table above. They matter for scheduling because a player who survives Day 1 must return.</p>
""" + table(["Date","#Start","#Ev","Event","Source"],
            [f'<tr data-date="{r["date"]}" data-search="{E((r["date"]+" "+r["event_no"]+" "+r["name_printed"]).lower())}">'
             f'<td class="mono">{r["date"]}</td><td class="mono">{E(r["start"])}</td><td>#{E(r["event_no"])}</td>'
             f'<td>{E(r["name_printed"])}</td><td>{src_link("V_CAL","calendar")} · {src_link("V_S%02d" % int(r["sheet_url"].split("_")[-1].replace(".pdf","")), "sheet")}</td></tr>'
             for r in EV["restarts"]], caption="Day 2 / final-table rows from the same official calendar", table_id="restarts")
    page("tournaments.html", "Tournaments", body, "tournaments.html")


def page_index():
    n_entries = EV["meta"]["entry_rows"]
    n_wpt = OTHER["wpt_meta"]["entry_rows"]
    singles = sum(1 for r in OTHER["wpt_events"] if r["entry_rule_status"] == "single_entry_per_flight_confirmed")
    body = f"""
<p class="eyebrow">Decision dashboard · official-source snapshot {RET}</p>
<h1>Strip poker, organised so you can decide.</h1>
<p class="lede">Upcoming Las Vegas Strip tournaments, what each one actually costs to enter, what the hotel really costs per night, and an honest list of what is still unconfirmed. Built from the operators' own pages and PDFs, checked line by line on {RET}. Nothing is filled in or inferred — blanks are blanks.</p>
<div class="pill-row"><a class="btn" href="tournaments.html">Browse {n_entries + n_wpt + 6} dated entries</a> <a class="btn ghost" href="calculator.html">Price a trip</a> <a class="btn ghost" href="flagged.html">What is unverified</a></div>

<div class="kpis">
<div class="kpi"><span>Venetian dated entries</span><b>{n_entries}</b><span>DSE IV, Nov 16 – Dec 23 2026</span></div>
<div class="kpi"><span>Wynn WPT dated entries</span><b>{n_wpt}</b><span>Nov 27 – Dec 21 2026</span></div>
<div class="kpi"><span>Confirmed 1-entry-per-flight</span><b>{singles}</b><span>WPT $10,400 Championship flights only</span></div>
<div class="kpi"><span>Venetian resort fee</span><b>$55</b><span>+ 13.38% tax, confirmed on the hotel's own terms</span></div>
</div>

<div class="callout bad"><strong>The single biggest finding: you cannot yet prove any Strip tournament is single-entry.</strong>
The Venetian's own 2026 structure sheets state a <em>late-registration</em> window and nothing else about entry. They do not say “one entry only”, and they do not say “re-entry allowed”. Prior Venetian sheets from 2023–2024 did print “Registration and Re-Entry is allowed”, which shows the silence is meaningful and not a formatting habit. The only official single-entry statement found anywhere on the Strip is the WPT's own release for the <strong>$10,400 WPT World Championship at Wynn</strong>: “a single entry per starting flight” — and with three flights that still allows three entries in total. <a href="flagged.html">See the full evidence trail →</a></div>

<h2>What the data actually supports</h2>
<div class="grid">
{"".join(dashboard_cards())}</div>

<h2>Hotel cost, honestly labelled</h2>
<div class="tablewrap"><table data-searchable="1"><caption>The only fee numbers confirmed on an operator's own page, plus the one published rate floor<span data-count style="float:right"></span></caption>
<thead><tr><th>Property</th><th class="num">Resort fee</th><th class="num">Room tax</th><th class="num">Published room floor</th><th class="num">Derived true cost / night</th><th>Status</th><th>Source</th></tr></thead><tbody>
<tr data-search="venetian"><td>The Venetian / Palazzo</td><td class="num">$55</td><td class="num">13.38%</td><td class="num">$119</td><td class="num">$197.28</td><td><span class="tag warn">derived, not a quote</span></td><td>{src_link('V_FEE')} · {src_link('V_RATES')}</td></tr>
<tr data-search="venetian"><td>The Venetian / Palazzo (upper “from”)</td><td class="num">$55</td><td class="num">13.38%</td><td class="num">$209</td><td class="num">$299.32</td><td><span class="tag warn">derived, not a quote</span></td><td>{src_link('V_RATES')}</td></tr>
<tr data-search="wynn"><td>Wynn / Encore</td><td class="num">$55</td><td class="num">13.38%*</td><td class="num"><span class="blank">UNVERIFIED</span></td><td class="num"><span class="blank">—</span></td><td><span class="tag bad">no dated rate read</span></td><td>{src_link('W_TC_FEE')}</td></tr>
<tr data-search="treasure island ti"><td>Treasure Island</td><td class="num">$49.95</td><td class="num">13.38%*</td><td class="num">$69 promo</td><td class="num">$78.23</td><td><span class="tag warn">promo headline</span></td><td>{src_link('I_FEE')}</td></tr>
<tr data-search="caesars palace"><td>Caesars Palace</td><td class="num"><span class="blank">UNVERIFIED</span></td><td class="num">13.38%*</td><td class="num">$139 promo</td><td class="num"><span class="blank">—</span></td><td><span class="tag bad">fee not on official page</span></td><td><a href="https://www.caesars.com/caesars-palace/hotel">caesars.com</a></td></tr>
<tr data-search="bellagio"><td>Bellagio</td><td class="num"><span class="blank">UNVERIFIED</span></td><td class="num">13.38%*</td><td class="num"><span class="blank">UNVERIFIED</span></td><td class="num"><span class="blank">—</span></td><td><span class="tag bad">MGM fee page 404</span></td><td>{src_link('M_FEES_UNVERIFIED')}</td></tr>
</tbody></table></div>
<p class="small muted">*13.38% is the Clark County rate as printed on The Venetian's hotel terms. Wynn, TI, Caesars and Bellagio did not print a tax percentage on the pages read, so using 13.38% for them is a derivation, not a quote.</p>

<h2>The question that decides everything</h2>
<ol class="tight">
<li><strong>Which exact dates are you travelling?</strong> Rates are date-specific. Without dates every hotel total is a "from" figure. The site therefore computes with your inputs rather than inventing a number.</li>
<li><strong>Is a single entry per flight acceptable, or must it be one entry for the whole event?</strong> This flips the entire ranking: if per-flight is acceptable, the WPT $10,400 is the only official single-entry-per-flight event found; if not, nothing on the Strip qualifies on current evidence.</li>
<li><strong>Will you call the poker room to get the entry rule in writing?</strong> That is the one action that converts the whole Venetian list from "unverified" to usable.</li>
</ol>
<p>Full decision list on <a href="questions.html">Questions</a>. Improvements ranked by impact on <a href="suggestions.html">Suggestions</a>.</p>

<h2>Go deeper</h2>
<div class="grid">
<article class="card"><h3><a href="tournaments.html">Tournaments</a></h3><p>{n_entries} Venetian entries with fee, stack, level length and late-reg clock time, each linked to its own structure sheet.</p></article>
<article class="card"><h3><a href="schedule.html">Day plans</a></h3><p>Which two events on the same day can actually both be played, and which are physically impossible.</p></article>
<article class="card"><h3><a href="hotels.html">Hotels & rates</a></h3><p>Resort fee, tax, parking, cancellation, the poker-rate play requirement, and walking time to each room.</p></article>
<article class="card"><h3><a href="venues.html">Venues</a></h3><p>One page per room: Venetian, Wynn, Caesars Palace, Bellagio — events plus the nearest hotels.</p></article>
<article class="card"><h3><a href="separate.html">Re-entry / add-on</a></h3><p>Every event where spending more buys more chips: re-entry, rebuys, add-ons, and Bellagio's gratuity chips.</p></article>
<article class="card"><h3><a href="flagged.html">Flagged for review</a></h3><p>{len(FLAG['items'])} specific unresolved items with the source that should settle each one.</p></article>
</div>
"""
    page("index.html", "Dashboard", body, "index.html")


def page_schedule():
    days = {}
    for e in EV["events"]:
        days.setdefault(e["date"], []).append(e)
    restart_days = {}
    for r in EV["restarts"]:
        restart_days.setdefault(r["date"], []).append(r)

    plan_rows, overlap_rows = [], []
    for d in sorted(days):
        evs = sorted(days[d], key=lambda x: datetime.strptime(x["start"], "%I:%M %p"))
        mains = [e for e in evs if e["kind"] not in ("satellite",)]
        sats = [e for e in evs if e["kind"] == "satellite"]
        primary = mains[0] if mains else (evs[0] if evs else None)
        fallback = None
        if primary and len(mains) > 1:
            cand = mains[1]
            if cand["event_no"] == primary["event_no"]:
                cand2 = next((m for m in mains[1:] if m["event_no"] != primary["event_no"]), None)
                mains = [primary] + ([cand2] if cand2 else [])
            gap = (datetime.strptime(cand["start"], "%I:%M %p") - datetime.strptime(primary["start"], "%I:%M %p")).seconds / 3600
            fallback = (cand, gap)
        if primary:
            pf = ""
            if fallback:
                ok = fallback[1] >= (primary["plausible_min_hours"] or 99)
                pf = (f'<span class="tag {"ok" if ok else "bad"}">{"possible" if ok else "conditional"}</span> '
                      f'#{fallback[0]["event_no"]} {fallback[0]["start"]} — {fallback[1]:g}h after the start, '
                      f'primary needs ≈{primary["plausible_min_hours"]}h+')
            plan_rows.append(
                f'<tr data-date="{d}" data-search="{E((d + " " + primary["name_printed"]).lower())}">'
                f'<td class="mono">{d}</td>'
                f'<td><strong>#{primary["event_no"]}</strong> {E(primary["name_printed"].split(" - ")[0])}<br><span class="small muted">{primary["start"]} · {money(primary["buy_in"])} · {primary["chips"]} chips · {primary["level_min"]} min levels</span></td>'
                f'<td>{"—" if not fallback else pf}</td>'
                f'<td class="small">{("Satellites: " + ", ".join(s["start"] + " #" + s["event_no"] for s in sats)) if sats else "—"}</td>'
                f'<td>{"Yes — Day 2/final table" if d in restart_days else "No"}</td>'
                f'<td>{src_link("V_CAL","calendar")} · {src_link("V_S%02d" % int(primary["sheet_url"].split("_")[-1].replace(".pdf","")), "sheet")}</td></tr>')
        for i in range(len(evs) - 1):
            a, b = evs[i], evs[i + 1]
            if a["event_no"] == b["event_no"]:
                continue  # same event number = two flights of one tournament, not two tournaments
            gap = (datetime.strptime(b["start"], "%I:%M %p") - datetime.strptime(a["start"], "%I:%M %p")).seconds / 3600
            need = a["plausible_min_hours"]
            ok = need is not None and gap >= need
            overlap_rows.append(
                f'<tr data-date="{d}" data-search="{E((d + " " + a["name_printed"] + " " + b["name_printed"]).lower())}">'
                f'<td class="mono">{d}</td><td>#{a["event_no"]} {a["start"]}</td><td>#{b["event_no"]} {b["start"]}</td>'
                f'<td class="num">{gap:g}h</td><td class="num">{need if need is not None else "—"}h</td>'
                f'<td><span class="tag {"ok" if ok else "bad"}">{"plausible" if ok else "not plausible"}</span></td>'
                f'<td>{src_link("V_CAL", "calendar")} · {src_link("V_S%02d" % int(a["sheet_url"].split("_")[-1].replace(".pdf","")), "sheet A")} · {src_link("V_S%02d" % int(b["sheet_url"].split("_")[-1].replace(".pdf","")), "sheet B")}</td></tr>')

    body = f"""
<div class="breadcrumb"><a href="index.html">Dashboard</a> / Day plans</div>
<h1>Can you play “all day”? Here is the honest answer.</h1>
<p class="lede">The user asked for a schedule that starts at 08:00 and runs all day. No official Strip schedule in this dataset starts at 08:00. The earliest verified start is <strong>9:10 AM</strong> (Venetian satellite #46, Dec 12), and the earliest main-event start is <strong>10:10 AM</strong>. This page instead gives each day one <strong>primary</strong> event and, where a second event exists, a <strong>conditional fallback</strong> — never an impossible sequence.</p>
<div class="callout warn"><strong>Why “fallback” and not “both”.</strong> A poker tournament has no published finish time. The estimator below uses the event's own structure: the time until registration closes, doubled, plus one hour of breaks — a conservative proxy for reaching the money. Two events only count as playable in sequence if the gap between their start times exceeds that estimate. This is a planning heuristic derived from the official structure, <em>not</em> a published finish time, and it is labelled as such everywhere.</div>
<h2>One primary event per day</h2>
{controls(show_date=True, show_se=False, show_kind=False)}
{table(["Date","Primary event","Conditional fallback","Also on that day","Return needed","Source"], plan_rows, caption="Primary + fallback plan, derived from official start times and structure sheets", table_id="plan")}
<h2>Every same-day pair, scored</h2>
{table(["Date","First","Second","#Gap","#First needs ≈","Verdict","Source"], overlap_rows, caption="All {n} same-day pairs in the Venetian series".replace("{n}", str(len(overlap_rows))), table_id="overlaps")}
<h2>What makes a “play all day” trip possible</h2>
<ol class="tight">
<li><strong>Morning slot.</strong> Venetian 10:10 AM main events exist on Nov 19–21 (RaceDay), Dec 2 and Dec 8 (Seniors, 50+ only), Dec 9 (#35 tag team, women/women or women/men teams), Dec 10 (LIPS Ladies — women only), Dec 13/14 (Seniors), Dec 17–19 (#56 Day 1 flights) and Dec 12 (#47 10:10 AM). For a male player under 50 the practical morning starts are Nov 19–21, Dec 9's tag team (needs a female teammate), and the Dec 17–19 $1,100 flights.</li>
<li><strong>Evening slot.</strong> The 5:10 PM events are one-day bounty tournaments with a 9:40 PM late-registration cut-off. A 10:10 AM start plus a plausible finish makes the 5:10 PM event a real fallback only if you bust early — which is exactly what the conditional label means.</li>
<li><strong>Return days.</strong> {len(EV['restarts'])} calendar rows are Day-2 restarts or final tables. If you survive, you must be back in the room; a trip cannot be planned as one event per calendar day without accounting for those.</li>
</ol>
<h2>Wynn alternative</h2>
<p>Wynn runs dailies at 12:00 PM and 6:00 PM with late registration to about 4:30 PM ({src_link('W_DAILY','Wynn daily terms')}). During the WPT World Championship (Nov 27 – Dec 21) the dailies are suspended ({src_link('W_POKER','Wynn poker page')}), so a Wynn “all day” only works inside that window via the WPT schedule itself — <a href="separate.html">see the WPT row list</a>.</p>
"""
    page("schedule.html", "Day plans", body, "schedule.html")


def page_hotels():
    rows = []
    for h in HOT["hotels"]:
        best = None
        for w in h["walk_to_venues"]:
            if w["status"] != "same_property" and w.get("minutes") is not None:
                if best is None or w["minutes"] < best["minutes"]:
                    best = w
        walkcell = (("%.1f min to %s (%s m)" % (best["minutes"], E(best["venue"]), format(best["osrm_m"], ","))) if best else "same property")
        fee = h.get("resort_fee_usd")
        cost = next((r for r in h["rate_log"] if r.get("derived_true_cost_per_night")), None)
        feetxt = ("$%.2f" % fee) if fee is not None else UNV
        taxtxt = ("%.2f%%" % (h["room_tax_rate"] * 100)) if h.get("room_tax_rate") else ("%.2f%%" % (HOT["meta"]["default_tax_rate"] * 100) + DAGGER)
        anyrate = next((r for r in h["rate_log"] if r.get("room_rate_usd")), None)
        ratetxt = ("$" + format(anyrate["room_rate_usd"], ",.0f")) if anyrate else UNV
        costtxt = ("$" + format(cost["derived_true_cost_per_night"], ",.2f")) if cost and cost.get("derived_true_cost_per_night") else UNV
        label = E(cost["label"]) if cost else E(anyrate["label"] if anyrate else "—")
        src = src_link(h["resort_fee_source"], "fee") if h.get("resort_fee_source") else src_link(h.get("official_site", ""), "hotel site")
        key = E((h["name"] + " " + feetxt + " " + costtxt).lower())
        rows.append(
            '<tr data-search="%s"><td><strong>%s</strong><br><span class="small muted">%s</span></td>'
            '<td class="num">%s</td><td class="num">%s</td><td class="num">%s</td><td class="num">%s</td>'
            '<td class="small">%s</td><td class="small">%s</td><td>%s</td></tr>'
            % (key, E(h["name"]), E(h.get("towers", "")), feetxt, taxtxt, ratetxt, costtxt, label, walkcell, src))

    walkrows = []
    for h in HOT["hotels"]:
        for w in h["walk_to_venues"]:
            if w["status"] == "same_property":
                walkrows.append(
                    '<tr data-walk30="1" data-search="%s"><td>%s</td><td>%s</td>'
                    '<td class="num">—</td><td class="num">0 m</td>'
                    '<td><span class="tag ok">inside the resort</span></td>'
                    '<td class="small mono">same property</td><td>%s</td></tr>'
                    % (E((h["name"] + " " + w["venue"]).lower()), E(h["name"]), E(w["venue"]),
                       src_link("MAP_OSRM", "routing")))
                continue
            ok = w["minutes"] <= 30
            asy = w["reciprocal_difference_pct"]
            astag = ('<span class="tag warn">asymmetric %d%%</span>' % asy) if asy > 20 else ""
            route = "route %s to %s, %s m; reverse %s m" % (
                w["origin_node"], w["venue_node"], format(w["osrm_m"], ","), format(w["osrm_m_reverse"], ","))
            walkrows.append(
                '<tr data-walk30="%d" data-search="%s"><td>%s</td><td>%s</td>'
                '<td class="num">%.1f min</td><td class="num">%s m</td>'
                '<td><span class="tag %s">%s</span> %s</td>'
                '<td class="small mono">%s</td><td>%s</td></tr>'
                % (1 if ok else 0, E((h["name"] + " " + w["venue"]).lower()), E(h["name"]), E(w["venue"]),
                   w["minutes"], format(w["osrm_m"], ","), "ok" if ok else "bad",
                   "\u226430 min" if ok else "over 30", astag, E(route),
                   src_link("MAP_OSRM", "routing")))

    fees = []
    for h in HOT["hotels"]:
        for r in h["rate_log"]:
            rr = ("$%.2f" % r["room_rate_usd"]) if r.get("room_rate_usd") else UNV
            rf = ("$%.2f" % r["resort_fee_usd"]) if r.get("resort_fee_usd") is not None else UNV
            tx = ("%.4f" % (1 + r["tax_rate"])) if r.get("tax_rate") else NA_
            ct = ("$%.2f" % r["checkout_total_usd"]) if r.get("checkout_total_usd") else '<span class="blank">not read</span>'
            dv = ("$%.2f" % r["derived_true_cost_per_night"]) if r.get("derived_true_cost_per_night") else NOFEE
            sk = src_link(r["page"], "src") if r.get("page") else src_link(h.get("official_site", ""), "hotel site")
            fees.append(
                '<tr data-search="%s"><td class="mono">%s</td><td>%s</td>'
                '<td>%s → %s</td><td class="num">%s</td>'
                '<td class="num">%s</td><td class="num">%s</td><td class="num">%s</td>'
                '<td class="num">%s</td><td class="num">%s</td>'
                '<td class="small">%s</td><td class="small mono">%s</td><td>%s</td></tr>'
                % (E((h["name"] + " " + r["label"]).lower()), r["observed"], E(h["name"]),
                   E(str(r.get("checkin") or NA_)), E(str(r.get("checkout") or NA_)), str(r.get("nights") or NA_),
                   rr, rf, tx, ct, dv, E(r["label"]), E(r.get("derived_formula") or NA_), sk))

    body = f"""
<div class="breadcrumb"><a href="index.html">Dashboard</a> / Hotels &amp; rates</div>
<h1>Hotels: fee by fee, with the rate kept as a dated log</h1>
<p class="lede">There is no single “price per night” on this site. Each observation records what was seen, on which date, on which official page, and whether it is a bookable quote or merely a published floor. The true nightly cost is computed the same way for everyone: <span class="mono">(room rate + resort fee) × (1 + 13.38%)</span>, plus parking when you drive.</p>
<div class="callout bad"><strong>What could not be confirmed.</strong> Only two resort fees could be read on an operator's own page — The Venetian ($55), Wynn ($55) and Treasure Island ($49.95). No dated Wynn, Caesars or Bellagio room rate was readable, and Caesars Palace and Bellagio printed no fee at all: MGM's resort-fee and reservation pages both returned 404, and Caesars' property, hotel and policy pages printed none. Third-party figures exist for all of them and are <em>deliberately not shown</em>; they are listed as leads on <a href="flagged.html">Flagged for review</a>.</div>
<h2>Fee and derived-cost summary</h2>
{controls(show_date=False, show_se=False, show_walk=False)}
{table(["Property","#Resort fee","#Room tax","#Published room floor","#Derived true cost / night","What that number is","Nearest poker room by foot","Source"], rows,
       caption="Only values read on an official page, or derived from one. {DAGGER} = the Clark County 13.38% rate printed by The Venetian, applied here as a labelled assumption because this hotel does not print its own rate.", table_id="hotelfees")}
<h2>Terms that change the total</h2>
<ul class="tight">
<li><strong>The Venetian poker rate is conditional.</strong> $119/$209 are “from” figures for players who book by phone with code EPOKR25 and then play <em>6 hours of live cash per night, or buy into a $300+ tournament</em>; miss it and the room reverts to the prevailing rate ({src_link('V_RATES','suite-rates page')}). Add a $150/night incidental hold and an 11:00 a.m. checkout ({src_link('V_TERMS','hotel terms')}).</li>
<li><strong>Parking.</strong> Venetian hotel guests pay $20/day self-park, but 3+ hours of poker play earns complimentary self-parking ({src_link('V_PARK','parking page')}). Wynn and Treasure Island include self-parking. Caesars and Bellagio parking were not read, so they are blank.</li>
<li><strong>Cancellation.</strong> Caesars advertises free 48-hour cancellation; Wynn's offer pages vary between a 48-hour deadline and fully non-refundable prepaid; the Venetian poker rate's deadline is not printed. Recorded per property in the rate log.</li>
</ul>
<h2>Rate log — every observation, dated</h2>
{table(["Observed","Hotel","Dates","#Nights","#Room","#Resort fee","#Tax multiplier","#Checkout total","#Derived / night","What it is","Formula","Source"], fees,
       caption="A dated log, not a single value. ‘Not read’ means the page would not render an amount to this session.", table_id="ratelog")}
<h2>Walking distance to each poker room</h2>
<p>One labelled OSRM distance matrix on OpenStreetMap data, converted with a single formula: <span class="mono">minutes = metres ÷ 4.8 km/h × 60 × 1.25</span>. The 25% allowance covers the Las Vegas Blvd crossings, pedestrian bridges, elevators and casino corridors — none of which the router models. Each row also shows the <em>reverse</em> route; where the two directions differ by more than 20% the row carries an <strong>asymmetric</strong> tag, because a large gap can be a real one-way pedestrian funnel or a geocoder snapping artefact, and quietly picking one number would hide it.</p>
<div class="callout warn"><strong>The 30-minute rule does bite — just not where you would guess.</strong> Six pairs exceed it: Wynn↔Caesars (42.4 min / 42.9 min), Wynn↔Bellagio (39.4 / 43.6), Treasure Island↔Bellagio (33.5) and Harrah's↔Bellagio (34.9). Every hotel is still within 30 minutes of <em>at least one</em> poker room, so no property is disqualified outright — but a Wynn guest cannot credibly walk to Bellagio between events.</div>
<p>Even the qualifying numbers are optimistic: they measure centroid to centroid and ignore the walk from your tower to the lobby, and the fact that the Venetian's poker room is on level 2 of the Grand Canal Shoppes while Wynn's is across in Encore.</p>
{controls(show_date=False, show_se=False, show_walk=True)}
{table(["Hotel","Venue","#Walk time","#Distance","30-min rule","Route method","Source"], walkrows, caption="Hotel → poker-room walking estimates", table_id="walks")}
<h2>Turn any row into a whole-trip number</h2>
<p>The <a href="calculator.html">trip calculator</a> applies exactly this page's formula and shows the arithmetic line by line: entries × buy-in, plus nights × true cost, plus parking.</p>
"""
    page("hotels.html", "Hotels & rates", body, "hotels.html")


def page_calculator():
    body = f"""
<div class="breadcrumb"><a href="index.html">Dashboard</a> / Trip calculator</div>
<h1>Trip calculator: entries × buy-ins + nights × true hotel cost</h1>
<p class="lede">All four numbers you need are either confirmed on an official page or printed in the table below. Nothing is pre-filled with an estimate — if a fee is unknown, type nothing and the calculator tells you the total is incomplete rather than inventing one.</p>
<h2>Run the numbers</h2>
<div class="controls">
<label>Entries planned<input type="number" id="c_entries" value="4" min="0" step="1"></label>
<label>Average buy-in ($)<input type="number" id="c_buyin" value="300" min="0" step="25"></label>
<label>Nights<input type="number" id="c_nights" value="5" min="0" step="1"></label>
<label>Room rate / night ($)<input type="number" id="c_rate" value="119" min="0" step="1"></label>
<label>Resort fee / night ($)<input type="number" id="c_fee" value="55" min="0" step="0.01"></label>
<label>Room tax (%)<input type="number" id="c_tax" value="13.38" min="0" step="0.01"></label>
<label>Parking / night ($)<input type="number" id="c_parking" value="0" min="0" step="1"></label>
</div>
<div class="calc-out" id="calcOut">—</div>
<p class="small muted">The default room rate ($119) and fee ($55) are The Venetian's published poker-rate floor and confirmed resort fee. The default is <em>not</em> a quote for your dates; it is the lowest figure the hotel itself publishes. Replace it with the amount your booking page shows for your dates.</p>
<h2>Buy-in shortcuts</h2>
<div class="tablewrap"><table data-searchable="1"><caption>Every confirmed total entry cost by venue, so the calculator can be filled without guessing<span data-count style="float:right"></span></caption>
<thead><tr><th>Venue</th><th>Event as printed</th><th class="num">Total entry</th><th class="num">House fee</th><th class="num">Fee %</th><th class="num">To prize pool</th><th class="num">Rows</th><th>Source</th></tr></thead><tbody>
{"".join(buyin_rows())}
<tr data-search="wynn"><td>Wynn</td><td>Daily Mon–Thu $200</td><td class="num">$200</td><td class="num">$38</td><td class="num">19.0%</td><td class="num">$162</td><td>{src_link('W_DAILY')}</td></tr>
<tr data-search="wynn"><td>Wynn</td><td>Friday rebuy $240</td><td class="num">$240</td><td class="num">$50</td><td class="num">20.8%</td><td class="num">$190</td><td>{src_link('W_DAILY')}</td></tr>
<tr data-search="wynn"><td>Wynn</td><td>WPT &amp; all series events</td><td class="num"><span class="blank">UNVERIFIED</span></td><td class="num"><span class="blank">—</span></td><td class="num"><span class="blank">—</span></td><td class="num"><span class="blank">—</span></td><td>{src_link('W_WPT')} (fee deferred to structure sheets)</td></tr>
<tr data-search="bellagio"><td>Bellagio</td><td>Friday $600</td><td class="num">$600 (+$40 gratuity)</td><td class="num">$50</td><td class="num">8.3%</td><td class="num">$510</td><td>{src_link('B_FRI')}</td></tr>
<tr data-search="caesars"><td>Caesars</td><td>Daily $100 / $160</td><td class="num">$100 / $160 (+$50 add-on)</td><td class="num">$30 / $45</td><td class="num">30.0% / 28.1%</td><td class="num">$70 / $115</td><td>{src_link('C_FLYER')}</td></tr>
<tr data-search="treasure island"><td>Treasure Island</td><td>No tournament confirmed</td><td class="num">—</td><td class="num">—</td><td class="num">—</td><td class="num">—</td><td>{src_link('I_FEE')}</td></tr>
</tbody></table></div>
<h2>Worked example, with every term visible</h2>
<div class="card">
<p><strong>Plan:</strong> 4 Venetian entries at $300, 5 nights at The Venetian's published poker-rate floor.</p>
<p class="mono">Entries&nbsp;&nbsp; 4 × $300 = $1,200<br>
True night ($119 + $55) × 1.1338 = $197.28<br>
Hotel&nbsp;&nbsp;&nbsp;&nbsp; 5 × $197.28 = $986.42<br>
Parking&nbsp;&nbsp; waived if you play 3+ hours per day (else 5 × $20 = $100)<br>
<strong>Total&nbsp;&nbsp;&nbsp; $2,186.42</strong> before food, travel and the incidental hold.</p>
<p class="small muted">The play requirement matters twice here: the poker rate itself needs 6 hours of cash play or a $300+ buy-in per night, and free parking needs 3 hours of play. Four $300 tournaments over five nights satisfies both on paper — but the rate reverts to the prevailing rate for any night you miss.</p>
</div>
<h2>What the calculator still cannot tell you</h2>
<ul class="tight">
<li>Whether your chosen event actually allows the number of entries you typed. For the Venetian, that is unresolved (see <a href="flagged.html">Flagged</a>).</li>
<li>Your real room rate, until you open the booking page for your exact dates and read the checkout total.</li>
<li>Food, travel to Las Vegas, tips, and the $150/night incidental hold.</li>
</ul>
"""
    page("calculator.html", "Trip calculator", body, "calculator.html")


def page_venues():
    venues = {
        "Venetian": {
            "full": "The Venetian Resort Las Vegas — Poker Room, The Palazzo level 2, Grand Canal Shoppes",
            "hours": "Open 24 hours (V_POKER)",
            "srcs": ["V_POKER", "V_CAL", "V_RATES", "V_FEE"],
            "hotels": ["venetian", "wynn", "harrahs", "treasure_island", "caesars_palace", "bellagio"],
            "note": "Location and level are confirmed on the official poker page. Table count and square footage were not read from an official source in this session, so they are not stated.",
        },
        "Wynn": {
            "full": "Wynn Las Vegas — Poker Room, located in Encore",
            "hours": "Not read on the official page for this snapshot",
            "srcs": ["W_POKER", "W_WPT", "W_DAILY", "W_TC_FEE"],
            "hotels": ["wynn", "treasure_island", "venetian"],
            "note": "Dailies at 12:00 PM and 6:00 PM, suspended during series; WPT World Championship Nov 27 – Dec 21 2026.",
        },
        "Caesars Palace": {
            "full": "Caesars Palace — Poker Room",
            "hours": "Not read for this snapshot",
            "srcs": ["C_FLYER"],
            "hotels": ["caesars_palace", "bellagio", "venetian"],
            "note": "Daily $100/$160 tournaments at 10 AM, 2 PM, 6 PM, 9 PM — all with re-entry and a $50 add-on.",
        },
        "Bellagio": {
            "full": "Bellagio — Poker Room, north side of the casino next to the sportsbook",
            "hours": "Not read for this snapshot",
            "srcs": ["B_POKER", "B_FRI", "B_SAT"],
            "hotels": ["bellagio", "caesars_palace", "venetian"],
            "note": "Weekly $600 Friday, $1,100 Saturday (contradictory sheet), $400 H.O.R.S.E Sunday.",
        },
    }
    cards = []
    for name, info in venues.items():
        evs = [e for e in EV["events"] if e["venue"] == name]
        wpt = [e for e in OTHER["wpt_events"] if e["venue"] == name]
        hand = [e for e in OTHER["events"] if e["venue"] == name]
        adv = [e for e in OTHER["advantage_by_spending"] if e["venue"] == name]
        rows = []
        for e in evs:
            rows.append(f'<tr data-date="{e["date"]}" data-search="{E((e["date"]+e["name_printed"]).lower())}"><td class="mono">{e["date"]}</td><td class="mono">{E(e["start"])}</td><td>#{E(e["event_no"])}</td><td>{E(e["name_printed"].split(" - ")[0])}</td><td class="num">{money(e["buy_in"])}</td><td class="num">{money(e["guarantee_printed"] or e["guarantee_on_sheet"])}</td><td>{src_link("V_CAL", "calendar")}</td></tr>')
        for e in wpt:
            if e["kind"] in ("restart", "final_table"):
                continue
            rows.append(f'<tr data-date="{e["date"]}" data-search="{E((e["date"]+e["name"]).lower())}"><td class="mono">{e["date"]}</td><td class="mono">{E(e["start"])}</td><td>{E(e["kind"][:4])}</td><td>{E(e["name"])}</td><td class="num">{money(e["buy_in"])}</td><td class="num">{money(e.get("guarantee"))}</td><td>{src_link("W_WPT", "poster")}</td></tr>')
        for e in hand:
            rows.append(f'<tr data-search="{E((e["name"]).lower())}"><td class="mono">{E(e["date"])}</td><td class="mono">{E(e["start"])}</td><td>rec.</td><td>{E(e["name"])}<br><span class="small muted">{E(e.get("reentry") or "")}</span></td><td class="num">{money(e["buy_in"])}</td><td class="num">{money(e.get("guarantee"))}</td><td>{src_links(e["sources"])}</td></tr>')
        for e in adv:
            rows.append(f'<tr data-search="{E((e["name"]).lower())}"><td class="mono">{E(e["date"])}</td><td class="mono">{E(e["times"][0])}</td><td class="tag sep">add-on</td><td>{E(e["name"])}</td><td class="num">{money(e["buy_in"])}</td><td class="num">{money(e.get("guarantee"))}</td><td>{src_links(e["sources"])}</td></tr>')
        hrows = []
        for hid in info["hotels"]:
            h = next(x for x in HOT["hotels"] if x["id"] == hid)
            w = next((x for x in h["walk_to_venues"] if x["venue"] == name), None)
            wmin = w["minutes"] if w and w.get("minutes") is not None else None
            fee = h.get("resort_fee_usd")
            cost = next((r["derived_true_cost_per_night"] for r in h["rate_log"] if r.get("derived_true_cost_per_night")), None)
            wtxt = ("inside the resort" if (w and w["status"] == "same_property")
                    else ("%.1f min" % wmin if wmin is not None else "no route read"))
            feetxt = ("$%.2f" % fee) if fee is not None else UNV
            costtxt = ("$%.2f" % cost) if cost else UNV
            hsrc = src_link(h["resort_fee_source"], "fee") if h.get("resort_fee_source") else src_link(h.get("official_site", ""), "hotel site")
            hrows.append(
                '<tr data-walk30="%d" data-search="%s"><td>%s</td><td class="num">%s</td>'
                '<td class="num">%s</td><td class="num">%s</td><td>%s</td></tr>'
                % (1 if (wmin is not None and wmin <= 30) else 0, E(h["name"].lower()),
                   E(h["name"]), wtxt, feetxt, costtxt, hsrc))
        cards.append(f"""
<section class="card" id="{name.lower().replace(' ','-')}">
<h2>{E(name)}</h2>
<p class="lede">{E(info["full"])}<br><span class="small muted">Hours: {E(info["hours"])} · {E(info["note"])}</span></p>
<p class="pill-row">{" ".join(src_link(s) for s in info["srcs"])}</p>
<h3>Events ({len([r for r in rows])} rows)</h3>
{table(["Date","Start","Ev","Name","#Buy-in","#GTD","Source"], rows, caption="Official rows for this venue", table_id="v-"+name.lower().replace(" ","-"))}
<h3>Nearest hotels, ranked by walk time</h3>
{table(["Hotel","#Walk","#Resort fee","#Derived true cost/night","Source"], hrows, caption="Walking minutes from the hotel centroid to this poker room", table_id="h-"+name.lower().replace(" ","-"))}
</section>""")
    body = f"""
<div class="breadcrumb"><a href="index.html">Dashboard</a> / Venues</div>
<h1>One page per room</h1>
<p class="lede">Each venue gets its own events and its own nearest beds. Rows marked <span class="tag sep">add-on</span> belong to the <a href="separate.html">separate section</a> because spending more buys more chips.</p>
{controls(show_date=True, show_se=False, show_walk=False, show_kind=True)}
{"".join(cards)}
"""
    page("venues.html", "Venues", body, "venues.html")


def page_separate():
    adv = OTHER["advantage_by_spending"]
    adv_rows = []
    for e in adv:
        adv_rows.append(
            '<tr data-search="%s"><td>%s</td><td>%s</td><td class="num">%s</td><td class="num">%s</td>'
            '<td>%s</td><td>%s</td><td class="small">%s</td><td>%s</td></tr>'
            % (E((e["venue"] + " " + e["name"]).lower()), E(e["venue"]), E(e["name"]),
               money(e["buy_in"]), money(e.get("guarantee")),
               E(e.get("reentry") or NA_), E(e.get("addon") or "None published"),
               E(e["why"]), src_links(e["sources"])))

    re_rows = []
    for e in OTHER["events"] + OTHER["wpt_events"]:
        if e.get("entry_rule_status") in ("reentry_allowed_published", "addon_or_rebuy_published", "single_entry_per_flight_confirmed"):
            dv = str(e.get("date") or "")
            datattr = dv if re.match(r"^\d{4}-", dv) else ""
            tagcls = "ok" if e["entry_rule_status"] == "single_entry_per_flight_confirmed" else "warn"
            re_rows.append(
                '<tr data-date="%s" data-search="%s"><td>%s</td><td class="mono">%s</td><td>%s</td>'
                '<td class="num">%s</td><td><span class="tag %s">%s</span></td>'
                '<td class="small">%s</td><td class="small">%s</td><td>%s</td></tr>'
                % (datattr, E((e["venue"] + " " + e["name"]).lower()), E(e["venue"]), E(dv), E(e.get("name", "")),
                   money(e.get("buy_in")), tagcls, E(e["entry_rule_status"].replace("_", " ")),
                   E(e.get("reentry") or NA_), E(e.get("addon") or "None published"), src_links(e["sources"])))

    body = f"""
<div class="breadcrumb"><a href="index.html">Dashboard</a> / Re-entry &amp; add-on</div>
<h1>Every event where money buys chips — kept separate, on purpose</h1>
<p class="lede">The brief was single-entry only, with anything that lets a player gain an advantage by spending more held in a separate section. This page is that section. These events are not “bad” — they are simply a different game from a freezeout, and mixing them into a single-entry ranking would make the ranking meaningless.</p>
<div class="callout warn"><strong>The distinction that matters.</strong> “No re-entry” is not the same as “no spending advantage”. Wynn's Friday $240 explicitly bars re-entry yet still offers unlimited $200 rebuys and a $100 add-on. Bellagio's Friday $600 allows re-entry and sells a $40 “voluntary staff gratuity” that adds 15,000 chips. Both belong here; neither belongs in the single-entry list.</div>
<h2>Advantage-by-spending catalogue</h2>
{controls(show_date=False, show_se=False)}
{table(["Venue","Event","#Buy-in","#GTD","Re-entry","Add-on / rebuy","Why it is here","Source"], adv_rows, caption="Events where paying more can increase your chips or attempts", table_id="adv")}
<h2>Every published entry rule found on the Strip</h2>
<p>This is the complete set of official statements on entry that this session could read. Everything not on this list has no published rule — which is different from having a single-entry rule.</p>
{table(["Venue","Date","Event","#Buy-in","Official rule status","What the official page says","Add-on","Source"], re_rows, caption="Only rows with a quoted official rule appear here", table_id="rules")}
<h2>The one single-entry-per-flight event on the Strip</h2>
<div class="card"><span class="tag ok">published</span>
<h3>WPT World Championship — $10,400, Dec 13 / 14 / 15 flights</h3>
<p>The organiser's own release says players are allowed <strong>“a single entry per starting flight”</strong>, with the last chance to enter before the start of Day 2 ({src_link('W_WPT_PR','WPT release')}). There are three starting flights, so a determined player can still enter three times across the event. It is the closest thing to a guaranteed freezeout this dataset contains — and it is a $10,400 decision, not a $300 one.</p>
<p>Contrast: the $400 Super Gold Million in the same festival is explicitly <strong>“unlimited re-entry”</strong>. Same room, same month, opposite rule — which is why each event has to be checked on its own sheet.</p></div>
<h2>How the filter behaves on the tournaments table</h2>
<p>The <a href="tournaments.html">tournaments page</a> has a checkbox labelled <em>official single-entry rule only</em>. Today it returns <strong>zero Venetian rows</strong>, because no Venetian 2026 sheet states a rule. That is the honest output, not a bug. Once a poker room confirms a rule in writing, adding it to <code>data/v2/events.json</code> and rebuilding flips that row into the filter.</p>
"""
    page("separate.html", "Re-entry & add-on", body, "separate.html")


def page_flagged():
    cats = {}
    for item in FLAG["items"]:
        cats.setdefault(item["category"], []).append(item)
    blocks = []
    for cat in sorted(cats):
        rows = []
        for it in cats[cat]:
            srcs = " ".join(src_link(s) for s in it.get("sources", []))
            rows.append(
                f'<tr data-search="{E((it["id"] + " " + it["title"] + " " + it["detail"]).lower())}">'
                f'<td class="mono">{E(it["id"])}</td><td><strong>{E(it["title"])}</strong><br><span class="small muted">{E(it["detail"])}</span></td>'
                f'<td><span class="tag {"bad" if it["severity"]=="blocking" else "warn"}">{E(it["severity"])}</span></td>'
                f'<td class="small">{E(it["how_to_settle"])}</td><td>{srcs}{(" " + src_link(it["repo_link"], "repo file")) if it.get("repo_link") else ""}</td></tr>')
        blocks.append(f"<h2>{E(cat)}</h2>" + table(["#ID","Item","#Severity","How to settle it","Source"], rows, caption=f"{len(rows)} items in {E(cat)}", table_id="f-" + re.sub(r'[^a-z]', '', cat.lower())))
    body = f"""
<div class="breadcrumb"><a href="index.html">Dashboard</a> / Flagged for review</div>
<h1>Flagged for review — {len(FLAG['items'])} items</h1>
<p class="lede">These are the things this session could not confirm, could not find, or found to contradict each other. They do not block publication, and they are the most useful part of the site: each one names the exact step that would settle it.</p>
<div class="callout"><strong>Severity key.</strong> <span class="tag bad">blocking</span> = a decision the user asked for cannot be made correctly until this is resolved. <span class="tag warn">material</span> = it changes a cost or a ranking but a reasonable estimate exists. Everything here has a source link so you can check it yourself in a browser.</div>
{controls(show_date=False, show_se=False)}
{''.join(blocks)}
<h2>What was deliberately left blank rather than estimated</h2>
<ul class="tight">
<li>Every Venetian entry rule (83 rows).</li>
<li>Every WPT festival fee (134 rows) — the poster defers them to structure sheets.</li>
<li>Caesars Palace, Bellagio and Harrah's resort fees — no official page printed them.</li>
<li>All date-specific hotel quotes — no booking calendar rendered an amount to this session.</li>
</ul>
"""
    page("flagged.html", "Flagged for review", body, "flagged.html")


def page_questions():
    groups = {}
    for q in QUEST["questions"]:
        groups.setdefault(q["group"], []).append(q)
    blocks = []
    for g in QUEST["group_order"]:
        items = groups.get(g, [])
        cards = []
        for q in items:
            ans = q.get("answer") or '<span class="blank">Not answerable from current data.</span>'
            cards.append(f"""<details><summary>{E(q['q'])} <span class="tag {'ok' if q.get('answer') and q['status']=='answered' else 'warn'}">{E(q['status'])}</span></summary>
<p><strong>Answer from this dataset:</strong> {ans}</p>
<p><strong>Why it matters:</strong> {E(q['why'])}</p>
<p><strong>What would settle it:</strong> {E(q['settle'])}</p>
<p class="small muted">Sources: {" ".join(src_link(s) for s in q.get('sources', [])) or "none — this is a question, not a claim"}</p></details>""")
        blocks.append(f'<h2>{E(g)}</h2>' + "".join(cards))
    n_ans = sum(1 for q in QUEST["questions"] if q["status"] == "answered")
    body = f"""
<div class="breadcrumb"><a href="index.html">Dashboard</a> / Questions</div>
<h1>Questions that must be answered before a decision</h1>
<p class="lede">Every question is split three ways: the best answer the current official data supports, why the answer matters to a booking, and the specific action that would settle it. {n_ans} of {len(QUEST['questions'])} have a real answer today; the rest are open and are the reason the ranking stops where it does.</p>
<div class="callout warn"><strong>The five that actually gate a purchase.</strong>
<ol class="tight">
<li>Are your travel dates fixed? (Every hotel number is date-specific.)</li>
<li>Is “single entry per starting flight” acceptable, or must it be one entry for the whole event?</li>
<li>Will the Venetian Poker Room put its re-entry rule in writing for the specific event numbers?</li>
<li>Will you meet the poker-rate play requirement (6 h cash or a $300+ buy-in per night)?</li>
<li>Can you walk the actual route — rooms to poker room — in under 30 minutes on the day?</li>
</ol></div>
{''.join(blocks)}
"""
    page("questions.html", "Questions", body, "questions.html")


def page_suggestions():
    tiers = {}
    for s in SUGG["suggestions"]:
        tiers.setdefault(s["tier"], []).append(s)
    blocks = []
    for t in SUGG["tier_order"]:
        rows = []
        for s in tiers.get(t, []):
            rows.append(
                f'<tr data-search="{E((s["id"] + " " + s["title"] + " " + s["detail"]).lower())}">'
                f'<td class="mono">{E(s["id"])}</td><td><strong>{E(s["title"])}</strong><br><span class="small muted">{E(s["detail"])}</span></td>'
                f'<td class="small">{E(s["impact"])}</td><td class="small">{E(s["effort"])}</td>'
                f'<td><span class="tag {"info" if s.get("recommended") else ""}">{E("recommended" if s.get("recommended") else "optional")}</span></td>'
                f'<td class="small">{(" ".join(src_link(x) for x in s["sources"])) if s.get("sources") else src_link("https://github.com/karagemop466-tech/Poker4/tree/main", "repo")}</td></tr>')
        blocks.append(f"<h2>{E(t)}</h2>" + table(["#ID","Suggestion","Impact on a decision","Effort","Status","Related source"], rows, caption=f"{len(rows)} suggestions — {E(t)}", table_id="s-" + re.sub(r'[^a-z]', '', t.lower())))
    body = f"""
<div class="breadcrumb"><a href="index.html">Dashboard</a> / Suggestions</div>
<h1>Suggested improvements — decide the path before changing the site</h1>
<p class="lede">Nothing on this page has been implemented. Each suggestion states what it would change about a real decision, how much work it is, and whether it is recommended. Pick the ones you want and they become the next build's scope.</p>
<div class="callout"><strong>Recommended path, if you only pick three.</strong>
<ol class="tight"><li><strong>S1</strong> — get the Venetian entry rule in writing. It converts 83 unverified rows into a usable single-entry list and costs one phone call.</li>
<li><strong>S2</strong> — read the Wynn WPT per-event structure sheets to fill 134 missing fee values. That is the difference between a listed buy-in and a true cost.</li>
<li><strong>S3</strong> — capture one real date-specific hotel checkout total per property. Until then every hotel number is a floor, not a quote.</li></ol></div>
{controls(show_date=False, show_se=False)}
{''.join(blocks)}
<h2>Deliberately not suggested</h2>
<p>Auto-scraping the Venetian calendar or the Wynn PDFs was considered and is not recommended yet: both are official sources with no machine-readable API, and a scraper that silently fails would turn “unverified” into “looks verified”. If it is built, it must write the same retrieval date and excerpt for every value it captures, exactly like the manual log on this site.</p>
"""
    page("suggestions.html", "Suggestions", body, "suggestions.html")


def page_about():
    rows = []
    for k, s in sorted(SRC.items()):
        sc = (s.get("excerpt") or "")
        if len(sc) > 320:
            sc = sc[:317] + "…"
        rows.append(f'<tr data-search="{E((k + " " + s["publisher"] + " " + s["title"]).lower())}"><td class="mono">{E(k)}</td><td>{E(s["publisher"])}</td><td><a href="{E(s["url"])}">{E(s["title"])}</a></td><td class="mono">{E(s["retrieved"])}</td><td><span class="tag {"ok" if s["tier"]=="official" else ("info" if s["tier"]=="official_map_data" else "warn")}">{E(s["tier"])}</span></td><td class="small">{E(sc)}</td></tr>')
    body = f"""
<div class="breadcrumb"><a href="index.html">Dashboard</a> / Method &amp; sources</div>
<h1>Method, source table and repo findings</h1>
<p class="lede">How every number on this site was obtained, what was checked against what, and the irregularities found in the repository itself.</p>
<h2>The verification protocol, applied to every row</h2>
<ol class="tight">
<li><strong>Read the operator's own page or PDF.</strong> Not an aggregator, not a search snippet, not a review site.</li>
<li><strong>Record the retrieval date and a verbatim excerpt</strong> for the value. Those live in <code>data/v2/sources.json</code> and are visible on every table row's source link.</li>
<li><strong>Cross-check the second source.</strong> The Venetian calendar gives the buy-in and guarantee; that row's structure sheet gives the chips, level minutes, late-registration clock, house fee and pool contribution. Where they disagree, both are shown and the row is flagged.</li>
<li><strong>Never infer a rule from silence.</strong> A missing re-entry sentence is not a freezeout. The site proves this by citing prior-season Venetian sheets that print re-entry when they mean it.</li>
<li><strong>Leave it blank rather than estimate.</strong> A blank is rendered <span class="blank">UNVERIFIED</span> and appears on <a href="flagged.html">Flagged for review</a>.</li>
</ol>
<h2>Source table — {len(SRC)} entries, every one date-stamped</h2>
{controls(show_date=False, show_se=False)}
{table(["#ID","Publisher","Document","Retrieved","Tier","Excerpt read"], rows, caption="Official = casino/hotel operator or tournament organiser. official_map_data = OpenStreetMap/OSRM routing only. third_party_reference = lead only, never used for a displayed fact.", table_id="sources")}
<h2>Repo review — irregularities found in this repository</h2>
<table class="tablewrap"><tbody>
<tr><td class="mono">R1</td><td><strong>Residual merge-conflict markers in COORDINATION.md.</strong> A <code>=======</code> line and a <code>&gt;&gt;&gt;&gt;&gt;&gt;&gt; origin/main</code> line survived a merged PR, with a duplicated session block between them.</td><td class="small">Removed the two delimiter lines only; both blocks of text were kept verbatim. Logged in COORDINATION.md.</td></tr>
<tr><td class="mono">R2</td><td><strong>Several parallel sites ship competing “single entry” claims.</strong> <code>strip/</code>, <code>verified/</code>, <code>df41f5c6/</code>, <code>c07371e3/</code>, <code>60fb62da/</code> and <code>pages/</code> each carry their own snapshot; some earlier dashboards showed “single-entry” labels that were later corrected.</td><td class="small">This version does not edit or delete them; it links them as historical snapshots from <code>index.html</code> and states the current rule (zero confirmed Venetian single-entry rows).</td></tr>
<tr><td class="mono">R3</td><td><strong>No data is shared between the parallel sites.</strong> Six separate JSON schemas, four separate build scripts.</td><td class="small">The new <code>data/v2/</code> layer plus <code>tools/v2_*.py</code> is self-contained and documented here so the next session can extend it rather than fork it again.</td></tr>
<tr><td class="mono">R4</td><td><strong>Bellagio Saturday structure sheet contradicts itself</strong> — filename says $1,000, heading says $1,100, rule 07 splits a $600 buy-in.</td><td class="small">Flagged, buy-in not asserted; both figures shown on the row.</td></tr>
<tr><td class="mono">R5</td><td><strong>Guarantee semantics were mixed in earlier snapshots.</strong> Venetian prints “$8,000 (prize pool + total bounties)” — not a pure pool guarantee.</td><td class="small">Every guarantee on this site carries a <code>guarantee_basis</code> of <em>prize_pool</em> or <em>pool_plus_bounties</em>, and the ratio column tags the bounty-inclusive ones.</td></tr>
<tr><td class="mono">R6</td><td><strong>Caesars flyer is undated for a specific calendar day</strong> and carries no day-of-week qualifier.</td><td class="small">Rows are marked “daily, recurring”, not given dates.</td></tr>
<tr><td class="mono">R7</td><td><strong>Walking times were previously absent or unlabelled.</strong></td><td class="small">Now computed with a documented method (OSRM foot routing, property centroids) and labelled as an estimate on every row and in the footer.</td></tr>
</tbody></table>
<h2>How to reproduce this snapshot</h2>
<pre class="mono" style="background:#0c1424;border:1px solid #24314e;border-radius:10px;padding:12px;overflow:auto">python3 tools/v2_extract.py        # Venetian 94 rows + structure facts  -> data/v2/events.json
python3 tools/v2_extract_other.py   # Wynn WPT 134 rows + hand rows      -> data/v2/events_other.json
python3 tools/v2_build.py           # renders this site                  -> v2/*.html
python3 tools/v2_verify.py          # link + source + blank audits</pre>
<p class="small muted">Files are plain HTML/CSS/JS with no build step at deploy time; GitHub Pages serves the repository root, so <code>v2/</code> is live as soon as it is on <code>main</code>.</p>
"""
    page("about.html", "Method & sources", body, "about.html")


def main():
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    page_index()
    page_tournaments()
    page_schedule()
    page_hotels()
    page_calculator()
    page_venues()
    page_separate()
    page_flagged()
    page_questions()
    page_suggestions()
    page_about()
    print("built", len(os.listdir(OUT)), "items in v2/")


if __name__ == "__main__":
    main()
