# SRA Method Relationship Audit

Date: 2026-09-03
Branch: `audit/sra-wakeup-and-method-boundaries`
Parent issue: #156
Verdict: **PASS AFTER RECIPROCAL-BOUNDARY REMEDIATION**

## Audit Question

Are SRA's ownership boundaries with the existing Mindthus methods conceptually correct, visible from both sides, represented in the router, and protected by executable tests?

This audit checks ownership, not whether any method's semantic judgment is correct in a particular real-world case.

## SRA Ownership Center

SRA owns one judgment:

> Multiple sufficiently judgeable candidates genuinely compete for one shared scarce resource; decide which allocation receives the next meaningful tranche, which work stays at maintenance, which work is deferred or stopped, whether capacity remains reserved, and when to rerank.

SRA does not own:

- defining an unclear problem;
- stabilizing a malformed proposition or comparison axis;
- determining a long-term system direction;
- designing the carrier and exposure of one selected mainline;
- assigning Workflow / Agentic / Evidence control;
- strengthening one bounded artifact internally;
- detecting the repeated-local-repair brake;
- persisting Mission state or mutating tasks.

## Ownership Matrix

| Neighbor | Neighbor owns | SRA enters when | Handoff rule |
|---|---|---|---|
| `3L5S` | Problem discovery, definition, decomposition | Candidate problems/tasks are minimally judgeable and compete for one resource | 3L5S makes candidates judgeable; SRA allocates; selected work may return to 3L5S for deeper decomposition |
| `EDSP` | False binary, unstable proposition, structural coordinate system | Candidate structure is stable and the remaining question is resource allocation | EDSP stabilizes structure; SRA allocates; SRA does not run its own replacement Extreme Deduction |
| `SELA` | Long-term system-efficiency versus local-advantage direction | Direction is sufficiently accepted and current candidates compete for a resource pool | SELA supplies direction constraint; SRA chooses the current allocation |
| `MPG` | Carrier, exposure, timing, optionality, path posture for one selected mainline | Several problems, objectives, or bundles compete before one mainline/carrier is selected | SRA chooses across candidates; MPG assesses the selected candidate's carrier/path risk |
| `WAE` | Agentic-system control boundary and ownership closure | Workflow control is settled and valid actions compete for the resource | WAE constrains how SRA runs; SRA retains allocation semantics |
| `TVG` | Next value-gain round inside one bounded artifact | That artifact competes with external work for the same time/person/budget | TVG supplies internal value hypothesis; SRA decides cross-task allocation |
| `Anti-Spiral` | Detect and brake repeated local repair | The brake has released a resource and several next actions compete for it | One-way handoff: Anti-Spiral brakes, SRA allocates; no recursive loop |
| `TPlan` | Mission identity, state, Pulse, continuation, authority, recovery, task mutation | Real tasks/branches inside or outside a Mission compete for a common resource | SRA returns semantic allocation; TPlan records/applies it within authority |
| `using-mindthus` | Entry calibration and owner arbitration | The active judgment object matches SRA's allocation signature | Router selects one owner; it does not average SRA with neighboring methods |

## Initial Findings

### R1 — EDSP Had Only A One-Way Boundary

SRA correctly transferred unstable structure to EDSP, but the EDSP Skill and public method page did not state when EDSP must yield to SRA after the candidate structure is stable.

Risk:

- a resource allocation framed as A/B could remain inside EDSP;
- EDSP could continue scenario projection after the comparison axis was already settled;
- SRA would be discoverable only from its own documentation.

Remediation:

- EDSP Skill now routes stable, resource-contending candidates to SRA;
- EDSP public method page now records the same handoff;
- executable tests require both surfaces.

Status: **FIXED**.

### R2 — WAE Had Only A One-Way Boundary

SRA correctly routed controller mismatch to WAE, but WAE did not explicitly yield when the control boundary was already settled and the active question was resource allocation.

Risk:

- because SRA is a hybrid Workflow + Agentic Skill, WAE could become a generic wrapper around every allocation;
- control design could replace the actual allocation judgment;
- the user could receive an architecture answer when asking where the next engineer-day should go.

Remediation:

- WAE Skill now states that settled control plus competing valid actions routes to SRA;
- WAE public method page states that WAE constrains SRA's runtime but does not select the priority;
- executable tests require the reciprocal boundary.

Status: **FIXED**.

### R3 — General Router Arbitration Did Not Name The Full SRA Boundary Set

The owner table contained SRA, but the arbitration line previously named only SRA, SELA, and MPG. It did not explicitly preserve 3L5S/EDSP definition and structure, WAE control, or TPlan runtime ownership at the same join point.

Remediation:

The compact router now preserves:

```text
SRA owns allocation;
3L5S/EDSP own definition/structure;
WAE owns control;
TPlan owns runtime;
SELA owns direction pressure;
MPG owns path-carrying action.
```

Status: **FIXED**.

### R4 — Entry Triage Did Not Express The SRA Tie-Break

Entry Triage had low-frequency triggers for framing, Whole Elephant, EDSP, SELA, Anti-Spiral, and AQM, but not for resource allocation.

Remediation:

- added the SRA disease family;
- added the shared-resource trigger;
- added the positive loaded-action requirement;
- added the negative boundary: one blocker, undefined candidates, independent resources, or a cheaper reversible trial does not qualify;
- stated that unstable structure belongs to EDSP before SRA.

Status: **FIXED**.

## Reciprocal Surface Coverage

Skill-entry reciprocal boundaries:

```text
3L5S       PASS
EDSP       PASS
SELA       PASS
MPG        PASS
WAE        PASS
TVG        PASS
TPlan      PASS
```

Cross-cutting Anti-Spiral handoff:

```text
Anti-Spiral PASS
```

Public method-page handoffs:

```text
3L5S       PASS
EDSP       PASS
SELA       PASS
MPG        PASS
WAE        PASS
TVG        PASS
TPlan      PASS
```

Coverage totals:

- direct neighboring Skill surfaces: **7 / 7**;
- Anti-Spiral handoff surface: **1 / 1**;
- public method documentation: **7 / 7**;
- general router + Entry Triage: **2 / 2**.

## Negative Ownership Cases

The dedicated holdout protects these non-SRA routes:

1. unclear candidate problem -> 3L5S;
2. unstable all-human/all-automation binary -> EDSP;
3. long-term manual-versus-automation direction -> SELA;
4. selected mainline carrier/exposure -> MPG;
5. script-versus-agent controller mismatch -> WAE;
6. one bounded artifact with no external competition -> TVG;
7. Mission recovery and state -> TPlan;
8. third repeated local patch -> Anti-Spiral;
9. one known blocker -> direct;
10. independent resources -> direct parallel work;
11. missing resource/cost facts -> information acquisition;
12. deterministic checklist -> direct execution.

These cases ensure SRA is not certified by calling it more often.

## TPlan Boundary

This audit does not change:

```text
skills/tplan/resources/hooks.md
skills/tplan/resources/schema.md
skills/tplan/scripts/tplan_runtime.py
```

No `allocation_review` hook is added. SRA remains independently useful and supplies a semantic recommendation only; TPlan retains Mission/runtime authority.

## Executable Protection

`tests/test_sra_wakeup_and_boundaries.py` verifies:

- direct SRA loading without 3L5S/TPlan prerequisites;
- five release layouts;
- router and Entry Triage signature alignment;
- reciprocal Skill boundaries;
- public method-page handoffs;
- 12 SRA positives, eight adjacent controls, and four stay-asleep controls;
- separation of static availability from behavioral wake-up rate.

The test is registered in `tests/test-lifecycle-registry.json`.

## Mechanical Evidence

```text
git diff --check                         PASS
SRA/router/method focused suite          109 PASS
Test Lifecycle executable coverage       73 / 73
full unittest suite                       927 PASS, 5 skipped
all-platform release pack                PASS
using-mindthus entry                      900 words / 7,308 bytes
SRA entry                                 10,128 / 10,240 bytes
WAE entry                                 10,185 / 10,240 bytes
TPlan hook/schema/runtime diff            EMPTY
```

## Claim Ceiling

Supported conclusion:

> SRA's ownership relationship with all current Mindthus judgment methods is explicit, reciprocal where needed, represented in the router, and protected by deterministic tests.

Unsupported conclusions:

- every host will select the correct owner naturally;
- a reciprocal mention proves semantic routing accuracy;
- SRA will never overlap another method in a real mixed question;
- static boundary tests establish a behavioral wake-up rate.

## Final Verdict

- SRA method center: **PASS**.
- Neighbor ownership model: **PASS**.
- Reciprocal Skill boundaries: **PASS after EDSP/WAE remediation**.
- Public documentation: **PASS**.
- Router arbitration and Entry Triage: **PASS**.
- TPlan ownership preserved: **PASS**.
- Behavioral cross-method routing accuracy: **PENDING live host/model evidence**.
