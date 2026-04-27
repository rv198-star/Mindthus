# Installing Mindthus for Codex

Enable Mindthus skills in Codex through native skill discovery.

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
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/mindthus/skills ~/.agents/skills/mindthus
   ```

3. Restart Codex so it discovers the skills.

## Available Skills

After installation, Codex should discover:

- `mindthus:using-mindthus`
- `mindthus:sela`
- `mindthus:3l5s`
- `mindthus:edsp`
- `mindthus:wae`
- `mindthus:tvg`

## Verify

```bash
ls -la ~/.agents/skills/mindthus
```

The path should point to `~/.codex/mindthus/skills`.

## Update

```bash
cd ~/.codex/mindthus
git pull
```

The symlink means updated skills are available after restart.

## Uninstall

```bash
rm ~/.agents/skills/mindthus
```

Optionally delete the clone:

```bash
rm -rf ~/.codex/mindthus
```
