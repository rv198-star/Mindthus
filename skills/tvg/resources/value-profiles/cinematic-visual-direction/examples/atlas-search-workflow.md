# Cinematic Visual Direction Atlas Search

## Core

The cinematic Profile owns visual value. Generic atlas runtime support owns board shape,
IDs, lineage, evidence references, and state validation. The user owns the final taste
choice.

The stable ID format is `Rnn-Eyy`:

- `R00-E01` means round 0, exploration candidate 1.
- `R01-E01` means round 1, exploration candidate 1.
- Parent lineage is displayed separately, for example `from R00-E04`.

Do not encode ancestry into the primary ID. Stable IDs remain easy to reference while the
trace preserves the complete parent chain.

## Mainline

1. Resolve and lock one Profile snapshot plus any scene adapters; record every path and hash.
2. Predeclare nine Profile-relevant exploration intents for `R00-E01..R00-E09`.
3. Persist the exact prompt, model path, output paths, and SHA-256 evidence.
4. Generate one unlabeled `3x3`, then add deterministic IDs.
5. Audit all nine with the Profile and select three branch parents.
6. Record preserve, repair, subtraction, and next-gain hypotheses.
7. Generate the next `3x3`, with one selected parent per row and three gain moves per parent.
8. Label children with `R01-Eyy` plus visible `from R00-Exx` provenance.
9. Repeat `9 -> 3 -> 9` only while a named positive-value hypothesis remains.
10. End the search with `search-freeze` or `search-freeze-with-review-bound-warning`.
11. Generate or deterministically compose a `2x2` delivery board.
12. Audit the actual four delivery images after generation.
13. Return a ready board to the user only when the delivery audit permits it.
14. Record finalization as pending, skipped, accepted tile, or controlled rerender.

Search freeze is not final artifact freeze. A regenerated `2x2` contains new images and
must receive a delivery audit. A deterministic composition may inherit candidate findings,
but its trace records a composition manifest instead of pretending a model prompt created
the board. A blocked search produces no delivery board.

## Candidate Shape

The initial nine are planned before generation. Useful axes include camera relation,
emotional temperature, motion, scene density, medium, reveal logic, and subtraction.
They are not nine unexplained seeds.

For each selected parent, the next row normally contains:

1. preserve-and-repair
2. targeted gain on one weak realization surface
3. bounded alternative or scene-adapter intensity test

The Profile decides which concrete move is useful. The atlas workflow does not invent a
generic mutation policy.

## Delivery And Finalization

The `2x2` should contain four viable and differentiated options. It may use the final
three branches plus one controlled synthesis or contrast branch. Every tile records its
source IDs and receives post-generation audit findings.

Finalization states:

- `pending-user-selection`: a ready `2x2` is waiting for user taste authority
- `skipped`: the user accepts the board or declines a final master
- `completed`: a selected tile is accepted or rerendered with output evidence

A ready delivery state requires every candidate veto list to be empty. A completed output
records its source shortlist ID, path, and SHA-256; `--check-files` verifies the bytes.

## Commands

```bash
python3 skills/tvg/scripts/atlas/label_atlas.py \
  --input artifacts/r01-raw.png \
  --output artifacts/r01-labeled.png \
  --layout 3x3 \
  --id-prefix R01-E \
  --lineage-json artifacts/r01-lineage.json \
  --json
```

```bash
python3 skills/tvg/scripts/atlas/build_selection_board.py \
  --input artifacts/r01-raw.png \
  --labels-json artifacts/r01-labels.json \
  --selected R01-E01 R01-E04 R01-E07 \
  --output artifacts/r01-selected.png \
  --json
```

```bash
python3 skills/tvg/scripts/atlas/validate_trace.py artifacts/run-trace.json \
  --check-files --json
```

Validation proves only deterministic shape, references, hashes, and lineage. It does not
prove that exploration intents, selections, gains, delivery audit, or Profile claims are
aesthetically true.

## Boundaries

- Do not apply the `colossal-pressure` adapter to unrelated scenes.
- Do not let a valid lineage schema stand in for visible parent-specific gain.
- Do not regenerate after a ready delivery audit without reopening delivery audit.
- Do not require `1x1` rerender when the board tile is already usable.
- Do not present a post-hoc R00 intent as predeclared evidence.
