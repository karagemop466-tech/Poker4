# Las Vegas Strip Poker Finder

Static GitHub Pages site. Every table row cites an official source. Values that could not be confirmed are left blank and marked ⚑ and listed on `flagged.html`.

## Pages
- `index.html` — summary and headline numbers
- `tournaments.html` — main list (Venetian DeepStack Extravaganza IV), with single-entry status shown
- `addons.html` — Wynn daily, Wynn WPT, Bellagio: re-entry, rebuy, add-on events
- `schedule.html` — official start times by day
- `hotels.html` — resort fees; room rates and walk times not yet captured
- `questions.html` — open questions and how to get each answer
- `review.html` — repo review and irregularities
- `flagged.html` — every unverified value

## Data
- `data/venetian_deepstack_iv.csv` — all 94 official schedule rows
- `data/wynn_daily.csv`, `data/wynn_wpt.csv`, `data/bellagio.csv`, `data/resort_fees.csv`

## Rebuild
    python3 tools/build.py

Pages are generated from the CSVs. Edit data, not HTML.
