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


def test_detection_rules_validate_and_link_to_real_playbooks():
    from validate import load_detections

    trees, errors, _ = validate()
    assert not errors
    dets, det_errors = load_detections(trees)
    assert not det_errors
    assert dets, "expected at least one detection rule in detections/"
    for d in dets.values():
        assert all(pb in trees for pb in d["playbooks"])


def test_detection_with_missing_playbook_is_caught(tmp_path):
    import yaml
    from validate import load_detections

    trees, _, _ = validate()
    rule = yaml.safe_load((ROOT / "detections" / "net-user-add.yaml").read_text())
    rule["playbooks"] = ["no-such-playbook"]
    (tmp_path / "net-user-add.yaml").write_text(yaml.safe_dump(rule))
    _, errors = load_detections(trees, tmp_path)
    assert any("no-such-playbook" in e for e in errors)


def test_import_reads_attack_v20_mapping(tmp_path):
    sys.path.insert(0, str(ROOT / "tools"))
    from import_detections import convert

    rule = tmp_path / "detections" / "credential-access" / "lsass-test.md"
    rule.parent.mkdir(parents=True)
    rule.write_text(textwrap.dedent("""\
        # LSASS test
        ## Title
        LSASS test
        ## Goal (ADS)
        Catch LSASS dumping.
        ## MITRE Mapping
        - ATT&CK version: v20 (Enterprise)
        - Tactic: Credential Access (TA0006); Stealth (TA0005) for T1218.011
        - Technique: LSASS Memory (T1003.001), Rundll32 (T1218.011)
        - Technique ID: T1003.001, T1218.011
        - Detection Strategy: [DET0363](https://attack.mitre.org/detectionstrategies/DET0363) (T1003.001), [DET0475](https://attack.mitre.org/detectionstrategies/DET0475) (T1218.011)
        - Analytic (Windows): [AN1030](https://attack.mitre.org/detectionstrategies/DET0363#AN1030) (T1003.001), [AN1308](https://attack.mitre.org/detectionstrategies/DET0475#AN1308) (T1218.011)
        - Telemetry: DeviceProcessEvents
        ## KQL Query
        ```kql
        DeviceProcessEvents
        ```
        """))
    d = convert(rule, tmp_path)
    assert d["tactic"] == "Credential Access"
    assert d["tactics"] == ["Credential Access", "Stealth"]
    assert d["attack_version"] == "v20 (Enterprise)"
    assert d["detection_strategies"] == ["DET0363", "DET0475"]
    assert d["analytics"] == [{"id": "AN1030", "strategy": "DET0363"}, {"id": "AN1308", "strategy": "DET0475"}]
    assert d["telemetry"] == "DeviceProcessEvents"


def test_osint_tools_validate_and_link_to_real_playbooks():
    from validate import load_osint

    trees, _, _ = validate()
    tools, errors, _ = load_osint(trees)
    assert not errors, "\n".join(errors)
    assert tools, "expected at least one tool in osint/tools.yaml"
    assert len({t["id"] for t in tools}) == len(tools)


def _osint_file(tmp_path, tool):
    import yaml
    path = tmp_path / "tools.yaml"
    path.write_text(yaml.safe_dump({"tools": [tool]}))
    return path


GOOD_TOOL = {
    "id": "sample", "name": "Sample", "url": "https://example.com/", "group": "reputation",
    "what": "w", "use_when": "u", "opsec": "lookup", "access": "free",
    "lookups": {"ip": "https://example.com/ip/{value}"},
    "playbooks": ["risky-ip-signin"], "verified": {"date": "2026-10-01", "how": "Opened it."},
}


def test_osint_bad_playbook_template_and_future_date_are_caught(tmp_path):
    from datetime import date
    from validate import load_osint

    trees, _, _ = validate()
    bad = dict(GOOD_TOOL, playbooks=["no-such-playbook"], lookups={"ip": "https://example.com/{hashtype}/{value}"},
               verified={"date": "2027-01-01", "how": "x"})
    _, errors, _ = load_osint(trees, _osint_file(tmp_path, bad), today=date(2026, 10, 1))
    assert any("no-such-playbook" in e for e in errors), errors
    assert any("hashtype" in e for e in errors), errors
    assert any("future" in e for e in errors), errors


def test_osint_template_without_value_and_unknown_type_fail_schema(tmp_path):
    from validate import load_osint

    trees, _, _ = validate()
    for lookups in ({"ip": "https://example.com/static"}, {"asn": "https://example.com/{value}"}):
        _, errors, _ = load_osint(trees, _osint_file(tmp_path, dict(GOOD_TOOL, lookups=lookups)))
        assert errors, lookups


def test_osint_stale_check_warns(tmp_path):
    from datetime import date
    from validate import load_osint

    trees, _, _ = validate()
    _, errors, warnings = load_osint(trees, _osint_file(tmp_path, GOOD_TOOL), today=date(2027, 6, 1))
    assert not errors
    assert any("over 180 days" in w for w in warnings), warnings


def test_public_safety_lint(tmp_path):
    from validate import check_public_safety
    p = tmp_path / "t.yaml"
    p.write_text(
        "a: jdoe@contoso.com\n"
        "b: someone@realclient.co.uk\n"
        "c: 3f2504e0-4f89-11d3-9a0c-0305e82c3301\n"
        "d: 1131f6aa-9c07-11d1-f79f-00c04fc2dcd2\n"
        "e: connects to ACME-DC01\n"
    )
    errors = check_public_safety([p], denylist=["acme-dc01"])
    joined = "\n".join(errors)
    assert "realclient.co.uk" in joined
    assert "3f2504e0" in joined
    assert "1131f6aa" not in joined and "domain 'contoso.com'" not in joined
    assert "denylisted term" in joined
    assert len(errors) == 3


def test_typed_actions_and_lifecycle(tmp_path):
    body = BASE.format(id="lifecycle") + textwrap.indent(textwrap.dedent("""
        q-a:
          type: question
          text: Is it bad?
          on_empty: No rows means the sign-in table is not connected; resolve the gap first.
          yes: o-bad
          no: o-ok
          notes: {yes: It is bad., no: It is fine.}
        o-bad:
          type: outcome
          verdict: true_positive
          title: Bad
          anchor: It was bad.
          risk: Risk applies.
          actions:
            - {type: contain, text: Revoke sessions, approval: SOC lead, reversible: true}
            - {type: notify, text: Phone the user, tip_off: true}
            - Plain string action
        o-ok:
          type: outcome
          verdict: false_positive
          title: Fine
          anchor: It was fine.
          risk: Risk does not apply.
          actions: [Close]
    """), "  ")
    body = body.replace("authors: [Test]", "authors: [Test]\nstatus: stable\nreview_by: 2000-01-01")
    _write(tmp_path, "lifecycle", body)
    trees, errors, warnings = validate(tmp_path)
    assert not errors, errors
    assert any("review_by" in w for w in warnings)

    bad = body.replace("approval: SOC lead, ", "")
    _write(tmp_path, "lifecycle", bad)
    _, errors, _ = validate(tmp_path)
    assert any("schema" in e for e in errors), "contain without approval should fail"
