#!/usr/bin/env python3
"""Build the static 'strip' site from data/events.csv and data/hotels.csv.

Every row in events.csv carries a source key that maps to an official URL below.
Computed columns (guarantee divided by buy-in) are labelled as computed.
Run:  python3 strip/build.py   (from repo root)
"""
import csv, html, os, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = HERE

SOURCES = {
    "VEN": ("Venetian official DeepStack Extravaganza IV schedule",
            "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"),
    "WPT": ("Wynn official WPT World Championship schedule (PDF)",
            "https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf"),
    "SIG": ("Wynn official Signature Series Jan 2027 schedule (PDF)",
            "https://cdn.wynnresorts.com/image/upload/v1753296112/visitwynn_pdfs_files/Poker/Wynn%20Signature%20Series/Wynn_Signature_Series_Schedule.pdf"),
    "WDAILY": ("Wynn official daily tournaments poster (PDF)",
               "https://cdn.wynnresorts.com/image/upload/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf"),
    "CAES": ("Caesars Palace official daily NLH tournament flyer 2026 (PDF)",
             "https://www.caesars.com/content/dam/empire/clv/casino/poker/tournament-schedule/clv-poker-daily-nlh-tournament-flyer-2026.pdf"),
}
WYNN_TERMS = "https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf"

FLAG_WORDS = ("confirm", "conflict", "ambiguous", "shifted", "as printed", "not available")


def esc(s):
    return html.escape(s or "", quote=True)


def money(v):
    if v in (None, ""):
        return ""
    return "${:,.0f}".format(float(v))


def load_events():
    rows = []
    with open(os.path.join(DATA, "events.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["event"] = r["event"].replace("\\$", "$")
            r["note"] = r["note"].replace("\\$", "$")
            r["buyin_v"] = float(r["buyin"]) if r["buyin"] else None
            r["gtd_v"] = float(r["gtd"]) if r["gtd"] else None
            d = r["date"]
            if d and not d[0].isdigit():
                r["day"] = d
                r["sort"] = "9999 " + r["time"] + " " + d
                r["date_label"] = "Recurring"
                r["date"] = ""
            elif d:
                dt = datetime.date.fromisoformat(d)
                r["day"] = dt.strftime("%a")
                r["sort"] = d + " " + r["time"]
                r["date_label"] = dt.strftime("%b %d, %Y").replace(" 0", " ")
            else:
                r["sort"] = "9999 " + r["time"]
                r["date_label"] = "Recurring"
            r["ratio"] = (r["gtd_v"] / r["buyin_v"]) if (r["gtd_v"] and r["buyin_v"]) else None
            r["flagged"] = any(w in r["note"].lower() for w in FLAG_WORDS) or r["venue"].startswith("Wynn Las Vegas (WPT)") and "ambig" in r["note"].lower()
            r["venue_short"] = r["venue"]
            rows.append(r)
    return rows


def load_hotels():
    with open(os.path.join(DATA, "hotels.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def src_link(key):
    label, url = SOURCES[key]
    return '<a href="%s" rel="noopener">%s</a>' % (esc(url), esc(label))


def table(headers, rows, cls="", id_=""):
    h = "".join("<th>%s</th>" % esc(x) for x in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    idattr = ' id="%s"' % id_ if id_ else ""
    return ('<div class="table-wrap"><table class="%s"%s><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (cls, idattr, h, body))


NAV = [
    ("index.html", "Overview"),
    ("tournaments.html", "Single-entry candidates"),
    ("separate.html", "Separate: add-on / rebuy / satellite"),
    ("schedule.html", "Day schedule"),
    ("hotels.html", "Hotels"),
    ("analysis.html", "Analysis"),
    ("questions.html", "Questions and gaps"),
    ("suggestions.html", "Site suggestions"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]


def page(fname, title, active, body, lead=""):
    nav = "".join('<a href="%s"%s>%s</a>' % (h, ' class="active" aria-current="page"' if h == active else "", esc(t))
                  for h, t in NAV)
    doc = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s · Las Vegas Strip Poker Planner</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body>
<header class="top"><div class="wrap">
<div class="brand">Las Vegas Strip Poker Planner <span class="tag">Research snapshot 16 Nov 2026</span></div>
<nav class="nav">%(nav)s</nav>
</div></header>
<main class="wrap">
<h1>%(title)s</h1>
%(lead)s
%(body)s
</main>
<footer class="wrap small">Independent research. Verify every value with the venue before you travel. Nothing on this site is an endorsement. Local time: Pacific.
Built from <a href="sources.html">official sources</a>; unverified items are blank and listed in <a href="flagged.html">Flagged for review</a>.</footer>
<script src="assets/filter.js"></script>
</body></html>
""" % {"title": esc(title), "nav": nav, "lead": ('<p class="lead">%s</p>' % lead) if lead else "", "body": body}
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
        f.write(doc)


def main_rows(events):
    return [e for e in events if e["category"] == "MAIN"]


def build():
    events = load_events()
    hotels = load_hotels()
    main = sorted(main_rows(events), key=lambda e: e["sort"])
    spend = sorted([e for e in events if e["category"] == "SPEND"], key=lambda e: e["sort"])
    sat = sorted([e for e in events if e["category"] == "SATELLITE"], key=lambda e: e["sort"])
    fmt = sorted([e for e in events if e["category"] == "FORMAT"], key=lambda e: e["sort"])
    dated_main = [e for e in main if e["date"]]
    earliest_main = min(dated_main, key=lambda e: e["sort"])
    earliest_any = min([e for e in events if e["date"] and e["category"] in ("MAIN", "SATELLITE", "SPEND", "FORMAT")], key=lambda e: e["sort"])
    earliest_by_time = min(dated_main, key=lambda e: (e["time"], e["sort"]))
    earliest_main_time = earliest_by_time["time"]
    venetian_earliest = min([e for e in dated_main if e["venue"] == "Venetian"], key=lambda e: e["time"])["time"]
    venues = collections.Counter(e["venue"] for e in main)
    flagged_n = sum(1 for e in main if e["flagged"])
    # Top lists (computed ratio = guarantee / buy-in; not an EV or expected prize)
    ratio_list = sorted([e for e in main if e["ratio"]], key=lambda e: -e["ratio"])
    gtd_list = sorted([e for e in main if e["gtd_v"]], key=lambda e: -e["gtd_v"])
    max_flights = []

    def row_main(e):
        flag = ' <span class="flag">confirm</span>' if e["flagged"] else ""
        ratio = ("%s×" % format(e["ratio"], ",.1f").rstrip("0").rstrip(".")) if e["ratio"] else ""
        when = ("%s %s" % (e["day"], e["date_label"])) if e["date"] else ("Recurring: " + e["day"])
        return [esc(when), esc(e["time"]), esc(e["venue"]), esc(e["event"]) + flag,
                money(e["buyin_v"]), money(e["gtd_v"]) if e["gtd_v"] else "", ratio,
                "Unverified", esc(e["note"]), src_link(e["source"])]

    # ---- tournaments.html
    th = ["Date", "Time", "Venue", "Event (official listing)", "Buy-in", "Guarantee", "Guarantee ÷ buy-in (computed)",
          "Single entry", "Notes", "Source"]
    controls = ('<div class="controls"><label>Search <input id="q" type="search" placeholder="e.g. Bounty, Dec 12, Venetian"></label>'
                '<label>Venue <select id="venue"><option value="">All</option>%s</select></label>'
                '<label>Max buy-in $ <input id="maxbuy" type="number" min="0" step="50" placeholder="any"></label>'
                '<span class="count" id="count"></span></div>') % "".join(
        '<option>%s</option>' % esc(v) for v in sorted(venues))
    body = ('<div class="notice"><b>What this list is.</b> %d official-listed events (single-day or flight entries) at Strip venues, '
            'excluding anything that adds money to your entry (add-on, rebuy, re-entry), satellites and team/eligibility formats (those are on the <a href="separate.html">separate page</a>). '
            '<b>Single-entry is not verified</b> for any row: the official listings do not show re-entry or add-on terms here, and the structure sheets were not fully reviewed. '
            'Guarantees are organiser-posted minimums, not expected or actual prize pools.</div>') % len(main)
    body += controls + table(th, [row_main(e) for e in main], cls="sortable filterable", id_="main-table")
    body += ('<p class="small">Recurring Wynn daily rows (Mon–Thu, Sat, Sun, nightly) come from a poster dated June 2026; Wynn states daily events are suspended during its series, including the WPT World Championship (Nov 27 to Dec 21). Flights ("Day 1A", "1B") are separate entries in the listing but may not be playable together; check the venue.</p>')
    page("tournaments.html", "Single-entry candidates (Strip venues)", "tournaments.html", body,
         lead="Official-listed events, sorted by date. Nothing here is certified single-entry. Use the filters to narrow.")

    # ---- separate.html
    sep = ""
    sep += "<h2>A. Add-on, rebuy, or re-entry available (spending can buy more chances)</h2>"
    sep += table(["Date", "Time", "Venue", "Event", "Buy-in", "Guarantee", "Why separated", "Source"],
                 [[esc(e["date_label"] if e["date"] else "Daily (recurring)"), esc(e["time"]), esc(e["venue"]),
                   esc(e["event"]), money(e["buyin_v"]), money(e["gtd_v"]), esc(e["note"]), src_link(e["source"])]
                  for e in spend])
    sep += ("<p class=\"small\">Caesars Palace lists an optional $50 add-on and a re-entry rule in its official flyer; these are excluded from the single-entry list. "
            "Wynn's Friday $240 event is titled 'Rebuy' on its official poster.</p>")
    sep += "<h2>B. Satellites and qualifiers (buy-in is for a seat or ticket, not a cash prize entry)</h2>"
    sep += table(["Date", "Time", "Venue", "Event", "Buy-in", "Notes", "Source"],
                 [[esc(e["day"] + " " + e["date_label"]), esc(e["time"]), esc(e["venue"]), esc(e["event"]),
                   money(e["buyin_v"]), esc(e["note"]), src_link(e["source"])] for e in sat])
    sep += "<h2>C. Team, women-only, or eligibility-restricted formats</h2>"
    sep += table(["Date", "Time", "Venue", "Event", "Buy-in", "Guarantee", "Why separated", "Source"],
                 [[esc(e["day"] + " " + e["date_label"]), esc(e["time"]), esc(e["venue"]), esc(e["event"]),
                   money(e["buyin_v"]), money(e["gtd_v"]), esc(e["note"]), src_link(e["source"])] for e in fmt])
    page("separate.html", "Separate section: add-on, rebuy, re-entry, satellites, special formats", "separate.html", sep,
         lead="These are kept out of the main list because extra spending can change your chances, or the entry is for a seat rather than a cash prize.")

    # ---- schedule.html
    day_rows = lambda d: [e for e in main if e["date"] == d]
    def plan(d, title, note):
        rows = []
        for e in sorted(day_rows(d), key=lambda x: x["time"]):
            rows.append([esc(e["time"]), esc(e["venue"]), esc(e["event"]), money(e["buyin_v"]),
                         money(e["gtd_v"]) if e["gtd_v"] else "", "Unknown (no duration published)", src_link(e["source"])])
        return "<h3>%s</h3><p class=\"small\">%s</p>" % (esc(title), esc(note)) + table(
            ["Start", "Venue", "Event", "Buy-in", "Guarantee", "Expected length", "Source"], rows)
    s = ('<div class="notice"><b>Can you play all day from 8:00 AM?</b> Not from the verified listings. '
         'The earliest single-entry candidate in the official data starts at %s (%s); the Venetian earliest is %s. '
         'No listed event starts at 8:00 or 9:00 AM. Event lengths are not published, so overlaps cannot be proven safe.</div>') % (
        esc(earliest_main_time), esc(earliest_by_time["venue"] + ", " + earliest_by_time["day"] + " " + earliest_by_time["date_label"]), esc(venetian_earliest))
    s += plan("2026-12-12", "Example: Saturday Dec 12, 2026 (busiest Strip day in the data)",
              "Pick at most one event per overlapping start time. Two venues (Venetian and Wynn) are involved; walking time between them is not verified.")
    s += plan("2026-12-17", "Example: Thursday Dec 17, 2026",
              "Venetian flights 1A and 1B of Event 56 are separate listings for the same event; choose one.")
    s += ("<h3>Planning rules used</h3><ul>"
          "<li>Only single-day or flight entries from the main list are used.</li>"
          "<li>Registration opening times are not all published. Wynn's WPT T&amp;C says registration opens 4 hours before start; Caesars says sign-ups start 1 hour before. Venetian's is not published.</li>"
          "<li>Walking distance and travel time were not verified, so the plan does not assume you can move between venues.</li></ul>")
    page("schedule.html", "Day schedule and the 8 AM question", "schedule.html", s,
         lead="A practical view of the official start times. It shows where an all-day plan breaks down.")

    # ---- hotels.html
    hrows = []
    for h in hotels:
        hrows.append([esc(h["hotel"]),
                      '<a href="%s">%s</a>' % (esc(h["poker_room_official_url"]), "Poker room page") if h["poker_room_official_url"] else "",
                      esc(h["poker_room_official_facts"]),
                      esc(h["official_address"]) or '<span class="blank">unverified</span>',
                      '<span class="blank">unverified</span>',
                      '<span class="blank">unverified</span>',
                      '<span class="blank">unverified</span>',
                      '<a href="%s">Official page</a>' % esc(h["hotel_source"]),
                      esc(h["flags"])])
    s = ('<div class="notice"><b>No hotel is ranked yet.</b> Nightly cost, resort fee, and walking time depend on dates and party size, '
         'and no official source with a dated quote was captured. Blank cells are deliberate. '
         'Rankings need your travel dates, party size, and a rate pull from each official booking page.</div>')
    s += table(["Hotel", "Poker room (official)", "Official poker room facts", "Official address", "Resort fee (per night)",
                "Nightly rate (true cost)", "Walk to each tournament (≤30 min)", "Hotel source", "Flags"], hrows)
    s += ("<h2>What a true per-night cost needs</h2><ol>"
          "<li>Dated room rate for the exact nights from the hotel's own booking engine.</li>"
          "<li>Resort fee and tax, from the official booking breakdown.</li>"
          "<li>Parking charge (self/valet) and whether poker-player rates apply (Aria and Venetian publish poker-player rate programs).</li>"
          "<li>Walking time from the hotel entrance to each poker room, from a map tool.</li></ol>")
    page("hotels.html", "Hotels near the Strip poker rooms", "hotels.html", s,
         lead="Official poker-room and address facts are shown. Price and walking fields stay blank until they can be verified for your dates.")

    # ---- analysis.html
    top_ratio = ratio_list[:10]
    top_gtd = gtd_list[:10]
    a = ('<h2>Method</h2><p>Computed columns are arithmetic only: guarantee ÷ buy-in. They are not expected value. '
         'A guarantee is a minimum the organiser promises. Actual prize pools depend on the number of entries, rake, and the structure. Field sizes are not published in these sources.</p>')
    a += "<h2>Best guarantee-to-buy-in ratios (single-entry candidates)</h2>"
    a += table(["Date", "Venue", "Event", "Buy-in", "Guarantee", "Ratio (computed)", "Source"],
               [[esc(e["day"] + " " + e["date_label"] if e["date"] else e["day"]), esc(e["venue"]), esc(e["event"]),
                 money(e["buyin_v"]), money(e["gtd_v"]), "%.0f×" % e["ratio"], src_link(e["source"])] for e in top_ratio])
    a += "<h2>Largest posted guarantees (single-entry candidates)</h2>"
    a += table(["Date", "Venue", "Event", "Buy-in", "Guarantee", "Source"],
               [[esc(e["day"] + " " + e["date_label"]), esc(e["venue"]), esc(e["event"]), money(e["buyin_v"]),
                 money(e["gtd_v"]), src_link(e["source"])] for e in top_gtd])
    a += "<h2>Key findings</h2><ul>"
    a += ("<li>Venetian DeepStack Extravaganza IV (Nov 16 to Dec 23, 2026) has %d single-entry candidate rows (Wynn's WPT has more rows, but that count includes flights), "
          "including many one-day events at $200 to $600 with $8K to $40K guarantees.</li>" % sum(1 for e in main if e["venue"] == "Venetian"))
    a += ("<li>Wynn's WPT World Championship (Nov 27 to Dec 21, 2026) lists %d candidate rows. The largest posted guarantees are the $5,000,000 WPT Prime Championship ($1,100) and the $3,000,000 Super Gold Million Mystery Bounty ($400). "
          "The $10,400 main event lists a $1,000,000 add to the prize pool from ClubWPT Gold, which the source says is not available in Nevada.</li>" % sum(1 for e in main if e["venue"].startswith("Wynn Las Vegas (WPT)")))
    a += ("<li>Wynn's Signature Series (Jan 11 to 24, 2027) lists %d candidate rows. Its structure sheet is still 'Coming Soon' on the official site.</li>" % sum(1 for e in main if e["venue"].startswith("Wynn Las Vegas (Signature)")))
    a += ("<li>Caesars Palace's daily $100 and $160 events are among the lowest-cost official listings in our data, but they carry an optional add-on and re-entry, so they sit on the separate page.</li>")
    a += ("<li>Earliest single-entry start time of day in the official data: %s. Nothing starts at 8 or 9 AM, so the 8 AM all-day plan is not supported by the official listings.</li>" % esc(earliest_main_time))
    a += ("<li>%d candidate rows carry a note that needs confirmation (conflicting or ambiguous source text). These are marked in the table.</li>" % flagged_n)
    a += "</ul>"
    page("analysis.html", "Analysis and findings", "analysis.html", a,
         lead="What the verified listings show. Every figure links to an official source row.")

    # ---- questions.html
    q = """<h2>Decisions that cannot be made yet</h2>
<table class="qa"><thead><tr><th>#</th><th>Question</th><th>Why it matters</th><th>What we have</th><th>How to resolve</th></tr></thead><tbody>
<tr><td>1</td><td>What are your travel dates and party size?</td><td>Hotel rates, resort fees, and which series overlap.</td><td>Nothing provided.</td><td>Tell us the dates. Use official booking pages to pull rates.</td></tr>
<tr><td>2</td><td>Do you want single-entry only, or will you pay for add-ons and re-entries?</td><td>Decides whether the separate page is in scope.</td><td>Single-entry is the stated filter; add-on and re-entry rules are not verified per event.</td><td>Confirm with each venue's tournament director.</td></tr>
<tr><td>3</td><td>Is each event single-entry? (Re-entry, add-on, max entries.)</td><td>The core filter. The listings do not state it.</td><td>Caesars flyer: optional add-on and re-entry. Wynn WPT T&amp;C: structure sheets per event.</td><td>Read each event's structure sheet (Venetian: structure PDF per event on its official listing; Wynn: per-event sheets) and ask staff.</td></tr>
<tr><td>4</td><td>Which Wynn daily events still run Nov 16 to 26?</td><td>The daily poster is dated June 2026 and is suspended during series.</td><td>Poster says suspended during WPT.</td><td>Call Wynn poker room (702) 770-7654 listed on official PDF.</td></tr>
<tr><td>5</td><td>What are the true nightly costs at each hotel for your dates?</td><td>Cost is the top priority in the brief.</td><td>No dated rates captured.</td><td>Pull rates and resort fees from each official booking engine.</td></tr>
<tr><td>6</td><td>What is the walking time from each hotel to each poker room?</td><td>30-minute maximum requirement.</td><td>Not verified.</td><td>Use a map walking route to each poker room entrance.</td></tr>
<tr><td>7</td><td>Horseshoe, Aria, Mandalay Bay and Resorts World: what are the current daily tournaments?</td><td>Candidates with no official schedule.</td><td>Only third-party data, which conflicts.</td><td>Call each poker room. Numbers are in the flagged list.</td></tr>
<tr><td>8</td><td>Venetian's daily tournament schedule outside DeepStack series?</td><td>Gaps between series.</td><td>Official page shows the series only.</td><td>Ask the Venetian poker room.</td></tr>
<tr><td>9</td><td>What is the ClubWPT Gold $1,000,000 added money condition?</td><td>It changes the value of the WPT main event.</td><td>Footnote says not available in Nevada.</td><td>Confirm with Wynn poker room how the added money is funded.</td></tr>
<tr><td>10</td><td>Does Wynn Signature Series (Jan 2027) keep the same structure?</td><td>Structure sheet is 'Coming Soon'.</td><td>Schedule only.</td><td>Check wynnpoker.com after the sheet is published.</td></tr>
<tr><td>11</td><td>Are you eligible for women-only, age-50+, or tag-team events?</td><td>Eligibility limits.</td><td>Stated in listings.</td><td>Your own call.</td></tr>
<tr><td>12</td><td>Should the plan include off-Strip rooms (Golden Nugget downtown, Westgate, Red Rock)?</td><td>Scope.</td><td>Excluded from this list (not on the Strip).</td><td>Decide the scope.</td></tr>
</tbody></table>"""
    page("questions.html", "Questions and information gaps", "questions.html", q,
         lead="Each question shows what is known, what is missing, and how to fill the gap.")

    # ---- suggestions.html
    sg = """<div class="notice"><b>Proposals only.</b> Nothing below has been implemented. Pick the options you want and the next step will apply only those.</div>
<table class="qa"><thead><tr><th>#</th><th>Suggestion</th><th>Benefit</th><th>Cost or risk</th><th>Choose</th></tr></thead><tbody>
<tr><td>S1</td><td>Add a date picker so the tournament table filters to your trip dates.</td><td>Shows only events you can play.</td><td>Needs your dates.</td><td>[ ] Yes [ ] No</td></tr>
<tr><td>S2</td><td>Pull dated hotel rates and resort fees from each official booking engine on a schedule.</td><td>Real per-night totals instead of blanks.</td><td>Booking engines may block automated pulls; manual refresh may be needed.</td><td>[ ] Yes [ ] No</td></tr>
<tr><td>S3</td><td>Add a walking-time column from a map API, with the route link.</td><td>Checks the 30-minute rule.</td><td>Map API key and terms of use.</td><td>[ ] Yes [ ] No</td></tr>
<tr><td>S4</td><td>Add a 'structure sheet' link and a single-entry check to every row.</td><td>Turns 'unverified' into verified for the core filter.</td><td>Manual reading of many PDFs.</td><td>[ ] Yes [ ] No</td></tr>
<tr><td>S5</td><td>Add a 'last checked' date on each row, with a stale-data warning after 7 days.</td><td>Avoids planning from old posters.</td><td>Needs ongoing checks.</td><td>[ ] Yes [ ] No</td></tr>
<tr><td>S6</td><td>Build a single 'all-day plan' builder that drops overlaps and shows travel time.</td><td>Answers the 8 AM question directly.</td><td>Needs event durations, not published.</td><td>[ ] Yes [ ] No</td></tr>
<tr><td>S7</td><td>Link this section with the root site (Venetian-focused dashboard) into one navigation.</td><td>One place for all venues.</td><td>Requires an edit to the root session's files.</td><td>[ ] Yes [ ] No</td></tr>
<tr><td>S8</td><td>Export the table as CSV for a spreadsheet.</td><td>Easy comparisons.</td><td>None.</td><td>[ ] Yes [ ] No</td></tr>
</tbody></table>"""
    page("suggestions.html", "Site improvement suggestions", "suggestions.html", sg,
         lead="Options to choose from before any change is made.")

    # ---- flagged.html
    fl = """<div class="notice"><b>Flagged for Review.</b> These are irregularities and unverified items. They do not block publication, but each one should be checked before you rely on it. Source links are included.</div>
<h2>A. Irregularities between sources</h2>
<table class="qa"><thead><tr><th>#</th><th>Item</th><th>What conflicts</th><th>Sources</th></tr></thead><tbody>
<tr><td>F1</td><td>Resorts World poker buy-ins</td><td>Third-party sources show $160, $200 and $240 daily events. No official schedule found.</td><td><a href="https://www.rwlasvegas.com/eblast/poker-invite/">Official e-blast (no schedule)</a> · <a href="https://www.pokernews.com/">PokerNews (third-party)</a> · <a href="https://www.elevatedmagazines.com/">Elevated Magazines (third-party, 2025)</a></td></tr>
<tr><td>F2</td><td>Aria daily tournament</td><td>Third-party sources show a $200 1pm event (Oct 2026), a $140 Mon-Thu event, and $240 weekend events. Official page says to call the room.</td><td><a href="https://aria.mgmresorts.com/en/casino/poker.html">Official poker page</a> · <a href="https://vegasadvantage.com/">VegasAdvantage (third-party)</a> · <a href="https://somuchpoker.com/">SoMuchPoker (third-party)</a></td></tr>
<tr><td>F3</td><td>Horseshoe daily tournaments</td><td>Official page: six daily tournament times. Third-party (Aug 2026): four daily $100 events at 9 AM, 11 AM, 2 PM and 11 PM. Buy-ins not on the official page.</td><td><a href="https://www.caesars.com/horseshoe-las-vegas/casino">Official casino page</a> · <a href="https://www.angryacespoker.com/">AngryAcesPoker (third-party)</a></td></tr>
<tr><td>F4</td><td>Mandalay Bay daily tournaments</td><td>Third-party: $60 at 1 PM and 8 PM. Official page gives hours and says call for details.</td><td><a href="https://mandalaybay.mgmresorts.com/en/casino/poker-tables.html">Official poker page</a> · <a href="https://vegasadvantage.com/">VegasAdvantage (third-party)</a></td></tr>
<tr><td>F5</td><td>Venetian daily OneDay events (outside the DeepStack series)</td><td>Third-party listings are from 2019 and a database page. Official pages show only series events.</td><td><a href="https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament.html">Official series page</a> · <a href="https://venetianpokerroom.blog/">Venetian poker blog (2019 listing)</a></td></tr>
<tr><td>F6</td><td>Caesars Palace resort fee</td><td>Third-party values: $49.95 and $54.95 a night. Not stated on the official hotel page.</td><td><a href="https://www.caesars.com/caesars-palace/hotel">Official hotel page (no fee)</a> · <a href="https://hoteltiplasvegas.com/">HotelTipLV (third-party)</a> · <a href="https://lasvegaswonders.com/">LasVegasWonders (third-party)</a></td></tr>
<tr><td>F7</td><td>Wynn resort fee</td><td>Third-party values: $55 plus tax (Oct 2026); $51 in a 2026 roundup. Not verified on an official Wynn page (the Wynn stay-policy URL we tried is gone).</td><td><a href="https://www.wynnlasvegas.com/casino/poker">Official poker page</a> · <a href="https://www.thingsvegas.com/">ThingsVegas (third-party)</a></td></tr>
<tr><td>F8</td><td>Wynn daily tournament poster date</td><td>The poster file is dated June 2026, so it may be out of date. The WPT series suspends daily events.</td><td><a href="https://cdn.wynnresorts.com/image/upload/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf">Wynn daily poster</a></td></tr>
<tr><td>F9</td><td>WPT World Championship $10,400 event</td><td>Guarantee column is blank in the source. The source states $1,000,000 added by ClubWPT Gold, and that ClubWPT Gold is not available in Nevada.</td><td><a href="https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf">Wynn WPT schedule</a></td></tr>
<tr><td>F10</td><td>WPT footnote markers</td><td>Ladies NLH: listed $1,100, footnote says entry is $11,100 with discount. PLO 6-Max, NLH 6-Max, PLO and NLH 8-Max: the footnote marker is ambiguous. 'NIH' used for NLH in two events.</td><td><a href="https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf">Wynn WPT schedule</a></td></tr>
<tr><td>F11</td><td>Signature Series layout and structure</td><td>Several rows have a shifted column layout, so guarantee and entry are read from the shifted positions. The structure sheet is 'Coming Soon'.</td><td><a href="https://cdn.wynnresorts.com/image/upload/v1753296112/visitwynn_pdfs_files/Poker/Wynn%20Signature%20Series/Wynn_Signature_Series_Schedule.pdf">Signature schedule PDF</a> · <a href="https://cdn.wynnresorts.com/image/upload/v1762299460/visitwynn_pdfs_files/Poker/Wynn%20Signature%20Series/Wynn_Signature_Series_Structures.pdf">Signature structures PDF ('Coming Soon')</a></td></tr>
<tr><td>F12</td><td>'Day 2' rows listed with a buy-in</td><td>Several WPT rows labelled 'Day 2' carry a buy-in, which may mean a separate entry or just a continuation. Kept in the main list and marked.</td><td><a href="https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf">Wynn WPT schedule</a></td></tr>
<tr><td>F13</td><td>Caesars flyer is undated</td><td>The flyer has no effective date, so it may not be current.</td><td><a href="https://www.caesars.com/content/dam/empire/clv/casino/poker/tournament-schedule/clv-poker-daily-nlh-tournament-flyer-2026.pdf">Caesars flyer</a></td></tr>
<tr><td>F14</td><td>Search results dated after today</td><td>Several third-party pages in our research carry dates later than 16 Nov 2026. Their figures were not used as primary evidence.</td><td>Multiple third-party sites (see sources).</td></tr>
</tbody></table>
<h2>B. Unverified values left blank (no official source)</h2>
<ul>
<li>All hotel nightly rates, resort fees, and walking times (see <a href="hotels.html">hotels</a>).</li>
<li>Single-entry, re-entry, and add-on status for every main-list row (structure sheets not fully reviewed).</li>
<li>Event durations and registration open times (not published for most events).</li>
<li>Field size, actual prize pools, and payouts (not published in the listings).</li>
<li>Daily tournaments for Horseshoe, Aria, Mandalay Bay, Resorts World (no official schedule in our research).</li>
</ul>
<h2>C. Not upcoming (ended before 16 Nov 2026) and excluded</h2>
<ul>
<li>Venetian WPT Fall Festival, Oct 28 to Nov 15, 2026: ended (<a href="https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament.html">official series page</a>).</li>
<li>WSOP 2026, May 26 to Jul 15 (Horseshoe and Paris): ended. Dates from third-party coverage only; the official WSOP schedule was not fetched.</li>
<li>Off-Strip or downtown rooms not included: Golden Nugget (downtown; <a href="https://www.goldennugget.com/las-vegas/casino/poker-room/">official</a>), Westgate, Green Valley Ranch, Red Rock, South Point, The Orleans. None were verified against an official page in this research.</li>
</ul>
<h2>D. Coordination note</h2>
<p>Another session (branch <code>arena/25b96c20-poker4</code>) already published a Venetian-focused dashboard at the site root. This section sits in <code>/strip/</code> so the two do not overwrite each other. The root site does not link here; see COORDINATION.md.</p>"""
    page("flagged.html", "Flagged for Review", "flagged.html", fl,
         lead="Irregularities, unverified items, and things that have ended. Publish-blocking? No. Read before relying on any row.")

    # ---- sources.html
    srcs = "<ul>"
    for k, (label, url) in SOURCES.items():
        srcs += '<li><b>%s</b>: <a href="%s">%s</a></li>' % (esc(k), esc(url), esc(url))
    srcs += ('<li><b>Wynn WPT General Terms and Conditions (structures PDF, page 1)</b>: <a href="%s">%s</a></li>' % (esc(WYNN_TERMS), esc(WYNN_TERMS)))
    srcs += ("<li><b>Wynn daily tournament general T&amp;C</b>: <a href=\"https://cdn.wynnresorts.com/image/upload/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf\">PDF</a></li>")
    srcs += ('<li><b>Venetian DeepStack page with series list</b>: <a href="https://www.venetianlasvegas.com/resort/casino/poker.html">venetianlasvegas.com/resort/casino/poker.html</a></li>')
    srcs += ('<li><b>Aria official poker page</b>: <a href="https://aria.mgmresorts.com/en/casino/poker.html">aria.mgmresorts.com</a></li>')
    srcs += ('<li><b>Mandalay Bay official poker page</b>: <a href="https://mandalaybay.mgmresorts.com/en/casino/poker-tables.html">mandalaybay.mgmresorts.com</a></li>')
    srcs += ('<li><b>Horseshoe official casino page</b>: <a href="https://www.caesars.com/horseshoe-las-vegas/casino">caesars.com/horseshoe-las-vegas/casino</a></li>')
    srcs += ('<li><b>Caesars Palace official hotel page</b>: <a href="https://www.caesars.com/caesars-palace/hotel">caesars.com/caesars-palace/hotel</a></li>')
    srcs += ('<li><b>Resorts World official e-blast</b>: <a href="https://www.rwlasvegas.com/eblast/poker-invite/">rwlasvegas.com/eblast/poker-invite</a></li>')
    srcs += "</ul>"
    srcs += ("<p>Third-party pages were used only to flag conflicts (see Flagged for Review). They are not used as values in the tables.</p>")
    page("sources.html", "Sources", "sources.html", srcs,
         lead="Official sources used for every table value. Click a link to check it yourself.")

    # ---- index.html
    ov = """<div class="cards">
<div class="card"><div class="num">%(main)d</div><div>single-entry candidate rows (official listings)</div></div>
<div class="card"><div class="num">%(venetian)d</div><div>Venetian DeepStack IV rows, Nov 16 to Dec 23</div></div>
<div class="card"><div class="num">%(wpt)d</div><div>Wynn WPT World Championship rows, Nov 27 to Dec 21</div></div>
<div class="card"><div class="num">%(spend)d</div><div>add-on, rebuy, or re-entry rows (separate)</div></div>
<div class="card"><div class="num">%(sat)d</div><div>satellite rows (separate)</div></div>
<div class="card"><div class="num">0</div><div>hotel nightly totals verified</div></div>
</div>""" % {"main": len(main), "venetian": sum(1 for e in main if e["venue"] == "Venetian"),
             "wpt": sum(1 for e in main if e["venue"].startswith("Wynn Las Vegas (WPT)")),
             "spend": len(spend), "sat": len(sat)}
    top3 = ratio_list[:3]
    top_txt = "; ".join("%s, %s, buy-in %s, guarantee %s (%s×)" % (e["day"] + " " + e["date_label"], e["event"], money(e["buyin_v"]), money(e["gtd_v"]), "{:,.0f}".format(e["ratio"])) for e in top3)
    ov += """<h2>Executive summary</h2>
<ul class="summary">
<li><b>What is live now (16 Nov 2026).</b> The Venetian's DeepStack Extravaganza IV runs Nov 16 to Dec 23 on the Strip, with one-day events at 10:10 AM, 11:10 AM, 12:10 PM, and 5:10 PM. Wynn's WPT World Championship runs Nov 27 to Dec 21; its daily events are suspended during that series.</li>
<li><b>Single-entry is not confirmed.</b> The official listings do not state re-entry or add-on rules for most events. Every main-list row is marked 'unverified'. Caesars Palace (optional add-on and re-entry) and Wynn's Friday rebuy are separated out.</li>
<li><b>Best value by ratio.</b> Highest guarantee-to-buy-in ratios on the main list: %(top)s. Ratios are arithmetic, not expected value. See <a href="analysis.html">Analysis</a>.</li>
<li><b>The 8 AM plan does not work from verified data.</b> The earliest single-entry start is %(early)s (Wynn WPT); Venetian's earliest is %(venearly)s. Event lengths are not published, so back-to-back play cannot be confirmed.</li>
<li><b>Hotels cannot be ranked yet.</b> No dated rate, resort fee, or walking time is verified. Blanks are intentional. Official poker-room facts are on the <a href="hotels.html">Hotels</a> page.</li>
<li><b>Coverage gaps.</b> Horseshoe, Aria, Mandalay Bay, and Resorts World have no official daily schedule in our research. Their values are flagged, not filled in.</li>
</ul>
<h2>Start here</h2>
<div class="cards nav-cards">
<a class="card link" href="tournaments.html"><b>Single-entry candidates</b><span>Filterable table of the main list</span></a>
<a class="card link" href="separate.html"><b>Separate section</b><span>Add-on, rebuy, satellite, format</span></a>
<a class="card link" href="schedule.html"><b>Day schedule</b><span>What an 8 AM start looks like</span></a>
<a class="card link" href="hotels.html"><b>Hotels</b><span>Official facts, blanks flagged</span></a>
<a class="card link" href="questions.html"><b>Questions</b><span>What must be answered before deciding</span></a>
<a class="card link" href="flagged.html"><b>Flagged for review</b><span>Irregularities, unverified, ended</span></a>
</div>
<p class="small">Also see the root-level Venetian dashboard (another session's work) at <a href="../">the main site</a>.</p>""" % {"top": top_txt, "early": earliest_main_time, "venearly": venetian_earliest}
    page("index.html", "Overview", "index.html", ov,
         lead="A research dashboard for poker tournaments on or near the Las Vegas Strip, with every value linked to an official source.")


if __name__ == "__main__":
    build()
    print("built")
