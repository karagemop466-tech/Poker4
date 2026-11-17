Snapshots from `.github/workflows/v2-monitor.yml` (`check-<run-id>.txt`), plus the
baseline `data/v2/source_state.json`, are committed on purpose: they come from
GitHub runners with real network access, so they are an honest record of what the
official pages said on a given day.

`tools/v2_check_sources.py` refuses to write `source_state.json` at all if every
fetch failed, so a run from a network-blocked sandbox cannot create a false
"nothing changed" baseline.
