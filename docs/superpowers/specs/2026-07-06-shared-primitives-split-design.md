# Shared Primitives Split Design

Date: 2026-07-06

## Problem

`docs/methodologies/shared-primitives.md` has become too dense to serve as both
index and full rule body. At the time of this design it is about `761` lines,
`45KB`, and `4966` words.

The risk is not only reader fatigue. For agent usage, a single thick shared file
can dilute attention between unrelated cross-cutting primitives: Whole Elephant,
Frame Fitness, Decision Context, MPG scalar unpack, Aspect Ownership, AQM,
Pressure, Gate Probes, and Failure Smells all compete in one context block.

The split should reduce attention load without creating a new documentation maze.

## Goal

Make `shared-primitives.md` a compact index and cross-primitive map, while moving
high-complexity or high-conflict primitive bodies into focused files.

Success means:

- Agents can load the index first, then only the primitive detail they need.
- Cross-primitive arbitration remains visible in one place.
- Existing links to `shared-primitives.md` remain useful.
- Release packaging includes the new primitive files.
- No primitive becomes a new judgment center because it received its own file.

## Non-Goals

- Do not add new primitives.
- Do not rewrite primitive theory.
- Do not split every small primitive in this stage.
- Do not change method behavior unless a broken reference or packaging gap requires it.

Full split of the smaller primitives is tracked separately in issue #83.

## Recommended Stage 1 Structure

```text
docs/methodologies/shared-primitives.md
docs/methodologies/primitives/
  aspect-ownership.md
  frame-fitness-check.md
  decision-context-calibration.md
  whole-elephant-protocol.md
  mpg-scalar-commitment-unpack.md
  expression-pressure-and-gates.md
```

### `shared-primitives.md`

Role: compact public index and cross-primitive map.

Keep:

- What cognitive primitives are and are not.
- Cognitive Primitive Index table.
- One-sentence core rule for each primitive.
- Owner / trigger / role summary.
- Link to each detailed primitive file.
- A short Aspect Ownership summary so readers know not to average active aspects.
- Boundaries: not a new method layer, not a semantic judge, not a default route.

Remove from index:

- Long internal field lists.
- Detailed validator behavior.
- Long calibration cases.
- Extended examples.
- Large per-primitive guardrail packages.

### `primitives/aspect-ownership.md`

Role: cross-primitive arbitration contract.

Move:

- Aspect Ownership Matrix.
- `judgment_owner / constraint / support` roles.
- `exclusive_with`, `owns_when`, `defer_when`, and `degrade_to`.
- Aspect Aggregation Ban.
- Boundary-fill is not 50/50.

Reason: this is the rule that prevents multiple active cross-cutting primitives
from producing a balanced but toothless answer. It is shared infrastructure, not
one primitive's local detail.

### `primitives/frame-fitness-check.md`

Role: input framing and local-frame capture.

Move:

- Input Framing Audit contract.
- Framing-risk signals, not keyword rules.
- Original prompt contract.
- Route effects: preserve, qualify, reframe, block.
- Boundaries for low-risk direct execution and user-value preservation.

Reason: this is an entry protocol. It should be easy to load without dragging the
full Whole Elephant package.

### `primitives/decision-context-calibration.md`

Role: situated decision ownership.

Move:

- Decision actor, timing, target function, acceptable tradeoff.
- Answer-flip trigger.
- Conflict rule with Whole Elephant.
- Display-scaling calibration case link or condensed reference.

Reason: it can conflict with Whole Elephant over the visible first thesis. Its
body should be isolated enough to compare directly with definition-authority
cases.

### `primitives/whole-elephant-protocol.md`

Role: partial truth capture and definition authority.

Move:

- Partial Truth Capture.
- Whole Object Reconstruction.
- Definition Object Lock.
- Compact Semantic Triad.
- Contrastive Consequence Probe.
- Validator and audit package behavior.
- First Sentence Stress Test / Core Thesis / Essence Wording Guard.
- Result Controller Viewpoint.

Reason: this is the largest and highest-risk primitive cluster. It is also the
most likely to become a guardrail-as-judgment-center if left mixed with the index.

### `primitives/mpg-scalar-commitment-unpack.md`

Role: MPG pre-route support primitive.

Move:

- Scalar Commitment Under Path Volatility.
- `mainline / carrier / path_volatility / exposure / commitment`.
- Route states: `mpg_ready`, `needs_one_clarification`, `mainline_unclear`,
  `evidence_missing`, `not_applicable`.
- Boundaries and visible behavior.
- Link to #82 manual review cases.

Reason: this primitive exists specifically to shape MPG routing input. Keeping it
near, but not inside, the main MPG skill protects the support-only boundary.

### `primitives/expression-pressure-and-gates.md`

Role: compact home for smaller cross-cutting primitives that are not yet worth
one file each.

Move:

- Approximate Quantified Mapping.
- Pressure Surface Consolidation.
- Gate Probes.
- Failure Smells.

Reason: these are real primitives, but they are smaller and lower-conflict than
Whole Elephant / Frame Fitness / Decision Context. Splitting all of them now
would increase churn and link maintenance before the first-stage pattern is
proven.

## Why Not Split Everything Now

The long-term preference is to give every primitive its own file. That is tracked
in issue #83.

Stage 1 should not do that yet because:

- Many tests and release-pack checks still expect `shared-primitives.md` as the
  central source.
- The highest attention problem comes from a few large/high-conflict sections,
  not from every small primitive.
- A staged split lets packaging, tests, and agent-loading behavior prove the new
  pattern before repeating it everywhere.
- Full splitting too early may become the same local-repair spiral the project is
  trying to avoid.

## Migration Plan

1. Add `docs/methodologies/primitives/` with the six stage-1 files.
2. Move text verbatim first, with only minimal heading and link edits.
3. Replace moved sections in `shared-primitives.md` with compact summaries and links.
4. Update tests to check:
   - index links exist;
   - primitive files contain their required core phrases;
   - packaging includes `docs/methodologies/primitives/`;
   - existing references to `shared-primitives.md` still work.
5. Run full test suite.
6. Only after this lands, evaluate issue #83 for full small-primitive split.

## Testing Strategy

Use static tests for file existence, links, and key contract phrases. Do not add a
new semantic validator.

Recommended tests:

- `shared-primitives.md` keeps the Cognitive Primitive Index.
- Every detailed primitive link points to an existing file.
- `whole-elephant-protocol.md` contains Compact Semantic Triad and validator
  boundary wording.
- `frame-fitness-check.md` contains the original input audit contract and
  "not keyword rules".
- `decision-context-calibration.md` contains answer-flip and conflict ownership.
- `mpg-scalar-commitment-unpack.md` contains the five latent fields and route states.
- Release-pack tests include the new `primitives/` directory.

## Stop Conditions

Stop or reduce scope if:

- The split requires rewriting method behavior rather than moving docs.
- Packaging changes become larger than the documentation move.
- Tests start asserting long duplicated text across both index and detail files.
- The index remains overlong after moving high-complexity bodies.
- The work starts adding new guardrails instead of relocating existing ones.

## Open Follow-Up

Issue #83 tracks the future full split of remaining small primitives into one file
per primitive. It should start only after this stage proves the index/detail file
pattern works without weakening route discovery.
