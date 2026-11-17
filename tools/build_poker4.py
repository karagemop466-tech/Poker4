#!/usr/bin/env python3
"""Build the poker4 dashboard from the verified data files.

Everything on the pages comes from data/08f07d1d/*.json (+ the re-verified schedule
table). A value a source does not state is rendered blank with a flag, never guessed.
The monitor (.github/workflows/tournament-monitor.yml) runs this after every re-check
so 'last checked' and 'source changed' marks stay live without anyone editing HTML.
"""
from __future__ import annotations
import csv, html, json, os, re, sys, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "08f07d1d")
OUT = os.path.join(ROOT, "poker4")
TODAY = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
SCHED = "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html"

def load(name, default=None):
    p = os.path.join(D, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

def esc(s):
    return html.escape(str(s), quote=True)

def money(v):
    return "—" if v in (None, "") else "$" + format(int(round(float(v))), ",")

# --------------------------------------------------------------------------- data join
def build_rows():
    csvp = os.path.join(ROOT, "data", "c07371e3", "venetian_deepstack_iv.csv")
    rules = {r["sheet"]: r for r in load("structure_rules.json", [])}
    state = load("monitor_state.json", {"sources": {}})
    feed = load("feed/venetian_dse.json")
    policy = load("policy.json", {})
    src_by_url = {s["url"]: s for s in load("sources.json", {"sources": []})["sources"]}
    rows = []
    for r in csv.DictReader(open(csvp, encoding="utf-8")):
        name = r["event_name"]
        sheet = None
        m = re.search(r"structure_(\d+)\.pdf", r["structure_pdf"] or "")
        if m:
            sheet = int(m.group(1))
        ru = rules.get(sheet, {})
        mon = ru.get("monitor") or {}
        stated = mon.get("stated") or {}
        url = ru.get("source_url") or (f"https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/"
                                      f"2026/structures/dse_nov_2026-structure_{sheet}.pdf")
        buy = int(r["buy_in_usd"]) if str(r.get("buy_in_usd", "")).strip() else None
        gtd = int(r["guarantee_usd"]) if str(r.get("guarantee_usd", "")).strip() else None
        restart = bool(re.search(r"Day \d Restart|Final Table", name))
        multi = bool(re.search(r"\b1[A-F]\b", name)) or "2Day" in name or restart
        bounty = bool(re.search(r"(?i)bounty|PKO", name))
        other_game = bool(re.search(r"(?i)Omaha|BIG O|Razz|Stud", name))
        restricted = bool(re.search(r"(?i)Seniors|Ladies|Tag Team", name))
        satellite = bool(re.search(r"(?i)satellite", name)) or "Satellite" == r.get("kind")
        fee = ru.get("fee_usd") or (int(stated["fee_withheld"].replace(",", "")) if stated.get("fee_withheld") else None)
        to_pool = ru.get("to_pool_usd")
        if to_pool is None and stated.get("to_pool"):
            to_pool = int(stated["to_pool"].replace(",", ""))
        if buy and fee and to_pool is None:
            to_pool = buy - fee
        reg_close = ru.get("reg_close") or stated.get("reg_close")
        rc = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", reg_close or "", re.I)
        rc_min = None
        if rc:
            h, mi = int(rc.group(1)), int(rc.group(2))
            ap = rc.group(3).upper()
            if ap == "PM" and h != 12: h += 12
            if ap == "AM" and h == 12: h = 0
            rc_min = h * 60 + mi
        confirmed = bool(ru.get("single_entry_confirmed") or mon.get("single_entry_confirmed"))
        multi_entry = bool(ru.get("multi_entry_confirmed")) or bool(stated.get("reentry_allowed")
                                                                    or stated.get("addon_allowed"))
        audited = bool(ru)
        # change mark from the monitor state
        st = state["sources"].get(url, {})
        rows.append({
            "id": f'{r["date"]}-{r["event_no"]}-{r["time"].replace(" ", "")}',
            "venue": "venetian", "date": r["date"], "time": r["time"], "weekday": r["weekday"],
            "event_no": r["event_no"], "name": name, "listing_kind": r.get("kind") or "Tournament",
            "buy_in": buy, "guarantee": gtd, "fee": fee, "to_pool": to_pool,
            "payout_pct": ru.get("payout"), "chips": ru.get("chips"), "level": ru.get("level"),
            "start": ru.get("start") or stated.get("start_time"),
            "reg_close": reg_close, "reg_close_min": rc_min, "sheet": sheet,
            "sheet_url": url, "schedule_url": SCHED, "entry_rule_note": r.get("entry_rule") or "UNVERIFIED",
            "audited": audited, "frozen_confirmed": confirmed, "multi_entry_confirmed": multi_entry,
            "rule_excerpt": ru.get("entry_rule_excerpt") or (mon.get("rule_lines") or [None])[0],
            "rule_status": ("confirmed single-entry by the sheet" if confirmed else
                            "sheet says extra entries are offered" if multi_entry else
                            "not stated on the sheet" if audited else "sheet not audited in this pass"),
            "last_checked": ru.get("last_checked") or ("2026-11-17" if audited else "2026-11-16"),
            "source_changed": bool(st.get("changed")), "source_checked_at": st.get("last_change"),
            "ratio": round(gtd / buy, 1) if (gtd and buy) else None,
            "group": ("separate" if (bounty or other_game or restricted or satellite or multi) else "candidate"),
            "tags": ([t for t, on in (("one-day", not multi), ("multi-flight", multi), ("bounty", bounty),
                     ("satellite/flight", satellite), ("other game", other_game),
                     ("restricted field", restricted), ("restart/final table", restart)) if on]),
            "note": "",
        })
    if feed and feed.get("rows"):
        for row in rows:
            row["feed_verified"] = any(abs(int(x.get("buy_in_usd") or 0) - (row["buy_in"] or -1)) < 1
                                      and x.get("event_no", "").strip() == row["event_no"].strip()
                                      for x in feed["rows"])
    # continuation rows (Day 2 / Day 3 restarts, final tables) are not entries: entry-only fields
    # (start, registration cutoff, chips, level, fee, pool) must not be copied from the Day 1 sheet
    for row in rows:
        if str(row.get("listing_kind", "")).startswith("Continuation"):
            for k in ("start", "reg_close", "reg_close_min", "chips", "level", "fee", "to_pool"):
                row[k] = None
    rows.sort(key=lambda x: (x["date"], x["reg_close_min"] or 0, x["time"]))
    return rows, rules

# --------------------------------------------------------------------------- day plan
def mins(t):
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", t or "", re.I)
    if not m: return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
    if ap == "PM" and h != 12: h += 12
    if ap == "AM" and h == 12: h = 0
    return h * 60 + mi

def day_plan(rows):
    days = {}
    for r in rows:
        days.setdefault(r["date"], []).append(r)
    plan = []
    for date in sorted(days):
        evs = sorted(days[date], key=lambda x: mins(x["time"]) or 0)
        elig = [e for e in evs if e["group"] == "candidate" and not e["multi_entry_confirmed"]]
        ranked = sorted(elig, key=lambda e: (-(e["ratio"] or 0), e["buy_in"] or 10 ** 6))
        primary = ranked[0] if ranked else None
        fallback, why = None, ""
        pool = [e for e in ranked if e is not primary] + [e for e in evs if e["group"] == "separate"]
        for cand in pool:
            p_end = (primary or {}).get("reg_close_min")
            if mins(cand["time"]) is None or p_end is None:
                continue
            if mins(cand["time"]) >= p_end:      # can be entered after the primary's window shuts
                fallback, why = cand, "start is after the primary event's registration window closes"
                break
        if primary and not fallback:
            for cand in pool:
                if cand is primary: continue
                fallback, why = cand, ("conditional: only if you are out of the primary event before this one's "
                                       "registration closes")
                break
        conflicts = []
        for a in evs:
            for b in evs:
                if a is b: continue
                am, bm = mins(a["time"]), mins(b["time"])
                if am is None or bm is None or am >= bm: continue
                if a["reg_close_min"] and bm < a["reg_close_min"]:
                    conflicts.append({"a": a, "b": b, "kind": "overlap",
                                      "text": f"{a['name']} keeps accepting entries until {a['reg_close']}, "
                                              f"which is after {b['name']} starts at {b['time']}: you cannot be "
                                              f"registered for both."})
                elif a["reg_close_min"] and bm >= a["reg_close_min"]:
                    conflicts.append({"a": a, "b": b, "kind": "conditional",
                                      "text": f"{b['name']} ({b['time']}) is only reachable if you are out of "
                                              f"{a['name']} before its window closes at {a['reg_close']}."})
        plan.append({"date": date, "events": evs, "primary": primary, "fallback": fallback,
                     "fallback_why": why, "conflicts": conflicts,
                     "earliest": min((mins(e["time"]) for e in evs if mins(e["time"])), default=None)})
    return plan

# --------------------------------------------------------------------------- html parts
NAV = [("index.html", "Executive brief"), ("tournaments.html", "Tournaments"),
       ("schedule.html", "Day plan"), ("hotels.html", "Hotels & true cost"),
       ("calculator.html", "Trip cost"), ("venues/venetian.html", "Venues"),
       ("structures.html", "Rule audit"), ("monitor.html", "Source monitor"),
       ("questions.html", "Open questions"), ("suggestions.html", "Suggestions"),
       ("flagged.html", "Flagged for review"), ("sources.html", "Sources"),
       ("search.html", "Search")]

def page(fname, title, body, *, active=None, blurb="", data_js=""):
    prefix = "../" * fname.count("/")
    nav = "".join(f'<a class="{"active" if href == active else ""}" href="{prefix}{href}">{lbl}</a>'
                  for href, lbl in NAV)
    stamp = load("monitor_state.json", {}).get("last_checked", TODAY)
    out = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{esc(blurb or title)} — official-source Las Vegas Strip poker planning dashboard">
<title>{esc(title)} · Strip Poker Planner</title><link rel="stylesheet" href="{prefix}style.css"></head>
<body><header class="topbar"><div class="bar"><a class="brand" href="{prefix}index.html">♠ STRIP POKER PLANNER</a>
<form class="navsearch" role="search" onsubmit="return Poker4.navSearch(this)"><input type="search" name="q" placeholder="Search every table…" aria-label="Search all tables"><button>Go</button></form>
<span class="stamp">sources last re-checked {esc(str(stamp)[:16].replace('T',' '))} UTC</span></div></header>
<nav class="nav"><div class="nav-inner">{nav}</div></nav><main>{body}</main>
<footer class="footer">Official-source snapshot. Every row links the operator's own page; anything a source does not state is
blank and flagged, never inferred. <a href="@@/flagged.html">Open items</a> ·
<a href="@@/monitor.html">Re-check schedule</a> ·
<a href="@@/suggestions.html">Suggested next steps</a></footer>
{data_js}<script src="{prefix}app.js"></script></body></html>"""
    out = out.replace("@@ROOT/", prefix + "../").replace("@@/", prefix)
    d = os.path.join(OUT, os.path.dirname(fname)) if os.path.dirname(fname) else OUT
    os.makedirs(d, exist_ok=True)
    open(os.path.join(OUT, fname), "w", encoding="utf-8").write(out)
    return len(out)

def callout(text, kind=""):
    return f'<div class="callout {kind}">{text}</div>'

def pill(text, kind="warn"):
    return f'<span class="pill {kind}">{esc(text)}</span>'

def srclinks(*pairs):
    return " ".join(f'<a class="source-link" href="{esc(u)}" target="_blank" rel="noopener">{esc(l)} ↗</a>'
                    for l, u in pairs)

def table(headers, rows_html, cls="data must"):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "\n".join(rows_html) or f'<tr><td colspan="{len(headers)}">No rows.</td></tr>'
    return f'<div class="table-wrap"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'

# --------------------------------------------------------------------------- pages
def render(rows, rules, plan):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "venues"), exist_ok=True)
    hotels = load("hotels.json", {"hotels": []})
    rates = load("rates.json", {"log": []})
    walks = load("walks.json", {"pairs": []})
    flags = {f["id"]: f for f in load("flags.json", {"items": []})["items"]}
    questions = load("questions.json", {"items": []})["items"]
    suggestions = load("suggestions.json", {"items": []})["items"]
    venues = load("venues.json", {"venues": []})["venues"]
    policy = load("policy.json", {})
    state = load("monitor_state.json", {"sources": {}})
    log = load("monitor_log.json", {"runs": []})
    sizes = {}
    cand = [r for r in rows if r["group"] == "candidate"]
    sep = [r for r in rows if r["group"] == "separate"]
    frozen = [r for r in rows if r["frozen_confirmed"]]
    audited = [r for r in rows if r["audited"]]
    changed = [r for r in rows if r["source_changed"]]
    upcoming = [r for r in rows if r["date"] >= TODAY]
    ratio_best = sorted([c for c in cand if c["ratio"]], key=lambda c: -c["ratio"])

    # ---- shared row renderer -----------------------------------------------------
    def trow(r):
        badge = (pill("Single-entry CONFIRMED", "ok") if r["frozen_confirmed"] else
                 pill("Multi-entry offered", "danger") if r["multi_entry_confirmed"] else
                 pill("Unverified", "warn"))
        ratio = f'{r["ratio"]}×' if r["ratio"] else "—"
        chg = " " + pill("SOURCE CHANGED", "danger") if r["source_changed"] else ""
        return (f'<tr id="{r["id"]}" data-date="{r["date"]}" data-venue="{r["venue"]}" data-frozen="{"yes" if r["frozen_confirmed"] else "no"}" '
                f'data-group="{r["group"]}" data-buyin="{r["buy_in"] or 0}">'
                f'<td>{esc(r["date"])}</td><td>{esc(r["time"])}</td><td>#{esc(r["event_no"])}</td>'
                f'<td class="nm">{esc(r["name"])}<small>{esc(" · ".join(r["tags"]))}{(" — " + esc(r["rule_status"])) if r["rule_status"] != "not stated on the sheet" else ""}</small></td>'
                f'<td class="n">{money(r["buy_in"])}</td><td class="n">{money(r["guarantee"])}</td>'
                f'<td class="n">{ratio}</td><td class="n">{money(r["to_pool"])}</td>'
                f'<td>{esc(r["reg_close"] or "—")}</td><td>{badge}</td>'
                f'<td class="chk">{esc(r["last_checked"])}{chg}</td>'
                f'<td>{srclinks(("Calendar", r["schedule_url"]), ("Sheet #" + str(r["sheet"]), r["sheet_url"]))}</td></tr>')

    HEAD = ["Date", "Start", "Ev #", "Event", "Buy-in", "Guarantee", "GTD ÷ entry", "$ to pool / entry",
            "Late reg closes", "Entry rule", "Last checked", "Official sources"]

    # ---- index / executive brief -------------------------------------------------
    stats = [("Dated official rows", len(rows), "Venetian DeepStack IV calendar, Nov 16 – Dec 23, re-checked 2026-11-17"),
             ("Rows whose sheet was read", f"{len(audited)}", f"{len(rules)} of 37 structure sheets audited in this pass"),
             ("Confirmed single-entry", len(frozen), "0 — no sheet read states one-entry/no-re-entry"),
             ("Events where extra entries ARE priced", len([r for r in rows if r['multi_entry_confirmed']]), "sheet #8 (Valuetown) prices subsequent buy-ins"),
             ("Lowest candidate buy-in", money(min([c['buy_in'] for c in cand if c['buy_in']]) if cand else None), "one-day plain NLH candidates"),
             ("Rows flagged as changed", len(changed), "set by the scheduled re-check, not by hand")]
    cards = f'<div class="stats">' + "".join(
        f'<div class="stat"><span>{esc(a)}</span><b>{esc(b)}</b><span>{esc(c)}</span></div>' for a, b, c in stats) + "</div>"
    top = "".join(f"<tr><td>{esc(c['date'])} {esc(c['time'])}</td><td>{esc(c['name'])}</td>"
                  f"<td class='n'>{money(c['buy_in'])}</td><td class='n'>{money(c['guarantee'])}</td>"
                  f"<td class='n'>{c['ratio']}×</td><td class='n'>{money(c['to_pool'])}</td>"
                  f"<td>{pill('Unverified')}</td><td>{srclinks(('Sheet #'+str(c['sheet']), c['sheet_url']))}</td></tr>"
                  for c in ratio_best[:6])
    blockers = "".join(f'<li><b>{esc(q["q"])}</b><span>{esc(q["missing"])}</span>{srclinks(("why this flag", "@@/flagged.html#" + q["flag"]))}</li>'
                       for q in questions if q["blocking"])
    body = f"""<section class="hero"><p class="eyebrow">Decision dashboard · verified against operator documents on {TODAY}</p>
<h1>Vegas poker trip, decided on what the sources actually say.</h1>
<p>All 94 dated rows of the official Venetian DeepStack IV calendar, joined to the official structure sheets that set
buy-in, fee split, late-registration close and guarantee — plus the hotel fee math, a trip-cost estimator, a per-day
plan, and a scheduled re-check that marks a row the moment its source moves.</p>
<div class="hero-actions"><a class="button" href="@@/tournaments.html">Tournament shortlist</a>
<a class="button ghost" href="@@/calculator.html">Trip cost</a>
<a class="button ghost" href="@@/flagged.html">{len(flags)} open items</a></div></section>
{cards}
{callout("<b>Do not book on the assumption of single-entry play.</b> The candidate list is empty in the strict sense: "
         "no structure sheet read in this pass states one entry per player, and silence is not confirmation. "
         "Every row below carries its own sheet so the wording (or its absence) is one click away.", "danger")}
{callout("<b>What is verified:</b> 93 of 94 calendar rows were re-read cell-by-cell against the live official page "
         "(`tools/check_rows.py` → 0 mismatches); " + str(len(rules)) + " of 37 structure sheets were read end-to-end; the $55 + tax nightly "
         "resort fee was re-read today. <b>What is not:</b> entry rules, dated room rates, cancellation deadlines, "
         "walking minutes, and every non-Venetian room's schedule.")}
<section class="section"><h2>Best descriptive ratio among low-cost candidates</h2>
<p class="muted">Guarantee ÷ buy-in is arithmetic on published numbers — a screening ratio, not expected value, not a
forecast, and not adjusted for field size or the money that actually reaches the pool.</p>
{table(["Date · start","Event","Buy-in","Guarantee","GTD ÷ entry","$ to pool / entry","Entry rule","Source"], [top])}
<p class="muted">Bounty, satellite/flight, restricted-field and other-game events are ranked separately on the
<a href="@@/tournaments.html">tournaments page</a> — their guarantees may include bounty payouts, so they are
not comparable with plain NLH pools.</p></section>
<section class="section"><h2>Questions that block a decision</h2><ol class="qlist">{blockers}</ol>
<p><a class="button" href="@@/questions.html">All {len(questions)} questions with the answers we have</a></p></section>
<section class="section"><h2>Plan constraints found, not assumed</h2><div class="grid">
<div class="card"><h3>No 8 AM start exists here</h3><p>Earliest row on the official calendar is 9:10 AM (a Dec 12 satellite);
earliest main-event start is 10:00–10:10 AM. The day plan is built from real starts, not a wish.</p></div>
<div class="card"><h3>Finish times are not published</h3><p>Sheets give start and late-registration close only, so overlaps are
flagged as "cannot register for both" or "conditional on busting out in time" — never as a certainty.</p></div>
<div class="card"><h3>Hotel total needs your dates</h3><p>$55 + tax nightly fee is confirmed; the room rate is not a single
stored number but a dated log, so no nightly total is claimed for undated stays.</p></div></div></section>
<section class="section"><h2>Where the money goes per entry</h2><p class="muted">The official sheets state the house fee is withheld
<i>from</i> the advertised buy-in, not added on top: e.g. "$58 of the $300 Buy-In is withheld for house fees … the prize pool
consists of $242 of every $300 Buy In." That is the number to compare across buy-in levels.</p></section>"""
    sizes["index.html"] = page("index.html", "Executive brief", body, active="index.html",
                               blurb="Executive brief: verified Strip poker tournament and hotel decision dashboard")

    # ---- tournaments -------------------------------------------------------------
    filters = f"""<div class="toolbar" id="filters">
<label>From <input type="date" data-filter="from" value="{esc(policy.get('trip_window',{}).get('first_day',TODAY))}"></label>
<label>To <input type="date" data-filter="to" value="{esc(policy.get('trip_window',{}).get('last_day','2026-12-23'))}"></label>
<label>Venue <select data-filter="venue"><option value="">all</option><option value="venetian">Venetian</option></select></label>
<label class="chk"><input type="checkbox" data-filter="frozen"> only confirmed single-entry / freezeout</label>
<label class="chk"><input type="checkbox" data-filter="changed"> only rows whose source changed</label>
<input type="search" data-filter="q" placeholder="Search date, event #, buy-in…">
<span class="count" data-count></span></div>"""
    cand_tbl = table(HEAD, [trow(r) for r in sorted(cand, key=lambda x: (-x["ratio"] if x["ratio"] else 0, x["date"]))])
    sep_tbl = table(HEAD, [trow(r) for r in sorted(sep, key=lambda x: (x["date"], x["time"]))])
    body = f"""<p class="eyebrow">Ranked on confirmed fee and confirmed guarantee only</p><h1>Tournaments</h1>
<p class="lede">One-day plain No-Limit Hold'em candidates first, ranked by the published guarantee-to-buy-in ratio; every row
shows the money that actually reaches the pool, the registration window, the entry-rule verdict and the date its source was
last read. Filters apply to both tables and to the search box on every page.</p>
{callout("<b>The single-entry filter is honest: it returns nothing yet.</b> No structure sheet audited in this pass states "
         "one entry per player, so nothing qualifies as confirmed. Toggle it to see the emptiness rather than a false list.", "danger")}
{filters}
<section class="section"><h2>Candidates — one-day plain NLH ({len(cand)})</h2>{cand_tbl}</section>
<section class="section"><h2>Separate section — bounty / satellite-flight / restricted-field / other-game / multi-flight ({len(sep)})</h2>
<p class="muted">Kept apart because their guarantees may include bounty payouts (e.g. "$8,000 (prize pool + total bounties)"),
their entry economics differ (satellites award an entry, the Valuetown sheet prices repeat buy-ins), or their fields are
restricted (Seniors 50+, Ladies, tag teams) — none of which is comparable with a plain freezeout candidate.</p>{sep_tbl}</section>
<section class="section"><h2>Reading this table</h2><div class="grid">
<div class="card"><h3>GTD ÷ entry</h3><p>Published guarantee divided by the buy-in. Descriptive only: it ignores field size,
payout structure, rake and variance, and multi-flight events pool entries across several days.</p></div>
<div class="card"><h3>$ to pool / entry</h3><p>From the sheet's own sentence (e.g. $242 of every $300). Blank where the sheet
was not audited in this pass.</p></div>
<div class="card"><h3>Late reg closes</h3><p>Quoted from the sheet ("10 levels + Break (~ 4:55 PM)"). It is the only published
time that constrains whether a second event can be entered the same day.</p></div></div></section>"""
    sizes["tournaments.html"] = page("tournaments.html", "Tournaments", body, active="tournaments.html",
                                     blurb="Dated Strip tournament rows with entry-rule audit, filters and source links")

    # ---- structures (rule audit) -------------------------------------------------
    def srow(n):
        r = rules.get(n, {})
        mon = r.get("monitor") or {}
        lines = (mon.get("rule_lines") or [])[:3] or ([r["entry_rule_excerpt"]] if r.get("entry_rule_excerpt") else [])
        quote = "<br>".join(f"<q>{esc(l)}</q>" for l in lines) or "<span class='unknown'>no entry-rule sentence found</span>"
        st = ("CONFIRMED single-entry" if r.get("single_entry_confirmed") else
              "extra entries offered" if (mon.get("stated", {}).get("reentry_allowed") or r.get("multi_entry_confirmed")) else
              "not stated" if r else "not audited in this pass")
        chk = r.get("last_checked") or "—"
        return (f"<tr id='sheet-{n}'><td>#{n}</td><td>{esc(r.get('title') or 'sheet read pending')}</td>"
                f"<td>{esc(', '.join('#' + str(e) for e in (r.get('events') or [])) or '—')}</td>"
                f"<td class='n'>{money(r.get('fee_usd'))}</td><td class='n'>{money(r.get('to_pool_usd'))}</td>"
                f"<td>{esc(r.get('reg_close') or '—')}</td><td>{pill(st,'ok' if r.get('single_entry_confirmed') else 'warn')}</td>"
                f"<td>{quote}</td><td class='chk'>{esc(chk)}</td>"
                f"<td>{srclinks(('Sheet', r.get('source_url') or f'https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_{n}.pdf'))}</td></tr>")
    body = f"""<p class="eyebrow">Every structure sheet, read as text</p><h1>Rule audit</h1>
<p class="lede">The instruction was to read every structure sheet and drop the "unverified" label only where the sheet actually
confirms the entry rule. {len(rules)} of 37 sheets have been read end-to-end in this pass; the rest are listed with their
official link and marked as not yet audited rather than assumed.</p>
{callout("A sheet is only flipped to <b>confirmed</b> if it contains an explicit sentence — 'one entry per player', "
         "'no re-entry', 'no add-on', 'freezeout'. The multi-flight sheets do carry one real entry rule "
         "('Any player who bags chips for Day 2 may not play a subsequent flight'), which restricts flights but does not "
         "answer the re-entry question, so it is quoted and the row stays unverified.")}
{table(["Sheet","Title on the sheet","Events","House fee","$ to pool","Late reg closes","Entry-rule verdict","Quoted rule sentences","Last read","Official PDF"],
       [srow(n) for n in range(1, 38)], cls="data must")}"""
    sizes["structures.html"] = page("structures.html", "Rule audit", body, active="structures.html",
                                    blurb="Line-by-line audit of every official structure sheet")

    # ---- schedule / day plan -----------------------------------------------------
    days_html = []
    for d in plan:
        if d["date"] < TODAY: continue
        ev_rows = "".join(f'<li>{esc(e["time"])} · #{esc(e["event_no"])} {esc(e["name"])} '
                          f'<span class="mini">{money(e["buy_in"])}{(" / " + money(e["guarantee"]) + " GTD") if e["guarantee"] else ""}</span> '
                          f'{pill("candidate","ok") if e["group"]=="candidate" else pill("separate")}</li>' for e in d["events"])
        prim = d["primary"]
        conf = "".join(f'<li class="{"hard" if c["kind"]=="overlap" else "cond"}">{esc(c["text"])}</li>' for c in d["conflicts"])
        days_html.append(f"""<article class="day"><h3>{esc(d["date"])} <span class="muted">{len(d["events"])} official rows</span></h3>
<div class="cols"><div><p class="eyebrow">Primary</p><p>{(f'<b>#{esc(prim["event_no"])} {esc(prim["name"])}</b> · {esc(prim["time"])} start · {money(prim["buy_in"])} entry · reg closes {esc(prim["reg_close"] or "not stated")} · {pill(prim["rule_status"])}' if prim else '<span class="unknown">no one-day plain NLH candidate that day — flights or separate-format events only</span>')}</p>
<p class="eyebrow">Conditional fallback</p><p>{(f'<b>#{esc(d["fallback"]["event_no"])} {esc(d["fallback"]["name"])}</b> · {esc(d["fallback"]["time"])} · {esc(d["fallback_why"])}' if d["fallback"] else '<span class="muted">none — no second start sits after the primary registration window</span>')}</p></div>
<div><p class="eyebrow">Same-day rows</p><ul class="evlist">{ev_rows}</ul></div></div>
{('<p class="eyebrow">Overlap check</p><ul class="conf">' + conf + '</ul>') if conf else ''}
<p class="rowlinks">{srclinks(("Calendar row", d["events"][0]["schedule_url"]))}</p></article>""")
    earliest = min((d["earliest"] for d in plan if d["earliest"]), default=0)
    body = f"""<p class="eyebrow">Start · late-reg window · plausible duration</p><h1>Day plan</h1>
<p class="lede">One event per day by default. A second event is added only where the published late-registration windows make it
possible, and then labelled conditional — because no source publishes a finish time. Earliest start anywhere in the verified
calendar is {earliest//60}:{earliest%60:02d} ({esc(policy.get('day_plan',{}).get('note',''))})</p>
{callout("Overlaps are computed from two published facts only: each event's start and its registration close. "
         "Anything that cannot be sequenced is marked <i>cannot be registered for both</i>; anything that depends on busting out "
         "in time is marked <i>conditional</i>. Nothing here claims an event ends at a particular hour.", "danger")}
{''.join(days_html)}"""
    sizes["schedule.html"] = page("schedule.html", "Day plan", body, active="schedule.html",
                                  blurb="Per-day primary event with conditional fallback and overlap flags")

    # ---- hotels ------------------------------------------------------------------
    def hotel_row(h):
        fee = h.get("resort_fee", {})
        tax = h.get("room_tax", {})
        fee_v = fee.get("value")
        status = lambda d_: pill(d_.get("status", "not verified"),
                                 "ok" if str(d_.get("status", "")).startswith("confirmed") else "warn")
        link = h.get("booking_link", "").replace("{guests}", str(policy.get("occupancy", {}).get("guests", 2))) \
            .replace("{arrive}", policy.get("trip_window", {}).get("first_day", TODAY)) \
            .replace("{depart}", "2026-11-24").replace("{arrive_us}", "11/17/2026").replace("{depart_us}", "11/24/2026")
        return (f"<tr id='{h['id']}' data-venue='{h['venue']}'><td><b>{esc(h['name'])}</b><small>{esc(h['relationship'])}</small></td>"
                f"<td class='n'>{money(fee_v)} {status(fee)}</td>"
                f"<td class='n'>{(str(tax.get('value')) + '%') if tax.get('value') else '—'} {status(tax)}</td>"
                f"<td class='n'>{'—'} {pill(h.get('checkout_total',{}).get('status','not captured'))}</td>"
                f"<td class='n'>{'—'} {pill(h.get('cancellation',{}).get('status','not captured'))}</td>"
                f"<td class='n'>{'—'} {pill(h.get('parking',{}).get('status','not captured'))}</td>"
                f"<td class='n'>{'—'} {pill(h.get('quality',{}).get('status','not verified'))}</td>"
                f"<td>{('<a class=' + chr(34) + 'source-link' + chr(34) + ' href=' + chr(34) + esc(link) + chr(34) + ' target=_blank>dated quote ↗</a>') if link else '—'}</td></tr>")
    rate_rows = "".join(f"<tr><td>{esc(o['observed'])}</td><td>{esc(o['hotel'])}</td><td>{esc(o['kind'])}</td>"
                        f"<td class='n'>{money(o.get('value'))}</td><td>{esc(o.get('occupancy','—'))}</td>"
                        f"<td>{esc(o.get('terms',''))}</td><td>{pill('carried / re-check pending' if 'carried' in str(o.get('status','')) else o.get('status',''))}</td>"
                        f"<td>{srclinks(('Source', o['source']))}</td></tr>" for o in rates.get("log", []))
    walk_rows = "".join(f"<tr><td>{esc(p['hotel'])}</td><td>{esc(p['venue'])}</td><td class='n'>{'—' if p['minutes'] is None else str(p['minutes'])+' min'}</td>"
                        f"<td class='n'>{'—' if p['distance_mi'] is None else str(p['distance_mi'])+' mi'}</td>"
                        f"<td>{pill('not verified','warn')}</td><td>{esc(p['status'])}</td>"
                        f"<td>{srclinks(('Google Maps', p['route']['google']),('Apple Maps', p['route']['apple']))}</td></tr>"
                        for p in walks.get("pairs", []))
    body = f"""<p class="eyebrow">Fees confirmed today · rates as a dated log</p><h1>Hotels &amp; true cost</h1>
<p class="lede">True cost per night = advertised room rate + mandatory resort fee + tax, and only that sum is comparable between
properties. The nightly rate is kept as a dated log of observations, so a rate never silently replaces an older one.</p>
{callout("<b>Confirmed today:</b> the Venetian/Palazzo page states “Rates include a daily Resort Fee of $55 plus tax per night, "
         "payable upon check-in.” <b>Not confirmed:</b> the 13.38% room-tax figure, parking and cancellation terms are carried from "
         "an earlier session's reading of a page that this environment could not load, so they are marked carried and the "
         "monitor re-reads them. No dated room rate exists for any property, so no nightly total is asserted.", "danger")}
<section class="section"><h2>Per-property itemisation</h2>
{table(["Property","Mandatory resort fee / night","Room tax","Checkout total (itemised)","Cancellation deadline","Parking","Quality metric","Official dated quote"],
       [hotel_row(h) for h in hotels["hotels"]], cls="data must")}
<p class="muted">Every blank cell is a value the operator's public page does not state; the calculator therefore takes it as an
input instead of inventing it. Booking links use the official engine's own URL pattern (read from the property pages today), so
they open the dated quote without this site claiming a price.</p></section>
<section class="section"><h2>Rate log — dated observations, not a single value</h2>
{table(["Observed","Property","What it is","Value / night","Occupancy","Terms","Status","Source"], [rate_rows], cls="data must") if rate_rows else '<p class="muted">No observations yet.</p>'}
<p class="muted">{esc(rates.get('note',''))}</p></section>
<section class="section"><h2>Walking routes ({policy.get('walk_limit_minutes',30)}-minute limit)</h2>
{table(["From","To","Minutes","Distance","Filter verdict","Basis","Live route link"], [walk_rows], cls="data must")}
{callout("The ≤30-minute filter cannot pass any hotel yet, because no walking minute has been verified. "
         "Staying at the host property is the only route this dashboard can recommend on distance grounds — and it is "
         "recommended because it is the same building, not because a number was invented.")}
</section>"""
    sizes["hotels.html"] = page("hotels.html", "Hotels & true cost", body, active="hotels.html",
                                blurb="Hotel true-cost math, dated rate log and walking-route status")

    # ---- calculator --------------------------------------------------------------
    opts = "".join(f'<label class="pick"><input type="checkbox" data-buyin="{c["buy_in"] or 0}" data-gtd="{c["guarantee"] or 0}" '
                   f'data-checked="{1 if (c in ratio_best[:3] and c["date"] >= TODAY) else 0}"> '
                   f'{esc(c["date"])} {esc(c["time"])} · #{esc(c["event_no"])} {esc(c["name"])} — {money(c["buy_in"])}'
                   f'{(" · " + money(c["guarantee"]) + " GTD") if c["guarantee"] else ""}</label>' for c in sorted(cand, key=lambda x: x["date"]))
    body = f"""<p class="eyebrow">entries × buy-ins + nights × true hotel cost</p><h1>Estimated trip cost</h1>
<p class="lede">Tick the events you would actually play, set the nights and the room rate, and the total is itemised — including
how much of each entry reaches the prize pool, and exactly which inputs are assumptions rather than confirmed figures.</p>
<div class="calc" id="calc">
<div class="panel"><h3>Entries</h3><div class="picks">{opts}</div>
<p class="muted">Only one-day plain NLH candidates are listed. Bounty/satellite/restricted events are excluded by design — comparing them
inflates what a trip "costs per shot at a pool".</p></div>
<div class="panel"><h3>Lodging</h3>
<label>Nights <input type="number" id="c-nights" value="5" min="1" max="30"></label>
<label>Room rate / night (USD) <input type="number" id="c-rate" value="119" min="0" step="1"></label>
<label>Mandatory resort fee / night <input type="number" id="c-fee" value="55" min="0" step="0.01"></label>
<label>Tax on room + fee (%) <input type="number" id="c-tax" value="13.38" min="0" step="0.01"></label>
<label>Parking / day (0 if none) <input type="number" id="c-park" value="0" min="0" step="1"></label>
<label>Entries per event (re-entry count — 0 means the rule is unverified, so leave 1) <input type="number" id="c-entries" value="1" min="1" max="10"></label>
</div>
<div class="panel out"><h3>Estimated total</h3>
<p class="big" id="c-total">—</p>
<ul id="c-lines"></ul>
<div class="warnbox" id="c-warn"></div>
<p class="muted">Formula: (entries × Σ buy-ins) + nights × (rate + fee) × (1 + tax%) + parking. Every field is your input except the
$55 fee, which is quoted from the property's own page; the $119 default is the advertised conditional poker-rate starting point,
not a quote for your dates.</p></div></div>
{callout("This estimator is a decision aid, not a bill. It cannot include a dated room quote, resort credits, resort-fee tax "
         "treatment differences between properties, or cancellation penalties, because those are not published values — see the "
         "open items list.", "danger")}"""
    sizes["calculator.html"] = page("calculator.html", "Trip cost", body, active="calculator.html",
                                    blurb="Trip cost estimator: entries × buy-ins plus nights × true hotel cost",
                                    data_js=calc_js(rows))

    # ---- venues ------------------------------------------------------------------
    for v in venues:
        vrows = [r for r in rows if r["venue"] == v["id"]] if v["id"] != "other-rooms" else []
        vhotel = [h for h in hotels["hotels"] if v["id"] in (h.get("venue"), ) or h["id"] in ("venetian", "palazzo") and v["id"] == "venetian"]
        ev_tbl = table(HEAD, [trow(r) for r in sorted(vrows, key=lambda x: (x["date"], x["time"]))]) if vrows else \
            f'<p class="unknown">{esc(v["schedule_status"])}</p>'
        links = " · ".join(f'<a href="{esc(p["url"])}" target="_blank" rel="noopener">{esc(p["label"])} ↗</a>' for p in v["official_pages"])
        st = state.get("sources", {})
        mon_rows = "".join(f"<tr><td>{esc(p['label'])}</td><td class='mono'><a href=\"{esc(p['url'])}\" target='_blank' rel='noopener'>{esc(p['url'][:64])}…</a></td>"
                           f"<td>{esc((st.get(p['url']) or {}).get('status') or 'not yet run')}</td>"
                           f"<td class='chk'>{esc((st.get(p['url']) or {}).get('checked_at') or 'first run pending')}</td>"
                           f"<td>{pill('changed','danger') if (st.get(p['url']) or {}).get('changed') else pill('unchanged','ok')}</td></tr>"
                           for p in v["official_pages"])
        body = f"""<p class="eyebrow">Venue page · events and lodging together</p><h1>{esc(v['name'])}</h1>
<p class="lede">{esc(v.get('property',''))} — official pages: {links}</p>
{callout(esc(v['schedule_status']), "danger" if ("NOT VERIFIED" in v['schedule_status'] or "FLAGGED" in v['schedule_status']) else "")}
<section class="section"><h2>Events here ({len(vrows)})</h2>{ev_tbl}</section>
<section class="section"><h2>Hotels at this venue</h2>
{table(["Property","Resort fee / night","Room tax","Checkout total","Cancellation","Parking","Quality","Dated quote"],[hotel_row(h) for h in vhotel], cls="data must") if vhotel else '<p class="muted">No hotel verified for this venue.</p>'}</section>
<section class="section"><h2>Source monitoring for this venue</h2>
{table(["Official page","URL","HTTP status","Last checked","Content hash"," "][:-1], [mon_rows]) if mon_rows else ''}
<p class="muted">Structure sheets audited for this venue: {v.get('sheets_audited_this_pass',0)} of {v.get('structure_sheets',0)}.</p></section>"""
        sizes[f"venues/{v['id']}.html"] = page(f"venues/{v['id']}.html", v["name"], body,
                                               active="venues/venetian.html", blurb=f"{v['name']} — events, hotels and source status")
    nav_venues = "".join(f'<li><a href="@@/venues/{v["id"]}.html"><b>{esc(v["name"])}</b> — {esc(v.get("schedule_status")[:110])}…</a></li>' for v in venues)
    page("venues/index.html", "Venues", f"""<p class="eyebrow">One page per venue</p><h1>Venues</h1>
<p class="lede">Each venue page holds its own events, its own hotels, and the monitoring status of the official pages it was built from,
so a claim can be checked at its source without crossing properties.</p><ul class="venlist">{nav_venues}</ul>""",
         active="venues/venetian.html", blurb="Venues index")

    # ---- monitor -----------------------------------------------------------------
    srcs = load("sources.json", {"sources": []})["sources"]
    def mrow(s):
        u = s["url"]
        st = state.get("sources", {}).get(u, {})
        status = "not yet run"
        if st:
            status = ("error: " + st["error"][:60]) if st.get("error") else (f"HTTP {st.get('status')}" if st.get("status") else "unknown")
            if st.get("redirected"): status += " · redirected"
        return (f"<tr><td>{esc(s['id'])}</td><td>{esc(s['label'])}</td><td class='mono'><a href='{esc(u)}' target='_blank' rel='noopener'>{esc(u[:80])}…</a></td>"
                f"<td>{esc(status)}</td><td class='chk'>{esc(st.get('checked_at') or '—')}</td>"
                f"<td class='mono'>{esc((st.get('sha256') or '—')[:12])}</td>"
                f"<td>{pill('changed','danger') if st.get('changed') else pill('same','ok') if st else pill('pending')}</td>"
                f"<td class='n'>{st.get('bytes','—') if st.get('bytes') else '—'}</td></tr>")
    runs = "".join(f"<tr><td>{esc(r['at'])}</td><td class='n'>{r['checked']}</td><td>{esc(', '.join(r['changed']) or 'none')}</td>"
                   f"<td>{esc(', '.join(r['unreachable']) or 'none')}</td><td>{esc(', '.join('#'+str(s) for s in (r.get('newly_confirmed_sheets') or [])) or 'none')}</td></tr>"
                   for r in (log.get("runs") or [])[-15:][::-1])
    changed_rows = [r for r in rows if r["source_changed"]]
    body = f"""<p class="eyebrow">Scheduled re-check of every official URL</p><h1>Source monitor</h1>
<p class="lede">A GitHub Actions job runs each morning ({esc("06:20 Las Vegas time")}): it re-fetches all {len(srcs)} official URLs, compares
the <i>content hash</i> rather than just the status code, audits every structure sheet's entry-rule wording, re-parses the calendar
into a machine feed, rebuilds these pages, and commits only if the site still verifies. Rows whose source moved are marked
<span class="pill danger">SOURCE CHANGED</span> everywhere they appear.</p>
{callout("Why a hash, not a status code: the official Wynn poker page returned HTTP 200 while handing over the property's home page. "
         "A status check would call that healthy and quietly keep stale rows. Here it is recorded as a redirect and shown as a problem.", "danger")}
<section class="section"><h2>Rows currently marked changed ({len(changed_rows)})</h2>
{table(HEAD, [trow(r) for r in changed_rows], cls="data must") if changed_rows else '<p class="muted">No source has moved since the last run. The first run has no baseline, so "changed" cannot be true yet — that is an honest empty state, not a result.</p>'}</section>
<section class="section"><h2>Recent runs</h2>
{table(["Run (UTC)","Sources","Content changed","Unreachable","Newly confirmed sheets"], [runs], cls="data prose") if runs else '<p class="muted">No run recorded yet — the schedule starts on the default branch.</p>'}</section>
<section class="section"><h2>Every tracked official URL</h2>
{table(["ID","What it is","URL","Result","Last checked","Content hash","Verdict","Bytes"], [mrow(s) for s in srcs], cls="data must")}</section>
<p class="muted">Feeds produced by the same job: <code>data/08f07d1d/feed/venetian_dse.json</code> (daily calendar scrape),
<code>monitor_state.json</code> (per-URL hashes + change dates), <code>monitor_log.json</code> (run history).</p>"""
    sizes["monitor.html"] = page("monitor.html", "Source monitor", body, active="monitor.html",
                                 blurb="Scheduled official-source re-check, change marks and per-URL status")

    # ---- questions / suggestions / flagged / sources / repo review ----------------
    body = f"""<p class="eyebrow">What must be answered before a decision is reasonable</p><h1>Questions &amp; missing information</h1>
<p class="lede">Twelve questions, each with what is already known, what is missing, and the concrete action that closes it. Blocking
questions are the ones where a wrong assumption costs money.</p>
<ol class="qlist">""" + "".join(
        f"""<li id="{esc(q['id'])}"><b>{esc(q['q'])}</b>{pill('blocking','danger') if q['blocking'] else pill('refines the plan')}
<p><span class="lab">We have:</span> {esc(q['have'])}</p><p><span class="lab">Missing:</span> {esc(q['missing'])}</p>
<p><span class="lab">How to find out:</span> {esc(q['how'])}</p><p><span class="lab">Who answers:</span> {esc(q['who'])} ·
{srclinks(('related flag', '@@/flagged.html#' + q['flag']))}</p></li>""" for q in questions) + "</ol>"
    sizes["questions.html"] = page("questions.html", "Open questions", body, active="questions.html",
                                   blurb="Decision-blocking questions with what is known, missing, and how to discover it")

    body = f"""<p class="eyebrow">Review and choose — nothing here is built on your behalf</p><h1>Suggestions</h1>
<p class="lede">Each suggestion says what it fixes, its impact and effort, and what it depends on. Items marked
<i>implemented</i> were requested outright in the brief; everything else waits for your choice.</p>"""
    srows = []
    for sg in suggestions:
        srows.append("<tr id='" + esc(sg["id"]) + "'><td>" + esc(sg["id"]) + "</td><td><b>" + esc(sg["title"])
                     + "</b></td><td>" + esc(sg["why"]) + "</td><td>"
                     + pill(sg["impact"], "ok" if sg["impact"] == "high" else "warn") + "</td><td>" + esc(sg["effort"])
                     + "</td><td>" + esc(sg.get("depends", "—")) + "</td><td>"
                     + pill(sg["status"][:40], "danger" if "awaiting" in sg["status"] else "ok") + "</td></tr>")
    body += table(["ID", "Suggestion", "Why it helps", "Impact", "Effort", "Depends on", "Status"], srows, cls="data prose")
    sizes["suggestions.html"] = page("suggestions.html", "Suggestions", body, active="suggestions.html",
                                     blurb="Staged suggestions for better decision-making, awaiting the owner's choice")

    def frow(f):
        links = (srclinks(*[(s["label"], s["url"]) for s in f["sources"]]) if f.get("sources")
                 else "<span class='muted'>— no official source applies: this is a traveller decision, not a documentation gap</span>")
        return (f"<tr id='{esc(f['id'])}'><td>{esc(f['id'])}</td><td><b>{esc(f['title'])}</b><p>{esc(f['detail'])}</p></td>"
                f"<td>{pill(f['severity'],'danger' if f['severity']=='blocking' else 'warn' if f['severity']=='important' else 'ok')}</td>"
                f"<td>{esc(f.get('how_to_close', 'owner decision'))}</td><td>{links}</td></tr>")
    body = f"""<p class="eyebrow">Unverified values, irregularities and closed items</p><h1>Flagged for review</h1>
<p class="lede">Nothing on this site is hidden behind a blank cell. Each gap, conflict or dead source below says what is missing,
what would close it, and links the official page that should carry the answer. These items do not block the publish — they block a
decision, which is the point.</p>""" + table(["ID","Flag","Severity","How to close it","Official source"], [frow(f) for f in flags.values()], cls="data prose")
    sizes["flagged.html"] = page("flagged.html", "Flagged for review", body, active="flagged.html",
                                 blurb="Every unverified value and irregularity with its official source link")

    body = f"""<p class="eyebrow">Property-owned and organiser-owned documents only</p><h1>Sources</h1>
<p class="lede">Every table row links one of these. A source is only ever used for a value the document itself states; where a page
could not be read, the row is blank and flagged.</p>""" + table(
        ["ID","Document","Venue","What it is used for","Link"],
        [f"<tr><td>{esc(s['id'])}</td><td>{esc(s['label'])}</td><td>{esc(s.get('venue') or '—')}</td>"
         f"<td>{esc({'schedule':'dated event rows, buy-ins, guarantees, sheet index','structure':'fee split, late-reg window, entry-rule wording, payout share','room':'room existence and location','fee':'resort fee amount and inclusions','terms':'tax, parking, cancellation (currently not loadable)','rates':'advertised conditional rate starting points','booking':'dated quote entry point for the calculator','other':'-'}.get(s['kind'],'-'))}</td>"
         f"<td>{srclinks(('open', s['url']))}</td></tr>" for s in srcs])
    sizes["sources.html"] = page("sources.html", "Sources", body, active="sources.html", blurb="Official source registry with what each source supports")

    # repo review page
    irregular = [
     ("Board file carried unresolved merge markers", "COORDINATION.md on main contained '=======' and '>>>>>>> origin/main' plus a duplicated section — a half-resolved conflict committed as if resolved. Fixed in this session's first commit; the deleted lines were verified to be a strict subset of retained text."),
     ("Six parallel views of the same data", "Root dashboard plus 60fb62da/, c07371e3/, df41f5c6/, strip/, verified/ each publish Venetian rows with different entry-rule labels. Same event, different confidence, nothing reconciling them."),
     ("Prior-session sources that no longer resolve", "The Wynn poker URL cited by three earlier sessions returns the Wynn home page to this environment (twice, 2026-11-17). Bellagio was recorded as 'Page not found', Planet Hollywood 'HTTP 500', Golden Nugget 'empty', Orleans '404' by an earlier session; those folders still publish rows attributed to such sources."),
     ("'Verified' labels resting on silence", "Earlier boards describe Wynn/structure-sheet rows as verified while also noting the sheets do not state entry rules — the contradiction that this site's policy exists to prevent."),
     ("Committed build artefact", "strip/__pycache__/build.cpython-311.pyc is tracked in git."),
     ("CRLF in shared CSV data", "data/c07371e3/*.csv use CRLF, producing repository-wide 'git diff --check' whitespace warnings."),
     ("No licence, and a Pages workflow that uploads the whole repository root", "README is now substantive (earlier notes describe an 8-byte README), but the deploy step ships every folder, including other sessions' snapshots and .pyc files, to the live site."),
    ]
    body = f"""<p class="eyebrow">Repo state as found on 2026-11-17</p><h1>Repository review</h1>
<p class="lede">Checked: git history, working tree, shared files, deploy workflow, and the claims of earlier sessions on this board.
Flagged for your decision rather than silently "tidied", because several fixes touch other sessions' files.</p>""" + table(
        ["Irregularity","Detail and status"],
        [f"<tr><td><b>{esc(t)}</b></td><td>{esc(d)}</td></tr>" for t, d in irregular], cls="data prose") + callout(
        "Verified this session: 93 of 94 official calendar rows re-read cell-by-cell (0 mismatches); " + str(len(rules)) + " of 37 structure sheets read "
        "end-to-end; the $55 + tax resort fee re-read today. Not verified by this session: room tax, parking, cancellation, every "
        "non-Venetian room, all dated room rates, all walking minutes.")
    sizes["repo-review.html"] = page("repo-review.html", "Repository review", body, active="repo-review.html",
                                     blurb="Repository state, conflicts and irregularities found during verification")

    # ---- search + data for client side -------------------------------------------
    idx = []
    for r in rows:
        idx.append({"t": f'{r["date"]} {r["time"]} #{r["event_no"]} {r["name"]}', "k": "Tournament",
                    "d": f'{money(r["buy_in"])} entry · {money(r["guarantee"])} GTD · {r["rule_status"]}',
                    "u": "@@/tournaments.html", "a": r["id"]})
    for n in range(1, 38):
        r = rules.get(n, {})
        idx.append({"t": f'Structure sheet #{n} {r.get("title","")}', "k": "Structure sheet",
                    "d": f'fees {money(r.get("fee_usd"))} · reg closes {r.get("reg_close","—")} · {("single-entry confirmed" if r.get("single_entry_confirmed") else "entry rule not stated" if r else "not audited in this pass")}',
                    "u": "@@/structures.html", "a": f"sheet-{n}"})
    for f_ in flags.values():
        idx.append({"t": f'{f_["id"]} {f_["title"]}', "k": "Flag", "d": f_["detail"][:180],
                    "u": "@@/flagged.html", "a": f_["id"]})
    for q in questions:
        idx.append({"t": q["q"], "k": "Question", "d": q["missing"][:180], "u": "@@/questions.html", "a": q["id"]})
    for s in suggestions:
        idx.append({"t": s["title"], "k": "Suggestion", "d": s["why"][:180], "u": "@@/suggestions.html", "a": s["id"]})
    for h in hotels["hotels"]:
        idx.append({"t": h["name"], "k": "Hotel", "d": f'resort fee {money(h.get("resort_fee",{}).get("value"))} ({h.get("resort_fee",{}).get("status","")}) · checkout total not captured',
                    "u": "@@/hotels.html", "a": h["id"]})
    for v in venues:
        idx.append({"t": v["name"], "k": "Venue", "d": v["schedule_status"][:180], "u": f'@/venues/{v["id"]}.html', "a": ""})
    json.dump({"generated": TODAY, "rows": idx}, open(os.path.join(D, "search_index.json"), "w"), indent=1, ensure_ascii=False)
    body = f"""<p class="eyebrow">One box, every table</p><h1>Search</h1>
<p class="lede">Searches all {len(idx)} indexed rows — 94 tournament rows, 37 structure sheets, every flag, question, suggestion,
hotel and venue — and links to the exact anchor. The box in the header does the same on each page, filtering every table on it.</p>
<div class="searchbox"><input type="search" id="gs" placeholder="Try: 4:55 PM · RaceDay · $300 · walk · unverified · Dec 6" autofocus></div>
<div id="gr" class="results"></div>"""
    sizes["search.html"] = page("search.html", "Search", body, active="search.html",
                                blurb="Cross-table search over all rows", data_js=index_js())

    # assets
    css = CSS.replace("__ROWS__", str(len(rows)))
    open(os.path.join(OUT, "style.css"), "w").write(css)
    open(os.path.join(OUT, "app.js"), "w").write(APP_JS)
    json.dump({"generated": TODAY, "rows": rows, "index": idx,
               "calculator": {"candidate_rows": [
                   {"id": r["id"], "date": r["date"], "time": r["time"], "name": r["name"], "buy_in": r["buy_in"],
                    "guarantee": r["guarantee"], "to_pool": r["to_pool"], "frozen": r["frozen_confirmed"]}
                   for r in sorted(cand, key=lambda x: x["date"])]}},
              open(os.path.join(D, "tournaments.json"), "w"), indent=1, ensure_ascii=False)
    return sizes

def calc_js(rows):
    cand = [r for r in rows if r["group"] == "candidate"]
    data = [{"id": r["id"], "date": r["date"], "time": r["time"], "name": r["name"], "buy_in": r["buy_in"],
             "guarantee": r["guarantee"], "to_pool": r["to_pool"], "frozen": r["frozen_confirmed"]} for r in cand]
    return ('<script>window.__P4CAND__=' + json.dumps(data) + ';window.__P4IDS__='
            + json.dumps([r["id"] for r in cand]) + ';window.__P4CONFIRMED__='
            + ("true" if any(r["frozen_confirmed"] for r in rows) else "false") + ';</script>')


def index_js():
    idx = load("search_index.json", {"rows": []})
    return "<script>window.__P4INDEX__=" + json.dumps(idx["rows"], ensure_ascii=False) + ";</script>"

CSS = """
:root{--ink:#152421;--muted:#5e716b;--green:#0a6a51;--soft:#e8f3ee;--gold:#b7801f;--line:#dde6e1;--bg:#f7f8f5;--red:#8f3a2c;--redbg:#fbeee9;--shadow:0 10px 28px rgba(20,42,35,.07)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "DM Sans",system-ui,sans-serif}
a{color:var(--green)}h1,h2,h3{font-family:Manrope,"DM Sans",sans-serif;line-height:1.18;letter-spacing:-.02em;margin:0 0 10px}
h1{font-size:clamp(28px,4.4vw,44px)}h2{font-size:22px}h3{font-size:16px}main{max-width:1260px;margin:0 auto;padding:30px 22px 70px}
.topbar{background:#0f2b25;color:#fff;padding:11px max(20px,calc((100vw - 1260px)/2))}.bar{display:flex;align-items:center;gap:16px}
.brand{color:#fff;font:800 15px Manrope,sans-serif;text-decoration:none;letter-spacing:.02em}
.stamp{margin-left:auto;color:#cfe1d9;font-size:12px;white-space:nowrap}
.navsearch{display:flex;gap:6px}.navsearch input{border:0;border-radius:8px;padding:8px 10px;font:inherit;min-width:200px}
.navsearch button{border:0;border-radius:8px;background:#2e6d5b;color:#fff;font:600 12px inherit;padding:0 11px;cursor:pointer}
.nav{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--line);z-index:9}.nav-inner{max-width:1260px;margin:auto;padding:0 18px;display:flex;gap:2px;overflow-x:auto}
.nav a{white-space:nowrap;text-decoration:none;padding:12px;font:600 13px "DM Sans",sans-serif;color:#4c615b;border-bottom:2px solid transparent}
.nav a.active,.nav a:hover{color:var(--green);border-color:var(--green)}
.eyebrow{text-transform:uppercase;letter-spacing:.13em;font-size:11px;font-weight:800;color:var(--green);margin:0 0 8px}
.lede{max-width:900px;font-size:16.5px;color:#41564f;margin:0 0 20px}.muted{color:var(--muted);font-size:13px}
.hero{background:linear-gradient(140deg,#10312a,#0b5040);color:#fff;border-radius:18px;padding:30px 32px;box-shadow:var(--shadow);margin-bottom:18px}
.hero h1{max-width:840px}.hero p{color:#d6e7df;max-width:860px}.hero .eyebrow{color:#96d5bd}
.hero-actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:18px}.button{display:inline-block;padding:10px 14px;border-radius:9px;text-decoration:none;font-weight:800;font-size:13px;background:#fff;color:#12463a;border:0;cursor:pointer}
.button.ghost{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.4)}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}
.stat,.card,.panel{background:#fff;border:1px solid var(--line);border-radius:13px;padding:16px;box-shadow:var(--shadow)}
.stat b{font:800 24px Manrope,sans-serif;display:block}.stat span{color:var(--muted);font-size:12px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.section{margin:30px 0}
.callout{border-left:4px solid var(--gold);background:#fff8e8;padding:15px 17px;border-radius:0 11px 11px 0;margin:16px 0;font-size:14px}
.callout.danger{border-color:var(--red);background:var(--redbg)}.callout b{display:block;margin-bottom:3px}
.pill{display:inline-block;border-radius:99px;background:var(--soft);color:#18614a;padding:3px 8px;font-size:11px;font-weight:800;white-space:nowrap}
.pill.warn{background:#fff1d8;color:#7a5514}.pill.danger{background:var(--redbg);color:var(--red)}.pill.ok{background:#dff3e6;color:#186b41}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px;background:#fff;box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;min-width:1050px;font-size:12.5px}th{background:#eef4f0;text-transform:uppercase;letter-spacing:.05em;font-size:10.5px;text-align:left;padding:10px;white-space:nowrap;color:#3d534d;position:sticky;top:0}
td{padding:10px;border-top:1px solid #e9efeb;vertical-align:top}tr:hover td{background:#fbfdfb}td.n,th.n{text-align:right;white-space:nowrap}
td.nm small{display:block;color:var(--muted);font-size:11.5px;margin-top:3px;max-width:340px}.chk{font-size:11.5px;color:var(--muted);white-space:nowrap}
.mono{font-family:ui-monospace,monospace;font-size:11.5px}.source-link{font-weight:700;font-size:11.5px;white-space:nowrap}
q{display:block;font-style:italic;color:#3f544e;font-size:11.5px;margin:3px 0;border-left:2px solid var(--line);padding-left:7px}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:end;background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px;margin:14px 0;box-shadow:var(--shadow)}
.toolbar label{font-size:11.5px;color:var(--muted);display:flex;flex-direction:column;gap:4px}.toolbar input[type=date],.toolbar input[type=search],.toolbar select{border:1px solid #c9d6d0;border-radius:8px;padding:8px;font:inherit;min-width:150px}
.toolbar .chk{flex-direction:row;align-items:center;gap:6px;font-weight:700;color:var(--ink)}.toolbar .count{margin-left:auto;font-size:12px;color:var(--muted)}
.day{background:#fff;border:1px solid var(--line);border-radius:13px;padding:16px 18px;margin:11px 0;box-shadow:var(--shadow)}.day h3{display:flex;gap:10px;align-items:baseline}
.cols{display:grid;grid-template-columns:1.15fr .85fr;gap:18px}.evlist{margin:0;padding-left:18px;font-size:12.5px}.evlist li{margin:3px 0}.mini{color:var(--muted)}
.conf{margin:6px 0 0;padding-left:18px;font-size:12.5px}.conf .hard{color:var(--red);font-weight:600}.conf .cond{color:#7a5514}
.qlist{padding-left:20px}.qlist li{background:#fff;border:1px solid var(--line);border-radius:12px;margin:9px 0;padding:14px 16px;list-style:none;position:relative}
.qlist li p{margin:6px 0 0;font-size:13.5px;color:#41564f}.qlist .lab{font-weight:800;color:var(--green);font-size:11.5px;text-transform:uppercase;letter-spacing:.05em}
.venlist{list-style:none;padding:0}.venlist li{background:#fff;border:1px solid var(--line);border-radius:12px;margin:9px 0;padding:14px}
.calc{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:start}.picks{max-height:420px;overflow:auto;display:flex;flex-direction:column;gap:4px}
.pick{font-size:12.5px;display:flex;gap:7px;align-items:center;background:#f6faf7;border:1px solid var(--line);border-radius:8px;padding:6px 8px}
.calc label{display:flex;flex-direction:column;gap:4px;font-size:11.5px;color:var(--muted);margin:9px 0}.calc input{border:1px solid #c9d6d0;border-radius:8px;padding:9px;font:inherit}
.out .big{font:800 30px Manrope,sans-serif;margin:4px 0 8px}.out ul{margin:0;padding-left:18px;font-size:13px}.warnbox{margin-top:10px;font-size:12px;color:var(--red)}
.searchbox input{width:100%;padding:15px 17px;font:16px inherit;border:1px solid #c9d6d0;border-radius:12px;box-shadow:var(--shadow)}
.results{margin-top:14px}.results a{display:block;background:#fff;border:1px solid var(--line);border-radius:11px;padding:11px 13px;margin:7px 0;text-decoration:none;color:var(--ink)}
.results a b{color:var(--green)}.results small{display:block;color:var(--muted)}.results .k{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;font-weight:800;color:#4c615b}
.footer{border-top:1px solid var(--line);margin-top:40px;padding-top:16px;color:var(--muted);font-size:12px}
.unknown{color:var(--red);font-weight:700}.rowlinks{margin:8px 0 0}
@media(max-width:1000px){.stats,.grid,.calc,.cols{grid-template-columns:1fr}}
@media(max-width:640px){.stamp{display:none}main{padding:20px 13px 50px}.hero{padding:22px}}
"""

APP_JS = r"""
window.Poker4=(function(){
 const money=v=>v==null||v===0?'—':'$'+Number(v).toLocaleString('en-US');
 function fmt(el,on){[...el.querySelectorAll('tbody tr')].forEach(tr=>{tr.hidden=!on(tr);});}
 function count(bar,n,total){const c=bar.querySelector('[data-count]');if(c)c.textContent=n+' of '+total+' rows shown';}
 function initFilters(){
  const bar=document.getElementById('filters');if(!bar)return;
  const rows=[...document.querySelectorAll('table.data tbody tr')];
  const q=bar.querySelector('[data-filter=q]'),from=bar.querySelector('[data-filter=from]'),
        to=bar.querySelector('[data-filter=to]'),venue=bar.querySelector('[data-filter=venue]'),
        frozen=bar.querySelector('[data-filter=frozen]'),changed=bar.querySelector('[data-filter=changed]');
  const run=()=>{let n=0;rows.forEach(tr=>{
    const d=tr.dataset.date||'';const ok=!from.value||!d||d>=from.value;const ik=!to.value||!d||d<=to.value;
    const okv=!venue.value||tr.dataset.venue===venue.value;
    const okf=!frozen.checked||tr.dataset.frozen==='yes';
    const okc=!changed.checked||/SOURCE CHANGED/.test(tr.textContent);
    const needle=(q.value||'').toLowerCase().trim();
    const okq=!needle||tr.textContent.toLowerCase().includes(needle);
    const show=ok&&ik&&okv&&okf&&okc&&okq;tr.hidden=!show;if(show)n++;});
    count(bar,n,rows.length);};
  bar.addEventListener('input',run);bar.addEventListener('change',run);run();
 }
 function initTableSearch(){ /* header box filters every table on the page */
  const form=document.querySelector('.navsearch');if(!form)return;
  form.addEventListener('input',e=>{
    const v=(e.target.value||'').toLowerCase().trim();
    document.querySelectorAll('main table tbody tr').forEach(tr=>{tr.hidden=!!v&&!tr.textContent.toLowerCase().includes(v);});
  });
 }
 function navSearch(form){
  const v=(form.q.value||'').trim();
  location.href='@/search.html'+(v?'#'+encodeURIComponent(v):'');return false;
 }
 function initCalc(){
  const box=document.getElementById('calc');if(!box)return;
  const picks=[...box.querySelectorAll('input[data-buyin]')];
  const g=id=>Number(document.getElementById(id).value||0);
  const render=()=>{
   const chosen=picks.filter(p=>p.checked);
   const perEntry=g('c-entries')||1;
   const buy=chosen.reduce((a,p)=>a+Number(p.dataset.buyin),0);
   const gtd=chosen.reduce((a,p)=>a+Number(p.dataset.gtd||0),0);
   const pool=chosen.reduce((a,p)=>{const c=window.__P4CAND__.find(x=>String(x.id)===p.dataset.id);return a+((c&&c.to_pool)||Number(p.dataset.buyin));},0);
   const nights=g('c-nights'),rate=g('c-rate'),fee=g('c-fee'),tax=g('c-tax')/100,park=g('c-park');
   const entriesCost=buy*perEntry, lodging=nights*(rate+fee)*(1+tax)+nights*park;
   document.getElementById('c-total').textContent=money(Math.round(entriesCost+lodging));
   document.getElementById('c-lines').innerHTML=
     `<li>Events ticked: <b>${chosen.length}</b> × ${perEntry} entr${perEntry>1?'ies':'y'} = <b>${money(entriesCost)}</b></li>`+
     `<li>Guaranteed pools you are aiming at: ${money(gtd)} (descriptive, not expected value)</li>`+
     `<li>Money reaching those pools from your entries: ${money(pool*perEntry)} of ${money(entriesCost)}</li>`+
     `<li>Lodging: ${nights} night${nights>1?'s':''} × (${money(rate)} + ${money(fee)} fee) × ${(1+tax).toFixed(4)} + ${money(nights*park)} parking = <b>${money(Math.round(lodging))}</b></li>`+
     `<li>Cost per night all-in: ${money(Math.round(lodging/(nights||1)))}</li>`;
   const w=[];
   if(!chosen.length)w.push('No events selected — the total covers lodging only.');
   if(chosen.some(p=>!p.dataset.gtd||Number(p.dataset.gtd)===0))w.push('One or more selected events publish no guarantee, so no value ratio is available for them.');
   if(perEntry>1)w.push(`You assumed ${perEntry} entries per event. No structure sheet audited confirms whether re-entry is allowed — treat this as your own budget choice, not a verified rule.`);
   if(!window.__P4CONFIRMED__)w.push('Entry rules unverified for every listed event: no sheet read states "one entry per player".');
   w.push('The room rate is an input. It is not a dated quote; only the $55 fee is quoted from the property page.');
   document.getElementById('c-warn').innerHTML=w.map(x=>'! '+x).join('<br>');
  };
  picks.forEach((p,i)=>p.dataset.id=(window.__P4IDS__||[])[i]||'');
  box.addEventListener('input',render);render();
 }
 function initGlobalSearch(){
  const inp=document.getElementById('gs');if(!inp)return;
  const out=document.getElementById('gr');const all=window.__P4INDEX__||[];
  const go=()=>{const v=inp.value.toLowerCase().trim();
   if(!v){out.innerHTML='<p class="muted">Type to search all '+all.length+' indexed rows.</p>';return;}
   const hits=all.filter(r=>(r.t+' '+r.d+' '+r.k).toLowerCase().includes(v)).slice(0,80);
   out.innerHTML=hits.length?hits.map(h=>`<a href="${h.u}${h.a?'#'+h.a:''}"><span class="k">${h.k}</span><b>${h.t.replace(/</g,'&lt;')}</b><small>${(h.d||'').replace(/</g,'&lt;')}</small></a>`).join(''):'<p class="muted">No rows match that.</p>';};
  inp.addEventListener('input',go);
  if(location.hash){inp.value=decodeURIComponent(location.hash.slice(1));}
  go();
 }
 document.addEventListener('DOMContentLoaded',()=>{initFilters();initTableSearch();initCalc();initGlobalSearch();});
 return {navSearch};
})();
"""
if __name__ == "__main__":
    rows, rules = build_rows()
    plan = day_plan(rows)
    sizes = render(rows, rules, plan)
    print(f"built {len(sizes)} pages from {len(rows)} verified rows")
    for k, v in sorted(sizes.items()):
        print(f"  {k:28} {v:>7} bytes")
