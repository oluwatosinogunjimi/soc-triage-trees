# Contributing a tree

A tree is one YAML file in `trees/`. The file name is the tree id. You never need to touch the viewer code to add or change content.

```bash
python tools/new_tree.py mfa-fatigue "MFA Fatigue / Push Bombing" identity
# edit trees/mfa-fatigue.yaml
python tools/validate.py
python tools/gen_router.py   # adds it to the Universal Triage menus and the catalogue
python tools/build.py && python -m http.server -d dist
```

## Node types

| Type | Purpose | Required fields |
|---|---|---|
| `check` | Gather context. No branching. | `text`, `note`, `next` |
| `question` | A yes/no decision, optionally with a "can't tell yet" edge. | `text`, `yes`, `no`, `notes.yes`, `notes.no` (+ `unknown`, `notes.unknown`) |
| `choice` | Route between more than two paths (for example, alert direction). | `text`, `options[].label`, `options[].next` |
| `outcome` | A verdict. Every path ends at one. | `verdict`, `title`, `anchor`, `risk`, `actions` |
| `link` | Continue in another tree, optionally at a given node. | `text`, `tree` (+ `node`) |

Optional on `check`, `question` and `choice`: `why` (one short paragraph), `look_for` (checks only, a list), `kql` (a list of `{title, platform, query}` where platform is `sentinel`, `xdr` or `both`).

`also_check` (optional on `check`, `question` and `choice`) is a list of wider yes/no questions to rule out at that step, where yes always means "suspicious". They don't change the route. The analyst answers each one, and the answers go into the closure note. A yes before a benign verdict gets a warning. Use them for related activity the tree doesn't branch on: persistence, privilege changes, lateral movement, collection and exfiltration for the same entities. Each question may appear only once per tree.

Optional on `outcome`: `monitor`, `escalate: true`, `tuning`.

Node ids use a prefix for their type: `c-` check, `q-` question, `ch-` choice, `o-` outcome, `l-` link.

## Entities and placeholders

Declare the values an analyst fills in once under `entities`, then use them anywhere as `{{key}}`: in text, notes, outcomes and queries. The validator rejects any placeholder that is not declared. Keep keys consistent across trees (`user`, `ip`, `device`, `sha256`) so values carry over when a path links between trees.

## Writing guidance

**Questions**
- Ask one thing, answerable from evidence. "Did the sign-in succeed?" rather than "Is this suspicious?"
- Put the discriminating question early. If a baseline check settles most alerts, ask it first.
- Add an `unknown` edge only when "can't tell" is common and has a sensible next step.
- Use `why` to say what the answer tells you, especially where a common assumption is wrong ("MFA passed" does not rule out AiTM).

**Notes** become the findings in the closure note, one per step.
- First person, past tense, carrying placeholders: "I found no session reuse across IPs for {{user}}."
- State the finding, not the question. The analyst's typed evidence is appended after it.

**Outcomes**
- `anchor` follows the verdict sentence ("This alert closes as a false positive.") and ties the verdict to the evidence. Don't repeat the verdict word inside it.
- `risk` names the threat vector and says why it does or doesn't apply here: "The risk here is X; it doesn't apply because Y." A line that would fit any case unchanged is too generic.
- `actions` are specific and ordered by priority.
- Add `monitor` for true positives, inconclusive results, privileged accounts and anything with residual doubt.
- Add `tuning` to false and benign outcomes when a scoped exclusion or logic fix would stop the noise.

**Also check**
- One question each, ending in "?", phrased so that yes means bad.
- Put it on the step whose subject it matches, and prefer steps that most paths pass through.
- Don't repeat what the tree already asks or lists in `look_for`.
- Use the tree's entity placeholders ("Has {{user}} ...") and quote each item in double quotes in YAML.

**KQL**
- Put the query on the question it answers, not in a big block at the start.
- Filter on entities with `{{key}}` and keep lookbacks explicit (`ago(7d)`).
- Mark the platform correctly: Sentinel tables use `TimeGenerated`, Defender XDR advanced hunting uses `Timestamp`.
- Test against a real workspace before opening the PR, and note any connector the query depends on.

**Style**
- Plain, direct language. No em dashes.
- Cite where the checks come from in `sources`, with https links.
- Bump `version` (semver) and `last_reviewed` whenever you change a tree.

## Detection rules

Detection rules live in `detections/`, one YAML file per rule, and show on the Detections page. They are written and tested in the [KQL detection library](https://github.com/oluwatosinogunjimi/KQL-Query) first, then copied here:

```bash
python tools/import_detections.py ../KQL-Query   # copies every rule; a rule it can't read is skipped, never half-written
python tools/validate.py                         # checks each rule against schema/detection.schema.json
```

You can also add or edit a file in `detections/` by hand. The site reads only these files. `playbooks` lists the playbook ids to walk when the rule fires; the validator fails if one doesn't exist, so renaming a playbook means updating the rules that point at it.

## Review checklist

- [ ] `python tools/validate.py` passes with no warnings
- [ ] `python tools/gen_router.py` has been run (CI fails if the router or catalogue is stale)
- [ ] Every path reaches an outcome that a senior analyst would agree with
- [ ] Queries were run against a real workspace
- [ ] No client names, real IPs, real users or internal hostnames anywhere (use the examples format)
- [ ] `version` and `last_reviewed` updated

## OSINT tools

Tools live in `osint/tools.yaml`. The comment at the top of the file describes every field. Before adding or changing a tool:

- Open the site yourself and confirm it still does what `what` says.
- Add a lookup template only after you have opened it with a real indicator and seen the right result. If the site blocks the check or needs a date or login, leave `lookups` out and say so in `verified.how`.
- Set `opsec` honestly. If a free tier makes submissions public, it is `submits`.
- Put the date and method in `verified`. The validator warns when a check is over 180 days old, so re-check the link and bump the date rather than ignoring the warning.
- `playbooks` must be real tree ids. Run `python tools/validate.py`.

