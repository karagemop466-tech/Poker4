# 27e8ed8e — provenance repair (R1) and live spot-check (R2)

Date of check: 2026-11-18 (UTC). Session branch: `arena/27e8ed8e-poker4`.

## R1 — provenance hashes (`data/room-facts.json`)

- **Irregularity found:** the committed `data/room-facts.json` recorded SHA-256 values for
  `wynn-wpt-terms.txt`, `wynn-daily-structures.txt` and `caesars-daily-flyer-2026.txt` that did not
  match the captures committed in `data/raw/`. Re-running `tools/room_extract.py` changed the file.
- **Repair:** re-ran `tools/room_extract.py` on the committed captures. The diff is limited to the
  three hash lines (3 insertions, 3 deletions); no extracted fact, buy-in, fee, rule or date changed.
- **Result:** all 6 recorded hashes (`sha256` / `capture_sha256`) now equal the SHA-256 of the file
  they point to. `scripts/integrate_data.py` run twice gives identical output (byte-stable).
- Gates after repair: `room_extract` (WPT-08 fee-split irregularity still printed, still flagged),
  `integrate_data`, `verify_root` (16 pages, 253 rows, 0 warnings), `verify`, `verify_markup` (37/0),
  `linkcheck` (30 pages).

## R2 — live spot-check against official sources

Method: the official pages were read live with the page-fetch tool (rendered text, not bytes), and
compared with the committed captures in `data/raw/`. A byte-level hash comparison of the live PDF
was **not** possible from this sandbox; the capture headers record the source hash at capture time.

| # | Official source (live) | Committed capture | Result |
|---|---|---|---|
| 1 | Venetian poker room page — https://www.venetianlasvegas.com/resort/casino/poker.html | `data/raw/venetian-poker-room.txt` | Match: "Open 24 Hours", "50 tables", "14,000 square feet", free self-parking for non-registered guests who play 3+ hours |
| 2 | Wynn WPT World Championship structures PDF (general terms and each event sheet) — https://cdn.wynnresorts.com/image/upload/v1750864036/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Structures.pdf | `data/raw/wynn-wpt-terms.txt` | Match on every event read: $600 NLH Turbo $515/$60/$25; $1,600 PLO Mystery Bounty $930/$500/$120/$50; $600 Limit O8/Stud 8 $510/$65/$25; $1,100 PLO $975/$85/$45; $1,600 NLH $1,430/$120/$50; $600 HORSE $510/$65/$25; $1,100 WPT Prime $970/$90/$40. Re-entry lines match ("Unlimited re-entry… level 9", "One (1) Entry and One (1) re-entry…", "Unlimited re-entry for each starting flight… level 10"). "Four (4) Entries maximum" appears in the committed capture (WPT World Championship sheet) and was not re-read live in this check. |
| 3 | Caesars daily flyer 2026 | `data/raw/caesars-daily-flyer-2026.txt` | Not re-read live in this session (see irregularities). |

## Irregularities (logged, not corrected)

1. Stale hashes in `data/room-facts.json` before this session (repaired, see R1).
2. WPT-08 printed fee split ($1,105) does not equal the printed buy-in ($1,100) — unchanged from prior
   logs; still flagged by `room_extract.py`.
3. The live PDF cannot be hashed from this sandbox, so byte-identity with the committed capture is
   unconfirmed; only the text read live was compared.
4. The Caesars flyer was not re-checked live in this session; its last capture stands as recorded.
