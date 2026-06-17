# Weak-Cue Router Wake-Up Holdout Cases

These cases are for discriminative A/B evaluation after the known set failed with
`baseline-ceiling`. They are not copied into the router text and should not be shown to
agents together with expected owners.

Calibration status: failed on 2026-06-17 with baseline positive wake-up recall at
100%. Do not use this v1 pool for full certification. Keep it as a documented failed
attempt and move certification sampling toward real-use replay or more indirect
multi-turn synthetic transcripts.

Rules:

- No method names in prompts.
- No wake-up vocabulary in prompts.
- Prompt wording should look like ordinary product, workflow, review, planning, or
  writing requests.
- Adjacent skip traps are included so higher low-frequency activation alone cannot pass.
- Run a calibration pilot first; if baseline positive recall hits `baseline-ceiling`,
  discard or rewrite the set.

## Positive Weak-Cue Cases

### WH-S1

Expected owner: `sela`

Surface trap: looks like an operations staffing decision.

Prompt: Our senior support people solve rare angry-account situations better than the new bot, but the bot handles most routine setup questions instantly and costs almost nothing per case. Should the old staffing model remain the default?

Pass condition: notices that rare human excellence and default-system economics are different decision layers; changes the default/escalation strategy.

### WH-S2

Expected owner: `sela`

Surface trap: looks like a quality preference question.

Prompt: The handmade review step catches some nuanced issues that automation misses. The automated route misses a few edge cases but lets every team ship in hours instead of waiting two days. Which route should become the normal path?

Pass condition: treats the handmade strength as real but asks whether the normal path is being overtaken by a system-level throughput advantage.

### WH-M1

Expected owner: `mpg`

Surface trap: looks like generic planning.

Prompt: We agree the new recurring product is where the company has to end up. The trouble is that one-off services still pay salaries, account managers are rewarded for the old contracts, and cash runs thin if we move too quickly. What should the commitment look like?

Pass condition: separates destination from carrier, exposure, timing, incentives, and runway.

### WH-M2

Expected owner: `mpg`

Surface trap: looks like a prioritization request.

Prompt: Everyone agrees the platform should move from custom delivery to self-serve. But the current enterprise pipeline funds the migration, and the sales team will resist anything that cuts quarterly commission. How do we avoid getting stuck halfway?

Pass condition: produces a path-carrying strategy with exposure budget, sequencing, incentive transition, and triggers.

### WH-E1

Expected owner: `edsp`

Surface trap: looks like a simple policy choice.

Prompt: Should the review system bother engineers less, or should it catch every risky change even if people complain? Both options sound obviously responsible depending on who you ask.

Pass condition: identifies that the choice depends on risk tiers, reversibility, and failure cost rather than one universal objective.

### WH-E2

Expected owner: `edsp`

Surface trap: looks like a metric choice.

Prompt: For internal search, should we optimize for fewer irrelevant results or fewer missed useful results? Product wants clean pages; research users say missing one useful thing is worse than seeing extra noise.

Pass condition: builds a coordinate system for task type, miss cost, noise cost, and user segment.

## Adjacent Skip Traps

### WH-X1

Expected owner: `information_acquisition`

Prompt: The new ranking model is probably cheaper and faster, but the latency logs and relevance judgments have not been compared yet. Should we remove the old one this week?

Pass condition: asks for measurements and rollback proof before any strategic conclusion.

### WH-X2

Expected owner: `information_acquisition`

Prompt: Which checkout version converts better? The experiment finished yesterday, but nobody has opened the results dashboard yet.

Pass condition: asks for experiment data, metric definition, sample, and confidence.

### WH-X3

Expected owner: `tvg`

Prompt: The launch memo is already scoped and the strategy is settled, but the draft reads generic and gives the sales team no usable trade-offs, examples, or objections. Please strengthen the memo.

Pass condition: keeps the bounded artifact as the object instead of reopening upstream strategy.

### WH-X4

Expected owner: `3l5s`

Prompt: The incident report mixes customer complaints, deploy timing, missing logs, and three possible fixes. We cannot yet state what actually failed. Help us turn it into an actionable investigation.

Pass condition: treats the object as problem-definition failure rather than low-frequency strategic judgment.
