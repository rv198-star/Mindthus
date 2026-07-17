# Mindthus 1.x / 2.x Dual-Release Shared-Core Design

Status: proposed for implementation after the current 2.0 Beta evaluation checkpoint

Related work:

- Stable baseline: `v1.4.6`
- 2.0 Beta charter: https://github.com/rv198-star/Mindthus/issues/112
- TVG Profile atlas workflow: https://github.com/rv198-star/Mindthus/issues/120

## Core Decision

Mindthus will maintain two release versions for a period of time, but it must not maintain
two copies of the product.

- The 1.x line remains the Stable runtime and continues receiving compatible features,
  bug fixes, documentation, methods, Profiles, and tooling.
- The 2.x line carries the alternative entry and activation architecture intended to
  reduce unnecessary routing and token cost on highly capable models while remaining
  usable on ordinary models.
- Product capabilities outside the entry and activation plane are shared. A feature such
  as the TVG Profile atlas workflow is implemented once and shipped by both release lines.
- The two lines may publish at different times, but capability drift must be explicit,
  temporary, and visible in release metadata.

Short form:

> One shared product core, two runtime profiles, two release cadences.

## Why The Current Shape Is Insufficient

The current Beta release builder treats the live repository `skills/tvg` tree as if it
must remain byte-identical to the frozen 1.4.6 evaluation baseline. This was useful for
creating one reproducible Beta experiment, but it is not a viable long-term dual-release
contract.

The #120 forward-port exposed the mismatch:

- the shared implementation commit applies cleanly to the Beta branch;
- Stable tests pass;
- the Beta suite rejects the build because `skills/tvg` no longer matches the frozen
  1.4.6 reference digest;
- the failure is an evaluation-identity veto, not a TVG compatibility failure.

A frozen experiment must pin an immutable artifact or Git object. It must not require the
active product source tree to stop evolving.

## Goals

1. Implement shared features and shared bug fixes once.
2. Ship those capabilities in both 1.x and 2.x packages without copying source trees.
3. Keep the full `using-mindthus` runtime available in Stable 1.x.
4. Keep the Thin Kernel and alternative activation path isolated in 2.x.
5. Preserve frozen Beta evaluation evidence while the 2.x product line advances.
6. Allow independent release timing without hiding temporary capability lag.
7. Make package identity, source provenance, runtime profile, and rollback target
   mechanically auditable.

## Non-Goals

- Do not maintain separate 1.x and 2.x copies of TVG, tplan, SELA, MPG, EDSP, WAE, or
  their shared resources.
- Do not require every 1.x release to wait for a 2.x Beta evaluation checkpoint.
- Do not rewrite or silently refresh a frozen evaluation arm after results are inspected.
- Do not treat 2.x as a model-name router. Runtime selection remains an explicit package
  and host-capability choice.
- Do not promise that every shared commit is published by both lines on the same day.

## Layer Ownership

| Layer | Examples | Ownership |
| --- | --- | --- |
| Shared Product Core | owner skills, TVG Profiles, generic runtime support, methodology docs, schemas, validators, shared tests | one canonical source |
| 1.x Runtime Profile | full `using-mindthus`, current Stable routing and activation behavior | 1.x only |
| 2.x Runtime Profile | Thin Kernel, arbitration-only entry, hooks, activation telemetry, host capability handling | 2.x only |
| Evaluation Harness | frozen arms, protocols, manifests, judges, receipts, replay evidence | checkpoint-specific |
| Release Assembly | version, `shared_core_ref`, runtime overlay, namespace, package identity, artifact hashes | release-line-specific |

The Shared Product Core defines what Mindthus can do. Runtime Profiles define how those
capabilities are exposed, selected, and activated. The evaluation harness measures a
named frozen composition; it does not own the live product source.

## Source And Branch Model

Recommended long-lived branches:

- `main`: integration source for Shared Product Core changes.
- `release/1.x`: Stable release preparation, 1.x runtime profile, compatibility fixes,
  versioning, and packaging metadata.
- `release/2.x`: 2.x runtime profile, Beta/RC release preparation, host adapters,
  versioning, and packaging metadata.

Feature development starts from the shared integration source. Release branches should
not independently reimplement a shared feature. They consume a reviewed shared commit by
updating a release reference or merging the same canonical commit.

Release branches may contain line-specific fixes only when the affected behavior truly
belongs to that runtime. Such a change must state why it is not shared.

## Release Manifest Contract

Each release line declares the shared core and runtime profile independently:

```json
{
  "release_line": "1.x",
  "version": "1.5.0",
  "shared_core_ref": "<reviewed-git-commit>",
  "runtime_profile": "full-using-mindthus",
  "package_identity": "mindthus"
}
```

```json
{
  "release_line": "2.x",
  "version": "2.0.0-beta.N",
  "shared_core_ref": "<same-or-newer-reviewed-git-commit>",
  "runtime_profile": "thin-kernel",
  "package_identity": "mindthus-beta"
}
```

The build must materialize `shared_core_ref` from the named Git object or an immutable
source artifact. It must not assume that the current worktree is the referenced version.

The manifest records at least:

- `shared_core_ref`
- shared-core tree digest
- runtime profile and runtime overlay digest
- package identity and namespace adapter
- release version and source commit
- included capability register version
- generated package hashes
- rollback package identity

## Product Release Versus Evaluation Freeze

The 2.x line needs two separate references:

- `shared_core_ref`: the product capabilities intended for the next 2.x package.
- `evaluation_baseline_ref`: the immutable composition used by a named experiment.

The current Beta2 evaluation may continue to use the 1.4.6 baseline. Its manifests,
protocol digests, receipts, and generated package hashes remain unchanged.

After that evaluation closes, a new Beta checkpoint may advance `shared_core_ref`, adopt
new shared capabilities, and produce new package identities. If comparative evidence is
required for that composition, it receives new arm manifests and a new authorization
record. Historical Beta2 evidence is retained rather than rewritten.

## Change Routing

| Change type | 1.x | 2.x | Rule |
| --- | --- | --- | --- |
| Shared feature | include | include at next Beta checkpoint | one implementation |
| Shared bug fix | include | include | same fix and regression test |
| Shared security or evidence fix | expedite | expedite or block affected Beta | no silent lag |
| 1.x routing compatibility fix | include | normally exclude | state 1.x runtime ownership |
| 2.x activation or hook change | exclude | include | requires 2.x runtime evidence |
| Evaluation harness change | exclude | checkpoint only | never presented as product capability |
| Breaking owner-contract change | explicit product decision | explicit product decision | not an automatic backport |

Temporary release lag is allowed. Silent capability divergence is not.

## Capability Register

Maintain a small machine-readable register for shared features that have entered either
release line. A record should contain:

```json
{
  "id": "tvg-profile-atlas-v1",
  "source_commit": "9b2a1793f97a4551a219c21976105a533a0e1d72",
  "ownership": "shared-product-core",
  "release_1x": {"state": "included", "version": "pending"},
  "release_2x": {"state": "queued-next-checkpoint", "version": "pending"}
}
```

Allowed release states should remain small: `not-applicable`, `queued`, `included`,
`blocked`, and `retired`. Every `not-applicable` or `blocked` state requires a reason.

The register is release coordination evidence. It is not a second feature specification
and must not duplicate implementation details.

## Development And Release Flow

1. Classify the change as shared, 1.x runtime, 2.x runtime, or evaluation-only.
2. Implement shared work once against the Shared Product Core.
3. Run shared unit, documentation, packaging, and compatibility tests.
4. Update the capability register with intended 1.x and 2.x disposition.
5. Promote the reviewed `shared_core_ref` independently in each release manifest.
6. Build both packages from their declared core and runtime profile.
7. Run line-specific runtime tests and cross-line shared-capability parity checks.
8. Publish immutable tags and package hashes.
9. Keep an older package and runtime profile available as the declared rollback target.

Urgent 1.x releases do not wait for a Beta checkpoint. The 2.x register remains `queued`
until the next Beta package advances its shared core. Conversely, a 2.x runtime experiment
does not force a Stable runtime change.

## CI And Verification

The CI matrix should include four independent lines:

1. **Shared-core tests**
   - owner skill and Profile contracts
   - shared scripts and schemas
   - documentation and packaging boundaries
2. **1.x package tests**
   - full `using-mindthus` runtime
   - Stable identity, compatibility, and rollback
3. **2.x package tests**
   - Thin Kernel, hooks, isolation, namespace, and ordinary/high-capability model paths
4. **Frozen-evaluation tests**
   - materialize `evaluation_baseline_ref`
   - verify historical arm and protocol digests
   - fail on mutation of frozen evidence, not on unrelated live-source progress

For shared capabilities, CI should compare the assembled package trees after approved
namespace rewriting. A Profile, schema, or deterministic script marked shared must be
byte-equivalent across 1.x and 2.x packages unless a declared packaging transform applies.

Required release gates:

- no missing shared capability without an explicit register state
- no unrecorded runtime-specific delta
- no package built from a dirty or unresolved source reference
- no frozen evaluation artifact rebuilt from the live worktree
- no tag or package digest reused for changed bytes

## Versioning Policy

- Published tags and evaluation checkpoints are immutable.
- Compatible 1.x features normally advance the minor version; compatible bug fixes
  normally advance the patch version, subject to the repository's release policy.
- 2.x capabilities enter the next Beta/RC identifier; an existing Beta artifact is not
  silently republished with new bytes.
- Product capability version and runtime architecture version are recorded separately.
  A 2.x package may use the same Shared Product Core as a 1.x release while exposing it
  through a different runtime profile.

## Migration Plan

### Phase 0: Preserve Current Evidence

- Keep `v1.4.6` immutable.
- Keep the current Beta2 evaluation refs, manifests, protocols, and receipts immutable.
- Do not push the failed direct #120 Beta cherry-pick as a releasable branch.

### Phase 1: Separate References

- Add `shared_core_ref` to 1.x and 2.x release profiles.
- Add `evaluation_baseline_ref` to the Beta evaluation configuration.
- Change reference validation to read the named Git object or immutable artifact.
- Stop comparing the frozen baseline digest with the live repository tree.

### Phase 2: Add Runtime Assembly

- Make the release builder compose Shared Product Core plus one runtime profile.
- Keep 1.x full entry files and 2.x Thin Kernel files in explicit overlays.
- Add cross-package parity checks for shared paths.
- Add the capability register and release-state validation.

### Phase 3: Promote Shared Capabilities

- Use #120 commit `9b2a1793` as the first shared-capability migration case.
- Build and test the next 1.x package with the Stable runtime profile.
- After the current Beta evaluation closes, advance the next 2.x checkpoint to the same
  shared capability and build it with the Thin Kernel runtime profile.
- Record any temporary lag rather than copying or rewriting the feature.

### Phase 4: Release Rehearsal

- Build both packages from clean checkouts using only manifest references.
- Install each package in an isolated host environment.
- Run shared feature smoke tests plus line-specific activation tests.
- Verify package hashes, rollback, namespace isolation, and capability register closure.

## #120 As The Acceptance Case

The TVG Profile atlas workflow is a useful first proof because it is clearly shared:

- its Profile semantics, atlas contract, lineage scripts, documentation, and tests do not
  depend on the full or Thin Kernel entry path;
- its canonical implementation is commit `9b2a1793`;
- the Stable tree passed 611 tests after implementation;
- a direct Beta cherry-pick reached the Beta release lock and failed only because the
  live TVG tree no longer matched the frozen 1.4.6 digest.

The dual-release design is accepted only when the same #120 implementation can appear in
both assembled packages while the historical Beta2 evaluation package still reproduces
its original digest.

## Acceptance Criteria

- one canonical Shared Product Core implementation serves both release lines
- 1.x and 2.x packages can reference the same shared commit
- runtime differences are isolated to declared overlays
- current Beta2 evaluation artifacts remain reproducible and unchanged
- shared features and fixes have explicit per-line release states
- package construction does not depend on the live worktree matching an old baseline
- CI detects both accidental capability divergence and accidental evaluation mutation
- #120 packages and tests pass in both release compositions without source duplication
- rollback identifies a concrete prior package and runtime profile for each line

## Deferred Decisions

The following choices should be made when the current Beta evaluation closes:

- exact permanent branch names
- the next 1.x and 2.x release numbers
- whether `main` immediately becomes the shared integration branch or transitions after
  one release cycle
- the storage location and schema name of the capability register
- whether the next 2.x checkpoint requires a complete comparative rerun or a bounded
  regression authorization

These choices do not change the central architecture: shared capabilities remain single
source, runtime profiles remain separate, and frozen evaluations remain immutable.
