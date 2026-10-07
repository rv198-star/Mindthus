# #228 — Display Repair R1

## Status

**DISPLAY REPAIR: PASS.**

This repair closes the shared display blocker recorded by the original #228 model batch:
wide V2 flow diagrams now fit the default reading viewport instead of hiding the right
side. The original 18 model generations remain immutable. No model generation or
independent model review was repeated for this repair.

This status is limited to the presentation/compiler repair. It does **not** claim a new
ChatGPT in-conversation app-block visibility receipt, merge, release, or approval to
expand tree/timeline.

## Recovery point

- Worktree: `/srv/agentdock/worktrees/Mindthus-explain-v2-design-20261007`
- Branch: `feat/explain-html-v2`
- Pre-repair HEAD: `3ebe402ac9cf283b0824ad8053d2a82e3c2f313e`
- Original frozen D2 result: [model-r1/RESULT.md](../model-r1/RESULT.md)
- Original V1 visual baseline: [Explain V1 sample](../../../explain-v1/samples/d-report.html)
- Same-content V2 reproduction source: [same-content-v2.md](same-content-v2.md)

## Repair

1. Flow and sequence diagrams default to **fit the available reading width**.
2. With JavaScript enabled, a local control switches each diagram between fitted and
   actual size; actual size remains inside the scrollable diagram container.
3. `sequence` moves into the current V2 slice so the repaired implementation does not
   regress the original Explain visual vocabulary. Tree/timeline remain later candidates.
4. The default presentation palette changes from the earlier pale-green-dominant look to
   blue structural emphasis plus semantic green / amber / red states.
5. Sheet layout, headings, panels, tables, metrics and controls are tightened to reduce
   low-value whitespace while preserving the two-column composition.
6. No judgment, facts, source recovery contract, TPlan state or authorization semantics
   move into the renderer.

## Verification

| Check | Result |
| --- | --- |
| Python 3.10 compiler behavior | 43/43 PASS |
| Python 3.12 Explain + contract + packaging + fidelity | 107 tests: 106 PASS, 1 pre-existing skip, 0 failures |
| Managed Skill lint | portable=true; 56 files; 0 errors; 0 warnings |
| Final showcase browser matrix | 8/8 PASS: Node/Python × 1440/390 × JS on/off |
| Diagram default-fit assertion | PASS in all 8 showcase combinations |
| Actual-size ↔ fit control | Real browser click/toggle PASS |
| Existing #228 A pages + repaired B rerenders | 108/108 PASS, 0 failures |
| New model calls | 0 |
| Repeated model generations | 0 |

The 108-page checks reuse the original nine A pages and rerender the original nine B
`generated.md` drafts through both Node and Python backends. The original model pages
under `model-r1/runs/` are not overwritten.

## Visual comparison

The repository's exact V1 demonstration source and HTML were reused as the baseline,
rather than reconstructing the old page from memory. The same business material was
represented as a V2 short draft and rendered at the same 1440 px browser width.

Requested parity axes:

- **Sequence / timing representation:** current V2 now renders deterministic sequence
  diagrams with participant lifelines, ordered messages, dashed return/error paths and
  a textual fallback.
- **Multi-tile composition:** sheet layout retains paired blocks; the same-content demo
  shows green “can continue” and amber “blocker” tiles side by side, followed by table,
  relationship view and next-step block.
- **Color hierarchy:** structural blue, success green, warning amber and error red are
  distinct; the prior nearly monochrome pale-green presentation is removed.
- **Wide-flow readability:** repaired 11B/12B show the full graph in the default 1440 px
  view, with labels still readable; the user can switch to actual size when desired.
- **Progress/dashboard density:** repaired 31B keeps table and remaining-work metrics in
  a balanced two-column sheet without the prior excess padding.

The old V1 single-report sample remains more vertically compact: its 1440 px capture is
1050 px tall, while the same-content V2 demonstration is 1896 px tall because it adds a
relationship diagram, section navigation and explicit panel grouping. This repair does
not claim “fewer pixels” as a universal win. On the user's requested visual axes—diagram
coverage, sequence capability, tile composition, semantic color and readable density—the
repaired V2 is judged **not visually below the V1 baseline**.

## Remaining boundary

The original D2 report separately recorded that a real ChatGPT host-side inline
app-block receipt had not been demonstrated. This repair does not convert downloadable or
browser HTML into that receipt. #229 tree/timeline expansion should therefore remain
separate from this display repair.
