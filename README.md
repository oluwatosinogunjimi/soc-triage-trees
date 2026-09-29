# Triage Trees

Question-driven investigation playbooks for SOC analysts. Pick the alert type, answer yes/no questions backed by ready-to-run KQL, reach a verdict with recommended actions, and export a closure note written from the path you took.

This project grew out of the article [Lessons from the SOC: How Analysts Can Triage Smarter, Tune Better, and Stop Drowning in Alerts](https://medium.com/@OluwatosinOgunjimi/lessons-from-the-soc-04d395c195c7). The article's question bank is now structured data, checked against vendor incident response playbooks and MITRE ATT&CK.

## What's inside

100 playbooks. See the full list with alert names and ATT&CK mappings in [docs/CATALOGUE.md](docs/CATALOGUE.md).

| Category | Playbooks | Examples |
|---|---|---|
| Start here | 1 | Universal Triage Flow, which routes to every other playbook |
| Email and collaboration | 15 | Phishing, BEC and vendor fraud, QR code phishing, HTML smuggling, callback phishing, Teams fake helpdesk, mail flow rules |
| Identity | 29 | Impossible travel, AiTM, MFA fatigue, device code phishing, OAuth consent, privileged role changes, Kerberoasting, DCSync, golden ticket, AD CS abuse |
| Endpoint | 24 | EDR malware, ransomware, LSASS dumping, Cobalt Strike, BYOVD, RMM tools, persistence (tasks, services, Run keys, WMI), web shells, Linux reverse shells |
| Network, perimeter and OT | 13 | IDS alerts, DNS tunnelling, VPN anomalies, inbound brute force, edge device exploitation, exfiltration volume, OT/ICS commands |
| Cloud and SaaS | 18 | AWS root use, stolen keys, logging disabled, public buckets, Key Vault harvesting, Kubernetes, SharePoint mass download, DLP, exposed secrets, LLMjacking |

The checks draw on the Microsoft incident response playbooks, Entra ID Protection and Defender for Identity detection references, Defender for Cloud Apps policies, AWS GuardDuty finding types, CISA advisories and MITRE ATT&CK, with sources listed in each tree.

Every tree has:

- **Questions with a reason.** Each question can explain why it matters, so the tool also teaches new analysts.
- **KQL at the point of use.** Queries for Microsoft Sentinel and Defender XDR sit on the question they answer. Case entities (user, IP, hash) fill into the queries.
- **An "unknown" path.** Real triage often stalls on "can't tell yet". Where that matters, the tree says what to do about it.
- **Interactive map.** Every playbook opens as a decision tree you expand one branch at a time, with your path highlighted and the full detail of any step on click.
- **At a glance.** Each playbook shows its stages in order, the alternatives at each, and every way it can end, before you start.
- **Outcomes with a verdict.** Each outcome is a false positive, benign true positive, true positive or inconclusive result, with a risk statement, recommended actions, a monitoring line and tuning advice.
- **Closure note export.** Your path, the evidence you typed at each step and the outcome become a draft note you can paste into the ticket.

## Using it

Open the published site, or build it locally:

```bash
pip install -r requirements.txt
python tools/build.py          # validates, then writes dist/
python -m http.server -d dist  # open http://localhost:8000
```

`dist/index.html` is self-contained with the trees embedded, so you can also open it straight from disk. Link to a tree directly with `#tree-id`, for example `#phishing-email`.

Case state (your path, evidence and entity values) stays in your own browser's local storage. Nothing is sent anywhere. Don't paste data into the tool that your client's handling rules forbid storing on your workstation.

## Repository layout

```
trees/                 one YAML file per playbook (this is the content)
schema/tree.schema.json  the contract every tree must meet
tools/validate.py      schema plus graph checks (orphans, broken edges, cycles, placeholders)
tools/build.py         validate, then bundle into dist/
tools/new_tree.py      scaffold a new tree that already validates
tools/gen_router.py    regenerate the Universal Triage menus and docs/CATALOGUE.md
site/viewer.html       the viewer (walkthrough, map, closure note)
tests/                 pytest suite for the validator and build
```

## Contributing

Adding or improving a tree means editing one YAML file. See [CONTRIBUTING.md](CONTRIBUTING.md) for the node types, writing guidance and review checklist. CI validates every pull request and publishes the site when `main` changes.

## Disclaimer

These trees are guidance, not a substitute for your client's runbooks, RACI or legal and regulatory obligations. KQL is written against the public Microsoft Sentinel and Defender XDR schemas; table availability depends on the connectors and licences in each environment, so test queries before relying on them.

## Licence

MIT. See [LICENSE](LICENSE).
