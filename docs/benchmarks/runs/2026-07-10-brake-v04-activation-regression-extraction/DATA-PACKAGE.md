# Brake V0.4 Activation Regression Extraction

Status: derived data only. This package invokes no benchmark CLI and changes no prompt,
fixture, runner, threshold, gate, or anchor. It extracts pre-existing JSONL/manifest
artifacts for the audit's pre-registered two-branch interpretation.

## Sources And Units

- Current diagnostic source: `2026-07-10-brake-v04-action-anchor-dev/repeat-*/original/`.
- Comparator: `2026-07-09-brake-semantic-triage-v03-threshold-085-dev/repeat-*/`, whose
  recorded verdict is four pre-registered gates PASS and positive triage fire `48/48`.
- Both use the same original fixture SHA-256:
  `5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13`.
- Both use threshold `0.85` and explicit model `gpt-5.5`; their prompt and runner
  fingerprints differ and are recorded in [`source-manifest.json`](source-manifest.json).
- A **case-repeat** is one positive case in one of three repeats. It is the unit of the
  `35/48` activation result. A **case-turn** preserves every triage call, including
  the second turn of multi-turn cases.

## Extracted Files

| File | Rows | Contents |
| --- | ---: | --- |
| [`old-positive-case-turns.jsonl`](old-positive-case-turns.jsonl) | 60 | Every original-fixture positive case-turn: fired, four hard gates, confidence, raw `abstain_reason`, expected-owner result, blind score, and owner fidelity. |
| [`lost-activation-v03-085-comparison.jsonl`](lost-activation-v03-085-comparison.jsonl) | 13 | Every current no-fire case-repeat, matched to the same V0.3/0.85 repeat, case, and turn. |
| [`fired-no-owner-load.jsonl`](fired-no-owner-load.jsonl) | 8 | Every current fired case-repeat with `expected_owner_loaded=false`, including exposure reasons, exposed owners, actual loaded owner collection, and raw loaded-command collection. |

A raw empty string in `abstain_reason` is retained as an empty string. `prior_repair_count`
is preserved as an integer and `prior_repair_count_ge_3` is the corresponding hard-gate
boolean.

## Thirteen Current Activation Losses

`F@x` means `triage_fired=true` at confidence `x`; `A@x` means false. Semicolons
separate turns. All 13 current rows have no fired turn; all matched V0.3/0.85 case
repeats fired at least once.

| Repeat | Case | V0.4 turns | V0.3/0.85 same-case same-turn comparison |
| ---: | --- | --- | --- |
| 1 | brake-triage-p01 | A@0.84 | F@0.92 |
| 1 | brake-triage-p06 | A@0.82 | F@0.91 |
| 1 | brake-triage-p11 | A@0.84 | F@0.86 |
| 1 | brake-triage-s04 | A@0.83; A@0.78 | F@0.86; A@0.86 |
| 2 | brake-triage-p08 | A@0.78 | F@0.86 |
| 2 | brake-triage-p11 | A@0.83 | F@0.86 |
| 2 | brake-triage-s04 | A@0.82; A@0.78 | F@0.86; A@0.76 |
| 3 | brake-triage-p02 | A@0.84 | F@0.91 |
| 3 | brake-triage-p06 | A@0.82 | F@0.91 |
| 3 | brake-triage-p08 | A@0.74 | F@0.86 |
| 3 | brake-triage-p11 | A@0.82 | F@0.89 |
| 3 | brake-triage-p12 | A@0.82 | F@0.86 |
| 3 | brake-triage-s03 | A@0.82; A@0.82 | F@0.86; F@0.94 |

## Eight Fired-But-Not-Loaded Records

The `loaded_owner` column is the raw score-record collection. The exposure fields are
kept separate: owner skill exposure can occur even when no owner skill is actually
loaded by the generator.

| Repeat | Case | V0.4 turns | Exposure reason by turn | Loaded owner | Judge score | Owner fidelity |
| ---: | --- | --- | --- | --- | ---: | --- |
| 1 | brake-triage-p02 | F@0.88 | ["current_turn_fire"] | [] | 2 | no_load |
| 1 | brake-triage-p03 | F@0.86 | ["current_turn_fire"] | [] | 2 | no_load |
| 1 | brake-triage-p10 | F@0.86 | ["current_turn_fire"] | [] | 2 | no_load |
| 1 | brake-triage-p12 | F@0.90 | ["current_turn_fire"] | [] | 2 | no_load |
| 2 | brake-triage-p05 | F@0.86 | ["current_turn_fire"] | [] | 2 | no_load |
| 3 | brake-triage-p04 | F@0.86 | ["current_turn_fire"] | [] | 2 | no_load |
| 3 | brake-triage-p05 | F@0.93 | ["current_turn_fire"] | [] | 2 | no_load |
| 3 | brake-triage-p09 | F@0.88 | ["current_turn_fire"] | [] | 2 | no_load |

## Interpretation Boundary

The package supplies data for audit interpretation; it does not adjudicate whether the
activation difference is prompt behavior, runner integration, or sample variance. In
particular, the V0.3 comparator has a different prompt and runner fingerprint, so it is
a historical same-fixture/same-threshold control rather than an isolated single-variable
experiment. No Batch 5 request follows from this extraction.
