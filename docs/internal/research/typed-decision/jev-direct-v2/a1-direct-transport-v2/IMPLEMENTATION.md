# A1③ bounded execution under the adopted protocol

Parent commit: 62845d9139c701715b875a186695637a434ced76.
The user's current instruction adopts [PROTOCOL.json](PROTOCOL.json) forward only.
It does not qualify earlier requests retrospectively or lift actual safety refusals.

The shared `pilot.host_call` appends the exact seven overrides in the already parsed
[candidate](../host-transport-boundary-2026-09-27/candidate-profile.json) to this CLI invocation.
Model/effort remain gpt-6-sol/xhigh. Official managed authentication and default official
endpoint stay in place; no base_url, credential extraction, global configuration change,
or additional recovery loop. The local full schema and existing API projection remain.
The verified official bounded authentication recovery is allowed to operate; absence of
future 401 cannot be pre-proved and is not a gate. Observed ambiguous recovery requires
request-bound reconciliation before a subsequent dispatch. A successful answer is kept.

`transport_profile.register` appends a technical successor to the existing batch root,
binding the candidate, protocol, implementation, original freeze, previous successor,
and hashes of historical evidence. A1/native remains delivered and used 2/4. Its time
balance is inherited from the prior conservative debit and measured retry session.
A1/direct retains its original 4 calls / 900s host budget and two-layer Jev cap.
Current dispatch scope is only A1/direct; configuration is common to either arm.
The original serial ledger and 60s monotonic cooldown are reused. A batch stop is checked
before any later dispatch when invocation logs show unclassified recovery.

The five new tests cover shared wiring/schema immutability, stop-before-next-dispatch,
unknown underlying counts, unbound 401 and retained protocol boundaries. Fixtures are
not live results. The three config parser runs and seventeen source/evidence checks from
the parent commit were not repeated. No full-repository audit or model probe ran.

Raw logs retain their own counting scopes. Driver retries=0 is not a claim of zero
internal recovery. Generation/HTTP totals or sub-times lacking direct evidence remain
unknown; successful generation supplies a lower bound only. Recovery wall time stays
inside the measured invocation. The old 119s native session is not a matched speed or
cost baseline for this profile. Content comparisons may use the retained actual answers.
