#!/usr/bin/env python3
"""Validate the trees, then build the static site into dist/.

Outputs:
  dist/trees.json   all trees as one JSON bundle
  dist/index.html   the viewer as a full page with the bundle embedded (GitHub Pages, offline use)
  dist/viewer.html  the same page as a bare fragment, for hosts that supply their own <html> shell

Usage: python tools/build.py
"""
from __future__ import annotations

import base64
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import ROOT, load_detections, load_osint, validate  # noqa: E402

SITE = ROOT / "site"
DIST = ROOT / "dist"
MARKER = "/*__TREE_DATA__*/null"
FONT_BLOCK = re.compile(r"/\*__FONTS__\*/.*?/\*__END_FONTS__\*/", re.S)
# (file in site/fonts, CSS family name, licence file)
FONTS = [
    ("AtkinsonHyperlegibleNext.woff2", "Atkinson Hyperlegible Next", "OFL-AtkinsonHyperlegibleNext.txt"),
    ("AtkinsonHyperlegibleMono.woff2", "Atkinson Hyperlegible Mono", "OFL-AtkinsonHyperlegibleMono.txt"),
]


def embedded_fonts() -> str:
    """@font-face rules with the fonts inlined, so the built page needs no network.

    Both fonts are SIL Open Font License 1.1. The copyright line and licence name stay with
    each rule, and the full licence texts ship in site/fonts/.
    """
    rules = []
    for file, family, licence in FONTS:
        data = base64.b64encode((SITE / "fonts" / file).read_bytes()).decode("ascii")
        notice = (SITE / "fonts" / licence).read_text(encoding="utf-8").split("\n", 1)[0].split(") ", 1)[0] + ")"
        rules.append(
            f"/* {family}. {notice}. Licensed under the SIL Open Font License 1.1, https://openfontlicense.org */\n"
            f'@font-face {{ font-family: "{family}"; src: url(data:font/woff2;base64,{data}) format("woff2"); '
            f"font-weight: 200 800; font-style: normal; font-display: swap; }}"
        )
    return "\n".join(rules)


def main() -> int:
    trees, errors, warnings = validate()
    dets, det_errors = load_detections(trees)
    osint, osint_errors, osint_warnings = load_osint(trees)
    errors += det_errors + osint_errors
    warnings += osint_warnings
    for w in warnings:
        print(f"warning: {w}")
    if errors:
        for e in errors:
            print(f"error: {e}")
        print("Build aborted: fix validation errors first.")
        return 1

    order = {"triage": 0, "email": 1, "identity": 2, "endpoint": 3, "network": 4, "cloud": 5}
    bundle = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trees": [
            {k: v for k, v in t.items() if not k.startswith("_")}
            for t in sorted(trees.values(), key=lambda t: (order[t["category"]], t["title"]))
        ],
        "detections": sorted(dets.values(), key=lambda d: (d["tactic"], d["title"])),
        "osint": osint,
    }
    payload = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / "trees.json").write_text(payload, encoding="utf-8")

    template = (SITE / "viewer.html").read_text(encoding="utf-8")
    if MARKER not in template:
        print(f"error: {MARKER} marker missing from site/viewer.html")
        return 1
    if FONT_BLOCK.search(template):
        template = FONT_BLOCK.sub(lambda _: embedded_fonts(), template, count=1)
    # Escape "</" so a query containing "</script>" cannot close the tag.
    safe = payload.replace("</", "<\\/")
    fragment = template.replace(MARKER, safe)
    (DIST / "viewer.html").write_text(fragment, encoding="utf-8")
    page = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        "</head>\n<body>\n" + fragment + "\n</body>\n</html>\n"
    )
    (DIST / "index.html").write_text(page, encoding="utf-8")

    print(f"Built dist/index.html, dist/viewer.html and dist/trees.json ({len(trees)} trees, {len(dets)} detection rules, {len(osint)} OSINT tools)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
