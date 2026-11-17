#!/usr/bin/env python3
"""Dependency-free consistency checks for the Vegas Field Notes dashboard."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA_PATH = SITE / "data.json"


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def check_source_refs(items: list[dict], source_ids: set[str], label: str) -> None:
    for index, item in enumerate(items, start=1):
        refs = item.get("sources", [])
        require(bool(refs), f"{label} item {index} has no evidence source")
        missing = set(refs) - source_ids
        require(not missing, f"{label} item {index} has unknown source IDs: {sorted(missing)}")


def main() -> None:
    for relative in ("index.html", "app.js", "styles.css", "favicon.svg", ".nojekyll"):
        require((SITE / relative).is_file(), f"missing site/{relative}")

    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot load site/data.json: {error}")

    sources = data.get("sources", [])
    source_ids = {source.get("id") for source in sources}
    require(len(source_ids) == len(sources), "source IDs must be unique")
    require(None not in source_ids, "every official source needs an ID")
    official_hosts = (
        "venetianlasvegas.com", "caesars.com", "wynnresorts.com", "wynnlasvegas.com",
        "worldpokertour.com", "mgmresorts.com", "contentstack.io", "westgateresorts.com",
        "saharalasvegas.com",
    )
    for source in sources:
        parsed = urlparse(source.get("url", ""))
        require(parsed.scheme == "https" and parsed.netloc, f"source is not an absolute HTTPS URL: {source}")
        require(any(parsed.hostname == host or parsed.hostname.endswith(f".{host}") for host in official_hosts), f"source host is outside the official-source allowlist: {source}")

    events = data.get("events", [])
    require(bool(events), "at least one dated event record is required")
    check_source_refs(events, source_ids, "event")
    check_source_refs(data.get("recurring", []), source_ids, "recurring schedule")
    check_source_refs(data.get("festivalEvents", []), source_ids, "festival event")
    check_source_refs(data.get("value", []), source_ids, "value example")
    check_source_refs(data.get("spendAdvantages", []), source_ids, "spend-advantage record")
    check_source_refs(data.get("hotels", []), source_ids, "hotel")
    check_source_refs([flag for flag in data.get("flags", []) if flag.get("sources")], source_ids, "flag")
    report_url = urlparse(data.get("meta", {}).get("reportUrl", ""))
    require(report_url.scheme == "https" and report_url.hostname == "github.com", "full research notes should link to this repository over HTTPS")
    for recommendation in data.get("recommendations", []):
        source_id = recommendation.get("source")
        if source_id:
            require(source_id in source_ids, f"recommendation refers to unknown source ID: {source_id}")

    confirmed = [event for event in events if event.get("status") == "confirmed"]
    require(data.get("summary", {}).get("confirmedSingleEntry") == len(confirmed), "confirmed count must match event statuses")
    require(not confirmed, "a newly confirmed event must first be reviewed against the strict-entry rule and report updated")
    require(data.get("summary", {}).get("eightAmVerified") == 0, "the current source snapshot verifies no 8 a.m. start")
    require(data.get("summary", {}).get("reviewedCandidateCount") == 8, "update the reviewed event count and README when the candidate set changes")
    require(all(event.get("status") in {"unknown", "excluded"} for event in events), "event status must be unknown or excluded until documented proof supports otherwise")

    snapshot = data.get("meta", {}).get("snapshot", "")
    require(bool(re.fullmatch(r"20\d{2}-\d{2}-\d{2}", snapshot)), "snapshot must use YYYY-MM-DD")
    for event in events:
        require(event.get("date", "") >= snapshot, f"event {event.get('id')} predates the research snapshot")
        require(bool(event.get("time")), f"event {event.get('id')} needs a verified start time")
        require(event.get("buyIn") is not None, f"event {event.get('id')} needs a published buy-in")
        require(0 < event.get("poolShare", 1) <= 100, f"invalid pool share for {event.get('id')}")
        require("re-entry" in event.get("rule", "").lower() or "entry" in event.get("rule", "").lower(), f"entry-rule explanation missing for {event.get('id')}")

    for hotel in data.get("hotels", []):
        if hotel.get("feeVerified"):
            require(isinstance(hotel.get("fee"), (int, float)), f"verified hotel fee missing numeric amount: {hotel.get('name')}")
        else:
            require(hotel.get("fee") is None, f"unverified hotel fee must not be presented as an exact property amount: {hotel.get('name')}")

    index = (SITE / "index.html").read_text(encoding="utf-8")
    app = (SITE / "app.js").read_text(encoding="utf-8")
    ids = re.findall(r'\bid="([^"]+)"', index)
    id_set = set(ids)
    duplicates = [element_id for element_id, count in Counter(ids).items() if count > 1]
    require(not duplicates, f"duplicate HTML IDs: {duplicates}")
    anchor_targets = re.findall(r'href="#([^"]+)"', index)
    require(set(anchor_targets) <= id_set, f"HTML anchor points to missing section: {sorted(set(anchor_targets) - id_set)}")
    recommendation_targets = {item["section"] for item in data.get("recommendations", []) if item.get("section")}
    require(recommendation_targets <= id_set, f"recommendation points to missing section: {sorted(recommendation_targets - id_set)}")
    js_targets = re.findall(r"\$\('#([a-zA-Z0-9_-]+)'", app)
    require(set(js_targets) <= id_set, f"JavaScript selector points to missing HTML ID: {sorted(set(js_targets) - id_set)}")
    require('id="event-table-body"' in index, "dashboard event table target missing")
    require('id="source-groups"' in index, "dashboard source register target missing")
    require("noopener noreferrer" in app, "external links should use safe target attributes")
    require("downloadCSV" in app, "CSV export handler missing")
    require("window.print()" in app, "print handler missing")

    print(
        "OK: "
        f"{len(events)} dated schedule rows / {data['summary']['reviewedCandidateCount']} reviewed event IDs, "
        f"{len(data.get('recurring', []))} recurring room schedules, {len(sources)} official sources, "
        f"{len(data.get('hotels', []))} hotel records. "
        "No strict single-entry qualifier is claimed."
    )


if __name__ == "__main__":
    main()
