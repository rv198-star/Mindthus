# Beta.2 #119 execution authorization gate

## Pending incremental authorization (v0.5)

The user authorized the v0.5 design change, but that instruction did not authorize new
semantic model calls. The frozen protocol SHA-256 is
`f9bc7232647b02a77c67010a74deff79f205cc99590452c2134c515e252b4336`; the
lock digest is
`8c2d7ddcb1aac478eae31b937afa85a63505d1d4e48f5082781aa6a5c7321713`.

`authorizations/issue-119-codex-v0.5.pending.json` proposes only the five-batch
Judge-backed smoke:

- `gpt-5.6-sol` / `xhigh` for the generator and both isolated Judge sessions;
- five committed case/repeat triplets, containing 15 generation outputs and 30 Judge
  records;
- ceilings of 17 generation calls, 34 Judge calls, and 3,000,000 newly counted tokens;
- William as human adjudicator and stop authority; and
- no release preparation and no architecture, hidden-set, or generalization claim.

The two extra generation calls and four extra Judge calls are infrastructure-failure
headroom; they do not increase the five-commit evidence ceiling. Previous v0.3/v0.4
consumption remains visible in the packet: 146 generation calls, 42 Judge calls, and
8,133,510 counted tokens.

The pending packet digest is
`c110fb10bfc48f33617071eb9809e301f423ca7593aae968ccf4846f18b99440`.
`runtime/validate-execution-authorization-v0.5.py --allow-pending` validates its shape,
while the normal validator exits blocked. Real execution requires William to confirm
the exact protocol and lock digests and authorize the five-batch/17-call/34-call/
3,000,000-token ceiling. Any later batches require another explicit budget decision;
v0.4 authority does not transfer.

## Current visible-case authorization (v0.3)

After the user removed the four sealed-shadow cases, v0.3 replaced—not edited—the
blocked v0.2 execution path. The sealed packet
`authorizations/issue-119-codex-v0.3.json` binds:

- protocol SHA-256
  `ce8c06eb0656e1023de9ff477ab7a0b5a3302194e9e5af952b916130a231b144`;
- 25 visible matched cases, with all four sealed cases and both unauthorized replays
  excluded;
- `gpt-5.6-sol` / `xhigh` for the generator and two isolated judge sessions;
- 225 planned successful generations and 450 planned judge records;
- ceilings of 240 generation calls, 480 judge calls, and 22,000,000 counted tokens;
- William as human adjudicator and stop authority; and
- no release preparation or hidden-set/generalization claim.

`runtime/validate-execution-authorization-v0.3.py` verifies the immutable protocol and
lock, the exact workload and budget, the delegated user decision, the authorization
digest, and the installed `codex-cli 0.144.4` runtime. It returned `authorized` before
the first model call. The authorization was then consumed by the smoke and does not
permit bypassing a frozen veto.

The first smoke cell triggered `missing-primary-native-evidence`: the runtime supplied
usage and lifecycle data but no native timestamp for
`first_useful_action_latency_seconds`. The stop authority was exercised automatically;
no judge or later generation call was made. Resumption under v0.3 is valid only on a
host that supplies the required native event. Redefining or downgrading that evidence
line requires a new protocol version and review.

## Historical sealed-case gate (v0.2)

The Codex-only v0.2 protocol is frozen, but a protocol lock is not permission to make
semantic model calls. `authorizations/issue-119-codex-v0.2.pending.json` binds the
known model, workload, call, token, adjudication, and stop-authority values while
remaining visibly blocked on two facts that cannot be inferred:

1. William must confirm the exact frozen protocol digest after freeze.
2. An independent case custodian must bind the four sealed-shadow receipts to content
   stored outside the implementation repository and attest blindness after freeze and
   before the digest confirmation.

`runtime/validate-execution-authorization.py` validates deterministic facts: protocol
and lock integrity, exact configuration equality, budget equality, timestamp order,
receipt cardinality, content hashes, and storage outside the repository. It does not
prove that a custodian is genuinely independent or that no human leaked content. Those
remain evidence-backed human claims, and the final report must preserve that claim
ceiling.

For an otherwise authorized packet, the CLI path also checks that the installed Codex
runtime still resolves to the frozen `codex-cli 0.144.4` version before returning a
passing report.

Any real #119 executor must require a passing authorization report before the first
generator call. A blocked packet cannot be bypassed by reducing the case set, omitting
judge records, changing the model, or treating visible development cases as blind. A
changed case set must be frozen as a new version, as v0.3 demonstrates.
