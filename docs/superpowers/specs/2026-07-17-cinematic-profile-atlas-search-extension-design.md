# Cinematic Profile And Atlas Search Redesign

Status: implemented design after live river-run audit

Issue: https://github.com/rv198-star/Mindthus/issues/120

## Core

The advanced case is a general cinematic visual-direction Profile, not a colossal-only
Profile. Colossal pressure is one scene adapter. Atlas search is generic TVG runtime
support. Neither layer may take over the other's judgment.

Canonical layers:

1. `cinematic-visual-direction` owns reusable cinematic value semantics, realization
   surfaces, gain policy, and Profile-local prompt support.
2. Scene adapters add bounded local constraints. `colossal-pressure` owns witnessed scale,
   partial threat, environment feedback, and its own intensity ladder.
3. Generic atlas runtime owns deterministic board shape, IDs, lineage, evidence references,
   search state, delivery state, and finalization state.
4. Agentic TVG audit owns semantic selection, gain truth, search exit, and delivery audit.
5. The user owns final taste when the `2x2` has no objective single winner.

## Profile Architecture

The cinematic core includes:

- primary read and one-frame intention
- director shot spine and reveal logic
- director subtraction and shot economy
- scene relation and physical camera-light-material coherence
- controlled fracture rather than decorative chaos or sterile cleanup
- adapter-fit checks and evidence claim ceilings

The `colossal-pressure` adapter includes only:

- witness or instrument anchor
- human, environment, and colossal scale ladder
- one dominant partial threat fragment
- partial visibility and frame overflow
- environment response to large force
- adapter intensity 2-5

TVG method pressure is resource investment. Adapter intensity is scene realization. They
must be recorded separately.

The old `cinematic-colossal-realism` path remains a compatibility alias and historical
evidence package. It is not a second canonical Profile.

## Atlas Mainline

### Initial Round

Before generation, the agent records nine Profile-relevant intents. IDs use stable
round-scoped form:

```text
R00-E01 ... R00-E09
```

`R` identifies the round and `E` identifies the candidate within that round. Post-hoc
intent reconstruction must be marked `post-hoc-with-warning`; it cannot be presented as
predeclared control evidence.

### Parent Selection And Expansion

The Profile audit selects three parents and records preserve, repair, subtraction, and
next-gain hypotheses. The next board is:

```text
row 1: three children of selected parent 1
row 2: three children of selected parent 2
row 3: three children of selected parent 3
```

Children keep stable IDs such as `R01-E01`. Parentage is displayed separately as
`from R00-E04` and stored as `parent_candidate_id`. This keeps references short while
making genetic lineage visible and machine-auditable.

Each row normally explores preserve-and-repair, targeted gain, and one bounded alternative.
Concrete moves come from the active Profile and adapter, not from board layout.

### Search Exit

The search loop ends with:

- `search-freeze`
- `search-freeze-with-review-bound-warning`
- `blocked`

Search freeze means three branches are sufficient to prepare delivery. It is not final
artifact freeze because the next Images2 call may create new images.

### Delivery Audit

The `2x2` may be regenerated from final parents or deterministically composed from frozen
tiles. A regenerated board must receive a Profile audit after generation. Each `S01-S04`
records sources, delta, findings, and veto findings.

Regeneration evidence stores the prompt and both raw and labeled boards. Deterministic
composition stores a composition manifest and both boards. A candidate veto prevents a
ready delivery state. A blocked search has no delivery board.

Delivery states:

- `ready-for-user-selection`
- `ready-for-user-selection-with-warning`
- `return-remediate`
- `blocked`

Only a ready state may be handed to the user as a decision board.

### Finalization

Finalization is explicit:

- `pending-user-selection`
- `skipped`
- `completed`

Completed modes are `accept-tile`, `rerender-selected`, or
`rerender-selected-plus-backup`. Every completed output records source ID, path, and hash.

## Evidence Package

A replayable run records:

- fixed Profile snapshot path and hash, source mode, and adapter path/hash snapshots
- TVG pressure separately from adapter intensity
- exact task and prompt manifest
- per-round prompt, raw image, labeled image, and SHA-256
- predeclared or warning-marked R00 exploration intents
- candidate findings, selected parents, and parent chain
- search gate, delivery audit, finalization state, and claim ceiling

Scripts may verify paths, hashes, IDs, row lineage, and state shape. They must not decide
whether an intent, gain, audit, or image is aesthetically correct.

## Runtime Support

Generic:

- `skills/tvg/resources/atlas-search-contract.json`
- `skills/tvg/scripts/atlas/label_atlas.py`
- `skills/tvg/scripts/atlas/build_selection_board.py`
- `skills/tvg/scripts/atlas/validate_trace.py`

Profile-local:

- `skills/tvg/resources/value-profiles/cinematic-visual-direction/profile.md`
- `resources/director-controls.json`
- `resources/image-audit-rubric.json`
- `resources/scene-adapters/colossal-pressure.json`
- prompt skeleton, lint, and field-lock scripts

## Acceptance

- the advanced case is scene-general and keeps four explicit Profile layers
- colossal rules exist only as a bounded adapter
- R00 intents are recorded before generation or marked post-hoc with warning
- IDs use `Rnn-Eyy`; parentage is visible separately and traceable
- repeated rounds follow `9 -> 3 -> 9`
- search freeze does not certify regenerated delivery images
- regenerated `2x2` boards require post-generation delivery audit
- finalize can remain pending, be skipped, accept a tile, or rerender selected sources
- prompts, paths, hashes, lineage, audit state, and claim ceiling are persisted
- scripts validate deterministic facts without deciding value or exit truth
- old v1.4.6 paths remain replayable as compatibility evidence
