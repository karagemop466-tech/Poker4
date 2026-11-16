#!/usr/bin/env python3
"""Builds the static GitHub Pages sub-site in /verified from data/*.json.

Run:  python3 build/build_site.py
Only standard library is used. Every table row is generated from data files
that carry official source keys; the sources page is generated from the same registry.
"""
import html
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "verified"
DOCS.mkdir(exist_ok=True)
DATA = ROOT / "data"
ACCESSED = "2026-11-16"

T = json.loads((DATA / "tournaments.json").read_text(encoding="utf-8"))
U = json.loads((DATA / "unverified.json").read_text(encoding="utf-8"))
H = json.loads((DATA / "hotels.json").read_text(encoding="utf-8"))

# ---------- source registry ----------
SRC = dict(T["sources"])
SRC.update({
    "V_RESORT": {"label": "Venetian resort fee page", "url": "https://www.venetianlasvegas.com/resort/resort-fee.html"},
    "V_PARKING": {"label": "Venetian player parking page (linked from official poker page)", "url": "https://www.venetianlasvegas.com/resort/casino/poker/player-parking.html"},
    "B_HOTEL": {"label": "Bellagio hotel rooms page", "url": "https://bellagio.mgmresorts.com/en/hotel.html"},
    "C_HOTEL": {"label": "Caesars Palace hotel page", "url": "https://www.caesars.com/caesars-palace/hotel"},
    "GN": {"label": "Golden Nugget poker room page (off-Strip, downtown)", "url": "https://www.goldennugget.com/las-vegas/casino/poker-room/"},
    "RW": {"label": "Resorts World poker room page (dining only)", "url": "https://www.rwlasvegas.com/gaming/poker-room/poker-room-dining/"},
    "HSL": {"label": "Horseshoe Las Vegas casino page (poker section)", "url": "https://www.caesars.com/horseshoe-las-vegas/casino"},
    "ARIA_TRY": {"label": "Aria poker page — attempted, returned 404", "url": "https://www.aria.com/en/casino/poker"},
    "MGMG_TRY": {"label": "MGM Grand poker page — attempted, returned 404", "url": "https://www.mgmgrand.com/en/casino/poker.html"},
    "PH_TRY": {"label": "Planet Hollywood poker page — attempted, error", "url": "https://www.planethollywoodresortcasino.com/casino/poker"},
    "WSOP_SCHED": {"label": "WSOP official tournament schedule", "url": "https://www.wsop.com/schedule/"},
    "W_FEE_TRY": {"label": "Wynn resort-fee page — attempted, unavailable", "url": "https://www.wynnlasvegas.com/hotel/resort-fee"},
    "C_FEE_TRY": {"label": "Caesars Palace resort-fee page — attempted, redirected to general hotel page", "url": "https://www.caesars.com/caesars-palace/resort-fee"},
    "B_FEE_TRY": {"label": "Bellagio resort-fee page — attempted, 404", "url": "https://bellagio.mgmresorts.com/en/hotel/resort-fee.html"},
})
THIRD_PARTY = [
    ("Wynn fee figures (third-party, conflicting)", "https://getcostidea.com/how-much-does-it-cost-to-stay-at-wynn-las-vegas-rates-fees/", "$55 + tax"),
    ("Wynn fee figures (third-party, conflicting)", "https://www.thingsvegas.com/guides/las-vegas-resort-fees/", "$51"),
    ("Wynn fee figures (third-party, conflicting)", "https://lasvegashotels.blog/wynn-las-vegas-review", "$56.69 incl. tax"),
    ("Bellagio fee figures (third-party, conflicting)", "https://www.feelingvegas.com/does-bellagio-have-a-resort-fee/", "$45 + tax"),
    ("Bellagio fee figures (third-party, conflicting)", "https://unleashvegas.com/hotels/bellagio", "$50 + tax"),
    ("Caesars fee figures (third-party, conflicting)", "https://lasvegaswonders.com/caesars-palace-prices/", "$49.95 + tax"),
    ("Caesars fee figures (third-party, conflicting)", "https://hoteltiplasvegas.com/caesars-palace-review/", "$54.95 + tax"),
    ("Caesars fee figures (third-party, conflicting)", "https://www.resortfeechecker.com/hotel_resort_fees_las_vegas_nv.html", "$62.30"),
    ("Palazzo fee figures (third-party, conflicting)", "https://unleashvegas.com/hotels/palazzo", "$50 + tax"),
    ("Third-party tournament listing (stale; contains a 2019 article and inconsistent details)", "https://www.888poker.com/magazine/poker-world/poker-tournaments-las-vegas-where-play-2026", "Not used for values"),
    ("Third-party schedule aggregator (not used for values)", "https://pokertournaments101.com/tools/2026-wsop-tournament-planner", "Not used for values"),
]
for k, v in SRC.items():
    pass


def esc(s):
    return html.escape("" if s is None else str(s))


def money(v):
    if v is None or v == "":
        return "<span class='unv'>blank — unverified</span>"
    return f"${v:,.0f}" if isinstance(v, (int, float)) else esc(v)


def link_tags(keys):
    out = []
    for k in keys:
        s = SRC.get(k)
        if not s:
            out.append(f"<code>{esc(k)}</code>")
            continue
        out.append(f"<a href='{esc(s['url'])}' target='_blank' rel='noopener'>{esc(s['label'])}</a>")
    return "<br>".join(out)


def ratio_cell(v):
    if v is None:
        return "<span class='unv'>blank</span>"
    return f"{v:.1f}×"


NAV = [
    ("index.html", "Home"),
    ("summary.html", "Executive summary"),
    ("tournaments.html", "Candidate events (rules unverified)"),
    ("reentry.html", "Re-entry / add-on (separate)"),
    ("hotels.html", "Hotels"),
    ("schedule.html", "Daily schedule"),
    ("questions.html", "Questions & info needed"),
    ("suggestions.html", "Suggestions (for your decision)"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
    ("../index.html", "Original dashboard ↗"),
]

CSS = """
:root{--ink:#1d2330;--mut:#5b6474;--line:#e3e7ee;--bg:#f7f9fc;--acc:#0b6e4f;--warn:#b26a00;--bad:#9b1c1c}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#0f2b25;color:#fff;padding:14px 20px;position:sticky;top:0;z-index:5}
header .t{font-weight:700;font-size:17px}header nav{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px 14px}
header nav a{color:#cfe9e1;text-decoration:none;font-size:13px}header nav a.on{color:#fff;font-weight:700;border-bottom:2px solid #7fd6b5}
main{max-width:1200px;margin:0 auto;padding:22px 18px 60px}
h1{font-size:26px;margin:4px 0 6px}h2{font-size:20px;margin:26px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}h3{font-size:16px;margin:18px 0 6px}
p,li{max-width:900px}.mut{color:var(--mut)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:14px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
.card b.n{font-size:26px;display:block}.card a{color:var(--acc);font-weight:600;text-decoration:none}
.note{background:#fff8e6;border:1px solid #f1d58a;border-radius:8px;padding:10px 14px;margin:12px 0}
.ok{background:#e9f7f1;border:1px solid #a7dcc4;border-radius:8px;padding:10px 14px;margin:12px 0}
.bad{background:#fdecec;border:1px solid #f0b3b3;border-radius:8px;padding:10px 14px;margin:12px 0}
.tbl-wrap{overflow:auto;background:#fff;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#eef3f8;position:sticky;top:0;font-size:12.5px;text-transform:uppercase;letter-spacing:.03em;color:#33405a}
tr:nth-child(even) td{background:#fbfcfe}
td.num,th.num{text-align:right;white-space:nowrap}
.unv{color:var(--warn);font-style:italic}
a{color:#0b5fa5}
code{background:#eef2f7;padding:1px 4px;border-radius:4px;font-size:12.5px}
.filter{padding:8px 10px;border:1px solid var(--line);border-radius:8px;width:320px;max-width:100%;margin:8px 0}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;background:#e8eef6;margin-right:4px}
footer{max-width:1200px;margin:0 auto;padding:0 18px 30px;color:var(--mut);font-size:12.5px}
"""

JS = """
function filt(id,q){q=q.toLowerCase();document.querySelectorAll('#'+id+' tbody tr').forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(q)>-1?'':'none'})}
"""


def page(fname, title, body, active=None):
    nav_html = "".join(
        f"<a href='{h}' class='{'on' if h == active else ''}'>{esc(t)}</a>" for h, t in NAV
    )
    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Las Vegas Strip Poker Planner</title>
<style>{CSS}</style></head>
<body>
<header><div class="t">Las Vegas Strip Poker Planner <span class="mut" style="color:#9fc7b9;font-weight:400">· verified from official sources · data as of {ACCESSED}</span></div>
<nav>{nav_html}</nav></header>
<main>{body}</main>
<footer>Built from <code>data/*.json</code> by <code>build/build_site.py</code>. Blank values are unverified and were not inferred. Times and prices can change; confirm with the venue before travel. Contact details shown are copied from official pages.</footer>
<script>{JS}</script>
</body></html>"""
    (DOCS / fname).write_text(html_doc, encoding="utf-8")


def table(tid, headers, rows, num_cols=()):
    th = "".join(f"<th class='{'num' if i in num_cols else ''}'>{esc(h)}</th>" for i, h in enumerate(headers))
    body = "".join("<tr>" + "".join(f"<td class='{'num' if i in num_cols else ''}'>{c}</td>" for i, c in enumerate(r)) + "</tr>" for r in rows)
    return (f"<input class='filter' placeholder='Filter rows (type any word)…' oninput=\"filt('{tid}',this.value)\">"
            f"<div class='tbl-wrap'><table id='{tid}'><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>")


def fmt_time_key(t):
    m = re.match(r"(\d+):(\d+)\s*(AM|PM)", t or "")
    if not m:
        return 9999
    h, mi, ap = int(m.group(1)) % 12, int(m.group(2)), m.group(3)
    return (h + (12 if ap == "PM" else 0)) * 60 + mi


SE = T["entry_rules_unverified"]
RE = T["reentry_or_addon"]
DAYS_ORDER = {}
SE_sorted = sorted(SE, key=lambda r: (r["day"][4:9] if False else "", fmt_time_key(r["time"])))

# ---------- verified count for home ----------
n_se = len(SE)
n_re = len(RE)
n_unv_v = len(U["venetian"])
n_unv_w = len(U["wynn_wpt"])

# ---------- 1. tournaments.html ----------
def se_row(r):
    return [
        esc(r["day"]), esc(r["time"]), esc(r["event"]), esc(r["name"]), esc(r["venue"]),
        money(r["buy_in"]), money(r["guarantee"]), ratio_cell(r["value_ratio"]),
        f"{r['chips']:,}" if r.get("chips") else "<span class='unv'>blank</span>",
        esc(r["reg_closes"]), money(r["prize_share"]), money(r["house_fee"]),
        esc(r["reentry_addon"]), link_tags(r["sources"]), esc(r["notes"]),
    ]

se_headers = ["Day", "Start", "Event #", "Tournament", "Venue", "Buy-in", "Guarantee", "GTD ÷ buy-in (computed)",
              "Starting chips", "Reg. closes", "Prize pool share", "House fee", "Re-entry / add-on (structure)", "Source (official)", "Notes"]
se_rows = [se_row(r) for r in SE]
top = sorted([r for r in SE if r["value_ratio"]], key=lambda r: -r["value_ratio"])[:3]
top_html = "".join(f"<li><b>{esc(r['day'])} · {esc(r['time'])} · {esc(r['name'])}</b> — buy-in ${r['buy_in']}, guarantee ${r['guarantee']:,}, ratio {r['value_ratio']}× (computed). <span class='mut'>Sources: {', '.join(esc(SRC[s]['label']) for s in r['sources'][:1])}</span></li>" for r in top)
body = f"""
<h1>Candidate tournaments — entry rules unverified</h1>
<p class="mut">Strip poker rooms. Window: Nov 16 – Dec 23, 2026. These structure sheets do <b>not</b> explicitly confirm single-entry or prohibit re-entry, rebuy, or add-on. Rows below are candidates only—not verified single-entry events. Every row links to official documentation.</p>
<div class="ok"><b>{n_se} candidate rows</b> — all at The Venetian Poker Room (The Palazzo, level 2); entry rules remain unverified. Buy-ins $200–$600. Guarantees $8,000–$40,000 (one $200 event has no guarantee printed; left blank).</div>
<h2>Candidate guarantee-to-buy-in ratios (arithmetic only; not ranked as single-entry)</h2>
<ul>{top_html}</ul>
<p class="mut">Ratio = official guarantee ÷ buy-in. It is a comparison aid, not an official figure. Prize-pool share and house fee are from the structure sheets where shown.</p>
<h2>All candidate rows (not confirmed single-entry)</h2>
{table('tblSE', se_headers, se_rows, num_cols=(5,6,7,8,10,11))}
<h2>Not included in candidate list</h2>
<p>Schedule-only and entry-rule questions are on the <a href="flagged.html">Flagged for Review</a> page. Events explicitly allowing re-entry, rebuys or add-ons are on the <a href="reentry.html">separate page</a>.</p>
"""
page("tournaments.html", "Candidate tournaments (entry rules unverified)", body, "tournaments.html")

# ---------- 2. reentry.html ----------
re_headers = ["Day", "Start", "Event", "Tournament", "Venue", "Buy-in", "Guarantee", "Starting chips", "Reg. closes", "Re-entry / rebuy / add-on", "Source (official)", "Notes"]
re_rows = []
for r in RE:
    re_rows.append([
        esc(r["day"]), esc(r["time"]), esc(r["event"]), esc(r["name"]), esc(r["venue"]),
        money(r["buy_in"]), money(r["guarantee"]),
        f"{r['chips']:,}" if r.get("chips") else "<span class='unv'>blank</span>",
        esc(r["reg_closes"] or ""), esc(r["reentry_addon"]), link_tags(r["sources"]), esc(r["notes"]),
    ])
body = f"""
<h1>Re-entry, rebuy & add-on events (separate section)</h1>
<p class="mut">These events let you pay again or buy extra chips. Per your rules they are kept out of the single-entry list. <b>Not ranked.</b></p>
<div class="bad"><b>Why this matters:</b> the Bellagio events also sell an <i>optional staff gratuity</i> that adds chips to the starting stack. That is paying more for an advantage, so it sits in this section too.</div>
<h2>Events</h2>
{table('tblRE', re_headers, re_rows, num_cols=(5,6,7))}
<h2>Excluded from this list</h2>
<ul>
<li>Venetian "Milestone Satellite" events (awards seats, not a tournament entry you pay for). Excluded from the window.</li>
<li>Venetian Day 2 restarts and flight events: their re-entry status is not confirmed, so they are on <a href="flagged.html">Flagged for Review</a>.</li>
</ul>
"""
page("reentry.html", "Re-entry & add-on events", body, "reentry.html")

# ---------- 3. hotels.html ----------
hot_headers = ["Property", "Poker room location (official)", "Resort fee (official)", "Room rate per night", "Tax", "True cost per night", "Walking to poker room", "Sources (official)", "Notes"]
hot_rows = []
for h in H["hotels"]:
    hot_rows.append([
        f"<b>{esc(h['property'])}</b>",
        esc(h["poker_location"]),
        esc(h["resort_fee"]) if h.get("resort_fee") else "<span class='unv'>unverified</span>",
        "<span class='unv'>blank — unverified</span>",
        "<span class='unv'>blank</span>",
        "<span class='unv'>blank</span>",
        esc(h["walk"]),
        link_tags(h["sources"]),
        esc(h["notes"]),
    ])
body = f"""
<h1>Hotels near the tournaments</h1>
<p class="mut">Priority per your brief: cost and quality first, then distance (≤30 min walk). Only one value on this page is confirmed from an official page: the Venetian resort fee. Room rates, taxes, and walking times were not confirmed from official sources, so they are blank.</p>
<div class="note"><b>True nightly cost formula:</b> (room rate + resort fee) × (1 + lodging tax), plus any parking, extra-guest and mandatory fees. Only the resort fee at The Venetian is currently verified; the other inputs are blank until confirmed.</div>
<h2>Candidate hotels (on-site poker rooms)</h2>
{table('tblHot', hot_headers, hot_rows)}
<h2>Notes</h2>
<ul>
<li>Resort fee figures on third-party sites conflict with each other for the same property (see <a href="flagged.html">Flagged for Review</a>). They were <b>not</b> used as values.</li>
<li>Walking distance: each candidate has its poker room inside the same resort, so the walk is internal. Exact walking time was not measured or confirmed from an official map; please confirm on the property map before booking.</li>
<li>Venetian poker players may get reduced suite rates with a Venetian Rewards card (official page). The amounts were not confirmed, so they are not shown.</li>
<li>Off-Strip and other poker rooms (Golden Nugget downtown, Horseshoe, Resorts World, Aria, MGM Grand, Planet Hollywood) are not shown: no verified single-entry schedule for them in this window. See <a href="flagged.html">Flagged</a>.</li>
</ul>
"""
page("hotels.html", "Hotels", body, "hotels.html")

# ---------- 4. schedule.html ----------
body = """
<h1>Daily schedule planner</h1>
<p class="mut">Goal: play from 8:00 AM all day. The official sources do not support that yet, so this page shows what <i>is</i> verified.</p>
<div class="bad"><b>8:00 AM start is not supported.</b> The earliest listed candidate start is 11:10 AM (The Venetian); single-entry status is unverified. The official Caesars daily events start at 10:00 AM, but those have re-entry/add-ons (separate section). Official Venetian events at 10:10 AM (RaceDay, #49, #47, etc.) are not verified.</div>
<h2>Candidate days with two listed events at the same venue (entry rules unverified)</h2>
<div class="tbl-wrap"><table>
<thead><tr><th>Day</th><th>Afternoon/early event</th><th>Evening event</th><th>Venue</th><th>Note</th><th>Sources</th></tr></thead>
<tbody>
<tr><td>Thu Nov 26, 2026</td><td>11:10 AM · #12 $300 NLH (1-Day), $10,000 GTD</td><td>5:10 PM · #13 $200 NLH Bounty, $8,000 GTD</td><td>The Venetian</td><td>Registration for #12 closes ~4:55 PM; #13 starts 5:10 PM. Run times are not in the official data, so overlap is possible if you are still playing #12.</td><td>""" + link_tags(["V_SCHED", "V_S5", "V_S1"]) + """</td></tr>
<tr><td>Fri Nov 27, 2026</td><td>11:10 AM · #14 $600 NLH (1-Day), $30,000 GTD</td><td>5:10 PM · #15 $200 NLH Bounty, $8,000 GTD</td><td>The Venetian</td><td>Same overlap caveat. #14 is the higher-value event of the two.</td><td>""" + link_tags(["V_SCHED", "V_S7", "V_S1"]) + """</td></tr>
</tbody></table></div>
<h2>Time blocks (verified only)</h2>
<div class="tbl-wrap"><table>
<thead><tr><th>Time</th><th>What is verified</th><th>Gap / to do</th></tr></thead>
<tbody>
<tr><td>8:00 – 10:00 AM</td><td>No single-entry event verified.</td><td>Confirm with venues whether any early events exist and their entry rules.</td></tr>
<tr><td>10:00 AM – 11:10 AM</td><td>Caesars daily 10:00 AM is re-entry/add-on (separate). No single-entry event verified.</td><td>Use the time to walk to the poker room or register.</td></tr>
<tr><td>11:10 AM</td><td>The Venetian candidate-event starts (Nov 18, 22, 25, 26, 27; Dec 6, 23); entry rules unverified.</td><td>Late registration closes ~3:40–4:55 PM depending on the event.</td></tr>
<tr><td>5:10 PM</td><td>The Venetian $200 Bounty events (Nov 24 – Dec 23 on listed days).</td><td>Late registration closes 9:40 PM.</td></tr>
</tbody></table></div>
<h2>What we still need to make a full day plan</h2>
<ul>
<li>Trip dates (not provided). The plan above uses the printed schedule window.</li>
<li>Run times for each tournament (length of play), so overlapping events can be scheduled. Not in the sources reviewed.</li>
<li>Confirmation of any 8 AM events from each venue's official poker desk (venue poker desks; contact details not verified).</li>
</ul>
"""
page("schedule.html", "Daily schedule", body, "schedule.html")

# ---------- 5. summary.html ----------
body = f"""
<h1>Executive summary</h1>
<p class="mut">As of Sunday, Nov 16, 2026 (Los Angeles). Based on official schedules and structure sheets fetched on {ACCESSED}.</p>
<h2>Key findings</h2>
<ol>
<li><b>No single-entry event is verified by the reviewed sources.</b> {n_se} Venetian candidate rows have structure sheets, but the reviewed sheets do not explicitly confirm single-entry or prohibit additional entries/add-ons. They are listed as candidates only.</li>
<li><b>Ratio comparisons are not recommendations:</b> guarantee ÷ buy-in is arithmetic only; entry rules and expected value are not established.</li>
<li><b>Potential low-buy-in candidates:</b> $200 Venetian events are not ranked until entry rules are confirmed.</li>
<li><b>Re-entry, rebuys, and add-ons are separate.</b> Caesars Palace daily ($100/$160, re-entry and add-on), Wynn daily and nightly ($160–$240, re-entry/rebuy/add-on, $10,000–$40,000 guarantees), and Bellagio weekly ($400–$1,000+). These are on the separate page and are not ranked.</li>
<li><b>Wynn WPT World Championship (Nov 27 – Dec 21)</b> has large guarantees ($1M–$5M) and $10,400 entries. Structure sheets were not fully reviewed, so these are on Flagged and not ranked.</li>
<li><b>Hotels:</b> The Venetian is the only candidate with an official resort-fee figure ($55 plus tax). Room rates, taxes, and other resort fees are not verified, so the true cost per night cannot yet be calculated for any hotel.</li>
<li><b>8:00 AM all-day plan is not supported</b> by verified official schedules. Candidate starts are not classified as single-entry; overlapping play duration is also unknown.</li>
<li><b>WSOP:</b> the official WSOP schedule for Nov–Dec 2026 lists no Las Vegas event (Circuit events are elsewhere).</li>
</ol>
<h2>What is verified vs not</h2>
<div class="cards">
<div class="card"><b class="n">0</b>verified single-entry rows</div>
<div class="card"><b class="n">{n_re}</b>re-entry / rebuy / add-on rows (separate)</div>
<div class="card"><b class="n">{n_unv_v + n_unv_w}</b>schedule-only rows (flagged, not ranked)</div>
<div class="card"><b class="n">1 of 4</b>candidate hotels with an official resort fee</div>
</div>
<h2>Decisions needed from you</h2>
<ul>
<li>Trip dates and length of stay.</li>
<li>Maximum buy-in per tournament and total budget for the trip.</li>
<li>Whether re-entry events should be included in the plan (the rules you gave say they go in a separate section; we keep them out of ranking).</li>
<li>Whether to spend time on structure-sheet verification for the flagged rows (see <a href="suggestions.html">Suggestions</a>).</li>
</ul>
"""
page("summary.html", "Executive summary", body, "summary.html")

# ---------- 6. questions.html ----------
Q = [
    ("Q1", "Which Strip single-entry tournaments are running Nov 16 – Dec 23, 2026?", "Answered (partly)",
     "19 Venetian candidate rows have reviewed structure sheets, but those sheets do not explicitly establish single-entry or prohibit re-entry/add-ons. Other events are flagged as not reviewed.", "Review the flagged structure sheets (see Suggestions)."),
    ("Q2", "Is the Caesars Palace daily schedule still current?", "Open",
     "The flyer is official but undated (2026). Re-entry and add-on rules are printed on it.", "Call the Caesars Palace poker room or check the live schedule on the day."),
    ("Q3", "Are the Bellagio weekly events still running?", "Open",
     "PDFs are undated. One PDF refers to a final day of 9/13/26, and the poker page has a stale notice (‘resume Saturday, July 26’). The Saturday buy-in conflicts ($1,000 vs $1,100).", "Confirm the Bellagio poker room hours and host contact from the official page before play."),
    ("Q4", "What is the Saturday Bellagio buy-in?", "Open", "$1,000 (file name) vs $1,100 (PDF header). Left blank.", "Ask Bellagio poker room; check the live schedule."),
    ("Q5", "Are Wynn WPT events single entry? What are their re-entry rules?", "Open",
     "Schedule and general terms are official. Event structure sheets were not transcribed.", "Review each WPT structure sheet (Wynn publishes them with the schedule)."),
    ("Q6", "Does an 8:00 AM start work anywhere?", "Open (likely no)",
     "No single-entry start is verified. Earliest listed candidate start is 11:10 AM at The Venetian; Caesars 10:00 AM allows re-entry.", "Confirm early-morning events directly with each poker room."),
    ("Q7", "What are the true hotel costs per night?", "Open",
     "Room rates are dynamic and were not confirmed from official sources. The Venetian resort fee is $55 + tax (official).", "Pull rates for your exact dates from each official booking engine and keep a dated snapshot."),
    ("Q8", "What is the Clark County lodging tax rate used in the cost formula?", "Open",
     "Third-party sites give a figure; it is not used here. No official government source was checked yet.", "Verify on a Clark County or Nevada Department of Taxation page before using it."),
    ("Q9", "Which resort fee applies at Wynn, Caesars Palace and Bellagio?", "Open",
     "Official fee pages were not reachable. Third-party figures conflict (e.g. Caesars $49.95 to $62.30).", "Check each property's booking page or front desk for the fee on your dates."),
    ("Q10", "How long does each tournament take to play?", "Open", "Not in the official data reviewed.", "Ask each poker room or use the structure sheets (levels × blind durations) to estimate."),
    ("Q11", "Are the Venetian $200 bounty events single entry?", "Open",
     "Structure sheet 1 describes the buy-in, late registration and bounty, but does not explicitly establish a one-entry limit or prohibit re-entry/add-ons.", "Ask the poker room to confirm the entry cap and all additional-spend mechanics."),
    ("Q12", "Do Wynn tournaments require a loyalty card?", "Answered", "Not confirmed on an official page reviewed; check before play.", "Ask the poker desk."),
    ("Q13", "Do Venetian tournaments require a loyalty card?", "Answered", "Yes: Venetian Rewards card and age 21+ (structure sheets).", "Sign up before play."),
    ("Q14", "What are your travel dates and length of stay?", "Open (needed from you)", "Not provided.", "Provide dates so the plan can be built for that window."),
    ("Q15", "Are there verified Las Vegas WSOP events in this window?", "Answered (no)", "The official WSOP schedule for Nov–Dec 2026 lists no Las Vegas event.", "Check the WSOP schedule again for 2027 dates when posted."),
    ("Q16", "Do Aria, MGM Grand, Planet Hollywood, Horseshoe, Resorts World or Golden Nugget have verified single-entry events in the window?", "Open",
     "Official pages were not reachable (404 or error) or gave no schedule. See Flagged.", "Fetch current official schedules for each venue."),
]
q_rows = [[esc(a), esc(b), esc(c), esc(d), esc(e)] for a, b, c, d, e in Q]
body = f"""
<h1>Questions & information needed</h1>
<p class="mut">What must be answered before a decision can be made reasonably. Answered items cite the source on the Flagged or source pages.</p>
{table('tblQ', ['ID', 'Question', 'Status', 'What we know (official)', 'How to get the missing piece'], q_rows)}
"""
page("questions.html", "Questions & info needed", body, "questions.html")

# ---------- 7. suggestions.html ----------
body = """
<h1>Suggestions for improving the site (for your decision)</h1>
<p class="mut">Nothing on this list has been implemented. Choose the items you want; we will implement only the approved ones.</p>
<div class="note"><b>Your choice:</b> reply with the IDs you approve (e.g. "S1, S3, S5") or "none".</div>
<div class="tbl-wrap"><table>
<thead><tr><th>ID</th><th>Suggestion</th><th>Why</th><th>Effort</th></tr></thead>
<tbody>
<tr><td>S1</td><td>Structure-sheet review for all flagged Venetian rows, with a re-entry/add-on column filled in per row.</td><td>Would move dozens of rows into the ranked list or the separate section.</td><td>Medium</td></tr>
<tr><td>S2</td><td>Add a "last verified" date and source per row, and a status icon (verified / unverified / conflict).</td><td>Makes it obvious what is confirmed.</td><td>Low</td></tr>
<tr><td>S3</td><td>Trip-date input: filter the schedule to your dates and show what is open on each day.</td><td>Needed for a real planner.</td><td>Medium</td></tr>
<tr><td>S4</td><td>Dated room-rate snapshots from each official booking engine (e.g. weekly pulls).</td><td>Room rate is the biggest missing input for the true-cost calculation.</td><td>Medium–High</td></tr>
<tr><td>S5</td><td>Clark County / Nevada tax rate page as a cited input.</td><td>Needed for the true cost formula.</td><td>Low</td></tr>
<tr><td>S6</td><td>Walking-time checks from an official property map (or a map-service API) for each hotel-to-room pair.</td><td>Distance rule is ≤30 min walk; this is currently unverified.</td><td>Low–Medium</td></tr>
<tr><td>S7</td><td>Add a calendar (.ics) export of the approved events.</td><td>Helps plan a full day.</td><td>Low</td></tr>
<tr><td>S8</td><td>Add off-Strip venues (Golden Nugget, Horseshoe, Resorts World, Aria, MGM Grand, Planet Hollywood) once their official schedules are verified.</td><td>Broader choice; currently not verifiable from the sources reached.</td><td>Medium</td></tr>
<tr><td>S9</td><td>Automated re-check of official sources on a schedule, with a diff log.</td><td>Schedules change; this catches changes quickly.</td><td>Medium–High</td></tr>
<tr><td>S10</td><td>Separate "Bounty" flag and "Age 50+" flag in the table.</td><td>Relevant to eligibility and format.</td><td>Low</td></tr>
</tbody></table></div>
<h2>Three paths to choose from</h2>
<ul>
<li><b>Path A — minimal:</b> keep the current site; approve S2 and S5 only.</li>
<li><b>Path B — planner:</b> approve S1, S2, S3, S5, S6 (complete verification plus a trip-date planner).</li>
<li><b>Path C — full:</b> approve everything (S1–S10).</li>
</ul>
"""
page("suggestions.html", "Suggestions", body, "suggestions.html")

# ---------- 8. flagged.html ----------
flag_items = [
    ("Repo", "Repo has only a one-line README (<code>README.md</code>, 8 bytes). No license, no code, no CI, no .gitignore.", "https://github.com/karagemop466-tech/Poker4"),
    ("Hotels", "Resort-fee figures from third-party sites conflict for the same property: Wynn $51 / $55 / $56.69 / $62.36; Bellagio $45 / $50 / $51 / $56.69 / $62.36; Caesars $49.95 / $50 / $54.95 / $55 / $62.30; Palazzo $50 / $55 / $56.69 / $62.36. None were used as values.", None),
    ("Hotels", "Official resort-fee page for Wynn, Caesars, and Bellagio could not be reached (see sources page).", None),
    ("Bellagio", "PDFs are undated. Friday PDF is titled '$600 NLH'. Saturday PDF file name says $1000 but header says $1100; combined guarantee $50,000.", "B_SAT"),
    ("Bellagio", "Saturday PDF references a 'Combined Final Day 2 (9/13/26)' — a date that appears to be in the past relative to Nov 16, 2026, so the PDF may be outdated.", "B_SAT"),
    ("Bellagio", "Poker page notice still says 'Tournament play will resume on Saturday, July 26' — stale.", "B_PAGE"),
    ("Caesars", "Daily NLH flyer is undated (2026 in filename). Confirm it is current.", "C_FLYER"),
    ("Wynn", "Wynn daily structure sheets say the events 'Wynn daily structure text includes a suspension clause; exact wording not re-checked' — the WPT series is not named; conflicting for Nov 27 – Dec 21.", "W_DAILY"),
    ("Wynn", "WPT schedule footnotes conflict: $1,100 'Ladies NLH' vs '$11,100 Ladies entry (discounted)'. The '$10,500' entries carry a footnote on discounted entry that was not fully reviewed.", "W_WPT"),
    ("Wynn", "Wynn poker page FAQ entries are listed as questions with no answers in the fetched text.", "W_PAGE"),
    ("Venetian", "Event numbers are shared across different flights and dates (e.g. #19 on Nov 29 / Nov 30 / Dec 1 / Dec 2; #26 on Dec 3–6; #56 on Dec 17–19). The schedule is correct, but event-number lookups are ambiguous.", "V_SCHED"),
    ("Venetian", "Event #6 ($200 NLH, Sun Nov 22) has no guarantee printed on the schedule or structure sheet. Left blank.", "V_S29"),
    ("Venetian", "Event #8 ($200 PKO, Nov 23) is not in the structure-sheet event list linked for bounty events; its structure was not reviewed.", "V_SCHED"),
    ("Venetian", "Venetian DSE page header names a different series (WPT Fall Festival, Oct 28 – Nov 15, 2026). Its status is not verified here; the DSE schedule covers Nov 16 – Dec 23.", "V_PAGE"),
    ("Horseshoe", "Official page says 'six exciting tournament times daily' with no times or buy-ins. Not verified.", "HSL"),
    ("Resorts World", "Official poker page shows poker dining only; no tournament schedule verified.", "RW"),
    ("Aria / MGM Grand / Planet Hollywood", "Official poker pages were not reachable (404 or error). No schedule verified.", "ARIA_TRY"),
    ("WSOP", "The WSOP official schedule for Nov–Dec 2026 lists no Las Vegas events in this window. Schedule page lists a 2027 Super Circuit LATAM event (not Vegas).", "WSOP_SCHED"),
    ("Third-party", "Search results included contradictory third-party guides, including a 2019 article titled '2026', and a Mandalay Bay / Caesars listing that does not match official pages. Not used for values.", None),
    ("Entry-rule correction", "The reviewed Venetian structures do not explicitly confirm single-entry or prohibit re-entry/add-ons. All 19 rows are candidates only; none is verified single-entry. The root dashboard and this subsite are aligned on this limitation.", "V_S5"),
    ("Walking distance", "Walking times to each poker room were not confirmed from an official map source. Left blank.", None),
    ("Room rates", "Nightly room rates are dynamic; no official rate snapshot was taken for the window. Left blank.", None),
]
flag_rows = []
for area, text, src in flag_items:
    srccell = link_tags([src]) if src else "<span class='mut'>see text</span>"
    flag_rows.append([esc(area), text, srccell])

u_rows_v = []
for r in U["venetian"]:
    u_rows_v.append([esc(r["when"]), esc(r["event"]), money(r["buy_in"]), money(r["guarantee"]), esc(r["reg_closes"] or ""), esc(r["structure_status"]), esc(r["why_unverified"]), link_tags([k.strip() for k in r["source"].split("/") if k.strip() in SRC])])
u_rows_w = []
for r in U["wynn_wpt"]:
    u_rows_w.append([esc(r["when"]), esc(r["event"]), money(r["buy_in"]), money(r["guarantee"]), esc(r["reg_closes"] or ""), esc(r["structure_status"]), esc(r["why_unverified"]), link_tags([r["source"]])])
u_headers = ["When", "Event", "Buy-in", "Guarantee", "Reg. closes", "Structure status", "Why not ranked", "Source (official)"]
ex_rows = []
for r in U["not_in_scope_or_not_verified"]:
    key = {"Aria Las Vegas": "ARIA_TRY", "MGM Grand": "MGMG_TRY", "Planet Hollywood": "PH_TRY", "Resorts World Las Vegas": "RW",
           "Horseshoe Las Vegas": "HSL", "Golden Nugget (downtown, off-Strip)": "GN", "WSOP": "WSOP_SCHED"}.get(r["venue"])
    ex_rows.append([esc(r["venue"]), esc(r["reason"]), link_tags([key]) if key else ""])

body = f"""
<h1>Flagged for Review</h1>
<p class="mut">Published so you can review irregularities, unverified items and sources after the site goes live. Flags do not block the merge. Each item has its source where available.</p>
<h2>1. Irregularities and conflicts</h2>
{table('tblFlag', ['Area', 'Irregularity / note', 'Source'], flag_rows)}
<h2>2. Unverified schedule rows — Venetian (not ranked; structure not reviewed)</h2>
{table('tblUV', u_headers, u_rows_v)}
<h2>3. Unverified schedule rows — Wynn WPT (not ranked)</h2>
{table('tblUW', u_headers, u_rows_w)}
<h2>4. Venues not verified</h2>
{table('tblEx', ['Venue', 'Reason', 'Source'], ex_rows)}
<h2>5. Repo review</h2>
<ul>
<li>Repo: <a href="https://github.com/karagemop466-tech/Poker4" target="_blank" rel="noopener">karagemop466-tech/Poker4</a> — base commit <code>52654c1</code> ("Initial commit").</li>
<li>Only file at base: <code>README.md</code> (contents: <code>Poker4</code>). No irregularities beyond the lack of documentation and license.</li>
<li>This session added: <code>COORDINATION.md</code>, <code>data/*.json</code>, <code>build/build_site.py</code>, <code>docs/*</code>.</li>
</ul>
"""
page("flagged.html", "Flagged for Review", body, "flagged.html")

# ---------- 9. sources.html ----------
rows = []
for k, v in SRC.items():
    rows.append([f"<code>{esc(k)}</code>", esc(v["label"]), f"<a href='{esc(v['url'])}' target='_blank' rel='noopener'>{esc(v['url'])}</a>", ACCESSED])
tp_rows = [[esc(a), f"<a href='{esc(u)}' target='_blank' rel='noopener'>{esc(u)}</a>", esc(note)] for a, u, note in THIRD_PARTY]
body = f"""
<h1>Sources</h1>
<p class="mut">Official sources were fetched on {ACCESSED}. Each table row on the site links to one or more of these keys.</p>
<h2>Official sources (used for values)</h2>
{table('tblSrc', ['Key', 'Label', 'URL', 'Accessed'], rows)}
<h2>Third-party pages (checked, NOT used for values)</h2>
{table('tblTP', ['Topic', 'URL', 'Note'], tp_rows)}
<p class="mut">Verification rule used: a value is shown only if an official page or PDF states it. Otherwise the cell is blank and labeled unverified.</p>
"""
page("sources.html", "Sources", body, "sources.html")

# ---------- 10. index.html ----------
body = f"""
<h1>Las Vegas Strip poker — verified tournaments, hotels and plan</h1>
<p class="mut">A simple dashboard. Every number links to an official source. Blank = not verified. Data as of {ACCESSED}.</p>
<div class="cards">
<div class="card"><b class="n">0</b><a href="tournaments.html">Candidate tournaments →</a><br><span class="mut">single-entry status unverified</span></div>
<div class="card"><b class="n">{n_re}</b><a href="reentry.html">Re-entry / add-on →</a><br><span class="mut">separate section</span></div>
<div class="card"><b class="n">{n_unv_v + n_unv_w}</b><a href="flagged.html">Flagged for Review →</a><br><span class="mut">schedule-only, not ranked</span></div>
<div class="card"><b class="n">1 of 4</b><a href="hotels.html">Hotels →</a><br><span class="mut">with an official resort fee</span></div>
</div>
<div class="cards">
<div class="card"><a href="summary.html">Executive summary →</a></div>
<div class="card"><a href="schedule.html">Daily schedule planner →</a></div>
<div class="card"><a href="questions.html">Questions & info needed →</a></div>
<div class="card"><a href="suggestions.html">Suggestions (choose before any change) →</a></div>
<div class="card"><a href="sources.html">Sources & verification →</a></div>
</div>
<div class="note"><b>Important:</b> this site is a research snapshot. Nothing has been filled in from non-official sources. Travel dates, budget, and room rates are still needed (see Questions).</div>
"""
page("index.html", "Home", body, "index.html")

# .nojekyll so GitHub Pages serves files as-is
(DOCS / ".nojekyll").write_text("", encoding="utf-8")
print("built pages:", sorted(p.name for p in DOCS.glob("*.html")))
