# Mindthus 2.0 Native Thin Router Candidate

Status: `static candidate / not Beta.3 / no live qualification`

This unpublished Codex-only profile tests one successor hypothesis: one natively
discoverable thin `using-mindthus` entry can preserve minimum passive obligations while
concrete Mindthus owners remain directly discoverable from their own descriptions.

The candidate deliberately has no SessionStart Hook, separate Passive Kernel, guard
Skill, model-name route, or plugin default-prompt routing policy. The seven owner Skills
remain locked to the 1.4.6 source contracts with only the existing package-time namespace
adapter.

## Static verification

Build the isolated plugin:

```bash
python3 scripts/build-release-pack.py \
  --release-line 2.0-next-native-thin-router \
  --package plugins \
  --out /tmp/mindthus-native-thin-router
```

Then inspect the built plugin without making a semantic activation claim:

```bash
python3 /tmp/mindthus-native-thin-router/codex-plugin/mindthus-beta/scripts/check-native-router.py \
  --plugin-root /tmp/mindthus-native-thin-router/codex-plugin/mindthus-beta \
  --stable-state disabled \
  --require-isolated \
  --json
```

Passing this diagnostic proves package shape, hashes, namespace isolation, owner-tree
identity, absence of forbidden carriers, and static budgets. It does not prove native
Skill activation, passive recall, owner selection, answer quality, token savings, or
latency.

## Model-free rehearsal checkpoint

The initial N2 rehearsal completed in a temporary `CODEX_HOME` on 2026-07-19:

- the local Codex marketplace registered successfully;
- `mindthus-beta@mindthus-beta` installed as version `2.0.0-next.1`;
- the host inventory contained one enabled candidate and no Stable plugin;
- the installed artifact passed the diagnostic as `isolated-observed` with
  `native_entry_status=packaged-unproven`; and
- no Codex conversation, Generator, Judge, or semantic activation probe ran.

This checkpoint is reproducible package evidence, not native-carrier eligibility.

## Runtime boundary

- Use a fresh isolated `CODEX_HOME` for any later qualification.
- Do not enable Stable and this candidate together.
- Do not run the closed eight-call qualification without William's separate authority.
- Do not publish, tag, promote, or rename this candidate as Beta.3.
- If native activation cannot be observed after the one permitted wording correction,
  stop the route; do not add a Hook fallback.
