# Installing Mindthus for Codex

Enable Mindthus skills in Codex through native skill discovery.

This is the bundle-style installation path for the `mindthus:*` namespace.
Codex's system `skill-installer` is useful for individual skills, but it installs them into `~/.codex/skills` rather than as a grouped namespace bundle.

## Prerequisites

- Git
- Access to the private `rv198-star/Mindthus` repository

## Installation

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
