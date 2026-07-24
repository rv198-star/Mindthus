# TPlan Runtime Provenance

## Core

A newly initialized Mission pins the TPlan runtime that created it. Supported Mission
mutations and renderers compare that recorded fingerprint with the runtime currently
executing. A mismatch is a selection/configuration error, not permission to reinterpret
or rewrite the Mission.

The fingerprint records:

- package version and source id
- canonical skill root and script root
- a build hash over the runtime manifest and declared runtime scripts
- trace, renderer, provenance, and doctor capability versions
- the declared capability set

`runtime_provenance` is script-owned and immutable. Business-state mutations must not
edit or replace it.

## Mainline

Initialize normally:

```bash
python3 skills/tplan/scripts/init_mission.py ...
```

Before a risky mutation, release handoff, or when more than one TPlan installation may
be discoverable, run:

```bash
python3 skills/tplan/scripts/runtime_doctor.py "$MISSION_DIR" \
  --selected-root /path/to/selected/skills/tplan \
  --installed-root /path/to/installed/skills/tplan
```

Use `--candidate-root` repeatedly with `--no-default-discovery` for a deterministic
fixture or controlled preflight. Use `--selection-mode discovery` only when no runtime
has yet been selected; multiple distinct roots then fail as genuinely ambiguous.
With `--selection-mode explicit`, multiple roots are still reported, but an explicit
compatible selection is not mislabeled as unresolved discovery.

Interpret the Mission/runtime result as follows:

| Status | Meaning | Supported mutation | Read-only render | Terminal handoff |
| --- | --- | --- | --- | --- |
| `exact` | Recorded and selected identity match | allow | allow | allow |
| `compatible_relocated` | Same build and capabilities at a different canonical path | allow with warning | allow with warning | allow with warning |
| `legacy_unpinned` | Old Mission has no creator fingerprint | first unguarded mutation adopts current runtime with warning | allow with warning | allow with warning |
| `legacy_adopted_exact` | A later runtime pinned a legacy Mission; original creator is unknown | allow with warning | allow with warning | allow with warning |
| `legacy_adopted_compatible_relocated` | A later runtime pinned the Mission and the same build now runs from another canonical path | allow with warning | allow with warning | allow with warning |
| `incompatible` | Version, source, build, or capability identity differs | reject before write | allow only as diagnostic output | reject before replacing artifacts |

Legacy adoption cannot happen inside a protected interaction-guard mutation. Resolve
the guard under a runtime whose provenance is already known, or perform an explicit
recovery outside that protected mutation.

The provenance preflight is shared by every canonical writer: Mission transactions,
evidence, execution trace, step logs, log archives, interaction guards, and Codex
telemetry state/coverage. A writer may delegate to that boundary, but it must not
perform an artifact write before the boundary succeeds.

## Guardrail

This guardrail protects the normal mutation and terminal-render mainline from stale
same-name skills, partial installations, and incompatible runtime copies. The doctor
reports:

- every distinct canonical candidate and its configured aliases
- explicit selected path versus expected installed path
- duplicate or ambiguous same-name runtime roots
- missing manifest, renderer, or required scripts
- incompatible trace/render capability versions
- Mission fingerprint mismatch

For a pre-manifest runtime, the doctor keeps the missing-manifest error but separately
reports filesystem-probed capabilities. Identity is read from the enclosing Git
checkout when available: exact commit, `git describe`, dirty state, repository root,
and a release version parsed from the tag. A version-shaped path is only a fallback
when Git metadata is unavailable; otherwise identity is explicitly `unavailable`.
Git/path fields are diagnostic observations, not a verified release manifest or
compatibility proof.

Ordinary rendering remains available for diagnosis when a Mission fingerprint is
incompatible. `--completion-handoff` is stricter: it fails before writing
`reports/execution-cost-tree.md` or its SVG sidecar, so a stale/custom diagram cannot
silently replace the current terminal handoff.

## Recovery

1. Remove or disable the stale duplicate skill path from the active Codex profile.
2. If duplicates are intentional, validate the intended installed release with an
   explicit `--selected-root`, then execute the mutation/render script from that same
   absolute skill root.
3. Restore any missing renderer/runtime files from that same release; do not mix files
   from different versions.
4. Re-run `runtime_doctor.py` against the Mission.
5. Continue only when status is `ok`, or when a `compatible_relocated` warning is
   understood and intentional.

For example, after the doctor selects `/opt/mindthus/skills/tplan`, run the renderer
from `/opt/mindthus/skills/tplan/scripts/render_execution_cost_tree.py`; do not fall
back to an unqualified same-name discovery.

Do not repair a mismatch by copying the current fingerprint into `mission.json`. That
would erase the evidence being checked.

## Boundary

Runtime provenance provides detection and fail-closed rejection only through supported
TPlan scripts. It cannot prevent an arbitrary process from writing `mission.json`,
execution traces, or report files directly. Preventing such writes requires a
host-enforced sole-writer boundary, filesystem sandbox, or equivalent platform control.
