# SRA Independent Wake-Up Experiment Design

Status: executable protocol / no certified behavioral result yet
Date: 2026-09-03
Case fixture: `tests/sra_wakeup_holdout_cases.jsonl`

## Questions

This experiment separates two claims that must not be conflated:

1. **Independent invocation:** can `sra` run as a standalone Skill when it is explicitly loaded, without requiring `3l5s`, `tplan`, or `using-mindthus` to own the judgment?
2. **Natural wake-up:** when only the normal Mindthus routing surface is available and the prompt does not name a method, how often does the host select `sra` for real cross-candidate scarce-resource allocation without over-calling it on adjacent cases?

Static contracts and package presence can prove independent availability. Only completed host/model runs can establish a behavioral wake-up rate.

## Case Set

The holdout contains 24 prompts with no Mindthus method names:

- 12 SRA positives: 5 bounded Lite decisions and 7 Full or cross-boundary allocation decisions;
- 8 adjacent-owner controls: `3l5s`, `edsp`, `sela`, `mpg`, `wae`, `tvg`, `tplan`, and Anti-Spiral;
- 4 stay-asleep controls: direct debugging, independent parallel work, information acquisition, and a deterministic checklist.

The cases test semantic ownership rather than keywords. A prompt can mention time, money, people, or priority without qualifying for SRA; a positive case requires at least two sufficiently judgeable candidates that genuinely compete for one resource and an allocation decision that changes action.

## Arm A: Explicit Standalone Invocation

Load `skills/sra/SKILL.md` directly, without routing through `using-mindthus`. Run the 12 SRA-positive cases in fresh sessions.

A pass requires more than repeating the method name. The answer must change at least one of:

- next meaningful tranche;
- investment ceiling or authorization horizon;
- maintenance line;
- defer or stop set;
- reserve posture;
- reranking trigger.

Recommended sample: 3 fresh sessions per positive case, 36 outputs.

Metrics:

- `standalone_method_execution_rate`;
- `action_changing_rate`;
- `lite_full_depth_accuracy`;
- `unnecessary_dependency_rate` for answers that incorrectly require 3L5S or TPlan.

Certification thresholds:

- standalone method execution >= 90%;
- action-changing output >= 90%;
- unnecessary dependency <= 5%.

## Arm B: Natural Router Wake-Up

Expose the normal Mindthus installation and allow the agent to route normally. Do not name SRA or reveal the expected owner.

Recommended sample: 5 fresh sessions per case, 120 outputs.

Primary metrics:

- `sra_positive_wakeup_recall`: SRA is the selected/loaded owner and the answer changes allocation on the 12 SRA positives;
- `sra_false_activation_rate`: SRA is selected on any of the 12 controls;
- `adjacent_owner_accuracy`: the eight adjacent method controls reach their expected owner;
- `direct_stay_asleep_rate`: the four direct/evidence controls do not load Mindthus;
- `execution_impact_rate`: the answer changes a tranche, ceiling, displaced work, reserve, or rerank condition where SRA is expected.

Certification thresholds:

- SRA positive wake-up recall >= 80%;
- SRA false activation rate <= 10%;
- adjacent owner accuracy >= 80%;
- direct stay-asleep rate >= 90%;
- execution impact among SRA wake-ups >= 90%.

## Optional A/B Attribution

To attribute the effect of the SRA wake-up additions rather than merely measure the current state:

- baseline: commit `b497ee380fb275727f1ba715f8035f17327a7efe`;
- treatment: the audited wake-up/boundary commit produced from this work;
- identical prompts, models, host configuration, fresh-session policy, and random order;
- blind scoring before the variant is revealed.

The treatment should improve SRA positive recall without increasing false activation by more than 5 percentage points.

## Execution Harness

The existing CLI benchmark runner accepts this case file:

```bash
python3 scripts/run-judgment-benchmark-cli.py \
  --cases tests/sra_wakeup_holdout_cases.jsonl \
  --out-dir /tmp/sra-wakeup-run \
  --codex-home /path/to/installed/codex-home \
  --empty-home-root /tmp/sra-wakeup-homes \
  --plugin-context mindthus \
  --model <answer-model> \
  --judge-model <judge-model> \
  --phase all \
  --fail-on-contamination
```

Repeat runs with isolated homes and unique output directories. Aggregate only completed model and judge records. Authentication failures, timeouts before model output, malformed carrier output, or missing judge output are infrastructure failures, not wake-up misses.

## Scoring Boundary

A positive wake-up requires all three:

1. SRA owns the active judgment object;
2. the answer identifies the shared constrained resource and sufficiently judgeable candidates;
3. the answer changes allocation rather than only saying which item is more important.

A method name without allocation impact does not count. A correct direct or adjacent-method route is a control success, not an SRA miss.

## Current Evidence Boundary

Repository tests may certify:

- direct-load entry presence;
- package availability across supported layouts;
- routing and Entry Triage contract presence;
- reciprocal method-boundary wording;
- benchmark case integrity and host-run readiness.

They cannot certify natural wake-up recall. A percentage may be reported only after valid fresh model outputs and blind scores exist.
