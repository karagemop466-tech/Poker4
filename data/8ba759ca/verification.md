# Independent verification record — session arena/8ba759ca-poker4 (2026-11-17)

Policy: every value below was re-read from the live official page/PDF in this session (page-fetch
tool), compared programmatically where possible, and only then recorded. Nothing is inferred;
blank stays blank.

## V1 — line-by-line re-verification against live official sources

### 1. Venetian DeepStack Extravaganza IV calendar — 94/94 rows, 0 problems

- Live source (all 4 chunks fetched this session):
  https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html
- My own transcription of the live table: `live_calendar_2026-11-17.tsv` (94 rows).
- Compared cell-by-cell (date, time, event #, printed buy-in, printed guarantee, structure-sheet
  number) against:
  1. session 75757cc1's same-day live transcription (`data/75757cc1/official_calendar_2026-11-17.tsv`) → 0 mismatches
     (their `0` guarantee encoding = my blank; both mean "no guarantee printed");
  2. `data/schedule-snapshot.json` (the feed that builds the tournaments table) → 0 mismatches;
  3. published `data/site-events.json` (94/94 keys matched; buy-in + guarantee agree on every
     printed value) → 0 mismatches.
- Result: **94/94 rows verified, 0 problems** (`compare_live.py`, exit 0).

### 2. Venetian hotel facts — live-confirmed, published values match

| Fact | Live official text (retrieved 2026-11-17) | Source | Published value |
|------|--------------------------------------------|--------|-----------------|
| Resort fee | "Rates include a daily Resort Fee of $55 plus tax per night" | venetianlasvegas.com/resort/resort-fee.html | $55 ✓ |
| Room tax | "Clark County Room Tax of 13.38%" | venetianlasvegas.com/legal/hotel-terms-and-conditions.html | 13.38% ✓ |
| Resort fee (terms copy) | "standard Las Vegas Resort Fee of $55 plus applicable tax per night" | same terms page | ✓ |
| Parking | guests $20/day; non-guests $20 Mon–Thu / $25 Fri–Sun; valet $40/day | same terms page | $20/$40 ✓ (guest/valet shown) |
| Early check-out | "$100 plus tax" | same terms page | $100 ✓ |
| Incidental deposit | "$150 per night" | same terms page | $150 ✓ |

### 3. Treasure Island fee — live-confirmed

- "The $49.95 + tax daily resort fee at TI Las Vegas …" + "Always Free Valet Parking & Self Park
  Garage" — https://treasureisland.com/hotel/tower-suite (retrieved 2026-11-17). Published $49.95 ✓.

### 4. Structure-sheet entry-rule verdict — spot-checked live, verdict stands

- Sheet #8 (Valuetown, Events 18 & 58), fetched live today:
  "$40 of the $200 Buy-In is withheld … prize pool consists of $160"; rule 7 "All subsequent
  buy in's after the initial buy in will be $200"; "Guarantee: $20,000 (prize pool + total
  bounties)". Matches published excerpt; confirms multi-entry pricing → separate section (F2). ✓
- Sheet #10 (Event 1, $300/$75K), fetched live today: late reg "6 levels + Break (~ 3:40 PM)",
  "$60 of the $300 Buy-In … $240", "Any player who bags chips for Day 2 may not play a subsequent
  flight", and **no single-entry / re-entry / add-on statement anywhere** — silence confirmed, so
  the unverified label stays (F1). ✓
- Verdict: **0 events confirmed single-entry** remains correct.

### 5. Wynn $55 resort fee source (flag F19) — stays open, re-checked

- `wynnlasvegas.com/hotel/resort-fee.html` → dead ("IT SEEMS THIS PAGE HAS CHECKED OUT").
- The two official pages found stating "$55 plus tax" (terms 850257 and 850249) are both
  **Concours promo-package terms** with travel windows ending 2026-11-01 — expired.
- No current general Wynn fee page exists that was reachable today → F19 correctly remains open.

### 6. WPT schedule "Dec. 18 Wednesday" typo (flag F4) — real and live today

- Live PDF (cdn.wynnresorts.com/…/WPT_World_Championship_Schedule.pdf, fetched today) page 2
  prints **eight rows under "Dec. 18 Wednesday"** ($1,100 NLH $1M GTD 1A/1B, WPT World
  Championship Day 2, PLO Double Board Bomb Pot, PLO 6-Max, HORSE, two satellites), between the
  "Dec. 15 Tuesday" and "Dec. 17 Thursday" blocks; the adjacent "Dec. 18 Friday" rows are
  different events. In 2026 Dec 18 is a Friday and Dec 16 is the Wednesday — the flag's text is
  accurate.
- Note: the scheduled raw capture `data/raw/wynn-wpt-schedule.txt` does **not** contain the typo
  block (its extraction re-orders/drops it) — irregularity noted below.
- The canonical date for those rows is NOT an inference: the official WPT **structures** PDF
  prints verbatim "December 16, 2026 at 11 a.m." (Day 1A) and "December 16, 2026 at 7 p.m."
  (Day 1B) for the $1,100 $1M GTD event (room-facts excerpt, retrieved 2026-11-17). So the site's
  2026-12-16 dating is sourced from an official document, and F4 is published for the schedule
  PDF's own typo. ✓

### 7. Hotels with no official fee — blanks are honest

- Bellagio (fee page still 404), Caesars, ARIA, Horseshoe, Harrah's: `resort_fee.amount_usd` is
  null with an explicit status string; no third-party number adopted. ✓ (F6/F8/F5)

### 8. Walking minutes — still no official source

- `walk_policy.verified_minutes_source` states every minutes cell is blank and flagged. ✓ (F3/F18)

## V2 — full gate run + feature audit (all green)

Gates executed locally on this branch (== origin/main @ ff3fa36):

| Gate | Result |
|------|--------|
| `scripts/verify_root.py` | PASS — 16 pages · 253 event rows · 74 rate-log lines · 64 tracked sources · 0 warnings |
| `scripts/verify.py` | PASS |
| `scripts/verify_markup.py` | PASS |
| `scripts/linkcheck.py` | PASS |
| `scripts/validate_site.py` | PASS |
| `tools/verify_poker4.py` | PASS |
| `tools/check_rows.py` | PASS |
| `tools/poker4_monitor.py --selftest` | PASS |
| `node --check app.js` / `site/app.js` | PASS |
| `scripts/integrate_data.py` re-run | byte-identical (no drift) |
| Arithmetic spot checks | ($119+$55)×1.1338 = $197.28 ✓ · ($209+$55)×1.1338 = $299.32 ✓ · TI example ✓ · $1,024.39/2 = $512.20 ✓ |

Feature audit vs the brief (page + marker checks): trip calculator, site search, date filter,
single-entry toggle, spend-advantage section, descriptive GTD÷entry ratio, ≤30-min walk filter,
dated rate log, primary+conditional-fallback day plan, change monitor, executive summary,
questions, suggestions, flagged, repo review, six per-venue pages, sources page — **0 failures**.

Headline counts on index.html match the data (94 Venetian rows · 253 total · 0 confirmed
single-entry).

## Irregularities found this session (for the Flagged / review owners)

1. **W-RAW** — `data/raw/wynn-wpt-schedule.txt` (scheduled capture) omits the eight
   "Dec. 18 Wednesday" rows that the live PDF prints; anyone auditing from the capture alone
   would not see F4's typo. The live PDF (fetched this session) contains it.
2. **F19 re-confirmed open** — Wynn's dedicated resort-fee page is dead; the only official $55
   wording lives in expired promo terms. Needs a current general Wynn fee page before the value
   can be un-flagged.
3. No other mismatch found: Venetian calendar 94/94, hotel facts, fee splits, and the
   single-entry verdict all re-confirmed against live official pages.

## Sources re-read live in this session (all 2026-11-17)

- https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html (4 chunks)
- https://www.venetianlasvegas.com/resort/resort-fee.html
- https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html (2 chunks)
- https://treasureisland.com/hotel/tower-suite
- https://www.wynnlasvegas.com/terms-and-conditions/850257 (expired promo)
- https://www.wynnlasvegas.com/terms-and-conditions/850249 (expired promo)
- https://www.wynnlasvegas.com/hotel/resort-fee.html (dead — "page has checked out")
- https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf (2 chunks)
- https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_8.pdf
- https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_10.pdf
