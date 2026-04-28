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

## Addition And Subtraction Bias

High risk tolerance with rich resources allows more exploration and splitting.

High risk tolerance with poor resources still accepts uncertainty in principle, but
prunes weak exploration branches.

Low risk tolerance with rich resources allows observation without broad branching.

Low risk tolerance with poor resources converges aggressively.
