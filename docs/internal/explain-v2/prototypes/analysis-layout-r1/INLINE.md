# Inline container correction · 2026-10-08

## Current decision

The final destination is an HTML explanation embedded in a ChatGPT conversation, not a downloadable dashboard. The preceding standalone analysis pages were useful composition prototypes but their 1280/1440px full-window acceptance did not validate the actual delivery surface. This corrects a delivery assumption, not the owner's preference for compact, high-information-density layouts.

The primary width is the host-assigned content container. No fixed ChatGPT width is assumed. A wide browser may contain a narrow message column. An expanded host view may allow more room, but the initial explanation must be useful without expansion, download or a separate site.

## Prototype correction

- `render_inline.py` returns a scoped fragment on stdout by default, or the existing prepare-only `variant=inline`, `language=html` envelope with `--format app-block`.
- No document/body/iframe shell, logo, app toolbar, global CSS, page background, global theme toggle, site navigation, fixed height or viewport-width minimum is emitted.
- The same four source-backed sample bodies are reused. Shared `skills/`, TPlan, historical source drafts and model outputs remain unchanged. This is still an authored prototype, not a newly released generic layout engine.
- `inline.css` uses a 100%-bounded root and container queries, not browser-width media queries for layout. Without container-query support the conservative single-column defaults and wrapping tables remain readable.
- Metrics use two columns at narrow widths and four only when space permits. Related supplementary blocks pair when readable. A true side rail is used only with ample container width.
- Work tables retain their fields and source labels; below 540px they become labelled row groups instead of enforcing the previous 550–600px minimum table width. Comparison matrices wrap in place.
- Diagram canvases retain readable natural text size and local horizontal inspection, with an optional whole-diagram overview. Existing textual relationships remain accessible. This is not a claim of a working host fullscreen action.
- Native details retain source access without JavaScript. A small scoped script provides diagram overview and source copying; one instance cannot toggle another. No model call, installer, remote asset or business operation is added.

Default delivery preparation (no saved HTML):

```bash
python3 docs/internal/explain-v2/prototypes/analysis-layout-r1/render_inline.py --case report
python3 docs/internal/explain-v2/prototypes/analysis-layout-r1/render_inline.py --case progress --format app-block
```

`--qa-out` is an explicit developer-only fixture export. The previous `build.py` documents remain comparison evidence, not the default delivery path.

## Actual checks

All six widths below are **test points**, not measurements or official specifications of ChatGPT's message width.

- Browser viewport fixed at 1440×1000; embedded content constrained to 320, 390, 480, 640, 768 or 960px.
- Four cases × two existing graph engines × six container widths × JS on/off: **96/96 PASS**.
- Root and document horizontal overflow: none; work-table width stays within its parent; base body text remains 13px.
- Embedded source SHA-256 matches the pinned source in each run.
- Visible critical-fact checks: 16 report + 11 progress + 7 comparison + 7 mechanism anchors preserved. These checks are mechanical, not an independent semantic review.
- Two same-source widgets with distinct instance IDs: independent graph controls and no duplicate IDs; host sentinel styling and body classes unchanged.
- Dark-mode simulation, source-copy fallback and print checks passed. Host-specific theme/height/expansion integration remains unverified.

Full local logs and screenshots: `/srv/agentdock/.cache/mindthus-explain-inline-r1/qa/`.
Committed compact receipts: `inline-checks.json` and `inline-semantics.json`.

## Delivery ceiling

**Local embedded rendering passed; actual ChatGPT interactive delivery remains pending.**

The available tools and a targeted plugin lookup did not expose a generic Visualizations/app_block raw-HTML submission action in this session. Do not invent an embedding directive, substitute a download/canvas/screenshot as interactive acceptance, or turn a prepared JSON envelope into a rendering receipt. Any screenshot is explicitly a local width-test image, not a ChatGPT screenshot.

Once a real host adapter is available, use this same fragment and verify actual width, content height, source disclosure and diagram interaction inside the conversation. Source generation, preparation, host submission and actual visibility remain distinct facts. No merge, release or generic runtime migration is authorized by this local correction.

Reference: OpenAI's [optional plugin UI guidelines](https://developers.openai.com/plugins/concepts/ui-guidelines) and [conversation-first app design guidance](https://developers.openai.com/blog/what-makes-a-great-chatgpt-app), consulted 2026-10-08. These are design references, not proof that the prototype's existing app-block envelope is an Apps SDK integration.
