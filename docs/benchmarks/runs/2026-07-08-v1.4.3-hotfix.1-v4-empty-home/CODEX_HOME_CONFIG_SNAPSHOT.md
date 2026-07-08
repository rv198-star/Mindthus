# V4 Codex Home Config Snapshot

These sanitized config snapshots document the model/plugin settings used by the V4
diagnostic run. No auth material is included.

Important reproducibility note: the benchmark runner manifests record `model: null` and
`judge_model: null` because this run inherited the model from these Codex home configs
instead of passing explicit `--model` and `--judge-model` CLI flags. A certification run
should pass both flags explicitly.

## Baseline

Path at run time: `/tmp/codex-mindthus-baseline-home-v4/config.toml`

```toml
#:schema none
model = "gpt-5.5"
model_reasoning_effort = "medium"
service_tier = "default"

[projects."/tmp/mindthus-benchmark-workspace-v4"]
trust_level = "trusted"
```

## Treatment

Path at run time: `/tmp/codex-mindthus-eval-home-v4/config.toml`

```toml
#:schema none
model = "gpt-5.5"
model_reasoning_effort = "medium"
service_tier = "default"

[projects."/tmp/mindthus-benchmark-workspace-v4"]
trust_level = "trusted"

[marketplaces.mindthus]
last_updated = "2026-07-08T00:00:00Z"
source_type = "local"
source = "/private/tmp/mindthus-v4-plugins-pack/codex-plugin"

[plugins."mindthus@mindthus"]
enabled = true
```
