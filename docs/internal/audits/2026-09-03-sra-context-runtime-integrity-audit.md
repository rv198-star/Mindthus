# SRA Context-Runtime Integrity Audit — Superseded

Date: 2026-09-03
Issue: #157
Status: **SUPERSEDED BY ROOT-CAUSE REPLACEMENT**

This audit verified deterministic integrity of the earlier runtime:

```text
prepared -> blind_recorded -> finalized
```

Its evidence about packet hashes, reference validation, carrier receipts, mutation
boundaries, and failure-closed behavior remains part of project history. Its state-machine
verdict is no longer current.

The earlier workflow was replaced because it gave the blind result default authority and
made the state-aware judgment explain whether it changed that result. The current
runtime uses orthogonal status fields and two independent views:

```text
coverage: conditional
challenge: independent and de-anchored
situated: independent and action-bearing
comparison: typed agree/conflict
reconciliation: one pass only on conflict
finalization: finalized or blocked
```

Current audits:

- `2026-09-03-sra-dual-view-priority-audit.md`
- `2026-09-03-sra-dual-view-wae-architecture-audit.md`

Current implementation evidence must be recorded against the v0.2 dual-view runtime,
not inferred from this superseded audit.
