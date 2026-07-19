# H2.1 Companion-gate Mission Authorization

Authorized by William on 2026-07-19 after the H2 continuation closed:

> 允许在 H2 拓扑不变、不新增 H3 的前提下，对 MPG↔SELA companion gate 做一次减法式修正，并由 Agent 自主完成因果测试、完整资格与必要的 Stable 对照。

William replied: `确认`.

## Authority boundary

- autonomous TPlan Mission (`human_in_loop=0`)
- preserve the H2 single-entry / on-demand resource-owner topology
- one conceptual equal-replacement or subtractive correction, limited to the
  MPG↔SELA companion gate
- do not modify the canonical Stable owner Skills
- do not add H3, Hook, AGENTS injection, defaultPrompt routing, a second discoverable
  entry, a second index, model-name routing, or a semantic router script
- no release, merge, tag, PR, issue, marketplace, Beta.3, or Stable installation change
- William retains stop authority

## Resource boundary

The doubled 8,000,000 counted-token program ceiling remains controlling. Prior work
used 1,187,341, so H2.1 may use at most 6,812,659 additional counted tokens. Each
completed Generator or Judge call remains capped at 400,000 counted tokens.

The earlier aggregate call ceilings remain controlling rather than silently resetting:
32 Generator and 8 Judge across the program. Prior work used 13 Generator and 0 Judge,
leaving at most 19 Generator and 8 Judge for H2.1.

William's confirmation specifically authorizes the nine H2.1 candidate qualification
Generator calls (`Q1/Q2 + C2 + C3 + Q3-Q7`) and supersedes the old qualification-phase
sub-cap for those calls. It does not reset or enlarge the aggregate 32/8 ceilings.

Operational reservations fail below the authorized 400,000 maximum so worst-case calls
cannot overrun the remaining total:

- at most 16 planned Generator calls × 275,000 counted tokens;
- at most 7 planned Judge calls × 200,000 counted tokens;
- at most one pre-registered noise review pair × 275,000 plus one reserved Judge ×
  200,000, only if its frozen trigger fires.

Maximum H2.1 reservation is therefore 6,550,000 counted tokens and 18 Generator / 8
Judge, leaving 262,659 counted tokens and one Generator call unallocated. Any individual
call above its phase reservation rejects that run; the 400,000 outer maximum is not a
license to spend the total reserve twice.

Counted tokens are `input_tokens + output_tokens`; cached input is a subset and is not
added twice.
