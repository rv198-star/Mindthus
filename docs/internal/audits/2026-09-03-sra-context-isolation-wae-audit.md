# SRA Context-Isolation WAE Audit — Superseded

Date: 2026-09-03
Issue: #157
Status: **SUPERSEDED BY ROOT-CAUSE REPLACEMENT**

This audit evaluated the earlier linear runtime:

```text
blind judgment -> state-aware override
```

The audit evidence remains useful as a record of why packet binding, context admission,
source references, read-only carriers, and TPlan separation were introduced. Its final
architecture verdict is no longer current.

A later review found that the linear topology created a new anchor: the situated/state
judgment received the blind result and was required to preserve or overturn it. It also
allowed candidate input fields to disclose semantic roles before SRA judgment.

The canonical replacement is:

```text
shared decision base
    -> independent de-anchored challenge
    -> independent situated judgment
    -> typed comparison
    -> one targeted reconciliation only on material conflict
```

Current audits:

- `2026-09-03-sra-dual-view-priority-audit.md`
- `2026-09-03-sra-dual-view-wae-architecture-audit.md`

Current design:

- `docs/superpowers/specs/2026-09-03-sra-context-isolated-runtime-design.md`

The retained claim ceiling is unchanged: packet and carrier integrity do not prove
complete context, absence of hidden host context, correct semantic priority, or optimal
ROI.
