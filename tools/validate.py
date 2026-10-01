#!/usr/bin/env python3
"""Validate every tree in trees/ against the schema and the graph rules.

Checks, in order:
  1. YAML parses, with no duplicate keys (PyYAML silently overwrites them).
  2. The file matches schema/tree.schema.json.
  3. The file name matches the tree id.
  4. start and every edge (yes/no/unknown/next/options) point at a node that exists.
  5. Every link points at a tree (and node) that exists.
  6. Every node is reachable from start (no orphans).
  7. No cycles, inside a tree or across trees through links.
  8. Every {{placeholder}} is declared in that tree's entities.
  9. No also_check question repeats within a tree.
 10. Warnings: unused entities, questions with an unknown edge but no unknown note.
 11. Detection rules in detections/ match schema/detection.schema.json and link to playbooks that exist.
 12. OSINT tools in osint/tools.yaml match schema/osint.schema.json, link to playbooks that exist,
     and were verified in the last 180 days (warning only).

Usage: python tools/validate.py [trees_dir]
Exit code 1 if any error.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "tree.schema.json"
PLACEHOLDER = re.compile(r"\{\{\s*([a-z][a-z0-9_]*)\s*\}\}")


class UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys."""


def _construct_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key '{key}'", key_node.start_mark
            )
        seen.add(key)
    return loader.construct_mapping(node, deep)


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)

# YAML 1.1 turns yes/no/on/off into booleans, which would break the yes:/no: edges.
# Keep only true/false as booleans.
UniqueKeyLoader.yaml_implicit_resolvers = {
    first: [(tag, rx) for tag, rx in resolvers if tag != "tag:yaml.org,2002:bool"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
UniqueKeyLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF")
)


def edges(node: dict) -> list[tuple[str, str]]:
    """Return (label, target) pairs for in-tree edges of a node."""
    t = node["type"]
    if t == "question":
        out = [("yes", node["yes"]), ("no", node["no"])]
        if "unknown" in node:
            out.append(("unknown", node["unknown"]))
        return out
    if t == "choice":
        return [(o["label"], o["next"]) for o in node["options"]]
    if t == "check":
        return [("next", node["next"])]
    return []


def strings_in(obj) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in strings_in(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in strings_in(v)]
    return []


def load_trees(trees_dir: Path) -> tuple[dict[str, dict], list[str]]:
    errors: list[str] = []
    trees: dict[str, dict] = {}
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    for path in sorted(trees_dir.glob("*.y*ml")):
        rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        try:
            data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        except yaml.YAMLError as exc:
            errors.append(f"{rel}: YAML error: {exc}")
            continue
        # YAML parses dates into date objects; the schema wants strings.
        if "last_reviewed" in data and not isinstance(data["last_reviewed"], str):
            data["last_reviewed"] = str(data["last_reviewed"])

        schema_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        for err in schema_errors:
            loc = "/".join(str(p) for p in err.path) or "(root)"
            errors.append(f"{rel}: schema: {loc}: {err.message}")
        if schema_errors:
            continue

        if data["id"] != path.stem:
            errors.append(f"{rel}: id '{data['id']}' must match file name '{path.stem}'")
        if data["id"] in trees:
            errors.append(f"{rel}: duplicate tree id '{data['id']}'")
        data["_path"] = str(rel)
        trees[data["id"]] = data
    return trees, errors


def check_graphs(trees: dict[str, dict]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for tid, tree in trees.items():
        where = tree["_path"]
        nodes = tree["nodes"]

        if tree["start"] not in nodes:
            errors.append(f"{where}: start '{tree['start']}' is not a node")
            continue

        for nid, node in nodes.items():
            for label, target in edges(node):
                if target not in nodes:
                    errors.append(f"{where}: {nid} --{label}--> '{target}' does not exist")
            if node["type"] == "link":
                target_tree = trees.get(node["tree"])
                if target_tree is None:
                    errors.append(f"{where}: {nid} links to unknown tree '{node['tree']}'")
                elif "node" in node and node["node"] not in target_tree["nodes"]:
                    errors.append(f"{where}: {nid} links to unknown node '{node['tree']}:{node['node']}'")
            if node["type"] == "question" and "unknown" in node and "unknown" not in node["notes"]:
                warnings.append(f"{where}: {nid} has an unknown edge but no notes.unknown")

        # also_check questions: each asked once per tree
        asked: dict[str, str] = {}
        for nid, node in nodes.items():
            for q in node.get("also_check", []):
                if q in asked:
                    errors.append(f"{where}: also_check repeated in {asked[q]} and {nid}: {q}")
                asked[q] = nid

        # Reachability
        seen, stack = set(), [tree["start"]]
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in nodes:
                continue
            seen.add(cur)
            stack.extend(t for _, t in edges(nodes[cur]))
        for orphan in sorted(set(nodes) - seen):
            errors.append(f"{where}: node '{orphan}' is unreachable from start")

        # Placeholders
        declared = {e["key"] for e in tree.get("entities", [])}
        used = set()
        for s in strings_in(nodes):
            used.update(PLACEHOLDER.findall(s))
        for key in sorted(used - declared):
            errors.append(f"{where}: placeholder '{{{{{key}}}}}' is not declared in entities")
        for key in sorted(declared - used):
            warnings.append(f"{where}: entity '{key}' is declared but never used")

    # Cycle detection across the whole forest (links become edges).
    def successors(tid: str, nid: str) -> list[tuple[str, str]]:
        node = trees[tid]["nodes"].get(nid)
        if node is None:
            return []
        if node["type"] == "link":
            t = trees.get(node["tree"])
            if t is None:
                return []
            return [(node["tree"], node.get("node", t["start"]))]
        return [(tid, target) for _, target in edges(node)]

    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[tuple[str, str], int] = {}

    def visit(start: tuple[str, str]) -> None:
        stack = [(start, iter(successors(*start)))]
        colour[start] = GREY
        path = [start]
        while stack:
            current, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                colour[current] = BLACK
                stack.pop()
                path.pop()
                continue
            state = colour.get(nxt, WHITE)
            if state == GREY:
                cyc = path[path.index(nxt):] + [nxt]
                errors.append("cycle: " + " -> ".join(f"{t}:{n}" for t, n in cyc))
            elif state == WHITE:
                colour[nxt] = GREY
                path.append(nxt)
                stack.append((nxt, iter(successors(*nxt))))

    for tid, tree in trees.items():
        for nid in tree["nodes"]:
            if colour.get((tid, nid), WHITE) == WHITE:
                visit((tid, nid))

    return errors, warnings


DETECTION_SCHEMA_PATH = ROOT / "schema" / "detection.schema.json"


def load_detections(trees: dict[str, dict], det_dir: Path = ROOT / "detections") -> tuple[dict[str, dict], list[str]]:
    """Detection rules copied from the KQL-Query repo: schema, file name, and playbook links."""
    validator = Draft202012Validator(json.loads(DETECTION_SCHEMA_PATH.read_text()))
    dets: dict[str, dict] = {}
    errors: list[str] = []
    for path in sorted(det_dir.glob("*.y*ml")) if det_dir.exists() else []:
        try:
            data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        except yaml.YAMLError as e:
            errors.append(f"{path.name}: YAML error: {e}")
            continue
        problems = [f"{path.name}: {'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in validator.iter_errors(data)]
        if problems:
            errors.extend(problems)
            continue
        if data["id"] != path.stem:
            errors.append(f"{path.name}: id '{data['id']}' does not match the file name")
        for pb in data["playbooks"]:
            if pb not in trees:
                errors.append(f"{path.name}: playbook '{pb}' does not exist in trees/")
        dets[data["id"]] = data
    return dets, errors


OSINT_SCHEMA_PATH = ROOT / "schema" / "osint.schema.json"
OSINT_PATH = ROOT / "osint" / "tools.yaml"
OSINT_STALE_DAYS = 180


def load_osint(trees: dict[str, dict], path: Path = OSINT_PATH, today: date | None = None) -> tuple[list[dict], list[str], list[str]]:
    """OSINT tools: schema, unique ids, real playbooks, sane templates. Warn when a check is over 180 days old."""
    if not path.exists():
        return [], [], []
    name = path.name
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except yaml.YAMLError as e:
        return [], [f"{name}: YAML error: {e}"], []
    # YAML turns unquoted dates into date objects; the schema wants strings.
    for t in (data or {}).get("tools", []) if isinstance(data, dict) else []:
        v = t.get("verified") if isinstance(t, dict) else None
        if isinstance(v, dict) and "date" in v and not isinstance(v["date"], str):
            v["date"] = str(v["date"])
    validator = Draft202012Validator(json.loads(OSINT_SCHEMA_PATH.read_text()))
    problems = [f"{name}: {'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in validator.iter_errors(data)]
    if problems:
        return [], problems, []

    errors: list[str] = []
    warnings: list[str] = []
    today = today or date.today()
    seen: set[str] = set()
    for t in data["tools"]:
        where = f"{name}: {t['id']}"
        if t["id"] in seen:
            errors.append(f"{where}: duplicate tool id")
        seen.add(t["id"])
        for pb in t["playbooks"]:
            if pb not in trees:
                errors.append(f"{where}: playbook '{pb}' does not exist in trees/")
        for kind, tpl in t.get("lookups", {}).items():
            if "{hashtype}" in tpl and kind != "hash":
                errors.append(f"{where}: {{hashtype}} only works in a hash lookup, not {kind}")
            if "{urlsha256}" in tpl and kind != "url":
                errors.append(f"{where}: {{urlsha256}} only works in a url lookup, not {kind}")
            leftover = set(re.findall(r"\{([a-z0-9]+)\}", tpl)) - {"value", "hashtype", "urlsha256"}
            if leftover:
                errors.append(f"{where}: unknown placeholder {sorted(leftover)} in {kind} lookup")
        try:
            checked = date.fromisoformat(t["verified"]["date"])
        except ValueError:
            errors.append(f"{where}: verified.date '{t['verified']['date']}' is not a real date")
            continue
        if checked > today:
            errors.append(f"{where}: verified.date {checked} is in the future")
        elif (today - checked).days > OSINT_STALE_DAYS:
            warnings.append(f"{where}: last verified {checked}, over {OSINT_STALE_DAYS} days ago. Re-check the link and lookups.")
    return data["tools"], errors, warnings


def validate(trees_dir: Path = ROOT / "trees") -> tuple[dict[str, dict], list[str], list[str]]:
    trees, errors = load_trees(trees_dir)
    graph_errors, warnings = check_graphs(trees)
    return trees, errors + graph_errors, warnings


def main() -> int:
    trees_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "trees"
    trees, errors, warnings = validate(trees_dir)
    dets, det_errors = load_detections(trees) if len(sys.argv) == 1 else ({}, [])
    osint, osint_errors, osint_warnings = load_osint(trees) if len(sys.argv) == 1 else ([], [], [])
    errors += det_errors + osint_errors
    warnings += osint_warnings
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    total_nodes = sum(len(t["nodes"]) for t in trees.values())
    status = "FAILED" if errors else "OK"
    print(f"{status}: {len(trees)} trees, {total_nodes} nodes, {len(dets)} detection rules, {len(osint)} OSINT tools, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
