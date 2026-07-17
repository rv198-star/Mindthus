# Mindthus 2.0.0-beta.1

This is an opt-in functional prototype, published as `mindthus-beta` alongside the
stable `mindthus` identity. It tests one change: keep a small passive obligation Kernel
in session context, route clear cases directly to a concrete owner skill, and use
`using-mindthus` only for genuine arbitration. Beta 1 is not a release candidate and
does not run the quality, recall, token, or latency A/B; that work starts in Beta 2.

## Runtime boundary

- Active Beta runtime: `runtime/passive-activation-kernel.md`, the SessionStart hook,
  `skills/using-mindthus/SKILL.md`, and `scripts/check-beta-runtime.py`.
- Active owner skills: 1.4.6 contracts with a package-time coordinate-only adapter from
  `mindthus:*` to `mindthus-beta:*`. Source contracts remain unchanged and are locked by
  `reference/1.4.6/reference-lock.json`.
- Stable methodologies, the old `using-mindthus`, and Stable runtime scripts remain
  under `reference/1.4.6/`. They are reference-only and are not active Beta routers.
- The host enforces only SessionStart injection. Before-route and before-answer are
  model obligations; there is no host-enforced before-answer sentinel in Beta 1.
- Stable and Beta may be installed together, but they must not be enabled in the same
  host environment. Co-enabling injects two routers and invalidates Beta isolation.

## Isolation before activation

- Codex: use a dedicated `CODEX_HOME` containing only `mindthus-beta`. The current Codex
  plugin CLI has no plugin-disable command, so a shared active home is not a supported
  Beta 1 path. Keep the normal Stable home untouched for rollback.
- Claude Code: Stable may remain installed, but disable `mindthus@mindthus` before
  enabling `mindthus-beta@mindthus-beta`.
- If both `mindthus:*` and `mindthus-beta:*` skills are visible, stop. Do not evaluate
  Beta behavior or cost in that session.

## Codex activation

Installing a plugin does not automatically trust its bundled hooks.

1. Enter a dedicated Beta `CODEX_HOME` and install the separate `mindthus-beta` plugin.
2. Run `/hooks`, review the Beta SessionStart hook, and trust it.
3. Start or clear a session so the trusted hook can inject the Kernel.
4. From the installed plugin root, run:

   `python3 scripts/check-beta-runtime.py --inspect-host --require-isolated --hook-state fired --require-passive`

The diagnostic cannot inspect Codex's hook trust store, so pass `fired` only after the
host event is observed. With `--inspect-host`, it reads the current host's plugin list to
verify that Beta is enabled and Stable is absent or disabled. It independently hashes
the generated manifest and hook carrier, then executes the known hook and checks that it
emits the exact packaged Kernel. This proves package/carrier function and host isolation,
not model behavior.

## Status meanings

| Diagnostic state | What is established |
| --- | --- |
| `reported-fired-carrier-verified` | The known carrier emits the exact Kernel and host firing was reported. |
| `carrier-verified-not-observed` | The carrier is verified and trust was reported, but host firing was not observed. |
| `degraded` | Direct owner discovery remains; passive Kernel recall is unproven. |

Isolation is reported separately as `isolated-observed`, `isolated-reported`,
`unverified`, `beta-inactive`, or `conflict`.
None of these states proves better answer quality, owner hit rate, lower token use, or
lower latency. Beta 1 deliberately leaves those claims unproven and defers A/B work to
Beta 2.

## Rollback and known limits

For Codex, leave the dedicated Beta `CODEX_HOME` and return to the normal Stable home.
For Claude Code, disable Beta and re-enable Stable. Beta 1 validates the Bash
SessionStart carrier on macOS and Linux. A Windows hook command is not implemented.
