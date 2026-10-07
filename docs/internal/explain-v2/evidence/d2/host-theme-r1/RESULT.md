# Explain D2 · Visualizations routing and adaptive theme (R1)

Date: 2026-10-08. Status: **implementation and local qualification PASS**;
does not imply full #228 host acceptance, main merge, publication or #229 expansion.

**Owner visual acceptance (2026-10-08): PASS for the demonstrated native ChatGPT
Visualization and its compact layout / light-dark presentation.** The Owner saw
the actual in-conversation interface and subsequently instructed us to commit/push
while withholding release. The chat demo drew on compiler output but manually
simplified some markup/styles and added a host theme control. Therefore this
approval is an observed UI/visual acceptance, **not a byte-identical compiler
payload submission receipt or proof that every compiled control was exercised**.
No main merge, tag or release is authorized.

## Reason for change

The owner observed a **real native ChatGPT visualization** (a hand-authored AppBlock,
with selectable report/progress/comparison/sequence views). Its dark-mode screenshot
showed the problem: hardcoded light-theme ink was almost invisible against a dark
conversation surface. This is a real host observation for that **hand-authored demo**,
not evidence that the compiler's `--format app-block` was submitted by the host.

The other owner decision is explicit: rich Explain HTML must first be delivered
**inside ChatGPT's available Visualizations**, not through HTML exports, screenshots
or external preview links. Codex uses actual host capabilities, not an assumed CLI
feature; non-ChatGPT/Codex hosts degrade faithfully. Ordinary clarity-mode prose
continues to use the lightest useful surface.

## Changes

- `skills/explain/SKILL.md` now makes host selection mandatory for visual/rich HTML.
  Detailed policy is in `resources/host-delivery.md` to keep SKILL.md under 10 KiB.
  Portable Explain core and TPlan judgment/state authority are unchanged.
- Compiler HTML starts with `data-mode="auto" data-host-theme="auto"`.
  CSS uses system `prefers-color-scheme` and accepts an explicit *live host binding*
  (`data-host-theme=light|dark`); optional user preference outranks auto. The original
  dark button now toggles between the opposite of auto and auto.
- The dark palette changes from muddy low-contrast colors to charcoal/navy surfaces,
  pale main/secondary text, cool blue informational accents, teal success, amber
  warnings and red errors.
- The authored `analysis-layout-r1` inline prototype applies the same precedence
  with scoped `.ex-inline` tokens and a matching local surface background. It does
  not style the host `html`/`body` or change business content.
- No release, no main merge, no old 18 model page rewrite, no TPlan renderer change.

## Verification

| Real verification | Result |
| --- | --- |
| Explain compiler + routing contract + packaging/fidelity on Python 3.12 | 109 tests: 108 pass, 1 pre-existing skip |
| Node/Python showcase × 1440/390px × JS on/off | 8/8 pass |
| New browser theme suite: system light/dark, host override against system, live switch, manual control, nested widths 320/640/960px, main/secondary text contrast, JS off | **144/144 pass**, 0 errors |
| Source Skill lint | portable=true, **57 files, 0 errors, 0 warnings** |
| Skill entry budget | <=10 KiB, details moved to resource |
| Model calls | 0 |

Browser test: `tests/check_explain_theme.mjs` with Playwright/Chromium already on
OCI. Node+Python HTML generated from existing `showcase.md`; four inline sample
fragments generated from fixed development source drafts. Temporary evidence and
screenshots: `/tmp/mindthus-explain-auto-theme-r1/theme-qa-final/`. Machine summary:
[checks.json](checks.json).

## Acceptance boundary

The compiler emits HTML/payload data and the host is responsible for submitting a
native Visualization. The owner-provided screenshot confirms an **earlier, manually
authored AppBlock** was visible and interactive in ChatGPT. The revised compiler's
payload has not separately received a true host submission/interaction receipt.
The system theme can differ from an app-specific theme; when a live host color
preference is exposed, its adapter must set/update `data-host-theme`. Without
that binding, system scheme is the fallback and local background/ink stay readable.

The next real host-side check should submit the **compiled** HTML fragment to
the actual ChatGPT Visualizations component, then verify both light and dark chat
themes and user interaction, with no download or screenshot substitution.
