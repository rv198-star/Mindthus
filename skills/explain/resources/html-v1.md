# HTML V1 — Interactive Reading

Generic HTML generation now uses the [HTML V2 compiler](html-v2.md). This resource
continues to define the source, interaction, persistence and host-surface contract;
TPlan keeps its existing dedicated renderer.

Runtime support for `--html`. Build a portable explanation that is easier to read,
navigate, and inspect. Choose the smallest useful set of interactions for the source.

## Mainline

### Build One Source-backed HTML View

Build one explanation view from the source result, then adapt only its presentation
wrapper to the host.

On ChatGPT, when **Visualizations / app_block** is available, submit a raw HTML fragment
through that surface with `variant=inline` and `language=html`. The fragment must not
contain `<!doctype>`, `<html>`, `<head>`, `<body>`, Markdown fences, or a nested
iframe. The host already supplies the sandbox document and iframe-like presentation.
Use one stable root, local CSS, semantic controls, inline SVG when useful, and one final
local script when interaction adds reading value.

When the user explicitly asks for a saved/downloadable/exported file, render the same
source-backed view as a complete UTF-8 HTML document such as `report.html`, with its
own title, character encoding, viewport, inline CSS, and only the small inline
JavaScript needed for reading interactions. The persisted copy must remain readable
directly from the filesystem.

These are two wrappers around the same explanation semantics, not two independent
analyses. Do **not** persist a file solely because `--html` was requested.

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

### Deliver The Requested Surface

HTML is the portable file format for this resource; it is **not the only valid
interactive surface**. If the user asks only for an interactive view inside the
conversation, any actually available host interaction surface may satisfy that request
without creating a downloadable HTML file. It must consume the same source-backed result
and must be visibly interactive in the current conversation.

This resource has no mandatory dependency on any external plugin, app, canvas, or
provider. Provider-specific adapters are optional host integrations and must stay
outside the portable Explain core.

An explicit request for **HTML visible and interactive inside the conversation**
requires the HTML itself on a real rendered host surface, not merely source code with a
possible Preview tab. A downloadable copy is added when the user also requests
HTML/file export or when the host naturally exposes the same artifact as a file. General
visual summaries may still use images; they fulfill a different request.

On ChatGPT, **Visualizations / app_block is the preferred rendered HTML adapter**.
Use its host chrome instead of recreating a title bar, expand button, iframe, or app
shell. Keep the block focused on one explanation experience and let its height follow
content. Local state and reading interactions may update the block in place.

A previewable HTML code block is **not** a substitute or automatic fallback for an
explicit rendered `--html` request. Use an `html` code block only when the user asks
to inspect the HTML source itself. Code/Preview belongs to the code-block surface, not
to Visualizations.

On hosts without Visualizations, use another actually available sandboxed HTML renderer
when one exists. A generic runtime may carry the same complete document through its own
transport (for example the current `explain.inline_html.v1` envelope), but that
transport is not the ChatGPT Visualizations trigger.

If no rendered HTML surface exists, keep the rendered-HTML requirement open and report
that host limitation. Do not first write a file merely to obtain a preview block and do
not invent undocumented embedding metadata. Rendering is accepted only when the user
can actually see the rendered surface.

If an HTML file already exists because the user requested a file artifact, the optional
`scripts/prepare_html_delivery.py` helper can prepare a preview block from that file
without rewriting it:

```bash
python3 scripts/prepare_html_delivery.py /path/to/report.html
```

The helper returns prepared content, not a rendering receipt. A host can initially show
Code rather than Preview; do not claim automatic display unless observed. When a native
inline HTML/artifact tool exists, prefer it to a code block. Use only documented,
currently exposed host capabilities; do not invent an embedding directive.

Keep these facts separate: HTML content was generated; it was submitted to a
presentation surface; the user actually saw and interacted with it there; and,
separately, a file artifact exists when one was requested. Record visibility/interaction
as verified only with host evidence or user confirmation. Code/CI/browser checks alone
establish neither in-conversation visibility nor delivery acceptance.

When the requested inline surface remains unverified or unavailable, keep that delivery
requirement open and state the actual attempted path and result. Do not silently replace
it with a file attachment, screenshot, or PNG.

Reference: [ChatGPT code-block previews](https://help.openai.com/en/articles/20001246-working-with-writing-blocks-and-code-blocks-in-chatgpt).

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
