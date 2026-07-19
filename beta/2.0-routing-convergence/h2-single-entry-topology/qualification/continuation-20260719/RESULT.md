# H2 Qualification Continuation Result

Terminal H2 outcome: `H2_REJECTED`

Mission consequence: `STOP_2X_EXPLORATION`

The continuation removed both hard failures from the prior carrier: Q2 ran from the
isolated workspace and stayed below the doubled per-call token ceiling. The frozen H2
candidate nevertheless failed its owner-fidelity criterion under clean conditions.

## Q1 — pass

Q1 ran from the isolated workspace and read only the installed thin entry. It loaded no
index or owner, supplied no continue/hold/stop posture, and asked one answer-changing
blocking question. Usage was 28,113 input + 452 output = 28,565 counted tokens.

As in the previous run, it exposed one same-turn sentence announcing use of Mindthus.
This remains a usability defect, but it added no user interaction round and was not the
stopping failure.

## Q2 — critical owner-fidelity failure

Q2 resumed Q1's exact thread UUID while the host process remained in the isolated Q1/Q2
workspace. It did not read the repository, project `AGENTS.md`, or Stable Skills. It
read the installed thin entry, owner index, MPG owner, and then the SELA owner.

MPG was the matching owner: the prompt contained an established mainline, a concrete
carrier and actor, meaningful exposure, path volatility, and a current continue/hold/
stop decision. The prompt did not contain the independent SELA condition of long-term
system efficiency or trend direction conflicting with a real local advantage. Reading
SELA was therefore an unrelated owner load and violated the frozen requirement that a
clear owner task load the correct owner without unrelated owners.

The final answer was practically useful, but the protocol forbids averaging a critical
owner-fidelity failure away with answer quality. Usage was 94,877 input + 2,371 output =
97,248 counted tokens, below the new 400,000 per-call ceiling.

## Usage

| Phase | Calls | Input | Output | Counted |
| --- | ---: | ---: | ---: | ---: |
| Q1 | 1 | 28,113 | 452 | 28,565 |
| Q2 | 1 | 94,877 | 2,371 | 97,248 |
| **Continuation total** | **2 Generator** | **122,990** | **2,823** | **125,813** |
| **Prior + continuation** | **13 Generator** | **1,165,346** | **21,995** | **1,187,341** |

No Judge ran. Q3-Q7 and the Stable comparison were not run after the first trusted
critical failure. The cumulative total remained far below the 8,000,000 counted-token
ceiling; stopping was caused by qualification quality, not resource exhaustion.

## Claim ceiling

The continuation proves that the prior Q2 result was not merely a budget or working-
directory artifact: after fixing both, the frozen candidate still loaded an unrelated
owner on a clear-owner task. It does not prove that every conceivable single-entry
topology is impossible. It proves that candidate `9c271c1f3fb86f1e81f4860d32d9e5ac4f08b59c`
cannot satisfy the frozen H2 qualification without another candidate change or a relaxed
criterion, neither of which is authorized.

Raw host JSONL, stderr, and final answers are under `evidence/live/`.
