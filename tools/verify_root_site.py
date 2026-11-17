#!/usr/bin/env python3
"""Canonical root-site integrity gate.

The older verifier asserted markers from a pre-2026 root-page generation and
produced false failures against the integrated dashboard. This gate delegates
link/data validation to scripts/verify_root.py and checks the current dashboard
features without depending on page-specific editorial wording.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []

result = subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "verify_root.py")],
    cwd=ROOT, text=True, capture_output=True,
)
print(result.stdout, end="")
if result.stderr:
    print(result.stderr, file=sys.stderr, end="")
if result.returncode:
    errors.append("scripts/verify_root.py failed")

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
