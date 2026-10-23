# Design notes

Why Triage Trees works and looks the way it does. This summarises research done in October 2026 and the choices that came out of it. Read it before changing the data model or the viewer.

## What the tool is

A decision aid, not a procedure. Each tree turns one alert into a short run of questions, each with the reason it matters and the query that answers it. It ends in a verdict and a closure note written from the path taken. The analyst always owns the verdict. The tool suggests, explains and records. It never decides or acts.

## Principles

| Principle | What it means here |
|---|---|
| Say why | Every tree has a summary and every question can carry a `why`. Unexplained prompts get ignored: clinical decision support sees 46 to 96% of alerts overridden. |
| One owner per decision | The analyst picks every answer and the verdict. Queries, OSINT lookups and "also check" items only gather evidence. |
| Investigate, then decide | Checking happens on each step; the verdict sits at the end. Changing an earlier answer flags later steps instead of silently wiping them. |
| Verify independently | CI validates every tree (schema, graph, references, public-safety lint). Each tree carries its version and review date, and the note records which version was followed. |
| Gate by stakes | Enrichment is free. Containment and remediation are recommendations that name who must approve them. Nothing runs from the tool. |
| Remember | Trees are versioned YAML in git. Changes are reviewable diffs, and deprecated content is marked, not deleted. |
| Make doubt easy | Questions can offer "Unsure / can't tell". Inconclusive is a valid ending, not a forced guess. |

## Functionality choices

- **Verdicts:** true positive, benign true positive, false positive and inconclusive. These map onto Microsoft Sentinel and Defender XDR closing classifications. Most "false positives" in SOC research are really benign triggers, so benign true positive is first-class.
- **Benign closures get the most care.** In a vendor-run trial, analysts shown an assistant's verdicts missed 46% of its wrong "benign" calls, against 17% without them. Benign endings should need the clearest evidence.
- **No rows is a data gap, not a clean result.** A query that returns nothing can mean missing logs. A question can say what an empty result means (`on_empty`).
- **Typed actions.** An ending's actions can be typed `enrich`, `contain`, `remediate` or `notify`. Containment and remediation say who approves them and whether they can be undone. Actions that could alert the attacker are flagged.
- **Closure notes are assembled, not typed.** The note is built from the answers, the evidence typed at each step and the ending, and stamped with the tree ID and version.
- **Privacy.** Everything runs in the browser. Case data stays in local storage on the analyst's machine and can be cleared. Entity values never go into the URL.

## UX choices

- **Route, step, case file.** Three columns: the path taken (the trace), the current question, and what will be handed over (entities, possible endings, the note draft).
- **The trace.** One continuous line from the alert to the verdict. Answered steps show the answer in pen colour; untaken branches leave a short stub.
- **One current item.** Only the active question is framed. The alert that opened the tree is reproduced at the top so the analyst can confirm they're on the right card, a technique from aviation checklists.
- **Speed.** `Ctrl K` / `⌘K` search across titles and alert names, single-key answers, copy buttons on every query, entities typed once and filled everywhere.
- **Plain language.** Second person, short sentences, no marketing copy.

## Visual design: "Three inks" on a quick-reference card

### What we avoid

AI-generated interfaces converge on recognisable defaults. The first wave is purple or indigo gradients, Inter everywhere, uniform rounded cards with soft shadows, emoji icons, glassmorphism and pill badges. The second, "tasteful" wave is now a default too: cream paper with a serif display headline and an italic accent word, near-black with a single acid accent, and uppercase tracked labels above every heading. The earlier version of this site sat in the second wave, so this redesign moves away from it.

The fix is not a different trend. It is grounding every visual choice in the domain: the printed quick-reference handbook used in aviation and incident response.

### What we use

- **Colour has jobs.** Ink for what the guide says. Pen blue for what the analyst did: answers, the trace, typed evidence, filled entities, focus. Violet for the card system: the current domain, card headers, links and the alert root. Stamp colours for verdicts only.
- **Verdicts are shapes first.** True positive ▲, inconclusive ◆, benign true positive ●, false positive ■, always with a text label, so they read in greyscale and for colour-blind users.
- **Type:** Atkinson Hyperlegible Next for text and Atkinson Hyperlegible Mono for queries, IDs and indicators (slashed zero, distinct 1/l/I). Both are SIL Open Font License 1.1 and embedded in the build, so the site looks the same offline. No italics, no all-caps except the verdict stamp.
- **Card motif:** each tree is drawn as a ring-bound reference card with a header strip, punch holes, crop marks, dotted leaders between check and answer, and a rubber-stamp verdict.
- **Signature element:** the tree illustration on the home page, with the trace drawing itself from the alert to an ending. Motion is limited to the trace, the stamp landing and small state changes, and all of it stops under reduced-motion settings.
- **Themes:** Day (paper) and Night (graphite), switched with the sun/moon button. Night is a separate palette, not an inversion.
- **Collections are tables.** Playbooks, OSINT tools and detections are listed in index tables, not grids of identical cards.

### Core tokens

| Token | Day | Night |
|---|---|---|
| paper | `#f5f4f1` | `#111316` |
| card | `#fdfcfb` | `#191c20` |
| ink | `#181c21` | `#eaeae5` |
| ink-2 | `#41454c` | `#c1c4c9` |
| muted (smallest text allowed) | `#5f646a` | `#9a9fa5` |
| rule-strong (control borders) | `#7c8186` | `#646970` |
| pen | `#1a57a1` | `#83c1fb` |
| violet | `#5b45a0` | `#b5a3f2` |
| TP text / fill | `#b12822` / `#a91515` | `#f87f73` / `#d9544b` |
| INC text / fill | `#8d5416` / `#c27919` | `#edb65c` / `#f2af48` |
| BTP text / fill | `#227240` / `#3f9557` | `#75d291` / `#6ed889` |
| FP text / fill | `#5f646a` / `#7c8186` | `#a6abb2` / `#6d7279` |

Text tokens meet WCAG 2.2 AA (4.5:1) on their surfaces; control borders and fills meet 3:1. Exact colours may still be tuned.

## Rules for future edits

Keep these when changing the viewer, by hand or with an AI assistant.

1. Colours come only from the token block.
2. Pen marks analyst actions and focus only. Violet marks the card system only. Neither is decoration.
3. A verdict colour always appears with its shape and its label.
4. Text tokens stay at 4.5:1 or better; borders and fills at 3:1.
5. Fonts are the two embedded Atkinson families. No external font requests.
6. Uppercase only for the verdict stamp and keycaps. Labels are sentence case without letter-spacing.
7. One radius (4px). No pills, gradients, glows, glass or coloured side borders on cards.
8. Collections are lists or tables. Number only real sequences.
9. One framed current item and one primary action per view.
10. Motion only for the trace, the stamp and small state changes, all off under reduced motion.
11. Answer buttons are visually equal. The tool never pre-weights an answer.
12. Before merging UI work: check Day and Night, run the accessibility checks, and ask a fresh reviewer which AI tool made it. The right answer is "none".

## Evidence and its limits

No controlled study compares decision-tree, wizard or checklist designs for SOC triage. Most of the UX guidance is borrowed from aviation checklist design, clinical decision support and general usability research. The figures on AI-assisted triage come from one vendor-authored trial and early academic benchmarks. The visual direction is design judgement, checked against published accessibility standards. No study shows that an "AI look" harms analysts; the aim is a tool that looks deliberate and stays readable through a long shift.

## Key sources

- Alahmadi et al., [99% False Positives](https://www.usenix.org/conference/usenixsecurity22/presentation/alahmadi), USENIX Security 2022
- Sundaramurthy et al., [Human-centred SOC fieldwork](https://cse.usf.edu/~xou/publications/sundaramurthyIEEEIC17.pdf), IEEE Internet Computing 2017
- Burian, [Design guidance for emergency and abnormal checklists](https://hsi.arc.nasa.gov/flightcognition/Publications/EA_Checklist_Design.pdf), NASA Ames
- Poly et al., [Alert override in clinical decision support](https://medinform.jmir.org/2020/7/e15653), JMIR 2020
- Nielsen Norman Group on [wizards](https://www.nngroup.com/articles/wizards/) and [progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
- [Microsoft Sentinel incident classification](https://learn.microsoft.com/en-us/azure/sentinel/incident-navigate-triage)
- [Phishing triage agent trial](https://arxiv.org/abs/2511.13860) (vendor-authored)
- Anthropic, [Improving frontend design through skills](https://claude.com/blog/improving-frontend-design-through-skills), and Krebs, [Design slop](https://adriankrebs.ch/blog/design-slop/)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) and the [SIL Open Font License FAQ](https://openfontlicense.org/ofl-faq/)

## Status

- [x] Design notes
- [ ] Data model: review status, typed actions, empty-result rule, public-safety lint
- [ ] Viewer re-skin: tokens, embedded fonts, verdict shapes, card motif, trace, home illustration
- [ ] Viewer functionality: typed actions, empty-result hints, version stamp in notes, clear case
- [ ] CI: contrast test, offline test, design lint
