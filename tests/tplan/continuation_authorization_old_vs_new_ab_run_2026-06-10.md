# tplan Continuation Authorization Old-vs-New A/B Run Packet - 2026-06-10

## Purpose

This packet tests whether the #33 continuation authorization change blocks ungated expensive same-path continuation after late evidence-shape defects.

The claim is narrow: B blocks ungated expensive same-path continuation before another broad rerun. This is not proof that the whole Mission ends earlier; it proves the runtime now forces an explicit authorization record before the costly path can continue.

## Scenario

The replay is based on a PhaseX-style long task where placeholder/sample red-team anchors are discovered near the end of a broad generation/validation run. The candidate bad next move is another expensive same-path continuation without first classifying the evidence-shape defect.

The desired treatment behavior is not automatic stop. A child task may still continue, but the Mission-facing expensive path must expose:

- `evidence_shape_lint`
- `defect_classification`
- `expected_evidence_delta`
- `authorized_action`

## A / Pre-continuation-authorization Baseline

Source snapshot: `be25f48`.

Expected behavior:

- runtime profile: `pre_continuation_authorization`
- same Mission-facing `continue` decision with `path_assessment` is accepted without `continuation_authorization`
- `authorization_latency.expensive_same_path_continue_attempts_before_gate = 1`
- final allowed action: `continue_same_path`

This represents the old risk: plain judgment may eventually redirect, but the runtime does not force an evidence-shape classification before allowing the expensive continuation candidate.

## B / Continuation-authorization Treatment

Source snapshot: current branch after #33.

Expected behavior:

- runtime profile: `continuation_authorization`
- the same ungated `continue` decision fails with `decision missing field: continuation_authorization`
- a second decision passes only when `continuation_authorization.authorized_action = targeted_fix`
- invalid enum values such as an unsupported `defect_classification` are rejected
- `authorization_latency.expensive_same_path_continue_attempts_before_gate = 0`

This proves the treatment blocks the untrusted expensive path and permits a smaller authorized recovery path.

## Deterministic Replay

Simulator:

```bash
python3 tests/tplan/continuation_authorization_ab_simulator.py \
  --source-root <source-root> \
  --output-dir <output-dir>
```

Unit test:

```bash
python3 -m unittest tests.tplan.test_continuation_authorization_ab_simulator -v
```

The test extracts the old baseline with:

```bash
git archive --format=tar be25f48
```

Then it runs `continuation_authorization_ab_simulator.py` against both the old source and the current source.

## Metrics

| Metric | A / Baseline | B / Treatment |
| --- | --- | --- |
| runtime profile | `pre_continuation_authorization` | `continuation_authorization` |
| ungated continue allowed | `true` | `false` |
| missing authorization result | applied | rejected |
| blocked action | `null` | `expensive_same_path_continue` |
| final allowed action | `continue_same_path` | `targeted_fix` |
| expensive same-path attempts before gate | `1` | `0` |
| mechanical score | `0` | `6` |

## Observed Replay Summary

Observed local replay on 2026-06-10:

```json
{"group": "A", "runtime_profile": "pre_continuation_authorization", "ungated_continue_allowed": true, "mechanical_score": 0, "missing_authorization_stderr": "", "expensive_same_path_continue_attempts_before_gate": 1, "blocked_action": null, "final_allowed_action": "continue_same_path"}
{"group": "B", "runtime_profile": "continuation_authorization", "ungated_continue_allowed": false, "mechanical_score": 6, "missing_authorization_stderr": "decision missing field: continuation_authorization", "expensive_same_path_continue_attempts_before_gate": 0, "blocked_action": "expensive_same_path_continue", "final_allowed_action": "targeted_fix"}
```

## Acceptance

The modification is accepted if:

- A allows the missing-authorization continue payload.
- B rejects the same missing-authorization continue payload.
- B accepts the authorized payload with `authorized_action = targeted_fix`.
- B rejects malformed authorization shape or unsupported enum values.
- The result is described as blocking an untrusted expensive path, not as proof of whole-Mission early termination.
