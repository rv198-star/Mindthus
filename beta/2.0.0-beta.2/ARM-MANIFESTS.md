# Beta.2 sealed arm manifests

An arm name is not experimental identity. A Beta.2 run may identify itself as
`stable`, `direct-only`, or `thin-kernel` only through a verified manifest path and its
`identity_digest`.

The manifest binds four different things:

1. the static arm contract in `arm-definitions.json`;
2. the exact plugin tree and package manifest, including its default prompt;
3. the observed host home, config, active Mindthus namespace, hook state, and Beta.1
   runtime diagnostic where applicable;
4. the declared model, reasoning setting, tool surface, and ambient-context ledger.

It does not prove answer quality, recall, latency, or token efficiency. Those remain
Beta.2 behavior measurements behind the later protocol and authorization gates.

## Arm contracts

| Arm | Active namespace | Carrier contract | Runtime diagnostic |
| --- | --- | --- | --- |
| `stable` | `mindthus:` only | Stable 1.4.6 router | Must be absent; the Beta diagnostic does not apply. |
| `direct-only` | `mindthus-beta:` only | Beta hook reported disabled | Must show package/carrier integrity, observed isolation, and degraded passive status. |
| `thin-kernel` | `mindthus-beta:` only | Beta SessionStart reported fired | Must show package/carrier integrity, observed isolation, and verified passive status. |

`direct-only` and `thin-kernel` must use the same Beta package tree. They must use
different host homes. `direct-only` is an ablation for measuring recall loss, not a
candidate product configuration.

## Input spec

The sealer takes a strict `mindthus-beta2-arm-spec-v0.1` JSON object. Paths may be
absolute or relative to the spec file.

```json
{
  "schema_version": "mindthus-beta2-arm-spec-v0.1",
  "arm_id": "thin-kernel",
  "surface": "codex-plugin",
  "plugin_root": "/isolated/packages/mindthus-beta",
  "host_home": "/isolated/homes/thin-kernel",
  "execution_root": "/isolated/workspaces/thin-kernel",
  "host_runtime": {
    "name": "codex-cli",
    "version": "<captured-host-version>",
    "platform": "<captured-os-and-architecture>"
  },
  "host_cli": {
    "name": "codex",
    "version": "<captured-version>"
  },
  "host_config_files": [
    "/isolated/homes/thin-kernel/config.toml"
  ],
  "plugin_list_evidence": "/isolated/evidence/thin-kernel/plugin-list.json",
  "runtime_diagnostic_evidence": "/isolated/evidence/thin-kernel/runtime-diagnostic.json",
  "hook_state": "fired",
  "model": {
    "id": "<frozen-model-id>",
    "reasoning": "<frozen-reasoning-setting>"
  },
  "tools": [
    "read",
    "shell"
  ],
  "ambient_context_files": [
    {
      "kind": "agents-file",
      "id": "workspace-agents",
      "path": "/isolated/workspaces/AGENTS.md"
    }
  ],
  "opaque_context": [
    {
      "kind": "system-context",
      "id": "host-system-context",
      "sha256": "<lowercase-sha256>"
    }
  ]
}
```

Every `AGENTS.md` discoverable from the host home or the execution-root ancestor chain
must appear as an `agents-file`. The package default prompt is discovered and hashed
automatically. Other non-file context is represented by a caller-supplied opaque digest;
the sealer can bind that declaration but cannot independently inspect a host's hidden
system context.

The plugin-list evidence must be saved native JSON from the selected host. Beta arms
also require saved JSON output from the packaged Beta.1 diagnostic, generated against
that isolated host observation. The sealer rejects reported-only isolation,
co-enabled Stable/Beta namespaces, mismatched hook state, or a failed carrier.

## Seal and verify

```text
python3 beta/2.0.0-beta.2/runtime/seal-arm-manifest.py seal \
  --spec /isolated/specs/thin-kernel.json \
  --out /isolated/manifests/thin-kernel.json

python3 beta/2.0.0-beta.2/runtime/seal-arm-manifest.py verify \
  /isolated/manifests/thin-kernel.json

python3 beta/2.0.0-beta.2/runtime/seal-arm-manifest.py verify-set \
  /isolated/manifests/stable.json \
  /isolated/manifests/direct-only.json \
  /isolated/manifests/thin-kernel.json
```

Write the sealed manifest outside the measured plugin tree. `verify` re-reads every
file receipt and rebuilds the manifest; package, host config, plugin list, diagnostic,
or declared file-context drift invalidates it. `verify-set` additionally requires a
complete three-arm surface, unique host homes, and byte-identical Beta package trees
between `direct-only` and `thin-kernel`.

The manifest has no timestamp, run result, or free-text variant label. Re-sealing the
same evidence produces the same digest. Run artifacts may record time separately, but
must refer back to the immutable manifest path and digest.
