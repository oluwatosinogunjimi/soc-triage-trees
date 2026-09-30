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
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import ROOT, validate  # noqa: E402

SITE = ROOT / "site"
DIST = ROOT / "dist"
MARKER = "/*__TREE_DATA__*/null"


def csp(fragment: str) -> str:
    """Content Security Policy for the published page.

    Only the page's own inline script may run (pinned by its hash, so an injected
    <script> or event handler is blocked), the only outside origins are Google Fonts,
    and the page can make no network requests, so case data cannot leave the browser.
    """
    scripts = re.findall(r"<script>(.*?)</script>", fragment, flags=re.S)
    hashes = " ".join(
        "'sha256-" + base64.b64encode(hashlib.sha256(s.encode("utf-8")).digest()).decode() + "'"
        for s in scripts
    )
    return "; ".join([
        "default-src 'none'",
        f"script-src {hashes}",
        "style-src 'unsafe-inline' https://fonts.googleapis.com",
        "font-src https://fonts.gstatic.com",
        "img-src data:",
        "connect-src 'none'",
        "base-uri 'none'",
        "form-action 'none'",
        "object-src 'none'",
    ])


def main() -> int:
    trees, errors, warnings = validate()
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
    # Escape "</" so a query containing "</script>" cannot close the tag.
    safe = payload.replace("</", "<\\/")
    fragment = template.replace(MARKER, safe)
    (DIST / "viewer.html").write_text(fragment, encoding="utf-8")
    page = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f'<meta http-equiv="Content-Security-Policy" content="{csp(fragment)}">\n'
        '<meta name="referrer" content="no-referrer">\n'
        "</head>\n<body>\n" + fragment + "\n</body>\n</html>\n"
    )
    (DIST / "index.html").write_text(page, encoding="utf-8")

    print(f"Built dist/index.html, dist/viewer.html and dist/trees.json ({len(trees)} trees)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
