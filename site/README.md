# Vegas Field Notes

This self-contained static dashboard is a sub-site of the Poker4 repository. The existing repository Pages workflow publishes the repository root; after the change is merged and deployed, the dashboard is available at `/site/` (for example, `https://karagemop466-tech.github.io/Poker4/site/`). It does not replace the root dashboard or the shared Pages workflow.

## Research snapshot

- Snapshot: November 16, 2026 (UTC).
- Zero strict single-entry tournaments are confirmed by the reviewed official rules. Unknown terms are not treated as freezeout terms.
- All-in hotel totals are omitted because trip dates, stay length, room type, and occupancy were not supplied.
- Full dated findings and limitations: [`../research/VERIFICATION.md`](../research/VERIFICATION.md).

## Run and validate

From the repository root, serve this folder (the dashboard uses `fetch` for its JSON data):

```sh
python3 -m http.server 4173 --bind 0.0.0.0 --directory site
```

Run checks from the repository root:

```sh
python3 scripts/validate_site.py
node --check site/app.js
```

The UI is dependency-free and includes a searchable, filterable dated schedule, CSV export, print styling, recurring-room schedules, hotel fee comparisons, and official-source links.
