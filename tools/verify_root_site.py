#!/usr/bin/env python3
"""Verification entry point for the published root dashboard.

This tool used to assert page markers and data-file names from before the last
site restructure (plan.html / review.html replaced schedule.html / trip-calculator.html,
and the canonical data layer moved from ``data/0f6c627b/`` to ``data/``). Against the
current, fully verified pages it reported 19 false errors, and because
``.github/workflows/recheck.yml`` ran it every morning the job was permanently red.

It now delegates to the canonical verifiers that actually guard the published site:

  * ``scripts/verify_root.py`` — internal links, anchors, unresolved template values,
    balanced markup, one official-source link (or an explicit unverified marker) on every
    event row, and agreement between the rendered rows and ``data/site-events.json``;
  * ``scripts/verify.py`` — the preserved df41f5c6 sub-site's own check.

Run: python3 tools/verify_root_site.py   (exit 0 = pass)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(script: str) -> int:
    path = ROOT / "scripts" / script
    proc = subprocess.run([sys.executable, str(path)], cwd=ROOT)
    return proc.returncode


def main() -> int:
    rc = run("verify_root.py")
    if rc != 0:
        return rc
    return run("verify.py")


if __name__ == "__main__":
    sys.exit(main())
