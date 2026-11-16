# Poker Trip Planner — Las Vegas

A static, source-linked research dashboard for upcoming Las Vegas poker tournaments, tournament entry-rule checks, hotel pricing, decision questions, and unresolved research flags.

## Dashboard pages

- [Executive overview](index.html)
- [Tournament candidates and special formats](schedule.html)
- [Hotels and conditional nightly cost floors](hotels.html)
- [Decision checklist](decisions.html)
- [Flagged for Review](review.html)
- [Sources and methodology](sources.html)

## Research scope and caution

Snapshot dated November 16, 2026. The verified upcoming schedule currently included is the Venetian DeepStack Extravaganza IV (Nov 16–Dec 23, 2026). The listed plain-format candidate events are **not confirmed single-entry**: the official sources reviewed do not publish a maximum-entry / re-entry / rebuy / add-on policy. Do not treat the shortlist as meeting a strict single-entry requirement until the organizer confirms it. Dated hotel totals are also unavailable without stay dates and a live official quote; conditional starting floors are clearly labeled.

All data is static and kept in `data.js`; page rendering and filtering are in `site.js`; styles are in `site.css`. Official source URLs are linked directly from every displayed data row. Unknown values remain blank and are listed on the Flagged for Review page.

## Local preview

Open `index.html` in a browser, or run a static server from this directory, for example:

```sh
python3 -m http.server 8000
```

## GitHub Pages

The repository's existing Pages configuration serves the repository root from `main` at [https://karagemop466-tech.github.io/Poker4/](https://karagemop466-tech.github.io/Poker4/). The site is plain static HTML, CSS, and JavaScript; `.nojekyll` keeps static assets available. Merging changes into `main` triggers the configured Pages build and deployment.
