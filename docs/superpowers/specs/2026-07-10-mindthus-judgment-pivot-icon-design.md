# Mindthus Judgment Pivot Icon Candidates — Design Spec

## Core

Create five raster icon candidates for the Mindthus Codex plugin. Each candidate uses the same central visual claim: a line travelling in one direction reaches an explicit anchor, pivots, and proceeds on a truer path. The mark represents the Mindthus promise to pause at a consequential judgment point, correct the frame when needed, and then act deliberately.

The chosen candidate will later be adapted into the plugin's `logo` and `composerIcon`. This spec covers the five exploration assets only; it does not change packaging or the plugin manifest.

## Shared Visual System

- Square 1:1 icon tile, rendered at 1024 × 1024 for inspection.
- Dark inky navy base (`#0B1524`), electric blue for the active path (`#46A6FF`), and a restrained warm-yellow anchor (`#F5C451`).
- One principal stroke, one anchor, and at most one supporting geometric plane. Generous protected margin: no important form outside the central 72% of the tile.
- Flat, vector-friendly geometry with crisp, slightly softened joins. No gradients, shadows, texture, lettering, monograms, or watermarks.
- Avoid generic AI metaphors: brain, neural network, robot, gear, eye, compass, lightbulb, fingerprint, or circuit board.
- Test mentally at 16px: the pivot must remain visible as a direction change, not dissolve into decorative detail.

## Candidate Set

1. **Sentinel Turn** — a heavy forward stroke makes a clean 90-degree turn through a single circular anchor. The most minimal, strongest small-size candidate.
2. **Offset Correction** — an incoming path ends just before the anchor; the outgoing path begins slightly displaced, making the correction visible rather than implying a smooth continuation.
3. **Threshold Cut** — a path crosses a thin decision boundary, pauses at the anchor, then exits on a new angle. This is the clearest expression of "do not keep going under the old frame."
4. **Field Pivot** — the anchor sits at the corner of one restrained plane; the outgoing path follows a different axis. This adds strategic breadth without turning into an abstract cube.
5. **Spiral Break** — a short, almost-repeating path is visibly interrupted at the anchor and redirected outward. This carries Mindthus's anti-spiral discipline while remaining simple and non-literal.

## Generation Constraints

- Generate five independent raster assets, one for each candidate above; do not combine the five designs into a single contact sheet.
- Use the built-in image generator. These are preview assets and remain outside the project until a selection is made.
- The candidates are icon marks only, centered on a dark square tile; do not include application chrome, a wordmark, descriptive labels, or additional objects.
- After selection, the chosen concept may be regenerated on a chroma-key background and converted to an alpha PNG for plugin packaging.

## Acceptance Checks

- Every candidate visibly contains a pivot and an anchor at normal viewing size.
- Each candidate is recognizably different by its path logic, not merely by a changed color or minor rotation.
- The set reads as one brand family through palette, line weight, geometry, and negative space.
- No candidate relies on a textual explanation to avoid being mistaken for a generic AI icon.
- A selected candidate can be simplified to a readable 16px composer icon without losing the pivot.
