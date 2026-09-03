# v1.9.0 ROI Beta — SRA Compatibility Qualification Result

Date: 2026-09-04

## Verdict

PASS for deterministic composition and SRA compatibility.

This verdict authorizes the `v1.9.0-roi-beta` supplemental experimental asset under the
existing Stable + ROI Beta release rule. It does not claim a Beta-specific natural
wake-up rate, relative model-quality gain, universal allocation correctness, or Token
ROI improvement.

## Frozen inputs

- Stable shared core commit: `3dfbd563315b761bae0ea2d1a9e0f04d9ff1b946`
- Stable shared core tree: `a9dcdfd9a7fb435ba6f0bdf2bf38fd894d36ffea`
- SRA Thin Core implementation: `0bd58701fd36f33d5640ff2d00aa5e208026dbfa`
- Historical ROI.2 implementation: `493f9520b75f582aa22f6c8647ec08eab3e122d3`
- Historical ROI.2 qualification: `4ee3e034db6bf8d1e34002d7f162e2b008516490`
- Qualified composition source: `cc5c313d629eb89f20f0aab02ae5221b4457d876`

## Deterministic gates

- Thin Core size: `2274 / 2300` bytes — PASS.
- Existing frame/whole, decision-context, evidence-ceiling, Anti-Spiral, one-thesis and
  direct-execution obligations — PASS.
- SRA route marker requires multiple judgeable candidates sharing one scarce resource —
  PASS.
- SRA Skill, methodology, context-isolation contract, templates and runtime scripts
  inherited from exact Stable shared core — PASS.
- Capability register includes SRA allocation and context-isolated runtime for Stable and
  ROI Beta — PASS.
- Historical ROI.2 3L5S Anti-Spiral correction preserved exactly — PASS.
- Non-declared-delta plugin files byte-identical after Beta namespace normalization —
  PASS.
- Stable namespace absent from the Beta artifact — PASS.
- Packaged runtime diagnostic `--strict`: `status=ok` — PASS.
- Two independent Beta archives byte-identical — PASS.

Qualification archive SHA-256:

```text
c69895cb75987d4b11b7c5c95d3d972673ea7987c7fe940b75c72301e19ad548  mindthus-beta-1.9.0-roi-beta.tar.gz
```

The published archive is rebuilt from the final Beta source tag, so its final digest is
recorded separately in the post-publication verification note and `SHA256SUMS`.

## Stable evidence inherited by source

The exact Stable shared core passed Python compileall, Test Lifecycle validation, the
complete repository unittest suite, split plugins/skills builds, and the SRA release
acceptance recorded on Issue #156. The Stable behavior sample measured 10/12 natural SRA
positive activations and 0/12 false SRA activations outside SRA, plus complete explicit
standalone activation and final-SHA Agentic scenario replays.

Those measurements qualify the Stable SRA product surface. They do not measure the ROI
Thin Core itself, so they are not reported as Beta-specific ratios.

## Registered but unexecuted Beta model cases

`cases.json` freezes five matched Stable/Beta cases covering SRA positive routing,
independent-resource direct execution, missing-evidence blocking, MPG adjacency, and
Anti-Spiral-to-SRA handoff. They were not executed for this release because deterministic
compatibility was the declared gate and no Beta-specific performance claim is made.
