# C01-v2 — entry mode before owner

## Core

Choose the next handling mode directly. Keep a separate obligation question only because
it can independently return control to the original agent. The graph is advisory until
separate semantic and host-consumption qualification exists.

## Mainline

| Node | Input / responsibility | Consequence |
| --- | --- | --- |
| D0 | Code checks required fields, evidence reference shape, provenance source/revision, freshness, supported explicit owner, risk and declared advisory permission. Session binds engine/serving/source identity. | Invalid input goes to the original path with zero provider calls. |
| J1 `entry_mode` | Current request, constraints, evidence, provenance, risk, freshness, known obligations, explicit method, permission and complete canonical entry contract. | `direct_execution`, `acquire_information`, `mindthus_intervention`, or `unclear` (the explicit unclear/no-match option). |
| J2 `unresolved_obligation` | Exactly the same State as J1; no dependency on its answer. | `clear`, `present`, or `unclear`; retain supported/uncertain obligations and hand back to the original agent. |
| M1 | Code consumes J1/J2 under the policy below. | Direct proposal, information acquisition, fallback, or owner selection. |
| J4 `owner` | Intervention State plus the canonical owner catalog. | One owner or explicit `unclear`/no-match. A valid explicit user method binds the owner deterministically instead of spending another call. |
| L1 | Read the selected owner's complete `skills/<owner>/SKILL.md`. | A real new contract dependency; bind its SHA256 even when applicability is later rejected. Unavailable source returns `missing_context`. |
| J5 `applicable` | Original State, selected owner and its full canonical skill contract. | `yes`, `no`, or `unclear`; an explicit request does not prove method preconditions. |
| M2 | Code consumes applicability. | Propose intervention or return to the original agent. |

Normal physical calls: **(J1 + J2) → J4 → J5**. Explicit invocation uses two calls.
L1 is a file-read dependency, not a fourth model question. Direct, information and
first-stage fallback paths use one batch; invalid D0 inputs use none.

### M1 policy

1. Preserve known obligations and any successful J2 obligation observation, including
   when the other answer fails. Non-ok provider statuses retain their distinct cause.
2. An unresolved obligation returns control to the original agent, including when J1
   proposes information acquisition. The host decides how to acquire evidence while
   respecting that obligation; the experiment does not discard it.
3. `unclear` is a valid semantic answer with reason `entry_mode_no_match`; it is distinct
   from transport failure, unsupported capability and missing structural context.
4. `acquire_information` requests the concrete missing input. An empty evidence list
   alone is not a mechanical failure or a model instruction to select this route.
5. `direct_execution` produces `direct_execute` only at low risk and without an explicit
   method constraint. A conflicting explicit method returns to the original agent.
6. Only `mindthus_intervention` enters owner selection / explicit owner binding.

## Guardrail

This protects advisory routing from being mistaken for authorization: `permission.mode`
must be `advisory` with a nonempty host/source reference. This is a declared input scope,
not proof of external authority. C01 performs no downstream action, reports
`consumption=not_executed`, and retains existing host permission owners. Confidence is
recorded by the provider journal but is neither a branch gate nor input to later semantic
questions. The old trace field `hard_judgment` is derived conservatively: explicit method
invocation and information/no-match paths leave it unknown. It is no longer a question.

## Boundary

`unclear` is the serialized spelling of the requested `unclear/no_match` exit; the existing
option identifier contract remains unchanged. There is no new engine/provider abstraction,
generic graph platform, automatic designer, C02 runtime or change to canonical methods.
The first live SRA/high-confidence and low fact-sufficiency observation is treated as a
Decision Contract diagnostic; it does not by itself demonstrate engine inconsistency.

## Runtime support

Graph and affected DecisionSpecs are version 2. Old immutable trials remain historical;
use a new trial root because the implementation and questions changed. Within v2, unchanged
completed batches replay, changed first-stage State invalidates relevant downstream work,
and changing only the selected method recomputes applicability. The existing Session owns
resolved-runtime locking and interruption semantics.

The Chinese development set is separate from scripted engineering fixtures. Its expected
labels never belong in provider State. See `c01-v2-development-freeze.json` for exact
source/data bindings and `c01-v2-semantic-plan.md` for the next bounded run.
