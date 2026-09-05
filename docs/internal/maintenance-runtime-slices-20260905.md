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

The core loses 198 definition lines and gains two explicit imports. No same-wording
conflict behavior was changed. Code size alone is not the acceptance criterion.

## SRA slice 2 / #171 closeout

The second slice moves the remaining high-cohesion runtime surfaces without changing
judgment semantics:

- `sra_packets.py` owns context admission, candidate-context weighting, state projection,
  challenge alias construction, base/coverage/challenge/situated packets, and targeted
  reconciliation packet construction.
- `sra_carriers.py` owns stage prompts, output-schema dispatch surfaces, ephemeral CLI
  command generation, observable receipt storage, context-boundary reporting, and final
  decision copies.
- `sra_io.py` owns the single SRA error hierarchy, JSON/JSONL persistence, run-state
  loading, and deterministic trace-event identity.
- `sra_runtime_core.py` is now the bounded contract-validation owner: input contract,
  output schemas, bundle/allocation/domain invariants, and judgment validation. It no
  longer owns packet construction, carrier orchestration, comparison normalization, or
  runtime persistence primitives.

The reconciliation packet moved with the packet owner after the first extraction exposed
its hidden dependency on `_packet`; the focused suite failed before that correction and
passed after the ownership boundary was fixed. Public `sra_runtime` continues to re-export
the existing names. Runtime-integrity code imports packet and carrier owners directly,
so it does not rely on a reverse facade import. All seven split helper modules are present
in all five release-pack layouts.

Final #171 verification on this slice: 160 focused SRA tests passed; the complete suite
ran 1037 tests with 5 documented optional-dependency skips; Test Lifecycle remained
77/77 valid. `sra_runtime_core.py` is 2033 lines after extraction, down from 3174 at the
maintenance baseline. Remaining size is contract validation rather than mixed packet,
carrier, comparison and IO ownership, so #171 stops here rather than splitting one
validation algorithm into arbitrary small files.

## TPlan slice 1 (#172)

- `tplan_identity.py` owns manifest loading, fingerprinting and provenance inspection.
- `tplan_errors.py` owns the single TplanError class, directly re-exported by the runtime.
- `execution_time_metrics.py` owns pure timestamp conversion, interval union/clipping,
  elapsed reconciliation and token subset counting.
- Mission reads, journal recovery, locks, authority receipts and mutation orchestration
  remain in their original owner. No runtime fingerprint compatibility rule is relaxed.

One-time AST comparison: nine identity functions, the error class and nine metric
functions are identical to their original definitions. `runtime_skill_root` now defaults
to the new module's file in the same scripts directory, producing the same skill root.
The runtime manifest includes all three new modules in required_scripts and fingerprint_files.
A regression deletes and modifies each module in a temporary skill copy, verifying missing
modules block and modifications alter build_hash; restored bytes recover the exact hash.
The original public import still refers to the same function/error objects.

Focused TPlan suite: 364 tests passed. Existing transactional late-failure and recovery
fault-injection tests remained unchanged and actually executed. Core definition lines moved:
352 from tplan_runtime (8 import lines added), 109 from execution_cost_tree (7 added).
This closes the first slice only. SVG/Markdown presentation and additional core breakup,
followed by transaction-owner extraction, remain open in #172.
