# Installing Mindthus for Codex

Enable Mindthus skills in Codex through plugin mode or native skill discovery.

The bundle-style skills-pack path provides the `mindthus:*` namespace.
Codex's system `skill-installer` is useful for individual skills, but it installs them into `~/.codex/skills` rather than as a grouped namespace bundle.

## Prerequisites

- Git
- A local checkout of `rv198-star/Mindthus` or an extracted public release pack

## Choose A Mode

- **Codex plugin mode**：把 Mindthus 作为一个 Codex App plugin 管理。适合想要统一启用、禁用和识别 Mindthus 的用户。
- **skills-pack mode**：创建 `${CODEX_HOME:-~/.codex}/skills/mindthus -> <repo>/skills`。适合 portable checkout、开发调试或不使用插件管理的环境。

同一个 Codex profile 中不要同时启用 Codex plugin mode 和 skills-pack mode，除非你明确想测试重复 discovery。迁移到 plugin mode 前，先移除旧的 `~/.codex/skills/mindthus` symlink。

轻量路由纪律：

> 当问题涉及战略判断、结构歧义、路径波动、控制边界、产物价值厚度时，优先使用 `using-mindthus` 选择最小充分方法；清楚低风险任务直接执行。

## Codex Plugin Mode

Generated release packs include `codex-plugin/mindthus/` with `.codex-plugin/plugin.json` and the same packaged `skills/` tree. Use this mode when Codex App should present Mindthus as one plugin product.

## Skills-Pack Mode Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/rv198-star/Mindthus.git ~/.codex/mindthus
   ```

2. Create the skills namespace symlink:

   ```bash
   cd ~/.codex/mindthus
   scripts/install-skills.sh codex --force
   ```

3. Restart Codex so it discovers the skills.

## Available Skills

After installation, Codex should discover:

- `mindthus:using-mindthus`
- `mindthus:sela`
- `mindthus:mpg`
- `mindthus:3l5s`
- `mindthus:edsp`
- `mindthus:wae`
- `mindthus:tvg`
- `mindthus:tplan`

## Verify

```bash
ls -la "${CODEX_HOME:-$HOME/.codex}/skills/mindthus"
```

The path should point to the checkout's `skills` directory, for example `~/.codex/mindthus/skills`.

For a repository checkout in another location, pass it explicitly:

```bash
scripts/install-skills.sh codex --repo /path/to/Mindthus --force
```

## Update

```bash
cd ~/.codex/mindthus
git pull
scripts/install-skills.sh codex --force
```

The symlink means updated skills are available after restart.

## Uninstall

```bash
rm "${CODEX_HOME:-$HOME/.codex}/skills/mindthus"
```

Optionally delete the clone:

```bash
rm -rf ~/.codex/mindthus
```
