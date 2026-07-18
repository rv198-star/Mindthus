# N3 Native-Carrier Qualification Result

Terminal outcome: `REJECT_NATIVE_ENTRY`

The qualification ran on 2026-07-19 with `gpt-5.6-sol / xhigh`, 16 Generator
calls, zero Judge calls, no Stable plugin, and no release or comparison action. Candidate
A used the authorized entry SHA `b1035c3656fbf7b9e41cc264c4faf5b954690da2cfd784d98e9183ba868caad9`.
Candidate B used the one permitted correction and entry SHA
`2cf45620b83a8f4b32ba85a9957be9f7aa85dabacdf0e16af4699c6c82c83eb9`.

## Decision

Native discovery itself worked: every fresh Candidate A and B thread directly read the
thin entry, and the clear-owner case directly co-loaded WAE without a routing turn. The
route nevertheless fails eligibility because direct owner discovery also bypasses the
thin entry's arbitration boundary:

1. In both A and B, the Frame/Whole release case loaded the full WAE owner even though
   the task was a product-readiness evidence problem with no agentic-system controller
   mismatch. The behavior was safe, but owner loading was a false positive and added a
   large unrelated contract.
2. In both A and B, the underspecified migration case loaded MPG and SELA before locking
   actor, target, authority, timing, or acceptable loss. It then issued a pause/stop
   recommendation instead of asking the one blocking question required by the frozen
   case.
3. Candidate B moved the decision-context obligation into the Skill description and
   before owner selection in the body. The same failure remained in an empty isolated
   case directory. The failure is therefore not explained by Candidate A's shared
   fixture directory.

This is an observed rejection, not an observability stop. Raw lifecycle events expose
the Skill file reads directly. A third wording repair, Hook fallback, owner rewrite, or
new protocol layer is outside the frozen design and is not authorized.

## Case results

| Call | Case | A | B | Controlling evidence |
| ---: | --- | --- | --- | --- |
| 1 | Clear direct work | pass | pass | thin entry read; no owner read; same-turn file change |
| 2 | Evidence first | pass | pass | thin entry read; `service.json` read before verified answer |
| 3 | Clear WAE owner | pass | pass | thin entry and WAE read in one turn; no routing exchange |
| 4 | Frame plus Whole | fail | fail | safe whole-product hold, but unrelated WAE body also loaded |
| 5 | Decision context plus ambiguity | fail | fail | MPG+SELA loaded; no blocking context question |
| 6 | Anti-Spiral evidence turn 1 | pass | pass | bounded evidence-driven plan change |
| 7 | Anti-Spiral evidence turn 2 | pass | pass | new metric caused one bounded refinement |
| 8 | Anti-Spiral no-delta turn 3 | pass | pass | file unchanged; additive process explicitly refused |

## Host-reported usage

Cached input is a subset of input and must not be added to it.

| Candidate | Calls | Input | Cached input | Output | Reasoning output |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 8 | 859,161 | 755,712 | 10,629 | 3,039 |
| B | 8 | 785,296 | 668,672 | 11,637 | 4,943 |
| Total | 16 | 1,644,457 | 1,424,384 | 22,266 | 7,982 |

These figures characterize this qualification run only. There is no Stable comparison,
so they do not establish a token or latency advantage or regression.

## Evidence location

The exact JSONL stdout streams are stored under `evidence/arm-a/` and
`evidence/arm-b/`. The logs include lifecycle events, command-level Skill reads, file
changes, final messages, and host-reported token fields. Candidate B call 1 also emitted
a concurrent state-database migration warning on stderr; the call completed, loaded the
correct Skill digest, changed the requested file, and is not involved in either
controlling failure.

## Consequence

Stop this successor route. The experiment proves that a compact mandatory entry can be
natively discovered, but it does not prove that unchanged owner descriptions can safely
remain fully direct while the thin entry arbitrates ambiguity. Sol can select the large
owners before the entry's body has a chance to constrain that selection. Any next design
must treat owner metadata precision or the discovery topology itself as the active
problem; it must not continue repairing this thin entry.
