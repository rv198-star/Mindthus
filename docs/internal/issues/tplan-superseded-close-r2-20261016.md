# #232 / #233: explicit supersession at Mission closure

## Decision replacing the first candidate

The earlier candidate inferred a successor from node order plus shared acceptance IDs. That is insufficient: separate tasks can share AC_GOAL. R2 instead requires the reviewer to declare exact old-to-new Task identities in the ordinary canonical close decision. No separate Task store, replacement registry or change to historical Task status is introduced.

A close decision may include:

```json
{"task_replacements":[{"task_id":"T1","replacement_task_id":"T2"}]}
```

This field is valid only with recommendation=close and the sole mutation set_mission_status=completed. The existing apply_decision writer supplies its reserved decision_applied evidence to the same atomic closure transaction. Only that current decision's mapping is consumed. Prior decisions, ordinary evidence, node order, shared labels, and unrelated accepted Tasks are not replacement authority.

For each declared pair the old Task must remain superseded/success-critical. The target must be completed/success-critical, cover every original acceptance ID and possess current qualified acceptance_passed evidence for those IDs. Normal Mission-wide acceptance and adverse-evidence checks remain unchanged. Unfinished, pruned, abandoned, ambiguous, self-referential, incomplete or unsupported pairs remain blocked. Semantic equivalence of deliverables is still the Coordinator/reviewer's judgment; scripts validate the declared relation and evidence, not meaning.

## Verification

The new tests are unittest.TestCase methods under tests/tplan, not undiscovered module-level pytest functions. The 13-case targeted suite includes the implicit-AC counterexample, stale-decision rejection, invalid pair rejection, evidence failures, and actual official init_lite/add_node/transition/record_evidence/apply_decision/check_mission execution. It preserves T1=superseded while the explicitly accepted replacement permits Mission=completed. No production source or existing business files were changed by those tests.

R1 CI success is retained as historical regression evidence; it did not discover the original seven free test functions. Production application requires the tested R2 commit, source/provenance verification and a recorded explicit T1→T2 close decision. Broader unrelated platform release and UI redesign are not part of this fix.

## Fixed-runtime compatibility

The source manifest explicitly admits only predecessor build `sha256:77c95fe8f3d7d3f503673e8b78f1f8f93ede4587913cb66a5893ed6902ada5c9`. Package, source ID and capabilities must still match, and the current fingerprint must recompute exactly from the actual selected files. This is not a skip-check flag or a model-supplied allowlist. Original Mission provenance remains immutable; compatibility is reported with a warning and both build hashes. Arbitrary builds, fabricated current fingerprints and capability/package changes remain incompatible. The additional five discoverable tests include an actual canonical close of a synthetic prior-build fixture without rewriting its provenance. Total targeted suite: 18 PASS.
