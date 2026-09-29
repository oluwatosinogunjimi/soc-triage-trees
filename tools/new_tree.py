#!/usr/bin/env python3
"""Scaffold a new tree file that already passes validation.

Usage: python tools/new_tree.py <id> "<Title>" <category>
Example: python tools/new_tree.py mfa-fatigue "MFA Fatigue / Push Bombing" identity
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = ["triage", "email", "identity", "endpoint", "network", "cloud"]

TEMPLATE = """id: {id}
title: {title}
category: {category}
summary: >-
  One or two sentences on what this alert is and the questions that decide it.
applies_to: [Example alert name]
mitre: []
version: 0.1.0
last_reviewed: {today}
authors: [Your Name]
sources:
  - title: Where the checks come from (vendor playbook, ATT&CK page, your write-up)
    url: https://attack.mitre.org/
entities:
  - {{ key: user, label: User principal name, example: "jdoe@contoso.com" }}
start: c-context
nodes:
  c-context:
    type: check
    text: Establish what fired and for whom.
    look_for:
      - The detection logic and the fields that matched
    note: I reviewed the alert for {{{{user}}}}.
    next: q-expected

  q-expected:
    type: question
    text: Is the activity expected for this user?
    yes: o-benign
    no: o-escalate
    notes:
      yes: The activity is expected for {{{{user}}}}.
      no: The activity is not expected for {{{{user}}}}.

  o-benign:
    type: outcome
    verdict: benign_positive
    title: Expected activity
    anchor: The activity is expected for {{{{user}}}}.
    risk: The risk here is X; it doesn't apply because Y.
    actions: [Close]

  o-escalate:
    type: outcome
    verdict: true_positive
    title: Unexpected activity
    anchor: The activity is not expected for {{{{user}}}}.
    risk: The risk here is X; containment is required.
    actions: [Escalate per client RACI]
    escalate: true
"""


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[3] not in CATEGORIES:
        print(__doc__)
        print("Categories:", ", ".join(CATEGORIES))
        return 1
    tid, title, category = sys.argv[1:]
    path = ROOT / "trees" / f"{tid}.yaml"
    if path.exists():
        print(f"{path} already exists")
        return 1
    path.write_text(TEMPLATE.format(id=tid, title=title, category=category, today=date.today().isoformat()), encoding="utf-8")
    print(f"Created {path.relative_to(ROOT)}. Edit it, then run: python tools/validate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
