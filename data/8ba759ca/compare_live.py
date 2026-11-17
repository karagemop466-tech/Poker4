#!/usr/bin/env python3
"""Independent line-by-line comparison: live fetch (session 8ba759ca, 2026-11-17)
vs session 75757cc1's live transcription, vs data/schedule-snapshot.json, vs
data/site-events.json (published rows)."""
import csv, json, sys

def load_tsv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))

mine = load_tsv('data/8ba759ca/live_calendar_2026-11-17.tsv')
theirs = load_tsv('data/75757cc1/official_calendar_2026-11-17.tsv')

def key(r):
    return (r['date'], r['time'], r['event_no'])

def norm(g):
    g = (g or '').strip()
    if g in ('0', '0.0'):   # session 75757cc1 records '0' for "no guarantee printed"
        return ''
    return g or ''

problems = []

# --- (a) mine vs 75757cc1 transcription ---
a = {key(r): r for r in mine}
b = {key(r): r for r in theirs}
for k in sorted(set(a) | set(b)):
    if k not in a: problems.append(f'A-MISSING-MINE {k} theirs={b[k]}')
    elif k not in b: problems.append(f'A-MISSING-THEIRS {k} mine={a[k]}')
    else:
        for col in ('buy_in_usd','guarantee_usd','structure_no'):
            if norm(a[k][col]) != norm(b[k][col]):
                problems.append(f'A-DIFF {k} {col}: mine={a[k][col]!r} theirs={b[k][col]!r}')

# --- (b) mine vs schedule-snapshot.json ---
snap = json.load(open('data/schedule-snapshot.json'))
rows = snap['rows'] if isinstance(snap, dict) and 'rows' in snap else snap
if isinstance(rows, dict):
    for k,v in rows.items(): print('snap key', k, type(v))
    sys.exit(1)
def snap_key(r):
    d = r.get('date') or r.get('event_date') or ''
    if d and not d.startswith('2026'): d = '2026-' + d if len(d.split('-'))==2 else d
    return (d, (r.get('time') or r.get('start_time') or '').strip(), str(r.get('event_no') or r.get('event_number') or ''))
sb = {snap_key(r): r for r in rows}
for k in sorted(set(a) | set(sb)):
    if k not in a:
        problems.append(f'B-MISSING-MINE {k} snap={sb[k]}')
    elif k not in sb:
        problems.append(f'B-MISSING-SNAP {k} mine={a[k]}')
    else:
        r = sb[k]
        mg, sg = norm(a[k]['guarantee_usd']), str(r.get('guarantee_usd') or r.get('guarantee') or '')
        if mg and sg and mg != sg:
            problems.append(f'B-DIFF {k} guarantee mine={mg} snap={sg}')
        if not mg and sg:
            problems.append(f'B-DIFF {k} guarantee mine=(printed none) snap={sg}')

# --- (c) mine vs published site-events.json (Venetian rows) ---
ev = json.load(open('data/site-events.json'))['events']
ven = [e for e in ev if e.get('venue')=='venetian']
cb = {}
for e in ven:
    cb.setdefault((e.get('date',''), e.get('time',''), str(e.get('event_no',''))), []).append(e)
matched = 0
for k in sorted(a):
    if k not in cb:
        problems.append(f'C-NOT-PUBLISHED {k} mine={a[k]}')
        continue
    matched += 1
    rs = cb[k]
    aa = a[k]
    # buy-in and guarantee where printed
    pubs = [(e.get('buy_in_usd'), e.get('guarantee_usd')) for e in rs]
    if aa['buy_in_usd']:
        if not any(str(p[0] or '') == aa['buy_in_usd'] for p in pubs):
            problems.append(f'C-DIFF {k} buy_in mine={aa["buy_in_usd"]} published={pubs}')
    if aa['guarantee_usd']:
        if not any(str(p[1] or '') == aa['guarantee_usd'] for p in pubs):
            problems.append(f'C-DIFF {k} guarantee mine={aa["guarantee_usd"]} published={pubs}')
print(f'rows mine={len(mine)} theirs={len(theirs)} snapshot={len(rows)} venetian_published_keys={len(cb)} matched={matched}')
print(f'problems={len(problems)}')
for p in problems: print(p)
sys.exit(1 if problems else 0)
