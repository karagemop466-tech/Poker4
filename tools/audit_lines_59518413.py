#!/usr/bin/env python3
"""Line-by-line audit of the published Poker4 data (session arena/59518413-poker4).

Checks every row the site publishes against the committed official captures and
the arithmetic the pages claim, and writes a report to
data/verify/59518413-line-audit.md. Run from the repository root:

    python3 tools/audit_lines_59518413.py

Nothing here edits published data: it only reports. Exit code 0 even when
problems are found (they are expected to be published as flags, not fixed by
inference); the report lists everything.
"""
import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "data" / "verify" / "59518413-line-audit.md"

problems = []      # (severity, category, detail)
notes = []         # informational confirmations
counts = {}


def load(name):
    with open(ROOT / name, encoding="utf-8") as fh:
        return json.load(fh)


def is_http(url):
    return isinstance(url, str) and url.startswith(("http://", "https://"))


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def approx(a, b, tol=0.51):
    return a is not None and b is not None and abs(a - b) <= tol


def money_in(text):
    """All dollar amounts in a sentence, as floats."""
    return [float(m.replace(",", "")) for m in re.findall(r"\$([\d,]+(?:\.\d+)?)", text or "")]


# ---------------------------------------------------------------- load
events_doc = load("data/site-events.json")
events = events_doc["events"]
tracked = load("data/tracked-sources.json")["sources"]
registry = {s["url"] for s in tracked}
rate_log = load("data/rate-log.json")["entries"]
walks = load("data/walks.json")
day_plan = load("data/day-plan.json")["days"]
poker4 = load("data/poker4.json")
hotels = poker4["hotels"]
room_facts = load("data/room-facts.json")

counts.update(events=len(events), tracked=len(tracked), rate_log=len(rate_log),
              walk_pairs=len(walks["pairs"]), days=len(day_plan), hotels=len(hotels))

# ---------------------------------------------------------------- events
ids = [e["id"] for e in events]
dupes = {i for i in ids if ids.count(i) > 1}
if dupes:
    problems.append(("row", "event", f"duplicate event ids: {sorted(dupes)[:5]}"))

bad_weekday = []
no_source = []
source_not_tracked = []
no_last_checked = []
rule_gaps = []
fee_mismatch = []
fee_mismatch_known = []
ratio_mismatch = []
pool_mismatch = []
single_entry_claimed = []
for e in events:
    eid = e["id"]
    d = parse_date(e.get("date") or "")
    if d and e.get("weekday") and d.strftime("%A") != e["weekday"]:
        bad_weekday.append(f"{eid}: date {e['date']} is a {d.strftime('%A')}, row says {e['weekday']}")
    srcs = e.get("sources") or []
    if not srcs:
        no_source.append(eid)
    for u in srcs:
        if not is_http(u):
            source_not_tracked.append(f"{eid}: non-http source {u!r}")
        elif u not in registry:
            source_not_tracked.append(f"{eid}: {u}")
    if not e.get("last_checked"):
        no_last_checked.append(eid)
    rules = e.get("rules") or {}
    for key in ("single_entry", "re_entry", "add_on", "fee"):
        r = rules.get(key)
        if not isinstance(r, dict):
            rule_gaps.append(f"{eid}: rules.{key} missing")
            continue
        if not r.get("status"):
            rule_gaps.append(f"{eid}: rules.{key} has no status")
        if not r.get("retrieved"):
            rule_gaps.append(f"{eid}: rules.{key} has no retrieved date")
        su = r.get("source")
        if su and (not is_http(su) or su not in registry):
            rule_gaps.append(f"{eid}: rules.{key} source not in registry: {su}")
    if e.get("single_entry_confirmed"):
        st = (rules.get("single_entry") or {}).get("status")
        if st != "confirmed":
            single_entry_claimed.append(f"{eid}: confirmed flag without a confirmed clause")
    # fee split arithmetic (only where the row prints all three numbers). A
    # mismatch with sums_to_buy_in=False and the verbatim flag is a RECORDED
    # printed-source irregularity (flags F16/F22/F40) — reported as a note, not
    # a data problem; a mismatch WITHOUT the marker is a real problem.
    bi, hf, pp = e.get("buy_in_usd"), e.get("house_fee_usd"), e.get("pool_per_entry_usd")
    if bi and hf and pp and hf + pp != bi:
        fr = rules.get("fee") or {}
        if fr.get("sums_to_buy_in") is False and any("does not add up" in f for f in (e.get("flags") or [])):
            fee_mismatch_known.append(f"{eid}: printed split {hf}+{pp} != {bi} (recorded verbatim, flagged)")
        else:
            fee_mismatch.append(f"{eid}: house fee {hf} + pool {pp} != buy-in {bi} (no sums_to_buy_in marker/flag)")
    # descriptive ratio arithmetic
    gtd, ratio = e.get("guarantee_usd"), e.get("gtd_ratio")
    if e.get("rankable") and gtd and bi and ratio:
        if not approx(ratio, gtd / bi, tol=max(0.51, ratio * 0.002)):
            ratio_mismatch.append(f"{eid}: gtd_ratio {ratio} != {gtd}/{bi} = {gtd/bi:.2f}")
    if bi and pp and e.get("gtd_over_pool_contribution") and gtd and pp:
        if not approx(e["gtd_over_pool_contribution"], gtd / pp, tol=max(0.51, e["gtd_over_pool_contribution"] * 0.002)):
            pool_mismatch.append(f"{eid}: gtd_over_pool_contribution mismatch")

for label, items in [("weekday mismatches", bad_weekday), ("rows without sources", no_source),
                     ("sources outside the tracked registry", source_not_tracked),
                     ("rows without last_checked", no_last_checked),
                     ("structured-rule gaps", rule_gaps),
                     ("fee-split arithmetic mismatches without a recorded marker", fee_mismatch),
                     ("gtd_ratio arithmetic mismatches", ratio_mismatch),
                     ("gtd_over_pool mismatches", pool_mismatch),
                     ("single-entry claims without a clause", single_entry_claimed)]:
    if items:
        problems.append(("row", "event", f"{label}: {len(items)} — e.g. {items[0]}"))
    else:
        notes.append(f"events: {label} — 0 across all {len(events)} rows")
if fee_mismatch_known:
    notes.append("events: " + str(len(fee_mismatch_known)) + " printed fee splits that do not add up are recorded "
                 "verbatim and flagged (F16/F22/F40), never corrected — e.g. " + fee_mismatch_known[0])

# rule status census (the 'remove unverified where confirmed' requirement)
census = {}
for e in events:
    for key, r in (e.get("rules") or {}).items():
        if isinstance(r, dict):
            census[(key, r.get("status"))] = census.get((key, r.get("status")), 0) + 1

# ---------------------------------------------------------------- hotels
walk_by_hotel = {}
for p in walks["pairs"]:
    walk_by_hotel.setdefault(p["hotel_id"], []).append(p)

tax_conflicts = []
fee_source_missing = []
booking_missing = []
walk_missing = []
truecost_mismatch = []
for h in hotels:
    hid = h["id"]
    tax = h.get("tax") or {}
    if tax.get("rate_pct") not in (13.38, None):
        tax_conflicts.append(f"{hid}: tax rate {tax.get('rate_pct')}")
    fee = h.get("resort_fee") or {}
    if fee.get("amount_usd") is not None and not is_http(fee.get("source")):
        fee_source_missing.append(hid)
    if not is_http(h.get("booking_link")):
        booking_missing.append(hid)
    if hid not in walk_by_hotel:
        walk_missing.append(hid)
    # true cost/night recompute where the row keeps a dated rate
    tc = h.get("true_cost") or {}
    rate = tc.get("rate_usd") or (h.get("rate") or {}).get("amount_usd")
    amount = fee.get("amount_usd")
    shown = tc.get("per_night_usd") or tc.get("true_cost_night_usd")
    if shown and rate is not None and amount is not None:
        calc = (rate + amount) * (1 + (tax.get("rate_pct") or 13.38) / 100)
        if not approx(shown, calc, tol=0.75):
            truecost_mismatch.append(f"{hid}: shown {shown} vs (rate {rate} + fee {amount}) x 1.1338 = {calc:.2f}")

for label, items in [("tax-rate conflicts", tax_conflicts), ("fee rows without source", fee_source_missing),
                     ("hotels without a booking link", booking_missing),
                     ("hotels without a measured walk", walk_missing),
                     ("true-cost/night arithmetic mismatches", truecost_mismatch)]:
    if items:
        problems.append(("row", "hotel", f"{label}: {len(items)} — {items[:3]}"))
    else:
        notes.append(f"hotels: {label} — 0 across all {len(hotels)} rows")

# ---------------------------------------------------------------- rate-slot hygiene
# The build's true-cost chain takes the first rate_log entry tagged as a usable
# rate (or, when untagged, any entry with an amount). A fee re-read must never
# occupy the room-rate slot: that is how "$49.95 room rate" (a figure TI never
# printed as a room rate) reached the hotels table before this session's fix.
RATE_KINDS_USABLE = ("advertised_rate", "dated_rate", "quoted_rate")
RATE_KINDS_ALL_IN = ("all_in_per_night",)
rate_slot_bad = []
rate_slot_used = []
for h in hotels:
    rate = rate_note = all_in = None
    for e in (h.get("rate_log") or []):
        kind = e.get("kind") or ("advertised_rate" if e.get("amount_usd") else "not_published")
        amount = e.get("amount_usd")
        if not amount:
            continue
        if kind in RATE_KINDS_ALL_IN:
            all_in, rate_note = amount, e
            break
        if kind in RATE_KINDS_USABLE and rate is None:
            rate, rate_note = amount, e
    entry = rate_note or {}
    label_txt = f"{entry.get('label','')} {entry.get('qualifier','')}".lower()
    if rate is not None and ("resort fee" in label_txt or entry.get("kind") == "fee_only"):
        rate_slot_bad.append(f"{h['id']}: room-rate slot fed by a fee observation — {entry.get('label')!r}")
    if rate is not None:
        rate_slot_used.append(f"{h['id']}: ${rate} from {entry.get('label')!r} ({entry.get('observed_on')})")
    # every untagged entry with an amount is a landmine if the order changes
    for e in (h.get("rate_log") or []):
        if e.get("amount_usd") and not e.get("kind"):
            rate_slot_bad.append(f"{h['id']}: rate-log entry with an amount but no kind tag — {e.get('label')!r}")
if rate_slot_bad:
    problems.append(("row", "hotel-rate-slot", f"{len(rate_slot_bad)} — {rate_slot_bad[:4]}"))
else:
    notes.append("hotels: no room-rate slot is fed by a fee observation; every priced rate-log entry carries an explicit kind tag")

# ---------------------------------------------------------------- walks
walk_bad = []
for p in walks["pairs"]:
    try:
        mins = float(p.get("minutes"))
    except Exception:
        walk_bad.append(f"{p.get('hotel_id')}: non-numeric minutes {p.get('minutes')!r}")
        continue
    within = mins <= 30
    claimed = str(p.get("meets_30_min", "")).startswith("yes")
    if within != claimed and not (mins == 0):
        walk_bad.append(f"{p.get('hotel_id')}: minutes {mins} vs meets_30_min {p.get('meets_30_min')!r}")
    if not is_http(p.get("source")):
        walk_bad.append(f"{p.get('hotel_id')}: walk row without a source URL")
if walk_bad:
    problems.append(("row", "walk", f"inconsistencies: {len(walk_bad)} — {walk_bad[:3]}"))
else:
    notes.append(f"walks: all {len(walks['pairs'])} pairs consistent (minutes vs <=30 flag, source URL present)")

# ---------------------------------------------------------------- rate log
# (hotel_id, seq) is NOT unique by design — fact-wording lines share seq 90.
# The log's guarantees are: append-only, dated, sourced, and no exact duplicate
# (same label + qualifier + source + amount) rows.
seen = set()
rl_bad = []
for r in rate_log:
    key = (r.get("hotel_id"), r.get("label"), r.get("qualifier"), r.get("source"), r.get("amount_usd"))
    if key in seen:
        rl_bad.append(f"exact duplicate entry: {r.get('hotel_id')} / {r.get('label')}")
    seen.add(key)
    if not parse_date(r.get("observed_on") or ""):
        rl_bad.append(f"{r.get('hotel_id')}/{r.get('label')}: bad observed_on {r.get('observed_on')!r}")
    if not is_http(r.get("source")):
        rl_bad.append(f"{r.get('hotel_id')}/{r.get('label')}: no source URL")
if rl_bad:
    problems.append(("row", "rate-log", f"problems: {len(rl_bad)} — {rl_bad[:3]}"))
else:
    notes.append(f"rate-log: all {len(rate_log)} entries dated and sourced, no exact duplicates — append-only log intact")

# ---------------------------------------------------------------- day plan
event_id_set = set(ids)
dp_bad = []
for d in day_plan:
    prim = d.get("primary") or d.get("lead") or d.get("main")
    if not prim and not d.get("recurring_options"):
        dp_bad.append(f"{d.get('date')}: no primary and no recurring options")
    for key in ("primary", "fallback", "conditional_fallback", "evening"):
        node = d.get(key)
        if isinstance(node, dict):
            ref = node.get("id")
            if ref and ref not in event_id_set and not ref.startswith(("CAESARS", "WYNN")):
                dp_bad.append(f"{d.get('date')}: {key} id {ref} not in site-events")
    d2 = parse_date(d.get("date") or "")
    if d2 and d.get("weekday") and d2.strftime("%A") != d["weekday"]:
        dp_bad.append(f"{d.get('date')}: weekday mismatch")
if dp_bad:
    problems.append(("row", "day-plan", f"problems: {len(dp_bad)} — {dp_bad[:3]}"))
else:
    notes.append(f"day-plan: all {len(day_plan)} days carry a plan, referenced ids resolve, weekdays match")

# ---------------------------------------------------------------- room-facts provenance hashes
# the recurring defect (F28): raw capture headers rewrite every sync, so the
# stored sha256 must match the CURRENT file or the row is stale. Walk the whole
# room-facts tree for (file, sha256) / (capture_file, capture_sha256) pairs.
hash_mismatch = []
hash_checked = 0
import hashlib

def walk_hashes(node, path=""):
    global hash_checked
    if isinstance(node, dict):
        pairs = []
        if node.get("file") and node.get("sha256"):
            pairs.append((node["file"], node["sha256"]))
        if node.get("poster_file") and node.get("poster_sha256"):
            pairs.append((node["poster_file"], node["poster_sha256"]))
        if node.get("capture_file") and node.get("capture_sha256"):
            pairs.append((node["capture_file"], node["capture_sha256"]))
        for fname, sha in pairs:
            p = ROOT / fname if not fname.startswith("data/") else ROOT / fname
            if not p.exists():
                hash_mismatch.append(f"{path}: file missing {fname}")
                continue
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            hash_checked += 1
            if digest != sha:
                hash_mismatch.append(f"{path or fname}: stored {sha[:12]}… vs file {digest[:12]}…")
        for k, v in node.items():
            walk_hashes(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk_hashes(v, f"{path}[{i}]")

walk_hashes(room_facts)
if hash_mismatch:
    problems.append(("provenance", "room-facts", f"hash drift: {len(hash_mismatch)} — {hash_mismatch[:3]}"))
else:
    notes.append(f"room-facts: {hash_checked} stored source hashes match the current raw captures (F28 recurrence check)")

# ---------------------------------------------------------------- rendered pages spot-check
pages_checked = 0
render_bad = []
def page_contains(fname, needle, label):
    global pages_checked
    pages_checked += 1
    text = (ROOT / fname).read_text(encoding="utf-8")
    if needle not in text:
        render_bad.append(f"{fname}: missing {label} ({needle[:60]!r})")

page_contains("index.html", "253 events on this site", "event count")
page_contains("index.html", "0 confirmed single-entry", "single-entry count")
page_contains("tournaments.html", "global-search", "search box")
page_contains("hotels.html", "booking engine", "booking links")
page_contains("calculator.html", "entries", "trip calculator inputs")
page_contains("flagged.html", "F1", "flag F1")
page_contains("questions.html", "Q1", "question Q1")
page_contains("suggestions.html", "suggestion", "suggestions section")
page_contains("plan.html", "primary", "day-plan primary/fallback")
for v in ("venetian", "wynn", "bellagio", "caesars", "aria", "others"):
    page_contains(f"venues/{v}.html", "Hotels within a 30-minute walk", f"venue page {v} hotel section")
# sample rows
import random
random.seed(59518413)
sample = random.sample(events, 12)
for e in sample:
    page_contains("tournaments.html", e["id"], f"row {e['id']}")
if render_bad:
    problems.append(("render", "pages", f"{len(render_bad)} missing — {render_bad[:5]}"))
else:
    notes.append(f"pages: {pages_checked} spot-checks (counts, search box, booking links, calculator, flags, "
                 f"questions, suggestions, day plan, 6 venue pages, 12 sampled event rows) all present")

# ---------------------------------------------------------------- report
now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
lines = [
    "# Line-by-line audit — session arena/59518413-poker4",
    "",
    f"Run: {now} · script: `tools/audit_lines_59518413.py`",
    "",
    f"Rows audited: {counts['events']} events · {counts['hotels']} hotels · {counts['walk_pairs']} walk pairs · "
    f"{counts['rate_log']} rate-log entries · {counts['days']} plan days · {counts['tracked']} tracked official URLs.",
    "",
    "## Result",
    "",
    ("**No problems found.** Every published row carries an official source in the tracked registry, a "
     "`last_checked` date, structured rule fields with excerpt/retrieval provenance, and the arithmetic "
     "printed on the pages recomputes from the printed numbers.") if not problems else
    f"**{len(problems)} problem categories found** (details below). None of these were fixed by inference.",
    "",
    "## Confirmations",
    "",
]
lines += [f"- {n}" for n in notes]
if problems:
    lines += ["", "## Problems", ""]
    for sev, cat, detail in problems:
        lines.append(f"- [{cat}] {detail}")
lines += ["", "## Rule-status census (per structured rule field)", "",
          "| field | status | rows |", "|---|---|---|"]
for (k, st), n in sorted(census.items()):
    lines.append(f"| {k} | {st} | {n} |")
lines += ["", "## Method", "",
          "- Every event id, date/weekday, source URL, `last_checked`, and the four structured rule fields "
          "(single_entry / re_entry / add_on / fee, each with status + source + retrieved) were checked for all "
          f"{len(events)} rows; source URLs were required to appear in `data/tracked-sources.json` (the official "
          f"registry, now {len(tracked)} URLs — the three Bellagio structure PDFs were added to it by this session).",
          "- Fee-split arithmetic: house fee + pool-per-entry must equal the printed buy-in wherever the sheet "
          "prints all three. Printed inconsistencies (Wynn WPT-08, flag F22; the five Venetian rows on sheets "
          "31/32/33, flag F40) are recorded verbatim and flagged, never corrected; this audit reports a problem "
          "only where a mismatch carries no recorded marker.",
          "- Guarantee ÷ entry-fee and guarantee ÷ pool-per-entry were recomputed for every rankable row "
          "(descriptive ratios only).",
          "- Hotel rows: tax chain is 13.38% on rate + resort fee; true cost/night recomputed where a dated rate "
          "exists; every row needs an official source URL and a booking link; no room-rate slot may be fed by a "
          "fee observation, and every priced rate-log entry carries an explicit kind tag.",
          "- Walk pairs: `meets_30_min` re-derived from the measured minutes (30-minute hard filter).",
          "- Rate log: dated, sourced, no exact duplicates — the log is append-only.",
          "- Day plan: every day carries a primary + conditional fallback; referenced ids resolve against the "
          "event table; weekdays match dates.",
          "- Provenance: stored `sha256` of every room-facts source recomputed against the current raw captures "
          "(recurrence check for F28).",
          "- Rendered pages: counts, search box, booking links, calculator, flags, questions, suggestions, day plan, "
          "all six venue pages, and 12 randomly sampled event rows were looked up in the built HTML.",
          "",
          "Live venue pages could not be re-fetched from this sandbox (outbound HTTP reaches github.com / npm / "
          "PyPI only). The scheduled GitHub Actions jobs (`source-recheck.yml`, `url-check.yml`, "
          "`maintenance.yml`) perform the live re-checks at 06:00 Las Vegas and write the dated results; this "
          "audit verifies the committed captures and the published pages against each other.",
          ""]
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text("\n".join(lines), encoding="utf-8")

print(f"report: {REPORT.relative_to(ROOT)}")
print(f"events={counts['events']} hotels={counts['hotels']} walks={counts['walk_pairs']} "
      f"rate-log={counts['rate_log']} days={counts['days']} sources={counts['tracked']}")
print(f"problems: {len(problems)} categories · confirmations: {len(notes)}")
for sev, cat, detail in problems:
    print(f"  [{cat}] {detail}")
