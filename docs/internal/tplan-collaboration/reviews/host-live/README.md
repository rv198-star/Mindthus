# Live host acceptance evidence

Result: **PASS for the ordinary local-account A/B/C loop**, completed on 2026-11-18
in the client's Asia/Shanghai timezone. Code under test:
`223b7d2b99969c6a6ee9549730d2b8a2271d2401`.

Evidence class: `live_host_bounded_canary_exercise`. A, B and C are real Codex chats;
B/C produced actual files, ran their own tools and returned ordinary messages. The
legacy canary and first-send result withholding are deliberate test faults. The old
Qwen/provider failure and immediate R2 history-index lag were observed host events.

## Evidence map

- `source-world.json`: actual chat identities, code revision, original paths and timezone.
- `input/`: the fixed contract and deliberately faulty initial canary.
- `frozen/r1`, `frozen/r2`: exact byte copies of B's delivered artifacts and self-checks.
- `c-out/r1`, `c-out/r2`: actual independent C drivers, reports, results and logs.
  R1: 337 cases, 151 failures. R2: 443 cases, all passed, including the original
  337 cases. B's 381 tests overlap and are not added to the independent count.
- `audit/native-*.json`: native thread/turn/input/return/tool records, with reasoning
  items omitted. These establish actual peer execution and origin association.
- `audit/host-events.jsonl`: A's actual choices, requests/results and before/after state;
  `source-support.py` is the support code used by A, not a preset autonomous solver.
- `audit/actual-sol-model-recovery.json`: old failed Qwen context, then the verified
  fresh Sol/high turn and actual execution. No global model configuration was changed.
- `audit/host-capabilities.json`, `audit/peer-access-observations.json`: actual host
  capabilities and scoped B/C compliance. Physical isolation, native transport
  deduplication and real cancellation were not exercised as guarantees.
- `audit/closeout-decision*.json`, `audit/final-check.json`, `audit/final-summary.json`:
  source Mission Review, normal runtime completion and final acceptance state.
- `mission/`: completed canonical snapshot, evidence, trace and execution report/SVG.
  This is historical evidence, not an active Mission to resume.
- `artifact-index.json`: original references mapped to byte-preserved archive files.

Original temporary paths remain provenance references. B's `b/r1` and `b/r2` map to
identical frozen copies. Source A alone used TPlan during the live exercise.

## Offline artifact recheck

```text
python3 -B docs/internal/tplan-collaboration/reviews/host-live/replay_contract.py
```

This mechanically reruns C's actual R2 driver against the byte-preserved artifact.
Only driver paths change in memory, and new results go to a disposable temporary
directory. The archive and Mission stay read-only. A replay creates no native messages
or new Agent-behavior evidence.
