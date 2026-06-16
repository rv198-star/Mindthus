# tplan Mission Shared Context Design

Status: approved for implementation
Date: 2026-06-17
GitHub Issue: #49

## Goal

Upgrade TPlan shared context from a risk-only runtime index into a Mission-level memory
surface that survives interrupted work and can be loaded before a Mission starts.

The shared context primary storage is a Markdown file:

```text
<Project>/.tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md
```

`mission.json.shared_context` remains a structured runtime index for script validation,
survey output, decision packets, and active risk consumption. It is not the full memory
store.

## Mission Identity

Mission identity is not a run, directory, branch, or task list. A Mission continues
when objective, acceptance evidence, and authority boundary remain continuous.

Startup choices are:

- `continue_existing`: caller gives a mission id and the existing shared context matches
  the requested Mission snapshot closely enough for scripts to avoid a mechanical
  conflict.
- `create_new`: no matching shared context exists, or caller intentionally uses a new
  mission id.
- `needs_agentic_selection`: no mission id is provided and existing shared contexts may
  be relevant, or a mechanical conflict prevents safe automatic continuation.

Derived work is not a Mission status. A new Mission may declare `source_contexts` such
as old mission ids or context files, but those sources are background memory only. They
do not inherit the old Mission's acceptance authority.

## Shared Context File

The Markdown file is the human/agent memory surface. It should contain:

- Mission snapshot: id, title, objective, acceptance evidence, status, active task.
- Source contexts: prior Mission ids or context files used as background.
- Current state: active node and latest recoverable state when known.
- Shared risks: active and recently resolved risk signals.
- Key findings: durable observations useful beyond one task log.
- Resume notes: what a future agent should load, check, or ask before continuing.

The file may include a small machine-readable metadata block so scripts can validate
mission id, objective, acceptance evidence, and source contexts without parsing prose.
Scripts validate structure only; they do not decide semantic sameness.

## Runtime Behavior

`init_mission.py` and `init_lite.py` gain a project-root-aware startup preflight.

When `--project-root` is supplied, startup must:

1. Resolve the context path under `<Project>/.tplan/shared_contexts/`.
2. If the matching context exists, load its metadata before creating runtime files.
3. If metadata mechanically conflicts with the requested objective or acceptance
   evidence, refuse startup and report a preflight conflict.
4. If the context does not exist, create it for the new Mission.
5. Store a structured index in `mission.json.shared_context`, including `context_file`,
   `source_contexts`, and `risk_signals`.

`record_risk_context.py` continues to write risk signals to the structured index and
evidence stream. When `mission.json.shared_context.context_file` exists, it also refreshes
the Markdown shared context so the memory file reflects current risk state.

## Preflight Command

Add a deterministic preflight command that can be called before initialization:

```bash
python3 skills/tplan/scripts/preflight_mission.py --project-root . --mission-id M1 ...
```

It reports one of:

- `continue_existing`
- `create_new`
- `needs_agentic_selection`

If no mission id is provided, it scans `.tplan/shared_contexts/` and returns candidate
contexts. It must not choose among candidates.

## Boundaries

- Shared context Markdown is not a cross-task transcript.
- Task logs remain task-local and are not copied wholesale into shared context.
- Evidence remains in `evidence.jsonl`.
- Scripts do not infer semantic continuity between Missions.
- Scripts do not auto-close, auto-resume, or auto-select Missions.
- Old `mission.json.shared_context.risk_signals` behavior remains compatible.

## Acceptance Criteria

- A helper resolves the expected project-level shared context path for a mission id.
- Preflight reports `create_new` when no context exists.
- Preflight reports `continue_existing` when a matching context exists.
- Preflight reports a conflict when the same mission id has different objective or
  acceptance evidence metadata.
- Preflight reports `needs_agentic_selection` with candidates when no mission id is
  provided and context files exist.
- `init_mission.py` and `init_lite.py` create/load the Markdown context when
  `--project-root` is provided.
- New Missions may record `source_contexts` without changing Mission status.
- `record_risk_context.py` refreshes the Markdown context after risk update/recovery
  when a context file is indexed.
- TPlan tests cover preflight, initialization, lineage, conflict detection, and risk
  refresh behavior.
