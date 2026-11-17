# prior_root_dashboard — preserved snapshot of the previous root dashboard

This folder preserves, byte for byte, the root-site files that were live on `main`
immediately before the `0f6c627b` integration (PR #33), so that no parallel
session's work is discarded when the root pages were replaced by the integrated
dashboard.

- `index.html`, `tournaments.html`, `schedule.html`, `hotels.html`, `questions.html`,
  `suggestions.html`, `sources.html`, `monitor.html`, `trip-calculator.html`,
  `assets/site.css`, `assets/site.js`, `venues/*.html` — the prior root pages at the
  moment of the merge conflict.
- `data_v2_json/` — the `data/v2/{events,flagged,hotels,sources}.json` files as they
  were on main's side of the conflict (the live `data/v2/` lane on `main` is unchanged
  and continues to feed the `v2/` subsite and `v2-monitor.yml`).
- `COORDINATION.theirs.md`, `README.theirs.md`, `COORDINATION.mine.md` — board and
  README snapshots from both sides of the conflict.

The prior root dashboard is still buildable from the repository root with
`python3 tools/build_data.py && python3 tools/build_site.py` (its own builders, kept
in `tools/`). The current root dashboard is built by `tools/build_root_site.py` from
`data/0f6c627b/`. Never run both builders against the same output paths.
