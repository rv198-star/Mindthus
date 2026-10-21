# H1-C2 controlled business acceptance — synthetic kernel result

Implemented for [Mindthus #241](https://github.com/rv198-star/Mindthus/issues/241),
on `feat/tplan-h1c2-20261021`, baseline
`ccb05ba8c3a8f5fac6bec1c47de069b24132ff60`. Contract and RED fixtures were committed
first in `fc4e815`. Original implementation: `78dd0f8`.
Current frozen repair source: `d6f284733aed7fa1c9c900bf71e208560c12aff1`.
Current build: `sha256:7fff3db886a8b3f1cb10c874a9258206966d2f7f5f6b4e8492ed6ee9d122b259`.
Runtime candidate: `1.6.0-h1c2.1`, capability
`scoped_task_completion`. Independent read-only review of HEAD `636a2e2` returned
**REVISE** (session `acps_6db8078d74195cc673b8bb43`). P1/P2 are now repaired with
local regression evidence; independent re-review remains pending. This is an
unpublished Draft PR candidate, not an enabled Host deployment. The historical
review and forwarded findings remain in [the review record](reviews/H1C2-636a2e2-REVISE.md).

## Core / resulting behavior

B can now complete through a separately authenticated business review after the
original native attempt's actual delivered bytes have been saved. Delivery alone
leaves B incomplete. The existing Mission transaction atomically records qualified
`acceptance_passed`, B completed, consumed review event/nonce and historical H1
command result. The original Mission-close path can then close the synthetic
A→Owner→B→accepted B Mission after independent C also meets its own criterion.

## Mainline / implementation

- `result.record` fixes B's bytes, original slot/native session/request/intent and
  delivered fact in the existing candidate store and slot. It does not accept B.
- `task.complete` verifies the separate signed acceptance scope, fixed Host task
  reviewer, exact business criteria, qualified evidence references, current Owner
  decision/revision/adoption and original input/dependency projection. Missing or
  changed bytes, stale intent, substituted native IDs or model/Q2 actor claims fail.
- The original writer receives prepared evidence with both reserved-evidence and
  scoped H1 capabilities. Old writers cannot create B acceptance or completion.
  Mission closure also requires the exact committed completion evidence and refuses
  later B failure even after unrelated positive evidence.
- Mission-close now shares adoption/claim's source-version acceptance projection.
  It requires the current adopted A candidate/SHA/attempt to remain qualified;
  unadopted v2 passes cannot hide v1 failure, and v2 failure cannot invalidate v1.
  Only source-version events are filtered; unrelated C keeps native AC ordering,
  including failures on an AC shared with A. Non-H1 close is unchanged.
- H1 rejects prospective evidence above the existing 4 MiB artifact limit before
  preparing a transaction. Rejection leaves Mission/evidence/trace, command results
  and nonces unchanged; data is retained and the original readers/recovery work.
- Same command replay returns history. A different completion command conflicts.
  Prepared recovery rolls forward the original event/state/result without a second
  review. Terminal late native results remain facts and cannot reopen authority.

## Runtime support / validation

Repair evidence: [H1C2-REVIEW-VERIFICATION.json](evidence/H1C2-REVIEW-VERIFICATION.json).
The original review stays REVISE; these are local repair results, not a new
independent approval.

| Repair check | Result |
|---|---|
| Frozen RED at `02162fc` | 3 tests, 3 expected failures on reviewed source |
| Additional C shared-AC guard RED | 1 expected failure on provisional local aggregation; approach replaced |
| Directed P1/P2 + C guard GREEN | 4 passed |
| Python 3.12 affected regression | **165 passed, 0 failed, 0 skipped**, including 20 C2 cases |
| Python 3.11.17 isolated C2 module at the same frozen repair source | **20 passed, 0 failed**, 11.000 s; previously completed run, no rerun |
| Five extracted package layouts in affected regression | Same current build; synthetic signer absent; live Host disabled |

The existing Python 3.11 log was copied byte-for-byte from OCI-local
`/tmp/mindthus-h1c2-fixed-py311.log` into [the archived log](evidence/h1c2-review-python311.log).
It records Python 3.11.17, 20 tests and OK. Owner supplied the run context:
frozen `d6f2847`, `tests.tplan.test_h1_completion`, OCI-cached
`python:3.11-slim-bookworm`, `--network none`, `--read-only` and a read-only source
mount. This supplements the Python 3.12 regression; it is not a full-suite or remote
CI certification. No tests were rerun for this archival update.

The unchanged full repository suite was not repeated in this repair. The following
results describe the earlier pre-review source only and do not certify the repair:

| Check | Result |
|---|---|
| Original pre-review failure baseline | 13 tests: 12 expected failures, 1 pass before runtime edits |
| Original pre-review C2 + clean package test | 17 passed (16 C2 cases plus five-layout packaging case) |
| Historical pre-review Python 3.12 full suite | 1313 run: 1306 passed, 7 skipped, 0 failed |
| Historical pre-review AIWork Node consumers | 17 passed; synthetic temporary Missions only |
| Five extracted package layouts | Same build fingerprint; no test signer; new actions live-disabled |
| Historical pre-review primitive smoke checks | Passed |

Historical commands, counts, skip reasons, pre-review build fingerprint and log hashes are in
[evidence/H1C2-VERIFICATION.json](evidence/H1C2-VERIFICATION.json). The final full
suite uses `TMPDIR=/var/tmp`, preserving the pre-existing host `/tmp/.git` marker.
That historical full run used Python 3.12. The added Python 3.11 evidence above
covers only the isolated 20-case module; no full Python 3.11 suite or remote CI
result is claimed.
Seven unrelated dependency skips require jsonschema/Pillow; they are reported,
not presented as passes.

## Boundary / remaining acceptance

`_trust_config()` remains `None`. Only tests supply synthetic signing roots; shipped
code provides no signer, key/secret path or environment-selected trust. Host MAC
verification does not establish real reviewer identity, native delivery authenticity
or Agent-inaccessible storage. Those live admission requirements remain with AIWork
#158/#167. No real DSH/Web/IM E2E, production authentication or real Mission business
acceptance has passed here. Bounded synthetic kernel closure is the demonstrated
result. Independent re-review of the repaired frozen source is still required before merge.

No deployment, installed Skill edit, production key use, real Mission run, release
or merge was performed. #124 remains HOLD. No second completion state machine,
queue, database, new dispatch or slot-release mechanism was introduced.

Freeze probe: the artifact is a synthetic kernel implementation and evidence package;
its next consumer is the independent reviewer. Green tests authorize review of this
candidate, not live Host enablement or external business acceptance.
