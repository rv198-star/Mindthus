# TPlan Runtime Split Closeout — 2026-09-05

Parent #167, work item #172. This maintenance change separates high-cohesion pure and presentation surfaces while deliberately keeping the transactional Mission state machine under one owner.

## Final ownership

### `tplan_identity.py`
Owns runtime manifest loading, build fingerprinting, compatibility, provenance inspection, and runtime-source identity.

### `tplan_task_contract.py`
Owns task enums, task normalization, task input loading, acceptance-string parsing, and initial Mission Markdown formatting. These functions do not mutate Mission state.

### `execution_time_metrics.py`
Owns timestamp conversion, interval union/clipping, elapsed reconciliation, and token subset counting.

### `execution_svg_renderer.py`
Owns the SVG implementation for Standard/Audit execution-cost presentation. `execution_cost_tree.render_svg` remains the public compatibility entry and delegates to this module.

### `execution_markdown_renderer.py`
Owns Compact text, Markdown, JSON rendering, coverage/runtime diagnostic text, and telemetry coverage tables. Existing public render names remain available from `execution_cost_tree`.

### `tplan_runtime.py`
Retains Mission schema validation, persistent state, lock/journal recovery, authority receipts, interaction guard, re-entry, task mutation, evidence/event mutation, Pulse/decision application, and execution trace writes. These operations share Mission state and failure-atomicity requirements; splitting them further in this campaign would distribute one state machine across files without reducing semantic coupling.

### `execution_cost_tree.py`
Retains trace reading/validation, telemetry interpretation, lifecycle reconstruction, cost aggregation, node/tree construction, and small presentation helpers used by the two renderer modules. Large SVG/Markdown bodies no longer live here.

## Provenance and compatibility

Every extracted implementation module is listed in both `required_scripts` and `fingerprint_files`. The runtime-provenance regression mutates and removes each split module in a temporary skill copy: modification changes the build hash, removal blocks fingerprint construction, and byte restoration restores the original hash. `tplan_runtime.normalize_task` is the exact imported task-contract function, preserving the public import surface.

Physical refactoring changes the TPlan build fingerprint as intended. No compatibility bypass was added for Missions pinned to a different runtime. Existing relocation rules remain unchanged.

## Renderer equivalence

Before removing the large bodies from `execution_cost_tree.py`, Compact, Standard and Audit reports from the deterministic execution-cost fixture were rendered through both the existing functions and the extracted modules. Compact text/Markdown and Standard/Audit SVG/Markdown were byte-identical. The existing execution-cost and telemetry test suites then executed through the public compatibility entrypoints after extraction.

## Size and stopping point

Maintenance baseline:

```text
tplan_runtime.py          6800 lines
execution_cost_tree.py    3607 lines
```

After the two approved extraction slices:

```text
tplan_runtime.py          6288 lines
execution_cost_tree.py    2470 lines
```

The line reduction is an observation, not the acceptance criterion. The stopping rule is ownership: remaining large sections are cohesive state-machine or cost-tree construction algorithms protected by transaction/recovery and trace-contract tests. Further splitting requires a new concrete maintenance problem rather than a line-count target.

## Verification

The final focused TPlan run executed 364 tests successfully, including runtime provenance, persistence late-failure/recovery cases, execution-cost rendering, Codex telemetry activation/adapter behavior, Mission state and interaction guards. Full repository, lifecycle, release-pack and `git diff --check` gates are required before the closeout PR merges.
