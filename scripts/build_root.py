#!/usr/bin/env python3
"""Build the root GitHub Pages site from data/*.json.

Run:  python3 scripts/build_root.py

Every table row links to an official source keyed in data/sources.json.
Blank values stay blank and are flagged, never inferred.
"""
import datetime as dt
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CHECKED = "2026-11-16"


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


TOURN = load("tournaments.json")
HOTELS = load("hotels.json")
SOURCES = load("sources.json")
FLAGGED = load("flagged.json")

SRC = TOURN["sources"]
MONITORS = SOURCES.get("monitor_registry", [])
E = html.escape


def src(sid):
    if not sid or sid not in SRC:
        return None
    return SRC[sid]


def src_links(sids):
    if not sids:
        return "<em>none</em>"
    parts = []
    for s in sids:
        s = src(s)
        if s:
            parts.append(f"<a class='source-link' href='{E(s['url'])}' target='_blank' rel='noopener'>{E(s.get('label', s))}</a>")
    return " <br> ".join(parts) if parts else "<em>none</em>"


def pill(status):
    if status == "confirmed":
        return "<span class='pill'>Confirmed</span>"
    if status == "not_applicable":
        return "<span class='pill amb'>n/a</span>"
    return "<span class='pill warn'>Unverified</span>"


def money(v):
    if v is None:
        return "<span class='unknown'>—</span>"
    return f"${v:,.0f}"


def parse_day(iso):
    """Return a date object from 'Wed Nov 18, 2026' or ISO format."""
    if not iso:
        return None
    s = iso.strip()
    for fmt in ("%a %b %d, %Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def date_label(iso):
    d = parse_day(iso)
    if not d:
        return iso or ""
    return d.strftime("%a %b %-d, %Y")


def iso_date_only(iso):
    d = parse_day(iso)
    return d.isoformat() if d else ""


def nav(active):
    items = [
        ("index.html", "Executive brief"),
        ("tournaments.html", "Tournaments"),
        ("schedule.html", "Day plan"),
        ("hotels.html", "Hotels & cost"),
        ("venetian.html", "Venetian"),
        ("wynn.html", "Wynn"),
        ("others.html", "Other venues"),
        ("review.html", "Flagged for review"),
        ("questions.html", "Questions & answers"),
        ("suggestions.html", "Suggestions"),
        ("sources.html", "Sources & changes"),
    ]
    links = "".join(
        f"<a href='{h}' class='{'active' if h == active else ''}'>{E(t)}</a>"
        for h, t in items
    )
    return f"<div class='nav-inner'>{links}</div>"


def header(title, active, stamp="Research snapshot · 16 Nov 2026 UTC"):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)} — Strip Poker Planner</title><link rel="stylesheet" href="style.css"><script defer src="app.js"></script></head><body>
<header class="topbar"><a class="brand" href="index.html">♠ STRIP POKER PLANNER</a><span class="stamp">{stamp}</span></header>
<nav class="nav">{nav(active)}</nav>
<main><p class="eyebrow">Strip Poker Planner · official-source snapshot</p><h1>{E(title)}</h1>"""


def footer(extra=""):
    return f"""{extra}
<footer class="footer">All values are a point-in-time snapshot ({CHECKED} UTC), not a guarantee that events or rooms remain unchanged. Blank = not verified against an official source; nothing is inferred. <a href="sources.html">Sources & change log ↗</a> · <a href="review.html">Flagged for review ↗</a><br>Reconfirm with the venue before any nonrefundable booking.</footer></main></body></html>"""


def toolbar(search_placeholder="Filter this table…"):
    return f"""<div class="toolbar"><span style="font-size:12px;color:var(--muted)">Search across this table</span><input id="table-search" type="search" placeholder="{E(search_placeholder)}" aria-label="Filter table"></div>"""


SE = TOURN["entry_rules_unverified"]
RE = TOURN["reentry_or_addon"]

# distinct dates for the date filter
DATES = sorted({iso_date_only(r.get("day")) for r in SE + RE if r.get("day") and iso_date_only(r.get("day"))})


def event_rule_chip(r):
    rf = r.get("rule_fields", {})
    bits = [
        f"Single entry {pill(rf.get('single_entry', {}).get('status','unverified'))}",
        f"Re-entry {pill(rf.get('reentry', {}).get('status','unverified'))}",
        f"Add-on {pill(rf.get('addon', {}).get('status','unverified'))}",
        f"Fee {money(rf.get('fee', {}).get('value'))} {pill(rf.get('fee', {}).get('status','unverified'))}",
        f"Total {money(rf.get('total_entry_fee', {}).get('value'))} {pill(rf.get('total_entry_fee', {}).get('status','unverified'))}",
        f"Checked {r.get('last_checked', CHECKED)}",
    ]
    return " · ".join(bits)


def rule_detail_rows(rows, key_prefix):
    out = []
    for i, r in enumerate(rows):
        rf = r.get("rule_fields", {})
        cid = f"{key_prefix}-{i}"
        out.append(f"""<tr>
<td><b>{E(r.get('day',''))}</b> {E(r.get('time',''))} · {E(r.get('event',''))} {E(r.get('name',''))}</td>
<td>{E(r.get('venue',''))}</td>
<td><b>Single entry:</b> {rf.get('single_entry',{}).get('value','—')} ({pill(rf.get('single_entry',{}).get('status','unverified'))})<br><b>Re-entry:</b> {rf.get('reentry',{}).get('value','—')} ({pill(rf.get('reentry',{}).get('status','unverified'))})<br><b>Add-on:</b> {rf.get('addon',{}).get('value','—')} ({pill(rf.get('addon',{}).get('status','unverified'))})</td>
<td><b>Fee:</b> {money(rf.get('fee',{}).get('value'))} ({pill(rf.get('fee',{}).get('status','unverified'))})<br><b>Total entry fee:</b> {money(rf.get('total_entry_fee',{}).get('value'))} ({pill(rf.get('total_entry_fee',{}).get('status','unverified'))})</td>
<td>{E(rf.get('single_entry',{}).get('excerpt',''))}</td>
<td>{E(rf.get('reentry',{}).get('excerpt',''))}</td>
<td>{E(rf.get('addon',{}).get('excerpt',''))}</td>
<td>{E(rf.get('fee',{}).get('source','') or '')}<br>{E(rf.get('total_entry_fee',{}).get('source','') or '')}</td>
<td>{r.get('retrieval_date', CHECKED)}</td>
<td>{src_links(r.get('sources', []))}</td>
</tr>""")
    return "".join(out)


def group_by_date(rows):
    groups = {}
    for r in rows:
        d = iso_date_only(r.get("day"))
        groups.setdefault(d, []).append(r)
    return groups


# ============================ INDEX ============================

def build_index():
    body = f"""
<section class="hero">
<p class="eyebrow">Decision dashboard · official-source snapshot</p>
<h1>Vegas poker, organized for a real decision.</h1>
<p>Upcoming tournament dates, verified buy-ins and guarantees, hotel-fee math, and unresolved entry rules—kept separate so an attractive guarantee or low room rate is not mistaken for a confirmed value.</p>
<div class="hero-actions"><a class="button" href="tournaments.html">Review upcoming tournaments</a><a class="button ghost" href="review.html">See what is unverified</a></div>
</section>

<div class="stats">
<div class="stat"><span>Dated tournament listings reviewed</span><b>{len(SE) + len(RE)}</span><span>Venetian DSE IV, Nov 16 – Dec 23, 2026 (official calendar)</span></div>
<div class="stat"><span>Verified single-entry events</span><b>0</span><span>Official structures do not state freezeout / re-entry terms</span></div>
<div class="stat"><span>Earliest listed start</span><b>10:10 AM</span><span>Not 8:00 AM in this verified series</span></div>
<div class="stat"><span>Confirmed resort fee</span><b>$55 + tax</span><span>Venetian / Palazzo, per night (official)</span></div>
</div>

<div class="calc">
<h3>Estimated cost of a trip</h3>
<p class="muted">Formula: entries × buy-in + nights × true hotel cost/night. True cost/night = base rate + mandatory resort fee + 13.38% Clark County tax (+ parking if driving). Fill in your plan; blanks stay blank.</p>
<div class="row">
<div><label>Tournament entries</label><input type="number" id="calc-entries" value="1" min="0"></div>
<div><label>Buy-in per entry ($)</label><input type="number" id="calc-buyin" value="300" min="0" step="10"></div>
<div><label>Nights</label><input type="number" id="calc-nights" value="3" min="0"></div>
<div><label>Base room rate / night ($)</label><input type="number" id="calc-rate" value="0" min="0" step="10"></div>
</div>
<div class="row">
<div><label>Resort fee / night ($)</label><input type="number" id="calc-fee" value="55" min="0" step="5"></div>
<div><label>Tax rate (%)</label><input type="number" id="calc-tax" value="13.38" min="0" step="0.01"></div>
<div><label>Parking / night ($)</label><input type="number" id="calc-park" value="0" min="0" step="5"></div>
</div>
<div class="out" id="calc-out">Total trip cost: <b id="calc-total">$0</b> · True hotel cost/night: <b id="calc-nightly">$0</b></div>
<p class="note">Use the Venetian rate only after an official quote for your dates; $55 fee + tax is confirmed, room rate is not. This is an estimate, not a booking quote.</p>
</div>

<section class="section"><h2>Executive summary</h2>
<div class="callout danger"><strong>Eligibility is not established.</strong> No tournament in this snapshot is certified single-entry. The Venetian’s public structures give buy-ins, fees and late-registration cutoffs, but reviewed one-day sheets do not state whether re-entry, rebuy or add-on is permitted. Absence of a statement is not evidence of a freezeout.</div>
<ul>
<li><b>Series:</b> Venetian DeepStack Extravaganza IV, Nov 16 – Dec 23, 2026 (official calendar). Advertised aggregate &gt;$3.6M in guarantees is not a per-event promise.</li>
<li><b>Cost-conscious candidates:</b> $200–$600 Venetian one-day NLH events; guarantees $8,000–$40,000. Guarantee ÷ buy-in is shown as arithmetic only, never as expected value.</li>
<li><b>Kept separate:</b> events with re-entry, rebuy, add-on, bounty, multi-flight or conditional pricing (Caesars daily, Wynn daily/nightly, Wynn Friday rebuy, Bellagio weekly, Venetian flights/bounties).</li>
<li><b>Schedule:</b> no verified start before 10:10 AM; an 8 AM all-day plan is not supported by verified listings. Same-day overlap is possible because end times are not published.</li>
<li><b>Hotels:</b> Venetian is the event host; $55 resort fee + tax confirmed. Date-specific room rates, walking times, and quality comparisons are not verified.</li>
</ul>
<p><strong>Decision order:</strong> confirm entry rules → pick dates → compare surviving events → price itemized hotel totals → verify the walking route → book last.</p>
</section>

<section class="section"><h2>Go to</h2>
<div class="grid">
<a class="card" href="tournaments.html"><span class="tag">Tournaments</span><h3>Upcoming events</h3><p>Search, filter by date, toggle single-entry view, compare buy-in vs guarantee.</p></a>
<a class="card" href="schedule.html"><span class="tag">Day plan</span><h3>Schedule fit</h3><p>Day-by-day blocks, overlap flags, primary event + conditional fallback per day.</p></a>
<a class="card" href="hotels.html"><span class="tag">Hotels &amp; cost</span><h3>Stay</h3><p>Venue hotel pages, dated rate log, true cost/night calculator, walk filter.</p></a>
<a class="card" href="review.html"><span class="tag">Review</span><h3>Flagged for review</h3><p>Every unresolved item, irregularity, and the official source checked.</p></a>
<a class="card" href="questions.html"><span class="tag">Q&amp;A</span><h3>Questions &amp; answers</h3><p>What must be resolved before a decision can reasonably be made.</p></a>
<a class="card" href="suggestions.html"><span class="tag">Suggestions</span><h3>Site improvements</h3><p>Options to choose from before any change is implemented.</p></a>
</div>
</section>
"""
    open("index.html", "w", encoding="utf-8").write(header("Executive brief", "index.html") + body + footer())


# ============================ TOURNAMENTS ============================

def build_tournaments():
    se_rows = []
    for r in SE:
        rf = r.get("rule_fields", {})
        ratio = "—"
        if r.get("guarantee") and r.get("buy_in"):
            ratio = f"{r['guarantee'] / r['buy_in']:.1f}×"
        se_rows.append(f"""<tr>
<td>{date_label(r.get('day'))}</td>
<td>{E(r.get('time',''))}</td>
<td>{E(r.get('event',''))}</td>
<td>{E(r.get('name',''))}</td>
<td>{money(r.get('buy_in'))}</td>
<td>{money(r.get('guarantee'))}</td>
<td><span class="muted">{ratio}</span></td>
<td>{E(r.get('format',''))}</td>
<td>{event_rule_chip(r)}</td>
<td>{money(rf.get('total_entry_fee',{}).get('value'))}</td>
<td>{r.get('last_checked', CHECKED)}</td>
<td>{src_links(r.get('sources', []))}</td>
</tr>""")

    re_rows = []
    for r in RE:
        rf = r.get("rule_fields", {})
        ratio = "—"
        if r.get("guarantee") and r.get("buy_in"):
            ratio = f"{r['guarantee'] / r['buy_in']:.1f}×"
        re_rows.append(f"""<tr>
<td>{date_label(r.get('day'))}</td>
<td>{E(r.get('time',''))}</td>
<td>{E(r.get('event',''))}</td>
<td>{E(r.get('name',''))}</td>
<td>{money(r.get('buy_in'))}</td>
<td>{money(r.get('guarantee'))}</td>
<td><span class="muted">{ratio}</span></td>
<td>{E(r.get('format',''))}</td>
<td>{event_rule_chip(r)}</td>
<td>{money(rf.get('total_entry_fee',{}).get('value'))}</td>
<td>{r.get('last_checked', CHECKED)}</td>
<td>{src_links(r.get('sources', []))}</td>
</tr>""")

    body = f"""
<p class="lede">All upcoming listings from the sourced Strip rooms, Nov 16 – Dec 23, 2026 window. <strong>Nothing here is ranked as single-entry until official rules confirm it.</strong> Blank = value not printed by the official source checked.</p>
{toolbar()}
<div class="status-line">
<span id="count-se"><b>{len(SE)}</b> candidate rows</span>
<span id="count-re"><b>{len(RE)}</b> separate rows</span>
<span class="pill" id="filter-chip">All</span>
</div>

<section class="section"><h2>1 · Strict single-entry focus (candidate — entry rules unverified)</h2>
<p class="muted">Plain one-day NLH listings. None is confirmed freezeout; use the toggle below to show only rows whose entry rules are confirmed (currently none). Use the date filter to show only chosen days.</p>
<div class="toolbar"><span style="font-size:12px;color:var(--muted)">Single-entry confirmed filter</span><label class="chip" id="chip-se" role="checkbox" aria-checked="false">Only verified single-entry</label> <span style="font-size:12px;color:var(--muted)">Date</span><div id="date-chips"></div></div>
<div class="table-wrap"><table class="tournament-table"><thead><tr><th>Date</th><th>Start</th><th>Event #</th><th>Tournament</th><th>Buy-in</th><th>Guaranteed pool</th><th>GTD ÷ buy-in (arithmetic)</th><th>Format</th><th>Entry rules (last checked)</th><th>Total entry fee</th><th>Last checked</th><th>Official sources</th></tr></thead><tbody id="tbl-se">{"".join(se_rows) or '<tr><td colspan="12">No rows.</td></tr>'}</tbody></table></div>
<div id="rule-detail-se"><h3>Structured rule fields (excerpt + source per event)</h3><div class="table-wrap"><table><thead><tr><th>Event</th><th>Venue</th><th>Single entry / re-entry / add-on</th><th>Fee / total entry fee</th><th>Single-entry excerpt</th><th>Re-entry excerpt</th><th>Add-on excerpt</th><th>Fee source</th><th>Retrieved</th><th>Sources</th></tr></thead><tbody>{rule_detail_rows(SE, 'se')}</tbody></table></div></div>
</section>

<section class="section"><h2>2 · Separate: re-entry / rebuy / add-on / bounty / flight / conditional-price events</h2>
<p class="muted">Kept out of the single-entry focus. These let you pay again (re-entry/rebuy), buy chips (add-on), or play formats where extra spend changes the structure (bounties, flights with shared Day 2, member discounts). Labelled per format, not ranked against the candidate group.</p>
<div class="table-wrap"><table class="tournament-table"><thead><tr><th>Date</th><th>Start</th><th>Event #</th><th>Tournament</th><th>Buy-in</th><th>Guaranteed pool</th><th>GTD ÷ buy-in (arithmetic)</th><th>Format</th><th>Entry rules (last checked)</th><th>Total entry fee</th><th>Last checked</th><th>Official sources</th></tr></thead><tbody id="tbl-re">{"".join(re_rows) or '<tr><td colspan="12">No rows.</td></tr>'}</tbody></table></div>
<div id="rule-detail-re"><h3>Structured rule fields (excerpt + source per event)</h3><div class="table-wrap"><table><thead><tr><th>Event</th><th>Venue</th><th>Single entry / re-entry / add-on</th><th>Fee / total entry fee</th><th>Single-entry excerpt</th><th>Re-entry excerpt</th><th>Add-on excerpt</th><th>Fee source</th><th>Retrieved</th><th>Sources</th></tr></thead><tbody>{rule_detail_rows(RE, 're')}</tbody></table></div></div>
</section>

<p class="muted">Ratio = official guaranteed pool ÷ total entry fee. It is a descriptive comparison aid only, not a forecast, odds, or expected value. Multi-flight guarantees pool many potential entries; bounty guarantees may include bounty payments. Compare bounty and flight rows separately.</p>
"""
    open("tournaments.html", "w", encoding="utf-8").write(header("Tournaments", "tournaments.html") + body + footer())


# ============================ SCHEDULE ============================

def build_schedule():
    groups = group_by_date(SE)
    blocks = []
    for d in sorted(groups):
        evs = sorted(groups[d], key=lambda r: (r.get("time") or ""))
        rows = []
        for r in evs:
            rows.append(f"""<tr><td>{E(r.get('time',''))}</td><td>{E(r.get('event',''))} {E(r.get('name',''))}</td><td>{money(r.get('buy_in'))}</td><td>{money(r.get('guarantee'))}</td><td>{event_rule_chip(r)}</td><td>{src_links(r.get('sources', []))}</td></tr>""")
        # overlap logic: if more than one event same day and start times within unknown duration -> flag
        overlap = len(evs) > 1
        primary = evs[0]
        fallback = evs[1] if len(evs) > 1 else None
        if fallback:
            fallback_html = f"""<p><strong>Conditional fallback:</strong> {E(date_label(fallback.get('day')))} {E(fallback.get('time',''))} · {E(fallback.get('name',''))} · only if the primary event ends or the player busts before {E(fallback.get('time',''))}; end times are not published so same-day play of both is flagged as uncertain.</p>"""
        else:
            fallback_html = "<p><em>No second listing this day; no fallback needed.</em></p>"
        overlap_html = ""
        if overlap:
            overlap_html = f"""<div class="callout danger"><strong>Overlap flag:</strong> This day lists {len(evs)} events. Finish times and re-entry rules are not in the official data reviewed, so two same-day events <strong>cannot be treated as playable in sequence</strong>. Treat the day as a menu, not a fixed plan.</div>"""
        kind = "pill warn" if overlap else "pill blue"
        kind_text = "Multiple listings — overlap possible" if overlap else "One listing"
        blocks.append(f"""<div class="schedule-block">
<h3>{E(date_label(d))} <span class="{kind}">{kind_text}</span></h3>
<p><strong>Primary event:</strong> {E(date_label(primary.get('day')))} {E(primary.get('time',''))} · {E(primary.get('name',''))} · {money(primary.get('buy_in'))} · {money(primary.get('guarantee'))} guarantee. {src_links(primary.get('sources', []))}</p>
{fallback_html}
{overlap_html}
<table><thead><tr><th>Start</th><th>Event</th><th>Buy-in</th><th>Guarantee</th><th>Entry rules</th><th>Sources</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
</div>""")
    if not blocks:
        blocks = ["<p>No dated events in this window.</p>"]

    body = f"""
<p class="lede">One primary event per day first; add an evening event only where the player can realistically exit the earlier event. Start times and late-registration cutoffs are published; finish times are not, so same-day pairs are flagged as possible overlaps.</p>
<div class="callout danger"><strong>8:00 AM start not supported.</strong> The earliest listed start in this verified Venetian series is 10:10 AM. No 8:00 AM event is confirmed; other venues would need to be checked directly.</div>
{"".join(blocks)}
<section class="section"><h2>Same-day overlap watch</h2>
<div class="table-wrap"><table><thead><tr><th>Day</th><th>Listings</th><th>Overlap flag</th><th>Guidance</th></tr></thead><tbody>
<tr><td>Thu Nov 26</td><td>#12 $300 NLH 11:10 AM · #13 $200 Bounty 5:10 PM</td><td class="pill warn">Possible</td><td>#12 registration closes ~4:55 PM; if still playing, #13 at 5:10 PM conflicts.</td></tr>
<tr><td>Fri Nov 27</td><td>#14 $600 NLH 11:10 AM · #15 $200 Bounty 5:10 PM</td><td class="pill warn">Possible</td><td>Same caveat; #14 is the higher-value event of the pair.</td></tr>
</tbody></table></div>
<p class="muted">Undated daily Wynn rows and multi-day Day 2 restarts appear on the Tournaments page; they are not placed here because their confirmed dates are not fixed.</p>
</section>
"""
    open("schedule.html", "w", encoding="utf-8").write(header("Day plan", "schedule.html") + body + footer())


# ============================ HOTELS ============================

def build_hotels():
    rows = []
    for h in HOTELS["hotels"]:
        log = h.get("rate_log", [])
        last = log[-1] if log else {}
        fee = last.get("resort_fee")
        rate = last.get("rate")
        tax = last.get("tax_rate")
        nightly = None
        if isinstance(rate, (int, float)) and isinstance(fee, (int, float)) and isinstance(tax, (int, float)):
            nightly = (rate + fee) * (1 + tax)
        rows.append(f"""<tr>
<td><b>{E(h['property'])}</b></td>
<td>{E(h.get('poker_location',''))}</td>
<td>{money(fee) if isinstance(fee,(int,float)) else '<span class="unknown">—</span>'}</td>
<td>{money(rate) if isinstance(rate,(int,float)) else '<span class="unknown">—</span>'}</td>
<td>{f"{tax*100:.2f}%" if isinstance(tax,(int,float)) else '<span class="unknown">—</span>'}</td>
<td>{money(nightly) if nightly is not None else '<span class="unknown">—</span>'}</td>
<td>{money(h.get('checkout_total')) if isinstance(h.get('checkout_total'),(int,float)) else '<span class="unknown">—</span>'}</td>
<td>{money(h.get('nightly_average')) if isinstance(h.get('nightly_average'),(int,float)) else '<span class="unknown">—</span>'}</td>
<td>{E(str(h.get('parking'))) if h.get('parking') is not None else '<span class="unknown">—</span>'}</td>
<td>{E(str(h.get('cancellation_deadline'))) if h.get('cancellation_deadline') else '<span class="unknown">—</span>'}</td>
<td>{last.get('timestamp','')[:10]}</td>
<td>{src_links(h.get('sources', []))}</td>
</tr>""")

    # per-venue rate logs
    log_sections = []
    for h in HOTELS["hotels"]:
        logs = h.get("rate_log", [])
        lr = ""
        for lg in logs:
            nightly = None
            if isinstance(lg.get("rate"),(int,float)) and isinstance(lg.get("resort_fee"),(int,float)) and isinstance(lg.get("tax_rate"),(int,float)):
                nightly = (lg["rate"] + lg["resort_fee"]) * (1 + lg["tax_rate"])
            tax_txt = f"{lg['tax_rate']*100:.2f}%" if isinstance(lg.get('tax_rate'),(int,float)) else '<span class="unknown">—</span>'
            lr += f"""<tr><td>{lg.get('date','')}</td><td>{money(lg.get('rate')) if isinstance(lg.get('rate'),(int,float)) else '<span class="unknown">—</span>'}</td><td>{money(lg.get('resort_fee')) if isinstance(lg.get('resort_fee'),(int,float)) else '<span class="unknown">—</span>'}</td><td>{tax_txt}</td><td>{money(nightly) if nightly is not None else '<span class="unknown">—</span>'}</td><td>{lg.get('timestamp','')}</td><td>{E(lg.get('note',''))}</td><td>{src_links([lg.get('source')] if lg.get('source') else [] )}</td></tr>"""
        log_sections.append(f"""<div class="section"><h3>{E(h['property'])} · dated rate log</h3>
<p class="muted">{E(h.get('notes',''))}</p>
<div class="table-wrap"><table class="rate-log"><thead><tr><th>Log date</th><th>Base rate</th><th>Resort fee</th><th>Tax</th><th>True cost/night</th><th>Rate timestamp</th><th>Note</th><th>Source</th></tr></thead><tbody>{lr or '<tr><td colspan="8">No dated rate entries.</td></tr>'}</tbody></table></div>
<p><strong>Checkout total:</strong> {money(h.get('checkout_total')) if isinstance(h.get('checkout_total'),(int,float)) else '<span class="unknown">—</span>'} &nbsp;·&nbsp; <strong>Nightly average:</strong> {money(h.get('nightly_average')) if isinstance(h.get('nightly_average'),(int,float)) else '<span class="unknown">—</span>'} &nbsp;·&nbsp; <strong>Parking:</strong> {E(str(h.get('parking'))) if h.get('parking') is not None else '<span class="unknown">—</span>'} &nbsp;·&nbsp; <strong>Cancellation deadline:</strong> {E(str(h.get('cancellation_deadline'))) if h.get('cancellation_deadline') else '<span class="unknown">—</span>'}</p>
</div>""")

    body = f"""
<p class="lede">Priority per the brief: cost and quality first, then distance (must still be ≤ 30 minutes walking). True nightly cost = base rate + mandatory resort fee + 13.38% Clark County tax; checkout total adds nights, parking and mandatory fees. Rates are a dated log, not a single value.</p>
<div class="calc">
<h3>True cost per night &amp; trip total</h3>
<p class="muted">Calculator works for any property: true cost/night = rate + resort fee + tax + parking. Trip total adds entries × buy-in.</p>
<div class="row">
<div><label>Base room rate / night ($)</label><input type="number" id="hotel-rate" value="0" min="0" step="10"></div>
<div><label>Resort fee / night ($)</label><input type="number" id="hotel-fee" value="0" min="0" step="5"></div>
<div><label>Tax rate (%)</label><input type="number" id="hotel-tax" value="13.38" min="0" step="0.01"></div>
<div><label>Parking / night ($)</label><input type="number" id="hotel-park" value="0" min="0" step="5"></div>
</div>
<div class="row">
<div><label>Nights</label><input type="number" id="hotel-nights" value="1" min="0"></div>
<div><label>Tournament entries</label><input type="number" id="hotel-entries" value="0" min="0"></div>
<div><label>Buy-in per entry ($)</label><input type="number" id="hotel-buyin" value="0" min="0" step="10"></div>
</div>
<div class="out" id="hotel-out">True cost/night: <b id="hotel-nightly">$0</b> · Stay hotel total: <b id="hotel-stay">$0</b> · Entries: <b id="hotel-entries-cost">$0</b> · Grand total: <b id="hotel-grand">$0</b></div>
<p class="note">Venetian: $55 fee + tax confirmed at snapshot; room rate not confirmed for any date — enter your quoted rate. Official booking: <a class="button" style="font-size:12px;padding:6px 10px" href="https://www.venetianlasvegas.com/book" target="_blank" rel="noopener">Check official rates ↗</a></p>
</div>

<div class="toolbar"><span style="font-size:12px;color:var(--muted)">Walking filter</span><label class="chip" id="chip-walk" role="checkbox" aria-checked="false">Show ≤ 30 min walk only</label> <span style="font-size:12px;color:var(--muted)" id="walk-note">Walking times not verified for any route — filter matches nothing yet.</span></div>

<section class="section"><h2>Candidate hotels (on-site poker rooms)</h2>
<div class="table-wrap"><table><thead><tr><th>Property</th><th>Poker room location (official)</th><th>Resort fee / night</th><th>Base rate</th><th>Tax</th><th>True cost/night</th><th>Checkout total</th><th>Nightly average</th><th>Parking</th><th>Cancellation</th><th>Rate logged</th><th>Official sources</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
</section>

{"".join(log_sections)}

<section class="section"><h2>Walking-distance check (≤ 30 min)</h2>
<p class="muted">Each candidate's poker room is inside the same resort, so the route is internal. No official walking-time source was read, so every route is flagged unverified and the ≤30-minute filter shows nothing until a route time is confirmed from an official property map or directions.</p>
<div class="callout danger"><strong>Walk limit not confirmed.</strong> No door-to-door walking minutes were read from an official source for any hotel. Distance is left blank rather than estimated.</div>
</section>
"""
    open("hotels.html", "w", encoding="utf-8").write(header("Hotels & cost", "hotels.html") + body + footer())


# ============================ VENUE PAGES ============================

def hotel_block(h):
    log = h.get("rate_log", [])
    last = log[-1] if log else {}
    fee = last.get("resort_fee"); rate = last.get("rate"); tax = last.get("tax_rate")
    nightly = None
    if isinstance(rate,(int,float)) and isinstance(fee,(int,float)) and isinstance(tax,(int,float)):
        nightly = (rate + fee) * (1 + tax)
    return f"""<div class="venue"><header><h2>{E(h['property'])} — hotel</h2></header><div class="body">
<p class="muted">{E(h.get('poker_location',''))}</p>
<div class="table-wrap"><table><thead><tr><th>Logged date</th><th>Base rate</th><th>Resort fee</th><th>Tax</th><th>True cost/night</th><th>Rate timestamp</th><th>Official sources</th></tr></thead><tbody>
<tr><td>{last.get('date','—')}</td><td>{money(rate) if isinstance(rate,(int,float)) else '<span class="unknown">—</span>'}</td><td>{money(fee) if isinstance(fee,(int,float)) else '<span class="unknown">—</span>'}</td><td>{f"{tax*100:.2f}%" if isinstance(tax,(int,float)) else '<span class="unknown">—</span>'}</td><td>{money(nightly) if nightly is not None else '<span class="unknown">—</span>'}</td><td>{last.get('timestamp','—')}</td><td>{src_links(h.get('sources',[]))}</td></tr>
</tbody></table></div>
<p><strong>Checkout total:</strong> {money(h.get('checkout_total')) if isinstance(h.get('checkout_total'),(int,float)) else '<span class="unknown">—</span>'} &nbsp;·&nbsp; <strong>Nightly average:</strong> {money(h.get('nightly_average')) if isinstance(h.get('nightly_average'),(int,float)) else '<span class="unknown">—</span>'} &nbsp;·&nbsp; <strong>Parking:</strong> {E(str(h.get('parking'))) if h.get('parking') is not None else '<span class="unknown">—</span>'} &nbsp;·&nbsp; <strong>Cancellation deadline:</strong> {E(str(h.get('cancellation_deadline'))) if h.get('cancellation_deadline') else '<span class="unknown">—</span>'}</p>
<p class="note">Full dated rate log and the walk filter are on <a href="hotels.html">Hotels &amp; cost ↗</a>.</p>
</div></div>"""


def build_venue(slug, title, venue_name, events, active, hotel=None):
    rows = []
    for r in events:
        rf = r.get("rule_fields", {})
        ratio = f"{r['guarantee'] / r['buy_in']:.1f}×" if r.get("guarantee") and r.get("buy_in") else "—"
        rows.append(f"""<tr>
<td>{date_label(r.get('day'))}</td>
<td>{E(r.get('time',''))}</td>
<td>{E(r.get('event',''))} {E(r.get('name',''))}</td>
<td>{money(r.get('buy_in'))}</td>
<td>{money(r.get('guarantee'))}</td>
<td><span class="muted">{ratio}</span></td>
<td>{event_rule_chip(r)}</td>
<td>{src_links(r.get('sources', []))}</td>
</tr>""")
    hotel_html = hotel_block(hotel) if hotel else "<p class='muted'>No hotel matched to this venue in the dated rate log.</p>"
    body = f"""
<p class="lede">All {E(venue_name)} listings in this snapshot, with official sources per row. Entry rules are unverified unless a rule field says confirmed.</p>
{toolbar()}
<div class="table-wrap"><table><thead><tr><th>Date</th><th>Start</th><th>Event</th><th>Buy-in</th><th>Guarantee</th><th>GTD ÷ buy-in (arithmetic)</th><th>Entry rules</th><th>Official sources</th></tr></thead><tbody>{"".join(rows) or '<tr><td colspan="8">No dated listings in this window.</td></tr>'}</tbody></table></div>
<section class="section"><h2>Hotel matched to this venue</h2>{hotel_html}</section>
<div class="callout info"><strong>{E(venue_name)}:</strong> the official schedule and structure sheets cited below were the source of every value. Nothing was inferred.</div>
"""
    open(f"{slug}.html", "w", encoding="utf-8").write(header(title, active) + body + footer())


def build_venues():
    venetian = [r for r in SE if "Venetian" in r.get("venue", "")]
    wynn = [r for r in SE + RE if "Wynn" in r.get("venue", "")]
    venetian_hotel = next((h for h in HOTELS["hotels"] if "Venetian" in h["property"]), None)
    wynn_hotel = next((h for h in HOTELS["hotels"] if h["property"] == "Wynn Las Vegas"), None)
    build_venue("venetian", "Venetian — events & hotels", "The Venetian / Palazzo", venetian, "venetian.html", venetian_hotel)
    build_venue("wynn", "Wynn — events & hotels", "Wynn Las Vegas", wynn, "wynn.html", wynn_hotel)

    # Others page
    others_rows = []
    others = [
        ("Caesars Palace", "Daily NLH flyer: $100 / $160 entries with re-entry and optional $50 add-on — kept in the separate section; buy-in conflict ($100 page vs $160 flyer rows) unresolved.", "S7", "C_FLYER", "C_PAGE"),
        ("Bellagio", "Weekly Friday $600 NLH, Saturday $1,000/$1,100 NLH, Sunday $400 H.O.R.S.E. PDFs undated; Saturday buy-in conflict unresolved; poker page notice stale.", "S12", "B_PAGE", "B_FRI", "B_SAT", "B_SUN"),
        ("ARIA", "Official poker page has room info only; no verified schedule or buy-ins.", "S10",),
        ("MGM Grand", "Official poker page lists times (11 AM / 7 PM / 11 PM); buy-ins not on the page; third-party conflict.", "S9",),
        ("Horseshoe Las Vegas", "Official page confirms six daily tournament times; times and buy-ins not on the page.", "S8",),
        ("Resorts World", "Official poker page shows dining only; no tournament schedule verified.", "S14",),
        ("Planet Hollywood", "Official poker page returned HTTP 500; not listed.", "S13",),
        ("Golden Nugget / Orleans / South Point", "Off-Strip or pages not usable; not listed as Strip candidates.", "S11", "S16", "S17"),
    ]
    for name, detail, *sids in others:
        others_rows.append(f"""<tr><td><b>{E(name)}</b></td><td>{detail}</td><td>{src_links(sids)}</td></tr>""")
    body = f"""
<p class="lede">Other Strip-area rooms checked. None has a verified upcoming single-entry tournament in this window; all are leads or flagged items, not recommendations.</p>
<div class="table-wrap"><table><thead><tr><th>Venue</th><th>What the official source shows</th><th>Official sources</th></tr></thead><tbody>{"".join(others_rows)}</tbody></table></div>
<div class="callout danger"><strong>Not recommended for booking yet.</strong> No date-specific buy-in, guarantee, entry-rule, fee or walking-time value is confirmed for any of these rooms from an official source.</div>
"""
    open("others.html", "w", encoding="utf-8").write(header("Other venues", "others.html") + body + footer())


# ============================ REVIEW ============================

def build_review():
    rows = []
    for f in FLAGGED["items"]:
        rows.append(f"""<tr><td><span id="{E(f['id'])}"><b>{E(f['id'])}</b></span></td><td>{E(f['title'])}</td><td>{E(f['detail'])}</td><td>{src_links(f.get('sources', []))}</td></tr>""")
    body = f"""
<p class="lede">Intentional blanks and unresolved facts—not assumptions. Each issue is paired with the official source checked and the follow-up needed. Nothing here was promoted to “verified” without direct source support.</p>
<div class="callout danger"><strong>Eligibility is not established.</strong> No tournament is currently certified as single-entry. This is the central open issue; all tournament rows are candidates only until the room confirms the entry cap and no re-entry / add-on policy in writing.</div>
<div class="table-wrap"><table><thead><tr><th>ID</th><th>Issue</th><th>Detail</th><th>Official source</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
"""
    open("review.html", "w", encoding="utf-8").write(header("Flagged for review", "review.html") + body + footer())


# ============================ QUESTIONS ============================

def build_questions():
    qs = [
        ("Which dates can the trip cover?", "The Venetian series runs Nov 16 – Dec 23, 2026.", "Travel dates are needed to select events and obtain an actual hotel quote.", "Select arrival/departure dates and backup dates; compare official booking totals.", "S1", "Venetian series dates / booking"),
        ("Is each event strictly single-entry (no re-entry, rebuy, add-on)?", "Reviewed structures list buy-ins, fees and late-registration cutoffs but not an entry cap.", "Allowed entry count and maximum spend cannot be verified.", "Ask the Venetian Poker Room for the written rule sheet per event number; get yes/no on re-entry, rebuy, add-ons.", "S1 / V_S5", "Venetian schedule + structures"),
        ("What is the actual prize pool and payout?", "Published guarantees and some per-entry pool contributions appear in event structures.", "Future entrants and actual payouts are unknown; a guarantee is not an expected payout.", "Use official results after each event; request past turnout for comparable formats.", "S1", "Venetian calendar / results"),
        ("Can the player enter a morning and an evening event the same date?", "Calendar sometimes lists an 11:10 AM and a 5:10 PM event on the same day.", "End time depends on the field; same-day events may conflict.", "Ask the venue for expected duration; plan one primary event per day.", "S1", "Venetian schedule"),
        ("Can the schedule begin at 8:00 AM?", "Earliest listed start in this series is 10:10 AM.", "No 8:00 AM start found in the reviewed series; other venues unchecked.", "Review official room calendars for exact travel dates.", "S1", "Venetian schedule"),
        ("What is the actual all-in hotel cost?", "Venetian: $55 resort fee/night + 13.38% tax confirmed; rate endpoints $119/$209 are conditional.", "Travel dates, occupancy, property-specific price, availability, blackout dates, qualification, cancellation terms missing.", "Enter exact dates/occupancy in the official booking flow and confirm the final checkout total.", "S3 / V_RESORT", "Venetian resort fee / poker rates / booking"),
        ("Is each alternative hotel within a 30-minute walk?", "Venetian is the host property; Palazzo is in the rate program.", "Official walking-time evidence for each route is not recorded.", "Confirm routes on the property map or with guest services before booking.", "S2", "Venetian poker room"),
        ("Which events allow cost advantages from a second spend?", "Schedule labels bounty formats, multi-flight events, conditional member discounts.", "Whether to exclude all bounty formats besides re-entry/rebuy/add-on must be decided.", "Read each official structure; ask the tournament desk about membership/optional paid entries.", "S1", "Venetian schedule"),
        ("Is registration open and the event unchanged?", "Published as scheduled; operator reserves the right to change/cancel.", "Caps, sellout, cancellation, last-minute changes not confirmed.", "Recheck the official calendar and contact the poker room before attending.", "S1", "Venetian schedule"),
    ]
    rows = "".join(f"""<tr><td>{E(a)}</td><td>{E(b)}</td><td>{E(c)}</td><td>{E(d)}</td><td>{src_links([e])}</td><td>{src_links([f])}</td></tr>""" for a, b, c, d, e, f in qs)
    body = f"""
<p class="lede">What must be answered before a decision can reasonably be made. Known = verified from an official source; missing = not verified.</p>
<div class="table-wrap"><table><thead><tr><th>Question</th><th>Known now</th><th>Still unanswered</th><th>How to verify</th><th>Schedule source</th><th>Hotel source</th></tr></thead><tbody>{rows}</tbody></table></div>
"""
    open("questions.html", "w", encoding="utf-8").write(header("Questions & answers", "questions.html") + body + footer())


# ============================ SUGGESTIONS ============================

def build_suggestions():
    sugg = [
        ("S1", "Add official rule-verification status per event (entry cap, re-entry/rebuy/add-on, deadline, last-checked timestamp).", "Resolves the single-entry blocker.", "Requires manual operator confirmation when PDFs omit the rule."),
        ("S2", "Date-specific hotel quote comparison (official checkout total: room + fee + tax + parking + cancellation).", "Replaces starting-rate estimates with spendable totals.", "Rates are perishable; timestamp each snapshot; needs travel dates."),
        ("S3", "Schedule-fit and overlap view with start, late-reg cutoff, estimated end range (only when operator-sourced).", "Estimates maximum playable volume.", "Finish-time forecasts are variable; keep marked as estimates."),
        ("S4", "Location & access verification: official addresses, property maps, pedestrian routes with measured time.", "Checks the ≤30-minute walk constraint.", "Routes change with resort layouts; refresh before travel."),
        ("S5", "Historical pool context from official results (entrants, actual pool, places paid, fee %).", "Helps compare real value vs guarantee.", "History does not guarantee future participation or EV."),
        ("S6", "Trip-date input that filters the schedule to chosen days.", "Needed for a real planner.", "None beyond UI work."),
        ("S7", "Automated re-check of official URLs on a schedule with a diff log (server-side; external fetch blocked in this static build).", "Catches schedule/rate changes quickly.", "Needs a scheduled job or CI step; licensing and parsing must be reliable."),
        ("S8", "Calendar (.ics) export of approved events.", "Helps plan a full day.", "Low effort."),
        ("S9", "Add off-Strip venues once official schedules are verified (Golden Nugget, Horseshoe, ARIA, MGM, Resorts World, Planet Hollywood).", "Broader choice.", "Currently not verifiable from reached sources."),
        ("S10", "Separate “Bounty” and “Age 50+” flags in the tables.", "Relevant to eligibility and format.", "Low effort."),
    ]
    rows = "".join(f"""<tr><td><b>{E(a)}</b></td><td>{E(b)}</td><td>{E(c)}</td><td>{E(d)}</td><td><em>Awaiting your choice</em></td></tr>""" for a, b, c, d in sugg)
    body = f"""
<p class="muted">These are recommendations only. Nothing here is implemented; choose the items you want before any change is made.</p>
<div class="table-wrap"><table><thead><tr><th>ID</th><th>Suggestion</th><th>Decision benefit</th><th>Tradeoff</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>
<h3>Suggested paths</h3>
<ul>
<li><strong>Path A — minimal:</strong> keep the current site; approve S2 and S5 only.</li>
<li><strong>Path B — planner:</strong> approve S1, S2, S3, S5, S6 (verification plus trip-date planner).</li>
<li><strong>Path C — full:</strong> approve everything (S1–S10).</li>
</ul>
<p class="muted">S7 (automated change monitoring) is listed as a suggestion because this static site cannot fetch external hosts; it would run server-side and update <code>last_checked</code> / <code>changed</code> in the data files before each publish.</p>
"""
    open("suggestions.html", "w", encoding="utf-8").write(header("Suggestions", "suggestions.html") + body + footer())


# ============================ SOURCES ============================

def build_sources():
    rows = "".join(f"""<tr><td><code>{E(k)}</code></td><td>{E(v.get('label',''))}</td><td>{E(v.get('type',''))}</td><td><a href="{E(v['url'])}">{E(v['url'])}</a></td></tr>""" for k, v in SRC.items())
    mrows = "".join(f"""<tr><td><b>{E(m['id'])}</b></td><td>{E(m['label'])}</td><td>{m.get('last_checked','')}</td><td><span class="{'pill danger' if m.get('changed') else 'pill warn'}">{'Changed' if m.get('changed') else m.get('status','')}</span></td><td>{E(m.get('note',''))}</td></tr>""" for m in MONITORS)
    body = f"""
<p class="lede">Every table row links to one or more of these official sources. Accessed {CHECKED}. A value is shown only if an official page or PDF states it; otherwise it is blank and flagged unverified.</p>
<section class="section"><h2>Official sources (used for values)</h2>
<div class="table-wrap"><table><thead><tr><th>Key</th><th>Title</th><th>Type</th><th>URL</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="section"><h2>Scheduled re-check of official URLs (change monitoring)</h2>
<p class="muted">External hosts are not reachable from this static build, so re-checks are recorded manually at publish time. A changed value sets <code>changed = true</code> and flags affected rows.</p>
<div class="table-wrap"><table><thead><tr><th>ID</th><th>URL</th><th>Last checked</th><th>Status</th><th>Note</th></tr></thead><tbody>{mrows}</tbody></table></div>
<p class="note">To run the re-check: fetch each URL server-side, diff the relevant values against the snapshot, update <code>last_checked</code> and <code>changed</code>, republish, and flag rows whose source changed.</p>
</section>
"""
    open("sources.html", "w", encoding="utf-8").write(header("Sources & changes", "sources.html") + body + footer())


if __name__ == "__main__":
    build_index()
    build_tournaments()
    build_schedule()
    build_hotels()
    build_venues()
    build_review()
    build_questions()
    build_suggestions()
    build_sources()
    print("root pages built:", [
        "index.html", "tournaments.html", "schedule.html", "hotels.html",
        "venetian.html", "wynn.html", "others.html", "review.html",
        "questions.html", "suggestions.html", "sources.html",
    ])
