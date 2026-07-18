# Decision Completeness Reset — independent audit protocol

Status: active design-audit procedure; no semantic evaluation authority.

## Independence rule

There are three sequential rounds. Each round has six fresh SubAgents. All six receive
the exact same frozen design file and digest. They do not read or receive another
reviewer's findings from the same round. The root agent does not revise the design until
all six reports are returned.

The platform exposes only three child-agent slots in addition to the root agent, so one
round is executed as two isolated waves of three. The second wave receives the original
round snapshot, never the first wave's reports. A round is complete only after all six
reports exist.

## Finding levels

- `BLOCKER`: the design can still consume material calls without reaching a terminal
  program action, erase valid observations, exceed authority, confuse product behavior
  with infrastructure, require an unplanned contract branch, or make a claim stronger
  than its evidence.
- `MAJOR`: the design is decision-complete in principle but an ambiguity could produce
  inconsistent implementation or materially waste budget.
- `MINOR`: clarity, naming, traceability, or non-blocking maintainability issue.

Audits are union-based, not majority votes. Every finding receives one disposition:
`accepted-fixed`, `accepted-boundary`, `rejected-with-evidence`, or
`unresolved-blocker`. Silence is not a disposition.

## Round focus

### Round 1 — foundation and historical falsification

1. v0.1–v0.6 forensic replay;
2. Workflow/Agentic/Evidence controller assignment;
3. terminal and decision-theory completeness;
4. real Codex/API/host integration assumptions;
5. budget, concurrency, settlement, and right-censoring;
6. blinding, judging, adjudication, and evidence integrity.

### Round 2 — adversarial fault injection

1. state-machine and unknown-event fault injection;
2. product-behavior versus infrastructure classification attacks;
3. denominators, missingness, partial evidence, and threshold validity;
4. operational feasibility against actual Codex interfaces;
5. authority, pause/deadline, and no-amendment governance;
6. anti-spiral and deletion audit for accidental overengineering.

### Round 3 — final attempt to break the design

1. construct a seventh-version failure;
2. independently replay every historical failure;
3. prove or disprove terminal totality;
4. calculate worst-case spend and authority exposure;
5. audit claim ceilings and route/program conclusion semantics;
6. audit maintainer usability and whether the design can be implemented without new
   judgment centers.

## Required reviewer output

Each reviewer returns:

1. verdict: `PASS`, `PASS-WITH-MAJORS`, or `BLOCK`;
2. findings with level, exact design section, counterexample, consequence, and required
   change;
3. at least one attempted novel failure scenario;
4. explicit answers to:
   - Can a valid attributable observation still be erased?
   - Can the program still end without one of the three terminal actions?
   - Can execution require an unplanned version/amendment?
   - Can authority be exceeded without an explicit envelope?
5. confidence and remaining uncertainty.

Reviewers are read-only. They must not edit files, run semantic Generator/Judge calls,
change Git/GitHub state, or read same-round reviewer outputs.

## Final pass condition

Round three passes only when all six reviewers return no unresolved `BLOCKER`, the
root disposition log accounts for every finding from all three rounds, and the frozen
final document plus replay table need no new semantic branch to absorb any submitted
failure scenario.
