# Internal Pilot Release: v1.11.0-wae-loop-pilot.3

Date: 2026-09-08  
Status: INTERNAL PILOT / NOT STABLE / NOT ROI BETA  
Issue: #207  
Research PR: #208  
Stable baseline: v1.10.1

## Purpose

This internal package supersedes `v1.11.0-wae-loop-pilot.2` for new WFF / EKRI / Slidethus pilots.

Pilot.2 fixed persisted-run integrity, but real WFF admission feedback identified a deeper method/runtime fidelity gap: `refine` recorded a claimed `changed_scope` without making the local semantic work unit, its result, and its absorption into the Parent first-class. A small blocker could therefore be followed by a whole-Parent rewrite while the runtime still considered the trace structurally normal.

Pilot.3 addresses that gap directly.

## New canonical refinement lifecycle

```text
Parent Handoff Artifact
        ↓
checkpoint(refine)
        ↓
Refinement Unit (RU-xxxx)
        ↓
work (optional)
        ↓
Refine Result
        ↓
Absorb
        ↓
Parent Handoff Artifact'
        ↓
next checkpoint / handoff
```

### Refinement Unit

A refine checkpoint now requires:

- exactly one current-owned blocking remainder;
- a bound Parent Artifact identity;
- a generated `RU-xxxx` Unit id;
- `unit_kind`;
- a semantic `scope_boundary`;
- an observable `completion_criterion`.

Only one Refinement Unit may remain open at a time.

### Parent stability before Result

For a project-file Parent, the live Parent must remain byte-identical from Unit creation until the Refine Result is recorded. This prevents the pilot from implementing `refine` as “rewrite the Parent first, then explain the scope afterward.”

Logical/multi-file Parents should use a versioned logical ref or manifest SHA when identity binding matters.

### Refine Result

The Unit must produce a bounded Result before the Parent changes.

- `resolved` explicitly resolves the Unit question;
- `blocked` preserves the unresolved boundary and only permits subsequent `need_input` or `stop`;
- `result_summary` is capped at 4096 characters; large content uses a result artifact ref/hash.

### Absorb

A resolved Unit must be explicitly absorbed into the Parent before another handoff/refine checkpoint.

- `update` binds a distinguishable new Parent identity;
- `confirm` records that the existing Parent already carries the required truth and therefore stays identical;
- project-file confirm re-checks the live Parent before accepting the unchanged identity;
- parent-before is derived from Unit creation and cannot be re-declared by the caller;
- result sequence and Parent lineage are validated from the authoritative trace.

## Retained pilot.2 integrity guarantees

Pilot.3 retains the pilot.2 root-cause fixes:

- immutable activation agreement + `activation_sha256`;
- every event binds the activation digest;
- valid fsynced hash-chain `trace.jsonl` is authoritative with `activation.json`;
- `summary.json` and `wae-loop-run.json` are recoverable derived views;
- interrupted append recovery derives the next sequence from valid trace, not stale summary;
- `guard-handoff` validates authoritative state before consuming handoff;
- invalid hash chain, invalid lifecycle, invalid enum/shape, unknown persisted fields, or activation mutation fail closed.

## Explicit scope boundaries

This package still does **not** make semantic locality a deterministic script verdict.

The runtime can enforce:

- one Unit question;
- Parent identity and ordering;
- Result-before-Parent-change for project-file Parents;
- Result/Absorb lifecycle;
- Parent lineage;
- observable before/after ref/hash/bytes.

The runtime cannot determine whether a broad Parent change at Absorb time was genuinely required by the Unit’s semantic dependency closure. That remains an Agentic/audit judgment; using line count or diff percentage as a hard semantic-locality gate would be a controller mismatch.

## Audit result

Two separately scoped audit paths were completed in the same ChatGPT session/model. They are not external/independent-model certification.

1. **Runtime Integrity Audit: PASS**  
   No known pilot.3 runtime-integrity blocker remains. The audit additionally found and closed:
   - confirm Absorb live-parent mismatch;
   - unknown top-level persisted activation/event fields.

2. **Method Choice Audit: PASS WITH PILOT-SCOPE CAVEAT**  
   For the current goal of measuring real WAE Loop handoff-depth value, Unit → Result → Absorb provides materially better causal attribution than pilot.2 or a unit-id-only variant, while remaining much thinner than a nested task-tree/runtime. The extra separation may create editing friction and is therefore not pre-declared as the final Stable UX.

Audit files:

```text
docs/internal/research/wae-loop-release-followup-v1/PILOT3-RUNTIME-INTEGRITY-AUDIT.zh-CN.md
docs/internal/research/wae-loop-release-followup-v1/PILOT3-METHOD-CHOICE-AUDIT.zh-CN.md
```

## Recommended consumer behavior

New real-project pilots should use only:

```text
v1.11.0-wae-loop-pilot.3
```

Do not start a new pilot on `.1` or `.2`.

For WFF/P1-P2 style project-file Parents:

1. bind the actual handoff artifact at refine checkpoint;
2. do bounded analysis/evidence work without modifying the Parent file;
3. record Refine Result;
4. apply the Result to the Parent;
5. record Absorb with the live new Parent;
6. checkpoint handoff against that exact Parent;
7. always pass the real artifact/ref/hash to `guard-handoff`.

## Not claimed

This internal release does not claim:

- semantic scope is mechanically guaranteed to be optimal;
- every Absorb is minimal;
- host Stop/SubAgent integration is automatically bypass-proof;
- real-project G2/G3 value has been established;
- Stable/ROI Beta release eligibility;
- historical WFF long-run overhead has been solved end-to-end.

## Final internal package validation

Package version: `v1.11.0-wae-loop-pilot.3`.

- trace schema: `mindthus.wae-loop-trace.v0.3`
- WAE/pilot targeted tests: `44 passed`
- full repository unittest: `1111 passed, 5 skipped`
- release-pack build: `PASS`
- `git diff --check`: `PASS`
- WAE `SKILL.md`: `10,119 bytes`, inside the 10 KiB entrypoint budget
- ZIP CRC / `testzip`: `PASS`
- embedded per-file `SHA256SUMS`: `PASS`

The final archive path, byte size and archive SHA256 are deliberately bound outside the ZIP in the internal release tracker/index so the archive does not contain a self-referential digest. These checks prove implementation/package integrity only. Real value remains the job of the three project pilots. The source worktree is still uncommitted; until a Mindthus Git mutation path is available, the immutable ZIP SHA256 plus embedded file hashes are the internal package authority.
