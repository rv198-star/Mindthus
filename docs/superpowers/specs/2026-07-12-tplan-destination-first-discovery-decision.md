# TPLAN Pre-Task Discovery Boundary: Research Decision And Narrow Design

Date: 2026-07-12
Issue: [#109](https://github.com/rv198-star/Mindthus/issues/109)
Status: Research complete; no-go for core runtime/schema adoption; recommend, but do
not ship, a narrow documentation convention and a prospective evidence gate.

## Core / 核心结论

Do not implement #109 as a new TPLAN mode, runtime node kind, Task status, durable
frontier engine, or `tplan.v0.1` schema extension now.

The useful part of #109 is real but narrower:

> When the Mission destination is stable but an in-scope region is not precise enough
> to become a Task, TPLAN should explicitly permit that region to remain in Mission
> Shared Context as a non-executable narrative discovery note. Once the question and
> decision condition are precise, the existing `addition` gate creates the Task.

This is a documentation and usage-boundary optimization. It is not a new lifecycle.

The full structured capability remains a deferred experiment. It may be reconsidered
only after prospective Missions show that correctly maintained narrative discovery
notes cannot preserve recovery fidelity.

## Evidence Status

This package makes the protocol, fixture, replay coding, expected result projection,
and exact verification commands reviewable in the repository. The baseline and
mechanical fixture checks are independently rerunnable from a checkout.

The two historical replay classifications remain owner-curated source coding. Their
anchors and the SHA-256 identities of the local runtime snapshots used during the
research are recorded in
[the source manifest](../../../tests/tplan/fixtures/issue_109_destination_first/source_manifest.md).
That makes the evidence auditable and the harness reproducible; it does not turn a
locally captured historical state into independently verified source truth.

The protocol was locally specified before result interpretation but was not published
or externally timestamped before execution. It is therefore not a public
preregistration. The result status is: mechanically reproducible, historical replay
conclusions owner-reported.

The recommended documentation convention is not added to release-facing `SKILL.md` or
`schema.md` by this research package. If it is wanted as formal TPLAN behavior, it
needs a separate, small documentation issue and review.

## Decision In Plain Language

The current TPLAN gap is not that it lacks another kind of Task. The gap is that it does
not say clearly where an important but not-yet-taskable region should live.

The real-Mission evidence did not show that a new runtime object solves a problem that
current TPLAN cannot already solve:

- V5 needed one genuinely vague region to remain visible, but its larger defects were
  stale Mission state and missing `addition`/`loopback` updates after #107 and #108
  emerged.
- Issue #31's clean-room follow-up was already precise enough to become a Task. Calling
  it Fog would delay materialization and hide a missing `addition` decision.
- MPG convergence completed with its initial Task sequence intact; a discovery mode
  should have stayed off.

The right optimization is therefore to clarify the pre-Task boundary and test it
prospectively, not to add a second planning system.

## Baseline / 当前事实

Current `tplan.v0.1` has these relevant properties:

- runtime nodes are `task`, `subtask`, and `step`;
- even Lite startup begins with an active Task, though it may delay Step materialization;
- `exploratory` means uncertain payoff, not an unformulated problem;
- `mission_intake`, `addition`, `selection`, and `loopback` already own the semantic
  handoff from discovery to runtime work;
- Mission Shared Context already supplies a recoverable narrative memory surface;
- Task dependencies are not a declared `tplan.v0.1` schema contract.

Therefore a deterministic dependency-aware frontier cannot be added as a small
read-only projection. It first needs a canonical dependency source. Adding that source
would be a schema or sidecar design decision, not a harmless display feature.

## Research Method

The trial sequence was locally specified before results were interpreted. It was not
committed or otherwise publicly timestamped before execution, so it is an
owner-recorded ordering constraint rather than independent preregistration:

1. Compare eager Task materialization.
2. Compare correct use of current TPLAN: discovery Task or narrative note, then
   `addition`/`selection`/`loopback`.
3. Compare an explicit destination-first representation.
4. Require unique value over variant 2, not merely over the eager anti-pattern.
5. Reject a production capability unless a correctly maintained narrative proves
   insufficient in at least one real Mission.

Protocol:
`tests/tplan/destination_first_discovery_trials.md`

Executable experiment:
`tests/tplan/destination_first_discovery_experiment.py`

Contract tests:
`tests/tplan/test_destination_first_discovery_experiment.py`

Committed input and result witnesses:
`tests/tplan/fixtures/issue_109_destination_first/`

## Fixture Result

The bounded structured representation is mechanically possible.

The fixture passed all ten invariants:

1. Destination uses Mission references and does not duplicate objective truth.
2. Fog and Tasks have disjoint identities.
3. Fog never enters the executable frontier.
4. A blocked Task stays out of the frontier.
5. A completed blocker can make a pending Task structurally eligible.
6. Multiple eligible Tasks route to existing `selection`.
7. Restart from identical canonical state reconstructs the same frontier.
8. Fog does not satisfy Mission completion.
9. Out-of-scope, superseded, and materialized history is retained.
10. Scripts need only validate structure; semantic graduation remains agentic.

This proves bounded feasibility. It does not prove product value.

## Real Mission Replay 1: V5 Targeted Stabilization

### Observed progression

The initial V5 map contained #102-#106. Later evidence created or reshaped important
work:

- #107 appeared to cover missing #8/#37 definition-authority register scope;
- #108 appeared after cross-review found public-case narrow fitting;
- #105 split internally into 105a/105b;
- #106 gained additional preflight dependencies;
- natural activation remained an uncertain carrier question after diagnostic register
  hints.

The canonical TPLAN state still had one root Task (`V5P`) and its Shared Context had no
key findings. That state was not sufficient to reconstruct the live issue graph by
itself.

### Attribution

Only the natural-activation carrier was genuinely not yet precise.

The #107 and #108 units were precise when they appeared and should have entered TPLAN
through `addition`. The #106 shadow-set constraint was a precise blocked condition, not
Fog. The observed recovery gap was therefore dominated by stale TPLAN state and missing
hook application.

### Variant result

- Destination-first beats eager creation of a speculative natural-activation
  implementation Task.
- Correct current TPLAN can obtain the same semantic result by keeping that uncertainty
  inside the #104 discovery Task or Mission narrative, then applying `addition` when a
  carrier is specified.
- A durable Fog object adds visibility, but the replay does not prove that correctly
  maintained narrative visibility would fail.

Result: no unique runtime value established.

## Real Mission Replay 2: Issue #31 TVG Value Profiles

### Observed progression

The three initial Tasks were well specified:

- implement the value-profile mechanism;
- create the sourced Shaw Brothers profile;
- run the pilot loop.

The user correction to produce one 18-panel image was a targeted change inside the
active pilot Task.

The later key finding said the pilot was context-contaminated and needed a clean-room
follow-up to prove independent storyboard-design capability.

### Attribution

The clean-room follow-up already had:

- a concrete question;
- a proof condition;
- an evidence boundary;
- a clear relationship to the active Mission.

It was therefore Task-ready. Keeping it as Fog would be under-materialization. The
correct action was the existing `addition` gate.

Result: no Fog need and no unique runtime value established.

## Negative Control: MPG Convergence

The initial four Tasks remained coherent through completion. No not-yet-precise region
needed durable representation. The optional mode correctly stayed off in the
experiment.

This control matters because a discovery capability that activates on every
method-design Mission would add ceremony without value.

## WAE Control Assignment

The main architectural question is who controls each part of the boundary.

| Concern | Controller | Evidence/constraint |
| --- | --- | --- |
| Whether Destination is sufficient | Agentic / human | Mission objective, acceptance evidence, authority boundary |
| Whether a region is in scope | Agentic / 3L5S | Mission alignment and source evidence |
| Whether the question is precise enough for a Task | Agentic / 3L5S | Concrete contribution/question, completion condition, dependencies, evidence/authority boundary |
| Recording a narrative discovery note | Agentic content inside Workflow-owned storage | Stable Mission Shared Context location |
| Creating a Task after graduation | Existing `addition` gate + Workflow mutation | Validated Task shape and Mission alignment |
| Choosing among Tasks | Existing `selection` gate | Path assessment and evidence |
| Task state transitions | Workflow | Existing lifecycle legality |
| Mission completion | Existing acceptance/evidence gates | Success-critical Tasks and acceptance evidence |
| Proving a structured discovery capability is valuable | Evidence | Prospective paired trials, not fixture completeness |

The key boundary is:

> Workflow may preserve an unresolved region, but it must not decide that the region is
> a valid problem, that it has graduated, or that it should be selected.

## Options Considered

### Option A: Add `fog` as a Task status or role

Decision: reject.

Why:

- conflates problem precision with execution state or payoff uncertainty;
- lets Fog leak into Task completion and selection logic;
- turns a pre-Task condition into a second Task lifecycle;
- makes a clean schema freeze uncertain truth.

### Option B: Add a first-class `discovery` runtime node kind

Decision: reject for current adoption.

Why:

- adds a second runtime graph;
- requires identity, transitions, references, recovery, migration, and completion
  boundaries;
- the real-Mission trials did not show unique value over correct current usage.

### Option C: Add `discovery.json` sidecar and deterministic frontier

Decision: defer behind prospective evidence.

Why:

- can keep Fog separate from Tasks;
- can make restart and projection deterministic;
- but needs a canonical dependency model before frontier calculation is honest;
- no replay proved narrative insufficiency when maintained correctly.

### Option D: Clarify an optional narrative pre-Task boundary

Decision: approve as the only current optimization.

Why:

- uses the existing Mission Shared Context memory surface;
- preserves semantic uncertainty without false Task precision;
- reuses existing gates;
- creates no new schema, lifecycle, script authority, or completion path;
- is reversible and low cost.

## Approved Narrow Design / 当前可落地设计

### Mainline: activation rule

Use the narrative pre-Task boundary only when all are true:

1. The Mission objective, acceptance evidence, and authority boundary are stable enough
   to orient work.
2. The region is in scope.
3. The region matters for later Mission convergence.
4. Its question or completion condition cannot yet be stated precisely enough for a
   Task.

Do not activate it when:

- the question is already precise but blocked;
- the work has uncertain payoff but a clear Task shape;
- one bounded discovery Task already contains the investigation and its recovery note
  is sufficient;
- all candidate Tasks are already specified;
- the Mission is too small to justify durable recovery memory.

### Mainline: narrative representation

Mission Shared Context may contain this optional section:

```markdown
## Not Yet Specified

- Region: <human-readable region name>
  - Why it matters: <Mission-relative relevance>
  - Why it is not a Task yet: <missing question, condition, dependency, evidence, or authority>
  - Revisit when: <observable trigger or prior decision>
  - Source refs: <evidence, task, issue, or artifact links>
```

This is recovery memory, not executable Mission state.

The section is agentic/human-authored. No script may infer entries from keywords,
unresolved Tasks, or issue labels.

### Mainline: graduation rule

A region is Task-ready only when it can carry all four items:

1. a concrete contribution or decision question;
2. a completion or decision condition;
3. dependencies or required prior decisions;
4. an evidence or authority boundary.

Graduation path:

```text
3L5S judgment
    -> existing addition gate
    -> Workflow creates Task
    -> narrative note links the Task and records materialization
    -> existing selection gate decides whether it becomes active
```

Graduation does not directly activate the Task.

### Mainline: invalidation and scope

If later evidence changes the route:

- move a narrative entry to `Superseded` with one-line reason and replacement link;
- move a region to `Out of Scope` with the Mission boundary that excludes it;
- do not delete history when it explains later Task shape or recovery state;
- do not count these sections as Tasks, decisions, or acceptance evidence.

### Mainline: user-facing output

Ordinary user updates should say:

- what is currently executable;
- which important region remains unclear;
- what observation would make it actionable.

They should not lead with `Fog`, raw ids, or internal state vocabulary unless the user
asks for audit detail.

## Guardrails / 从属补漏

### Guardrail 1: anti-under-materialization

Protects the graduation mainline from keeping precise work in narrative notes.

If the question, completion condition, dependencies, and evidence/authority boundary
are already clear, the region must go through `addition`. A blocker does not make a
Task into Fog.

This guardrail cannot decide whether the Task is valuable or should be active;
`addition` and `selection` still own those decisions.

### Guardrail 2: no second objective

Protects Mission identity from a narrative Destination becoming canonical.

Destination should be rendered from current Mission fields. Narrative wording may
explain the destination but cannot override objective, acceptance evidence, or
authority.

This guardrail cannot repair an actually ambiguous Mission; that requires
`mission_intake`, Mission Review, or stop.

### Guardrail 3: no automatic frontier

Protects `selection` from a projection silently choosing work.

Under the approved narrow design, no script computes a dependency-aware frontier.
Current pending/blocked Task state remains visible and existing `selection` decides.

This guardrail cannot provide deterministic dependency eligibility because
`tplan.v0.1` has no canonical dependency contract.

### Guardrail 4: no tracker truth

Protects canonical TPLAN state from external issue status drift.

Tracker links may be source references. Closing, assigning, or labeling an issue does
not change TPLAN Task state, evidence, or acceptance.

This guardrail cannot keep state synchronized automatically; the main agent must apply
TPLAN mutations explicitly.

## Boundary / 不做什么

The approved design does not add:

- `fog` Task status or role;
- a `discovery` node kind;
- a second objective field;
- a `discovery.json` file;
- automatic Fog extraction;
- a dependency-aware frontier;
- automatic Task addition or selection;
- concurrency claims;
- tracker adapters;
- Mission completion changes.

## Documentation Change Set / 后续若实施的最小改动

No production change is made by this research Mission. A later documentation-only PR
may touch:

1. `skills/tplan/SKILL.md`
   - add one short pre-Task discovery boundary paragraph under Runtime Loop;
   - keep the existing core claim unchanged.
2. `skills/tplan/resources/schema.md`
   - document the optional Mission Shared Context narrative section;
   - state explicitly that it is not `mission.json` state.
3. `skills/tplan/resources/hooks.md`
   - clarify `mission_intake -> narrative uncertainty -> addition -> selection`;
   - add the anti-under-materialization rule.
4. `docs/methodologies/tplan.md`
   - explain the boundary in plain language with one positive and one negative example.
5. `tests/tplan/test_skill_contract.py`
   - check only the semantic boundary: Fog is non-executable, Task-ready work uses
     `addition`, and no new Gate is introduced;
   - avoid brittle exact-phrase contracts.

This change set should not bump `tplan.v0.1` or `tplan.shared_context.v0.1`.

## Deferred Structured Design / 仅供未来重开，不获批准

If prospective evidence later proves that maintained narrative notes still fail
recovery, the smallest structured candidate is a sidecar, not a Task node.

Candidate shape:

```json
{
  "schema_version": "tplan.discovery.v0.1",
  "mission_id": "...",
  "destination_refs": {
    "objective": "mission.objective",
    "acceptance": ["A1"],
    "authority": "mission.human_in_loop"
  },
  "regions": [
    {
      "id": "F1",
      "region": "...",
      "why_not_task_yet": "...",
      "revisit_trigger": "...",
      "source_refs": [],
      "disposition": "open | materialized | out_of_scope | superseded",
      "materialized_task_ids": [],
      "supersedes": []
    }
  ]
}
```

Even this deferred design would not own frontier eligibility. Dependency semantics
must first be designed either as Task fields or as a separate canonical relation. A
projection cannot invent them.

Potential scripts, if ever authorized:

- `record_discovery_region.py`: shape-validating mutation only;
- `materialize_discovery_region.py`: requires an already-authorized `addition` output;
- `discovery_snapshot.py`: read-only summary, never selection;
- `check_discovery.py`: ids, refs, dispositions, and Mission link validation only.

These scripts remain unapproved until the prospective gate below passes.

## Prospective Reopen Gate

Reopen structured productization only after two prospective long-running Missions run
both of these maintained variants:

- current TPLAN + correctly maintained narrative discovery notes;
- experimental structured sidecar.

Required evidence:

1. Both variants receive equal operator maintenance; stale narrative is not an
   acceptable baseline.
2. The sidecar reduces resume reconstruction or repeated decisions in both Missions.
3. The sidecar does not increase premature nodes, under-materialization, stale records,
   or ceremony in the negative control.
4. At least one failure is attributable to narrative representation limits rather than
   missing `addition`, stale Shared Context, or external tracker drift.
5. A dependency model is justified independently before claiming a deterministic
   frontier.

Stop productization if these conditions do not hold.

## Verification Plan

Current research verification:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.tplan.test_destination_first_discovery_experiment -v

python3 tests/tplan/destination_first_discovery_experiment.py \
  --source-root . \
  --output-dir /tmp/issue-109-destination-first
```

The contract test compares a stable projection of the generated report with
`tests/tplan/fixtures/issue_109_destination_first/expected_result.json`. The full
generated report includes the caller's absolute source-root path and is therefore a
run artifact rather than a committed byte-for-byte snapshot.

If the documentation-only change is later implemented, also run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.tplan.test_skill_contract \
  tests.tplan.test_destination_first_discovery_experiment -v

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'
```

## Claim Ceiling

The experiment establishes only this:

- the proposed structured shape can preserve the intended control boundaries in a
  deterministic fixture;
- the two real-Mission replays do not establish unique value over correct current
  TPLAN usage;
- a documentation-level pre-Task boundary is justified;
- core runtime/schema productization is not justified by current evidence.

It does not establish that structured discovery can never be useful. It establishes
that TPLAN should not pay its lifecycle and schema cost before narrative insufficiency
is demonstrated prospectively. It also does not independently verify the historical
replay classifications beyond the cited sources and recorded local snapshot identities.
