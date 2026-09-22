# Choice decimal compatibility v1 — bounded research policy

Owner on2026-09-22 explicitly accepted treating1percentage-point discrepancy as a follow-up
item rather than blocking the experiment. This supersedes the earlier no-normalization stop
for this named technical revision, not the frozen question/label/authority rules.
A0.99sum is mathematically compatible with rounding three probabilities to two decimals:
three individual rounding errors can sum to0.015. It is not proof of server rounding.
Official docs still specify sum1; provider precision remains an unresolved investigation item.

Enable choice_rounding=True explicitly for Jev serving adapters. Choice only, exact option
support, every value finite in[0,1], at most hundredth precision, and absolute total deviation
above1e-6 but at most0.01 (1e-9 float slack): divide each value by the total. This is a local
experimental compatibility policy, not claimed vendor behavior or a semantic revision.
The original choice and confidence stay unchanged; the returned probabilities are derived,
not raw and not newly calibrated against confidence. reason=choice_probability_sum_normalized_v1
marks every conversion; immutable wire records retain original probabilities. Strict default,
shared Decision Contract validator, argmax check, Score/Noul and all authority gates unchanged.
Serving adapter_version=2-choice-rounding-v1 prevents identity reuse with earlier runs.
No new Engine/Provider architecture or canonical-method edits.

Remaining live scope:L18–L32,15pairs (13semantic,2D0). Prior14pairs L03–L16 remain under
strict version and are reported separately. L17/source remains a historical rejected response;
its existing safe response is reinterpreted OFFLINE only, explicitly not a live retry or old
acceptance rewrite. L17/English stays unrun. L01/L02 original transport unknowns remain.
Do not claim one homogeneous32case acceptance run. Total coverage after completion:29paired
cases, plus one rejected source view with offline sensitivity analysis, and2transport failures.

New immutable rounding-trial root; same questions, cases, accepted labels and full translations.
OfficialTypeSafe jev-1.13.0 through explicit per-process localproxy127.0.0.1:7890. Both views
lock runtime. Ordinary semantic failures continue; outside-policy technical/authority errors stop.
No blind retry. No prompt revision, holdout, C02 or A/B/C admission.

Carry forward47series attempts (2oldtransport+45proxy), not a budget reset.45calls per arm
plus47prior <=137total, reserveUSD0.368256 below original192call/USD0.55 ceilings.
260seconds per arm plus prior61.17seconds < original600seconds. No cost saving claim.
Independent read-only review found no blocking issue in the bounded conversion; parent verified.
Provider precision remains a tracked item, not a prerequisite to this explicitly authorized run.
