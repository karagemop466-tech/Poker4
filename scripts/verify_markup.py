#!/usr/bin/env python3
"""Markup + link gate for the published site (used by .github/workflows/site-verify.yml).

Kept as a script rather than an inline heredoc so the workflow YAML stays parseable.
Checks every root and venue page for unbalanced tags and for links that point at a file
that does not exist in the repository — a broken page must never reach GitHub Pages.
"""
import glob
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
        "source", "track", "wbr"}


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.problems.append(f"unclosed <{self.stack[-1]}> before </{tag}>")
                self.stack.pop()
            self.stack.pop()
        else:
            self.problems.append(f"stray </{tag}>")


pages = sorted(glob.glob(os.path.join(ROOT, "*.html"))) + sorted(glob.glob(os.path.join(ROOT, "venues", "*.html")))
bad = 0
for path in pages:
    rel = os.path.relpath(path, ROOT)
    doc = open(path, encoding="utf-8").read()
    bal = Balance()
    bal.feed(doc)
    leftover = [t for t in bal.stack if t not in ("html", "body")]
    if leftover or bal.problems:
        print(f"{rel}: markup problems {bal.problems[:3]} unclosed={leftover[:4]}")
        bad += 1
    for target in re.findall(r'(?:href|src)="([^"]+)"', doc):
        if target.startswith(("http:", "https:", "mailto:", "#", "data:")):
            continue
        f = target.split("#")[0]
        if f and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), f))):
            print(f"{rel}: broken internal link -> {target}")
            bad += 1
    if re.search(r"\bundefined\b|\[object Object\]|>None<", doc):
        print(f"{rel}: unresolved template value reached the page")
        bad += 1
print(f"markup gate: {len(pages)} pages checked, {bad} problems")
sys.exit(1 if bad else 0)
