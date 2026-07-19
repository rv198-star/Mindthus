# H2.1 Companion-gate Qualification Result

Terminal H2.1 outcome: `H2.1_REJECTED`

Mission consequence: `STOP_2X_EXPLORATION`

Candidate commit `1cbca9c997546e89cbf9088cdafc3d1cb976e17a` passed the
static package, full-test, fixture-lock, and responsibility-separated design gates. C1
then passed both turns. C2 produced a useful answer but traversed the companion owners in
the opposite direction from the frozen causal contract, so C3, Q3-Q7, Stable, and Judge
were correctly withheld.

## Non-call authentication incident

The first empty-home attempt failed with HTTP 401 before authenticated sampling. It had
no model output, no `turn.completed`, and no usage. It is preserved under
`evidence/preflight/auth-401/`, counted as zero Generator and zero tokens, and was
resolved by copying only the existing Codex `auth.json` into a new isolated home. No
config, Skill, plugin, prompt, fixture, or candidate byte was reused from that attempt.

## C1 — pass

Q1 read only the thin entry and asked one answer-changing question. It loaded neither
the owner index nor an owner and gave no direction. Q2 resumed the exact thread UUID in
the same isolated workspace, then read the owner index and MPG only. It did not read
SELA or any unrelated owner and returned a useful `HOLD` path action.

Observed lifecycle across the two-turn C1 session:

```text
Q1: entry
Q2: owner-index -> MPG
```

## C2 — trusted causal failure

The frozen positive case required:

```text
entry -> owner-index -> MPG -> SELA
```

The raw command lifecycle instead shows:

```text
entry -> owner-index -> SELA -> MPG
```

The entry read is at `evidence/live/c2/c2.jsonl:5`, index at line 8, SELA at line 10,
and MPG at line 13. The unchanged SELA owner selected MPG through its reverse handshake.
The modified MPG companion gate therefore did not cause the positive SELA read and its
positive branch remains unproved.

The final answer correctly held the German cutover while preserving the three-year
platform direction, but the protocol explicitly forbids using a useful answer to cancel
a lifecycle failure. This is a trusted causal failure, not missing evidence.

## Usage

| Phase | Generator calls | Input | Output | Counted |
| --- | ---: | ---: | ---: | ---: |
| C1 / Q1 | 1 | 28,096 | 333 | 28,429 |
| C1 / Q2 | 1 | 75,430 | 1,495 | 76,925 |
| C2 | 1 | 79,654 | 2,954 | 82,608 |
| **H2.1 total** | **3** | **183,180** | **4,782** | **187,962** |

Program cumulative usage is 16 Generator, 0 Judge, and 1,375,303 counted tokens. The
unused balance is 16 Generator, 8 Judge, and 6,624,697 counted tokens. Every completed
call stayed below the 275,000 Generator rejection line. The rejection is causal, not a
budget or infrastructure failure.

## Stop mapping

The protocol requires the first trusted causal failure to stop the candidate with no
patch or rerun. C3 cannot prove the missing MPG-to-SELA positive branch, and continuing
to Q3-Q7 or comparison would test an ineligible candidate. Repairing the order would
require another semantic change to owner selection or SELA/MPG ownership, outside the
single-correction authorization.

No C3, Q3-Q7, Stable arm, Judge, noise review, release, merge, tag, PR, issue, Beta.3,
marketplace deployment, or Stable installation change was performed.

## Claim ceiling

H2.1 proves that the static single-entry package is reproducible and that the narrowed
MPG gate avoids the prior false SELA read in C1/Q2. It does not prove the positive MPG
companion path, full passive coverage, Stable-relative quality, loaded-byte savings,
uncached-token savings, or practical compatibility. It rejects this exact H2.1 causal
hypothesis under the frozen Codex conditions; it does not prove that every imaginable
future architecture is impossible.
