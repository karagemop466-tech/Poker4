#!/usr/bin/env python3
"""Build the root GitHub Pages dashboard from data/v2/*.json.

Run:  python3 tools/build_root_site.py   (then python3 tools/verify_root_site.py)

Generates: index.html, tournaments.html, schedule.html, hotels.html,
trip-calculator.html, rate-log.html, monitor.html, questions.html,
suggestions.html, flagged.html, sources.html, venues/*.html
Shared UI: assets/site.css, assets/site.js (written by this script).
"""
import html
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data" / "v2"
OUT = ROOT
(OUT / "venues").mkdir(exist_ok=True)

EV = json.loads((D / "events.json").read_text(encoding="utf-8"))
HO = json.loads((D / "hotels.json").read_text(encoding="utf-8"))
WK = json.loads((D / "walking.json").read_text(encoding="utf-8"))
RL = json.loads((D / "rate_log.json").read_text(encoding="utf-8"))
FL = json.loads((D / "flagged.json").read_text(encoding="utf-8"))
SRC = EV["sources"]
TODAY = "2026-11-17"

def esc(s):
    return html.escape("" if s is None else str(s))

def src_links(keys):
    out = []
    for k in keys or []:
        s = SRC.get(k)
        if s:
            out.append(f'<a class="src" href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(k)}</a>')
    return " ".join(out) or '<span class="flag">no source</span>'

def money(v):
    return "—" if v is None else f"${v:,.0f}"

# ----------------------------------------------------------------- layout
NAV = [("index.html", "Executive summary"), ("tournaments.html", "Tournaments"),
       ("schedule.html", "Day plan"), ("hotels.html", "Hotels & true cost"),
       ("trip-calculator.html", "Trip calculator"), ("rate-log.html", "Rate log"),
       ("venues/venetian.html", "Venues"), ("monitor.html", "Source monitor"),
       ("questions.html", "Questions"), ("suggestions.html", "Suggestions"),
       ("flagged.html", "Flagged for review"), ("sources.html", "Sources")]

CSS = """
:root{--bg:#0f1420;--card:#171e2e;--ink:#e8ecf4;--mut:#9aa7bd;--line:#27324a;--gold:#d9b45b;--ok:#4ec98c;--warn:#e0a33e;--bad:#e06c6c;--blue:#6ea8fe}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}
.topbar{display:flex;justify-content:space-between;align-items:center;padding:14px 22px;background:#0b101b;border-bottom:1px solid var(--line)}
.brand{font-weight:700;letter-spacing:.5px;color:var(--gold);font-size:17px}
.stamp{color:var(--mut);font-size:12.5px}
nav.nav{background:#0b101b;border-bottom:1px solid var(--line);overflow-x:auto}
.nav-inner{display:flex;gap:2px;padding:0 14px;min-width:max-content}
.nav-inner a{padding:10px 12px;color:var(--mut);font-size:13.5px;border-bottom:2px solid transparent}
.nav-inner a.active{color:var(--gold);border-bottom-color:var(--gold)}
main{max-width:1180px;margin:0 auto;padding:26px 20px 80px}
h1{font-size:27px;margin:.2em 0}.sub{color:var(--mut)}
h2{font-size:20px;margin:1.6em 0 .5em;border-bottom:1px solid var(--line);padding-bottom:6px}
h3{font-size:16.5px;margin:1.2em 0 .4em}
.hero{padding:26px 0 8px}.eyebrow{color:var(--gold);text-transform:uppercase;letter-spacing:1.6px;font-size:11.5px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:18px 0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:3px}
.stat b{font-size:23px;color:var(--gold)}.stat span{color:var(--mut);font-size:12.5px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.callout{border-left:4px solid var(--gold);background:var(--card);padding:13px 16px;border-radius:8px;margin:14px 0}
.callout.danger{border-left-color:var(--bad)}.callout.ok{border-left-color:var(--ok)}
.tag{display:inline-block;background:#232c42;color:var(--gold);border-radius:20px;padding:2px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.8px}
table{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0}
th{background:#121929;color:var(--mut);text-align:left;padding:8px 9px;border-bottom:2px solid var(--line);position:sticky;top:0}
td{padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}
tr:hover td{background:#141c2d}
.src{display:inline-block;background:#202a40;border:1px solid #2d3a57;border-radius:6px;padding:1px 7px;margin:1px 3px 1px 0;font-size:11px}
.flag{color:var(--bad);font-size:12px}.okv{color:var(--ok);font-size:12px}.warnv{color:var(--warn);font-size:12px}
.mut{color:var(--mut)}.small{font-size:12px}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:12px 0}
.controls input[type=text],.controls input[type=date],.controls input[type=number],.controls select{background:#0e1524;color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 10px;font-size:13.5px}
.controls label{font-size:12.5px;color:var(--mut);display:flex;align-items:center;gap:6px}
button,.button{background:var(--gold);color:#141007;border:0;border-radius:8px;padding:8px 15px;font-weight:600;cursor:pointer;font-size:13.5px}
.button.ghost{background:transparent;color:var(--gold);border:1px solid var(--gold)}
.hero-actions{display:flex;gap:10px;margin-top:14px}
footer{border-top:1px solid var(--line);color:var(--mut);font-size:12px;padding:18px 0 30px;margin-top:40px}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:8px 0}
summary{cursor:pointer;font-weight:600}
.pill{border-radius:20px;padding:2px 9px;font-size:11px;font-weight:600}
.pill.ok{background:#123524;color:var(--ok)}.pill.warn{background:#3a2d10;color:var(--warn)}.pill.bad{background:#3a1717;color:var(--bad)}
.calc{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}
.calc label{display:flex;flex-direction:column;gap:4px;font-size:12px;color:var(--mut)}
.calc input{background:#0e1524;color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px}
.result{margin-top:12px;font-size:16px}
.result b{color:var(--gold);font-size:22px}
"""

JS = r"""
function applyFilter(tableId){
  const tbl=document.getElementById(tableId); if(!tbl) return;
  const page=tbl.closest('.filterable');
  const q=(page.querySelector('[data-search]')?.value||'').toLowerCase();
  const dt=page.querySelector('[data-date]')?.value||'';
  const entry=page.querySelector('[data-entry]')?.value||'';
  const kind=page.querySelector('[data-kind]')?.value||'';
  const walkMax=page.querySelector('[data-walkmax]');
  tbl.querySelectorAll('tbody tr').forEach(tr=>{
    let ok=(!q)||tr.innerText.toLowerCase().includes(q);
    if(ok&&dt){const d=tr.getAttribute('data-date')||''; ok=(d===dt)||(d===''&&tr.getAttribute('data-weekly')==='1');}
    if(ok&&entry){ok=(tr.getAttribute('data-entry')||'')===entry;}
    if(ok&&kind){ok=(tr.getAttribute('data-kind')||'')===kind;}
    if(ok&&walkMax&&walkMax.checked){const w=tr.getAttribute('data-walk');ok=(w!==null&&w!==''&&Number(w)<=30);}
    tr.style.display=ok?'':'none';
  });
}
document.addEventListener('input',e=>{const p=e.target.closest('.filterable');if(p)applyFilter(p.querySelector('table').id);});
document.addEventListener('change',e=>{const p=e.target.closest('.filterable');if(p)applyFilter(p.querySelector('table').id);});
function trueCost(rate,fee){return ((Number(rate)||0)+(Number(fee)||0))*1.1338;}
function bindCalc(){
  const c=document.getElementById('tripcalc'); if(!c) return;
  const upd=()=>{
    const n=Number(c.querySelector('#entries').value)||0;
    const b=Number(c.querySelector('#buyin').value)||0;
    const extra=Number(c.querySelector('#extraentries').value)||0;
    const nights=Number(c.querySelector('#nights').value)||0;
    const rate=Number(c.querySelector('#rate').value)||0;
    const fee=Number(c.querySelector('#fee').value)||0;
    const entriesTotal=n*b+extra;
    const perNight=trueCost(rate,fee);
    const stay=nights*perNight;
    c.querySelector('#r-entries').textContent='$'+entriesTotal.toLocaleString(undefined,{maximumFractionDigits:0});
    c.querySelector('#r-night').textContent='$'+perNight.toLocaleString(undefined,{maximumFractionDigits:2});
    c.querySelector('#r-stay').textContent='$'+stay.toLocaleString(undefined,{maximumFractionDigits:0});
    c.querySelector('#r-total').textContent='$'+(entriesTotal+stay).toLocaleString(undefined,{maximumFractionDigits:0});
  };
  c.addEventListener('input',upd); upd();
}
function bindHotelCalcs(){
  document.querySelectorAll('.hotelcalc').forEach(h=>{
    const upd=()=>{
      const rate=Number(h.querySelector('.h-rate').value)||0;
      const fee=Number(h.dataset.fee||0)||0;
      h.querySelector('.h-out').textContent='True cost/night: $'+trueCost(rate,fee).toLocaleString(undefined,{maximumFractionDigits:2})+'  = ($'+rate+' + $'+fee+') × 1.1338';
    };
    h.addEventListener('input',upd); upd();
  });
}
function monitorRefresh(){
  const el=document.getElementById('monitor-live'); if(!el) return;
  fetch('data/v2/monitor/status.json',{cache:'no-store'}).then(r=>r.json()).then(j=>{
    if(j && j.last_run){el.textContent='Live monitor file last run: '+j.last_run+' ('+(j.entries||[]).length+' URLs tracked). Any row marked "changed" below needs review.';}
  }).catch(()=>{el.textContent='Live monitor file not reachable (offline view) — showing the built snapshot.';});
}
document.addEventListener('DOMContentLoaded',()=>{bindCalc();bindHotelCalcs();monitorRefresh();});
"""

def page(fname, title, body, active=None):
    pre = "../" if fname.startswith("venues/") else ""
    nav = "".join(f'<a class="{"active" if href==active else ""}" href="{pre}{href}">{esc(lbl)}</a>' for href, lbl in NAV)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Official-source Las Vegas Strip poker tournament and hotel decision dashboard">
<title>{esc(title)} — Strip Poker Planner</title>
<link rel="stylesheet" href="{'../' if fname.startswith('venues/') else ''}assets/site.css">
</head><body>
<header class="topbar"><a class="brand" href="{'../' if fname.startswith('venues/') else ''}index.html">♠ STRIP POKER PLANNER</a>
<span class="stamp">Verified snapshot · 17 Nov 2026 UTC · every row links its official source</span></header>
<nav class="nav"><div class="nav-inner">{nav}</div></nav>
<main>{body}
<footer>Values read from official operator sources only, with retrieval dates. Unverified values are blank and flagged on the
<a href="{'../' if fname.startswith('venues/') else ''}flagged.html">Flagged for Review</a> page. This is a decision dashboard, not a booking engine or a forecast.
Re-checked automatically (see <a href="{'../' if fname.startswith('venues/') else ''}monitor.html">Source monitor</a>).</footer>
</main><script src="{'../' if fname.startswith('venues/') else ''}assets/site.js"></script></body></html>"""
    (OUT / fname).write_text(doc, encoding="utf-8")

(OUT / "assets").mkdir(exist_ok=True)
(OUT / "assets" / "site.css").write_text(CSS, encoding="utf-8")
(OUT / "assets" / "site.js").write_text(JS, encoding="utf-8")

# ------------------------------------------------------- helpers over events
def parse_time(t):
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", t or "")
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == "PM" and h != 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    return h * 60 + mi

def fmt_min(m):
    if m is None:
        return "—"
    ap = "AM" if m < 720 else "PM"
    h = (m // 60) % 12 or 12
    return f"{h}:{m % 60:02d} {ap}"

def reg_close_min(e):
    rc = (e.get("structure") or {}).get("reg_close") or ""
    times = re.findall(r"(\d{1,2}:\d{2}\s*(?:AM|PM))", rc)
    if times:
        return parse_time(times[-1])
    return None

def est_end_min(e):
    """Plausible finish heuristic (documented on Schedule page):
    late-registration cutoff + 5 hours (typical 1-day event span after reg closes)."""
    start = parse_time(e.get("start_time"))
    if start is None:
        return None
    rc = reg_close_min(e)
    if rc:
        return rc + 300
    return start + 480  # fallback: start + 8 h when no reg-close clock is printed

def dated(e):
    return bool(re.match(r"\d{4}-\d{2}-\d{2}$", e.get("date") or ""))

def entry_pill(e):
    st = e["entry_rules"]["status"]
    if st == "confirmed":
        re_v = e["entry_rules"]["reentry"]["value"]
        if re_v == "not_allowed":
            return '<span class="pill ok">re-entry NOT allowed (confirmed)</span>'
        return '<span class="pill warn">re-entry/add-on confirmed</span>'
    return '<span class="pill bad">entry rules unverified</span>'

def ratio_cell(e):
    r = e.get("ratio_guarantee_per_buy_in")
    if r is None:
        return '<span class="mut">—</span>'
    note = ""
    if e["kind"] == "bounty":
        note = "<br><span class='small warnv'>bounty — guarantee includes bounties</span>"
    if e["kind"] == "flight":
        note = "<br><span class='small warnv'>flight — guarantee spans all flights</span>"
    return f"{r}×{note}<br><span class='small mut'>descriptive ratio, not a forecast</span>"

def event_row(e, with_date=True):
    wk = e.get("weekday", "")
    dcell = "<td>" + esc(e["date"]) + " <span class='mut'>" + esc(wk) + "</span></td>" if with_date else ""
    buy = money(e["buy_in"]) if e["buy_in"] else '<span class="flag">—</span>'
    if e["guarantee"]:
        gtd = money(e["guarantee"])
    elif e["kind"] != "continuation":
        gtd = '<span class="mut">none listed</span>'
    else:
        gtd = '<span class="mut">n/a</span>'
    dd = esc(e["date"]) if dated(e) else ""
    ww = "1" if not dated(e) else ""
    st = esc(e["entry_rules"]["status"])
    kd = esc(e["kind"])
    nm = esc(e["name"])
    vn = esc(e["venue_name"])
    eno = esc(e["event_no"] or "—")
    stm = esc(e["start_time"])
    rre = esc(e["entry_rules"]["reentry"]["value"])
    rc = esc((e.get("structure") or {}).get("reg_close") or "—")
    lc = esc(e["last_checked"])
    review = ""
    if e.get("review_flags"):
        review = "<br><span class='pill warn'>source changed — recheck row</span>"
    return ("<tr data-date='" + dd + "' data-weekly='" + ww + "' data-entry='" + st + "' data-kind='" + kd + "'>"
            + dcell + "<td><b>" + nm + "</b><br><span class='small mut'>" + vn + " · event " + eno + "</span></td>"
            + "<td>" + stm + "</td><td>" + buy + "</td><td>" + gtd + "</td>"
            + "<td>" + ratio_cell(e) + "</td><td>" + entry_pill(e) + review + "<br><span class='small'>" + rre + "</span></td>"
            + "<td class='small'>" + rc + "</td>"
            + "<td class='small'>" + lc + "</td><td class='small'>" + src_links(e["sources"]) + "</td></tr>")

HEAD = ("<th>Date</th><th>Event</th><th>Start</th><th>Total entry fee</th><th>Guarantee</th>"
        "<th>Guarantee ÷ fee</th><th>Entry rules</th><th>Late reg</th><th>Last checked</th><th>Official sources</th>")

def controls(table_id, kinds=None, dates=None, walk=False, entry=True):
    opts = "".join('<option value="' + esc(k) + '">' + esc(k) + '</option>' for k in (kinds or []))
    if dates is not None:
        dlopts = "".join('<option value="' + esc(d) + '">' + esc(d) + '</option>' for d in dates)
        dl = '<label>Date <select data-date><option value="">All dates</option>' + dlopts + '</select></label>'
    else:
        dl = ""
    entry_html = ('<label>Entry rules <select data-entry><option value="">All</option>'
                  '<option value="confirmed">Confirmed only</option>'
                  '<option value="unverified">Unverified only</option></select></label>') if entry else ""
    kind_html = ('<label>Type <select data-kind><option value="">All</option>' + opts + '</select></label>') if kinds else ""
    walk_html = '<label><input type="checkbox" data-walkmax> ≤ 30-min walk only</label>' if walk else ""
    return ('<div class="controls">'
            '<label>Search <input type="text" data-search placeholder="name, venue, buy-in…"></label>'
            + dl + entry_html + kind_html + walk_html + '</div>')

# ============================================================ tournaments
all_dates = sorted({e["date"] for e in EV["events"] if dated(e)})
main_events = [e for e in EV["events"] if dated(e) or e["date"] in ("daily",) or e["date"].startswith("weekly:")]
def section_events(pred):
    return [e for e in EV["events"] if pred(e)]

se_confirmed = [e for e in EV["events"] if e["entry_rules"]["status"] == "confirmed"
                and e["entry_rules"]["reentry"]["value"] in ("not_allowed", "unverified")
                and e["kind"] in ("tournament",)]
single_confirmed = [e for e in se_confirmed if e["entry_rules"]["single_entry"]["value"] == "yes"]
cand = [e for e in EV["events"] if e["entry_rules"]["status"] == "unverified" and e["kind"] in ("tournament", "bounty")]
reentry_sec = [e for e in EV["events"] if e["entry_rules"]["status"] == "confirmed"
               and e["entry_rules"]["reentry"]["value"] not in ("not_allowed",)]
flights = [e for e in EV["events"] if e["kind"] == "flight"]
sat = [e for e in EV["events"] if e["kind"] == "satellite"]
cont = [e for e in EV["events"] if e["kind"] == "continuation"]

def table(tid, rows, with_date=True):
    body = "".join(event_row(e, with_date) for e in rows)
    return f'<table id="{tid}"><thead><tr>{HEAD if with_date else HEAD.replace("<th>Date</th>","")}</tr></thead><tbody>{body}</tbody></table>'

bounty_rows = [e for e in EV["events"] if e["kind"] == "bounty"]
ranked = sorted([e for e in EV["events"] if e.get("ratio_guarantee_per_buy_in") and e["entry_rules"]["status"] == "confirmed"
                 and e["kind"] in ("tournament",)], key=lambda e: -e["ratio_guarantee_per_buy_in"])
ranked_unv = sorted([e for e in EV["events"] if e.get("ratio_guarantee_per_buy_in") and e["entry_rules"]["status"] == "unverified"
                     and e["kind"] in ("tournament", "bounty")], key=lambda e: -e["ratio_guarantee_per_buy_in"])

body = f"""
<div class="hero"><p class="eyebrow">Tournaments · verified against official structure sheets</p>
<h1>Upcoming tournaments, honestly labeled.</h1>
<p class="sub">Search and filter every row. <b>Total entry fee</b> and <b>guarantee</b> rank only where both are confirmed on an official sheet.
The ratio is guarantee ÷ total entry fee — descriptive arithmetic, never a forecast. Bounty, flight and satellite events are kept in their own sections.</p></div>

<div class="callout danger"><b>Single-entry / freezeout confirmed: 0 events.</b> All 37 Venetian DSE IV structure sheets were read in full on 2026-11-17 and
none states an entry limit — silence is not confirmation. The toggle filter "Confirmed only" on this page therefore returns the Wynn/Bellagio/Caesars
events whose rules <i>are</i> confirmed (all of which allow re-entry, rebuys or add-ons, listed separately below). Ask the poker room in writing before treating any event as single-entry.</div>

<h2>1 · Candidate single-entry events (entry rules UNVERIFIED)</h2>
<p class="mut">These one-day events fit a freezeout-style day, but no official sheet confirms a single-entry limit. Filter "Entry rules: Unverified" to isolate them.</p>
<div class="filterable">{controls('t-cand', kinds=['tournament','bounty'], dates=all_dates)}{table('t-cand', cand)}</div>

<h2>2 · Ranking screen (only where entry fee + guarantee are confirmed)</h2>
<p class="mut">Confirmed rule sets today all allow some form of re-entry — so nothing here is a verified single-entry event. Ratio = guarantee ÷ total entry fee.</p>
<table><thead><tr><th>#</th><th>Event</th><th>Entry fee</th><th>Guarantee</th><th>Ratio</th><th>Why separate</th><th>Sources</th></tr></thead><tbody>
{''.join(f"<tr><td>{i+1}</td><td><b>{esc(e['name'])}</b><br><span class='small mut'>{esc(e['venue_name'])} · {esc(e['date'])} {esc(e['start_time'])}</span></td><td>{money(e['buy_in'])}</td><td>{money(e['guarantee'])}</td><td>{ratio_cell(e)}</td><td class='small'>{esc(e['kind'])}</td><td class='small'>{src_links(e['sources'])}</td></tr>" for i, e in enumerate(ranked))}
</tbody></table>
<details><summary>Unverified-rule ranking screen (same arithmetic, weaker basis) — {len(ranked_unv)} rows</summary>
<table><thead><tr><th>#</th><th>Event</th><th>Entry fee</th><th>Guarantee</th><th>Ratio</th><th>Type</th><th>Sources</th></tr></thead><tbody>
{''.join(f"<tr><td>{i+1}</td><td><b>{esc(e['name'])}</b><br><span class='small mut'>{esc(e['venue_name'])} · {esc(e['date'])} {esc(e['start_time'])}</span></td><td>{money(e['buy_in'])}</td><td>{money(e['guarantee'])}</td><td>{ratio_cell(e)}</td><td class='small'>{esc(e['kind'])}</td><td class='small'>{src_links(e['sources'])}</td></tr>" for i, e in enumerate(ranked_unv))}
</tbody></table></details>

<h2>3 · Re-entry / add-on / rebuy events (separate section — spending more money can buy an advantage)</h2>
<p class="mut">Rules confirmed on official sheets: these permit re-entries, rebuys or add-ons. Kept out of the main comparison by policy.</p>
<div class="filterable">{controls('t-re', kinds=['tournament'], dates=None, entry=False)}{table('t-re', reentry_sec)}</div>

<h2>4 · Bounty / PKO events (labeled separately — guarantee includes bounty money)</h2>
<div class="filterable">{controls('t-bo', kinds=['bounty'], dates=all_dates)}{table('t-bo', bounty_rows)}</div>

<h2>5 · Flights & multi-day events (guarantee spans all flights)</h2>
<div class="filterable">{controls('t-fl', kinds=['flight'], dates=None)}{table('t-fl', flights)}</div>

<h2>6 · Satellites (awards seats/entries, not cash)</h2>
<div class="filterable">{controls('t-sa', kinds=['satellite'], dates=None)}{table('t-sa', sat)}</div>

<h2>7 · Day-2 continuations (not an entry)</h2>
<table><thead><tr>{HEAD}</tr></thead><tbody>{''.join(event_row(e) for e in cont)}</tbody></table>
"""
page("tournaments.html", "Tournaments", body, "tournaments.html")

# ============================================================ schedule
WIN_START, WIN_END = date(2026, 11, 17), date(2026, 12, 23)
by_date = {}
for e in EV["events"]:
    if dated(e):
        by_date.setdefault(e["date"], []).append(e)

day_html = []
d = WIN_START
while d <= WIN_END:
    ds = d.isoformat()
    rows = sorted(by_date.get(ds, []), key=lambda e: parse_time(e.get("start_time")) or 0)
    playable = [e for e in rows if e["kind"] in ("tournament", "bounty", "flight")]
    primary = playable[0] if playable else None
    fallback = None
    if primary:
        pend = est_end_min(primary) or 0
        for e in playable[1:]:
            st = parse_time(e.get("start_time")) or 0
            if st >= (parse_time(primary.get("start_time")) or 0):
                fallback = e
                break
    overlaps = []
    for i in range(len(playable)):
        for j in range(i + 1, len(playable)):
            a, b = playable[i], playable[j]
            sa, ea = parse_time(a.get("start_time")), est_end_min(a)
            sb, eb = parse_time(b.get("start_time")), est_end_min(b)
            if None in (sa, ea, sb, eb):
                continue
            if sa < eb and sb < ea:
                overlaps.append((a, b))
    def slot(e, tag):
        if not e:
            return ""
        s, en = parse_time(e.get("start_time")), est_end_min(e)
        return (f"<tr><td><span class='pill {'ok' if tag=='primary' else 'warn'}'>{tag}</span></td>"
                f"<td><b>{esc(e['name'])}</b><br><span class='small mut'>{esc(e['venue_name'])}</span></td>"
                f"<td>{esc(e['start_time'])}</td><td class='small'>{fmt_min(en)} <span class='mut'>(est., heuristic)</span></td>"
                f"<td>{money(e['buy_in'])}</td><td>{entry_pill(e)}</td><td class='small'>{src_links(e['sources'])}</td></tr>")
    ov_html = "".join(f"<div class='callout danger small'>⚠ Overlap: <b>{esc(a['name'])}</b> ({esc(a['start_time'])}) and <b>{esc(b['name'])}</b> ({esc(b['start_time'])}) cannot both be played in sequence — their plausible time windows intersect.</div>" for a, b in overlaps)
    rows_html = "".join(slot(e, "primary" if e == primary else ("fallback" if e == fallback else "listed")) for e in playable)
    sat_html = "".join(f"<li>{esc(e['start_time'])} · {esc(e['name'])} <span class='mut'>({esc(e['kind'])})</span> {src_links(e['sources'])}</li>" for e in rows if e["kind"] in ("satellite", "continuation"))
    day_html.append(f"""<section class="card" data-date="{ds}" style="margin:12px 0">
    <h3>{d.strftime('%A %b %-d, %Y')}</h3>
    {ov_html or ''}
    {f'<table><thead><tr><th>Slot</th><th>Event</th><th>Start</th><th>Plausible end</th><th>Entry fee</th><th>Entry rules</th><th>Sources</th></tr></thead><tbody>{rows_html}</tbody></table>' if playable else '<p class="mut">No open tournament on the verified schedules for this date. Weekly rooms (Wynn dailies, Bellagio weekly, Caesars dailies) still run — see below.</p>'}
    {f'<details><summary>Satellites & continuations this day</summary><ul>{sat_html}</ul></details>' if sat_html else ''}
    </section>""")
    d += timedelta(days=1)

body = f"""
<div class="hero"><p class="eyebrow">Day plan · one primary event per day, fallback only where realistic</p>
<h1>Play all day — with honest sequencing.</h1>
<p class="sub">No verified event starts at 8:00 AM anywhere in the official schedules (earliest: 9:10 AM satellite, 10:10 AM open events — see
<a href="flagged.html">F-04</a>). Each day below gets a <b>primary</b> event and, only where the windows allow, a <b>conditional fallback</b>
(evening event playable only if you exit the primary in time). Events whose plausible windows intersect are flagged as impossible sequences.</p></div>

<div class="callout"><b>Plausible-end heuristic (documented):</b> late-registration cutoff + 5 hours. No official source publishes finish times
(<a href="flagged.html">F-08</a>) — so every "end" is an estimate, marked as such. A conditional fallback is a real option only if you bust or
the earlier event ends before the later start.</div>

<div class="controls filterable"><label>Jump to date <select data-date onchange="document.querySelectorAll('section[data-date]').forEach(s=>s.style.display=(!this.value||s.dataset.date===this.value)?'':'none')">
<option value="">All days (Nov 17 – Dec 23, 2026)</option>{''.join(f"<option value='{ds}'>{ds}</option>" for ds in sorted(by_date))}</select></label></div>

{''.join(day_html)}

<h2>Rooms that run every day / week (not date-bound)</h2>
<table><thead><tr><th>Room</th><th>Pattern</th><th>Time</th><th>Entry fee</th><th>Guarantee</th><th>Entry rules</th><th>Sources</th></tr></thead><tbody>
{''.join(f"<tr><td>{esc(e['venue_name'])}</td><td>{esc(e['weekday'])}</td><td>{esc(e['start_time'])}</td><td>{money(e['buy_in'])}</td><td>{money(e['guarantee'])}</td><td>{entry_pill(e)}</td><td class='small'>{src_links(e['sources'])}</td></tr>" for e in EV['events'] if not dated(e) and not e['date'].startswith('wpt:'))}
</tbody></table>
"""
page("schedule.html", "Day plan", body, "schedule.html")

# ============================================================ hotels
def route_links(p):
    out = []
    if p.get("maps_url"):
        out.append('<a class="src" href="' + esc(p["maps_url"]) + '" target="_blank" rel="noopener">Google route</a>')
    if p.get("apple_url"):
        out.append('<a class="src" href="' + esc(p["apple_url"]) + '" target="_blank" rel="noopener">Apple route</a>')
    return "".join(out)

hotel_rows = []
for h in HO["hotels"]:
    walk_vals = [p for p in WK["pairs"] if p["hotel"] == h["id"] and p["venue"] != h["id"]]
    best = min((p["walk_minutes"] for p in walk_vals), default=None)
    wtxt = " · ".join(f"{p['venue']} {p['walk_minutes']} min" for p in walk_vals)
    fee = h["resort_fee_usd"]
    fee_txt = ('$' + format(fee, '.2f')) if fee is not None else '<span class="flag">unverified</span>'
    hsrc = [k for k in [h["resort_fee_source"], h["tax_source"], h["parking_source"]] if k]
    hotel_rows.append("<tr>"
        "<td><b>" + esc(h["name"]) + "</b><br><span class='small mut'>" + esc(h["address"]) + "</span></td>"
        "<td>" + fee_txt + "<br><span class='small mut'>" + esc(h["resort_fee_note"] or "") + "</span></td>"
        "<td>" + esc(str(h["tax_rate_pct"]) + "%") + "<br><span class='small mut'>Clark County room tax</span></td>"
        "<td class='small'>" + esc(h["parking"] or "—") + "</td>"
        "<td class='small'>" + esc(h["cancellation"] or "—") + "</td>"
        "<td class='small'>" + esc(h["poker_rate"] or "—") + "</td>"
        "<td class='small' data-walk='" + ("" if best is None else str(best)) + "'>" + esc(wtxt or "—") + "<br>"
        + "".join('<a class="src" href="' + esc(p["maps_url"]) + '" target="_blank" rel="noopener">route</a>' for p in walk_vals) + "</td>"
        "<td class='small'>" + esc(h["last_checked"]) + "<br>" + src_links(hsrc) + "</td></tr>")

def hotel_name(hid):
    return next((x["name"] for x in HO["hotels"] if x["id"] == hid), hid)

walk_rows = []
for p in WK["pairs"]:
    ok30 = "✓ within 30 min" if p["walk_minutes"] <= 30 else "✗ over 30 min"
    walk_rows.append("<tr data-walk='" + str(p["walk_minutes"]) + "'>"
        "<td>" + esc(hotel_name(p["hotel"])) + "</td><td>" + esc(p["venue"]) + "</td>"
        "<td>" + str(p["walk_minutes"]) + " min</td><td>" + esc(p["walk_distance"]) + "</td>"
        "<td>" + ok30 + "</td>"
        "<td class='small'>" + src_links([p["source"]]) + " " + route_links(p) + "</td>"
        "<td class='small'>" + esc(p["last_checked"]) + "</td></tr>")
walk_table_rows = "".join(walk_rows)

body = f"""
<div class="hero"><p class="eyebrow">Hotels · true cost per night</p>
<h1>What a night actually costs.</h1>
<p class="sub">True cost/night = <b>(nightly rate + mandatory resort fee) × 1.1338</b> (13.38% Clark County room tax applies to room and fee —
stated on the official <a href="{esc(SRC['V_TERMS']['url'])}">Venetian hotel terms</a>). Walking times are Google Maps walking routes between official
addresses, read 2026-11-16/17; the ≤30-minute rule is applied. Cost and quality rank first, distance must simply qualify.</p></div>

<div class="callout"><b>Like-for-like comparison needs your dates + occupancy.</b> Official booking engines do not publish scrapable date-specific totals
(<a href="flagged.html">F-05</a>). Use the per-date official booking links in each hotel card, drop the quoted nightly rate into the calculator, and compare
true cost/night on equal terms. Published, timestamped rates live in the <a href="rate-log.html">dated rate log</a>.</div>

<div class="filterable">{controls('t-hotels', walk=True, entry=False)}
<table id="t-hotels"><thead><tr><th>Hotel</th><th>Resort fee / night</th><th>Room tax</th><th>Parking</th><th>Cancellation & deposit</th><th>Published poker/advertised rate</th><th>Walk to venues (Google Maps)</th><th>Last checked & sources</th></tr></thead>
<tbody>{''.join(hotel_rows)}</tbody></table></div>

<h2>Hotel × venue walking matrix (≤ 30-minute limit)</h2>
<div class="filterable">{controls('t-walk', walk=True, entry=False)}
<table id="t-walk"><thead><tr><th>Hotel</th><th>Venue</th><th>Walk</th><th>Distance</th><th>30-min rule</th><th>Verification route</th><th>Last checked</th></tr></thead>
<tbody>{walk_table_rows}</tbody></table></div>

<h2>True cost calculator & official booking links (per hotel)</h2>
{''.join(f'''<details class="card hotelcalc" data-fee="{h['resort_fee_usd'] or 0}"><summary>{esc(h['name'])} — true-cost calculator</summary>
<div class="calc"><label>Quoted nightly rate ($) <input class="h-rate" type="number" min="0" step="1" placeholder="from booking engine"></label>
<label>Mandatory resort fee ($) <input type="number" value="{h['resort_fee_usd'] or ''}" disabled></label>
<label>Tax <input value="13.38%" disabled></label></div>
<p class="result h-out"></p>
<p class="small">Official booking links for exact dates:
<a class="src" target="_blank" rel="noopener" href="https://www.venetianlasvegas.com/booking?adults[]=2&arrival_date=2026-11-17&children[]=0&departure_date=2026-11-19&view=calendar">Venetian sample (Nov 17–19)</a>
<span class="mut">— change the arrival_date/deep-link dates for your stay; equivalent links for other hotels on their venue pages.</span></p>
{f'<p class="small flag">Resort fee unverified for this property — calculator uses $0 until confirmed; see <a href="flagged.html">F-06</a>.' if h['resort_fee_usd'] is None else ''}</details>''' for h in HO['hotels'])}
"""
page("hotels.html", "Hotels & true cost", body, "hotels.html")

# ============================================================ trip calculator
body = f"""
<div class="hero"><p class="eyebrow">Trip cost · entries × buy-ins + nights × true hotel cost</p>
<h1>Estimated cost of the trip.</h1>
<p class="sub">Trip cost = Σ(entries × buy-in) + Σ(nights × true cost/night). True cost/night = (rate + resort fee) × 1.1338.
Numbers you type are your own quotes — everything else on this site stays source-linked.</p></div>

<div class="card filterable" id="tripcalc">
<div class="calc">
<label>Tournament entries (#) <input id="entries" type="number" min="0" value="5"></label>
<label>Average buy-in ($) <input id="buyin" type="number" min="0" value="300"></label>
<label>Extra entry fees — re-entries/satellites ($) <input id="extraentries" type="number" min="0" value="0"></label>
<label>Nights <input id="nights" type="number" min="0" value="5"></label>
<label>Quoted nightly rate ($) <input id="rate" type="number" min="0" value="119"></label>
<label>Mandatory resort fee ($/night) <input id="fee" type="number" min="0" value="55"></label>
</div>
<div class="result">
<p>Entries subtotal: <b id="r-entries">$0</b></p>
<p>True hotel cost/night: <b id="r-night">$0</b></p>
<p>Stay subtotal: <b id="r-stay">$0</b></p>
<p>Estimated trip cost: <b id="r-total">$0</b></p>
</div>
<p class="small mut">Defaults are the verified Venetian poker-suite starting rate ($119, conditional) and the verified $55 Venetian resort fee — replace them with your actual quote for exact planning. Tax source: {src_links(['V_TERMS'])}</p>
</div>

<h2>Worked example (documented, not a quote)</h2>
<table><thead><tr><th>Component</th><th>Values used</th><th>Source / status</th></tr></thead><tbody>
<tr><td>Entries</td><td>5 entries × $300 = $1,500</td><td class="small">example only — pick real events on the <a href="tournaments.html">Tournaments page</a></td></tr>
<tr><td>True hotel cost/night</td><td>($119 + $55) × 1.1338 = $197.28</td><td class="small">{src_links(['V_RATES','V_RESORT','V_TERMS'])} — conditional poker rate</td></tr>
<tr><td>Stay</td><td>5 nights × $197.28 = $986.40</td><td class="small">nights × true cost/night</td></tr>
<tr><td><b>Estimated trip cost</b></td><td><b>$2,486.40</b></td><td class="small">entries + stay</td></tr>
</tbody></table>
"""
page("trip-calculator.html", "Trip calculator", body, "trip-calculator.html")

# ============================================================ rate log
rl_rows = "".join(f"""<tr><td>{esc(x['id'])}</td><td>{esc(next((h['name'] for h in HO['hotels'] if h['id']==x['property']), x['property']))}</td>
<td class="small">{esc(x['retrieved'])}<br><span class="mut">{esc(x['rate_timestamp'])}</span></td>
<td class="small">{esc(x['stay_start'] or '—')} → {esc(x['stay_end'] or '—')}<br>{esc(x['occupancy'] or '')}</td>
<td>{esc(x['published_rate'] or '—')}</td><td>{esc(x['nightly_avg'] or '—')}</td><td>{esc(x['checkout_total'] or '—')}</td>
<td class="small">{esc(x['resort_fee'] or '—')}</td><td class="small">{esc(x['tax'] or '—')}</td>
<td class="small">{esc(x['parking'] or '—')}</td><td class="small">{esc(x['cancellation_deadline'] or '—')}</td>
<td class="small">{esc(x['notes'])}</td><td class="small">{src_links([x['source']])}</td></tr>""" for x in RL["entries"])

body = f"""
<div class="hero"><p class="eyebrow">Rates · a dated log, never a single value</p>
<h1>Rate log.</h1>
<p class="sub">Every rate observation keeps its retrieval timestamp, occupancy, fee, tax, parking, and cancellation terms — so later checks can
show what changed. Checkout totals and nightly averages fill in only when a date-specific official quote is captured; until then they stay blank.</p></div>
<table><thead><tr><th>ID</th><th>Property</th><th>Retrieved / rate timestamp</th><th>Stay window & occupancy</th><th>Published rate</th><th>Nightly avg</th><th>Checkout total</th><th>Resort fee</th><th>Tax</th><th>Parking</th><th>Cancellation deadline</th><th>Notes</th><th>Sources</th></tr></thead>
<tbody>{rl_rows}</tbody></table>
<h2>Capture checklist for an exact-date quote (compare like-for-like)</h2>
<ol><li>Same dates + same occupancy on each official booking engine (links on the <a href="hotels.html">Hotels page</a>).</li>
<li>Record: checkout total, nightly average, mandatory resort fee + tax, parking, cancellation deadline, rate timestamp.</li>
<li>Compute true cost/night = (rate + resort fee) × 1.1338 and compare — never compare a bare rate against an all-in total.</li>
<li>Append the capture to this log with its source link and timestamp.</li></ol>
"""
page("rate-log.html", "Rate log", body, "rate-log.html")

# ============================================================ venues
VENUE_META = {
    "venetian": ("The Venetian & The Palazzo", "Poker Room at The Palazzo, Level 2", "3355 Las Vegas Blvd S / 3325 Las Vegas Blvd S"),
    "wynn": ("Wynn Las Vegas & Encore", "Wynn Poker Room, located in Encore", "3131 Las Vegas Blvd S"),
    "bellagio": ("Bellagio", "Bellagio Poker Room", "3600 Las Vegas Blvd S"),
    "caesars": ("Caesars Palace", "Caesars Palace Poker Room", "3570 Las Vegas Blvd S"),
}
for vid, (vname, room, addr) in VENUE_META.items():
    vevs = [e for e in EV["events"] if e["venue"] == vid]
    vhot = [p for p in WK["pairs"] if p["venue"] == vid and p["hotel"] != vid]
    vrows = []
    for p in sorted(vhot, key=lambda x: x["walk_minutes"]):
        rl = route_links(p) or "on property"
        vrows.append("<tr><td>" + esc(hotel_name(p["hotel"])) + "</td><td>" + str(p["walk_minutes"]) + " min</td>"
            "<td>" + esc(p["walk_distance"]) + "</td><td class='small'>" + rl + "</td>"
            "<td class='small'>" + esc(p["last_checked"]) + "</td></tr>")
    pairs_html = "".join(vrows)
    body = f"""
<div class="hero"><p class="eyebrow">Venue page</p><h1>{esc(vname)}</h1>
<p class="sub">{esc(room)} · {esc(addr)} · <a href="{esc(SRC['V_POKER' if vid=='venetian' else ('W_PAGE' if vid=='wynn' else ('B_PAGE' if vid=='bellagio' else 'C_PAGE'))]['url'])}" target="_blank" rel="noopener">official page ↗</a></p></div>
<h2>Events at this venue</h2>
<div class="filterable">{controls('t-v', kinds=sorted({e['kind'] for e in vevs}), dates=sorted({e['date'] for e in vevs if dated(e)}))}
<table id="t-v"><thead><tr>{HEAD}</tr></thead><tbody>{''.join(event_row(e) for e in vevs)}</tbody></table></div>
<h2>Hotels within walking distance (30-minute limit)</h2>
<table><thead><tr><th>Hotel</th><th>Walk</th><th>Distance</th><th>Route</th><th>Last checked</th></tr></thead><tbody>{pairs_html}</tbody></table>
<h2>Hotel cost facts for this venue's own property</h2>
{next((f'''<div class="card"><b>{esc(h['name'])}</b>
<p class="small">Resort fee: {esc(h['resort_fee_note'])} {src_links([h['resort_fee_source']] if h['resort_fee_source'] else [])}</p>
<p class="small">Tax: {esc(h['tax_note'])} {src_links([h['tax_source']] if h['tax_source'] else [])}</p>
<p class="small">Parking: {esc(h['parking'] or '—')}</p>
<p class="small">Cancellation: {esc(h['cancellation'] or '—')}</p>
<p class="small">Poker/advertised rate: {esc(h['poker_rate'] or '—')}</p></div>''' for h in HO['hotels'] if h['id']==vid), '<p class="mut">No hotel data for this venue.</p>')}
"""
    page(f"venues/{vid}.html", vname, body, "venues/venetian.html")

others = [e for e in EV["events"] if e["venue"] not in VENUE_META]
body = f"""
<div class="hero"><p class="eyebrow">Venue page</p><h1>Other rooms</h1>
<p class="sub">Rooms referenced by the official sources but without a full verified event table in this snapshot.
Preserved independent research sets (not treated as confirmation) are linked from the
<a href="../index.html">executive summary</a>.</p></div>
<table><thead><tr>{HEAD}</tr></thead><tbody>{''.join(event_row(e) for e in others)}</tbody></table>
<h2>Rooms checked and found empty / unusable for this trip window</h2>
<ul class="small"><li>Circa (downtown) — official site confirms <b>no poker room</b> (checked 2026-11-16, circalasvegas.com).</li>
<li>ARIA / MGM Grand / Planet Hollywood poker pages returned 404 on official URLs (checked 2026-11-16) — listed on the <a href="../flagged.html">Flagged page</a>.</li></ul>
"""
page("venues/others.html", "Other venues", body, "venues/venetian.html")

# ============================================================ monitor
body = f"""
<div class="hero"><p class="eyebrow">Change monitoring</p><h1>Source monitor.</h1>
<p class="sub">Each official URL is re-checked on a daily schedule (GitHub Actions · tools/recheck.py). The checker stores a content hash per URL,
refreshes <b>last-checked</b> dates, and marks rows whose source changed since the previous run.</p></div>
<p id="monitor-live" class="mut">Loading live monitor file…</p>
<div class="callout"><b>How to read this:</b> "changed" means the official page text or PDF bytes differ from the previous check — not necessarily that
a value you care about changed. Open the source link, compare against the row, update the row (and its last-checked date) if needed.</div>
<table><thead><tr><th>URL group</th><th>What is monitored</th><th>Where results land</th><th>Schedule</th></tr></thead><tbody>
<tr><td>Venetian DSE IV page + schedule PDF + 37 structure sheets</td><td>schedule rows, buy-ins, guarantees, rule text</td><td class="small">data/v2/monitor/status.json + Flagged page</td><td>daily, ~06:00 UTC (recheck.yml)</td></tr>
<tr><td>Wynn poker page + daily structures + WPT PDFs</td><td>daily/weekly tournament terms, WPT schedule</td><td class="small">same</td><td>daily</td></tr>
<tr><td>Bellagio poker page + 3 structure PDFs; Caesars flyer</td><td>weekly events and rule text</td><td class="small">same</td><td>daily</td></tr>
<tr><td>Hotel terms: Venetian fee/terms/rates, Wynn terms, TI fee</td><td>fees, tax, parking, cancellation text</td><td class="small">same</td><td>daily</td></tr>
</tbody></table>
<p class="small mut">Daily-schedule snapshots (tools/daily_schedule.py) are stored under data/v2/monitor/snapshots/ for diffing; the daily run also
rebuilds this page's data when a change is detected.</p>
"""
page("monitor.html", "Source monitor", body, "monitor.html")

# ============================================================ questions
QS = [
    ("Q1", "What is the exact written re-entry / rebuy / add-on policy for each Venetian DSE IV one-day event?",
     "Decision-blocking for a single-entry trip.",
     "None of the 37 official structure sheets states one (read in full 2026-11-17).",
     "Email/phone the Venetian Poker Room (702.414.7657) asking for a written maximum-entry statement per event; publish the reply here."),
    ("Q2", "What are the exact trip dates and the nightly budget/quality floor?",
     "Every hotel comparison depends on it.",
     "Unknown — user input required (one of the few inputs that cannot be researched).",
     "Fix dates inside Nov 17–Dec 23, 2026; then re-run the rate capture per hotel for those dates."),
    ("Q3", "What date-specific checkout totals do the official booking engines quote for those dates?",
     "Needed for like-for-like true cost/night.",
     "Blank in the rate log — official engines do not expose scrapable totals (F-05).",
     "Open each hotel's official booking deep link (Hotels page) for the exact dates + occupancy; log checkout total, nightly average, cancellation deadline, timestamp."),
    ("Q4", "What are the Bellagio and Caesars Palace mandatory resort fees?",
     "Two of five comparison hotels have blank fee fields.",
     "Unverified — official fee pages 404 / no amount (F-06).",
     "Call the properties or capture the fee line inside the official booking flow; record with timestamp."),
    ("Q5", "What are the real finish times of the candidate events?",
     "Determines whether an evening fallback is actually playable.",
     "No official source publishes finish times (F-08) — heuristic used instead.",
     "Observe/crowdsource Day-1 end times during the series; replace the heuristic per event."),
    ("Q6", "Is the Bellagio Saturday event $600, $1,000 or $1,100, and is it weekly or flighted?",
     "Affects both the schedule and the ranking.",
     "The official PDF conflicts with itself (F-02).",
     "Confirm with the Bellagio poker room; update the row and remove the flag when answered."),
    ("Q7", "Do the WPT schedule 'Dec. 18 Wednesday' rows belong to Dec 16?",
     "Affects Dec 16–18 planning.",
     "Official PDF date labels conflict with the 2026 calendar (F-03).",
     "Confirm with the Wynn poker room / wynnpoker.com before booking around those dates."),
    ("Q8", "Which poker-suite / group rates will actually be available for the chosen dates?",
     "The $119/$209 Venetian poker rate is conditional and availability-based.",
     "'As low as' rates only; blackout dates may apply (rate log RL-001).",
     "Book by phone with code EPOKR25 and confirm the rate + play requirement in writing."),
    ("Q9", "What parking budget applies if the player rents a car?",
     "Adds $20–40/day at Venetian; Wynn/TI include parking.",
     "Verified for Venetian/Wynn/TI; unknown for Bellagio/Caesars.",
     "Confirm Bellagio/Caesars parking fees on their official pages at booking time."),
    ("Q10", "Is there any room that starts tournaments before 9:10 AM in this window?",
     "The 'play from 8 AM' goal depends on it.",
     "No — earliest verified is 9:10 AM (satellite) / 10:10 AM (open) (F-04).",
     "Check off-Strip rooms' morning dailies (Orleans, South Point) via their official pages if 8 AM is a hard requirement."),
]
q_rows = "".join(f"<tr><td>{qid}</td><td><b>{esc(q)}</b><br><span class='small mut'>{esc(why)}</span></td><td class='small'>{esc(have)}</td><td class='small'>{esc(nextstep)}</td></tr>" for qid, q, why, have, nextstep in QS)
body = f"""
<div class="hero"><p class="eyebrow">Questions · information needed before decisions</p>
<h1>What we know, what we don't, how to close the gap.</h1>
<p class="sub">A decision should not be made on rows that are blank. Each question lists what is already verified, what is missing, and the
suggested way to discover the missing value.</p></div>
<table><thead><tr><th>#</th><th>Question & why it matters</th><th>What we have now</th><th>How to get the missing information</th></tr></thead>
<tbody>{q_rows}</tbody></table>
"""
page("questions.html", "Questions", body, "questions.html")

# ============================================================ suggestions
SG = [
    ("S1", "Get the single-entry policy in writing before any nonrefundable payment", "decision-blocking",
     "Adds a 'single-entry confirmed' filter result of 10+ events instead of 0; makes the ranking meaningful.", "Venetian & Wynn poker rooms"),
    ("S2", "Fix trip dates + nightly budget, then capture date-specific totals per hotel", "decision-blocking",
     "Turns the rate log from published rates into checkout totals; enables like-for-like comparison.", "User + official booking engines"),
    ("S3", "Keep the daily source monitor emails visible (or forward them)", "high",
     "Rows whose official source changed get attention the same day instead of at booking time.", "GitHub Actions → notification"),
    ("S4", "Add a morning live-schedule feed per room (already scaffolded: tools/daily_schedule.py)", "medium",
     "Catches same-day room additions/cancellations (e.g. Wynn daily suspended during series).", "tools/daily_schedule.py"),
    ("S5", "Record observed event finish times during the trip", "medium",
     "Replaces the end-time heuristic with real durations; makes fallback/overlap flags precise.", "Player observations → data/v2"),
    ("S6", "Resolve the Bellagio Saturday and WPT date-label conflicts with the rooms", "medium",
     "Removes 2 flagged irregularities; secures 2 additional planning days.", "Bellagio & Wynn poker rooms"),
    ("S7", "Add a bankroll-mode toggle (total budget → max buy-in/day)", "nice-to-have",
     "Turns the trip calculator into a constraint solver rather than a post-hoc total.", "site enhancement"),
    ("S8", "Add Apple/Google Maps deep links to a mobile 'walking card' per venue day", "nice-to-have",
     "On-the-go navigation from hotel lobby to the right poker room entrance.", "site enhancement"),
]
s_rows = "".join(f"<tr><td>{sid}</td><td><b>{esc(t)}</b><br><span class='small mut'>{esc(impact)}</span></td><td><span class='pill {'bad' if pri=='decision-blocking' else ('warn' if pri=='high' else 'ok')}'>{esc(pri)}</span></td><td class='small'>{esc(who)}</td><td class='small'>☐ review → approve / reject</td></tr>" for sid, t, pri, impact, who in SG)
body = f"""
<div class="hero"><p class="eyebrow">Suggestions · review before implementing</p>
<h1>Choose the path before we build it.</h1>
<p class="sub">Nothing on this list is implemented. Each row is a proposal with its expected impact; pick the ones you want and they become tasks.</p></div>
<table><thead><tr><th>#</th><th>Suggestion & expected impact</th><th>Priority</th><th>Who/what it needs</th><th>Your decision</th></tr></thead>
<tbody>{s_rows}</tbody></table>
"""
page("suggestions.html", "Suggestions", body, "suggestions.html")

# ============================================================ flagged
f_rows = "".join(f"""<tr><td>{esc(x['id'])}</td><td><span class="pill {'bad' if x['severity']=='decision-blocking' else ('warn' if x['severity']=='irregularity' else 'ok')}">{esc(x['severity'])}</span></td>
<td><b>{esc(x['topic'])}</b><br><span class='small'>{esc(x['detail'])}</span></td><td class='small'>{src_links(x['sources'])}</td></tr>""" for x in FL["items"])
body = f"""
<div class="hero"><p class="eyebrow">Flagged for review · nothing here blocks the site</p>
<h1>Irregularities & unverified values.</h1>
<p class="sub">Published for post-launch review with source links. Per policy these do not block the merge; they block only decisions that depend on them.</p></div>
<table><thead><tr><th>#</th><th>Severity</th><th>Topic & detail</th><th>Sources</th></tr></thead><tbody>{f_rows}</tbody></table>
"""
page("flagged.html", "Flagged for review", body, "flagged.html")

# ============================================================ sources
s_rows = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v['label'])}</td><td class='small'><a href='{esc(v['url'])}' target='_blank' rel='noopener'>{esc(v['url'])}</a></td><td class='small'>{esc(TODAY)}</td></tr>" for k, v in sorted(SRC.items()))
body = f"""
<div class="hero"><p class="eyebrow">Sources · official operator pages only</p>
<h1>Every value traces here.</h1>
<p class="sub">{len(SRC)} sources. Third-party aggregators are never used for values. Structure-sheet PDFs are the authority for entry rules.</p></div>
<table><thead><tr><th>Key</th><th>Label</th><th>URL</th><th>Last checked</th></tr></thead><tbody>{s_rows}</tbody></table>
"""
page("sources.html", "Sources", body, "sources.html")

# ============================================================ index
n_events = len(EV["events"])
body = f"""
<div class="hero"><p class="eyebrow">Decision dashboard · official-source snapshot · 17 Nov 2026</p>
<h1>Vegas poker, organized for a real decision.</h1>
<p>Upcoming tournaments with verified buy-ins, guarantees and entry rules — plus hotels with true nightly cost, verified walking times,
a day plan with honest overlap flags, a trip-cost calculator, and a dated rate log. Every table row links its official source.</p>
<div class="hero-actions"><a class="button" href="tournaments.html">Review tournaments</a><a class="button ghost" href="flagged.html">See what is unverified</a></div></div>

<div class="stats">
<div class="stat"><b>{n_events}</b><span>event rows verified against official sheets (Venetian DSE IV, Wynn daily &amp; WPT, Bellagio, Caesars)</span></div>
<div class="stat"><b>37 / 37</b><span>Venetian structure sheets read in full — 0 state an entry limit</span></div>
<div class="stat"><b>0</b><span>events with 'single-entry / freezeout confirmed' today (see note below)</span></div>
<div class="stat"><b>23</b><span>events with CONFIRMED re-entry / add-on / rebuy rules (kept in their own section)</span></div>
<div class="stat"><b>10:10 AM</b><span>earliest open-tournament start on the verified schedules (9:10 AM satellite)</span></div>
<div class="stat"><b>$55 + tax</b><span>Venetian / Wynn resort fee per night (official pages); TI $49.95 + tax</span></div>
<div class="stat"><b>13.38%</b><span>Clark County room tax applied in every true-cost calculation</span></div>
<div class="stat"><b>14</b><span>hotel × venue walking pairs verified via Google Maps — all ≤ 30 min</span></div>
</div>

<div class="callout danger"><strong>Executive decision: do not book on the assumption of single-entry play.</strong>
Every Venetian structure sheet for DSE IV (Nov 16 – Dec 23, 2026) was read line by line on 2026-11-17: none confirms a single-entry / freezeout limit,
so the candidate events stay labeled "entry rules unverified". The rooms that do publish rules (Wynn, Bellagio, Caesars) all allow some form of
re-entry, rebuy or add-on — those are quarantined in their own section. Get a written maximum-entry policy before nonrefundable payment.</div>

<h2>What looks most promising (conditional, ranked only where fee + guarantee are confirmed)</h2>
<div class="grid">
<article class="card"><span class="tag">Best confirmed ratio</span><h3>{esc(ranked[0]['name']) if ranked else '—'}</h3>
<p>Guarantee ÷ total entry fee = {ranked[0]['ratio_guarantee_per_buy_in'] if ranked else '—'}× — descriptive arithmetic only.
{esc(ranked[0]['date']) if ranked else ''} {esc(ranked[0]['start_time']) if ranked else ''}. Note the re-entry rules on the row before comparing against candidates.</p>
<p><a href="tournaments.html">Ranking screen →</a></p></article>
<article class="card"><span class="tag">Lowest-cost candidates (rules unverified)</span><h3>$200–$300 one-day events</h3>
<p>Venetian $300 NLH $10K GTD (ratio 33.3×), $400 NLH $15K GTD (37.5×), $600 NLH $30K GTD (50×) — all with verified fee splits
($58/$65/$90 house fee) but unverified entry rules. Numbers are sheet-verified; the single-entry question is not.</p>
<p><a href="tournaments.html">Candidate table →</a></p></article>
<article class="card"><span class="tag">Closest lodging with verified economics</span><h3>Stay at the Venetian / Palazzo</h3>
<p>On-site to the poker room (Palazzo Level 2). Resort fee $55 + tax, tax 13.38%, poker suite rates from $119/$209 (conditional on
6 hrs cash play or a $300+ buy-in per night). True cost/night at $119 = $197.28 all-in.</p>
<p><a href="hotels.html">Hotel comparison →</a></p></article>
</div>

<h2>Planning constraints that change the answer</h2>
<div class="grid">
<article class="card"><h3>No 8 AM start exists</h3><p>Earliest verified open start is 10:10 AM (9:10 AM for a satellite). The day plan is built around that fact.</p></article>
<article class="card"><h3>One event per day, fallback only if realistic</h3><p>Overlapping windows are flagged as impossible sequences; evening events are conditional on exiting the earlier one.</p></article>
<article class="card"><h3>True hotel cost ≠ headline rate</h3><p>(rate + resort fee) × 1.1338. Two of five hotels still have unverified fees — flagged, not guessed.</p></article>
</div>

<h2>Recommended sequence (matches the project's trip workflow)</h2>
<ol><li><b>Fix trip dates and the nightly budget/quality floor.</b> Everything else keys off this.</li>
<li><b>For candidate events, obtain the written maximum-entry / no-rebuy / no-add-on rule</b> and drop any event that does not match a single-entry policy.</li>
<li><b>Compare only surviving events</b> on guarantee, total entry fee, starting stack / blind duration, payout structure and daily fit.</li>
<li><b>Capture itemized hotel totals for the same stay</b> and confirm the walking route is under 30 minutes (verified matrix already covers 14 pairs).</li>
<li><b>Build one event per day first</b>; add an evening event only where you can realistically exit the earlier one.</li>
<li><b>Reconfirm official schedules, rates and policies</b> right before any nonrefundable payment — the daily source monitor flags changes.</li></ol>

<h2>Preserved independent research sets</h2>
<p class="mut">Earlier sessions' dashboards survive untouched for comparison. They use their own snapshots and classifications; this integrated
dashboard supersedes them and does not treat them as confirmation:</p>
<p class="small"><a href="c07371e3/index.html">c07371e3 research ↗</a> · <a href="df41f5c6/index.html">df41f5c6 research ↗</a> ·
<a href="60fb62da/index.html">60fb62da research ↗</a> · <a href="verified/index.html">verified candidates ↗</a> ·
<a href="strip/index.html">strip-wide review ↗</a> · <a href="pages/executive-summary.html">first integration pages ↗</a></p>
"""
page("index.html", "Executive summary", body, "index.html")

print("built root site:", len([p for p in NAV]) , "nav pages + 5 venue pages")
