# C02 development disposition — 2026-09-22

## Core

Stop qualification of the current C02 contract/data pair. Keep ordinary TVG. The first
development run failed its frozen gate, and review exposed a label/standard defect that
cannot honestly be repaired by tuning only the question. The optional semantic revision
is unused (0/1); it is a ceiling, not an obligation to spend another attempt.

This is not a rejection of Jev or of TVG. It is a negative outcome for this experimental
design. No rewritten artifact, recheck, holdout or A/B/C was admitted after this result.
The graph's generation/recheck path has offline evidence only.

## Observed evidence

`c02-typesafe-dev-1.json` binds all trial artifacts and source `776adcc12`. Official
`jev-1.13.0` completed 12 cases in 18 calls, with no provider/contract failure and no
unauthorized rewrite or exit. Route matches: 10/12; utility matches: 9/12; all expected
action selections: 5/6. The frozen rule required at least 11/12 routes, 11/12 utility
labels and all six action selections. Support labels matched where a support label was
specified; the four scope/conflict cases had no support gold label, so 12/12 in the
raw summary is not twelve independently tested support judgments.

53100 input / 1713 output tokens and 14.249 cumulative inference seconds were observed.
Estimated inference price is USD 0.0022302; actual reported cost and total design,
context, generation/audit cost are unknown. Eighteen attempts reserve USD 0.048384.
There were no retries, diagnostic calls or second serving path. No savings conclusion.

## Review against the independent standards

| Case | Difference | Attribution and practical consequence |
| --- | --- | --- |
| C02D02 | Utility adequate, but action make_actionable rather than leave_unchanged | The action contract did not reliably distinguish a relevant transformation type from a needed transformation. This would cause an unnecessary rewrite. No rewrite was actually executed. |
| C02D04 | Utility adequate instead of deficit; compact_preserve selected correctly | The instruction already contains both booking branches and the no-overwrite limit. Repetitive filler can be removed, but the independent target does not specify when that burden makes the module inadequate. The deficit label is not a secure truth reference. |
| C02D09 | Utility conflict instead of deficit; returns to owner rather than acquire_information | The target requires measured satisfaction evidence while sources say no measurement exists. Missing evidence is not necessarily an internally inconsistent target. Utility mixes task fit, target coherence and usefulness, creating an avoidable ambiguous boundary. Support correctly reports missing. |
| C02D10 | Utility adequate instead of deficit; compact_preserve selected correctly | The explanation already gives the network reason, offline/live alternative, manual weekly update limit and absence of visitor measurement. As with D04, a possible compression gain does not establish the authored inadequacy label. |

Reference-based author review (not an independent reader experiment): D04 permits a
reader to recover 'free → enter name/time; occupied → waiting list; never overwrite'.
D10 permits 'unstable network → cached page rather than live; no automatic updates →
weekly manual replacement; no visitor-effect result'. These facts are already explicit
in the original texts. Thus Jev's adequate judgment is defensible even though removing
repetition can improve density. Token/phrase presence alone is not the final quality test.

## Why no immediate revision or holdout

The protocol freezes data, labels and targets. A question-only change could repair the
unnecessary action boundary, but could not make the disputed deficit labels an
independent standard. Adding 'all repetition is inadequate' to force those labels would
overstate the canonical TVG contract, which treats usefulness and further value as
judgments rather than formal phrase rules. Relabeling after seeing the answers would
invalidate the preregistered score. Selecting only successful cases would hide the defect.

This reaches #212's stop condition for standards that cannot yet be stably described
independently. The parent goal is a trustworthy contract and task-value test, not a
passing table. Do not proceed to downstream generation, freeze a purported holdout to
rescue the development result, or consume the unused revision without a defensible
new evidence hypothesis.

A future proposal would first need independently adjudicated usefulness/density
boundaries and a new data/protocol identity, plus a local weakness contract that does
not merge scope, conflicting demands and adequacy into a generic quality label. It
would be a new experiment, not a silent revision of these frozen labels.

## Issue and claim disposition

#212's full artifact/value acceptance is unmet. Preserve its OPEN status; do not check
boxes for actual generation, downstream usability or matched full-cost comparison.
#209 receives evidence that engine portability works mechanically but contract/label
validity remains prior to model qualification. #210 retains order, stops investment
in the current two qualification campaigns, and leaves C03–C08 unstarted. No formal
main, method truth, release, #112 or #207 state changes follow.
