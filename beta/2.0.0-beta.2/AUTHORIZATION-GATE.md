# Beta.2 #119 execution authorization gate

## Authorized incremental smoke (v0.5)

The earlier design-change instruction did not authorize semantic model calls. William
has now separately confirmed the frozen identifiers and authorized only the initial
five committed batches. The frozen protocol SHA-256 is
`f9bc7232647b02a77c67010a74deff79f205cc99590452c2134c515e252b4336`; the
lock digest is
`8c2d7ddcb1aac478eae31b937afa85a63505d1d4e48f5082781aa6a5c7321713`.

`authorizations/issue-119-codex-v0.5.json` binds only the five-batch Judge-backed
smoke:

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

The retained pre-authorization packet digest is
`c110fb10bfc48f33617071eb9809e301f423ca7593aae968ccf4846f18b99440`;
the active authorization digest is
`813b3cb648768db98d7782c0ddafc77396ac9eeb287586819e3ef5e880b79957`.
`runtime/validate-execution-authorization-v0.5.py` validates the exact configuration,
human evidence, protocol lock, installed Codex runtime, and native sandbox carrier
before returning `authorized`. Any batch after the first five requires another explicit
budget decision; v0.4 authority does not transfer.

### Judge compatibility recovery and second stop

The first v0.5 triplet did reach Judge immediately after its three isolated Generator
calls, which verifies the incremental-controller goal that v0.4 failed to provide. The
three retained outputs consumed 90,100 counted tokens. Both Judge slots then made their
two authorized attempts, but all four requests were rejected before model sampling
because the API-facing Structured Outputs schema contained unsupported `uniqueItems`
keywords. They consumed zero counted tokens, produced no Judge verdict, and no batch
commit was written.

The additive `0.5-judge-compat.1` amendment preserves those outputs and failures. It
removes exactly the two unsupported keywords from the API transport view while keeping
the canonical local validator—including duplicate rejection—and all scoring semantics
unchanged. Its frozen amendment SHA-256 is
`fd5312d66f59a11215bb78929a683cf3c57377d84b3f2d53390ae6d27578efe6`; its
lock digest is
`420e8cb9473c944cd41ca33166a0258f986bb4855d7a2ecefc42a5d44bbad16e`.

No budget was added. The original ceilings remain five commits, 17 Generator calls, 34
Judge calls, and 3,000,000 counted tokens. After the stopped run, 14 Generator calls,
30 Judge calls, and 2,909,900 counted tokens remain. The 30 Judge calls exactly equal
the 30 valid records needed for five commits, so the recovery grants no further retry:
any new Judge failure stops the run.

`authorizations/issue-119-codex-v0.5-judge-compat.1.pending.json` retains the
pre-authorization packet. William subsequently confirmed the exact amendment and lock
digests; `authorizations/issue-119-codex-v0.5-judge-compat.1.json` is now active. Its
configuration digest is
`c7d886513e225c83c11449e1b16efe0d853f31050df5b0adf502a23c41056aa8`.
The active authorization digest is
`3a87294be05939455de1157a1466acdd71710bae30bed852361afe28c7789e5a`.
The no-model preflight validates the three retained outputs, four original failures,
all isolation receipts, compatible transport schema, three sealed arms, and remaining
ceilings. The active validator now permits recovery within those unchanged ceilings.
Recovery still does not authorize release preparation or an architecture conclusion.

The authorized compatibility recovery subsequently completed and atomically committed
the retained first batch. That commit contains three Generator records and six valid
Judge records. It then generated all three answers for batch 2, but stopped before the
first batch-2 Judge call because one answer named its owner as `mindthus-beta:3l5s`.
The frozen contamination rule correctly treated the plugin namespace as an arm-identity
signal. At this second stop the cumulative v0.5 consumption is one committed batch,
six Generator calls, ten Judge calls (including the four original zero-token schema
failures), and 274,864 counted tokens.

### Final authorized Judge-only blinded-view recovery

The additive `0.5-blinded-view.1` amendment reuses the already validated v0.4
de-identification primitive. It removes only experiment identifiers from the copy sent
to the Judge: `mindthus:` and `mindthus-beta:` namespace prefixes are removed while the
owner name is preserved, and explicit arm labels are replaced. Original Generator
answers are never mutated. Exact sensitive-path exposure remains a terminal stop rather
than being silently redacted. Every non-identity Judge view receives a content-addressed
receipt, and the incremental analyzer reconstructs and verifies the same view before a
batch can be accepted.

The amendment binds the one committed batch, all six generated answers, all ten Judge
attempts, the three uncommitted batch-2 outputs, the compatibility stop state, and the
single observed namespace exposure. Its frozen SHA-256 is
`b52bc87e4eec22d01dae62c269768aa7e495b8ee1b077271ade6ce69cfd348bc`; its
lock digest is
`a98ee55e53ad2044431034a714ec49217f6cfdc58bdd644e969c9d2d8eefb6f2`.

No budget was added. Four commits, 11 Generator calls, 24 Judge calls, and 2,725,136
counted tokens remain under the original cumulative ceilings. The retained batch-2
triplet must be reused without regeneration. The 24 remaining Judge calls exactly equal
the 24 valid records still required for five commits, so any further Judge failure
stops the run.

`authorizations/issue-119-codex-v0.5-blinded-view.1.pending.json` retains the
pre-authorization packet. William subsequently confirmed the exact amendment and lock
digests; `authorizations/issue-119-codex-v0.5-blinded-view.1.json` is now active. Its
configuration digest is
`3bda3b701b7fe14f47244c42cb956e7a54e5235d6c3a3898f2da896c68c407ce`.
The active authorization digest is
`7878ac47035c36754876e72b9d4962d18f4e5106db388df2109aa5484ab35765`.
The no-model preflight and all 813 repository tests pass. This is the final v0.5
compatibility amendment: any new infrastructure blocker terminates v0.5, with no
further amendment. The recovery still excludes release preparation and any architecture
conclusion.

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
