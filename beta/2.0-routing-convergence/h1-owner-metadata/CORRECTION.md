# H1 one-time correction record

Status: `FROZEN / correction budget exhausted`

Candidate A commit `155648d0fb6ae123e0cb939b97953d0ade1991e5` passed the WAE
positive and near-negative probes, but failed Q3. It no longer loaded MPG or SELA for an
underspecified migration decision; it loaded 3L5S and then recommended stopping at a
reversible checkpoint before asking the required blocking context question.

The raw lifecycle evidence showed exactly one new owner read: `3l5s/SKILL.md`. Its
original description treated any unclear problem as sufficient, while the body defines
two narrower main uses: turning noisy/scattered signals into a falsifiable problem, and
decomposing an accepted but too-large problem. Missing decision context alone is owned
by the unchanged thin entry.

The only correction is therefore a package-time replacement of the 3L5S description:

> Use only when noisy or scattered signals, or repeated execution failures, must be
> turned into a falsifiable problem; or when an accepted problem or task plan is too
> large or complex to decompose into executable, verifiable work. A single
> underspecified decision request is missing context, not by itself a 3L5S problem.

This text contains no `migration`, `continue`, `stop`, `release`, or other workload
keyword. It preserves the two body-defined positive domains and lifts Decision Context
precedence into discovery metadata. Thin entry, owner bodies, topology, prompts, and
acceptance tests remain unchanged.

Before the complete qualification, the corrected candidate must pass the pre-existing
WH-X4 holdout in `tests/router_wakeup_weak_cue_holdout_cases.md`: thin entry plus 3L5S
must load in the same turn for a mixed incident report that cannot yet state the actual
failure. Missing 3L5S recall, any owner load on Q3, an action recommendation on Q3,
incorrect MPG recall on Q4, or any later critical failure rejects H1 immediately.

No further H1 metadata, thin-entry, owner-body, topology, prompt, or test correction is
allowed.
