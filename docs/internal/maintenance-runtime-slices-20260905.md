# Runtime Maintenance Slices — 2026-09-05

Parent #167. Each slice is a behavior-preserving move; semantic fixes are separate.

## SRA slice 1 (#171)

Baseline: 99c4cb23 (same SRA behavior as dependency fix 749b9a33).

- `sra_views.py` owns candidate/bundle normalization and typed comparison.
- `sra_serialization.py` owns canonical JSON and hashing used by both packets and views.
- Existing public `sra_runtime` and `sra_runtime_core` names re-export the same function
  objects. No copied implementation, wrapper decision, or reverse import to the facade.
- `sra_structure.py` and `sra_dependencies.py` were already established by the two
  separate defect fixes, not silently introduced as refactoring behavior.

Review evidence: all seven moved function ASTs were compared with their definitions in
`git show 99c4cb23:skills/sra/scripts/sra_runtime_core.py`; every AST is identical, ignoring
location and comments. This is a one-time move proof, not a permanent test tied to old
source layout. Existing agreement/conflict/hash/alias/repair tests remain the regression
owner. The first focused rerun contains 131 passing tests.

The core loses 198 definition lines and gains two explicit imports. This is not completion
of every #171 checkbox: packet/input/schema generation/carrier and larger integrity
organization remain separate follow-on slices. No same-wording conflict behavior was
changed. Code size alone is not the acceptance criterion.

## TPlan

Not yet changed in this record. Pure extraction will precede any transaction/authority
move; new implementation files must be added to the runtime manifest and fingerprints.
