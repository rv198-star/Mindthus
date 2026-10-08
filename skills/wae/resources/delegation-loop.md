# WAE Delegation Loop / 显式启用的自适应委派深度

Layer: `mainline extension` with explicit activation.
Status: research/pilot runtime support until real-project evidence closes #207.

## Core / 核心

> WAE Loop 默认关闭。一个有边界的任务或阶段被显式启用后，每次相关责任交接都要经过一次交接充分性判断；当前 Owner 只为仍属于自己的真实交接障碍继续工作，充分后立即放手。

The loop controls **handoff depth**, not task decomposition and not the number of model calls.
A single pass can be sufficient. Multiple checkpoints arise only when the current Owner
tries to hand off again after additional work or evidence.

## Activation / 显式启用

WAE Loop does not enter the normal WAE path passively. Activate it only when the user,
project, or authorized host explicitly requests the delegation-depth mode for a bounded
scope.

Activation establishes once:

1. current Owner responsibility;
2. downstream Owner responsibility and legitimate freedom;
3. decisions/facts reserved to another owner;
4. the downstream use the handoff must support.

The activation remains effective for that scope until it is finished, returned for
input, stopped, or explicitly aborted. Ordinary new findings and deeper technical work
apply the existing agreement; they do not renegotiate it. The pilot keeps the activation
header immutable: if current/downstream ownership, purpose, or authority materially
changes, close the current activation and explicitly enable a new one. Empty downstream
freedom or reserved-decision lists are valid for purely mechanical or unrestricted cases.

Runtime activation is persisted in the target project under:

```text
.mindthus/wae-loop/active.json
```

The pilot runtime is:

```bash
python3 skills/wae/scripts/delegation_loop.py --project-root <project> enable ...
```

The exact installed skill path may differ by host package layout. Use the packaged WAE
script in that host.

## Mandatory Handoff Check While Active / Active 作用域内的交接检查

When the active Owner is about to transfer responsibility, freeze its current artifact
or artifact reference and answer two questions together:

1. **Current responsibility complete?** The handoff contains the decisions, facts,
   conditions, or argument that the current Owner is responsible for.
2. **Recipient can actually take over?** Remaining choices belong to the downstream
   Owner, and the recipient has the material, authority, capability basis, tools, and
   validation surface needed for the declared use.

Then choose exactly one action:

- `handoff` — current responsibility is complete; remaining work is downstream-owned or
  mechanically determined.
- `refine` — a concrete blocking remainder belongs to the current Owner and has an
  effective authorized remedy.
- `need_input` — a necessary decision/fact belongs upstream or outside the current
  scope and is unavailable.
- `stop` — no effective safe next step remains in the active scope or the surrounding
  resource boundary has been reached.

The runtime records the decision; the business Agent owns the semantic judgment.
Scripts never decide that a handoff is sufficient.

Record a checkpoint with:

```bash
python3 skills/wae/scripts/delegation_loop.py --project-root <project> checkpoint \
  --decision handoff \
  --owner-of-remainder downstream \
  --artifact <relative-file>
```

For `refine` and `need_input`, also record the concrete blocking remainder and the
consequence of handing off too early. `refine` additionally names the next minimum work.

### Deterministic handoff guard

The runtime also exposes a host/project integration guard:

```bash
python3 skills/wae/scripts/delegation_loop.py --project-root <project> guard-handoff \
  --artifact <relative-file>
```

When WAE Loop is disabled, the guard allows the normal handoff path. When it is active,
the guard allows transfer only if the latest checkpoint decision is `handoff`; when an
artifact is supplied, its ref/hash must still match the checkpoint. This gives real
projects a mechanical carrier for the explicit activation contract without letting the
script decide semantic sufficiency.

## Refinement / 下钻工作

`refine` means the Owner continues the smallest work that removes **one identified handoff
obstacle and its necessary semantic dependency closure**. Depth is an outcome, not a
predefined architecture→module→algorithm→code ladder. Text length is not the locality
boundary: a correct unit may touch several dependent rules, while a one-line edit may
still change a broad semantic contract.

### First-class refinement lifecycle

Pilot.3 treats four identities as first-class:

```text
Parent Handoff Artifact
        ↓
Refinement Unit
        ↓
Refine Result
        ↓
Absorb
        ↓
Parent Handoff Artifact'
```

A `refine` checkpoint must bind the current Parent Artifact and exactly one current-owned
blocking remainder. The runtime creates one `RU-xxxx` Refinement Unit containing:

- the one question being solved;
- a semantic scope boundary that defines the direct dependency closure this Unit owns;
- an observable completion criterion;
- the immutable Parent identity at Unit creation.

Example:

```bash
python3 skills/wae/scripts/delegation_loop.py --project-root <project> checkpoint \
  --decision refine \
  --artifact P1.md \
  --blocking-remainder "review validity is unresolved" \
  --owner-of-remainder current \
  --consequence-if-handoff-now "P2 would invent review validity" \
  --next-minimum-work "decide the review-validity rule" \
  --unit-kind semantic_decision \
  --unit-scope "review validity and its direct completion dependency" \
  --completion-criterion "one canonical review-validity rule is explicit"
```

The returned `refinement_unit_id` identifies all subsequent work. Optional `work` events
may record evidence acquisition, design analysis, algorithm work, reference code or
another bounded action, but they do not themselves close the Unit:

```bash
python3 skills/wae/scripts/delegation_loop.py --project-root <project> work \
  --unit-id RU-0001 \
  --work-kind design_decision \
  --changed-scope "review validity"
```

For a project-file Parent, the Parent must stay byte-identical while the Unit is being
worked. This prevents `refine` from being implemented as "rewrite the whole Parent and
explain later". The Unit must first produce an explicit Refine Result:

```bash
python3 skills/wae/scripts/delegation_loop.py --project-root <project> refine-result \
  --unit-id RU-0001 \
  --result-status resolved \
  --result-summary "A cycle can be valid with zero actionable findings when all declared checks completed." \
  --resolved-remainder "review validity is unresolved"
```

Large result bodies belong in `--result-artifact`; the trace keeps a bounded summary.
A resolved Result cannot hand off directly. It must be explicitly absorbed into the
Parent:

```bash
# Apply the bounded result to P1.md, then bind the new Parent identity.
python3 skills/wae/scripts/delegation_loop.py --project-root <project> absorb \
  --unit-id RU-0001 \
  --absorb-mode update \
  --parent-after P1.md \
  --absorbed-scope "review validity and direct completion semantics"
```

Use `--absorb-mode confirm` when the Unit proves the current Parent already contains the
needed truth and therefore keeps the same Parent identity.

Only after `Absorb` can the Owner open another Unit or attempt `handoff`. If the Refine
Result instead proves the Unit is externally blocked, the next checkpoint is limited to
`need_input` or `stop`; the runtime does not pretend an unresolved Unit was absorbed.

This structure constrains decomposition and preserves causality, but it still does not
mechanically judge whether the semantic scope was *good*. A full-file rewrite performed
at Absorb time is visible as one Unit causing a large Parent identity change; deciding
whether that change was genuinely required by the Unit remains an Agentic/audit judgment.
Logical or multi-file Parents should use a versioned ref or manifest SHA when identity
binding matters; `update` absorption requires a distinguishable new Parent identity.
No extra checkpoint is created merely to make the trace look iterative.

## Two Valid Closure Paths / 两种合法出口

### Mechanical handoff

The current Owner has closed every result-changing semantic choice required by the
executor. Complete structured input determines the admitted behavior and unknown input
fails closed. The remaining work can be mechanical/Workflow-controlled.

### Agentic handoff

The current Owner has closed its own result-changing choices. Remaining choices are
explicitly delegated to a downstream semantic owner that is authorized and sufficiently
supported for the declared downstream use. Multiple legitimate downstream solutions are
expected and do not reopen upstream ownership.

This is the canonical stopping rule for the delegation loop:

> Every result-changing remainder has an explicit authorized owner, and the selected
> downstream owner can proceed without inventing meaning owned by someone else.

## Trace / 真实项目回放日志

The pilot writes observable facts to the project-local runtime root:

```text
.mindthus/wae-loop/
├── active.json
└── runs/<activation-id>/
    ├── activation.json
    ├── trace.jsonl
    ├── summary.json
    └── wae-loop-run.json
```

`wae-loop-run.json` is the convenient single-file retrieval artifact for later analysis.
It contains the activation agreement, append-only event records, and derived summary.
The persisted authority is the immutable `activation.json` agreement plus the valid
SHA256-chained `trace.jsonl`. `summary.json` and `wae-loop-run.json` are derived views:
when a process stops after an fsynced trace append but before those views advance, the
next runtime operation reconstructs them from the last valid trace event rather than
allocating a duplicate sequence from stale summary state.

The activation agreement carries `activation_sha256`; every trace event binds that digest.
Changing Owner, reserved decisions, scope or another activation field after enable makes
the run invalid instead of silently creating a new agreement under the same activation ID.

By default, trace records contain artifact references/hashes and short observable
summaries rather than artifact contents or private reasoning. A file artifact must live
under the selected project root. External or logical artifacts can be referenced by ID
and optional SHA256.

Each checkpoint can capture observable cost fields when available. Missing telemetry is
left absent rather than treated as zero. Downstream outcomes separately record telemetry
coverage as `complete`, `partial`, or `unknown`.

After a real handoff, record the outcome that matters for #207:

- whether downstream completed or returned upstream;
- whether downstream invented upstream-owned semantics;
- whether it requested a missing upstream decision;
- whether it overrode the handoff;
- whether rework was required and who owned it;
- acceptance result and available cost/coverage.

Example:

```bash
python3 skills/wae/scripts/delegation_loop.py --project-root <project> outcome \
  --handoff-result downstream_completed \
  --downstream-invented-upstream-semantics no \
  --downstream-requested-missing-upstream-decision no \
  --rework-required no \
  --rework-owner none \
  --acceptance-result pass \
  --downstream-outcome-coverage complete
```

The run remains retrievable after the active scope closes. `outcome --activation-id ...`
can append later evidence to a finished run, and the portable bundle is regenerated.

## Finish / 结束作用域

Close the active scope only after its latest checkpoint represents the matching terminal
state:

- `completed` follows `handoff`;
- `need_input` follows `need_input`;
- `stopped` follows `stop`;
- `aborted` closes an interrupted pilot without claiming successful convergence.

```bash
python3 skills/wae/scripts/delegation_loop.py --project-root <project> finish --status completed
```

Use `status` to recover the active activation ID and bundle path after context changes.
Use `validate` to check activation binding, persisted event shape/decision enums, sequence,
hash chain, lifecycle relationships, summary and portable bundle consistency before case
analysis. A hash-correct but structurally/semantically invalid persisted event is rejected.

## Boundaries / 边界

- Activation state is a WAE control-mode fact, not Mission/task state. TPlan continues to
  own scheduling, blockers, recovery, continuation, and long-running lifecycle.
- The pilot runtime records decisions and evidence references; it does not decide
  semantic sufficiency or allocate resource budgets.
- Host-level enforcement varies. `guard-handoff` provides the deterministic gate once a
  host/project routes its handoff carrier through it. While active, the guard first
  validates the authoritative activation/trace state and repairs only stale derived
  summary/bundle views; a broken hash chain, invalid event shape or activation binding
  fails closed before a `handoff` decision is consumed. Native Stop/SubAgent/phase-exit
  wiring must still be separately verified per host before claiming that an agent
  physically cannot bypass the active contract.
- Real-project logs are local analysis material. Public release packs do not include the
  generated `.mindthus/wae-loop/` data.
- WAE Loop remains off outside an explicit activation scope, so normal WAE usage keeps
  the existing minimal path and cost.

## Case Analysis Bridge

For later research, retrieve the single `wae-loop-run.json` from the actual project and
review it together with only the bounded source/artifact excerpts needed to explain the
handoff. Case Prep can then package the selected judgment/TPlan material as a separate
review-required case; the WAE trace does not become a full conversation or Mission dump.
