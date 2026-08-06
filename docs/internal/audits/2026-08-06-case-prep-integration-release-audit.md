# Case Prep Integration And Release Audit — 2026-08-06

## Scope

Independent review of skill discovery, method-layering compatibility, router ownership,
release packaging, runtime fingerprint coverage, cross-layout execution, TPlan adapter
operation, Test Lifecycle registration, and full regression behavior.

## Findings And Repairs

### 1. Unlayered `Excerpts` H2 violated the skill layering contract

Repair: excerpt rules moved under the `Guardrails` layer with a subordinate heading.

Verification: `tests.test_method_layering_contract`.

### 2. Router tests assumed every `skills/*/SKILL.md` was a judgment owner

That assumption would either force an explicit utility into passive routing or reject
any future non-method tool skill.

Repair: router contract now names `case-prep` as an explicit-only tool skill. It remains
outside the `using-mindthus` owner table and must state its explicit/no-passive-wake
boundary in its own SKILL.

Verification: `test_explicit_only_tool_skills_are_not_passive_router_owners`.

## Cross-layout Release Verification

The release builder was run and actual Judgment case archives were generated in all
supported layouts:

| Layout | Preparation | Archive | Strict runtime fingerprint |
|---|---|---|---|
| Codex plugin | pass | present | `ok` |
| Claude Code plugin | pass | present | `ok` |
| Claude portable skills | pass | present | `ok` |
| Codex portable skills | pass | present | `ok` |
| OpenCode portable skills | pass | present | `ok` |

The Codex plugin layout also initialized a packaged TPlan Mission and generated a
bounded TPlan case packet without copying `mission.json`.

## Runtime And Packaging Coverage

- `case-prep` is included in the Codex plugin skill allowlist.
- Claude and portable packs include the skill through the standard skills tree.
- Runtime diagnostics track the SKILL, preparation core, CLI, validator, and TPlan
  packet schema.
- Package tests execute the generated scripts rather than checking file presence only.
- Claude installer automatically links the new skill; README uninstall instructions
  include it.

## Test Lifecycle

`tests/test_case_prep.py` is registered under the judgment observability/case export
lifecycle owner. The registry covers all 69 executable test files exactly once.

## Complete Verification

```text
Ran 847 tests in 87.976s
OK (skipped=5)
```

Additional release audit output:

```text
codex-plugin     prep=pass archive=present runtime=ok
claude-plugin    prep=pass archive=present runtime=ok
claude-portable  prep=pass archive=present runtime=ok
codex-portable   prep=pass archive=present runtime=ok
opencode         prep=pass archive=present runtime=ok
```

`git diff --check` is required again immediately before commit.

## Non-claims

This audit does not prove:

- automatic redaction quality;
- that an agent selected the most useful case focus;
- semantic correctness of a Judgment Trace or TPlan case interpretation;
- readiness for automatic contribution or centralized telemetry.

## Verdict

Passed after the layering and explicit-tool router repairs. The skill is suitable for
explicit local case preparation and release packaging.
