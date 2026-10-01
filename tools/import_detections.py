#!/usr/bin/env python3
"""Copy detection rules from the KQL-Query repo into detections/*.yaml.

Optional helper. The site only ever reads detections/*.yaml in this repo, so it
never depends on the KQL-Query repo being there, keeping its name, or keeping
its layout. You can also add or edit a file in detections/ by hand.

If a rule can't be read (a missing section, a renamed heading), it is skipped
with a message and its existing copy here is left untouched. Nothing is deleted.

Usage: python tools/import_detections.py ../KQL-Query
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "detections"
REPO_URL = "https://github.com/oluwatosinogunjimi/KQL-Query/blob/main/"
PLAYBOOK_LINK = re.compile(r"soc-triage-trees/#([a-z0-9-]+)\)")


class Block(str):
    """A string that YAML should write as a | block."""


def _block(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


yaml.add_representer(Block, _block, Dumper=yaml.SafeDumper)


def sections(md: str) -> dict[str, str]:
    out, name, buf = {}, None, []
    for line in md.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            if name:
                out[name] = "\n".join(buf).strip()
            name, buf = re.sub(r"\s*\(ADS\)$", "", m.group(1)), []
        elif name:
            buf.append(line)
    if name:
        out[name] = "\n".join(buf).strip()
    return out


def bullets(text: str) -> list[str]:
    return [re.sub(r"^- ", "", l).strip() for l in text.splitlines() if l.startswith("- ") and l[2:].strip()]


def fields(text: str) -> dict[str, str]:
    out = {}
    for b in bullets(text):
        k, _, v = b.partition(":")
        out[k.strip()] = v.strip()
    return out


def table(text: str) -> list[list[str]]:
    rows = [l for l in text.splitlines() if l.startswith("|")]
    return [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]


def convert(path: Path, repo: Path) -> dict:
    s = sections(path.read_text(encoding="utf-8"))
    missing = [k for k in ("Title", "Goal", "MITRE Mapping", "KQL Query") if not s.get(k)]
    if missing:
        raise ValueError("missing section(s): " + ", ".join(missing))
    for k in ("Description", "Strategy Abstract", "Technical Context", "Blind Spots and Assumptions", "False Positives",
              "Severity", "Frequency / Lookback", "Recommended Actions", "Alert Settings", "Entity Mapping", "Validation", "Tuning Notes"):
        s.setdefault(k, "")
    mitre = fields(s["MITRE Mapping"])
    sev = bullets(s["Severity"])
    freq = fields(s["Frequency / Lookback"])
    m = re.search(r"```(?:kusto|kql)?\n(.*?)```", s["KQL Query"], re.S)
    if not m:
        raise ValueError("no query code block under KQL Query")
    kql = m.group(1).rstrip() + "\n"
    actions = bullets(s["Recommended Actions"])
    playbooks = [m.group(1) for a in actions for m in PLAYBOOK_LINK.finditer(a)]
    alert_lines = s["Alert Settings"].splitlines()
    alert = fields("\n".join(l for l in alert_lines if l.startswith("- ")))
    details = [l.strip()[2:] for l in alert_lines if l.startswith("  - ")]
    return {
        "id": path.stem,
        "title": s["Title"].strip(),
        "tactic": mitre.get("Tactic", ""),
        "technique": mitre.get("Technique", ""),
        "technique_ids": [t.strip() for t in mitre.get("Technique ID", "").split(",") if t.strip()],
        "severity": sev[0] if sev else "",
        "severity_why": sev[1].removeprefix("Why:").strip() if len(sev) > 1 else "",
        "goal": s["Goal"],
        "description": s["Description"],
        "strategy": s["Strategy Abstract"],
        "technical_context": s["Technical Context"],
        "blind_spots": bullets(s["Blind Spots and Assumptions"]),
        "false_positives": bullets(s["False Positives"]),
        "frequency": freq.get("Run frequency", ""),
        "lookback": freq.get("Lookback period", ""),
        "kql": Block(kql),
        "alert": {
            "title": alert.get("Title (max 3 variables)", ""),
            "description": alert.get("Description (max 3 variables)", ""),
            "custom_details": details,
        },
        "entity_mapping": {k: v for k, v in fields(s["Entity Mapping"]).items() if v and v != "N/A"},
        "validation": [dict(zip(["date", "method", "environment", "result"], r)) for r in table(s["Validation"])],
        "playbooks": playbooks,
        "actions": [a for a in actions if not a.startswith("Triage playbook:")],
        "tuning": [dict(zip(["date", "change", "reason"], r)) for r in table(s["Tuning Notes"])],
        "source": REPO_URL + path.relative_to(repo).as_posix(),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    repo = Path(sys.argv[1]).resolve()
    files = sorted((repo / "detections").glob("*/*.md"))
    if not files:
        print(f"error: no rules found under {repo / 'detections'}")
        return 1
    OUT.mkdir(exist_ok=True)
    done = 0
    for f in files:
        try:
            rule = convert(f, repo)
        except Exception as e:  # one bad rule never stops the rest, and never overwrites a good copy
            print(f"  skipped {f.name}: {e}")
            continue
        done += 1
        head = (f"# Copied from {rule['source']}\n"
                "# The site reads only this file. Edit it here by hand, or re-run tools/import_detections.py.\n")
        body = yaml.safe_dump(rule, sort_keys=False, allow_unicode=True, width=1000)
        (OUT / f"{rule['id']}.yaml").write_text(head + body, encoding="utf-8")
        print(f"  {rule['id']}  ->  playbooks: {', '.join(rule['playbooks']) or 'none'}")
    print(f"Imported {done} of {len(files)} rules into detections/. Run python tools/validate.py next.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
