# Mindthus / 心即

Mindthus is a personal methodology and agent-construction project.

`Thus` means "so / thus / it is so" with a sense of settled judgment. `心即 / Mindthus` means: once the mind has judged the pattern, the work should take that shape.

The name draws from Wang Yangming's `心即理`: method is not only an external checklist. It is the crystallization of judgment, evidence boundaries, action posture, and repeated practice.

Short formulation:

> Mindthus turns personal philosophy and methodology into durable `AGENTS.md` instructions and independent `SKILLS` that agents can actually use.

Mindthus can also be installed as a skills pack:

- `mindthus:using-mindthus`
- `mindthus:sela`
- `mindthus:3l5s`
- `mindthus:edsp`
- `mindthus:wae`
- `mindthus:tvg`

## Project Posture

The root agent stance is:

> 遇事不要慌，先搞清楚情况再说。

This means every agent working in this project should prefer situation clarity before conclusion, evidence before confidence, bounded judgment before procedural motion, and executable next steps before decorative structure.

## Organization

Mindthus is organized through two surfaces:

1. `AGENTS.md` defines the project-level agent posture, operating rules, and contribution boundaries.
2. `skills/<skill-name>/` contains independent skills, each with its own `SKILL.md` and optional bundled resources.

Current skills:

- `skills/using-mindthus/` — portable AGENTS-style entry skill for Mindthus posture and routing.
- `skills/sela/` — top-level decision principle: System Efficiency over Local Advantage.
- `skills/3l5s/` — structures vague, complex, or system-level problems through `Three Layers + Five Steps` (`三层五步`): `Discovery / Definition / Resolution` plus `Baseline -> Target -> Gap -> Strategy -> Breakdown`.
- `skills/edsp/` — handles ambiguous qualitative judgments through Extreme Deduction + Scenario Projection.
- `skills/wae/` — separates deterministic workflow control, agentic judgment, and evidence bridging.
- `skills/tvg/` — value-driven thinking-depth enhancer for shallow AI-generated artifacts.

Skill-specific resources live under `skills/*/resources/` so each skill can be used independently. Root-level files should stay limited to project orientation and agent posture.

## Install As A Skills Pack

### Codex

See [.codex/INSTALL.md](/root/mindthus/.codex/INSTALL.md).

Codex supports bundle-style discovery through `~/.agents/skills/`, so the intended namespace is `mindthus` and installation exposes the skills as `mindthus:*`.

### Claude Code

Claude Code personal skills live under `~/.claude/skills/`.

1. Clone the repository:

   ```bash
   git clone https://github.com/rv198-star/Mindthus.git ~/.claude/mindthus
   ```

2. Create the local skills links:

   ```bash
   mkdir -p ~/.claude/skills
   ln -s ~/.claude/mindthus/skills/using-mindthus ~/.claude/skills/using-mindthus
   ln -s ~/.claude/mindthus/skills/sela ~/.claude/skills/sela
   ln -s ~/.claude/mindthus/skills/3l5s ~/.claude/skills/3l5s
   ln -s ~/.claude/mindthus/skills/edsp ~/.claude/skills/edsp
   ln -s ~/.claude/mindthus/skills/wae ~/.claude/skills/wae
   ln -s ~/.claude/mindthus/skills/tvg ~/.claude/skills/tvg
   ```

3. Restart Claude Code.

This exposes the same skill set in Claude Code as local skills. Unlike Codex bundle discovery, this path does not currently add a `mindthus:` namespace prefix by itself.

## Skill Rule

Each skill should stay portable and self-contained:

- Put trigger logic and operating procedure in `SKILL.md`.
- Put longer methodology text in `resources/methodology.md`.
- Do not make a skill depend on project-local memory unless the dependency is explicit.
- Do not turn a method into ceremony; preserve the judgment it was meant to protect.
- Do not let scripts, schemas, or templates replace agentic judgment when truth is uncertain.

## Working Rule

When adding or revising a method:

1. Clarify the situation first.
2. Name the bounded method or skill being changed.
3. Preserve the method's philosophical claim.
4. Convert the claim into usable agent behavior.
5. Add evidence, boundaries, and stop conditions.
6. Keep the skill lean enough to load in context.

Mindthus is not a warehouse of notes. It is a forge for reusable judgment.
