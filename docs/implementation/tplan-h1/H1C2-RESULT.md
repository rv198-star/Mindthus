# H1-C2 controlled business acceptance — synthetic kernel result

Implemented for [Mindthus #241](https://github.com/rv198-star/Mindthus/issues/241),
on `feat/tplan-h1c2-20261021`, baseline
`ccb05ba8c3a8f5fac6bec1c47de069b24132ff60`. Contract and RED fixtures were committed
first in `fc4e815`. Implementation: `78dd0f8f32de5f3287d4a7c494d4a22dd78c5ea7`.
Build: `sha256:6cd8017008a6c914964b895d154020ab0a2f7461fa3dd9214879d0a98a775512`.
Runtime candidate: `1.6.0-h1c2.1`, capability
`scoped_task_completion`. This is an unpublished candidate awaiting independent
Draft PR review, not an enabled Host deployment.

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
- Same command replay returns history. A different completion command conflicts.
  Prepared recovery rolls forward the original event/state/result without a second
  review. Terminal late native results remain facts and cannot reopen authority.

## Runtime support / validation

| Check | Result |
|---|---|
| Frozen failure baseline | 13 tests: 12 expected failures, 1 pass before runtime edits |
| Final C2 tests + clean package test | 17 passed (16 C2 cases plus five-layout packaging case) |
| Python 3.12 full repository regression | 1313 run: 1306 passed, 7 skipped, 0 failed |
| AIWork existing Node admission and Q1/Q2 consumers | 17 passed; synthetic temporary Missions only |
| Five extracted package layouts | Same build fingerprint; no test signer; new actions live-disabled |
| Fidelity/SELA/MPG primitive smoke checks | Passed |

Exact commands, counts, skip reasons, build fingerprint and log hashes are in
[evidence/H1C2-VERIFICATION.json](evidence/H1C2-VERIFICATION.json). The final full
suite uses `TMPDIR=/var/tmp`, preserving the pre-existing host `/tmp/.git` marker.
The environment has Python 3.12; Python 3.11 CI is not claimed as locally verified.
Seven unrelated dependency skips require jsonschema/Pillow; they are reported,
not presented as passes.

## Boundary / remaining acceptance

`_trust_config()` remains `None`. Only tests supply synthetic signing roots; shipped
code provides no signer, key/secret path or environment-selected trust. Host MAC
verification does not establish real reviewer identity, native delivery authenticity
or Agent-inaccessible storage. Those live admission requirements remain with AIWork
#158/#167. No real DSH/Web/IM E2E, production authentication or real Mission business
acceptance has passed here. Bounded synthetic kernel closure is the demonstrated
result. Independent review is still required before merge.

No deployment, installed Skill edit, production key use, real Mission run, release
or merge was performed. #124 remains HOLD. No second completion state machine,
queue, database, new dispatch or slot-release mechanism was introduced.

Freeze probe: the artifact is a synthetic kernel implementation and evidence package;
its next consumer is the independent reviewer. Green tests authorize review of this
candidate, not live Host enablement or external business acceptance.
