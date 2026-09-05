# TPlan Authority Contract Repairs — Implementation Review

Date: 2026-09-05
Scope: #196, #197, #199, #198, in that implementation order.
Design: [frozen repair audit](2026-09-05-tplan-authority-contract-repair-audit.md).
Base: `33e66ad801cee70223ef3d4a931adebc22970a38`.
Final product/test candidate: `45c0ac0b1cdc80465deeb2accba5ad80bf919535`.
Candidate tree: `ec4be361f97780563678c387fc4d5cda35eb2a85`.
Verdict: **PASS for the four frozen deterministic repair contracts; ready for PR review.**
Merge and release are separate actions. #200 remains design-only.

## 1. Review method and evidence boundary

The implementing ChatGPT first wrote failing regressions, applied each repair, ran
focused and repository tests, and then reviewed alternate entry points and failure
boundaries. Review found two additional entry-point gaps, which were reproduced and
fixed before final validation in a fresh worktree at the candidate above.

This is same-assistant implementation review with isolated execution verification,
not an independent-model or fresh-Agent certification. No external reviewer CLI was
used. The original incident archive and admitted observations remain unchanged.

The test module `tests/tplan/test_authority_integrity.py` groups 30 regression methods
under the existing TPlan lifecycle owner. Subtests exercise multiple statuses and
mutation forms; they are not reported as additional real-use samples.

## 2. Delivered invariants

| Issue | Enforcement | Positive/compatibility controls |
| --- | --- | --- |
| #196 | New typed evidence references resolve uniquely against the locked Mission evidence plus same-transaction prepared events before journaling. Standalone trace append reuses the resolver. | Existing and prepared IDs work; artifact refs stay separate; unrelated writes can proceed despite unreferenced historical duplicates. |
| #197 | `add_task_node(status=active)` shares `set_task_status(active)` before one transaction. | Pending additions preserve the cursor; active ancestor/selected leaf and blocked recovery cursor remain supported. |
| #199 | One pure consequence validator is called by the existing shared hook-output validator. Stop/review/audit ceilings reject continue/switch/add and execution-widening/completion mutations. | Consistent continue, targeted fix, batching, narrowing stop and advisory review remain possible; weak ROI/lint is not an automatic stop oracle. |
| #198 | A new Mission completion checks every success-critical node and the latest qualified observation for every acceptance ID under the existing lock. | Stream order, complete legacy acceptance, same-transaction evidence, unfinished supporting work and advisory recommendations remain supported. |

The completion helper uses existing acceptance IDs and evidence events. It introduces
no new acceptance schema or reviewer registry. Missing, wrong-scope, ambiguous-ID or
incomplete observations cannot supply qualified positive acceptance. A qualified
failure later in stream order blocks closure; a later qualified positive observation
can satisfy that condition again. This is not semantic verification of the claim.

## 3. Red-to-green evidence

The original missing-reference and dynamic-activation scenarios failed the new expected
outcome tests before their respective repairs. The continuation matrix reproduced
stop/review plus activation under ordinary application and a correctly bound Guard
receipt. The completion tests reproduced missing acceptance, unfinished critical work,
late adverse evidence and receipt-bound premature closure.

After core implementation, the first whole-TPlan run found seven old fixture failures:
completion helper paths supplied no qualified acceptance, and a lifecycle test referred
to a nonexistent `E-acceptance`. The two existing fixture owners were corrected to
append explicit fixture acceptance events. Their renderer/lifecycle assertions were
preserved. Production checks were not relaxed to accommodate those fixtures.

First whole-repository self-test after those corrections:

- 1077 tests run; 1072 passed; 5 existing optional-dependency skips.
- 79/79 executable test files registered by the existing lifecycle registry glob.

## 4. Review findings and resolution

### R1 — Compatibility writer bypassed canonical completion checks

`write_mission()` described itself as initialization/test compatibility support, but
its existing-Mission branch could directly replace a live snapshot without the
transaction gate or lifecycle effects. A new review regression reproduced premature
completion and the absence of a completion trace.

Resolution: existing-state writes delegate to `_commit_mission_state_unlocked()` under
the existing lock, retaining the explicit Guard prohibition. The same reference,
completion, provenance and lifecycle rules now apply. No second closure check was
created in the compatibility writer. Initial snapshot creation remains a separate
initializer, not a semantic acceptance certification or historical import verifier.

### R2 — Standalone trace append accepted dangling evidence IDs

The standalone append API could persist lifecycle references without going through the
state transaction. The review regression reproduced a dangling typed evidence ID.

Resolution: the append path reuses `_validate_trace_evidence_references()` after shape
validation and under its existing lock. Its supported-write/provenance preparation
runs after input validation and before persistence. The contextual resolver is not
moved into the pure trace-shape validator.

These are integration completions of the frozen invariants, not new authority systems.

### Historical diagnostics

`check_mission.py` reads one locked attribution snapshot after its existing pending
recovery step, then reports `integrity_warning` for unresolved historical references
or a currently unsupported historical completion claim. Warnings do not rewrite the
files or certify acceptance. Shape-check success is explicitly separate from new
completion eligibility. The new test verifies both warnings and byte preservation.

## 5. Final executable verification

All results below bind to the clean product/test candidate named above, not the earlier
working-tree state.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -q
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.tplan.test_authority_integrity -q
python3 scripts/check-test-lifecycle.py --json
git diff --check
PYTHONDONTWRITEBYTECODE=1 python3 data/cases/slidethus-vq-execution-overrun-20260905/reproduce.py
python3 scripts/build-release-pack.py --out <new-temp-directory>/pack --package all
```

Environment: CPython 3.10.12; fresh detached worktree.

| Check | Observed result |
| --- | --- |
| Complete repository suite | 1084 run / 1079 passed / 5 existing optional skips / 0 failures |
| New authority regression module | 30/30 passed |
| Lifecycle registry | 79/79 executable files registered, valid, no findings |
| Git whitespace and fresh worktree | Clean |
| Original bounded packet | 10/10 source file hashes matched; original consent flags preserved |
| Original current-runtime probes | Missing/path-as-evidence refs rejected with no writes; active T6 has matching cursor/event; premature Mission completion rejected with no writes; stop/activation contradiction rejected with no writes |
| Legal probe controls | Existing evidence, artifact refs, pending creation and ordinary activation accepted |
| All release layouts | Built; both changed runtime/check scripts present in all five layouts and byte-identical to source |
| Isolated packaged Python processes | Five imports, provenance fingerprints and deterministic contract probes passed |

Packaged script SHA-256:

- `tplan_runtime.py`: `fa79ca946eda57ed167928e9e1a599872eec1a1aee8c646a7c8d4729b0c354fd`
- `check_mission.py`: `54297a88b53bac22120d252ab2553c7d5b75f15dc4e75cbad862c3eaf3724c0a`

The first package-import verification invocation passed a string to
`runtime_fingerprint`, which expects `Path`. That verification command was corrected;
all five isolated checks then passed. No product change was made for that invocation
error. Build success is not being used as a substitute for the subsequent import tests.

## 6. Atomicity, concurrency and compatibility review

- Rejected new refs, contradictory decisions and ineligible closures leave snapshots,
  trace, evidence and Guard state unchanged in clean fixtures.
- Same-transaction evidence can support the transaction that commits it.
- A journal preparation failure does not leave an orphan node or partial cursor.
- Interrupted qualified closure recovers once from prepared contents; repeated recovery
  leaves stable bytes and exactly one applied decision event.
- Failure appended before commit-lock acquisition prevents closure. A concurrent append
  attempted while closure holds the lock waits until that transaction commits; its
  later failure remains visible and invalidates current qualification, rather than
  being misrepresented as evidence that was available earlier.
- A genuine bound Guard receipt cannot override either completion or continuation
  contradictions; a valid guarded closure succeeds and releases the Guard.
- Existing provenance, Guard, persistence, renderer and installed-runtime regressions
  were included in final repository verification.
- Frozen legacy pending transactions retain their existing recovery behavior. Historical
  reads do not acquire a new verified-acceptance status, and no automatic migration or
  fingerprint rewriting was introduced.

## 7. Claim ceiling and remaining work

This repair establishes the stated deterministic consistency at the covered supported
APIs. It does not prove visual quality, model judgment, the truth of an acceptance
assertion, or an exact historical cause for the Slidethus overrun.

The Codex App / Sol High 16-hour task was not rerun. No claim is made about recovered
hours, Token ROI, hook activation, or prevention of arbitrary external provider calls.
#200 external continuation scope, #140 native enforcement and existing platform E2E
issues keep their separate ownership and approval boundaries.

No SRA method change, new scheduler, new host hook, global budget threshold, release
version update, tag movement or publishing action is included.
