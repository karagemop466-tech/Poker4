# Session b808eea0 artifacts

- `ui_smoke.js` — jsdom end-to-end smoke test of the built pages (run with
  `npm install jsdom` somewhere outside the repo, then
  `node -e "require('/path/to/jsdom')"` compatible run:
  `NODE_PATH=<dir with node_modules> node data/b808eea0/ui_smoke.js`).
  Covers: date filter, single-entry toggle (must show 0 rows — 0 events are
  confirmed single-entry), global search incl. no-match message, trip-cost
  calculator arithmetic (night = (rate+fee)×1.1338, hotel = night×nights+parking,
  trip = entries + hotel), "cannot compute" honesty when no dated rate, and the
  ≤30-min walk filter (shows only properties with a measured walk ≤ 30 min, per
  the Google Maps measurements merged 2026-11-17). Written 2026-11-17; all checks
  green on the merged tree.
