# Philosophy, research and design

Why Triage Trees exists, what it believes about triage, what research says about how analysts work, and how that shaped the data, the workflow and the look. It reflects research done in October 2026. Read it before changing the data model or the viewer.

## Why it exists

Alert triage is repetitive, high-volume work done under time pressure. The same alert types arrive every shift, yet two analysts can walk the same alert differently, miss different checks and write very different closure notes. New analysts learn mostly by shadowing, and the reasoning behind each check lives in people's heads.

The project began as the article [Lessons from the SOC](https://medium.com/@OluwatosinOgunjimi/lessons-from-the-soc-04d395c195c7), a bank of questions analysts should ask per alert type. Triage Trees turns that bank into structured, versioned decision trees anyone can use, check and improve.

## Philosophy

1. **A decision aid, not a procedure.** A tree suggests the next question and explains it. It does not force a path or a verdict. Rigid procedures that analysts cannot question make them worse at novel cases, not better.
2. **The analyst owns the verdict.** The tool gathers and organises. It never decides and never acts. Containment and remediation stay as recommendations that name who must approve them.
3. **Every check earns its place.** A question that cannot say why it matters gets skipped in a busy queue. Each question carries its reason, which is also how the tool teaches.
4. **Teach while doing.** The same tree serves a new analyst learning the alert and an experienced one moving fast. The reasoning is there for those who need it and out of the way for those who don't.
5. **Doubt is a valid answer.** "Can't tell yet" and "Inconclusive" are first-class. A forced guess is worse than an honest gap.
6. **Simple beats powerful.** A static page that opens from disk, not a platform. If it needs an account, a server or an integration, it is the wrong tool for this job.
7. **Free, vendor-neutral and private.** No sign-up, no tracking, no data leaves the browser. Content is generic so it works for any SOC, and the public repo holds no client or environment details.
8. **Open and versioned.** Trees are plain YAML in git, validated in CI. Every change is a reviewable diff, and every closure note records which version of the tree was followed.

## Who it is for

- **Analysts in a live queue**, who need the next question, the query that answers it and a closure note, without leaving their console for long.
- **New analysts and trainers**, for onboarding: the trees show what to check, in what order and why.
- **Team leads and reviewers**, who want consistent investigations and notes they can audit against a known version of the playbook.

## What the research says, and what we did with it

There are no controlled studies of decision-tree tools for SOC triage. The findings below come from SOC field research, adjacent safety-critical fields (aviation, medicine) and usability research. Each one drove a specific choice.

| Finding | Source | What we did |
|---|---|---|
| Analyst burnout is widespread. In one vendor survey of 900 analysts, 63% reported burnout and manual work was the top frustration. | Tines, Voice of the SOC 2023 (vendor survey) | Cut typing and repetition: entities are entered once and filled into every query and the note. Notes are assembled, not written from scratch. |
| Burnout runs in a cycle of low skill growth, low empowerment and low creativity. Analysts held to procedures they cannot question fall back on them and handle novel cases poorly. | Sundaramurthy et al., fieldwork 2015–2017 | Trees suggest, never enforce. Analysts can answer "Unsure", change earlier answers and record why their verdict differs from the tree's. |
| Most "false positives" are really benign triggers: the rule fired correctly on legitimate activity. Analysts need alarms that are explainable and in context. | Alahmadi et al., USENIX Security 2022 | Benign true positive is its own verdict, separate from false positive. Each tree reproduces the alert and explains every check. |
| Checklists work when they are short, used at natural pause points and suited to the user: "do-confirm" for experts, "read-do" for novices. A surgical checklist cut deaths from 1.5% to 0.8%. | Gawande, *The Checklist Manifesto*; Haynes et al. 2009 | Steps are one question at a time, grouped into short runs, with "also check" items at natural pauses. A guided mode for trainees and a faster mode for experts are planned. |
| Good abnormal-situation checklists start with a condition statement that reproduces the alert, highlight the current item and use generous white space and mixed-case sans-serif type. | Burian, NASA Ames checklist design guidance | The alert that opened the tree appears at the top of each step. Only the current question is framed. Type is a legibility-focused sans-serif. |
| Clinicians override 46 to 96% of decision-support alerts, mostly because they interrupt, lack explanation or don't fit the case. | Poly et al., JMIR 2020 review | No pop-ups or blocking prompts. Hints sit inline. Every prompt explains itself, and warnings are reserved for things that change the outcome. |
| Wizards suit novices and rare tasks but frustrate frequent users. Progressive disclosure beyond two levels gets people lost. | Nielsen Norman Group | Experts can jump to any step, see the whole tree on a map and use the keyboard. Detail is at most one click deep. |
| People shown a confident suggestion stop checking it. In a vendor-run trial, analysts who saw an assistant's verdicts missed 46% of its wrong "benign" calls, against 17% for those who didn't. | Microsoft phishing triage trial, 2025 (vendor-authored) | The tool never pre-weights an answer or highlights a "likely" verdict. Benign endings ask for the clearest evidence. |
| Investigations are wrongly closed more often when a query returns nothing, because "no rows" gets read as "nothing happened". | Alert-Bench benchmark, 2026 (abstract only) | Questions can state what an empty result means, usually a data gap to resolve, not a clean result. |
| Unaided analysts' written findings lose detail under load. | CSA benchmark, 2025 (vendor-involved) | The closure note is built from the path, the evidence typed at each step and the ending's verdict, risk and actions. |
| Asking people to re-enter information they already gave causes errors and fatigue. | WCAG 2.2, success criterion 3.3.7 | Case entities are typed once and reused everywhere. |

## Functionality choices

- **Verdicts:** true positive, benign true positive, false positive and inconclusive, mapping onto the Microsoft Sentinel and Defender XDR closing classifications.
- **"Also check" questions** at each step cover the wider picture (persistence, privilege changes, lateral movement, data leaving). A yes is carried into the note and warned about before a benign verdict.
- **Typed actions.** An ending's actions can be typed `enrich`, `contain`, `remediate` or `notify`. Containment and remediation name who approves them and whether they can be undone, and actions that could alert the attacker are flagged.
- **Empty results.** A question can say what "no rows" means (`on_empty`).
- **Lifecycle.** Trees carry a version, review dates and a status (draft, stable, deprecated). Deprecated trees point to their replacement instead of disappearing.
- **Privacy.** Case data stays in the browser's local storage on the analyst's machine and can be cleared. Entity values never go into the URL. The OSINT page labels every tool by what it does with your data.

## UX choices

- **Route, step, case file.** Three columns: the path taken, the current question, and what will be handed over (entities, possible endings, the draft note). It narrows to fit beside a SIEM console.
- **The trace.** One continuous line from the alert to the verdict. Answered steps show the answer; untaken branches leave a short stub showing what they lead to.
- **Endings narrow as you go.** Endings that can no longer be reached are struck through, so the analyst sees the decision space shrinking.
- **Changing your mind is safe.** Revisiting an earlier step flags later answers for review instead of wiping them.
- **Speed.** `Ctrl K` / `⌘K` search across titles and alert names, single-key answers, copy buttons on every query.
- **Plain language.** Second person, short sentences, no marketing copy.

## Visual design: "Three inks" on a quick-reference card

**What we avoid.** AI-generated interfaces converge on recognisable defaults. The first wave is purple or indigo gradients, Inter everywhere, uniform rounded cards with soft shadows, emoji icons and pill badges. The second, "tasteful" wave is now a default too: cream paper with a serif headline and an italic accent word, near-black with one acid accent, and uppercase tracked labels above every heading. The earlier version of this site sat in the second wave. The fix is not another trend. It is grounding each choice in the domain: the printed quick-reference handbook used in aviation and incident response.

**What we use.**

- **Colour has jobs.** Ink for what the guide says. Pen blue for what the analyst did: answers, the trace, typed evidence, focus. Violet for the card system: the current domain, card headers, links. Stamp colours for verdicts only.
- **Verdicts are shapes first.** True positive ▲, inconclusive ◆, benign true positive ●, false positive ■, always with a text label, so they read in greyscale and for colour-blind users.
- **Type.** Atkinson Hyperlegible Next for text and Atkinson Hyperlegible Mono for queries, IDs and indicators (slashed zero, distinct 1, l and I). Both are SIL Open Font License 1.1 and embedded, so the site looks the same offline.
- **Card motif.** Each tree is a ring-bound reference card: header strip, punch holes, crop marks, dotted leaders between check and answer, and a rubber-stamp verdict.
- **Signature.** The home-page tree, with the trace drawing itself from the alert to an ending. Motion is limited to the trace, the stamp and small state changes, and all of it stops under reduced-motion settings.
- **Themes.** Day (paper) and Night (graphite), switched with the sun/moon button. Night is its own palette, not an inversion.
- **Collections are tables.** Playbooks, OSINT tools and detections are listed in index tables, not grids of identical cards.

| Token | Day | Night |
|---|---|---|
| paper / card | `#f5f4f1` / `#fdfcfb` | `#111316` / `#191c20` |
| ink / ink-2 / muted | `#181c21` / `#41454c` / `#5f646a` | `#eaeae5` / `#c1c4c9` / `#9a9fa5` |
| control border | `#7c8186` | `#646970` |
| pen / violet | `#1a57a1` / `#5b45a0` | `#83c1fb` / `#b5a3f2` |
| TP text / fill | `#b12822` / `#a91515` | `#f87f73` / `#d9544b` |
| INC text / fill | `#8d5416` / `#c27919` | `#edb65c` / `#f2af48` |
| BTP text / fill | `#227240` / `#3f9557` | `#75d291` / `#6ed889` |
| FP text / fill | `#5f646a` / `#7c8186` | `#a6abb2` / `#6d7279` |

Text meets WCAG 2.2 AA (4.5:1) on its surface; control borders and fills meet 3:1. Exact colours may still be tuned.

## Rules for future edits

Keep these when changing the viewer, by hand or with an AI assistant.

1. Colours come only from the token block.
2. Pen marks analyst actions and focus only. Violet marks the card system only.
3. A verdict colour always appears with its shape and its label.
4. Text stays at 4.5:1 or better; borders and fills at 3:1.
5. Fonts are the two embedded Atkinson families. No external requests of any kind.
6. Uppercase only for the verdict stamp and keycaps.
7. One radius (4px). No pills, gradients, glows, glass or coloured side borders on cards.
8. Collections are lists or tables. Number only real sequences.
9. One framed current item and one primary action per view.
10. Motion only for the trace, the stamp and small state changes, all off under reduced motion.
11. Answer buttons are visually equal. The tool never pre-weights an answer.
12. Before merging UI work, check Day and Night, run the accessibility checks, and ask a fresh reviewer which AI tool made it. The right answer is "none".

## Limits, and what we'd like to learn

The evidence is uneven. The SOC findings are mostly fieldwork and surveys, several sources are vendor-run, and the checklist and decision-support findings are borrowed from other fields. The visual direction is design judgement checked against accessibility standards.

What would tell us the trees work, if teams choose to measure it on their side: time from alert to verdict, how often two analysts reach the same verdict on the same case, how often benign closures are later reopened, and which branches are never used. The tool collects none of this itself. Feedback on a specific step is welcome as a GitHub issue naming the tree, the step and what went wrong, with no case data.

## Key sources

- Sundaramurthy et al., [Human-centred SOC fieldwork](https://cse.usf.edu/~xou/publications/sundaramurthyIEEEIC17.pdf), IEEE Internet Computing 2017
- Alahmadi et al., [99% False Positives](https://www.usenix.org/conference/usenixsecurity22/presentation/alahmadi), USENIX Security 2022
- Tines, [Voice of the SOC 2023](https://www.tines.com/reports/voice-of-the-soc-2023/) (vendor survey)
- Burian, [Design guidance for emergency and abnormal checklists](https://hsi.arc.nasa.gov/flightcognition/Publications/EA_Checklist_Design.pdf), NASA Ames
- Poly et al., [Alert override in clinical decision support](https://medinform.jmir.org/2020/7/e15653), JMIR 2020
- Nielsen Norman Group on [wizards](https://www.nngroup.com/articles/wizards/) and [progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
- [Phishing triage agent trial](https://arxiv.org/abs/2511.13860), 2025 (vendor-authored)
- [Alert-Bench](https://neurips.cc/virtual/2026/168137), NeurIPS 2026 workshop
- [Microsoft Sentinel incident classification](https://learn.microsoft.com/en-us/azure/sentinel/incident-navigate-triage)
- Anthropic, [Improving frontend design through skills](https://claude.com/blog/improving-frontend-design-through-skills); Krebs, [Design slop](https://adriankrebs.ch/blog/design-slop/)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) and the [SIL Open Font License FAQ](https://openfontlicense.org/ofl-faq/)

## Status of the redesign

- [x] Philosophy, research and design notes
- [x] Data model: review status, typed actions, empty-result rule, public-safety lint
- [x] Viewer re-skin: tokens, embedded fonts, verdict shapes, card motif, trace, home illustration
- [x] Viewer functionality: typed actions, empty-result hints, alert condition box, version stamp in notes
- [ ] Adopt typed actions and `on_empty` across the other trees (one tree done: impossible travel)
- [ ] Guided and expert modes, and index tables for the OSINT and Detections pages
- [x] CI: contrast test, offline test, design lint (in the pytest suite)
