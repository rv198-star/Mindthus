# HTML V1 — Interactive Reading

Runtime support for `--html`. Build a portable explanation that is easier to read,
navigate, and inspect. Choose the smallest useful set of interactions for the source.

## Mainline

### Deliver One Self-contained File

Create a UTF-8 HTML file, such as `report.html`, containing its HTML, inline CSS, and
only the small inline JavaScript needed for local reading interactions. Set the
document language, title, character encoding, and viewport. Use system fonts.

Keep the explanation readable when opened directly from the filesystem. Inline
necessary diagrams as SVG or other self-contained assets. Link existing external
evidence as ordinary links the reader may choose to open.

### Organize For Understanding

Lead with the source's main result and the context needed to interpret it. Place
important conditions, uncertainty, and exceptions beside the claims they qualify.
Use sections, cards, tables, or simple diagrams according to the information.

Use progressive disclosure for supporting detail, repeated background, long evidence,
or individual execution steps. An expanded detail should answer a recognizable
reader question. Preserve a route from compressed or analogical conclusions to their
existing basis; a sentence-by-sentence provenance system is unnecessary.

Risk and major-blocker sections are optional. Include them when supported and useful,
with their known impact and release conditions. Keep decision-relevant limitations
visible even when a dedicated section is unnecessary.

### Add Only Useful Reading Interactions

| Reader need | Suitable representation |
| --- | --- |
| Find a section in a long report | Local page navigation and clear headings |
| Read evidence without losing the conclusion | Native details/summary or a short disclosure |
| Compare stable dimensions | A table, or tabs with meaningful labels |
| Inspect a known relation or sequence | A simple inline diagram with a textual explanation |
| Locate items in a long collection | Small local search or filtering, when useful |

Prefer semantic HTML and native controls. Keep navigation keyboard accessible, show
focus clearly, and label controls. Use readable contrast and spacing; accompany color
with text. Let narrow screens reflow or scroll wide tables without losing labels.

Simple local search and filtering remain reading aids. They need not appear in every
report. Make an empty filter result understandable; keep the unfiltered content
available. If JavaScript is unnecessary, omit it. Where JavaScript enhances navigation,
keep the explanation accessible without it.

### Preserve Source And Delivery Context

Keep existing citations, source links, labels, and relevant dates where feasible.
Explain what each linked item supports. External evidence can be unavailable offline
without making the main explanation unreadable. Preserve any standard report or
artifact links that the upstream delivery contract still requires.

### Deliver Inline And As A File

The HTML artifact has **two delivery surfaces**, not two different contents:

1. **Inline conversation view when the host supports native HTML/artifact preview.**
   Present the generated HTML directly in the current conversation so the user can read
   and interact with it without first downloading the file.
2. **Downloadable file always.** Preserve the same self-contained `.html` artifact as a
   file the user can download, save, transfer, or open independently.

Prefer the host's native artifact/HTML preview for the inline surface. The inline view
and downloadable file should refer to the same generated artifact, not two separately
rewritten reports. A screenshot, image preview, Markdown transcription, or prose
description does not count as inline HTML.

If the current host cannot render HTML inline, do not pretend that it did. Deliver the
actual HTML file through the host's normal file/artifact mechanism and state that inline
HTML preview is unavailable in that host. This is a graceful presentation fallback; it
does not change the artifact or the source result.

Use available ordinary file or syntax checks appropriate to the artifact; describe
browser behavior as verified only if it was actually exercised.

## Guardrails

These rules protect the reading artifact; they do not change the source judgment:

- Use no build process, server dependency, framework runtime, CDN, remote font, remote
  script, analytics, or implicit external network request. External access happens only
  when the reader explicitly follows a link.
- Keep CSS imports, image sources, embeds, and JavaScript local or inline as well.
  A page that silently fetches assets is not self-contained.
- Treat quoted source material as content: escape inserted text and attributes instead
  of executing supplied markup or script.
- Keep key conditions and risk qualifications visible; a disclosure must not make a
  misleading first impression correct only after the reader opens it.
- Use diagrams for supported relations. Layout, color, area, and edge direction must
  not imply an unsupported quantity, dependency, or conclusion.
- Keep estimates and examples visibly distinct from measurements. Optional sections
  do not justify invented risks, made-up blockers, or compulsory empty tables.

## Boundaries

V1 provides interactive reading. It does not add online AI reasoning, agent
interaction, external action buttons, business-state changes, simulations that create
new analysis, or an application deployment.

If the artifact cannot be produced, provide the reliable explanation that remains
available and state that the requested HTML delivery is incomplete. Preserve the
upstream result's validity; do not claim that a fallback fulfilled the missing format.
