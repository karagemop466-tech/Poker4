#!/usr/bin/env python3
"""Internal link audit for the root dashboard pages.

Checks that every local href/src in the given HTML files resolves to a file
in the repository. External http(s) links are listed but not fetched.
Exit code 1 if any internal link is broken.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGES = [
    "index.html", "tournaments.html", "schedule.html", "hotels.html",
    "decisions.html", "questions.html", "review.html", "calculator.html",
    "trip-calculator.html", "change-monitor.html",
    "venue-venetian.html", "venue-wynn.html", "venue-others.html",
    "recheck.html", "sources.html", "suggestions.html",
]

ATTR = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"')


def check(path: Path) -> list[str]:
    problems = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw in ATTR.findall(text):
        if raw.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
            continue
        if "${" in raw:  # template literal inside an inline script, not a real link
            continue
        target = unquote(urlparse(raw).path)
        if not target:
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            problems.append(f"{path.name}: escapes repo: {raw}")
            continue
        if not resolved.exists():
            problems.append(f"{path.name}: broken link -> {raw}")
    return problems


def main() -> int:
    pages = [ROOT / p for p in (sys.argv[1:] or DEFAULT_PAGES)]
    problems: list[str] = []
    for page in pages:
        if not page.exists():
            problems.append(f"missing page: {page.name}")
            continue
        problems.extend(check(page))
    if problems:
        print("FAIL: internal link problems:")
        for p in problems:
            print(" -", p)
        return 1
    print(f"OK: {len(pages)} pages, all internal links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
