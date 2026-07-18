# Decision Completeness Reset — round 1 audit record

## Frozen input

- Revision: `R0`
- Design SHA-256:
  `f7762e38817c1aa715a32a68fd1d76d5c8b8fba257481ba83c93f77e483182b1`
- Independence: six fresh read-only reviewers; two isolated waves of three; no R0 edit
  occurred until all six final reports were returned.
- Two second-wave sessions initially failed with platform stream disconnects. They
  produced no audit content, were not counted, and retried against the same R0.
- Semantic Generator/Judge calls: `0`

## Reviewer verdicts

| Reviewer | Independent focus | Verdict | Confidence |
| --- | --- | --- | ---: |
| R1-A1 | v0.1–v0.6 historical forensic replay | BLOCK | 0.91 |
| R1-A2 | Workflow/Agentic/Evidence control assignment | BLOCK | 0.92 |
| R1-A3 | terminal state and decision-theory completeness | BLOCK | 0.94 |
| R1-A4 | real Codex/API/runtime integration | BLOCK | 0.94 |
| R1-A5 | budget, concurrency, settlement, censoring | BLOCK | 0.97 |
| R1-A6 | Judge, views, evidence, adjudication | BLOCK | 0.94 |

Round result: `BLOCK / materially redesign before round 2`.

## Finding dispositions

Audits are union-based. Every finding below affected R1; no finding was discarded by
vote.

### R1-A1 — historical replay

| Finding | Level | Disposition | R1 change |
| --- | --- | --- | --- |
| R1-A1-01 | BLOCKER | accepted-fixed | corrected v0.4 from “seven affected cells” to shared carrier/epoch failure; dependency propagation invalidates every dependent comparison |
| R1-A1-02 | BLOCKER | accepted-fixed | split identity from relevance; added `output_stage`; progress-only supports UX/completion/cost, never final-answer scoring |
| R1-A1-03 | BLOCKER | accepted-fixed | added v0.4 common Judge-evidence omission, axis-specific capsule dependencies, and no post-outcome evidence selection |
| R1-A1-04 | MAJOR | accepted-fixed | corrected v0.1 to valid-but-unused preregistration superseded by a later user scope decision |

### R1-A2 — control assignment

| Finding | Level | Disposition | R1 change |
| --- | --- | --- | --- |
| R1-A2-F01 | BLOCKER | accepted-fixed | separated artifact retention, per-axis eligibility, and route effect; added workload/stimulus lineage |
| R1-A2-F02 | BLOCKER | accepted-fixed | added shared dependency graph and corruption propagation for wrappers, carriers, views, prompts, runtime, and capsules |
| R1-A2-F03 | MAJOR | accepted-fixed | workflow records facts only; frozen matrix maps them; any unproved classification is `unknown` |
| R1-A2-F04 | BLOCKER | accepted-fixed | human adjudication is label-deidentified and action-blind; it cannot replace a missing Judge or evidence field |
| R1-A2-F05 | BLOCKER | accepted-fixed | final qualification requires one complete Q1–Q10 packet under one candidate digest; no cross-digest pass splicing |
| R1-A2-F06 | BLOCKER | accepted-fixed | added bounded CALIBRATING/READY phases, fixed deadline, human approval boundary, and `STOP_UNPROVEN` timeout |
| R1-A2-F07 | BLOCKER | accepted-fixed | required preregistered randomized, counterbalanced arm order and temporal-block analysis |

### R1-A3 — terminal completeness

| Finding | Level | Disposition | R1 change |
| --- | --- | --- | --- |
| R1-A3-B01 | BLOCKER | accepted-fixed | replaced overlapping incident rows with role-typed reducer precedence and a conservative default; normal empty output is explicit product behavior |
| R1-A3-B02 | BLOCKER | accepted-fixed | introduced PASS/REFUTED/UNRESOLVED certificates; missingness and unreachable denominator cannot issue `STOP_ROUTE` |
| R1-A3-B03 | BLOCKER | accepted-fixed | replaced global E0 with per-axis eligibility dependencies; unrelated unknown cannot erase an eligible regression |
| R1-A3-B04 | BLOCKER | accepted-fixed | made deadline workflow-owned, adjudication wait single-use, terminal absorbing, and late facts archival only |
| R1-A3-B05 | BLOCKER | accepted-fixed | added pre-freeze satisfiability, joint all-pass witness, denominator capacity, monotonic bounds, and initial-state checks |
| R1-A3-M01 | MAJOR | accepted-fixed | limited qualification to candidate A plus one aggregate correction B; B reruns the whole suite |

### R1-A4 — Codex/runtime integration

| Finding | Level | Disposition | R1 change |
| --- | --- | --- | --- |
| R1-A4-B1 | BLOCKER | accepted-boundary | defined the estimand as live model-alias behavior over a bounded window, not an immutable backend; added continuity identities, balanced blocks, and explicit inability to prove server pinning. R1 does not make all unobservable rollout variation an automatic E0 failure because that would contradict the declared live-service estimand. |
| R1-A4-B2 | BLOCKER | accepted-fixed | added canonical post-qualification seed, complete write-set, cloned homes, frozen/disabled dynamic discovery, and separate cache-sensitive C4 surfaces |
| R1-A4-B3 | BLOCKER | accepted-fixed | Q2 covers every enabled event/tool type; unknown events cap dependencies; Judge tools are removed in config, not prompt-only |
| R1-A4-B4 | BLOCKER | accepted-fixed | added durable pre-send reservation/WAL, streaming append, parent-crash tests, provider cancellation/settlement evidence, and persistent outstanding exposure |
| R1-A4-M1 | MAJOR | accepted-fixed | renamed Judges as correlated replicas of one family; added Q10 shared-bias/evidence calibration and a lower claim ceiling |

### R1-A5 — authority and censoring

| Finding | Level | Disposition | R1 change |
| --- | --- | --- | --- |
| R1-A5-B01 | BLOCKER | accepted-fixed | defined outstanding exposure for every non-exactly-settled call; local kill never releases reservation; no finite U means no hard token-cap claim |
| R1-A5-B02 | BLOCKER | accepted-fixed | reserve the complete three-Generator/two-Judge block and retry allowance before starting; target crossing cannot truncate a reserved block |
| R1-A5-B03 | BLOCKER | accepted-fixed | every attempt receives `[L,U]`; C4 pass/refutation use adverse/favorable interval extremes; infinity remains unresolved |
| R1-A5-M01 | MAJOR | accepted-fixed | one monotonic ledger spans qualification, correction, formal work, retry, Judge backlog, and outstanding exposure |

### R1-A6 — Judge/evidence integrity

| Finding | Level | Disposition | R1 change |
| --- | --- | --- | --- |
| R1-A6-F01 | BLOCKER | accepted-fixed | same-model agreement is one correlated family signal; Q10 includes shared evidence-defect counterexamples; claim ceiling is explicit |
| R1-A6-F02 | BLOCKER | accepted-fixed | evidence capsule policy, sources, coverage, trigger, and precedence freeze before verdicts; post-outcome rejudge is forbidden |
| R1-A6-F03 | BLOCKER | accepted-fixed | all boolean/ordinal/enum/missing fields reduce to value sets; no default averaging; adjudicate only a real disagreement that can flip action |
| R1-A6-F04 | BLOCKER | accepted-fixed | human receipt requires trusted principal/event ID, packet digest, per-axis decision, time, and authentication source; runner cannot manufacture it |
| R1-A6-F05 | MAJOR | accepted-fixed | renamed “blind” to label-deidentified, added transform trace and residual arm-inference/leakage qualification |

## Novel scenarios added to the replay set

- normal provider-terminal empty output;
- shared wrong workload revision with otherwise perfect hashes;
- common valid-hash Judge capsule that lacks semantic coverage;
- cross-digest qualification pass splicing;
- third-position service throttling;
- invisible backend rollout between arm calls;
- parent crash after provider sampling but before local attempt commit;
- complete answer followed by zombie/late settlement;
- self-hashed but unauthenticated “William” adjudication; and
- terminal fact arriving after the terminal receipt.

## Material R1 changes

R1 is not a patch list over the old failure table. It changes the control model:

1. phase machine and terminal latch replace informal Hold/continue language;
2. dependency eligibility replaces global valid/invalid experiment labels;
3. product certificates replace “gate unreachable means route failed”;
4. a coherent candidate qualification replaces accumulated compatibility passes;
5. typed reducers and a conservative default replace named-error branching;
6. uncertainty intervals and outstanding reservations replace post-settlement token
   caps; and
7. correlated Judge replicas plus fixed evidence contracts replace two-vote confidence.

## Round output

- Revision: `R1`
- Design SHA-256:
  `34f8736d48c1d6ecfd43381dfe77c338fa6112870b3e1a5a50ec5b34ac50c4fd`
- Next allowed action: freeze this exact R1 and obtain six fresh round-2 fault-injection
  audits before any R2 edit.
