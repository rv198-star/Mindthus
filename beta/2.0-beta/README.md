# Mindthus 2.0 Internal Beta

Status: internal integration checkpoint; not a GitHub Release or marketplace package.

This checkpoint composes two immutable inputs:

- Shared Product Core: Mindthus `v1.5.0` / `2cd323d4875069bef17b137a6c7dd50bb06680f8`
- Runtime Profile: ROI.2 implementation / `493f9520b75f582aa22f6c8647ec08eab3e122d3`

ROI.2 qualification remains frozen at `4ee3e034`; the later convergence archive
`9a1c2268` is referenced as decision evidence and is not merged as product runtime.

The assembly is identified internally as `2.0.0-beta.1`. It uses the separate
`mindthus-beta` package and marketplace identities, rewrites only the namespace mention
inside the inherited Codex default prompt, replaces the full `using-mindthus` entry with
the frozen ROI.2 overlay, and applies the one qualified 3L5S Anti-Spiral sentence
replacement. All other packaged product capabilities come from the named 1.5 shared
core Git object.

Build locally:

```bash
python3 beta/2.0-beta/build-internal-beta.py \
  --out /tmp/mindthus-2.0-beta.1-marketplace
```

This command builds an inspectable Codex marketplace directory. It does not create an
archive, install into the user's CODEX_HOME, publish a Release, or update a marketplace.

Rollback target: the published `v1.5.0` Stable plugin package.
