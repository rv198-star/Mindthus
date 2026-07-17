# Beta.2 #119 execution authorization gate

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

The real #119 executor must require a passing authorization report before the first
generator call. A blocked packet cannot be bypassed by reducing the case set, omitting
judge records, changing the model, or treating visible development cases as blind.
