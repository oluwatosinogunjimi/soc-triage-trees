# Triage Trees

Question-driven investigation playbooks for SOC analysts, plus the custom detection rules behind some of the alerts and a verified set of OSINT tools for outside checks. Pick the alert type, answer yes/no questions backed by ready-to-run KQL, reach a verdict with recommended actions, and export a closure note written from the path you took.

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
- **Wider checks at each step.** Beyond the questions that route you, most steps carry an "Also check" list of yes/no questions: persistence, privilege changes, lateral movement and data leaving, for the same user, host or IP. A yes is flagged, carried into the note and warned about before a benign verdict.
- **An "unknown" path.** Real triage often stalls on "can't tell yet". Where that matters, the tree says what to do about it.
- **Interactive map.** Every playbook opens as a decision tree you expand one branch at a time, with your path highlighted and the full detail of any step on click.
- **At a glance.** Each playbook shows its stages in order, the alternatives at each, and every way it can end, before you start.
- **Outcomes with a verdict.** Each outcome is a false positive, benign true positive, true positive or inconclusive result, with a risk statement, recommended actions, a monitoring line and tuning advice.
- **Closure note export.** Your path, the evidence you typed at each step and the outcome become a draft note you can paste into the ticket.

## Detection rules

The Detections page shows custom Defender XDR detection rules from the [KQL detection library](https://github.com/oluwatosinogunjimi/KQL-Query). Each rule shows its query, what it catches, its blind spots and false positives, how it was tested, and the playbook to walk when it fires. Playbooks link back to the rules that lead to them.

| Rule | Tactic | Playbook |
|---|---|---|
| PowerShell DownloadString Remote Execution | Execution | Suspicious PowerShell or LOLBin Execution |
| Suspicious Office Child Process | Execution | Office Application Spawned a Suspicious Process |
| User Account Creation via Command Line | Persistence | Local Account Created or Added to Administrators |
| Local Administrators Group Modification via Command Line | Privilege Escalation | Local Account Created or Added to Administrators |
| Svchost Execution from Unusual Location | Defense Evasion | Malware or EDR Detection |

The rules are copied into `detections/` as YAML, so the site never depends on the KQL repo. To refresh them after a rule changes there, run `python tools/import_detections.py ../KQL-Query`, or edit the YAML by hand. Either way, `python tools/validate.py` checks every rule and that its playbook exists.

## OSINT tools

The OSINT page lists 40 tools for the checks your own logs can't answer: IP and domain reputation, infrastructure and domain age, sandboxes, email headers, CVE severity, and references such as LOLBAS, LOLDrivers and LOLRMM. Each tool says when to use it, what can mislead you, whether it is free, and what it does with what you give it:

- **Stays local**: runs in your browser or is a static reference.
- **Sends indicator**: the vendor sees and may log what you look up.
- **Public by default**: creates a scan or analysis others can see. Never submit client files or internal URLs.

Paste an IP, domain, URL, hash, email or CVE (defanged is fine) and the page builds one-click lookups for the tools that support it. Private addresses and internal names are refused. The indicator is never saved or put in the page URL. In a case, entity values that are public indicators get an **OSINT** link that opens the lookups in a new tab, so the case stays where you left it. The browser's Back button moves between pages.

Tools live in `osint/tools.yaml`. Every entry records when its links were last checked and how; the validator warns once a check is more than 180 days old.

## Using it

Open the published site, or build it locally:

```bash
pip install -r requirements.txt
python tools/build.py          # validates, then writes dist/
python -m http.server -d dist  # open http://localhost:8000
```

`dist/index.html` is self-contained with the trees embedded, so you can also open it straight from disk. Link to a tree directly with `#tree-id`, for example `#phishing-email`, and to a detection rule with `#detections/rule-id`, and to the OSINT tools with `#osint`. Press `Ctrl K` (`⌘K` on Mac) anywhere to jump to a playbook.

The site has a light mode (a field-guide look on paper) and a dark mode (a console look for long shifts). It follows your device setting until you use the sun/moon switch, then remembers your choice.

Case state (your path, evidence and entity values) stays in your own browser's local storage. Nothing is sent anywhere. Don't paste data into the tool that your client's handling rules forbid storing on your workstation.

## Repository layout

```
trees/                 one YAML file per playbook (this is the content)
detections/            one YAML file per detection rule, copied from the KQL library
osint/tools.yaml       the OSINT tools, edited by hand
schema/tree.schema.json  the contract every tree must meet
schema/detection.schema.json  the contract every detection rule must meet
schema/osint.schema.json  the contract every OSINT tool must meet
tools/validate.py      schema plus graph checks (orphans, broken edges, cycles, placeholders)
tools/build.py         validate, then bundle into dist/
tools/new_tree.py      scaffold a new tree that already validates
tools/gen_router.py    regenerate the Universal Triage menus and docs/CATALOGUE.md
tools/import_detections.py  copy rules from the KQL library into detections/ (optional)
site/viewer.html       the viewer (walkthrough, map, closure note)
tests/                 pytest suite for the validator and build
```

## Contributing

Adding or improving a tree means editing one YAML file. See [CONTRIBUTING.md](CONTRIBUTING.md) for the node types, writing guidance and review checklist. CI validates every pull request and publishes the site when `main` changes.

## Disclaimer

These trees are guidance, not a substitute for your client's runbooks, RACI or legal and regulatory obligations. KQL is written against the public Microsoft Sentinel and Defender XDR schemas; table availability depends on the connectors and licences in each environment, so test queries before relying on them.

## Author

Built by Oluwatosin Ogunjimi, SOC analyst and cybersecurity writer.

- LinkedIn: [oluwatosin-ogunjimi](https://www.linkedin.com/in/oluwatosin-ogunjimi/)
- Medium: [@OluwatosinOgunjimi](https://medium.com/@OluwatosinOgunjimi)

## Licence

MIT. See [LICENSE](LICENSE).
