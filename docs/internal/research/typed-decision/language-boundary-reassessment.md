# Language boundary reassessment — 2026-09-22

## Decision

User identified language as a plausible confound before the proposed broader Chinese
coverage diagnostic. Prioritize a frozen Chinese-source / English-execution translation
comparison before more prompt tuning or a larger Chinese-only Jev campaign. This is a
new research hypothesis, not evidence that language caused every prior failure, and not
a revival of the stopped candidate-1 trial. No new live calls were made for this review.

## Verified evidence

Official https://docs.typesafe.ai/models, Language support, checked 2026-09-22:
English is the primary training language and currently most accurate; other languages,
including CJK, are handled with unequal performance. The page does not establish that
Chinese was entirely absent from training. Translation superiority remains untested.

Offline reconstruction of candidate-1's six exact projected requests:
- N04/N02: English questions; request, evidence, entry_contract and method_contract contain CJK.
- N07/N08/N11/N12: English questions; artifact, target, evidence, veto_constraints and tvg_contract contain CJK.
- Existing typed outputs are stable enum IDs / numeric distributions, not Chinese prose.
Thus merely translating questions would not remove the language variable. Prior observations
remain valid for those mixed-language inputs, with contract and language effects unresolved.

## Translation boundary

Chinese user/source records remain authoritative. The host LLM supplies a versioned,
faithful English execution view upstream of the existing Decision Engine interface.
Keep semantic responsibilities, graph, criteria meanings, source identities, permissions
and output enum IDs unchanged. This is input preparation, not a new graph platform or
an Engine/Provider redesign. User-facing explanations remain Chinese; enum mapping is
code-owned and needs no LLM back-translation.

Translate every relevant natural-language field, including full selected canonical method
contracts; a translation is a derived view linked to the complete source and never a new
canonical method rule. Static contract translations can be reviewed once and cached by
source/version hash. Dynamic facts require their own source-bound snapshot. Literal text
operations, named entities, negation, numbers, conditions, unknowns and unresolved duties
must preserve their exact meaning; where this cannot be established, keep an explicit
translation limitation and return to the host rather than treating it as successful adaptation.

Artifact, evidence and target are translated as distinct fields. Translators must not see
gold labels or model results, decide routes, summarize away limitations, fill omissions,
or repair the artifact. In particular N12's absent reason must remain absent in the
English artifact even though it is present in the independently translated evidence.
A bilingual fidelity check must inspect both omissions and additions before Jev inference;
back-translation alone is not proof of fidelity.

## Next evidence and stop conditions

Use matched source/translation pairs with frozen graph, model, criteria and labels.
Preserve all known failures and successful controls; include independent situations before
making any general language claim. Keep exploratory paired comparisons separate from
holdout and the later formal A/B/C value experiment. Bind translations, translator/version,
source hashes, requests, budget and scoring before live calls; compare all pairs, not just
improved ones. Historical Chinese results cannot automatically count as a synchronized
control for a new campaign, and their repeated calls are not independent scenarios.

First check translation fidelity; then assess language-view effects with the contract held
fixed. Consistent gains would support an English execution path, not prove internal model
causes. No clear gain means no further blind translation/prompt polishing. A gain on
historical development examples still requires unseen qualification before adoption.

Full cost includes translation, fidelity checking, Jev, fallback and host execution, with
static one-time translation distinguished from per-task translation. Unknown costs stay
unknown. If translation duplicates enough LLM reasoning to erase the benefit, retain the
ordinary LLM path or restrict Jev to already-English/repeated inputs. Confidence remains
a diagnostic signal, never execution authority.

## Scope correction

The six earlier probes were three local contrasts, including node-only C01 checks. Their
5/6 result does not estimate task-distribution accuracy. Stopping unsupported prompt
revision remains justified; collecting new evidence about a named language variable is a
different research action. Keep C01/C02 qualification separate: C02's missing-rationale
error does not by itself disqualify C01. Old scores and freezes remain unchanged.
