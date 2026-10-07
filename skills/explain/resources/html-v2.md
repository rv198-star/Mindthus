# HTML V2 — Short Draft, Deterministic Presentation

Runtime support for generic Explain HTML. The current Agent writes a compact draft;
programs parse it once, lay out diagrams, and render the page. TPlan's dedicated
progress renderer stays on its existing route until its separate migration is accepted.
The [HTML V1 surface contract](html-v1.md) still owns fidelity, persistence and actual
host-delivery requirements. This compiler prepares content; it does not submit to a
host, verify visibility, or change upstream judgments.

## Mainline

Choose ordinary Markdown for prose and tables. Use components only where their
information shape helps. A level-two heading starts a section; `sheet` gives a two-column
overview, and `doc` gives linear reading. Coordinates, arrows, styles and interactions
come from the compiler, not hand-written HTML/CSS/SVG.

From the installed Explain Skill directory, run one command:

````bash
python3 scripts/render_explanation.py render - --format app-block <<'EXPLAIN'
---
title: Result and next step
layout: sheet
lang: en
---
## Conclusion {#result}
```callout info
The patch is ready for review
Tests passed; production deployment has not been authorized.
```

## Relationship {#route span=2}
```flow LR
Source -> Review: evidence
Review -> Owner: proposed decision
```

## Comparison {#comparison}
| Item | State | Basis |
| --- | --- | --- |
| Test | Passed | Existing test report |
| Deploy | Not authorized | Waiting for owner |

## Supporting evidence {#details collapsed}
Keep essential conditions above the fold. Supporting references can go here.
EXPLAIN
````

In ChatGPT, route the HTML through actual **Visualizations / AppBlock** when exposed, as the mandatory primary in-conversation delivery. In Codex use a truly exposed native rendered surface (never infer one from Codex CLI); other hosts use their real rendering capabilities or graceful readable fallbacks.
Consume the returned app-block payload only through a genuinely available host adapter.
It has the existing `variant=inline`, `language=html` shape, not a rendering receipt.
Use `--format fragment` for other inline HTML hosts. Both modes use stdout without files.
For an explicitly requested saved page, use `--format document --output report.html`.
Existing files require explicit `--overwrite`; rendering errors leave them unchanged.

Python 3.10+ is the common entry/runtime. `--engine auto` probes the actual PATH: a
working Node >=20 is preferred; missing, old, unexecutable or probe-timeout Node uses
the Python layout. Both paths render the same content and graph, with different layout
quality. The Node path uses bundled Dagre; neither path runs an installer or fetches assets.
`--engine node|python` fixes a backend for reproduction. `probe` reports availability.
Installation-integrity, source-syntax and renderer failures are reported rather than
silently retried on another engine.

## Draft grammar

Frontmatter is a scalar subset, not arbitrary YAML: `title`, optional `subtitle`,
`layout: sheet|doc`, `theme: paper|blueprint`, `lang` (BCP47-style tag), and
`style: warn|off`. Defaults are doc, paper, zh-CN, warn. Quote a scalar with JSON string
syntax when needed. Unknown or repeated keys are errors.

Section options are `{#unique-id span=2 collapsed}`; each option is optional. IDs are
ASCII identifiers and must be unique. Use explicit stable IDs for later patching.
Do not collapse conditions whose absence would make the first reading misleading.

| Shape | Draft |
| --- | --- |
| Conclusion and limitations | `callout info|ok|warn|error` fence: first line is its title, remaining lines are Markdown |
| Comparison | Ordinary Markdown table |
| Relationships | `flow LR|TB` fence: `A -> B: label`, `A --> B` for dashed edge, chains and `A -> B & C` for fan-out |
| Ordered message exchange | `sequence` fence: one `A -> B: message` per step; `A --> B: message` renders a dashed return/error path |
| Distinct objects sharing a display name | Declare `a[Same label]` and `b[Same label]`; later edges refer to `a` and `b` |
| Node names containing punctuation/arrows | Use `[name: detail]` or a JSON-quoted node label |
| Percent, interval, unit or unknown | `progress` (alias `range`) fence; each row is `label | value | unit | basis` |
| Exact code | A code fence with its language; code is escaped, not executed or read from other files |

Example progress values are illustrative, not project measurements:

````markdown
```progress
Illustrative completion | 62 | % | Hypothetical example only
Share of remaining work | 35..55 | % | Illustrative interval, no midpoint
Remaining work | 6..9 | hours | Illustrative estimate, not an overall percentage
Unestimated acceptance | ? | hours | Unknown is not zero
```
````

Percentages use the supplied values directly. Intervals use a solid lower bound plus a
hatched uncertain segment. Other units remain numeric labels; nothing normalizes units,
adds estimates, sums parent/child tasks, or computes overall completion from task counts.
Basis is explicit text, not proof that the supplied number is valid.

Markdown supports paragraphs, lists, tables, headings, links, quotations and exact code.
Raw HTML/SVG remains escaped content. Image syntax becomes an explicit link rather than
an implicit asset request. External links may be unavailable offline, but the page remains
readable. Unknown component/code-fence names are reported; `text` can display other syntax
literally. The current slice supports callout/table/flow/sequence/progress. Flow and
sequence diagrams default to fitting the available reading width; with JavaScript enabled,
the reader can switch to the diagram's actual size inside the scrollable container.
Tree/timeline remain later candidates and are not implied by this support.

## Compact visual presentation

The shared default is a compact editorial sheet: 24px desktop title, 15px section
headings and 14px body text; a small utility rail, flat ruled sections, restrained
warm-neutral color and semantic status accents. `blueprint` retains a cooler palette.
Full-width metrics use two columns in sheet mode and return to one column on narrow
screens; source order and declared section spans remain unchanged.

Compactness comes primarily from removing nested card frames and excess chrome, not
from clipping content, collapsing essential qualifications, transforming the whole page
with zoom, or reducing the diagram label sizes. Diagram geometry, fit/actual-size,
source recovery, automatic light/dark theme and keyboard disclosure keep their existing contracts. Theme is `auto` by default, driven by a host `data-host-theme` binding when known or `prefers-color-scheme` otherwise; a local user override remains optional.
Mobile controls retain larger hit areas. Use the same short-draft grammar; no extra
style-selection step or model generation is required.

## Source recovery and local updates

An explicitly exported document embeds only its delivery draft and digest. Copy the
source using its button (manual selection remains available), or use:

```bash
python3 scripts/render_explanation.py recover report.html --output draft.md
python3 scripts/render_explanation.py patch report.html --block result \
  --replacement changed-body.md --format document --output revised.html
```

A patch is body-only Markdown for one named section. It retains original frontmatter,
section headings, other source ranges, references and style selections. A missing or
ambiguous ID, missing source or invalid replacement is an error; the tool does not guess
or overwrite. The digest detects accidental source corruption, not authorship authenticity.
No global page archive, conversation capture, task mutation or settings service is added.

## Writing hints and failure handling

The compiler can warn about sentence/paragraph length, a small set of redundant phrases,
precision in operational steps, and an explicitly supplied `--glossary` JSON mapping.
`--style off` disables these hints. They never modify the source or block rendering.
Accept useful suggestions in context; zero revisions is valid. Preserve qualifiers,
uncertainty, precise terminology, citations and code. There is no strict-mode gate,
mandatory warning cleanup, semantic reviewer or additional model call.

Syntax errors return a code, source line, component and correct example. Fix only the
named syntax, at most twice; then report the missing delivery if it remains unresolved.
Never turn a source or engine error into a claim that HTML was shown successfully.

Normal diagnostics go to stderr; the requested HTML/payload goes to stdout. `--format
json` includes content and diagnostics for tools. Compiling to HTML, submitting it,
seeing/using it in the conversation, and exporting a file remain separate facts.

## Runtime boundary

There are no required environment variables, server, runtime build, CDN, remote font,
network request or browser launch. Fixed third-party sources, modifications, hashes and
licenses are recorded in `scripts/explain_compiler/_vendor/manifest.json` and the bundled
license files. The compiler is not a business application, judgment owner or authorization
mechanism. Online AI, user-decision widgets and video remain outside this slice.
