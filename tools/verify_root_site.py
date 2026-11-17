#!/usr/bin/env python3
"""Canonical root-site integrity gate.

Delegates link/data validation to scripts/verify_root.py and the preserved
df41f5c6 sub-site check (scripts/verify.py), then checks the current dashboard
features without depending on page-specific editorial wording:

  * every generated table page exists;
  * any page with a <table> carries the universal search input (data-search)
    and loads assets/dashboard.js.

Run: python3 tools/verify_root_site.py   (exit 0 = pass)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []


def run(script: str) -> int:
    path = ROOT / "scripts" / script
    proc = subprocess.run([sys.executable, str(path)], cwd=ROOT)
    return proc.returncode


if run("verify_root.py") != 0:
    errors.append("scripts/verify_root.py failed")
if run("verify.py") != 0:
    errors.append("scripts/verify.py failed")

# Source rows and the universal table search must be present on the generated
# pages that actually contain data tables. Keep these checks structural.
table_pages = ["tournaments.html", "schedule.html", "hotels.html", "venues/venetian.html",
               "venues/wynn.html", "venues/others.html", "flagged.html", "questions.html",
               "suggestions.html", "sources.html", "monitoring.html"]
for rel in table_pages:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"{rel}: missing generated dashboard page")
        continue
    doc = path.read_text(encoding="utf-8")
    if "<table" in doc and "data-search" not in doc:
        errors.append(f"{rel}: table page has no search input")
    if "<table" in doc and "assets/dashboard.js" not in doc:
        errors.append(f"{rel}: table page does not load the dashboard behavior")

if errors:
    print("ERRORS:")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print("OK: canonical dashboard integrity and table-search checks passed")
