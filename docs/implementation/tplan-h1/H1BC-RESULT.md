# H1-B/C core result — bounded candidate, not full H1-C delivery

Implemented on `feat/tplan-h1bc-20261021`, baseline `fe9fc239`.
Frozen implementation: `5eff0f98136832a374b9b1eee8d719cd2bff46a1`.
Runtime candidate: `1.6.0-h1bc.1`.
Build: `sha256:558a9dac551bd5084a7d3f1bda23d1461b29755f939d079bab29db0788448101`.

The same opt-in canonical Mission now supports actual content-addressed candidate
bytes, scoped waiting, signed Owner decision/revision/nonce semantics, bounded v2
request revision and v1 withdrawal, current adoption, unique kernel claim and native
receipt facts. B waits until A has completed and its adopted input has qualified acceptance; it
cannot launch merely because Owner signed. Independent C proceeds. Source ancestor contracts
and partially scoped failure evidence are protected. Claimed/unknown slots retain
native `session-UUID` / UUID identities and are never freed for automatic redispatch.

**Live Host remains disabled. Full H1-C business completion is NOT delivered.**
The shipped root is None; no caller can supply a verifier secret/key path, and no
runtime signer exists. Test HMAC roots/signers are synthetic, isolated under tests,
and absent from packaged Skills. Local file mode is not proof of Member storage
isolation. No real Owner/Web/IM authentication or native dispatch is certified.
Generic B business acceptance/completion remains fail-closed. The next bounded work
is [H1C2-COMPLETION-PLAN.md](H1C2-COMPLETION-PLAN.md), under #236; no new issue was filed.
AIWork #158/#167 handoff is [AIWORK-158-INTEGRATION.md](AIWORK-158-INTEGRATION.md).

Validation on the frozen source:

| Check | Result |
|---|---|
| Python 3.12 full local suite, TMPDIR=/var/tmp | 1297 run: 1290 passed, 7 skipped, 0 failed |
| Directed H1/gates/recovery/provenance/query/pack/release tests | 119 passed, including 32 new core tests |
| AIWork existing Node admission + Q1/Q2 consumer | 17 passed; synthetic Missions only |
| Five clean extracted candidate package layouts | PASS; H1 module included, test signer absent, unconfigured Host disabled |
| Primitive smoke validation | PASS |

All final non-passed items are seven environment skips: two Case Prep JSON schema
checks require jsonschema; the generated atlas packaging test and four TVG atlas tests
require Pillow. Exact test names/reasons and hashes are in
[evidence/H1BC-VERIFICATION.json](evidence/H1BC-VERIFICATION.json). Exact Python 3.11
CI was not available locally; no Python 3.11 PASS is claimed.

An initial full run encountered `workspace_has_project_ancestor` in older slim tests
because the host already has `/tmp/.git`; no host marker was removed. The affected
16-test group passed with TMPDIR=/var/tmp, as did the final complete suite. Earlier
full runs stopped for incoming source corrections are not counted as PASS.
All required RED logs are retained beside the final GREEN logs, including dependency,
request.revise, native ID and independent-review P1/P2 counterexamples.

No real Mission, installed Skill, production credential, OCI operational tree, main
or release was changed. Nothing was deployed or published. #124 remains HOLD.
