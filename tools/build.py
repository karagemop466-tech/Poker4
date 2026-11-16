#!/usr/bin/env python3
"""Build the static GitHub Pages site from data/*.csv.
Every table row is rendered with its official source link. Empty values render as a
flagged blank and are listed on flagged.html. Nothing is inferred or filled in."""
import csv, html, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
E = html.escape
NAV = [("index.html", "Summary"), ("tournaments.html", "Tournaments"),
       ("addons.html", "Add-on / re-entry"), ("schedule.html", "Schedule"),
       ("hotels.html", "Hotels"), ("questions.html", "Questions"),
       ("review.html", "Repo review"), ("flagged.html", "Flagged for Review")]
FLAG = '<span class="flag">⚑ unverified</span>'
NC = '<span class="flag">⚑ not captured</span>'

def rows(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))

def money(v):
    return f"${int(float(v)):,}" if v not in ("", None) and v.replace('.', '', 1).isdigit() else (v or None)

def cell(v, flag_html=FLAG):
    return E(v) if v not in ("", None) else flag_html

def link(url, label="source"):
    return f'<a href="{E(url)}" rel="noopener">{label}</a>' if url else NC

def page(title, body, active):
    nav = "".join(f'<a href="{h}" class="{"on" if h == active else ""}">{E(t)}</a>' for h, t in NAV)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)} · Las Vegas Strip Poker Finder</title>
<link rel="stylesheet" href="style.css"></head><body>
<header><div class="brand">Strip Poker Finder</div><nav>{nav}</nav></header>
<main>{body}</main>
<footer>Every value links to an official source. Blank values are flagged ⚑ and listed on <a href="flagged.html">Flagged for Review</a>. Data current as of 2026-11-16 (UTC). Not financial or travel advice.</footer>
</body></html>"""

def table(headers, body_rows):
    th = "".join(f"<th>{E(h)}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body_rows)
    return f'<div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'

# ---------- load data ----------
ven = rows("venetian_deepstack_iv.csv")
wd = rows("wynn_daily.csv")
ww = rows("wynn_wpt.csv")
bel = rows("bellagio.csv")
fees = rows("resort_fees.csv")

tourneys = [r for r in ven if r["kind"] == "Tournament"]
def gtd(r): return int(r["guarantee_usd"]) if r["guarantee_usd"] else 0
def bi(r): return int(r["buy_in_usd"]) if r["buy_in_usd"] else 0
tourneys.sort(key=lambda r: (-gtd(r), -bi(r), r["date"], r["time"]))

ten_am = sorted({(r["date"], r["time"], r["event_no"]) for r in ven
                 if r["kind"] != "Continuation (not an entry)" and r["time"].startswith("10:")})
earliest = min(ven, key=lambda r: (r["date"], r["time"][-2:] + r["time"]))  # diagnostic only
first_start = sorted({r["time"] for r in ven if r["kind"] != "Continuation (not an entry)"},
                     key=lambda t: (int(t.split(":")[0]) % 12 + (12 if "PM" in t else 0), int(t.split(":")[1][:2])))[0]

first_tourney_start = min((r['time'] for r in tourneys), key=lambda t:(int(t.split(':')[0])%12+(12 if 'PM' in t else 0), int(t.split(':')[1][:2])))
# ---------- pages ----------
pages = {}

pages["index.html"] = page("Summary", f"""
<section class="hero"><h1>Las Vegas Strip live poker: sourced tournament finder</h1>
<p>Official schedules and structures for the Venetian, Wynn, and Bellagio, with hotel resort fees and a day-plan. Every number links to the official page it came from. Items that could not be confirmed are blank and flagged.</p></section>
<div class="cards">
<div class="card"><b>{len(tourneys)}</b><span>Venetian tournaments (official schedule, 94 rows incl. satellites/restarts)</span></div>
<div class="card"><b>{sum(1 for r in ven if r['kind']=='Satellite')}</b><span>Venetian satellites (not main list)</span></div>
<div class="card"><b>{len(wd)+len(ww)+len(bel)}</b><span>Wynn daily / WPT and Bellagio rows, most with re-entry or add-on</span></div>
<div class="card"><b>0</b><span>Events with <i>verified</i> single-entry status</span></div>
<div class="card"><b>{first_tourney_start}</b><span>Earliest official Venetian tournament start (no 8 AM start found)</span></div>
</div>
<h2>Executive summary</h2>
<ul>
<li><b>Single-entry status is not verified for any event.</b> The Venetian structure sheets read so far do not state re-entry or add-on rules. The main list therefore shows every Venetian tournament, each marked ⚑ unverified, and no event is labelled single-entry.</li>
<li><b>Wynn daily and WPT events mostly allow re-entry, rebuys, or add-ons</b>, so they sit in the Add-on / re-entry section. Friday's $240 daily is rebuy/add-on with re-entry disallowed.</li>
<li><b>No 8 AM start is on any official schedule checked.</b> Earliest official Venetian tournament start is {first_tourney_start} (the earliest start of any kind, {first_start}, is a satellite); Wynn dailies start 12:00 PM and nightly 6:00 PM. A full-day plan cannot be built until event durations and single-entry status are confirmed.</li>
<li><b>Hotel cost and walk time cannot be ranked yet.</b> Only Wynn ($55 + tax) and Treasure Island ($49.95 + tax) resort fees are verified; no nightly room rates or walk times were captured from official sources.</li>
</ul>
<h2>Where to go next</h2>
<p>See <a href="questions.html">Questions</a> for what is still needed and how to get it, <a href="review.html">Repo review</a> for line-by-line checks and irregularities, and <a href="flagged.html">Flagged for Review</a> for every blank value.</p>
""", "index.html")

# tournaments
trows = []
for r in tourneys:
    ratio = f"{gtd(r)/bi(r):.1f}×" if gtd(r) and bi(r) else ""
    trows.append([E(r["date"]+" "+r["weekday"]), E(r["time"]), E(r["event_no"]),
                  E(r["event_name"]), E(f"${bi(r):,}") if bi(r) else cell(""),
                  E(f"${gtd(r):,}") if gtd(r) else cell(""),
                  E(ratio) if ratio else cell(""),
                  f'<span class="flag">⚑ unverified</span>',
                  link(r["source"], "schedule") + " · " + link("https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/"+r["structure_pdf"], "structure")])
pages["tournaments.html"] = page("Tournaments", f"""
<h1>Main list: Venetian DeepStack Extravaganza IV</h1>
<p class="note"><b>Filter status:</b> single-entry is <b>not verified</b> for any row, so this list cannot yet be filtered to single-entry only. Every row is shown and flagged. Sorted by prize pool, then buy-in. Starting-chip, rake, and level details are in each structure sheet.</p>
<p class="note">Ratio = guarantee ÷ buy-in. It is a comparison of two official figures, not an expected value. Satellites and day-2 restarts are excluded. Events with a 50+ age requirement are marked in the name.</p>
{table(["Date","Start","Event #","Event","Buy-in","Guarantee","GTD ÷ buy-in","Single-entry","Source"], trows)}
""", "tournaments.html")

# add-on / re-entry
arows = []
for r in wd:
    arows.append([E(r["schedule"]), E(r["time"]), E(r["event_name"]), E("$"+r["buy_in_usd"]),
                  E("$"+r["guarantee_usd"]), E(r["re_entry"]), E(r["rebuy_addon"]),
                  link(r["source"], "official page")])
wrows = []
for r in ww:
    wrows.append([E(r["dates"]), E(r["event_name"]), E("$"+r["buy_in_usd"]),
                  E("$"+r["guarantee_usd"]) if r["guarantee_usd"] else cell(""),
                  E(r["re_entry"]), link(r["source"], "official page")])
brows = []
for r in bel:
    brows.append([E(r["day"]), E(r["event_name"]), E(r["buy_in_usd"]),
                  E("$"+r["guarantee_usd"]) if r["guarantee_usd"] else cell(""),
                  E(r["re_entry"]), E(r["flag"]), link(r["source"], "official page")])
pages["addons.html"] = page("Add-on / re-entry", f"""
<h1>Add-on, rebuy, re-entry, and double-entry events</h1>
<p class="note">These are kept out of the main list because they are not single-entry. Each row shows the official entry rule. Blank rule = not captured.</p>
<h2>Wynn daily tournaments</h2>
{table(["Schedule","Start","Event","Buy-in","Guarantee","Re-entry","Rebuy / add-on","Source"], arows)}
<h2>Wynn WPT World Championship</h2>
{table(["Dates","Event","Buy-in","Guarantee","Re-entry / entry rule","Source"], wrows)}
<h2>Bellagio poker</h2>
{table(["Day","Event","Buy-in","Guarantee","Re-entry","Flag","Source"], brows)}
""", "addons.html")

# schedule
bykind = collections.defaultdict(list)
for r in ven:
    if r["kind"] != "Continuation (not an entry)":
        bykind[r["date"]].append(r)
sched_rows = []
for d in sorted(bykind)[:14]:
    evs = sorted(bykind[d], key=lambda r: (int(r["time"].split(":")[0]) % 12 + (12 if "PM" in r["time"] else 0), int(r["time"].split(":")[1][:2])))
    lst = "<br>".join(f'{E(r["time"])} · #{E(r["event_no"])} {E(r["event_name"][:70])}' for r in evs)
    sched_rows.append([E(d+" "+evs[0]["weekday"]), lst, link(evs[0]["source"], "official schedule")])
pages["schedule.html"] = page("Schedule", f"""
<h1>Schedule: start times by day</h1>
<p class="note"><b>No 8 AM start appears</b> on any official schedule checked. The earliest Venetian tournament start is {first_tourney_start}; the earliest satellite start is {first_start}. Wynn daily starts are 12:00 PM (Mon–Sun) and 6:00 PM (nightly).
A “play all day, maximize entries” plan needs each event's <b>duration</b> and <b>entry rule</b>. Neither is captured for most events, so no maximized plan is shown here.</p>
{table(["Day","Official start times (Venetian)","Source"], sched_rows)}
<p class="note">Showing the first 14 days. Full list: <a href="tournaments.html">Tournaments</a>. Continuation rows (day-2 restarts, final tables) are excluded because they are not new entries.</p>
""", "schedule.html")

# hotels
hrows = []
for name, url in [("Venetian","https://www.venetianlasvegas.com/hotel/offers.html"),
                  ("Wynn Las Vegas","https://www.wynnlasvegas.com/"),
                  ("Bellagio","https://bellagio.mgmresorts.com/en/casino/poker.html"),
                  ("Treasure Island","https://treasureisland.com/"),
                  ("Aria","https://aria.mgmresorts.com/en/casino/poker.html"),
                  ("Caesars Palace","https://www.caesars.com/caesars-palace"),
                  ("Harrah's Las Vegas","https://www.caesars.com/harrahs-las-vegas"),
                  ("Horseshoe Las Vegas","https://www.caesars.com/horseshoe-las-vegas")]:
    fee = next((f for f in fees if f["property"] == name), None)
    fee_cell = (E(fee["resort_fee_per_night"]) if fee and fee["resort_fee_per_night"] else cell(""))
    status = E(fee["status"]) if fee else NC
    hrows.append([E(name), cell(""), fee_cell, status, cell(""), cell(""), link(url, "official site") + (" · " + link(fee["source"], "fee source") if fee and fee["source"] != url else "")])
pages["hotels.html"] = page("Hotels", f"""
<h1>Hotels: resort fees and walk times</h1>
<p class="note"><b>Not ranked.</b> Nightly room rates, walk times, and quality ratings were not captured from official sources. The brief asks that cost and quality outweigh distance, and that walk time be within 30 minutes of the tournament. Neither can be checked yet, so every walk-time cell is blank.</p>
{table(["Property","Nightly room rate","Resort fee / night","Fee status","Walk to tournament (≤30 min?)","Quality rating","Source"], hrows)}
""", "hotels.html")

# questions
qs = [
 ("Single-entry status for Venetian events", "Read each Venetian structure sheet linked from the schedule (numbers 1–37 appear) for re-entry and add-on wording.", "Venetian schedule table, Structures column"),
 ("Tournament durations (needed for a maximized day plan)", "Each structure sheet lists levels and level length. Duration = levels × level minutes plus breaks. Read each sheet; no duration is computed here.", "Venetian structure sheets"),
 ("Earliest official start on or after 8 AM", "Confirm at the Venetian, Wynn, Bellagio, and MGM Grand whether any event starts before 10:10 AM. Only Wynn and Venetian schedules have been checked.", "Venetian & Wynn schedule pages"),
 ("Bellagio Saturday buy-in", "The PDF header says $1,100 and the rules say $600. Ask the Bellagio poker room, or check the current PDF revision.", "Bellagio poker page (contact details on the page)"),
 ("Bellagio start times and dates", "The Bellagio weekly PDFs give no start time or date. Use the poker page's schedule or call the room.", "bellagio.mgmresorts.com/en/casino/poker.html"),
 ("Venetian resort fee", "Confirm the per-night resort fee on a live rate page (booking flow) for a sample date. The Venetian Rewards terms do not state the amount.", "venetianlasvegas.com booking flow; Rewards terms"),
 ("Caesars Palace, Harrah's, Horseshoe resort fees", "Secondary sources conflict. Confirm on the property's own booking or terms page.", "caesars.com property pages"),
 ("Aria and MGM Grand schedules", "Aria has no online calendar; call or message @ARIAPoker. MGM Grand's poker page returned a 404 and needs a fresh official URL.", "Aria phone 702.590.7232; mgmgrand.mgmresorts.com"),
 ("Walk times and hotel-to-room distance", "Walk time is not on any official page checked. Use a route tool from each property's official address to each tournament room, and record the source link.", "Hotel address pages (official); route tool (not an official source)"),
 ("Wynn WPT NLH Turbo, World Championship, and Super Gold Million re-entry rules", "Read the WPT structures PDF chunks for these three events. Not captured.", "Wynn WPT structures PDF"),
]
QURL = {
 0: "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html",
 1: "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html",
 2: "https://www.wynnlasvegas.com/casino/poker",
 3: "https://bellagio.mgmresorts.com/en/casino/poker.html",
 4: "https://bellagio.mgmresorts.com/en/casino/poker.html",
 5: "https://www.venetianlasvegas.com/venetian-rewards/terms-and-conditions.html",
 6: "https://www.caesars.com/caesars-palace",
 7: "https://aria.mgmresorts.com/en/casino/poker.html",
 8: "https://www.venetianlasvegas.com/hotel/offers.html",
 9: "https://www.wynnlasvegas.com/casino/poker",
}
qrows = [[E(q), E(a), E(s), link(QURL[i], "official")] for i, (q, a, s) in enumerate(qs)]
pages["questions.html"] = page("Questions", f"""
<h1>Questions, missing information, and how to get it</h1>
<p class="note">These must be answered before a decision is made. Each item says where the answer comes from.</p>
{table(["Question","How to get it","Where","Source"], qrows)}
<h2>Suggestions (for later; not implemented)</h2>
<ul>
<li>Add a per-event entry-rule column that is filled only from the structure sheet (done for the Venetian schedule; rule still blank).</li>
<li>Add a schedule planner that uses durations once read from each structure sheet (not yet possible).</li>
<li>Split hotel data into a rate table once official nightly rates are captured for specific dates.</li>
</ul>
""", "questions.html")

# review
irr = [
 ("R1","Prior site's note said earliest Venetian start is 11:10 AM, with 10:10 AM only for RaceDay events 3–5.","Official table lists 10:10 AM starts for more than the RaceDay events (for example Events 24, 32, 35, 39, 47, 49, 56).", "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"),
 ("R2","Bellagio Saturday $1,000/$1,100 NLH PDF: header and rules disagree on buy-in.","Flagged, not inferred.", "https://bellagio.mgmresorts.com/en/casino/poker.html"),
 ("R3","Bellagio poker page has a stale 'resume July 26' note.","Not used. Treat as unverified.", "https://bellagio.mgmresorts.com/en/casino/poker.html"),
 ("R4","MGM Grand poker page returns 404.","Schedule unverified.", "https://mgmgrand.mgmresorts.com/en/casino/poker.html"),
 ("R5","Caesars Palace poker URL redirects to general Things To Do.","No poker or resort-fee data from it.", "https://www.caesars.com/caesars-palace/things-to-do/casino/poker"),
 ("R6","Resort-fee figures conflict across secondary sites (Caesars $49.95 vs $54.95; Venetian $55 vs $62.36).","Not recorded as verified.", "https://www.venetianlasvegas.com/venetian-rewards/terms-and-conditions.html"),
 ("R7","Prior site ratios (for example $600 buy-in / $30K = 50×) could be read as expected value.","Relabelled as GTD ÷ buy-in; not an expected value.", "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"),
 ("R8","Prior COORDINATION board still marked the research task 'in progress' after PR #1 merged.","Marked done; a correction is noted in COORDINATION.md.", "https://github.com/karagemop466-tech/Poker4/pull/1"),
 ("R9","Event 8 PKO $200 appeared absent from a structure sheet in an earlier read.","Resolved: structure_30 is the Event 8 sheet on the official page.", "https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_30.pdf"),
 ("R10","Several Venetian names had typos on the official page ('No LImit').","Corrected spelling in data; figures unchanged.", "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"),
 ("R11","Wynn daily Friday event is a rebuy/add-on event with re-entry not allowed; the others allow re-entry.","Split into Add-on / re-entry section.", "https://www.wynnlasvegas.com/casino/poker"),
 ("R12","Several other session branches in this repo claim the same research task.","Possible duplicate work; logged in COORDINATION.md. Not resolved here.", "https://github.com/karagemop466-tech/Poker4/blob/main/COORDINATION.md"),
]
irows = [[E(a), E(b), E(c), link(d, "official")] for a, b, c, d in irr]
pages["review.html"] = page("Repo review", f"""
<h1>Repo review: line-by-line check against official sources</h1>
<p class="note">Each finding names its source. Findings marked R-numbers are also listed on <a href="flagged.html">Flagged for Review</a>.</p>
{table(["ID","Finding","Action","Source"], irows)}
""", "review.html")

# flagged
frows = []
for r in ven:
    if r["entry_rule"].startswith("UNVERIFIED") and r["kind"] == "Tournament":
        frows.append([E("Venetian #"+r["event_no"]+" "+r["event_name"][:60]), "Single-entry status", link(r["source"], "schedule")])
for r in ww:
    if "NOT CAPTURED" in r["re_entry"]:
        frows.append([E(r["event_name"]), "Re-entry rule", link(r["source"], "official page")])
for r in bel:
    if r["flag"]:
        frows.append([E(r["event_name"]), E(r["flag"]), link(r["source"], "official page")])
for f in fees:
    if f["status"].startswith(("UNVERIFIED","NOT CAPTURED")):
        frows.append([E(f["property"]), "Resort fee: "+E(f["status"]), link(f["source"], "source")])
pages["flagged.html"] = page("Flagged for Review", f"""
<h1>Flagged for Review</h1>
<p class="note">These items are not confirmed from an official source. They are left blank or marked on the pages. They do not block publishing.</p>
{table(["Item","Flag","Source"], frows)}
""", "flagged.html")

for name, body in pages.items():
    (ROOT / name).write_text(body, encoding="utf-8")
print("built", len(pages), "pages;", "flagged rows", len(frows))
