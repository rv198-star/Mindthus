# SRA Method-Architecture Implementation Audit

Date: 2026-09-03  
Issue: #156  
Canonical branch: `feat/sra-implementation`  
Reviewed commit: `4f79446b`  
Verdict: **PASS FOR PHASE 1/2 BOUNDARIES**  
Phase 3 TPlan hook: **NOT AUTHORIZED**  
Independent model review: **NOT AVAILABLE — OCI Codex returned HTTP 401 before model execution**

## Audit Question

Does SRA occupy a valid independent position in Mindthus, and do its implemented
relationships preserve the ownership of 3L5S, EDSP, SELA, MPG, WAE, TVG, Anti-Spiral,
TPlan, using-mindthus, and shared runtime contracts?

This pass reviews method identity, ownership, direct-load handshakes, routing, packaging,
runtime registrations, schema compatibility, and the unchanged TPlan control surface.
Allocation quality is covered by the separate priority-effectiveness audit.

## Evidence Boundary

The architecture verdict rests on repository contracts, deterministic tests, diff
inspection, and a separate ownership checklist. A read-only Codex review was attempted,
but the OCI node returned `401 Unauthorized` before model execution. That failed call is
not independent model evidence.

## Cross-Session Reconciliation

Parallel work produced three relevant states:

- `fix/sra-core-realignment` at `7c3ec048`: correctly identified that contraction and
  replenishment must remain SRA's semantic center, but removed the explicit Lite/Full
  contract and retained the older Chinese name;
- `recovery/sra-cross-session-20260903` at `dbec0502`: preserves the complete concurrent
  implementation state after the approved Lite/Full contract was restored;
- `feat/sra-implementation`: canonical continuation branch, preserving Lite/Full while
  requiring micro-contraction and micro-replenishment in Lite.

The useful core-realignment insight was incorporated directly. The alternative branch is
not the merge target because it conflicts with the maintainer-approved two-depth public
contract.

## Confirmed Method Position

SRA is correctly implemented as a **Judgment Kernel Skill**:

- it owns allocation among sufficiently judgeable candidates sharing a scarce resource;
- it runs independently of 3L5S and TPlan;
- it has a standalone core, Lite/Full mainline, output contract, validator, public method
  page, and pressure surface;
- it does not own durable Mission state or task mutation;
- it is too substantial to be a cognitive primitive and produces a distinct
  action-bearing allocation decision.

## Ownership Matrix

| Surface | Retained owner | SRA relationship |
|---|---|---|
| Problem discovery, definition, decomposition | 3L5S | SRA allocates among minimally comparable candidates |
| False binary or unstable structural coordinates | EDSP | EDSP returns a structural constraint to SRA |
| System efficiency versus local advantage | SELA | SELA calibrates direction; SRA allocates current resources |
| Carrier, exposure, timing, path volatility | MPG | MPG evaluates one selected mainline; SRA does not redesign the carrier |
| Agentic controller mismatch | WAE | WAE controls Workflow/Agentic/Evidence ownership only |
| Value gain inside one bounded artifact | TVG | SRA enters only when the artifact competes with external work |
| Repeated local repair brake | Anti-Spiral | Anti-Spiral constrains allowed actions; SRA allocates released resources once |
| Mission state, Pulse, continuation, authority, recovery, mutation | TPlan | SRA may supply semantic cross-task allocation only |
| Ambiguous entry and owner arbitration | using-mindthus | Routes to SRA by semantic resource competition |

Direct-load handshakes are present on 3L5S, SELA, MPG, TVG, and TPlan Skill surfaces,
plus the Anti-Spiral public method page. EDSP and WAE remain unchanged because SRA's own
boundary already transfers structural ambiguity and controller mismatch to them;
requiring every neighboring Skill to name SRA would create unnecessary coupling.

## Findings And Remediation

### A1 — Alternative Realignment Removed The Approved Depth Contract

The `fix/sra-core-realignment` implementation converted Lite/Full into one adaptive
mainline. That protected contraction-replenishment fidelity, but contradicted the
approved requirement that ordinary execution expose a lightweight fast decision and
major allocation expose a distinct Full mode.

Remediation:

- retain `direct / lite / full / blocked` entry outcomes;
- preserve Lite and Full as explicit user-facing depths;
- require both depths to share the same contraction-replenishment semantic core;
- make Lite one micro-contraction plus one micro-replenishment;
- make Full the expanded bundle/resource/pressure loop.

Status: **FIXED IN CANONICAL BRANCH**.

### A2 — Legacy Judgment Trace v1 Was Accidentally Expanded

The first integration pass added SRA enums to both the current v1.1 schema and the
explicit legacy v1 schema. The project preserves v1 for compatibility while new
producers use v1.1.

Remediation:

- legacy v1 schema remains frozen without SRA enums;
- current v1.1 and the unversioned current alias include SRA;
- Python validation uses version-specific method, owner, and judgment-object sets;
- regression tests prove v1.1 accepts SRA while legacy v1 rejects the extension.

Status: **FIXED**.

### A3 — TPlan And SELA Wording Left Allocation Ownership Ambiguous

TPlan previously named SELA for broad Mission-level selection/subtraction language even
though SELA owns system-efficiency/local-advantage direction, not general scarce-resource
allocation.

Remediation:

- TPlan can route semantic cross-candidate allocation to SRA;
- SELA remains limited to genuine long-term system-efficiency/local-advantage pressure;
- TPlan retains state, Pulse arbitration, continuation, authority, recovery, and
  mutation;
- no new TPlan hook or runtime mutation path is introduced.

Status: **FIXED AT DOCUMENTED BOUNDARY**.

### A4 — Entry Surfaces Exceeded Thin-Skill Budgets

The combined implementation initially pushed SRA `SKILL.md` to 11,107 bytes after the
shared-core correction.

Remediation:

- repeated explanation moved to `resources/methodology.md`;
- the Skill entry retains entry outcomes, Candidate Horizon, priority order, Lite/Full,
  micro-contraction/replenishment, owner boundaries, and runtime references;
- SRA Skill size is now 9,480 bytes, below the project-wide 10 KiB limit;
- TPlan Skill is 7,932 bytes;
- using-mindthus is 898 words and 7,271 bytes.

Status: **FIXED**.

## TPlan Phase 3 Boundary

Diff inspection confirms no changes from the approved design base to:

```text
skills/tplan/resources/hooks.md
skills/tplan/resources/schema.md
skills/tplan/scripts/tplan_runtime.py
```

The implementation therefore does not:

- add an `allocation_review` hook;
- replace TPlan `selection` or `subtraction`;
- change Pulse Gate Arbitration;
- change residual Mission selection;
- change the Linear Continuation Gate;
- change mutation authority.

Any Phase 3 hook requires a separately reviewed follow-up after standalone SRA behavior
has live evidence.

## Routing And Runtime Integration

SRA is registered in:

- using-mindthus semantic routing;
- AGENTS and README method maps;
- Claude, Codex, and OpenCode release-pack skill lists;
- plugin discovery keywords and compact entry cue;
- Judgment Trace v1.1 owner/method/object enums;
- benchmark owner mapping and skill-load detection;
- Primitive Activation allowed method set;
- fidelity usage logging;
- Test Lifecycle registry.

The explicit legacy Judgment Trace v1 schema remains unchanged.

## Mechanical Evidence

Final checks on the isolated canonical worktree:

```text
git diff --check                         PASS
python3 -m compileall -q skills scripts PASS
Test Lifecycle executable coverage      71 / 71
SRA Skill entry size                    9,480 bytes
TPlan hook/schema/runtime diff          EMPTY
python3 -m unittest discover -s tests -q
Ran 892 tests                           OK
Skipped                                 5
```

## Remaining Evidence Limit

Repository contracts demonstrate explicit and internally consistent ownership. They do
not demonstrate natural SRA wake-up precision or priority quality across real host/model
sessions. The OCI node could not execute planned Codex calls because authentication
failed before model execution.

This limits release claims. It does not transfer allocation ownership back to another
method or invalidate SRA's independent architecture.

## Final Verdict

- Independent SRA Skill architecture: **PASS**.
- Phase 1 standalone contract: **PASS**.
- Phase 2 routing, packaging, and runtime-registration candidate: **PASS**.
- TPlan Phase 3 semantic hook: **NOT AUTHORIZED**.
- Natural host/model wake-up and behavior qualification: **PENDING**.
- Merge or release may claim contract and boundary completion only; it must not claim
  proven natural-routing accuracy or universally correct prioritization.
