# Vegas Field Notes

A static, official-source-checked dashboard for selected upcoming Las Vegas Strip poker tournaments, strict single-entry rules, prize-pool fee shares, and hotel resort fees.

## Research snapshot

- Snapshot date: **November 16, 2026 (UTC)**.
- Reviewed scope: selected published events and recurring-room schedules for Venetian, Wynn/WPT, Caesars Palace, Horseshoe, MGM Grand, Bellagio, ARIA, Westgate, and SAHARA; official hotel fee pages for matched properties.
- **Strict single-entry events confirmed: 0.** An event qualifies only when current official terms explicitly limit a player to one paid entry for the entire event and disallow re-entry, rebuys, add-ons, and paid extra chips. Missing terms are marked unknown, not interpreted as a freezeout.
- Exact hotel totals are intentionally omitted without trip dates, stay length, room type, and occupancy. Published resort fees are separated from taxes and room rates.
- The dashboard is a researched snapshot, not a live feed or an exhaustive inventory of every Las Vegas poker room.

The source register and detailed findings are in [`research/VERIFICATION.md`](research/VERIFICATION.md). The public dashboard links directly to the official event, structure, room, hotel, and fee sources used for each finding.

## Run locally

No package install or build step is required. From the repository root:

```sh
python3 -m http.server 4173 --bind 0.0.0.0 --directory site
```

Then open `http://localhost:4173`. The dashboard loads `site/data.json` with `fetch`, so opening `index.html` as a `file://` URL will not work.

Validate the dataset and dashboard references with:

```sh
python3 scripts/validate_site.py
node --check site/app.js
```

## Update the research

1. Use current official casino, tournament-operator, and hotel sources; record the fetch date and caveats in `research/VERIFICATION.md`.
2. Keep entry status as `unknown` unless the event-specific official rules establish a one-entry maximum for the whole event.
3. Add or update the sourced record in `site/data.json`; reference only source IDs in its `sources` list.
4. Run both validation commands above and review the dashboard at desktop and mobile sizes.
5. Update the snapshot date and release/deployment notes. Recheck schedules before any trip.

`site/index.html`, `site/styles.css`, and `site/app.js` are a dependency-free static frontend. The dashboard includes an event filter/search, CSV export, print layout, source register, and responsive navigation.

## GitHub Pages

`.github/workflows/pages.yml` validates the files and publishes the `site/` directory to GitHub Pages whenever changes to the dashboard land on `main` (or on a manual workflow dispatch). Set the repository’s Pages source to **GitHub Actions** if it is not already enabled. Deployment becomes public only after the workflow runs successfully on `main`.
