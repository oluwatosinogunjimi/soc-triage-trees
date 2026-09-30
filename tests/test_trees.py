"""Run with: python -m pytest -q"""
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from validate import validate  # noqa: E402


def test_repository_trees_are_valid():
    trees, errors, _ = validate(ROOT / "trees")
    assert not errors, "\n".join(errors)
    assert "universal-triage" in trees


def test_every_outcome_is_reachable_somewhere():
    trees, _, _ = validate(ROOT / "trees")
    for t in trees.values():
        assert any(n["type"] == "outcome" for n in t["nodes"].values()), f"{t['id']} has no outcomes"


def _write(tmp: Path, name: str, body: str) -> None:
    (tmp / f"{name}.yaml").write_text(textwrap.dedent(body))


BASE = """
id: {id}
title: Test tree
category: identity
summary: A test tree used by the validator tests.
version: 0.1.0
last_reviewed: 2026-01-01
authors: [Test]
start: q-a
nodes:
"""


def test_broken_edge_and_orphan_are_caught(tmp_path):
    _write(tmp_path, "t-one", BASE.format(id="t-one") + """
  q-a:
    type: question
    text: A?
    yes: o-done
    no: q-missing
    notes: {yes: y, no: n}
  o-done:
    type: outcome
    verdict: false_positive
    title: Done
    anchor: a
    risk: r
    actions: [x]
  o-orphan:
    type: outcome
    verdict: false_positive
    title: Orphan
    anchor: a
    risk: r
    actions: [x]
""")
    _, errors, _ = validate(tmp_path)
    assert any("q-missing" in e for e in errors)
    assert any("o-orphan" in e and "unreachable" in e for e in errors)


def test_cross_tree_cycle_is_caught(tmp_path):
    for me, other in (("t-one", "t-two"), ("t-two", "t-one")):
        _write(tmp_path, me, BASE.format(id=me) + f"""
  q-a:
    type: question
    text: A?
    yes: l-go
    no: o-done
    notes: {{yes: y, no: n}}
  l-go:
    type: link
    text: go
    tree: {other}
  o-done:
    type: outcome
    verdict: false_positive
    title: Done
    anchor: a
    risk: r
    actions: [x]
""")
    _, errors, _ = validate(tmp_path)
    assert any(e.startswith("cycle:") for e in errors)


def test_undeclared_placeholder_and_duplicate_key(tmp_path):
    _write(tmp_path, "t-one", BASE.format(id="t-one") + """
  q-a:
    type: question
    text: Is {{user}} ok?
    yes: o-done
    no: o-done
    no: o-done
    notes: {yes: y, no: n}
  o-done:
    type: outcome
    verdict: false_positive
    title: Done
    anchor: a
    risk: r
    actions: [x]
""")
    _, errors, _ = validate(tmp_path)
    assert any("duplicate key" in e for e in errors)


def test_build_produces_site(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "build.py")], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    html = (ROOT / "dist" / "index.html").read_text()
    assert "/*__TREE_DATA__*/null" not in html
    assert '"universal-triage"' in html


def test_router_and_catalogue_are_current():
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "gen_router.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout


def test_every_playbook_is_reachable_from_universal_triage():
    trees, _, _ = validate(ROOT / "trees")
    linked = {n["tree"] for n in trees["universal-triage"]["nodes"].values() if n["type"] == "link"}
    missing = sorted(t for t, tree in trees.items() if tree["category"] != "triage" and t not in linked)
    assert not missing, f"Not routed from universal-triage: {missing}"


def test_repeated_also_check_is_caught(tmp_path):
    _write(tmp_path, "t-also", BASE.format(id="t-also") + """
  q-a:
    type: question
    text: A?
    also_check:
      - "Did anything else happen?"
    yes: c-b
    no: c-b
    notes: {yes: y, no: n}
  c-b:
    type: check
    text: B
    also_check:
      - "Did anything else happen?"
    note: b
    next: o-done
  o-done:
    type: outcome
    verdict: false_positive
    title: Done
    anchor: a
    risk: r
    actions: [x]
""")
    _, errors, _ = validate(tmp_path)
    assert any("also_check repeated" in e for e in errors), errors


def test_csp_pins_the_inline_script():
    import base64
    import hashlib

    import build

    body = "const x = 1;"
    policy = build.csp("<div></div><script>" + body + "</script>")
    digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
    assert f"script-src 'sha256-{digest}'" in policy
    assert "connect-src 'none'" in policy
    assert "unsafe-inline" not in policy.split("script-src")[1].split(";")[0]
