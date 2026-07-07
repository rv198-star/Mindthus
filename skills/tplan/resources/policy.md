# tplan Policy

## human_in_loop

- `0`: autonomous; `tplan` may mutate decision state.
- `100`: advisory; `tplan` recommends and records rationale without decision mutation.
- `1-99`: reserved for future mixed modes.

## risk_tolerance

- `0-33`: low.
- `34-66`: normal.
- `67-100`: high.

## resource_sufficiency

- `0-33`: poor.
- `34-66`: normal.
- `67-100`: rich.

## Role-Separated Review Policy

Role separation is responsibility separation, not reviewer isolation and not a new
runtime role model. For important Missions, `tplan` separates doing,
direction-checking, acceptance, and learning by routing them to existing Mission
surfaces: Task/SubTask/Step, Pulse/hooks/Mission Review, acceptance evidence, and
Mission Shared Context / Shared Risk Context.

Use this policy for high-risk, release-facing, long-running, repeated-failure,
authority-sensitive, method-design, or meaningful closure claims. Low-risk reversible
work stays lightweight.

`tplan core` defines which responsibilities should not silently collapse into one
cognitive flow. It does not require SubAgents, clean sessions, extra gates, or new
schema. When no independent reviewer exists, use same-agent phase separation plus
rubric, acceptance evidence, scripts, or human confirmation. Platform adapters may
provide stronger isolation when their host capabilities are verified, but adapter
outputs remain candidate findings; the main agent or authorized human still owns
verification, recording, and final decision.

Learning output belongs in Mission Shared Context. Only risk-relevant learning becomes
Shared Risk Context, and neither inherits acceptance authority automatically.

## Addition And Subtraction Bias

High risk tolerance with rich resources allows more exploration and splitting.

High risk tolerance with poor resources still accepts uncertainty in principle, but
prunes weak exploration branches.

Low risk tolerance with rich resources allows observation without broad branching.

Low risk tolerance with poor resources converges aggressively.
