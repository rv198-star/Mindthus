# Explain host-first delivery and adaptive theme

This is runtime support for the [Explain](../SKILL.md) delivery step, not a new
judgment owner or additional model loop. Rich presentation is optional for ordinary
clarity responses; when interactive HTML or a meaningful host visualization is chosen,
the **delivery route below is mandatory**.

## Delivery priority by real host capability

| Environment | Primary surface | Honest fallback |
| --- | --- | --- |
| **ChatGPT** with native Visualizations / app_block exposed | Submit a live in-conversation Visualization / AppBlock (HTML: `variant=inline`, `language=html`, one raw fragment). Use matching native chart/diagram components when more appropriate | If the surface is not available *in this conversation*, deliver the supported readable explanation and explicitly identify any unfulfilled interactive HTML requirement |
| **Codex** with a rendered interactive host | Use the actually available native rendered surface, not an inferred ChatGPT feature | If Codex CLI/terminal has no such surface, use Markdown/table/text diagram and disclose unavailable inline interaction |
| **Other hosts** | Their real native visualization/rendered HTML surface, if available | Markdown, tabular data, Unicode text diagrams and source-backed prose. Mark unmet explicit interactive HTML honestly |

**Do not first export an HTML file, open a separate website, return a screenshot, or
invent an app-block invocation as a substitute for the requested chat-native view.**
Exports/downloads are an additional operation only on explicit request. The host owns
document chrome, frame, expansion and sandbox; HTML is a scoped fragment without
`<!doctype>`, `<html>`, `<head>`, `<body>` or nested iframe.

The compiler's `render --format app-block` and the analysis prototype's
`render_inline.py --format app-block` produce **data envelopes**, not tool calls.
Only a real host component invocation submits them. Keep four observations separate:
HTML prepared → host submitted → user saw content → user operated controls.
A simulated browser or user screenshot of a *different hand-authored* app block does not
prove the compiled source was delivered. Do not promote a host success claim by analogy.

## Theme rules

A chat-native view must be readable in either host theme. Use `auto` by default:

1. If the host truly exposes current light/dark state, provide it as
   `data-host-theme="light"` or `"dark"` on the component's scoped root and
   update it when the host theme changes.
2. Otherwise use CSS `prefers-color-scheme`; theme changes must update presentation
   without regenerating content or a new model call.
3. A deliberate **user** override (`data-mode=light|dark` in the compiler,
   `data-ex-theme=light|dark` in the prototype) outranks `auto` and host preference.
4. If the real host's theme and system theme disagree but no binding is exposed,
   keep a locally matched panel background/text pair to preserve readability. Do not
   falsely claim host-style parity.

Tokens cover **all** surfaces: background, main/secondary text, borders, links, tables,
comparison highlight, success/warning/error status, progress bars, SVG text/lines and
control states. Never set a dark-background color with a hardcoded light-theme text
color or style global `body`/`html` in an embedded fragment. For accessibility aim
at least 4.5:1 normal text, and preferably 7:1 for main text.

The current Explain HTML compiler uses the `.ex-root` palette; its `data-mode=auto`
works through CSS even without JavaScript. Inline analysis fragments use `.ex-inline`,
responsive container queries and the same theme priority. A local background matched to
the text palette prevents invisible text if the parent does not advertise theme state.
Host-specific theme bindings belong to the host adapter, not the portable compiler.

## Verification ceiling

Run representative embedded widths (not only 1440px standalone browser), light/dark
system emulation, explicit host light/dark with opposite system preference, live theme
changes, JavaScript-disabled output, multiple independent embedded widgets and print.
Keep source text, qualifiers, unknown values and diagram meaning unchanged. These are
engineering qualifications; **actual ChatGPT inline visibility/interaction** requires
the genuine native host surface and observation.
